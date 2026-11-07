"""Prepare generated leg poses, interpolate one batch, and encode 12-fps loops.

Examples:
  python scripts/build-leg-animations.py --prepare-only
  python scripts/build-leg-animations.py --exercise leg-extension --no-encode
  python scripts/build-leg-animations.py --encode-only
  python scripts/build-leg-animations.py

Sources remain unchanged. Registration is translation only; no human mesh,
affine deformation, optical-flow prewarp, or generated pixels are added here.
Interpolation and technical QA do not establish anatomical correctness.
"""
from pathlib import Path
import argparse
import bisect
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'docs/generated-frames-d-v1/config.json'
WORK = ROOT / 'output/leg-animations'
MEDIA = ROOT / 'dist/assets/animations-d-v1'
REPORT = ROOT / 'docs/leg-animations-v1-build.json'
IDS = ('leg-extension', 'hack-squat', 'lying-leg-curl',
       'dumbbell-stiff-leg-deadlift', 'machine-hip-abduction',
       'machine-hip-adduction', 'alternating-lunge')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    path = path.resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def rect_pixels(rect, side):
    if len(rect) != 4 or not (0 <= rect[0] < rect[2] <= 1 and 0 <= rect[1] < rect[3] <= 1):
        raise ValueError('Rectangles must be normalized [x0,y0,x1,y1], within 0..1.')
    return [round(v * side) for v in rect]


def region_error(reference, current, regions):
    errors = []
    for x0, y0, x1, y1 in regions:
        errors.append(np.abs(reference[y0:y1, x0:x1].astype(np.float32)
                             - current[y0:y1, x0:x1].astype(np.float32)).ravel())
    return float(np.concatenate(errors).mean()) if errors else None


def translation_only(reference, current, settings, anchor, identity=False):
    side = current.shape[0]
    regions = [rect_pixels(r, side) for r in settings.get('regions', [])]
    ref = cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY)
    gray = cv2.cvtColor(current, cv2.COLOR_RGB2GRAY)
    limit = float(settings.get('maxTranslationPixels', 10))
    if not 0 <= limit <= 10:
        raise ValueError('Registration is limited to at most 10 pixels per axis.')
    before = region_error(ref, gray, regions)
    candidates, shift, method, accepted = [], np.zeros(2), 'disabled; original crop retained', False
    if identity:
        method, accepted = 'reference identity', True
    elif 'translationPixels' in anchor:
        shift = np.asarray(anchor['translationPixels'], dtype=float)
        if shift.shape != (2,) or not np.all(np.isfinite(shift)) or np.max(np.abs(shift)) > limit:
            raise ValueError('Manual translationPixels must contain two finite shifts within the 10-pixel limit.')
        method, accepted = 'configured translation only', True
    elif settings.get('enabled', True) and regions:
        radius = math.ceil(limit)
        for box in regions:
            x0, y0, x1, y1 = box
            patch = ref[y0:y1, x0:x1]
            if float(patch.std()) < 3:
                continue
            sx, sy = max(0, x0-radius), max(0, y0-radius)
            ex, ey = min(side, x1+radius), min(side, y1+radius)
            scores = cv2.matchTemplate(gray[sy:ey, sx:ex], patch, cv2.TM_CCOEFF_NORMED)
            _, score, _, point = cv2.minMaxLoc(scores)
            px, py = point
            peak = np.array([float(px), float(py)])
            # Parabolic peak refinement keeps the applied translation subpixel.
            for axis, coord in enumerate([px, py]):
                if 0 < coord < scores.shape[1-axis]-1:
                    a, b, c = (scores[py, px-1:px+2] if axis == 0 else scores[py-1:py+2, px])
                    denominator = float(a - 2*b + c)
                    if denominator < -1e-8:
                        peak[axis] += float(np.clip(.5*(a-c)/denominator, -.5, .5))
            candidate = np.array([x0-sx, y0-sy]) - peak
            usable = bool(score >= settings.get('minScore', .55) and np.max(np.abs(candidate)) <= limit)
            candidates.append({'regionPixels': box, 'score': float(score),
                               'translationPixels': candidate.tolist(), 'usable': usable,
                               'atSearchLimit': bool(px in [0, scores.shape[1]-1] or py in [0, scores.shape[0]-1])})
        usable = [c['translationPixels'] for c in candidates if c['usable']]
        if usable:
            shift = np.median(np.asarray(usable), axis=0)
            method, accepted = 'fixed-feature template matching; translation only', True
        else:
            method = 'no reliable fixed template match; original crop retained'
    matrix = np.array([[1, 0, shift[0]], [0, 1, shift[1]]], dtype=np.float32)
    aligned = (current.copy() if not np.any(shift) else cv2.warpAffine(
        current, matrix, (side, side), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE))
    after = region_error(ref, cv2.cvtColor(aligned, cv2.COLOR_RGB2GRAY), regions)
    if accepted and not identity and before is not None and after > before + .25:
        shift[:], matrix[:, 2], aligned, after = 0, 0, current.copy(), before
        method, accepted = 'template increased fixed-region error; original crop retained', False
    return aligned, {'method': method, 'accepted': accepted, 'translationPixels': shift.tolist(),
                     'matrix': matrix.tolist(), 'maxTranslationPixels': limit, 'candidates': candidates,
                     'staticRegionMAEBefore': before, 'staticRegionMAEAfter': after}


