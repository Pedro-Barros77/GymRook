"""Verify source preservation, mirrored loop and encoded media for the pilot.

These are production checks, not a certificate of anatomical correctness.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EXERCISE = 'reverse-cable-curl'
OUT = ROOT / 'output/generated-motion' / EXERCISE


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ROOT / 'backups/2d-v2-20261106/backup-manifest.json').read_text())
    original_count = 0
    for record in manifest['files']:
        relative = record['path']
        if relative.startswith(('dist/assets/animations/', 'docs/generated-frames/', 'docs/generated-frames-v2/')):
            assert digest(ROOT / relative) == record['sha256'], f'Original image changed: {relative}'
            original_count += 1
    report = json.loads((OUT / 'interpolation.json').read_text())
    preparation = json.loads((OUT / 'preparation.json').read_text())
    assert report['frameCount'] == 72 and report['fps'] == 24
    assert report['originalSourcesModified'] is False
    assert report['model'] == 'rife-v4.6'
    assert all(a < b for a, b in zip(report['referenceProgress'][:-1], report['referenceProgress'][1:])), 'Non-monotonic reference timing'
    frames = sorted((OUT / 'frames').glob('frame_*.png'))
    assert len(frames) == 72
    assert digest(frames[0]) == digest(OUT / 'anchors/anchor_00.png'), 'First reference pose was not preserved'
    assert digest(frames[36]) == digest(OUT / 'anchors/anchor_08.png'), 'Top reference pose was not preserved'
    for index, forward in enumerate(range(36, 1, -1), start=38):
        assert digest(OUT / 'frames' / f'frame_{index:04d}.png') == digest(OUT / 'frames' / f'frame_{forward:04d}.png'), 'Return must reuse the identical forward trajectory'
    images = [cv2.imread(str(path)) for path in frames]
    assert all(image is not None and image.shape == (480, 480, 3) for image in images)
    seam_difference = float(np.mean(np.abs(images[-1].astype('float32') - images[0].astype('float32'))))
    ordinary = [float(np.mean(np.abs(a.astype('float32') - b.astype('float32')))) for a, b in zip(images[:-1], images[1:])]
    assert seam_difference <= max(ordinary) * .45, 'Loop seam has an excessive image jump'
    print(f'{original_count} original media/source files unchanged; 72 frames and exact mirrored return verified.')
    print(f'Loop seam mean pixel difference: {seam_difference:.3f}; largest ordinary step: {max(ordinary):.3f}.')
    print('Registration scales: ' + ', '.join(f"{record['scale']:.4f}" for record in preparation['anchors']))
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify-3d.py'), '--folder', str(ROOT / 'dist/assets/animations-interpolated')], check=True)


if __name__ == '__main__':
    main()
