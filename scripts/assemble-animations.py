"""Assemble generated 4x4 motion sheets into 16-frame colored GIFs.

Only mechanical crop, small translation registration, resizing and encoding happen
here. No independent re-generation, optical-flow morphs or crossfades.
Rebuild: python scripts/assemble-animations.py
Build dependencies: Pillow, numpy, opencv-python-headless (not used by the PWA).
"""
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import json

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs' / 'generated-frames-v2'
OUT = ROOT / 'dist' / 'assets' / 'animations'
OUT.mkdir(parents=True, exist_ok=True)

# Static shoes/base areas correct small crop/camera translations. Moving joints,
# machine levers and selected weight blocks are never registration anchors.
ANCHORS = {
    'incline-dumbbell-press': (.05, .79, .53, .97),
    'pec-deck': (.28, .81, .89, .97),
    'push-up': (.84, .77, .98, .86),
    'reverse-cable-curl': (.18, .81, .55, .98),
}
SIDE = 480


def register(frame, reference, bounds):
    """Translate the complete frame by at most 10 source pixels; no shape warps."""
    gray = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2GRAY)
    ref = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    x0, y0, x1, y1 = [round(value * (w if i % 2 == 0 else h)) for i, value in enumerate(bounds)]
    radius = 10
    sx0, sy0 = max(0, x0 - radius), max(0, y0 - radius)
    sx1, sy1 = min(w, x1 + radius), min(h, y1 + radius)
    scores = cv2.matchTemplate(gray[sy0:sy1, sx0:sx1], ref[y0:y1, x0:x1], cv2.TM_CCOEFF_NORMED)
    _, confidence, _, offset = cv2.minMaxLoc(scores)
    dx, dy = x0 - (sx0 + offset[0]), y0 - (sy0 + offset[1])
    if confidence < .72 or abs(dx) > radius or abs(dy) > radius:
        return frame, {'dx': 0, 'dy': 0, 'confidence': round(confidence, 4), 'registered': False}
    aligned = Image.new('RGB', frame.size, tuple(frame.getpixel((3, 3))))
    aligned.paste(frame, (dx, dy))
    return aligned, {'dx': dx, 'dy': dy, 'confidence': round(confidence, 4), 'registered': True}


report = []
for name, anchor in ANCHORS.items():
    sheet = Image.open(SOURCE / (name + '.png')).convert('RGB')
    width, height = sheet.size
    raw = []
    for index in range(16):
        column, row = index % 4, index // 4
        # Generated images may have an edge not divisible by four.
        box = (round(column * width / 4) + 2, round(row * height / 4) + 2,
               round((column + 1) * width / 4) - 2, round((row + 1) * height / 4) - 2)
        raw.append(sheet.crop(box).resize((312, 312), Image.Resampling.LANCZOS))
    frames, registrations = [], []
    for frame in raw:
        aligned, registration = register(frame, raw[0], anchor)
        frames.append(aligned.resize((SIDE, SIDE), Image.Resampling.LANCZOS))
        registrations.append(registration)
    # One shared palette without frame-local dithering or re-quantization avoids
    # introducing changing speckle/color tables into the generated illustration.
    contact = Image.new('RGB', (SIDE * 4, SIDE * 4))
    for index, frame in enumerate(frames):
        contact.paste(frame, ((index % 4) * SIDE, (index // 4) * SIDE))
    palette = contact.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [100] * 16
    durations[0] = durations[8] = 180
    destination = OUT / (name + '.gif')
    quantized[0].save(destination, save_all=True, append_images=quantized[1:], duration=durations,
                      loop=0, optimize=False, disposal=2, include_color_table=False)
    frames[0].save(OUT / (name + '-poster.webp'), quality=89, method=6)
    with Image.open(destination) as check:
        assert check.n_frames == 16, f'{name}: expected 16 real GIF frames, got {check.n_frames}'
        assert check.info.get('loop') == 0, f'{name}: expected repeating playback'
        for index, expected in enumerate(quantized):
            check.seek(index)
            decoded = np.asarray(check.convert('RGB')).astype('int16')
            error = np.abs(decoded - np.asarray(expected.convert('RGB')).astype('int16')).mean()
            assert error < .01, f'{name}: encoded frame {index} changed its palette/colors'
    report.append({'id': name, 'source': f'docs/generated-frames-v2/{name}.png', 'sourceFramesUsed': list(range(16)),
                   'gifFrames': 16, 'bytes': destination.stat().st_size, 'cycleMilliseconds': sum(durations),
                   'palette': 'one shared 192-color palette, no dithering', 'registrations': registrations})
    # Compact source contact sheet for QA, excluded from the published site.
    qa = ROOT / 'output' / 'animation-qa'
    qa.mkdir(parents=True, exist_ok=True)
    contact.resize((960, 960), Image.Resampling.LANCZOS).save(qa / (name + '.jpg'), quality=91)

(ROOT / 'docs' / 'animation-build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
for item in report:
    print(f"{item['id']}: {item['gifFrames']} frames, {item['bytes'] / 1024:.0f} KiB, {item['cycleMilliseconds']} ms")
