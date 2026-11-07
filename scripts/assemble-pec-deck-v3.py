"""Mechanically assemble the isolated pec-deck perspective revision.

Default input: docs/generated-frames-v3/pec-deck.png (a 3x3 sprite sheet).
Default sequence: nine concentric poses and the exact seven return poses,
indices [0..8, 7..1], yielding 16 frames without regenerating the return.

This script crops, optionally translates, resizes and encodes existing art. It
does not generate images, interpolate anatomy, morph frames or alter equipment.
Only Pillow is required, unless --stabilize also requests NumPy/OpenCV.
"""
from pathlib import Path
from PIL import Image, ImageChops
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'dist/assets/animations'
QA = ROOT / 'output/pec-deck-v3'
REPORT = ROOT / 'docs/pec-deck-v3-build.json'
GIF_NAME = 'pec-deck-v3.gif'
POSTER_NAME = 'pec-deck-v3-poster.webp'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def parse_anchor(value):
    try:
        numbers = tuple(float(part) for part in value.split(','))
    except ValueError as error:
        raise argparse.ArgumentTypeError('Anchor must contain four numbers x0,y0,x1,y1.') from error
    if len(numbers) != 4 or not (0 <= numbers[0] < numbers[2] <= 1 and 0 <= numbers[1] < numbers[3] <= 1):
        raise argparse.ArgumentTypeError('Anchor must be normalized bounds within 0..1.')
    return numbers


def register(frame, reference, bounds, maximum_shift):
    """Rigid translation only, anchored to a static base/feet patch."""
    import cv2
    import numpy as np

    gray = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2GRAY)
    ref = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2GRAY)
    width, height = frame.size
    x0, y0, x1, y1 = [round(value * (width if index % 2 == 0 else height)) for index, value in enumerate(bounds)]
    sx0, sy0 = max(0, x0 - maximum_shift), max(0, y0 - maximum_shift)
    sx1, sy1 = min(width, x1 + maximum_shift), min(height, y1 + maximum_shift)
    template = ref[y0:y1, x0:x1]
    scores = cv2.matchTemplate(gray[sy0:sy1, sx0:sx1], template, cv2.TM_CCOEFF_NORMED)
    _, confidence, _, offset = cv2.minMaxLoc(scores)
    dx, dy = x0 - (sx0 + offset[0]), y0 - (sy0 + offset[1])
    accepted = confidence >= .75 and abs(dx) <= maximum_shift and abs(dy) <= maximum_shift
    if not accepted:
        dx = dy = 0
    aligned = Image.new('RGB', frame.size, frame.getpixel((2, 2)))
    aligned.paste(frame, (dx, dy))
    return aligned, {'dx': dx, 'dy': dy, 'confidence': round(float(confidence), 6), 'accepted': accepted}


def preserved_files(source):
    # Snapshot all existing GIFs outside this revision, including the generated
    # originals and any archived/interpolated trial. Also protect original art.
    paths = {path for path in (ROOT / 'dist/assets').rglob('*.gif') if path != OUTPUT / GIF_NAME}
    paths.add(source)
    paths.update(path for path in [ROOT / 'docs/generated-frames-v2/pec-deck.png',
                                  OUTPUT / 'pec-deck-poster.webp'] if path.is_file())
    return {label(path): {'bytes': path.stat().st_size, 'sha256': digest(path)} for path in sorted(paths)}


