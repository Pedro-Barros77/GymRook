"""Verify the complete round4 media set and frozen round3 originals.

--exercise may check a staged export. Default always requires the complete
configured set and matching source/motion review; it never accepts partials.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT/'docs/generated-frames-v4-followup/config.json'
WORK = ROOT/'output/followup-round4'
MEDIA = ROOT/'dist/assets/animations-v4'
BUILD = ROOT/'docs/followup-animations-build.json'
BACKUP = ROOT/'backups/visual-v3-before-followup-20261107/manifest.json'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(path, expected):
    require(path.is_file() and digest(path) == expected, 'Frozen file changed: '+str(path))


def verify_preservation():
    snapshot = read(BACKUP)
    prefixes = ['dist/assets/', 'docs/generated-frames/', 'docs/generated-frames-v2/',
                'docs/generated-frames-v3/', 'docs/generated-frames-v4/', 'docs/generated-frames-v5/',
                'docs/generated-frames-d-v1/', 'docs/generated-frames-bc-v1/',
                'docs/generated-frames-v2-fixes/', 'docs/generated-frames-v3-repairs/',
                'output/repair-animations/', 'output/final-animations/', 'output/leg-animations/',
                'output/bc-animations/', 'output/pec-deck-v5/frames/',
                'output/generated-motion/reverse-cable-curl/frames/']
    names = {'scripts/build-repair-animations.py', 'scripts/build-final-animations.py',
             'scripts/build-leg-animations.py', 'scripts/build-bc-animations.py',
             'scripts/rife-batch.py', 'scripts/encode-3d.py'}
    selected = [r for r in snapshot['files'] if r['file'] in names
                or any(r['file'].startswith(p) for p in prefixes)]
    for entry in selected:
        exact(ROOT/entry['file'], entry['sha256'])
    restored = read(ROOT/'docs/generated-frames-v4-followup/supino-restore-preflight.json')
    for entry in restored['files']:
        exact(ROOT/entry['file'], entry['sha256'])
    return {'passed':True, 'manifest':BACKUP.relative_to(ROOT).as_posix(),
            'manifestSha256':digest(BACKUP), 'verifiedOriginalFiles':len(selected),
            'restoredPressFiles':len(restored['files'])}


def main():
    builder = module('round4_builder_verifier', ROOT/'scripts/build-followup-animations.py')
    utility = module('round4_readonly_media_checks', ROOT/'scripts/verify-repair-animations.py')
    codec = module('round4_readonly_codec_checks', ROOT/'scripts/verify-leg-animations.py')
    utility.MEDIA, utility.WORK, utility.CONFIG, utility.BUILD = MEDIA, WORK, CONFIG, BUILD
    codec.MEDIA, codec.SOURCES = MEDIA, WORK
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise', choices=['all', *builder.IDS], default='all')
    args = parser.parse_args()
    config = builder.checked_dependencies()
    build = read(BUILD)
    manifest = read(MEDIA/'manifest.json')
    require(manifest['preferredFormat'] == 'MP4' and manifest['fps'] == 12, 'Wrong MP4/fps contract.')
    by_id = {a['id']:a for a in manifest['animations']}
    records = {a['id']:a for a in build['animations']}
    require(len(by_id) == len(manifest['animations']), 'Duplicate encoded IDs.')
    coverage = manifest['coverage']
    require(coverage['expectedAnimationCount'] == len(builder.IDS), 'Wrong expected coverage.')
    require(coverage['encodedAnimationCount'] == len(by_id), 'Wrong encoded coverage.')
    require(coverage['pendingIds'] == [i for i in builder.IDS if i not in by_id], 'Stale pending list.')
    require(coverage['complete'] == (set(by_id) == set(builder.IDS)), 'Stale completion flag.')
    review = {}
    if args.exercise == 'all':
        require(set(by_id) == set(builder.IDS) and coverage['complete'], 'Full verification requires all configured round4 assets.')
        require(manifest['publicationStage'] == build['publicationStage'] == 'complete', 'Incomplete publication stage.')
        reference = manifest.get('visualReview', {})
        require(reference == build.get('visualReview') and reference['reviewedAnimationCount'] == len(builder.IDS), 'Visual review reference mismatch.')
        exact(ROOT/reference['file'], reference['sha256'])
        index = read(ROOT/reference['file'])
        require(index['complete'] and {r['id'] for r in index['animations']} == set(builder.IDS), 'Incomplete visual index.')
        review = {r['id']:r for r in index['animations']}
        for verdict in review.values():
            for entry in verdict.get('reviewEvidence', []):
                exact(ROOT/entry['file'], entry['sha256'])
    selected = builder.IDS if args.exercise == 'all' else [args.exercise]
    results = []
    for name in selected:
        require(name in by_id and name in records, 'Missing encoded asset: '+name)
        spec, record, media = config['exercises'][name], records[name], by_id[name]
        require(all(spec.get(k) for k in ['prepareReady', 'motionReady', 'exportReady']), 'Review gates not released: '+name)
        require((media['frameCount'],media['fps'],media['durationSeconds'],media['width'],media['height']) == (36,12,3,512,512), 'Wrong video contract: '+name)
        require((media['fpsNumerator'],media['fpsDenominator']) == (12,1), 'Wrong rational fps: '+name)
        require(record['frameSpecSha256'] == builder.frame_spec_digest(spec), 'Frame spec changed after build: '+name)
        if review:
            verdict = review[name]
            frame_hash = hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in record['frames'])).hexdigest()
            require(verdict['verdict'] == 'PASS' and verdict['sourceSha256'] == record['sourceSha256'] and verdict['frameDigestBin32'] == frame_hash, 'Source/frame visual index mismatch: '+name)
        codec.verify_files(media, name)
        anchors = utility.verify_inputs(name, spec, record)
        frames, diagnostics = utility.verify_frames(name, spec, record, anchors)
        codec.verify_video(name, media, frames, 36)
        utility.verify_gif_and_poster(name, spec, media, frames)
        results.append({'id':name, 'frameCount':36, 'fps':12, 'durationSeconds':3,
                        'gifFrames':media['gifFrames'], 'gifDurationMilliseconds':media['gifDurationMilliseconds'],
                        'sourceSha256':record['sourceSha256'], 'files':media['files'], **diagnostics})
        print(name+': PASS; exact frozen inputs/PNGs, H26412fps, GIF3s and poster.')
    result = {'passed':True, 'scope':'complete round4 production set' if args.exercise == 'all' else 'focused staged check: '+args.exercise,
              'configSha256':digest(CONFIG), 'buildReportSha256':digest(BUILD),
              'manifestSha256':digest(MEDIA/'manifest.json'), 'verifierSha256':digest(Path(__file__)),
              'preservation':verify_preservation(), 'animations':results,
              'limits':'Integrity/encoding/continuity only; visual exercise and equipment review is separate.'}
    output = WORK/('technical-verification.json' if args.exercise == 'all' else 'technical-verification-'+args.exercise+'.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('PASS: '+str(len(results))+' media sets; '+str(result['preservation']['verifiedOriginalFiles'])+' originals unchanged.')


if __name__ == '__main__':
    main()
