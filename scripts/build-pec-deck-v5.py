"""Compose reviewed, fixed equipment layers over archived pec-deck v4 frames.

No interpolation or human generation runs here. All input images must already
be aligned at the output dimensions. Only explicit upper-machine masks change;
the outward sequence is then mirrored exactly. QA images show every transition
against its previous frame and the canonical closed reference.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import argparse
import hashlib
import importlib.util
import json
import math
import numpy as np
import shutil

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'output/pec-deck-v5'
TARGET = ROOT / 'dist/assets/animations-pec-deck-v5'
REPORT = ROOT / 'docs/pec-deck-v5-build.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve(value, config_path):
    path = Path(value)
    return (path if path.is_absolute() else config_path.parent / path).resolve()


def stamp(path):
    return {'file': label(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def unchanged(records):
    for record in records:
        path = ROOT / record['file']
        if not path.is_file() or stamp(path) != record:
            raise RuntimeError('Preserved v4/input file changed: ' + record['file'])


def image(path, size, rgba=False):
    with Image.open(path) as opened:
        if opened.size != size:
            raise ValueError(f'Asset must already be aligned at {size}: {path}')
        if rgba and 'A' not in opened.getbands():
            raise ValueError('Lever frames must contain an actual alpha channel: ' + str(path))
        return np.asarray(opened.convert('RGBA' if rgba else 'RGB')).copy()


def blend(base, layer, alpha):
    values = layer.astype(np.float32) * alpha[:, :, None] + base.astype(np.float32) * (1 - alpha[:, :, None])
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def static_layer(spec, config_path, size, protected_y):
    path = resolve(spec['file'], config_path)
    asset = image(path, size)
    width, height = size
    box = spec['regionPixels']
    if len(box) != 4 or any(not isinstance(value, int) for value in box):
        raise ValueError('Static-layer regionPixels must contain integer x0,y0,x1,y1.')
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= protected_y):
        raise ValueError('Static-layer region must stay inside the protected upper-machine boundary.')
    feather = float(spec.get('featherPixels', 1))
    if not math.isfinite(feather) or feather < 0 or feather > min(x1 - x0, y1 - y0) / 2:
        raise ValueError('Static-layer featherPixels must fit inside the region.')
    alpha = np.zeros((height, width), dtype=np.float32)
    local = np.ones((y1 - y0, x1 - x0), dtype=np.float32)
    if feather:
        xs = np.arange(x1 - x0, dtype=np.float32) + .5
        ys = np.arange(y1 - y0, dtype=np.float32) + .5
        distance = np.minimum(np.minimum(xs, x1 - x0 - xs)[None, :], np.minimum(ys, y1 - y0 - ys)[:, None])
        local = .5 - .5 * np.cos(np.pi * np.clip(distance / feather, 0, 1))
    alpha[y0:y1, x0:x1] = local
    paths = [path]
    mask_path = None
    if spec.get('maskFile'):
        mask_path = resolve(spec['maskFile'], config_path)
        with Image.open(mask_path) as opened:
            if opened.size != size:
                raise ValueError('Static-layer mask dimensions differ from the aligned frames.')
            mask = np.asarray(opened.convert('L'), dtype=np.float32) / 255
        alpha *= mask
        paths.append(mask_path)
    report = {'source': stamp(path), 'regionPixels': box, 'featherPixels': feather,
              'maskSource': stamp(mask_path) if mask_path else None,
              'alphaPixelSha256': hashlib.sha256(alpha.tobytes()).hexdigest(),
              'method': 'Fixed aligned source pixels; cosine alpha remains inside the declared region.'}
    return {'asset': asset, 'alpha': alpha, 'report': report, 'paths': paths}


def inputs(config, config_path):
    size = tuple(config.get('frameSize', [512, 512]))
    if len(size) != 2 or any(not isinstance(value, int) or value < 128 for value in size):
        raise ValueError('frameSize must contain two integer dimensions of at least 128.')
    protected_y = int(config.get('protectedBelowY', 164))
    if not 1 <= protected_y < size[1]:
        raise ValueError('protectedBelowY must be an output pixel row within the frame.')
    snapshot_path = resolve(config['baseSnapshotManifest'], config_path)
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    preserved = []
    for entry in snapshot['files']:
        archived = ROOT / entry['backup']
        record = stamp(archived)
        if record['bytes'] != entry['bytes'] or record['sha256'] != entry['sha256']:
            raise RuntimeError('Archived v4 snapshot failed its hash check: ' + str(archived))
        preserved.append(record)
    frames_dir = resolve(config['baseFrames'], config_path)
    base_paths = [frames_dir / f'frame_{frame:04d}.png' for frame in range(1, 38)]
    snapshot_files = {record['file']: record['sha256'] for record in preserved}
    for path in base_paths:
        if label(path) not in snapshot_files:
            raise ValueError('Each base frame must come from the verified archived snapshot: ' + str(path))
    base_report_path = resolve(config['baseReport'], config_path)
    base_report = json.loads(base_report_path.read_text(encoding='utf-8'))
    if base_report.get('frameCount') != 72 or base_report.get('fps') != 24:
        raise ValueError('Base report must describe the archived 72-frame, 24 fps v4 sequence.')
    canonical_path = base_paths[-1]
    canonical = image(canonical_path, size)
    clean = static_layer(config['cleanPlate'], config_path, size, protected_y)
    foreground = [static_layer(spec, config_path, size, protected_y) for spec in config.get('foregroundLayers', [])]
    lever_spec = config['leverFrames']
    lever_dir = resolve(lever_spec['directory'], config_path)
    lever_paths = [lever_dir / lever_spec.get('pattern', 'frame_{frame:04d}.png').format(frame=frame) for frame in range(1, 38)]
    for path in lever_paths:
        if not path.is_file():
            raise FileNotFoundError('Reviewed rigid-lever frame is not ready: ' + str(path))
        rgba = image(path, size, rgba=True)
        if np.any(rgba[protected_y:, :, 3]):
            raise ValueError('Rigid-lever source alpha crosses protected human/handle rows: ' + str(path))
    new_paths = [config_path, snapshot_path, base_report_path, *clean['paths'], *lever_paths,
                 *(path for layer in foreground for path in layer['paths'])]
    cleanup = None
    if config.get('cleanupFrames'):
        cleanup_spec = config['cleanupFrames']
        cleanup_dir = resolve(cleanup_spec['directory'], config_path)
        cleanup_paths = [cleanup_dir / cleanup_spec.get('pattern', 'frame_{frame:04d}.png').format(frame=frame) for frame in range(1, 38)]
        for path in cleanup_paths:
            rgba = image(path, size, rgba=True)
            if np.any(rgba[protected_y:, :, 3]):
                raise ValueError('Cleanup alpha crosses protected human/handle rows: ' + str(path))
        cleanup = {'paths': cleanup_paths, 'manifest': None,
                   'method': 'Reviewed per-frame RGBA cleanup, applied before the fixed column and rigid equipment; only source alpha pixels may change.'}
        new_paths.extend(cleanup_paths)
        if cleanup_spec.get('manifest'):
            manifest_path = (cleanup_dir / cleanup_spec['manifest']).resolve()
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if manifest.get('frameCount') != 37 or manifest.get('frameSize') != list(size):
                raise ValueError('Cleanup manifest must describe 37 aligned frames at the configured size.')
            manifested = {entry['frame']: entry for entry in manifest.get('frames', [])}
            if len(manifest.get('frames', [])) != 37 or set(manifested) != set(range(1, 38)):
                raise ValueError('Cleanup manifest must contain each outward frame exactly once.')
            for frame, cleanup_path in enumerate(cleanup_paths, start=1):
                entry = manifested[frame]
                if (manifest_path.parent / entry['file']).resolve() != cleanup_path.resolve() or entry['sha256'] != sha(cleanup_path):
                    raise RuntimeError('Cleanup manifest source/hash mismatch in frame ' + str(frame))
            cleanup['manifest'] = {'source': stamp(manifest_path), 'data': manifest}
            new_paths.append(manifest_path)
    gear_manifest = None
    if lever_spec.get('manifest'):
        path = resolve(lever_spec['manifest'], config_path)
        gear_manifest = {'source': stamp(path), 'data': json.loads(path.read_text(encoding='utf-8'))}
        new_paths.append(path)
        manifest = gear_manifest['data']
        if manifest.get('frameCount') != 37 or manifest.get('frameSize') != list(size):
            raise ValueError('Rigid-lever manifest must describe 37 aligned frames at the configured size.')
        manifested = {entry['frame']: entry for entry in manifest.get('frames', [])}
        if len(manifest.get('frames', [])) != 37 or set(manifested) != set(range(1, 38)):
            raise ValueError('Rigid-lever manifest must contain each outward frame exactly once.')
        for frame, lever_path in enumerate(lever_paths, start=1):
            entry = manifested[frame]
            described = (path.parent / entry['file']).resolve()
            if described != lever_path.resolve() or entry['sha256'] != sha(lever_path):
                raise RuntimeError('Rigid-lever manifest source/hash mismatch in frame ' + str(frame))
        if manifest.get('metadata'):
            metadata_path = (path.parent / manifest['metadata']).resolve()
            gear_manifest['metadata'] = {'source': stamp(metadata_path),
                                         'data': json.loads(metadata_path.read_text(encoding='utf-8'))}
            new_paths.append(metadata_path)
        if manifest.get('sourceTexture'):
            texture_path = (path.parent / manifest['sourceTexture']).resolve()
            texture_record = stamp(texture_path)
            if texture_record['sha256'] != manifest.get('sourceTextureSha256'):
                raise RuntimeError('Rigid-lever material atlas does not match the manifest hash.')
            gear_manifest['sourceTexture'] = texture_record
            new_paths.append(texture_path)
    preserved.extend(stamp(path) for path in sorted(set(new_paths)))
    return size, protected_y, base_paths, base_report, canonical, clean, foreground, lever_paths, gear_manifest, cleanup, preserved


def qa_panel(path, previous, current, title, crop_y):
    # Explicit onion skin is a diagnostic, not an inferred motion correction.
    a, b = previous[:crop_y], current[:crop_y]
    onion = np.rint(a.astype(np.float32) * .5 + b.astype(np.float32) * .5).astype(np.uint8)
    strip = Image.new('RGB', (a.shape[1] * 3, crop_y + 24), 'white')
    draw = ImageDraw.Draw(strip)
    draw.text((7, 5), title + ' | reference / 50% onion / current', fill='black')
    for index, array in enumerate([a, onion, b]):
        strip.paste(Image.fromarray(array), (index * a.shape[1], 24))
    strip.save(path)


def encode(report):
    spec = importlib.util.spec_from_file_location('gymrook_v5_encoder', ROOT / 'scripts/encode-3d.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = module.encode('pec-deck-v5', ROOT / 'output', TARGET, 24, 72)
    files = {}
    for field in ['video', 'gif', 'poster']:
        old = record[field]
        new = old.replace('pec-deck-v5', 'pec-deck', 1)
        (TARGET / old).replace(TARGET / new)
        record[field] = new
        files[new] = record['files'][old]
    record.update({'files': files, 'id': 'pec-deck', 'render': 'generated-interpolated',
                   'reviewStatus': report['reviewStatus']})
    manifest = {'pipeline': 'Archived v4 motion → selective old-metal cleanup → fixed column → equipment-only rigid layers → fixed foreground caps → exact mirrored return',
                'preferredFormat': 'MP4', 'fps': 24, 'animations': [record], 'reviewStatus': report['reviewStatus'],
                'structure': {'cleanPlate': report['cleanPlate'], 'foregroundLayers': report['foregroundLayers'],
                              'cleanupFrames': report['cleanupFrames'],
                              'leverManifest': report['leverManifest'], 'protectedBelowY': report['protectedBelowY']}}
    (TARGET / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'docs/generated-frames-v5/pec-deck/structure.json')
    parser.add_argument('--prepare-only', action='store_true', help='Validate/hash all source assets without composing frames.')
    parser.add_argument('--no-encode', action='store_true', help='Compose PNGs and QA images for review without producing video/GIF.')
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    size, protected_y, base_paths, base_report, canonical, clean, foreground, lever_paths, gear_manifest, cleanup, preserved = inputs(config, config_path)
    report = {'id': 'pec-deck', 'revision': 'v5', 'status': 'inputs-validated', 'config': label(config_path),
              'frameSize': list(size), 'fps': 24, 'frameCount': 72, 'durationSeconds': 3,
              'protectedBelowY': protected_y, 'baseRevision': 'v4', 'baseInterpolation': base_report.get('interpolation', {}),
              'cleanPlate': clean['report'], 'foregroundLayers': [layer['report'] for layer in foreground],
              'cleanupFrames': {'method': cleanup['method'], 'manifest': cleanup['manifest']} if cleanup else None,
              'leverManifest': gear_manifest, 'preservedInputs': preserved,
              'reviewStatus': 'Experimental equipment continuity review; human exercise execution is not validated.'}
    try:
        if args.prepare_only:
            unchanged(preserved)
            report['preservationVerified'] = True
            REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print('Pec deck v5: aligned inputs and archived v4 hashes validated; no composition performed.')
            return
        frames_dir, qa_dir = WORK / 'frames', WORK / 'qa'
        frames_dir.mkdir(parents=True, exist_ok=True)
        qa_dir.mkdir(parents=True, exist_ok=True)
        calls, forward = [], []
        for index, (base_path, lever_path) in enumerate(zip(base_paths, lever_paths), start=1):
            before, gear = image(base_path, size), image(lever_path, size, rgba=True)
            gear_alpha = gear[:, :, 3].astype(np.float32) / 255
            if np.any(gear_alpha[protected_y:] > 0):
                raise ValueError(f'Lever frame {index} extends into protected human/handle rows y>={protected_y}.')
            result = before
            cleanup_alpha = np.zeros(before.shape[:2], dtype=np.float32)
            cleanup_source = None
            if cleanup:
                cleanup_path = cleanup['paths'][index - 1]
                cleanup_image = image(cleanup_path, size, rgba=True)
                cleanup_alpha = cleanup_image[:, :, 3].astype(np.float32) / 255
                result = blend(result, cleanup_image[:, :, :3], cleanup_alpha)
                nonzero_cleanup = np.argwhere(cleanup_alpha > 0)
                cleanup_source = {'source': stamp(cleanup_path),
                                  'alphaPixelSha256': hashlib.sha256(cleanup_image[:, :, 3].tobytes()).hexdigest(),
                                  'alphaNonzeroPixelCount': int(np.count_nonzero(cleanup_alpha)),
                                  'alphaBounds': [int(nonzero_cleanup[:, 1].min()), int(nonzero_cleanup[:, 0].min()),
                                                  int(nonzero_cleanup[:, 1].max() + 1), int(nonzero_cleanup[:, 0].max() + 1)] if len(nonzero_cleanup) else None}
            result = blend(result, clean['asset'], clean['alpha'])
            result = blend(result, gear[:, :, :3], gear_alpha)
            union = (cleanup_alpha > 0) | (clean['alpha'] > 0) | (gear_alpha > 0)
            foreground_union = np.zeros_like(union)
            for layer in foreground:
                result = blend(result, layer['asset'], layer['alpha'])
                union |= layer['alpha'] > 0
                foreground_union |= layer['alpha'] > 0
            foreground_errors = []
            later_foreground = np.zeros_like(union)
            for layer in reversed(foreground):
                visible = (layer['alpha'] == 1) & ~later_foreground
                error = int(np.abs(result.astype(np.int16) - layer['asset'].astype(np.int16))[visible].max()) if np.any(visible) else 0
                foreground_errors.insert(0, error)
                later_foreground |= layer['alpha'] > 0
            difference = np.abs(result.astype(np.int16) - before.astype(np.int16))
            outside_error = int(difference[~union].max()) if np.any(~union) else 0
            protected_error = int(difference[protected_y:].max())
            fixed_visible = (clean['alpha'] == 1) & (gear_alpha == 0) & ~foreground_union
            fixed_error = int(np.abs(result.astype(np.int16) - clean['asset'].astype(np.int16))[fixed_visible].max()) if np.any(fixed_visible) else 0
            if outside_error or protected_error or fixed_error or any(foreground_errors):
                raise RuntimeError(f'Equipment composition violated exact pixel preservation in frame {index}.')
            output = frames_dir / f'frame_{index:04d}.png'
            Image.fromarray(result).save(output)
            canonical_qa = qa_dir / f'canonical_{index:04d}.png'
            qa_panel(canonical_qa, canonical, result, f'Closed canonical vs frame {index:02d}', protected_y)
            transition_qa = None
            if forward:
                transition_qa = qa_dir / f'transition_{index - 1:04d}_{index:04d}.png'
                qa_panel(transition_qa, forward[-1], result, f'Previous {index - 1:02d} vs frame {index:02d}', protected_y)
            nonzero = np.argwhere(union)
            bounds = [int(nonzero[:, 1].min()), int(nonzero[:, 0].min()), int(nonzero[:, 1].max() + 1), int(nonzero[:, 0].max() + 1)] if len(nonzero) else None
            calls.append({'frame': index, 'source': stamp(base_path), 'leverSource': stamp(lever_path),
                          'cleanupSource': cleanup_source,
                          'maskOutputBounds': bounds, 'sha256': sha(output),
                          'differingPixelCount': int(np.count_nonzero(np.any(difference > 0, axis=2))),
                          'outsideMasksMaximumPixelError': outside_error, 'protectedBodyMaximumPixelError': protected_error,
                          'unoccludedFixedPlateMaximumPixelError': fixed_error,
                          'unoccludedForegroundMaximumPixelErrors': foreground_errors,
                          'canonicalOnionQa': label(canonical_qa), 'previousFrameOnionQa': label(transition_qa) if transition_qa else None})
            forward.append(result)
            print(f'Pec deck v5: composed, onion QA prepared {index}/37', flush=True)
        for frame, source in enumerate(range(36, 1, -1), start=38):
            src, dst = frames_dir / f'frame_{source:04d}.png', frames_dir / f'frame_{frame:04d}.png'
            shutil.copy2(src, dst)
            if sha(src) != sha(dst):
                raise RuntimeError('Mirrored return failed its byte equality check.')
            calls.append({'frame': frame, 'reusesForwardFrame': source, 'sha256': sha(dst)})
        unchanged(preserved)
        report.update({'frames': calls, 'exactMirroredReturn': True, 'preservationVerified': True,
                       'qa': {'canonicalComparisons': 37, 'consecutiveComparisons': 36,
                              'directory': label(qa_dir), 'visualReviewRequired': True},
                       'status': 'composed-for-visual-review'})
        if not args.no_encode:
            report['manifest'] = encode(report)
            report['status'] = 'encoded-for-visual-review'
        unchanged(preserved)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Pec deck v5: prior v4/input files preserved; all upper-machine comparisons require visual review.')
    except Exception as error:
        report.update({'status': 'needs-review', 'error': str(error)})
        unchanged(preserved)
        report['preservationVerified'] = True
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