def verify_preserved(before):
    for name, expected in before.items():
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        if not path.is_file() or path.stat().st_size != expected['bytes'] or digest(path) != expected['sha256']:
            raise RuntimeError(f'An existing source/GIF changed during assembly: {name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'docs/generated-frames-v3/pec-deck.png')
    parser.add_argument('--grid', type=int, choices=[3, 4], default=3, help='Source-sheet rows/columns; the preferred nine-pose source uses 3.')
    parser.add_argument('--sequence', choices=['full16', 'mirrored9'], default='mirrored9')
    parser.add_argument('--forward-only', action='store_true', help='Alias for --sequence mirrored9; reuse the same poses for the return.')
    parser.add_argument('--poster-index', type=int, default=0, help='Source-cell index for the representative poster (default 0).')
    parser.add_argument('--size', type=int, default=480, help='Square output edge in pixels.')
    parser.add_argument('--stabilize', action='store_true', help='Optional rigid translation registration; never warps anatomy.')
    parser.add_argument('--anchor', type=parse_anchor, default=(.15, .82, .90, .98), help='Static base/feet patch as normalized x0,y0,x1,y1.')
    parser.add_argument('--max-shift', type=int, default=8, help='Maximum rigid registration shift at output size, in pixels.')
    parser.add_argument('--save-frames', action='store_true', help='Also write individual selected QA PNGs.')
    args = parser.parse_args()
    if args.size < 64 or args.max_shift < 0:
        parser.error('Size must be at least 64 pixels; max-shift must be nonnegative.')
    source = args.source if args.source.is_absolute() else ROOT / args.source
    if not source.is_file():
        parser.error(f'Source sheet is not available: {source}')
    sequence_name = 'mirrored9' if args.forward_only else args.sequence
    if sequence_name == 'full16' and args.grid != 4:
        parser.error('--sequence full16 requires --grid 4.')
    if not 0 <= args.poster_index < args.grid ** 2:
        parser.error('--poster-index must name an existing source cell.')
    indices = list(range(16)) if sequence_name == 'full16' else list(range(9)) + list(range(7, 0, -1))
    before = preserved_files(source)
    with Image.open(source) as opened:
        sheet = opened.convert('RGB')
    width, height = sheet.size
    if min(width, height) < 256:
        parser.error('The source sheet is too small to crop safely.')
    raw, boxes = [], []
    for index in range(args.grid ** 2):
        column, row = index % args.grid, index // args.grid
        # Rounded boundaries support 1254px, 1536px, or other generated edges.
        box = (round(column * width / args.grid) + 2, round(row * height / args.grid) + 2,
               round((column + 1) * width / args.grid) - 2, round((row + 1) * height / args.grid) - 2)
        boxes.append(list(box))
        raw.append(sheet.crop(box).resize((args.size, args.size), Image.Resampling.LANCZOS))
    aligned, registrations = [], []
    for index, frame in enumerate(raw):
        if args.stabilize and index:
            image, record = register(frame, raw[0], args.anchor, args.max_shift)
        else:
            image, record = frame, {'dx': 0, 'dy': 0, 'accepted': False, 'reason': 'reference' if index == 0 else 'disabled'}
        aligned.append(image)
        registrations.append(record)
    selected = [aligned[index] for index in indices]
    contact = Image.new('RGB', (args.size * 4, args.size * 4))
    for index, frame in enumerate(selected):
        contact.paste(frame, ((index % 4) * args.size, (index // 4) * args.size))
    palette = contact.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in selected]
    durations = [100] * 16
    durations[0] = durations[8] = 180
    QA.mkdir(parents=True, exist_ok=True)
    temporary = QA / GIF_NAME
    encoded[0].save(temporary, format='GIF', save_all=True, append_images=encoded[1:], duration=durations,
                    loop=0, optimize=False, disposal=2, include_color_table=False)
    decoded_delays = []
    with Image.open(temporary) as check:
        if check.n_frames != 16:
            raise RuntimeError(f'Encoding produced {check.n_frames} frames, expected 16; do not invent duplicate/noise frames to hide repeated poses.')
        if check.info.get('loop') != 0:
            raise RuntimeError('Expected repeating GIF playback.')
        for index, expected in enumerate(encoded):
            check.seek(index)
            if ImageChops.difference(check.convert('RGB'), expected.convert('RGB')).getbbox() is not None:
                raise RuntimeError(f'Palette/color mismatch after decoding frame {index}.')
            decoded_delays.append(check.info.get('duration', 0))
    if decoded_delays != durations:
        raise RuntimeError('GIF frame delays changed while encoding.')
    verify_preserved(before)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / GIF_NAME
    temporary.replace(target)
    poster = OUTPUT / POSTER_NAME
    aligned[args.poster_index].save(poster, quality=89, method=6)
    contact.save(QA / 'contact.png')
    if args.save_frames:
        frames_dir = QA / 'frames'
        frames_dir.mkdir(exist_ok=True)
        for index, frame in enumerate(selected, start=1):
            frame.save(frames_dir / f'frame_{index:04d}.png')
    verify_preserved(before)
    report = {
        'id': 'pec-deck', 'revision': 'v3', 'status': 'assembled-for-visual-review',
        'source': label(source), 'sourceSha256': digest(source), 'sourceSize': [width, height],
        'sourceGrid': [args.grid, args.grid], 'sourceCropBoxes': boxes, 'sequence': sequence_name,
        'sourceFrameIndices': indices, 'gifFrames': 16, 'frameSize': [args.size, args.size],
        'frameDelaysMilliseconds': durations, 'cycleMilliseconds': sum(durations),
        'posterSourceIndex': args.poster_index, 'palette': 'one shared 192-color palette, no dithering',
        'stabilization': {'enabled': args.stabilize, 'type': 'rigid translation only',
                          'anchor': list(args.anchor), 'maximumShiftPixels': args.max_shift, 'sourceFrames': registrations},
        'files': {label(path): {'bytes': path.stat().st_size, 'sha256': digest(path)} for path in [target, poster, QA / 'contact.png']},
        'preservedFiles': before, 'preservationVerified': True,
        'validation': 'GIF frame count, timing and decoded colors only; visual execution/perspective review remains necessary.'
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Pec deck v3: 16 frames, {sum(durations)} ms, {sequence_name}; {len(before)} prior sources/GIFs preserved.')
    print(label(target))
    print(label(QA / 'contact.png'))


if __name__ == '__main__':
    main()
