"""Verify all fourteen B/C animation assets and their reviewed source frames.

Uses the same decoding, integrity and continuity checks as the D verifier in an
isolated module instance. Technical checks do not validate exercise execution.
"""
from pathlib import Path
import importlib.util
import json


ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / 'dist/assets/animations-bc-v1'
SOURCES = ROOT / 'output/bc-animations'
IDS = (
    'machine-shoulder-press', 'dumbbell-lateral-raise', 'cable-front-raise',
    'dumbbell-shrug', 'reverse-pec-deck', 'standing-machine-calf-raise',
    'stair-calf-raise', 'lat-pulldown', 'unilateral-converging-row',
    'seated-cable-row', 'rope-triceps-pushdown',
    'dumbbell-lying-triceps-extension', 'bench-dip', 'machine-ab-crunch',
)


def main():
    spec = importlib.util.spec_from_file_location('bc_animation_verifier', ROOT / 'scripts/verify-leg-animations.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    # Change only this loaded instance; the D verifier and its files stay intact.
    verifier.MEDIA = MEDIA
    verifier.SOURCES = SOURCES
    manifest = json.loads((MEDIA / 'manifest.json').read_text(encoding='utf-8'))
    verifier.require(manifest['preferredFormat'] == 'MP4' and manifest['fps'] == 12,
                     'B/C manifest must specify MP4 and 12 fps')
    records = manifest['animations']
    verifier.require(len(records) == len(IDS), 'B/C manifest must contain exactly fourteen animations')
    by_id = {record['id']: record for record in records}
    verifier.require(len(by_id) == len(IDS) and set(by_id) == set(IDS),
                     'B/C manifest IDs must match the fourteen exercises exactly once')
    for exercise_id in IDS:
        record = by_id[exercise_id]
        verifier.require(record['fps'] == 12 and record['frameCount'] == 36 and record['durationSeconds'] == 3,
                         f'{exercise_id}: expected 36 frames at 12 fps over three seconds')
        verifier.require(record['width'] == 512 and record['height'] == 512,
                         f'{exercise_id}: expected 512 × 512 media')
        verifier.require(record['render'] == 'generated-interpolated',
                         f'{exercise_id}: expected generated-interpolated provenance')
        verifier.verify_files(record, exercise_id)
        frames = verifier.verify_sources(exercise_id, 36)
        verifier.verify_video(exercise_id, record, frames, 36)
        verifier.verify_gif_and_poster(exercise_id, record, frames, 36, 3000)
    print('B/C technical verification complete. Visually review movement, seams, anatomy and exercise execution with a qualified professional.')


if __name__ == '__main__':
    main()
