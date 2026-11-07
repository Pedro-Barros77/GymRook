"""Measure reviewed 2D landmarks on actual raster anchors, without changing art.

Usage: python scripts/audit-animation-geometry.py annotations.json --output qa.json
Annotation format: poses[{file,sha256,points:{name:[x,y]}}], segments:{name:[a,b]},
ratios:{name:[numeratorSegment,denominatorSegment]}, angles:{name:[a,joint,b]},
fixedPoints:[name]. Coordinates refer to the actual 512-square PNGs.
Measurements flag visual inconsistencies; they are not 3D limb lengths or a
certificate of biomechanics. Expected drawing guides are not measured inputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent.parent


def summary(values):
    values = [v for v in values if v is not None]
    if not values:
        return {'samples': 0}
    mean = statistics.mean(values)
    return {'samples': len(values), 'minimum': min(values), 'maximum': max(values),
            'mean': mean, 'rangeDividedByMean': (max(values)-min(values))/mean if mean else None,
            'coefficientOfVariation': statistics.pstdev(values)/mean if mean else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('annotations', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.annotations.read_text(encoding='utf-8-sig'))
    if data.get('coordinateSpace') != 'actual-raster-512-pixels' or not data.get('reviewer'):
        raise ValueError('Declare the actual 512-pixel raster coordinate space and manual reviewer.')
    records = []
    for pose in data['poses']:
        source = ROOT/pose['file']
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if not pose.get('sha256') or actual != pose['sha256']:
            raise ValueError(f'Annotated actual image changed or lacks an exact hash: {source}')
        points = pose['points']
        lengths = {name: math.dist(points[a], points[b]) if a in points and b in points else None
                   for name,(a,b) in data.get('segments', {}).items()}
        ratios = {name: lengths[a]/lengths[b] if lengths.get(a) is not None and lengths.get(b) else None
                  for name,(a,b) in data.get('ratios', {}).items()}
        angles = {}
        for name,(a,joint,b) in data.get('angles', {}).items():
            if not all(p in points for p in [a,joint,b]):
                angles[name] = None
                continue
            u = [points[a][i]-points[joint][i] for i in [0,1]]
            v = [points[b][i]-points[joint][i] for i in [0,1]]
            denominator = math.hypot(*u)*math.hypot(*v)
            angles[name] = math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/denominator)))) if denominator else None
        records.append({'file': pose['file'], 'sha256': actual, 'points': points,
                        'projectedLengthsPixels': lengths, 'projectedRatios': ratios,
                        'projectedJointInteriorDegrees': angles, 'visibilityNotes': pose.get('visibilityNotes', '')})
    fixed = {}
    for name in data.get('fixedPoints', []):
        samples = [r['points'][name] for r in records if name in r['points']]
        if not samples:
            continue
        median = [statistics.median(p[i] for p in samples) for i in [0,1]]
        fixed[name] = {'sampleCount': len(samples), 'medianPixels': median,
                       'maximumDisplacementFromMedianPixels': max(math.dist(p,median) for p in samples)}
    report = {'exerciseId': data.get('exerciseId'), 'reviewer': data['reviewer'],
              'annotationFile': str(args.annotations),
              'annotationSha256': hashlib.sha256(args.annotations.read_bytes()).hexdigest(),
              'coordinateSpace': data['coordinateSpace'], 'projectionNotes': data.get('projectionNotes', ''),
              'limits': 'Lengths/ratios/angles are 2D projections measured manually on actual raster art. Foreshortening, occlusion and landmark uncertainty require visual interpretation. No automatic anatomy or exercise approval is inferred.',
              'poseMeasurements': records,
              'segmentSummary': {n: summary([r['projectedLengthsPixels'][n] for r in records]) for n in data.get('segments', {})},
              'ratioSummary': {n: summary([r['projectedRatios'][n] for r in records]) for n in data.get('ratios', {})},
              'angleSummary': {n: summary([r['projectedJointInteriorDegrees'][n] for r in records]) for n in data.get('angles', {})},
              'fixedLandmarkDisplacement': fixed, 'reviewVerdict': data.get('reviewVerdict', 'pending visual interpretation')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"Measured {len(records)} hashed actual source images; report {args.output}")


if __name__ == '__main__':
    main()