def contact(images, labels, path, columns=3, thumb=256):
    rows = math.ceil(len(images)/columns)
    canvas = Image.new('RGB', (columns*thumb, rows*(thumb+26)), 'white')
    draw = ImageDraw.Draw(canvas)
    for i, (image, text) in enumerate(zip(images, labels)):
        x, y = i % columns*thumb, i//columns*(thumb+26)
        canvas.paste(Image.fromarray(image).resize((thumb, thumb), Image.Resampling.LANCZOS), (x, y+26))
        draw.text((x+5, y+7), text, fill='black')
    canvas.save(path)


def onions(images, path, periodic=False):
    panels, labels = [], []
    for i, image in enumerate(images):
        before = images[(i-1) % len(images)] if periodic or i else image
        after = images[(i+1) % len(images)] if periodic or i < len(images)-1 else image
        panels.extend([np.asarray(Image.blend(Image.fromarray(before), Image.fromarray(image), .5)),
                       np.asarray(Image.blend(Image.fromarray(image), Image.fromarray(after), .5))])
        labels.extend([f'{i:02d} previous/current overlay', f'{i:02d} current/next overlay'])
    contact(panels, labels, path, columns=4, thumb=256)


def prepare(exercise, spec, config):
    source = project_path(spec['sheet'])
    if not source.is_file():
        raise FileNotFoundError(source)
    with Image.open(source) as opened:
        sheet = opened.convert('RGB')
    columns, rows = spec['grid']
    entries = spec['anchors']
    expected = 16 if spec['cycle'] == 'periodic' else 9
    if len(entries) != expected:
        raise ValueError(f'{exercise}: expected {expected} source anchor records.')
    progress = [float(entry['progress']) for entry in entries]
    if progress[0] != 0 or any(b <= a for a, b in zip(progress, progress[1:])):
        raise ValueError(f'{exercise}: anchor progress must start at zero and increase strictly.')
    if spec['cycle'] == 'ping-pong' and progress[-1] != 1:
        raise ValueError('Ping-pong anchors must end at progress 1.')
    if spec['cycle'] == 'periodic' and progress[-1] >= 1:
        raise ValueError('Periodic anchors exclude the repeated starting pose at progress 1.')
    folder = WORK / exercise
    anchor_dir, raw_dir, qa = folder/'anchors', folder/'anchors/raw', folder/'qa'
    for directory in [anchor_dir, raw_dir, qa]:
        directory.mkdir(parents=True, exist_ok=True)
    side, trim = config['size'], spec.get('cellTrimPixels', 2)
    if trim not in [1, 2]:
        raise ValueError('Only a one- or two-pixel source-cell border trim is supported.')
    images, bounds = [], []
    for entry in entries:
        cell = int(entry['cell'])
        if not 0 <= cell < columns*rows:
            raise ValueError('Source cell is outside the grid.')
        cx, cy = cell % columns, cell//columns
        box = [round(cx*sheet.width/columns)+trim, round(cy*sheet.height/rows)+trim,
               round((cx+1)*sheet.width/columns)-trim, round((cy+1)*sheet.height/rows)-trim]
        images.append(np.asarray(sheet.crop(box).resize((side, side), Image.Resampling.LANCZOS)).copy())
        bounds.append(box)
    reference_index = spec.get('referenceIndex', 0)
    reference = images[reference_index]
    records, aligned = [], []
    for i, (image, entry) in enumerate(zip(images, entries)):
        raw_path, path = raw_dir/f'anchor_{i:02d}.png', anchor_dir/f'anchor_{i:02d}.png'
        Image.fromarray(image).save(raw_path)
        registered, registration = translation_only(reference, image, spec.get('registration', {}),
                                                     entry, i == reference_index)
        Image.fromarray(registered).save(path)
        aligned.append(registered)
        records.append({'index': i, 'cell': entry['cell'], 'progress': entry['progress'],
                        'cropPixels': bounds[i], 'raw': label(raw_path), 'rawSha256': digest(raw_path),
                        'file': label(path), 'sha256': digest(path), 'registration': registration})
    for rect in spec.get('preserveStaticRects', []):
        rect_pixels(rect, side)
    contact(aligned, [f'Pose {i:02d} | progress {progress[i]:.4f}' for i in range(len(aligned))], qa/'anchors-contact.png')
    onions(aligned, qa/'anchors-onions.png', spec['cycle'] == 'periodic')
    extra_sources = {label(p): digest(p) for p in source.parent.iterdir()
                     if p.is_file() and p.suffix.lower() in ['.json', '.md']}
    record = {'id': exercise, 'status': 'prepared; visual source review required',
              'sourceReview': spec.get('sourceReview', 'pending'),
              'render': 'generated-interpolated', 'source': label(source), 'sourceSha256': digest(source),
              'sourceMetadataSha256': extra_sources, 'sourceSize': list(sheet.size), 'grid': [columns, rows],
              'cellTrimPixels': trim, 'width': side, 'height': side, 'fps': config['fps'],
              'cycle': spec['cycle'], 'frameCount': spec['frameCount'], 'phaseEasing': spec['phaseEasing'],
              'referenceIndex': reference_index, 'registration': spec.get('registration', {}),
              'preserveStaticRects': spec.get('preserveStaticRects', []), 'anchors': records,
              'qa': {'anchorsContact': label(qa/'anchors-contact.png'), 'anchorsOnions': label(qa/'anchors-onions.png')}}
    write_json(folder/'prepare.json', record)
    return record


