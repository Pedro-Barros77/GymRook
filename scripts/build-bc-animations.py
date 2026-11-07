"""Prepare and encode the fourteen B/C exercise loops at 12 fps.

Examples:
  python scripts/build-bc-animations.py --prepare-only
  python scripts/build-bc-animations.py --exercise lat-pulldown --no-encode
  python scripts/build-bc-animations.py --encode-only
  python scripts/build-bc-animations.py --exercise lat-pulldown --patch-overrides

This adapter reuses the validated D pipeline without changing its source,
configuration, output frames, or media. Source readiness is controlled by
prepareReady in the B/C config; source release is independent of this adapter.
"""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
import argparse
import hashlib
import importlib.util
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT/'scripts/build-leg-animations.py'
CONFIG = ROOT/'docs/generated-frames-bc-v1/config.json'
WORK = ROOT/'output/bc-animations'
MEDIA = ROOT/'dist/assets/animations-bc-v1'
REPORT = ROOT/'docs/bc-animations-v1-build.json'
IDS = (
    'machine-shoulder-press', 'dumbbell-lateral-raise', 'cable-front-raise',
    'dumbbell-shrug', 'reverse-pec-deck', 'standing-machine-calf-raise',
    'stair-calf-raise', 'lat-pulldown', 'unilateral-converging-row',
    'seated-cable-row', 'rope-triceps-pushdown',
    'dumbbell-lying-triceps-extension', 'bench-dip', 'machine-ab-crunch',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extra_input_snapshot(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--exercise', default='all')
    args, _ = parser.parse_known_args(argv)
    if '-h' in argv or '--help' in argv:
        return {}
    import json
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    selected = IDS if args.exercise == 'all' else [args.exercise]
    inputs = {}
    for exercise in selected:
        for anchor in config['exercises'][exercise]['anchors']:
            if 'imageOverride' not in anchor:
                continue
            path = Path(anchor['imageOverride'])
            path = path if path.is_absolute() else ROOT/path
            expected = anchor.get('imageOverrideSha256')
            if not expected or digest(path) != expected:
                raise ValueError(f'Extra reference SHA-256 mismatch: {path}')
            inputs[path] = expected
    return inputs


def prepare_selected_cells(engine, shared_prepare, exercise, spec, config):
    """Extract the canonical grid, then select/reindex reviewed source cells."""
    cells = [a['cell'] for a in spec['anchors']]
    if (not 3 <= len(cells) <= 9 or len(set(cells)) != len(cells)
            or any(not isinstance(cell, int) or not 0 <= cell < 9 for cell in cells)):
        raise ValueError('B/C requires 3..9 unique source-cell slots; progress declares the reference order.')
    progress = [float(a['progress']) for a in spec['anchors']]
    if progress[0] != 0 or progress[-1] != 1 or any(b <= a for a, b in zip(progress, progress[1:])):
        raise ValueError('Selected source progress must strictly increase from zero to one.')
    if spec.get('selectedCells', cells) != cells or spec.get('activeCells', cells) != cells:
        raise ValueError('Selected/active cell metadata does not match the actual anchor mapping.')
    extraction = deepcopy(spec)
    by_cell = {a['cell']: a for a in spec['anchors']}
    extraction['anchors'] = [{**by_cell.get(cell, {}), 'cell': cell, 'progress': cell/8} for cell in range(9)]
    extraction['referenceIndex'] = cells[spec.get('referenceIndex', 0)]
    if 'imageOverride' in spec['anchors'][spec.get('referenceIndex', 0)]:
        raise ValueError('The fixed registration reference must remain an original source-sheet cell.')
    record = shared_prepare(exercise, extraction, config)
    source_anchors = record['anchors']
    archive = WORK/exercise/'qa/excluded-source-cells'
    excluded = []
    overridden_cells = {a['cell'] for a in spec['anchors'] if 'imageOverride' in a}
    for cell in sorted((set(range(9))-set(cells)) | overridden_cells):
        rejected = source_anchors[cell]
        archive.mkdir(parents=True, exist_ok=True)
        archived = {}
        for field, sha_field in [('file', 'sha256'), ('raw', 'rawSha256')]:
            source = engine.project_path(rejected[field])
            target = archive/f'cell_{cell:02d}-{field}-{rejected[sha_field][:12]}.png'
            shutil.copyfile(source, target)
            if digest(target) != rejected[sha_field]:
                raise RuntimeError('Excluded-cell archival hash changed.')
            archived[field] = engine.label(target)
        reason = spec.get('excludedCellReasons', {}).get(str(cell), spec.get('excludedCellReason', 'Reviewed source-cell exclusion'))
        excluded.append({'cell': cell, 'originalCellOverridden': cell in overridden_cells, 'reason': reason, **archived,
                         'sha256': rejected['sha256'], 'rawSha256': rejected['rawSha256']})
    # Read all selected bytes before overwriting indices: selected cell3 can
    # become active anchor1 without destroying a later source candidate.
    payloads, overrides = [], []
    reference = engine.np.asarray(engine.Image.open(engine.project_path(
        source_anchors[extraction['referenceIndex']]['file'])).convert('RGB'))
    for selected in spec['anchors']:
        anchor = deepcopy(source_anchors[selected['cell']])
        if 'imageOverride' not in selected:
            payloads.append((anchor, engine.project_path(anchor['file']).read_bytes(),
                             engine.project_path(anchor['raw']).read_bytes()))
            continue
        path = engine.project_path(selected['imageOverride'])
        if digest(path) != selected['imageOverrideSha256']:
            raise ValueError(f'Reviewed image override changed: {path}')
        with engine.Image.open(path) as opened:
            if opened.mode != 'RGB' or opened.size != (512, 512):
                raise ValueError('An image override must be a reviewed RGB512 PNG; no implicit resizing.')
            image = engine.np.asarray(opened).copy()
        aligned, registration = engine.translation_only(reference, image, spec.get('registration', {}), selected)
        encoded = BytesIO()
        engine.Image.fromarray(aligned).save(encoded, format='PNG')
        raw_bytes, aligned_bytes = path.read_bytes(), encoded.getvalue()
        input_record = {'cellSlot': selected['cell'], 'file': engine.label(path), 'sha256': digest(path),
                        'sourceType': 'reviewed-external-image-override', 'reason': selected.get('overrideReason', '')}
        anchor.update({'cropPixels': None, 'sha256': hashlib.sha256(aligned_bytes).hexdigest(),
                       'rawSha256': hashlib.sha256(raw_bytes).hexdigest(), 'registration': registration,
                       'imageOverride': input_record})
        payloads.append((anchor, aligned_bytes, raw_bytes))
        overrides.append(input_record)
    record['anchors'] = []
    for index, (selected, (anchor, image_bytes, raw_bytes)) in enumerate(zip(spec['anchors'], payloads)):
        image_path = WORK/exercise/'anchors'/f'anchor_{index:02d}.png'
        raw_path = WORK/exercise/'anchors/raw'/f'anchor_{index:02d}.png'
        image_path.write_bytes(image_bytes)
        raw_path.write_bytes(raw_bytes)
        anchor.update({'index': index, 'progress': selected['progress'],
                       'file': engine.label(image_path), 'raw': engine.label(raw_path)})
        if digest(image_path) != anchor['sha256'] or digest(raw_path) != anchor['rawSha256']:
            raise RuntimeError('Selected source pixels changed during active-anchor reindexing.')
        record['anchors'].append(anchor)
    for index in range(len(cells), 9):
        for directory in [WORK/exercise/'anchors', WORK/exercise/'anchors/raw']:
            path = directory/f'anchor_{index:02d}.png'
            if not path.resolve().is_relative_to((WORK/exercise).resolve()):
                raise RuntimeError('Retired derived-anchor path escaped the exercise output directory.')
            path.unlink()
    record['sourceCellSelection'] = {
        'extractedCellCount': 9, 'selectedCells': cells, 'activeCells': cells, 'excludedCells': excluded,
        'originalSheetCellsUsed': [cell for cell in cells if cell not in overridden_cells],
        'imageOverrides': overrides,
    }
    record.update({'selectedCells': cells, 'activeCells': cells, 'referenceIndex': spec.get('referenceIndex', 0)})
    if 'timingEvidence' in spec:
        record['timingEvidence'] = spec['timingEvidence']
    images = [engine.np.asarray(engine.Image.open(engine.project_path(a['file'])).convert('RGB'))
              for a in record['anchors']]
    qa = WORK/exercise/'qa'
    engine.contact(images, [f"P{a['index']:02d} C{a['cell']} | progress {a['progress']:.4f}" for a in record['anchors']],
                   qa/'anchors-contact.png')
    engine.onions(images, qa/'anchors-onions.png')
    engine.write_json(WORK/exercise/'prepare.json', record)
    return record


def configured_engine():
    """Load a separate module instance; parameterize that instance only."""
    spec = importlib.util.spec_from_file_location('bc_animation_engine', ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.IDS = IDS
    engine.CONFIG, engine.WORK, engine.MEDIA, engine.REPORT = CONFIG, WORK, MEDIA, REPORT
    shared_prepare = engine.prepare
    engine.prepare = lambda exercise, spec, config: prepare_selected_cells(
        engine, shared_prepare, exercise, spec, config)
    # The shared main records this wrapper as the invoked generator. Its actual
    # implementation is identified separately by the immutable engine hash.
    engine.__file__, engine.__doc__ = str(Path(__file__).resolve()), __doc__
    return engine


def main():
    engine_hash = digest(ENGINE)
    extra_inputs = extra_input_snapshot(sys.argv[1:])
    engine = configured_engine()
    engine.main()
    if digest(ENGINE) != engine_hash:
        raise RuntimeError('The shared D implementation changed during processing.')
    for path, expected in extra_inputs.items():
        if digest(path) != expected:
            raise RuntimeError(f'Extra reviewed reference changed during processing: {path}')
    report = engine.read_json(REPORT)
    report['implementation'] = {
        'wrapper': 'scripts/build-bc-animations.py',
        'wrapperSha256': digest(Path(__file__)),
        'sharedEngine': 'scripts/build-leg-animations.py',
        'sharedEngineSha256': engine_hash,
        'extraInputs': {engine.label(path): expected for path, expected in extra_inputs.items()},
        'parameterization': {
            'exerciseIds': list(IDS), 'config': engine.label(CONFIG),
            'work': engine.label(WORK), 'media': engine.label(MEDIA),
            'report': engine.label(REPORT),
        },
    }
    report['method']['pingPong'] = (
        '19 forward frames using each exercise\'s configured cosine or linear '
        'phase progress, then byte-exact copies of forward frames 18..2.'
    )
    report['method'].pop('periodic', None)
    engine.write_json(REPORT, report)


if __name__ == '__main__':
    main()
