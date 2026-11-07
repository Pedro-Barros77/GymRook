"""Encode offline Blender PNGs as true-24-fps MP4s plus GIF compatibility copies.

Example: python scripts/encode-3d.py --exercise pec-deck
Input: output/3d/<exercise>/frames/frame_0001.png ... frame_0072.png
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from PIL import Image
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ['pec-deck', 'incline-dumbbell-press', 'push-up', 'reverse-cable-curl']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(exercise, source_root, destination, fps, count):
    source = (source_root / exercise / 'frames').resolve()
    paths = [source / f'frame_{index:04d}.png' for index in range(1, count + 1)]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f'{exercise}: {len(missing)} missing PNGs, beginning with {missing[0]}')
    frames = []
    size = None
    for path in paths:
        with Image.open(path) as image:
            rgb = image.convert('RGB')
            if size is None:
                size = rgb.size
            if rgb.size != size:
                raise RuntimeError(f'{path}: frame dimensions changed')
            frames.append(rgb.copy())
    if any(edge % 2 for edge in size):
        raise ValueError(f'{exercise}: MP4 yuv420p needs even dimensions, got {size}')
    destination.mkdir(parents=True, exist_ok=True)
    mp4 = destination / f'{exercise}.mp4'
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y',
               '-framerate', str(fps), '-start_number', '1', '-i', str(source / 'frame_%04d.png'),
               '-frames:v', str(count), '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-r', str(fps), '-movflags', '+faststart', str(mp4)]
    subprocess.run(command, check=True, capture_output=True)

    # Every source frame contributes to one global palette. Downsampling only the
    # palette samples keeps this step fast; encoded frames retain full resolution.
    sample_side = 128
    columns = 12
    rows = (count + columns - 1) // columns
    samples = Image.new('RGB', (columns * sample_side, rows * sample_side))
    for index, frame in enumerate(frames):
        samples.paste(frame.resize((sample_side, sample_side), Image.Resampling.LANCZOS),
                      ((index % columns) * sample_side, (index // columns) * sample_side))
    palette = samples.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    # GIF stores integer centiseconds. Cumulative rounding alternates 40/50 ms at
    # 24 fps and preserves the exact 3-second total of 72 frames.
    boundaries = [round(index * 100 / fps) for index in range(count + 1)]
    delays = [(boundaries[index + 1] - boundaries[index]) * 10 for index in range(count)]
    gif = destination / f'{exercise}.gif'
    indexed[0].save(gif, save_all=True, append_images=indexed[1:], duration=delays,
                    loop=0, disposal=2, optimize=False, include_color_table=False)
    with Image.open(gif) as decoded:
        gif_count = decoded.n_frames
        actual_delays = []
        for index in range(gif_count):
            decoded.seek(index)
            actual_delays.append(decoded.info.get('duration', 0))
    if sum(actual_delays) != round(count * 1000 / fps):
        raise RuntimeError(f'{exercise}: GIF timing changed during encoding')
    poster = destination / f'{exercise}-poster.webp'
    frames[0].save(poster, quality=90, method=6)

    contact = Image.new('RGB', (size[0] * 4, size[1] * 3))
    for slot in range(12):
        index = round(slot * (count - 1) / 11)
        contact.paste(frames[index], ((slot % 4) * size[0], (slot // 4) * size[1]))
    contact.thumbnail((1440, 1080), Image.Resampling.LANCZOS)
    contact.save(source.parent / 'contact-sheet.jpg', quality=92)
    record = {'id': exercise, 'source': source.relative_to(ROOT).as_posix(),
              'frameCount': count, 'fps': fps, 'fpsNumerator': fps, 'fpsDenominator': 1,
              'durationSeconds': count / fps, 'width': size[0], 'height': size[1],
              'video': mp4.name, 'gif': gif.name, 'poster': poster.name,
              'gifFrames': gif_count, 'gifDurationMilliseconds': sum(actual_delays),
              'gifFrameDelaysMilliseconds': actual_delays,
              'files': {path.name: {'bytes': path.stat().st_size, 'sha256': digest(path)} for path in [mp4, gif, poster]}}
    print(f'{exercise}: {count} PNGs -> {fps} fps MP4 ({mp4.stat().st_size / 1024:.0f} KiB), GIF {gif_count} frames ({gif.stat().st_size / 1024:.0f} KiB)')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise', choices=EXERCISES + ['all'], default='all')
    parser.add_argument('--frames-root', type=Path, default=ROOT / 'output' / '3d')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / 'assets' / 'animations-3d')
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--count', type=int, default=72)
    args = parser.parse_args()
    if args.fps != 24 or args.count != 72:
        parser.error('This pilot is defined as 72 rendered frames at 24 fps (3 seconds).')
    selection = EXERCISES if args.exercise == 'all' else [args.exercise]
    manifest_path = args.output / 'manifest.json'
    prior = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    records = {record['id']: record for record in prior.get('animations', [])}
    for exercise in selection:
        records[exercise] = encode(exercise, args.frames_root, args.output, args.fps, args.count)
    manifest = {'pipeline': 'Offline Blender 3D scenes → fixed-camera PNGs → encoded media',
                'preferredFormat': 'MP4', 'fps': args.fps,
                'gifTimingNote': 'GIF centisecond delays alternate between 40 and 50 ms; MP4 retains an exact constant 24 fps.',
                'encoder': {'package': f'imageio-ffmpeg {imageio_ffmpeg.__version__}', 'ffmpeg': imageio_ffmpeg.get_ffmpeg_version()},
                'animations': [records[exercise] for exercise in EXERCISES if exercise in records]}
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(error.stderr.decode('utf-8', errors='replace') if error.stderr else str(error), file=sys.stderr)
        raise