def frame_plan(spec):
    count = spec['frameCount']
    forward_count = count//2+1 if spec['cycle'] == 'ping-pong' else count
    progress = [float(a['progress']) for a in spec['anchors']]
    plans = []
    for i in range(forward_count):
        phase = i/(forward_count-1) if spec['cycle'] == 'ping-pong' else i/count
        target = .5-.5*math.cos(math.pi*phase) if spec['phaseEasing'] == 'cosine' else phase
        right = bisect.bisect_left(progress, target)
        if right < len(progress) and abs(progress[right]-target) < 1e-10:
            a = b = right
            t = 0.
        else:
            a, b = right-1, right % len(progress)
            end = progress[b] if b else 1.
            t = (target-progress[a])/(end-progress[a])
        plans.append({'frame': i+1, 'phase': phase, 'progress': target,
                      'anchor0': a, 'anchor1': b, 'timestep': t})
    if spec['cycle'] == 'ping-pong':
        for source_frame in range(forward_count-1, 1, -1):
            plans.append({'frame': len(plans)+1, 'mirroredFromFrame': source_frame})
    if len(plans) != count:
        raise ValueError('Invalid loop schedule.')
    return plans


def override_for(spec, plan):
    if 'anchor0' not in plan or plan['anchor0'] == plan['anchor1']:
        return None
    matches = [rule for rule in spec.get('interpolationOverrides', [])
               if rule['interval'] == plan['anchor0'] and
               ('frames' not in rule or plan['frame'] in rule['frames'])]
    if len(matches) > 1:
        raise ValueError('Multiple interpolation overrides match the same output frame.')
    if matches and matches[0]['engine'] not in ['google-film-tfhub-v1', 'Practical-RIFE 4.25']:
        raise ValueError('Only the configured RIFE and official Google FILM backends are supported.')
    if matches and 'timestep' in matches[0] and not 0 < float(matches[0]['timestep']) < 1:
        raise ValueError('A local interpolation-time override must remain strictly inside (0,1).')
    return matches[0] if matches else None


