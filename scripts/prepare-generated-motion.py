"""Prepare a reversible 2D stabilization/interpolation experiment.

This only registers existing generated frames; it never changes the source PNGs
or tries to infer exercise correctness from image similarity.
"""
from pathlib import Path
import argparse
import json
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SIDE = 480
BOXES = [( .62, .01, .90, .09), (.86, .10, .92, .87), (.60, .89, .96, .99)]


def prepare(exercise):
    source = ROOT / 'docs/generated-frames-v2' / (exercise + '.png')
    sheet = Image.open(source).convert('RGB')
    width, height = sheet.size
    cells = []
    for index in range(9):
        column, row = index % 4, index // 4
        bounds = (round(column * width / 4) + 2, round(row * height / 4) + 2,
                  round((column + 1) * width / 4) - 2, round((row + 1) * height / 4) - 2)
        cells.append(np.array(sheet.crop(bounds).resize((SIDE, SIDE), Image.Resampling.LANCZOS)))
    reference = cells[0]
    mask = np.zeros((SIDE, SIDE), dtype=np.uint8)
    for x0, y0, x1, y1 in BOXES:
        mask[round(y0 * SIDE):round(y1 * SIDE), round(x0 * SIDE):round(x1 * SIDE)] = 255
    gray_ref = cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY)
    sift = cv2.SIFT_create(nfeatures=800, contrastThreshold=.015)
    ref_points, ref_desc = sift.detectAndCompute(gray_ref, mask)
    target = ROOT / 'output/generated-motion' / exercise
    directory = target / 'anchors'
    directory.mkdir(parents=True, exist_ok=True)
    records, frames = [], []
    for index, cell in enumerate(cells):
        matrix = np.eye(2, 3, dtype=np.float32)
        method, matches_count = 'identity', 0
        if index:
            gray = cv2.cvtColor(cell, cv2.COLOR_RGB2GRAY)
            points, desc = sift.detectAndCompute(gray, mask)
            if desc is not None and ref_desc is not None:
                matches = cv2.BFMatcher().knnMatch(desc, ref_desc, k=2)
                valid = [a for pair in matches if len(pair) == 2 for a, b in [pair] if a.distance < .75 * b.distance]
                matches_count = len(valid)
                if len(valid) >= 5:
                    before = np.float32([points[m.queryIdx].pt for m in valid])
                    after = np.float32([ref_points[m.trainIdx].pt for m in valid])
                    estimated, inliers = cv2.estimateAffinePartial2D(before, after, method=cv2.RANSAC, ransacReprojThreshold=1.8, maxIters=4000)
                    if estimated is not None and int(inliers.sum()) >= 4:
                        matrix, method = estimated.astype(np.float32), 'rigid/similarity feature registration'
            if method == 'identity':
                try:
                    correlation, inverse = cv2.findTransformECC(gray_ref, gray, np.eye(2, 3, dtype=np.float32),
                        cv2.MOTION_EUCLIDEAN, (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 250, 1e-6), mask, 5)
                    matrix, method = cv2.invertAffineTransform(inverse), 'rigid ECC registration'
                except cv2.error:
                    method = 'registration rejected; source retained'
        scale = math.hypot(float(matrix[0, 0]), float(matrix[1, 0]))
        rotation = math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0])))
        if not (.965 <= scale <= 1.035 and abs(rotation) <= 2 and max(abs(float(matrix[0, 2])), abs(float(matrix[1, 2]))) <= 25):
            matrix, method = np.eye(2, 3, dtype=np.float32), 'excessive transform rejected; source retained'
            scale, rotation = 1, 0
        aligned = cv2.warpAffine(cell, matrix, (SIDE, SIDE), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
        gray_aligned = cv2.cvtColor(aligned, cv2.COLOR_RGB2GRAY)
        static_error = float(np.mean(np.abs(gray_aligned.astype('float32') - gray_ref.astype('float32'))[mask > 0]))
        Image.fromarray(aligned).save(directory / f'anchor_{index:02d}.png')
        frames.append(Image.fromarray(aligned))
        records.append({'sourceIndex': index, 'registration': method, 'featureMatches': matches_count,
                        'matrix': matrix.tolist(), 'scale': scale, 'rotationDegrees': rotation,
                        'staticRegionMeanAbsoluteError': static_error})
    contact = Image.new('RGB', (SIDE * 3, (SIDE + 32) * 3), 'white')
    draw = ImageDraw.Draw(contact)
    for index, frame in enumerate(frames):
        x, y = (index % 3) * SIDE, (index // 3) * (SIDE + 32)
        contact.paste(frame, (x, y + 32))
        draw.text((x + 10, y + 6), f'Anchor {index} | static error {records[index]["staticRegionMeanAbsoluteError"]:.2f}', fill='black')
        for line_y in range(144, 336, 24):
            draw.line((x + 145, y + 32 + line_y, x + 280, y + 32 + line_y), fill=(110, 140, 180), width=1)
            draw.text((x + 281, y + 32 + line_y - 5), str(line_y), fill=(70, 90, 120))
    contact.save(target / 'anchors-contact.png')
    result = {'exercise': exercise, 'source': source.relative_to(ROOT).as_posix(), 'size': SIDE,
              'sourceIndices': list(range(9)), 'staticAnchorRectangles': BOXES, 'anchors': records,
              'return': 'Reuses the exact forward frames in reverse; no separately generated return poses',
              'reviewStatus': 'Experimental registration only; no anatomical or execution validation'}
    (target / 'preparation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for record in records:
        print(f"Anchor {record['sourceIndex']}: {record['registration']}, scale {record['scale']:.4f}, angle {record['rotationDegrees']:.3f}, static MAE {record['staticRegionMeanAbsoluteError']:.2f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--exercise', choices=['reverse-cable-curl'], default='reverse-cable-curl')
    prepare(parser.parse_args().exercise)
