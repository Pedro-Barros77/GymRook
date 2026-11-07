"""Verify encoded Blender animations, exact MP4 frame count and 24-fps metadata."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
from PIL import Image
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent


def verify(record, folder):
    assert record['frameCount'] == 72 and record['fps'] == 24, f"{record['id']}: expected 72 frames / 24 fps"
    assert record['durationSeconds'] == 3, f"{record['id']}: expected a three-second cycle"
    for filename, expected in record['files'].items():
        path = folder / filename
        assert path.is_file(), f'Missing {path}'
        assert path.stat().st_size == expected['bytes'], f'Size changed: {path}'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256'], f'Hash changed: {path}'
    with Image.open(folder / record['gif']) as gif:
        assert gif.n_frames == record['gifFrames'], f"{record['id']}: GIF frame count mismatch"
        assert gif.size == (record['width'], record['height']), f"{record['id']}: GIF dimensions mismatch"
        durations = []
        first = gif.convert('RGB').tobytes()
        movement = False
        for index in range(gif.n_frames):
            gif.seek(index)
            durations.append(gif.info.get('duration', 0))
            movement = movement or gif.convert('RGB').tobytes() != first
        assert movement, f"{record['id']}: GIF has no motion"
        assert sum(durations) == 3000, f"{record['id']}: GIF cycle must be exactly three seconds"
        assert durations == record['gifFrameDelaysMilliseconds'], f"{record['id']}: GIF delays changed"
    with Image.open(folder / record['poster']) as image:
        assert image.size == (record['width'], record['height']), f"{record['id']}: poster dimensions mismatch"
        image.verify()
    # showinfo reports the actual input stream timebase/rate; decoding the entire
    # stream also checks that H.264 content is valid rather than trusting the JSON.
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-nostats', '-i', str(folder / record['video']),
               '-map', '0:v:0', '-vf', 'showinfo', '-progress', 'pipe:1', '-f', 'null', '-']
    decoded = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    frame_counts = re.findall(r'^frame=(\d+)\s*$', decoded.stdout, flags=re.MULTILINE)
    assert frame_counts and int(frame_counts[-1]) == 72, f"{record['id']}: video must decode exactly 72 frames"
    assert re.search(r'frame_rate:\s*24/1', decoded.stderr), f"{record['id']}: input video is not constant 24/1 fps"
    assert 'yuv420p' in decoded.stderr, f"{record['id']}: expected widely supported yuv420p format"
    print(f"Verified {record['id']}: MP4 72 frames at 24 fps; GIF {record['gifFrames']} frames / 3000 ms; hashes and poster valid.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=ROOT / 'dist' / 'assets' / 'animations-3d')
    args = parser.parse_args()
    manifest = json.loads((args.folder / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['preferredFormat'] == 'MP4' and manifest['fps'] == 24
    assert manifest['animations'], 'Manifest has no animations'
    for record in manifest['animations']:
        verify(record, args.folder)


if __name__ == '__main__':
    main()