def run_interpolation(jobs, config, suffix):
    batch_path = WORK/f'interpolation-jobs{suffix}.json'
    write_json(batch_path, jobs)
    started, runs, actual = time.monotonic(), [], {}
    for engine in ['Practical-RIFE 4.25', 'google-film-tfhub-v1']:
        selected = [{k: v for k, v in job.items() if k != 'engine'} for job in jobs if job['engine'] == engine]
        if not selected:
            continue
        film = engine == 'google-film-tfhub-v1'
        settings = config['interpolation']['film'] if film else config['interpolation']
        manifest = WORK/f'interpolation-jobs{suffix}-{"film" if film else "rife"}.json'
        write_json(manifest, selected)
        command = [str(project_path(settings['python'])), str(project_path(settings['helper'])),
                   '--manifest', str(manifest), '--model-dir', str(project_path(settings['modelDirectory'])),
                   '--threads', str(settings['threads'])]
        report_path = WORK/f'film-results{suffix}.json'
        command += (['--depth', str(settings['depth']), '--report', str(report_path)] if film else
                    ['--scale', str(settings['scale'])])
        subprocess.run(command, check=True, cwd=ROOT)
        run = {'engine': engine, 'jobCount': len(selected), 'modelLoads': 1,
               'manifest': label(manifest), 'manifestSha256': digest(manifest)}
        if film:
            report = read_json(report_path)
            if len(report['jobs']) != len(selected):
                raise RuntimeError('FILM returned an unexpected number of outputs.')
            for request, result in zip(selected, report['jobs']):
                if (Path(result['output']).resolve() != Path(request['output']).resolve()
                        or Path(result['input0']).resolve() != Path(request['input0']).resolve()
                        or Path(result['input1']).resolve() != Path(request['input1']).resolve()
                        or abs(result['requestedTimestep']-request['timestep']) > 1e-12):
                    raise RuntimeError('FILM report does not match its exact input/output request.')
                actual[str(Path(request['output']).resolve())] = result
            run.update({'actualReport': label(report_path), 'actualReportSha256': digest(report_path),
                        'depth': settings['depth'], 'midpointInferences': report['totalMidpointInferences']})
        runs.append(run)
    return {'jobCount': len(jobs), 'modelLoads': len(runs), 'batches': runs,
            'batchManifest': label(batch_path), 'batchManifestSha256': digest(batch_path),
            'elapsedSeconds': time.monotonic()-started}, actual


