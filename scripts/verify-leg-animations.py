"""Verify leg-animation files, decoded media and source-frame continuity.

This checks technical properties, not biomechanics or exercise correctness.
The reported seam metrics must be reviewed visually, especially for the lunge.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / 'dist/assets/animations-d-v1'
SOURCES = ROOT / 'output/leg-animations'
IDS = (
    'leg-extension', 'hack-squat', 'lying-leg-curl',
    'dumbbell-stiff-leg-deadlift', 'machine-hip-abduction',
    'machine-hip-adduction', 'alternating-lunge',
)
SIZE = (512, 512)
# Generous average-pixel limit catches an unrelated/wrongly ordered encode while
# allowing normal compression and GIF palette loss. It is not a visual QA score.
MAX_MEAN_ENCODING_ERROR = 25.0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mean_difference(a, b):
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def rgb_image(path):
    with Image.open(path) as image:
        require(image.size == SIZE, f'{path}: expected {SIZE} pixels')
        return np.asarray(image.convert('RGB')).copy()


def verify_files(record, exercise_id):
    for field, expected_name in (
        ('video', f'{exercise_id}.mp4'),
        ('gif', f'{exercise_id}.gif'),
        ('poster', f'{exercise_id}-poster.webp'),
    ):
        name = record[field]
        require(name == expected_name, f'{exercise_id}: unexpected {field} filename: {name}')
        path = MEDIA / name
        body = path.read_bytes()
        info = record['files'][name]
        require(len(body) == info['bytes'], f'{name}: file size does not match manifest')
        require(hashlib.sha256(body).hexdigest() == info['sha256'], f'{name}: SHA-256 does not match manifest')


def verify_sources(exercise_id, count):
    folder = SOURCES / exercise_id / 'frames'
    paths = sorted(folder.glob('frame_*.png'))
    expected = [f'frame_{i:04d}.png' for i in range(1, count + 1)]
    require([path.name for path in paths] == expected, f'{exercise_id}: source frame sequence is incomplete or has extra frames')
    frames = [rgb_image(path) for path in paths]
    if exercise_id != 'alternating-lunge':
        # 1..19 forward, 20..36 = 18..2. The first frame completes the loop.
        for returned, forward in zip(range(19, 36), range(17, 0, -1)):
            require(np.array_equal(frames[returned], frames[forward]),
                    f'{exercise_id}: frame {returned + 1} differs from mirrored frame {forward + 1}')
    steps = [mean_difference(a, b) for a, b in zip(frames, frames[1:])]
    require(max(steps) > 0, f'{exercise_id}: source frames show no motion')
    seam = mean_difference(frames[-1], frames[0])
    ratio = seam / max(steps)
    print(f'{exercise_id}: seam MAE {seam:.3f}, largest adjacent MAE {max(steps):.3f}, ratio {ratio:.3f}; visual review required.')
    return frames


def verify_video(exercise_id, record, source_frames, count):
    path = MEDIA / record['video']
    # Check stream codec and pixel format using the already-installed FFmpeg.
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', str(path),
         '-map', '0:v:0', '-frames:v', '1', '-f', 'null', '-'],
        capture_output=True, text=True, encoding='utf-8', errors='replace', check=True,
    )
    require(re.search(r'Video:\s*h264\b', result.stderr, re.I), f'{exercise_id}: expected H.264 video')
    require(re.search(r'\byuv420p\b', result.stderr, re.I), f'{exercise_id}: expected yuv420p video')
    capture = cv2.VideoCapture(str(path))
    require(capture.isOpened(), f'{exercise_id}: could not open video')
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        require(math.isfinite(fps) and abs(fps - 12) < 0.01, f'{exercise_id}: expected 12 fps, got {fps}')
        decoded = 0
        max_error = 0.0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            require(decoded < count, f'{exercise_id}: video has extra frames')
            require(frame is not None and frame.shape == (SIZE[1], SIZE[0], 3), f'{exercise_id}: decoded frame has incorrect size')
            error = mean_difference(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), source_frames[decoded])
            max_error = max(max_error, error)
            require(error <= MAX_MEAN_ENCODING_ERROR, f'{exercise_id}: decoded video frame {decoded + 1} differs excessively from source (MAE {error:.2f})')
            decoded += 1
        require(decoded == count, f'{exercise_id}: decoded {decoded} video frames, expected {count}')
        print(f'{exercise_id}: decoded {decoded} video frames at {fps:g} fps; maximum source MAE {max_error:.3f}.')
    finally:
        capture.release()


def verify_gif_and_poster(exercise_id, record, source_frames, count, duration_ms):
    with Image.open(MEDIA / record['gif']) as image:
        require(image.format == 'GIF' and image.size == SIZE, f'{exercise_id}: invalid GIF format or dimensions')
        require(image.n_frames == count == record['gifFrames'], f'{exercise_id}: incorrect GIF frame count')
        require(image.info.get('loop') == 0, f'{exercise_id}: GIF must loop continuously')
        delays = []
        max_error = 0.0
        for index in range(count):
            image.seek(index)
            delays.append(image.info.get('duration', 0))
            error = mean_difference(np.asarray(image.convert('RGB')), source_frames[index])
            max_error = max(max_error, error)
            require(error <= MAX_MEAN_ENCODING_ERROR, f'{exercise_id}: GIF frame {index + 1} differs excessively from source (MAE {error:.2f})')
        require(all(delay > 0 for delay in delays), f'{exercise_id}: GIF contains a nonpositive delay')
        require(sum(delays) == duration_ms == record['gifDurationMilliseconds'], f'{exercise_id}: incorrect GIF duration')
        require(delays == record['gifFrameDelaysMilliseconds'], f'{exercise_id}: GIF delays differ from manifest')
        print(f'{exercise_id}: GIF {count} frames / {sum(delays)} ms; maximum source MAE {max_error:.3f}.')
    with Image.open(MEDIA / record['poster']) as poster:
        require(poster.format == 'WEBP' and poster.size == SIZE, f'{exercise_id}: invalid WebP poster')
        pixels = np.asarray(poster.convert('RGB'))
        require(mean_difference(pixels, source_frames[0]) <= MAX_MEAN_ENCODING_ERROR,
                f'{exercise_id}: poster differs excessively from the opening source frame')


def main():
    manifest = json.loads((MEDIA / 'manifest.json').read_text(encoding='utf-8'))
    require(manifest['preferredFormat'] == 'MP4' and manifest['fps'] == 12, 'Manifest must specify MP4 and 12 fps')
    records = manifest['animations']
    require(len(records) == len(IDS), 'Manifest must contain exactly seven animations')
    by_id = {record['id']: record for record in records}
    require(set(by_id) == set(IDS), 'Manifest IDs differ from the seven leg exercises')
    for exercise_id in IDS:
        record = by_id[exercise_id]
        count = 48 if exercise_id == 'alternating-lunge' else 36
        seconds = count // 12
        require(record['fps'] == 12 and record['frameCount'] == count and record['durationSeconds'] == seconds,
                f'{exercise_id}: wrong frame rate, count or duration in manifest')
        require(record['width'] == SIZE[0] and record['height'] == SIZE[1], f'{exercise_id}: wrong manifest dimensions')
        verify_files(record, exercise_id)
        frames = verify_sources(exercise_id, count)
        verify_video(exercise_id, record, frames, count)
        verify_gif_and_poster(exercise_id, record, frames, count, seconds * 1000)
    print('Technical verification complete. Review motion, seams, anatomy and exercise execution visually with a qualified professional.')


if __name__ == '__main__':
    main()
