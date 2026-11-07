"""Crop generated nine-cell exercise sheets into reproducible card thumbnails.

The artwork is produced by the built-in image generator. This script only crops,
resizes and encodes the already generated panels; it does not invent the images.
"""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'docs' / 'generated-thumbnails'
OUT = ROOT / 'dist' / 'assets' / 'thumbnails'
PROMPTS = ROOT / 'docs' / 'prompts' / 'thumbnail-prompts.json'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads(PROMPTS.read_text(encoding='utf-8'))
    count = 0
    for sheet in spec['sheets']:
        image = Image.open(SOURCE / f"sheet-{sheet['sheet']}.png").convert('RGB')
        width, height = image.size
        assert len(sheet['ids']) == 9, 'A thumbnail sheet must have nine cells.'
        for index, exercise_id in enumerate(sheet['ids']):
            column, row = index % 3, index // 3
            # Rounded thirds also support image-generator outputs whose edge is
            # not divisible by three. Two pixels remove any incidental cell edge.
            bounds = (
                round(column * width / 3) + 2,
                round(row * height / 3) + 2,
                round((column + 1) * width / 3) - 2,
                round((row + 1) * height / 3) - 2,
            )
            panel = image.crop(bounds).resize((400, 400), Image.Resampling.LANCZOS)
            target = OUT / f'{exercise_id}.webp'
            panel.save(target, quality=87, method=6)
            with Image.open(target) as check:
                assert check.size == (400, 400)
                check.verify()
            count += 1
    print(f'{count} generated exercise thumbnails saved to {OUT}')


if __name__ == '__main__':
    main()