def build_frames(selected, specs, config, records, patch_overrides=False):
    jobs, plans_by_id, changed_by_id, unchanged_hashes = [], {}, {}, {}
    for exercise in selected:
        folder, spec = WORK/exercise, specs[exercise]
        frames = folder/'frames'
        frames.mkdir(exist_ok=True)
        expected = {f'frame_{i:04d}.png' for i in range(1, spec['frameCount']+1)}
        for path in frames.glob('frame_*.png'):
            if path.name not in expected:
                raise ValueError(f'Stale frame outside configured sequence: {path}; inspect it before rebuilding.')
        plans = frame_plan(spec)
        if patch_overrides:
            old_plans = records[exercise].get('frames', [])
            if len(old_plans) != len(plans):
                raise ValueError('A local override patch requires a complete previous frame sequence.')
            for old, new in zip(old_plans, plans):
                keys = ['frame', 'anchor0', 'anchor1', 'timestep', 'mirroredFromFrame']
                if any(old.get(key) != new.get(key) for key in keys):
                    raise ValueError('The trajectory changed; rebuild this exercise instead of patching overrides.')
                path = project_path(old['file'])
                if digest(path) != old['sha256']:
                    raise ValueError(f'Existing frame changed before local patch: {path}')
            for anchor in records[exercise]['anchors']:
                if digest(project_path(anchor['file'])) != anchor['sha256']:
                    raise ValueError('An input anchor changed before local patch.')
            if digest(project_path(spec['sheet'])) != records[exercise]['sourceSha256']:
                raise ValueError('The generated source sheet changed before local patch.')
            plans = [{**old, **new} for old, new in zip(old_plans, plans)]
        plans_by_id[exercise] = plans
        changed = set()
        changed_by_id[exercise] = changed
        for plan in plans:
            if 'mirroredFromFrame' in plan:
                continue
            override = override_for(spec, plan)
            if patch_overrides and not override:
                unchanged_hashes[frames/f"frame_{plan['frame']:04d}.png"] = plan['sha256']
                continue
            changed.add(plan['frame'])
            destination = frames/f"frame_{plan['frame']:04d}.png"
            if patch_overrides:
                archive = folder/'qa/override-backups'/f"frame_{plan['frame']:04d}-{plan['sha256'][:12]}.png"
                archive.parent.mkdir(parents=True, exist_ok=True)
                if not archive.exists():
                    shutil.copyfile(destination, archive)
                if digest(archive) != plan['sha256']:
                    raise ValueError('The original override-candidate backup hash does not match.')
                if 'previousOutput' in plan:
                    plan.setdefault('earlierOutputs', []).append(plan['previousOutput'])
                plan['previousOutput'] = {'file': label(archive), 'sha256': plan['sha256'],
                                          'engine': plan.get('engine', 'Practical-RIFE 4.25')}
            a = folder/'anchors'/f"anchor_{plan['anchor0']:02d}.png"
            b = folder/'anchors'/f"anchor_{plan['anchor1']:02d}.png"
            if plan['anchor0'] == plan['anchor1']:
                shutil.copyfile(a, destination)
                plan['engine'] = 'source-anchor copy'
            else:
                plan['engine'] = override['engine'] if override else 'Practical-RIFE 4.25'
                inference_timestep = float(override.get('timestep', plan['timestep'])) if override else plan['timestep']
                plan['requestedInterpolationTimestep'] = inference_timestep
                plan['actualTimestep'] = inference_timestep
                plan['localRetimingDelta'] = inference_timestep-plan['timestep']
                for key in ['dyadicDepth', 'timestepError', 'input0', 'input1']:
                    plan.pop(key, None)
                if override:
                    plan['override'] = override
                jobs.append({'input0': str(a.resolve()), 'input1': str(b.resolve()),
                             'timestep': inference_timestep, 'output': str(destination.resolve()), 'engine': plan['engine']})
    batch, actual = run_interpolation(jobs, config, '-patch' if patch_overrides else '')
    for exercise, plans in plans_by_id.items():
        folder, spec = WORK/exercise, specs[exercise]
        frames = folder/'frames'
        ref = np.asarray(Image.open(folder/'anchors'/f"anchor_{spec.get('referenceIndex', 0):02d}.png").convert('RGB'))
        for plan in plans:
            path = frames/f"frame_{plan['frame']:04d}.png"
            if 'mirroredFromFrame' in plan:
                if not patch_overrides or plan['mirroredFromFrame'] in changed_by_id[exercise]:
                    shutil.copyfile(frames/f"frame_{plan['mirroredFromFrame']:04d}.png", path)
                    changed_by_id[exercise].add(plan['frame'])
                else:
                    unchanged_hashes[path] = plan['sha256']
                plan['engine'] = 'byte-exact return copy'
            elif spec.get('preserveStaticRects') and (not patch_overrides or plan['frame'] in changed_by_id[exercise]):
                image = np.asarray(Image.open(path).convert('RGB')).copy()
                for rect in spec['preserveStaticRects']:
                    x0, y0, x1, y1 = rect_pixels(rect, config['size'])
                    image[y0:y1, x0:x1] = ref[y0:y1, x0:x1]
                Image.fromarray(image).save(path)
            if str(path.resolve()) in actual:
                result = actual[str(path.resolve())]
                plan.update({'actualTimestep': result['actualDyadicTimestep'], 'dyadicDepth': result['depth'],
                             'timestepError': result['timestepError'], 'input0': label(Path(result['input0'])),
                             'input1': label(Path(result['input1']))})
            plan['file'], plan['sha256'] = label(path), digest(path)
        images = [np.asarray(Image.open(frames/f"frame_{i:04d}.png").convert('RGB')) for i in range(1, len(plans)+1)]
        qa = folder/'qa'
        sample_indices = [round(i*(len(images)-1)/11) for i in range(12)]
        contact([images[i] for i in sample_indices], [f'Frame {i+1:02d}' for i in sample_indices], qa/'frames-contact.png', columns=4)
        last = len(images) if spec['cycle'] == 'periodic' else len(images)//2
        overlays = [np.asarray(Image.blend(Image.fromarray(images[i]), Image.fromarray(images[(i+1)%len(images)]), .5))
                    for i in range(last)]
        contact(overlays, [f'{i+1:02d}/{(i+1)%len(images)+1:02d} overlay' for i in range(last)], qa/'transitions-onions.png', columns=6)
        differences = [float(np.mean(np.abs(images[(i+1)%len(images)].astype(float)-im))) for i, im in enumerate(images)]
        record = records[exercise]
        record.update({'status': 'frames composed; visual motion review required', 'frames': plans,
                       'interpolationOverrides': spec.get('interpolationOverrides', []),
                       'seamMAE': differences[-1], 'adjacentFrameMAE': differences,
                       'qa': {**record['qa'], 'framesContact': label(qa/'frames-contact.png'),
                              'transitionsOnions': label(qa/'transitions-onions.png')}})
    for path, expected_sha in unchanged_hashes.items():
        if digest(path) != expected_sha:
            raise RuntimeError(f'An out-of-scope PNG changed during local override patch: {path}')
    batch.update({'patchOverridesOnly': patch_overrides, 'untouchedFramesVerified': len(unchanged_hashes),
                  'changedFrames': {exercise: sorted(indices) for exercise, indices in changed_by_id.items()}})
    return batch


