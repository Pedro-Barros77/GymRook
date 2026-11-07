"""Experimental RIFE interpolation of approved generated reference frames.

No Blender scene, new body model or independent image generation is used.
Forward references are reused exactly on return. Originals stay untouched.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import locale
import math
import shutil
import subprocess
import time
import cv2

ROOT = Path(__file__).resolve().parent.parent
EXERCISE = 'reverse-cable-curl'
# Approximate bar heights locate the actual metal shaft; Hough edges refine
# each value. These are visual retiming landmarks, not anatomical measurements.
BAR_HINTS = [284, 267, 249, 217, 204, 185, 171, 156, 146]


def locate_bar(image, expected):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    y0, y1 = max(0, expected - 12), min(gray.shape[0], expected + 13)
    crop = gray[y0:y1, 160:265]
    edges = cv2.Canny(crop, 35, 90)
    lines = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=24, minLineLength=44, maxLineGap=12)
    candidates = []
    if lines is not None:
        for x0, a, x1, b in lines.reshape(-1, 4):
            if abs(a - b) <= 2 and abs(x1 - x0) >= 44:
                height = y0 + (int(a) + int(b)) / 2
                candidates.append((abs(height - expected), -abs(x1 - x0), height))
    return min(candidates)[2] if candidates else float(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=ROOT / '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-ncnn-vulkan.exe')
    parser.add_argument('--model', type=Path, default=ROOT / '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-v4.6')
    parser.add_argument('--gpu', default='0')
    parser.add_argument('--timestep-decimal', choices=['auto', 'dot', 'comma'], default='auto')
    args = parser.parse_args()
    # The official Windows executable parses -s with locale-aware _wtof.
    # Match the OS decimal separator (pt-BR uses a comma); do not change files.
    previous_locale = locale.setlocale(locale.LC_NUMERIC)
    try:
        locale.setlocale(locale.LC_NUMERIC, '')
        separator = locale.localeconv()['decimal_point']
    finally:
        locale.setlocale(locale.LC_NUMERIC, previous_locale)
    if args.timestep_decimal != 'auto':
        separator = ',' if args.timestep_decimal == 'comma' else '.'
    if not args.binary.is_file() or not args.model.is_dir():
        parser.error('Official RIFE binary/model have not been prepared yet.')
    directory = ROOT / 'output/generated-motion' / EXERCISE
    anchors = [directory / 'anchors' / f'anchor_{index:02d}.png' for index in range(9)]
    if not all(path.is_file() for path in anchors):
        parser.error('Run python scripts/prepare-generated-motion.py first.')
    heights = [locate_bar(cv2.imread(str(path)), hint) for path, hint in zip(anchors, BAR_HINTS)]
    if not all(a > b for a, b in zip(heights[:-1], heights[1:])):
        raise ValueError(f'Bar trajectory must be visually monotonic before interpolation: {heights}')
    progress = [(heights[0] - y) / (heights[0] - heights[-1]) for y in heights]
    frames = directory / 'frames'
    frames.mkdir(exist_ok=True)
    records = []
    started = time.monotonic()
    for index in range(37):
        desired = (1 - math.cos(math.pi * index / 36)) / 2
        frame = frames / f'frame_{index + 1:04d}.png'
        if index in (0, 36):
            source_index = 0 if index == 0 else 8
            shutil.copy2(anchors[source_index], frame)
            records.append({'frame': index + 1, 'progress': desired, 'reference': source_index, 'interpolated': False})
            continue
        left = next(i for i in range(8) if progress[i] <= desired <= progress[i + 1])
        fraction = (desired - progress[left]) / (progress[left + 1] - progress[left])
        timestep = f'{fraction:.8f}'.replace('.', separator)
        command = [str(args.binary.resolve()), '-0', str(anchors[left]), '-1', str(anchors[left + 1]),
                   '-o', str(frame), '-m', str(args.model.resolve()), '-s', timestep, '-g', args.gpu,
                   '-j', '1:1:1', '-z']
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr[-3000:] or result.stdout[-3000:])
        if not frame.is_file():
            raise RuntimeError(f'Interpolator returned no output for frame {index + 1}')
        records.append({'frame': index + 1, 'progress': desired, 'references': [left, left + 1],
                        'timestep': fraction, 'interpolated': True})
        print(f'Forward {index + 1}/37 ready ({time.monotonic() - started:.1f}s)', flush=True)
    # 37 outward samples + the same35 interior samples in reverse = 72 frames.
    # Endpoints are never duplicated or independently regenerated.
    for offset, source_frame in enumerate(range(36, 1, -1), start=38):
        shutil.copy2(frames / f'frame_{source_frame:04d}.png', frames / f'frame_{offset:04d}.png')
        records.append({'frame': offset, 'reusesForwardFrame': source_frame, 'interpolated': False})
    spec = importlib.util.spec_from_file_location('gymrook_media_encoding', ROOT / 'scripts/encode-3d.py')
    encoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(encoder)
    target = ROOT / 'dist/assets/animations-interpolated'
    record = encoder.encode(EXERCISE, ROOT / 'output/generated-motion', target, 24, 72)
    record['render'] = 'generated-interpolated'
    record['reviewStatus'] = 'Experimental visual comparison; not validated as exercise instruction'
    manifest = {'pipeline': 'Original generated references → rigid stabilization → measured retiming → RIFE-v4.6 interpolation → exact mirrored return',
                'preferredFormat': 'MP4', 'fps': 24, 'animations': [record],
                'reviewStatus': record['reviewStatus']}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    report = {'exercise': EXERCISE, 'sourceReferences': [str(path.relative_to(ROOT)).replace('\\', '/') for path in anchors],
              'barHeights': heights, 'referenceProgress': progress, 'fps': 24, 'frameCount': 72,
              'frames': records, 'originalSourcesModified': False,
              'toolSha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
              'model': args.model.name, 'reviewStatus': record['reviewStatus']}
    (directory / 'interpolation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Experimental generated-motion pilot ready; original GIFs remain unchanged.', flush=True)


if __name__ == '__main__':
    main()
