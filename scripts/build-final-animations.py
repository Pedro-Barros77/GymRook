"""Build the reviewed final exercise corrections and remaining A guides at 12 fps.

Only this adapter's config, output/final-animations and animations-v2 media are
written. The D/B+C engines, original sheets and earlier media remain read-only.
Use --prepare-only before source review; --no-encode before motion review;
--encode-only exports exactly the PNG hashes that were reviewed.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT/'docs/generated-frames-v2-fixes/config.json'
WORK = ROOT/'output/final-animations'
MEDIA = ROOT/'dist/assets/animations-v2'
REPORT = ROOT/'docs/final-animations-build.json'
ENGINE = ROOT/'scripts/build-leg-animations.py'
ADAPTER = ROOT/'scripts/build-bc-animations.py'
IDS = (
    'high-cable-crossover', 'cable-biceps-curl', 'preacher-curl',
    'floor-crunch', 'reverse-crunch', 'forearm-plank',
    'lying-leg-curl', 'dumbbell-stiff-leg-deadlift', 'alternating-lunge',
    'dumbbell-lateral-raise', 'reverse-pec-deck', 'seated-plate-calf-raise',
    'unilateral-cable-row', 'machine-ab-crunch',
    'incline-dumbbell-press', 'push-up', 'reverse-cable-curl', 'pec-deck',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_spec_digest(spec):
    administrative = {'prepareReady', 'motionReady', 'sourceReview', 'pendingReason', 'geometryReview', 'reviewStatus'}
    payload = {k:v for k,v in spec.items() if k not in administrative}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attach_release_metadata(engine, report):
    path = MEDIA/'manifest.json'
    if not path.is_file():
        report['publicationStage'] = 'source-or-motion-review'
        return
    manifest = engine.read_json(path)
    report['coverage'] = manifest['coverage']
    if report['stage'] != 'encoded':
        report['publicationStage'] = 'source-or-motion-review'
        return
    complete = manifest['coverage']['complete']
    report['publicationStage'] = 'complete' if complete else 'partial-export'
    manifest['publicationStage'] = report['publicationStage']
    review_path = ROOT/'docs/generated-frames-v2-fixes/final-release-review.json'
    if complete:
        if not review_path.is_file():
            raise ValueError('Complete publication requires the final source/motion review index.')
        review = engine.read_json(review_path)
        indexed = {a['id']:a for a in review['animations']}
        records = {a['id']:a for a in report['animations']}
        if set(indexed) != set(IDS) or not review.get('complete'):
            raise ValueError('Final review index must cover all 18 actual animation sets.')
        for exercise in IDS:
            record, verdict = records[exercise], indexed[exercise]
            actual = hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in record['frames'])).hexdigest()
            if verdict['verdict'] != 'PASS' or verdict['sourceSha256'] != record['sourceSha256'] or verdict['frameDigestBin32'] != actual:
                raise ValueError(f'{exercise}: final review index does not match the exact encoded source/frame build.')
            record['status'] = 'encoded; source and temporal visual review passed for this illustrative release'
            record['sourceReview'] = verdict['sourceReview']
            record['finalReview'] = {'file':engine.label(review_path),'sha256':digest(review_path),'notes':verdict.get('notes',[])}
        reference = {'file':engine.label(review_path),'sha256':digest(review_path),
                     'scope':review['scope'],'reviewedAnimationCount':len(indexed)}
        manifest['visualReview'] = reference
        report['visualReview'] = reference
        report['reviewStatus'] = 'all 18 source and temporal raster reviews passed for this illustrative release'
    manifest['pipeline'] = 'Reviewed generated raster inputs, translation-only registration, RIFE where needed, and 12-fps media; one unchanged source for the isometric hold.'
    engine.write_json(path,manifest)


def reviewed_inputs(config, selected):
    """Validate every external PNG, including byte-exact 24-to-12-fps inputs."""
    inputs = {}
    for exercise in selected:
        spec = config['exercises'][exercise]
        if not spec.get('prepareReady', False):
            continue
        for item in spec.get('sourceFrames', []):
            inputs[ROOT/item['file']] = item['sha256']
        for item in spec.get('anchors', []):
            if 'imageOverride' in item:
                inputs[ROOT/item['imageOverride']] = item['imageOverrideSha256']
        if spec.get('sheetSha256'):
            inputs[ROOT/spec['sheet']] = spec['sheetSha256']
    for path, expected in inputs.items():
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'Reviewed source hash mismatch: {path}')
    return inputs


def prepare_decimated(engine, exercise, spec, config):
    """Normalize approved PNGs once, without invoking frame interpolation."""
    entries = spec['sourceFrames']
    if len(entries) != spec['frameCount'] or len(entries) != 36:
        raise ValueError('24-to-12-fps decimation requires 36 explicitly hashed source frames.')
    if [e['sourceFrame'] for e in entries] != list(range(1, 72, 2)):
        raise ValueError('The approved conversion samples source frames 1,3,...,71.')
    folder = WORK/exercise
    anchors, raw, qa = folder/'anchors', folder/'anchors/raw', folder/'qa'
    for directory in [anchors, raw, qa]:
        directory.mkdir(parents=True, exist_ok=True)
    images, records = [], []
    for i, entry in enumerate(entries):
        source = ROOT/entry['file']
        if digest(source) != entry['sha256']:
            raise ValueError(f'Decimated source changed: {source}')
        with engine.Image.open(source) as opened:
            original_size = opened.size
            image = opened.convert('RGB')
            if image.size != (config['size'],)*2:
                if spec.get('normalizeSourceSize') != list(image.size):
                    raise ValueError('Unexpected source dimensions; implicit normalization is forbidden.')
                image = image.resize((config['size'],)*2, engine.Image.Resampling.LANCZOS)
        out, raw_out = anchors/f'anchor_{i:02d}.png', raw/f'anchor_{i:02d}.png'
        # Preserve the approved PNG bytes when no dimension/mode conversion is needed.
        with engine.Image.open(source) as opened:
            identical = opened.mode == 'RGB' and opened.size == image.size
        if identical:
            out.write_bytes(source.read_bytes())
        else:
            image.save(out)
        raw_out.write_bytes(out.read_bytes())
        images.append(engine.np.asarray(image).copy())
        records.append({'index': i, 'cell': None, 'progress': i/36,
                        'file': engine.label(out), 'sha256': digest(out),
                        'raw': engine.label(raw_out), 'rawSha256': digest(raw_out),
                        'originalSourceFile': entry['file'], 'originalSourceSha256': entry['sha256'],
                        'sourceFrame': entry['sourceFrame'], 'originalSourceSize': list(original_size),
                        'normalization': 'none; exact PNG copy' if identical else 'one Lanczos normalization to 512 square',
                        'registration': {'method': 'already-reviewed source sequence; no additional registration',
                                         'accepted': True, 'translationPixels': [0, 0]}})
    engine.contact(images, [f"F{i+1:02d} <- old F{e['sourceFrame']:02d}" for i,e in enumerate(entries)], qa/'anchors-contact.png', columns=6)
    engine.onions(images, qa/'anchors-onions.png', periodic=True)
    record = {'id': exercise, 'status': 'prepared; sampled sequence review required',
              'sourceKind': spec['sourceKind'], 'sourceReview': spec['sourceReview'],
              'render': 'generated-interpolated', 'source': spec['sheet'],
              'sourceSha256': digest(ROOT/spec['sheet']), 'sourceSize': list(original_size),
              'width': 512, 'height': 512, 'fps': 12, 'cycle': spec['cycle'],
              'frameCount': 36, 'phaseEasing': 'source-timing-preserved',
              'referenceIndex': 0, 'preserveStaticRects': [], 'anchors': records,
              'sourceFrames': entries, 'conversion': spec['conversion'],
              'qa': {'anchorsContact': engine.label(qa/'anchors-contact.png'),
                     'anchorsOnions': engine.label(qa/'anchors-onions.png')}}
    engine.write_json(folder/'prepare.json', record)
    return record


def prepare_hold(engine, exercise, spec, config):
    source = ROOT/spec['sheet']
    with engine.Image.open(source) as opened:
        original_size = opened.size
        image = opened.convert('RGB')
        if image.size != (512, 512):
            image = image.resize((512, 512), engine.Image.Resampling.LANCZOS)
    folder = WORK/exercise
    for directory in [folder/'anchors', folder/'anchors/raw', folder/'qa']:
        directory.mkdir(parents=True, exist_ok=True)
    path, raw = folder/'anchors/anchor_00.png', folder/'anchors/raw/anchor_00.png'
    image.save(path)
    raw.write_bytes(path.read_bytes())
    engine.contact([engine.np.asarray(image)], ['Stable isometric hold; no exercise repetitions'], folder/'qa/anchors-contact.png', columns=1)
    engine.onions([engine.np.asarray(image)], folder/'qa/anchors-onions.png')
    record = {'id': exercise, 'status': 'prepared; isometric posture review required',
              'sourceKind': 'isometric-hold', 'sourceReview': spec['sourceReview'],
              'render': 'generated-static-hold', 'source': spec['sheet'], 'sourceSha256': digest(source),
              'sourceSize': list(original_size), 'width': 512, 'height': 512, 'fps': 12,
              'cycle': spec['cycle'], 'frameCount': 36, 'phaseEasing': 'none; isometric',
              'referenceIndex': 0, 'preserveStaticRects': [],
              'anchors': [{'index': 0, 'cell': None, 'progress': 0., 'file': engine.label(path),
                           'sha256': digest(path), 'raw': engine.label(raw), 'rawSha256': digest(raw),
                           'registration': {'method': 'single stable source; no registration', 'translationPixels': [0,0]}}],
              'qa': {'anchorsContact': engine.label(folder/'qa/anchors-contact.png'),
                     'anchorsOnions': engine.label(folder/'qa/anchors-onions.png')}}
    engine.write_json(folder/'prepare.json', record)
    return record


def prepare_image_keys(engine, exercise, spec, config):
    """Prepare actual reviewed individual key images, never derived fake poses."""
    entries = spec['anchors']
    require_count = spec.get('reviewedKeyCount', 2)
    if len(entries) != require_count or not 2 <= len(entries) <= 9:
        raise ValueError('Individual-image motion requires 2..9 explicitly reviewed actual input keys.')
    progress = [float(a['progress']) for a in entries]
    if progress[0] != 0 or progress[-1] != 1 or any(b <= a for a,b in zip(progress,progress[1:])):
        raise ValueError('Reviewed key progress must strictly increase from zero to one.')
    raw_images = []
    for entry in entries:
        path = ROOT/entry['imageOverride']
        if digest(path) != entry['imageOverrideSha256']:
            raise ValueError(f'Reviewed individual key changed: {path}')
        with engine.Image.open(path) as image:
            if image.mode != 'RGB' or image.size != (512,512):
                raise ValueError('Reviewed individual keys must already be RGB512; no implicit resizing.')
            raw_images.append(engine.np.asarray(image).copy())
    folder = WORK/exercise
    for directory in [folder/'anchors',folder/'anchors/raw',folder/'qa']:
        directory.mkdir(parents=True,exist_ok=True)
    records,images = [],[]
    ref_index = spec.get('referenceIndex',0)
    for i,(entry,image) in enumerate(zip(entries,raw_images)):
        source = ROOT/entry['imageOverride']
        raw,path = folder/'anchors/raw'/f'anchor_{i:02d}.png',folder/'anchors'/f'anchor_{i:02d}.png'
        raw.write_bytes(source.read_bytes())
        aligned,registration = engine.translation_only(raw_images[ref_index],image,spec.get('registration',{}),entry,i==ref_index)
        if not engine.np.any(engine.np.asarray(registration['translationPixels'])):
            path.write_bytes(source.read_bytes())
        else:
            engine.Image.fromarray(aligned).save(path)
        records.append({'index':i,'cell':None,'progress':entry['progress'],'cropPixels':None,
                        'raw':engine.label(raw),'rawSha256':digest(raw),'file':engine.label(path),'sha256':digest(path),
                        'registration':registration,'imageOverride':{'file':entry['imageOverride'],'sha256':entry['imageOverrideSha256']}})
        images.append(aligned)
    qa = folder/'qa'
    engine.contact(images,[f'Actual reviewed key {i}: progress {a["progress"]}' for i,a in enumerate(entries)],qa/'anchors-contact.png',columns=2)
    engine.onions(images,qa/'anchors-onions.png')
    record = {'id':exercise,'status':'prepared; actual individual key review required','sourceKind':'image-keyframes',
              'sourceReview':spec['sourceReview'],'render':'generated-interpolated','source':spec['sheet'],
              'sourceSha256':digest(ROOT/spec['sheet']),'sourceSize':[512,512],'width':512,'height':512,'fps':12,
              'cycle':spec['cycle'],'frameCount':spec['frameCount'],'phaseEasing':spec['phaseEasing'],
              'referenceIndex':ref_index,'registration':spec.get('registration',{}),'preserveStaticRects':[],
              'anchors':records,'reviewedKeyCount':len(entries),
              'qa':{'anchorsContact':engine.label(qa/'anchors-contact.png'),'anchorsOnions':engine.label(qa/'anchors-onions.png')}}
    engine.write_json(folder/'prepare.json',record)
    return record


def exact_gif_if_needed(engine, exercise, record):
    """Emit legitimate identical GIF frames without changing any image pixels."""
    if record['gifFrames'] == record['frameCount']:
        record['gifFrameEmission'] = 'ordinary Pillow save; all frames retained'
        return
    from PIL import GifImagePlugin
    path = MEDIA/record['gif']
    with engine.Image.open(path) as gif:
        palette = gif.copy().convert('P')
    frames = []
    for index in range(1, record['frameCount']+1):
        with engine.Image.open(WORK/exercise/'frames'/f'frame_{index:04d}.png') as image:
            frames.append(image.convert('RGB').quantize(palette=palette, dither=engine.Image.Dither.NONE))
    boundaries = [round(i*100/record['fps']) for i in range(len(frames)+1)]
    delays = [(b-a)*10 for a,b in zip(boundaries,boundaries[1:])]
    # getheader/getdata write each image descriptor explicitly. Pillow's normal
    # multi-image save merges identical frames even with optimize=False.
    header, _ = GifImagePlugin.getheader(frames[0], info={'loop': 0, 'optimize': False})
    with path.open('wb') as output:
        for chunk in header:
            output.write(chunk)
        for image, delay in zip(frames, delays):
            for chunk in GifImagePlugin.getdata(image, duration=delay, disposal=2, include_color_table=False):
                output.write(chunk)
        output.write(b';')
    with engine.Image.open(path) as gif:
        actual = []
        for i in range(gif.n_frames):
            gif.seek(i)
            actual.append(gif.info.get('duration', 0))
        if gif.n_frames != record['frameCount'] or gif.info.get('loop') != 0 or actual != delays:
            raise RuntimeError('Exact-frame GIF emission failed its count/timing/loop contract.')
    record.update({'gifFrames': len(actual), 'gifDurationMilliseconds': sum(actual),
                   'gifFrameDelaysMilliseconds': actual,
                   'gifFrameEmission': 'explicit GIF image descriptors; legitimate identical hold frames retained; no changed pixels'})
    record['files'][path.name] = {'bytes': path.stat().st_size, 'sha256': digest(path)}


def configured_engine():
    engine = load_module('final_shared_d_engine', ENGINE)
    bc = load_module('final_shared_bc_adapter', ADAPTER)
    bc.WORK = WORK
    engine.IDS = IDS
    engine.CONFIG, engine.WORK, engine.MEDIA, engine.REPORT = CONFIG, WORK, MEDIA, REPORT
    shared_prepare, shared_plan, shared_encode = engine.prepare, engine.frame_plan, engine.encode_media
    shared_build = engine.build_frames

    def prepare(exercise, spec, config):
        if spec.get('sourceKind') == 'image-keyframes':
            return prepare_image_keys(engine, exercise, spec, config)
        if spec.get('sourceKind') == 'isometric-hold':
            return prepare_hold(engine, exercise, spec, config)
        if spec.get('sourceKind') == 'decimated-png-loop':
            return prepare_decimated(engine, exercise, spec, config)
        if spec['cycle'] == 'periodic':
            return shared_prepare(exercise, spec, config)
        return bc.prepare_selected_cells(engine, shared_prepare, exercise, spec, config)

    def frame_plan(spec):
        if spec.get('sourceKind') == 'isometric-hold':
            return [{'frame': i+1, 'phase': i/36, 'progress': 0.,
                     'anchor0': 0, 'anchor1': 0, 'timestep': 0., 'isometricHold': True}
                    for i in range(36)]
        if spec.get('sourceKind') == 'decimated-png-loop':
            return [{'frame': i+1, 'phase': i/36, 'progress': i/36,
                     'anchor0': i, 'anchor1': i, 'timestep': 0.,
                     'sampledFromSourceFrame': item['sourceFrame']}
                    for i, item in enumerate(spec['sourceFrames'])]
        plans = shared_plan(spec)
        if spec['cycle'] == 'periodic':
            for plan in plans:
                a, b = plan['anchor0'], plan['anchor1']
                if a != b and (spec['anchors'][a]['cell'] == spec['anchors'][b]['cell']
                                  and not spec['registration'].get('enabled', True)
                                  and spec['anchors'][a].get('translationPixels') == spec['anchors'][b].get('translationPixels')
                                  and not any('imageOverride' in spec['anchors'][x] for x in [a,b])):
                    plan.update({'anchor1': a, 'timestep': 0., 'identicalSourceHold': True})
        return plans

    def encode_media(selected, config, records):
        for exercise in selected:
            if records[exercise].get('frameSpecSha256') != frame_spec_digest(config['exercises'][exercise]):
                raise ValueError(f'{exercise}: frame-producing configuration differs from the reviewed build; regenerate/review this exercise first.')
        shared_encode(selected, config, records)
        manifest = engine.read_json(MEDIA/'manifest.json')
        for record in manifest['animations']:
            if record['id'] in selected:
                if config['exercises'][record['id']].get('sourceKind') == 'isometric-hold':
                    if record['gifFrames'] != 1 or record['gifDurationMilliseconds'] != 3000:
                        raise RuntimeError('Isometric GIF must represent one unchanged pose for the full 3 seconds.')
                    record['render'] = 'generated-static-hold'
                    record['gifFrameEmission'] = 'one stable source pose, held for 3000 ms; 36 identical video frames at 12 fps'
                else:
                    exact_gif_if_needed(engine, record['id'], record)
                records[record['id']]['encoded'] = record
        manifest['coverage'] = {'expectedAnimationCount': len(IDS),
                                'encodedAnimationCount': len(manifest['animations']),
                                'pendingIds': [i for i in IDS if i not in {a['id'] for a in manifest['animations']}],
                                'complete': len(manifest['animations']) == len(IDS)}
        manifest['gifTimingNote'] = ('Cumulative 80/90 ms rounding preserves the exact 12-fps loop duration. '
                                    'Identical hold frames are emitted explicitly if ordinary saving merges them; no image pixels are fabricated.')
        engine.write_json(MEDIA/'manifest.json', manifest)

    def build_frames(selected, specs, config, records, patch_overrides=False):
        blocked = [i for i in selected if not specs[i].get('motionReady', False)]
        if blocked:
            raise ValueError(f'Source anatomy/mechanics QA has not released frame generation for: {blocked}. Use --prepare-only first.')
        result = shared_build(selected, specs, config, records, patch_overrides)
        for exercise in selected:
            records[exercise]['frameSpecSha256'] = frame_spec_digest(specs[exercise])
            records[exercise]['frameGeneratorSha256'] = digest(Path(__file__))
        return result

    engine.prepare, engine.frame_plan, engine.encode_media = prepare, frame_plan, encode_media
    engine.build_frames = build_frames
    engine.__file__, engine.__doc__ = str(Path(__file__).resolve()), __doc__
    return engine


def main():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--exercise', default='all')
    args, _ = parser.parse_known_args()
    if '-h' in sys.argv or '--help' in sys.argv:
        configured_engine().main()
        return
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    selected = IDS if args.exercise == 'all' else [args.exercise]
    preserved = reviewed_inputs(config, selected)
    preserved.update({ENGINE: digest(ENGINE), ADAPTER: digest(ADAPTER)})
    engine = configured_engine()
    engine.main()
    for path, expected in preserved.items():
        if digest(path) != expected:
            raise RuntimeError(f'Read-only shared implementation/source changed: {path}')
    report = engine.read_json(REPORT)
    report['implementation'] = {'wrapper': engine.label(Path(__file__)), 'wrapperSha256': digest(Path(__file__)),
                              'sharedEngine': engine.label(ENGINE), 'sharedEngineSha256': preserved[ENGINE],
                              'selectionAdapter': engine.label(ADAPTER), 'selectionAdapterSha256': preserved[ADAPTER],
                              'extraInputs': {engine.label(p): sha for p,sha in preserved.items() if p not in [ENGINE,ADAPTER]}}
    report['method'].update({'conversion': 'Approved 72-frame loops use exact odd frame sampling at 12 fps, preserving the 3-second duration. Existing 480-square curl gets one documented 512-square normalization.',
                             'periodic': 'Lunge uses a 48-frame full alternating cycle with identical standing reference at anchors 0,8,15; 15-to-0 is an intentional short hold.',
                             'isometric': 'Plank depicts a stable isometric position. No repeated flexion or exaggerated breathing is invented.',
                             'sourceQA': 'Review projected limb ratios, joint landmarks, equipment rigidity and actual mechanics, in addition to frame continuity; 2D foreshortening is not a biomechanical measurement.'})
    attach_release_metadata(engine, report)
    engine.write_json(REPORT, report)


if __name__ == '__main__':
    main()