def model_provenance(config):
    inference = config['interpolation']
    paths = [project_path(inference['helper']), project_path(inference['modelDirectory'])/'train_log/flownet.pkl']
    paths += sorted(project_path(inference['modelDirectory']).rglob('*.py'))
    result = {**inference, 'files': {label(p): {'sha256': digest(p), 'bytes': p.stat().st_size}
                                  for p in paths if p.is_file()},
            'missing': [label(p) for p in paths if not p.is_file()]}
    if 'film' in inference:
        film = inference['film']
        directory = project_path(film['modelDirectory'])
        paths = [project_path(film['helper']), directory/'saved_model.pb',
                 directory/'variables/variables.index', directory/'variables/variables.data-00000-of-00001']
        result['film'] = {**film, 'files': {label(p): {'sha256': digest(p), 'bytes': p.stat().st_size}
                                           for p in paths if p.is_file()},
                          'missing': [label(p) for p in paths if not p.is_file()]}
    return result


def generated_frame_timesteps(plans):
    result = []
    for plan in plans:
        if 'mirroredFromFrame' in plan:
            result.append({'frame': plan['frame'], 'mirroredFromFrame': plan['mirroredFromFrame']})
        else:
            result.append({'frame': plan['frame'], 'anchor0': plan['anchor0'], 'anchor1': plan['anchor1'],
                           'originalRequestedTimestep': plan['timestep'],
                           'effectiveInterpolationTimestep': plan.get('actualTimestep', plan['timestep']),
                           'engine': plan.get('engine', 'source-anchor copy' if plan['anchor0'] == plan['anchor1'] else 'Practical-RIFE 4.25')})
    return result


def encode_media(selected, config, records):
    spec = importlib.util.spec_from_file_location('leg_shared_encoder', ROOT/'scripts/encode-3d.py')
    encoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(encoder)
    manifest_path = MEDIA/'manifest.json'
    prior = read_json(manifest_path) if manifest_path.exists() else {}
    animations = {r['id']: r for r in prior.get('animations', [])}
    for exercise in selected:
        record = encoder.encode(exercise, WORK, MEDIA, config['fps'], records[exercise]['frameCount'])
        record['render'] = 'generated-interpolated'
        if record['gifFrames'] != record['frameCount']:
            print(f'{exercise}: GIF merged consecutive identical palette frames: {record["gifFrames"]}/{record["frameCount"]}. Review the actual file; no artificial pixel changes were added.', flush=True)
        animations[exercise] = record
        records[exercise]['status'] = 'encoded; visual motion review required'
        records[exercise]['encoded'] = record
    manifest = {'pipeline': 'Generated colored pose sheets -> translation-only registration -> Practical-RIFE 4.25 -> PNG loops -> encoded media',
                'render': 'generated-interpolated', 'preferredFormat': 'MP4', 'fps': config['fps'],
                'gifTimingNote': 'Cumulative centisecond rounding uses 80/90 ms delays at 12 fps and preserves the exact loop duration.',
                'encoder': {'package': f'imageio-ffmpeg {encoder.imageio_ffmpeg.__version__}',
                            'ffmpeg': encoder.imageio_ffmpeg.get_ffmpeg_version(),
                            'script': 'scripts/encode-3d.py', 'scriptSha256': digest(ROOT/'scripts/encode-3d.py')},
                'animations': [animations[i] for i in IDS if i in animations]}
    write_json(manifest_path, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise', choices=['all', *IDS], default='all')
    parser.add_argument('--config', type=Path, default=CONFIG)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only', action='store_true', help='Only crop/register anchors and create source-review QA; no inference or dist writes.')
    mode.add_argument('--no-encode', action='store_true', help='Also compose/interpolate PNGs, without publishing media into dist.')
    mode.add_argument('--encode-only', action='store_true', help='Encode the existing reviewed PNGs only, after verifying their recorded hashes; no preparation or inference.')
    mode.add_argument('--patch-overrides', action='store_true', help='Recompute only configured override output frames against existing anchors; verify every untouched frame hash. Does not encode.')
    args = parser.parse_args()
    config = read_json(args.config)
    config_sha256 = digest(args.config)
    if config['fps'] != 12 or config['size'] != 512:
        raise ValueError('This pipeline is defined as 512-square images at 12 fps.')
    specs = config['exercises']
    requested = list(IDS) if args.exercise == 'all' else [args.exercise]
    selected = [i for i in requested if specs[i].get('prepareReady', True)]
    skipped = {i: specs[i].get('pendingReason', 'Source review pending') for i in requested if i not in selected}
    if not selected:
        raise ValueError(f'No ready sources selected: {skipped}')
    for exercise in selected:
        expected = 48 if exercise == 'alternating-lunge' else 36
        if specs[exercise]['frameCount'] != expected:
            raise ValueError(f'{exercise}: expected {expected} frames.')
    # Existing pilot media and all selected originals are read-only inputs.
    preserved = {p: digest(p) for directory in (ROOT/'dist/assets').glob('animations*')
                 if directory.is_dir() and directory != MEDIA for p in directory.rglob('*') if p.is_file()}
    preserved.update({project_path(specs[i]['sheet']): digest(project_path(specs[i]['sheet'])) for i in selected})
    preserved[args.config] = config_sha256
    prior = read_json(REPORT) if REPORT.exists() else {}
    records = {r['id']: r for r in prior.get('animations', [])}
    frame_generation = None
    if args.encode_only:
        if prior.get('stage') not in ['frames', 'encoded'] or prior.get('configSha256') != config_sha256:
            raise ValueError('--encode-only requires an existing frame build with the exact current configuration hash.')
        for exercise in selected:
            record = records.get(exercise, {})
            if digest(project_path(specs[exercise]['sheet'])) != record.get('sourceSha256'):
                raise ValueError(f'{exercise}: source sheet no longer matches the reviewed frame build.')
            if len(record.get('frames', [])) != specs[exercise]['frameCount']:
                raise ValueError(f'{exercise}: no complete recorded PNG sequence to encode.')
            for frame in record['frames']:
                path = project_path(frame['file'])
                if not path.is_file() or digest(path) != frame['sha256']:
                    raise ValueError(f'Reviewed PNG hash changed: {path}')
                preserved[path] = frame['sha256']
        frame_generation = prior.get('frameGeneration') if prior.get('stage') == 'encoded' else None
        if not frame_generation:
            frame_generation = {'generator': prior['generator'], 'generatorSha256': prior['generatorSha256'],
                                'configSha256': prior['configSha256'], 'batch': prior.get('batch'),
                                'previousCandidateHistory': prior.get('frameGeneration')}
        batch = prior.get('batch')
        print('All selected reviewed PNG hashes match. Encoding only; no preparation or inference.', flush=True)
        encode_media(selected, config, records)
    elif args.patch_overrides:
        if prior.get('stage') not in ['frames', 'encoded']:
            raise ValueError('Local override patching requires an existing frame build.')
        for exercise in selected:
            if exercise not in records or not specs[exercise].get('interpolationOverrides'):
                raise ValueError(f'{exercise}: no existing frame build/configured overrides to patch.')
        frame_generation = {'previousGenerator': prior['generator'], 'previousGeneratorSha256': prior['generatorSha256'],
                            'previousConfigSha256': prior['configSha256'], 'previousBatch': prior.get('batch')}
        batch = None
    else:
        for exercise in selected:
            records[exercise] = prepare(exercise, specs[exercise], config)
            records[exercise]['configSha256'] = config_sha256
            write_json(WORK/exercise/'prepare.json', records[exercise])
            print(f'{exercise}: prepared {len(records[exercise]["anchors"])} anchors; review {WORK/exercise/"qa"/"anchors-contact.png"}', flush=True)
        batch = None
    if not args.prepare_only and not args.encode_only:
        batch = build_frames(selected, specs, config, records, args.patch_overrides)
        for exercise in selected:
            records[exercise]['configSha256'] = config_sha256
        if not args.no_encode and not args.patch_overrides:
            encode_media(selected, config, records)
    for path, expected in preserved.items():
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError(f'A preserved source or existing pilot media changed: {path}')
    for record in records.values():
        if 'frames' in record:
            record['generatedFrameTimesteps'] = generated_frame_timesteps(record['frames'])
    report = {'pipeline': 'generated-interpolated', 'stage': 'prepared' if args.prepare_only else ('frames' if args.no_encode or args.patch_overrides else 'encoded'),
              'fps': config['fps'], 'size': [config['size']]*2,
              'config': label(args.config), 'configSha256': config_sha256,
              'generator': label(Path(__file__)), 'generatorSha256': digest(Path(__file__)),
              'method': {'registration': 'translation only from configured fixed-feature templates, maximum 10 pixels per axis',
                         'pingPong': '19 cosine-progress forward frames, then byte-exact copies of forward frames 18..2',
                         'periodic': '48 uniformly timed frames through 16 anchors, including final-to-first interpolation; no image mirroring',
                         'qaLimit': 'Contact sheets, onions and pixel metrics support visual review; they do not validate biomechanics or prevent interpolation artifacts.'},
              'interpolation': model_provenance(config), 'batch': batch, 'frameGeneration': frame_generation, 'skipped': skipped,
              'preservedSourceAndPilotFiles': len(preserved), 'preservationVerified': True,
              'animations': [records[i] for i in IDS if i in records]}
    write_json(REPORT, report)
    print(f'{report["stage"]}: {len(selected)} exercises; report {REPORT}', flush=True)
    for exercise, reason in skipped.items():
        print(f'Skipped {exercise}: {reason}', flush=True)


if __name__ == '__main__':
    main()
