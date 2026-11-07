"""Prepare and interpolate separate, full-resolution pec-deck reference poses.

Input JSON (paths are relative to the JSON file):
{
  "coordinateSpace": "normalized",
  "referenceIndex": 8,
  "staticRegions": [[x0, y0, x1, y1], ...],
  "anchors": [{"file": "pose-00.png", "near": [x,y], "far": [x,y],
               "weightTop": [x,y]}, ...]
}

Three or more open-to-closed references are supported. --prepare-only also works
before hand landmarks are supplied. Original images are never modified. This
pipeline checks image/landmark continuity; it does not validate human execution.
The default interpolation backend is Practical-RIFE 4.25 (CPU, one batch).
Use --backend rife-ncnn-v4.6 for the archived Vulkan interpolation backend.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import argparse
import bisect
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import time
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'output/pec-deck-v4'
TARGET = ROOT / 'dist/assets/animations-pec-deck-v4'
REPORT = ROOT / 'docs/pec-deck-v4-build.json'
PRACTICAL_CACHE = ROOT / '.cache/qa-pec-deck-interpolation'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def preserve(config_path, entries, extra_paths=()):
    paths = {config_path, *(entry['path'] for entry in entries), *extra_paths}
    for directory in [ROOT / 'dist/assets', ROOT / 'assets/3d', ROOT / 'backups/2d-v2-20261106']:
        if directory.is_dir():
            paths.update(path for path in directory.rglob('*') if path.is_file() and TARGET not in path.parents)
    for directory in (ROOT / 'docs').glob('generated-frames*'):
        if directory.is_dir():
            paths.update(path for path in directory.rglob('*') if path.is_file())
    return {label(path): {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(paths)}


def verify_preserved(snapshot):
    for filename, expected in snapshot.items():
        path = Path(filename)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or path.stat().st_size != expected['bytes'] or sha(path) != expected['sha256']:
            raise RuntimeError('A preserved source/asset changed during processing: ' + filename)


def write_report(report):
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def config_entries(config, config_path):
    anchors = config.get('anchors', [])
    if len(anchors) < 3:
        raise ValueError('At least three separate open-to-closed reference poses are required.')
    entries = []
    for index, anchor in enumerate(anchors):
        path = Path(anchor['file'])
        path = path if path.is_absolute() else config_path.parent / path
        if not path.is_file():
            raise FileNotFoundError(f'Anchor {index} is not ready: {path}')
        entries.append({**anchor, 'path': path.resolve()})
    reference_index = int(config.get('referenceIndex', len(entries) - 1))
    if not 0 <= reference_index < len(entries):
        raise ValueError('referenceIndex must name an existing anchor (normally the final closed pose).')
    return entries, reference_index


def fitted_image(path, side):
    with Image.open(path) as opened:
        image = opened.convert('RGB')
    width, height = image.size
    ratio = min(side / width, side / height)
    resized = image.resize((round(width * ratio), round(height * ratio)), Image.Resampling.LANCZOS)
    offset = ((side - resized.width) // 2, (side - resized.height) // 2)
    canvas = Image.new('RGB', (side, side), image.getpixel((2, 2)))
    canvas.paste(resized, offset)
    transform = np.array([[ratio, 0, offset[0]], [0, ratio, offset[1]]], dtype=np.float32)
    return np.asarray(canvas), (width, height), transform


def hand_point(value, original_size, fit, matrix, coordinate_space):
    point = np.asarray(value, dtype=np.float64)
    if point.shape != (2,) or not np.all(np.isfinite(point)):
        raise ValueError('Each hand landmark must contain exactly two finite coordinates.')
    if coordinate_space == 'normalized':
        if np.any(point < 0) or np.any(point > 1):
            raise ValueError('Normalized hand coordinates must be within 0..1.')
        point *= np.asarray(original_size)
    elif coordinate_space != 'pixels':
        raise ValueError('Declare coordinateSpace as normalized or pixels.')
    point = fit @ np.append(point, 1)
    return (matrix @ np.append(point, 1)).tolist()


def static_mask(config, side):
    regions = config.get('staticRegions', [])
    if not regions:
        raise ValueError('Supply staticRegions containing fixed machine/base features, excluding arms, body and moving weight plates.')
    mask = np.zeros((side, side), np.uint8)
    for box in regions:
        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError('staticRegions must be normalized [x0,y0,x1,y1] boxes.')
        x0, y0, x1, y1 = [round(value * side) for value in box]
        mask[y0:y1, x0:x1] = 255
    if cv2.countNonZero(mask) < side * side * .015:
        raise ValueError('Static regions are too small for a robust whole-scene registration.')
    return mask


def register(reference, current, mask, limits, identity=False):
    matrix = np.eye(2, 3, dtype=np.float32)
    ref = cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY)
    gray = cv2.cvtColor(current, cv2.COLOR_RGB2GRAY)
    method, matches, inliers_count = 'reference identity', 0, 0
    if not identity:
        method = 'registration unavailable; original retained'
        sift = cv2.SIFT_create(nfeatures=1500, contrastThreshold=.012)
        a_points, a_desc = sift.detectAndCompute(gray, mask)
        b_points, b_desc = sift.detectAndCompute(ref, mask)
        if a_desc is not None and b_desc is not None:
            neighbors = cv2.BFMatcher().knnMatch(a_desc, b_desc, k=2)
            valid = [pair[0] for pair in neighbors if len(pair) == 2 and pair[0].distance < .73 * pair[1].distance]
            matches = len(valid)
            if matches >= 6:
                before = np.float32([a_points[item.queryIdx].pt for item in valid])
                after = np.float32([b_points[item.trainIdx].pt for item in valid])
                estimate, inliers = cv2.estimateAffinePartial2D(before, after, method=cv2.RANSAC, ransacReprojThreshold=1.8, maxIters=5000)
                if estimate is not None and inliers is not None and int(inliers.sum()) >= 5:
                    matrix, method = estimate.astype(np.float32), 'global similarity from fixed-feature RANSAC'
                    inliers_count = int(inliers.sum())
        if method.startswith('registration unavailable'):
            try:
                _, inverse = cv2.findTransformECC(ref, gray, matrix.copy(), cv2.MOTION_EUCLIDEAN,
                    (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 300, 1e-6), mask, 5)
                matrix = cv2.invertAffineTransform(inverse)
                method = 'global rigid ECC on fixed-feature regions'
            except cv2.error:
                pass
    scale = math.hypot(float(matrix[0, 0]), float(matrix[1, 0]))
    rotation = math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0])))
    center = np.array([current.shape[1] / 2, current.shape[0] / 2, 1])
    shift = matrix @ center - center[:2]
    accepted = (abs(scale - 1) <= limits['maxScaleDeviation'] and abs(rotation) <= limits['maxRotationDegrees']
                and float(np.max(np.abs(shift))) <= limits['maxTranslationPixels'])
    if not accepted:
        matrix = np.eye(2, 3, dtype=np.float32)
        method = 'excessive global transform rejected; original retained'
    aligned = cv2.warpAffine(current, matrix, (current.shape[1], current.shape[0]), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    error_before = float(np.mean(np.abs(gray.astype(np.float32) - ref.astype(np.float32))[mask > 0]))
    error_after = float(np.mean(np.abs(cv2.cvtColor(aligned, cv2.COLOR_RGB2GRAY).astype(np.float32) - ref.astype(np.float32))[mask > 0]))
    return aligned, matrix, {'method': method, 'accepted': accepted and not method.startswith('registration unavailable'),
        'matrix': matrix.tolist(), 'featureMatches': matches, 'inliers': inliers_count,
        'estimatedScale': scale, 'estimatedRotationDegrees': rotation, 'estimatedCenterShiftPixels': shift.tolist(),
        'staticRegionMAEBefore': error_before, 'staticRegionMAEAfter': error_after}


def prepare(config, entries, reference_index, side):
    loaded = [fitted_image(entry['path'], side) for entry in entries]
    mask = static_mask(config, side)
    reference = loaded[reference_index][0]
    limits = {'maxScaleDeviation': .025, 'maxRotationDegrees': 1.5, 'maxTranslationPixels': 16}
    limits.update(config.get('alignment', {}))
    anchor_dir = WORK / 'anchors'
    anchor_dir.mkdir(parents=True, exist_ok=True)
    records, images = [], []
    space = config.get('coordinateSpace')
    for index, (entry, (image, original_size, fit)) in enumerate(zip(entries, loaded)):
        aligned, matrix, registration = register(reference, image, mask, limits, index == reference_index)
        hands = entry.get('hands', entry)
        transformed_hands = {}
        for hand in ['near', 'far']:
            if hand in hands:
                transformed_hands[hand] = hand_point(hands[hand], original_size, fit, matrix, space)
        path = anchor_dir / f'anchor_{index:02d}.png'
        Image.fromarray(aligned).save(path)
        images.append(aligned)
        record = {'index': index, 'source': label(entry['path']), 'sourceSha256': sha(entry['path']),
                        'originalSize': list(original_size), 'fitMatrix': fit.tolist(), 'alignment': registration,
                        'hands': transformed_hands, 'file': label(path), 'sha256': sha(path)}
        weight_top = entry.get('weightTop', hands.get('weightTop'))
        if weight_top is not None:
            record['weightTop'] = hand_point(weight_top, original_size, fit, matrix, space)
        records.append(record)
    rows = math.ceil(len(images) / 3)
    contact = Image.new('RGB', (side * 3, (side + 32) * rows), 'white')
    draw = ImageDraw.Draw(contact)
    for index, image in enumerate(images):
        x, y = index % 3 * side, index // 3 * (side + 32)
        contact.paste(Image.fromarray(image), (x, y + 32))
        draw.text((x + 8, y + 8), f'Pose {index:02d} | fixed MAE {records[index]["alignment"]["staticRegionMAEAfter"]:.2f}', fill='black')
        for hand, color in [('near', '#e74c3c'), ('far', '#237dc0')]:
            if hand in records[index]['hands']:
                hx, hy = records[index]['hands'][hand]
                draw.ellipse((x + hx - 5, y + 32 + hy - 5, x + hx + 5, y + 32 + hy + 5), outline=color, width=2)
        if 'weightTop' in records[index]:
            wx, wy = records[index]['weightTop']
            draw.rectangle((x + wx - 5, y + 32 + wy - 5, x + wx + 5, y + 32 + wy + 5), outline='#18843b', width=2)
    contact.save(WORK / 'anchors-contact.png')
    return records, images, limits


def hand_progress(records, config):
    if any(set(record['hands']) != {'near', 'far'} for record in records):
        raise ValueError('Both near and far hand centers are required for every pose before interpolation.')
    positions = {hand: np.asarray([record['hands'][hand] for record in records], dtype=np.float64) for hand in ['near', 'far']}
    endpoint_lengths, projections, segment_lengths = {}, {}, {}
    quality = config.get('quality', {})
    tolerance = float(quality.get('monotonicTolerance', .025))
    issues = []
    for hand, values in positions.items():
        direction = values[-1] - values[0]
        length = float(np.linalg.norm(direction))
        if length < 12:
            raise ValueError(f'{hand} hand endpoint movement is too small for reliable retiming ({length:.1f}px).')
        endpoint_lengths[hand] = length
        projections[hand] = ((values - values[0]) @ direction / (length * length)).tolist()
        for interval, advance in enumerate(np.diff(projections[hand])):
            if advance < -tolerance:
                issues.append({'code': 'hand-projection-reversal', 'hand': hand, 'interval': [interval, interval + 1],
                               'advance': float(advance), 'blocking': bool(quality.get('enforceMonotonicHands', True)),
                               'message': f'{hand} hand endpoint-projection reverses between selected poses {interval} and {interval + 1}; review the actual arc.'})
        segment_lengths[hand] = np.linalg.norm(np.diff(values, axis=0), axis=1)
    # Normalize each track by its own projected displacement so the nearer/larger
    # hand does not hide an incorrectly timed far hand in three-quarter view.
    steps = np.sqrt(sum((segment_lengths[hand] / endpoint_lengths[hand]) ** 2 for hand in positions) / 2)
    if np.any(steps <= .0001):
        raise ValueError('A source transition repeats both hand positions; revise/remove the duplicate pose.')
    progress = np.concatenate(([0.], np.cumsum(steps)))
    progress /= progress[-1]
    intervals = []
    stalled_threshold = float(quality.get('bilateralStallThreshold', .01))
    moving_threshold = float(quality.get('bilateralOtherAdvanceThreshold', .12))
    maximum_ratio = float(quality.get('maximumBilateralStepRatio', 12))
    for interval in range(len(records) - 1):
        projected = {hand: projections[hand][interval + 1] - projections[hand][interval] for hand in positions}
        distances = {hand: float(segment_lengths[hand][interval] / endpoint_lengths[hand]) for hand in positions}
        weak, strong = min(projected.values()), max(projected.values())
        # This is a diagnostic about apparent image progress, not an assertion
        # that symmetric 3D hands must move linearly/symmetrically on the screen.
        stalled = strong > moving_threshold and weak < stalled_threshold
        ratio = max(distances.values()) / max(min(distances.values()), .000001)
        duration = float(progress[interval + 1] - progress[interval])
        intervals.append({'interval': [interval, interval + 1],
                          'sourceInterval': [records[interval]['source'], records[interval + 1]['source']],
                          'projectedAdvances': projected, 'normalizedArcDistances': distances,
                          'commonPhaseDuration': duration,
                          'normalizedSpeedsPerCommonPhase': {hand: distance / duration for hand, distance in distances.items()},
                          'bilateralStepRatio': ratio, 'apparentBilateralStall': stalled})
        if stalled:
            issues.append({'code': 'apparent-bilateral-stall', 'interval': [interval, interval + 1],
                           'projectedAdvances': projected, 'blocking': bool(quality.get('enforceBilateralStalls', True)),
                           'message': f'One hand appears to pause while the other advances between selected poses {interval} and {interval + 1}; a time remap cannot fix conflicting source poses.'})
        elif ratio > maximum_ratio and max(distances.values()) > moving_threshold:
            issues.append({'code': 'bilateral-speed-disparity', 'interval': [interval, interval + 1],
                           'stepRatio': ratio, 'blocking': bool(quality.get('enforceBilateralDisparity', False)),
                           'message': f'Large apparent hand-speed disparity in interval {interval}; inspect perspective and source trajectory.'})
    return progress.tolist(), {'endpointDistancesPixels': endpoint_lengths, 'projectedProgressPerHand': projections,
        'normalizedCombinedSegmentLengths': steps.tolist(), 'anchorProgress': progress.tolist(),
        'monotonicTolerance': tolerance, 'monotonicWithinTolerance': not any(issue['code'] == 'hand-projection-reversal' for issue in issues),
        'maximumApparentHandPhaseGap': float(max(abs(np.asarray(projections['near']) - np.asarray(projections['far'])))),
        'intervalDiagnostics': intervals, 'sourceQualityIssues': issues,
        'metricLimit': 'Endpoint projection is diagnostic only; three-quarter perspective may produce unequal screen speeds or local extrema. Gate settings must be justified by visual source review; no images are modified.'}, positions


def weight_progress(records, config):
    quality = config.get('quality', {})
    missing = [record['index'] for record in records if 'weightTop' not in record]
    if missing:
        issue = {'code': 'missing-weight-top-landmarks', 'poses': missing,
                 'blocking': bool(quality.get('requireWeightTop', True)),
                 'message': 'Selected weight-block top cannot be checked without a matching weightTop landmark on every selected pose.'}
        return {'status': 'not-measured', 'missingPoses': missing, 'sourceQualityIssues': [issue]}
    values = np.asarray([record['weightTop'] for record in records])
    heights = values[:, 1]
    tolerance = float(quality.get('weightMonotonicTolerancePixels', 2.0))
    lift = float(heights[0] - heights[-1])
    issues = []
    minimum_lift = float(quality.get('minimumWeightLiftPixels', 8.0))
    if lift < minimum_lift:
        issues.append({'code': 'insufficient-weight-lift', 'totalLiftPixels': lift,
                       'blocking': bool(quality.get('enforceWeightMonotonic', True)),
                       'message': 'Selected weight top does not show the required upward travel from open to closed.'})
    for interval, downward_step in enumerate(np.diff(heights)):
        if downward_step > tolerance:
            issues.append({'code': 'weight-top-reversal', 'interval': [interval, interval + 1],
                           'downwardStepPixels': float(downward_step),
                           'blocking': bool(quality.get('enforceWeightMonotonic', True)),
                           'message': f'Selected weight top moves downward during closure between selected poses {interval} and {interval + 1}.'})
    return {'status': 'measured-from-source-landmarks', 'topPointsPixels': values.tolist(),
            'imageYPerPose': heights.tolist(), 'totalLiftPixels': lift,
            'monotonicTolerancePixels': tolerance, 'sourceQualityIssues': issues,
            'monotonicRiseWithinTolerance': lift >= minimum_lift and not issues,
            'metricLimit': 'Source landmarks of the selected block, not unselected plates; interpolated image mechanics still require visual review.'}


class WeightLayer:
    """Reuse generated tower assets as deterministic animation layers.

    Every operation is confined to the declared tower channel. The interpolated
    human/hand pixels outside that channel remain byte-identical. No anatomy is
    warped, inferred, or independently redrawn by this composition step.
    """
    def __init__(self, config, config_path, side):
        self.config = config
        self.side = side
        self.basis = tuple(config.get('referenceSize', [1254, 1254]))
        self.sx, self.sy = side / self.basis[0], side / self.basis[1]
        def asset(key):
            path = Path(config[key])
            return path if path.is_absolute() else config_path.parent / path
        self.clean_path, self.sprite_path = asset('cleanPlate'), asset('spriteSource')
        with Image.open(self.clean_path) as opened:
            self.clean = np.asarray(opened.convert('RGB').resize((side, side), Image.Resampling.LANCZOS))
        with Image.open(self.sprite_path) as opened:
            self.canonical = opened.convert('RGB')
        self.canonical_canvas = np.asarray(self.canonical.resize((side, side), Image.Resampling.LANCZOS))
        self.sprite_crop = config.get('spriteCrop', [274 / 1254, 488 / 1254, 405 / 1254, 702 / 1254])
        self.rod_crop = config.get('rodCrop', [328 / 1254, 205 / 1254, 353 / 1254, 490 / 1254])
        self.base_crop = config.get('fixedBaseCrop', [274 / 1254, 845 / 1254, 405 / 1254, 975 / 1254])
        self.sprite, self.sprite_box = self.crop(self.sprite_crop)
        self.rod, self.rod_box = self.crop(self.rod_crop)
        base, self.base_box = self.crop(self.base_crop)
        self.open_top = float(config.get('openPlateTop', 655))
        self.closed_top = float(config.get('closedPlateTop', 512))
        self.source_top = float(config.get('sourcePlateTop', config.get('plateTop', 512)))
        self.source_bottom = float(config.get('sourcePlateBottom', 700))
        self.channel_x = tuple(config.get('channelX', [274, 405]))
        self.erase_bottom = float(config.get('eraseBottom', 975))
        self.erase_padding = float(config.get('eraseTopPadding', 40))
        self.erase_feather = float(config.get('eraseTopFeather', 10))
        if self.erase_feather < 0 or self.erase_padding < self.erase_feather + self.source_top - self.sprite_crop[1] * self.basis[1]:
            raise ValueError('Tower top feather must finish before the canonical moving sprite begins.')
        self.collar_offset = float(config.get('collarOffset', 22))
        self.report = {'type': 'deterministic composition of generated image layers',
            'cleanPlate': label(self.clean_path), 'cleanPlateSha256': sha(self.clean_path),
            'spriteSource': label(self.sprite_path), 'spriteSourceSha256': sha(self.sprite_path),
            'referenceSize': list(self.basis), 'spriteCropNormalized': self.sprite_crop,
            'spritePixelSha256': hashlib.sha256(self.sprite.tobytes()).hexdigest(),
            'selectedPlateCountFromSourceReview': int(config.get('selectedPlateCount', 9)),
            'plateCountMethod': 'One reviewed generated sprite is reused unchanged in every output pose; the image layer is never independently redrawn.',
            'rodCropNormalized': self.rod_crop, 'rodPixelSha256': hashlib.sha256(self.rod.tobytes()).hexdigest(),
            'fixedBaseCropNormalized': self.base_crop, 'fixedBasePixelSha256': hashlib.sha256(np.asarray(base).tobytes()).hexdigest(),
            'openPlateTopReferencePixels': self.open_top, 'closedPlateTopReferencePixels': self.closed_top,
            'sourcePlateTopReferencePixels': self.source_top, 'sourcePlateBottomReferencePixels': self.source_bottom,
            'channelXReferencePixels': list(self.channel_x), 'eraseBottomReferencePixels': self.erase_bottom,
            'eraseTopPaddingReferencePixels': self.erase_padding,
            'eraseTopFeatherReferencePixels': self.erase_feather,
            'humanHandling': 'No local human edits. All pixels outside the explicit tower-channel mask are preserved exactly before video/GIF encoding.'}

    def crop(self, box):
        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError('Weight-layer crop boxes must use normalized coordinates.')
        width, height = self.canonical.size
        pixels = (round(box[0] * width), round(box[1] * height), round(box[2] * width), round(box[3] * height))
        return np.asarray(self.canonical.crop(pixels)), pixels

    def place(self, image, asset, matrix, clip):
        # Warp RGB and its alpha together as premultiplied layers. Only the
        # sprite translation or the straight central-cable length may vary.
        rgb = cv2.warpAffine(asset.astype(np.float32), matrix, (self.side, self.side), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        alpha = cv2.warpAffine(np.ones(asset.shape[:2], np.float32), matrix, (self.side, self.side), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        alpha *= clip
        rgb *= clip[:, :, None]
        result = rgb + image.astype(np.float32) * (1 - alpha[:, :, None])
        return np.clip(np.rint(result), 0, 255).astype(np.uint8), alpha

    @staticmethod
    def blend(image, asset, alpha):
        """Blend a fixed RGB layer with its actual float opacity."""
        result = asset.astype(np.float32) * alpha[:, :, None] + image.astype(np.float32) * (1 - alpha[:, :, None])
        return np.clip(np.rint(result), 0, 255).astype(np.uint8)

    def compose(self, path, call):
        if 'expectedWeightTop' not in call:
            raise ValueError('Weight composition needs the original selected-weight-top landmarks to erase all generated plate variants safely.')
        with Image.open(path) as opened:
            before = np.asarray(opened.convert('RGB'))
        phase = float(call['progress'])
        plate_top = self.open_top + (self.closed_top - self.open_top) * phase
        top_output = plate_top * self.sy
        original_top_output = float(call['expectedWeightTop'][1])
        erase_top = min(original_top_output, top_output) - self.erase_padding * self.sy
        x0, x1 = math.floor(self.channel_x[0] * self.sx), math.ceil(self.channel_x[1] * self.sx)
        y0, y1 = max(0, math.floor(erase_top)), min(self.side, math.ceil(self.erase_bottom * self.sy))
        clip = np.zeros((self.side, self.side), np.float32)
        clip[y0:y1, x0:x1] = 1
        if self.erase_feather:
            # Only the top edge fades; the complete plate sprite lies below
            # this band at full opacity and remains canonically identical.
            opacity = np.clip((np.arange(y0, y1, dtype=np.float32) + .5 - erase_top)
                              / (self.erase_feather * self.sy), 0, 1)
            clip[y0:y1, x0:x1] *= opacity[:, None]
        image = self.blend(before, self.clean, clip)
        # The lower, unselected plates are fixed pixels from the same canonical
        # source as the moving block, so hole/plate geometry cannot drift.
        bx0, by0, bx1, by1 = [round(value * self.side) for value in self.base_crop]
        base_mask = np.zeros_like(clip)
        base_mask[by0:by1, bx0:bx1] = 1
        base_mask *= clip
        image = self.blend(image, self.canonical_canvas, base_mask)
        # Central rod/cable continues from its fixed top to the moving collar.
        rx0, ry0, rx1, ry1 = [value * axis for value, axis in zip(self.rod_crop, self.basis * 2)]
        collar_y = plate_top - self.collar_offset
        rod_height = (collar_y - ry0) * self.sy
        if rod_height <= 0:
            raise ValueError('The moving collar crossed the fixed cable anchor.')
        rod_matrix = np.float32([[self.sx, 0, rx0 * self.sx], [0, rod_height / self.rod.shape[0], ry0 * self.sy]])
        image, rod_alpha = self.place(image, self.rod, rod_matrix, clip)
        sx0, sy0, sx1, sy1 = [value * axis for value, axis in zip(self.sprite_crop, self.basis * 2)]
        sprite_top = plate_top + sy0 - self.source_top
        sprite_matrix = np.float32([[self.sx, 0, sx0 * self.sx], [0, self.sy, sprite_top * self.sy]])
        image, sprite_alpha = self.place(image, self.sprite, sprite_matrix, clip)
        # The two-pixel bottom crop margin can touch the fixed stack at the open
        # endpoint. Restore the canonical fixed block last, without moving it.
        image = self.blend(image, self.canonical_canvas, base_mask)
        outside = clip == 0
        outside_error = int(np.max(np.abs(image.astype(np.int16) - before.astype(np.int16))[outside])) if np.any(outside) else 0
        if outside_error:
            raise RuntimeError('Weight composition changed pixels outside its machine channel.')
        visible_clean = (clip == 1) & (base_mask == 0) & (rod_alpha == 0) & (sprite_alpha == 0)
        clean_error = int(np.max(np.abs(image.astype(np.int16) - self.clean.astype(np.int16))[visible_clean])) if np.any(visible_clean) else 0
        fixed_base_error = int(np.max(np.abs(image.astype(np.int16) - self.canonical_canvas.astype(np.int16))[base_mask > 0]))
        Image.fromarray(image).save(path)
        return {'plateTopReferencePixels': plate_top, 'plateTopOutputPixels': top_output,
            'plateBottomReferencePixels': plate_top + self.source_bottom - self.source_top,
            'maskOutputBounds': [x0, y0, x1, y1], 'sourceExpectedWeightTopOutputPixels': original_top_output,
            'topFeatherReferencePixels': self.erase_feather,
            'topFeatherOutputPixels': self.erase_feather * self.sy,
            'topFeatherEndOutputY': erase_top + self.erase_feather * self.sy,
            'spriteAffineMatrix': sprite_matrix.tolist(), 'rodAffineMatrix': rod_matrix.tolist(),
            'spritePixelSha256': self.report['spritePixelSha256'],
            'fixedBasePixelSha256': self.report['fixedBasePixelSha256'],
            'outsideChannelMaximumPixelError': outside_error, 'visibleCleanBandMaximumPixelError': clean_error,
            'fixedBaseMaximumPixelError': fixed_base_error,
            'spriteRigidTranslationOnly': True, 'independentWeightRedraw': False}


class FrameCorrections:
    """Composite reviewed, already aligned image-generation edits inside explicit ROIs."""
    def __init__(self, corrections, config_path, side):
        self.by_frame, self.paths, self.report = {}, [], []
        for index, correction in enumerate(corrections):
            frame = correction['frame']
            if not isinstance(frame, int) or not 1 <= frame <= 37:
                raise ValueError('frameCorrections frame must be an outward frame within 1..37; the return is mirrored automatically.')
            path = Path(correction['file'])
            path = (path if path.is_absolute() else config_path.parent / path).resolve()
            if not path.is_file():
                raise FileNotFoundError('Aligned frame-correction image is not ready: ' + str(path))
            with Image.open(path) as opened:
                if opened.size != (side, side):
                    raise ValueError(f'Frame correction must already be aligned at {side}x{side}, without resizing or warping: {path}')
                asset = np.asarray(opened.convert('RGB'))
            box = correction['crop']
            if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                raise ValueError('frameCorrections crop must be normalized [x0,y0,x1,y1].')
            x0, y0, x1, y1 = [round(value * side) for value in box]
            width, height = x1 - x0, y1 - y0
            feather = float(correction.get('featherPixels', 1))
            if not math.isfinite(feather) or feather < 0 or min(width, height) < 1 or feather > min(width, height) / 2:
                raise ValueError('frameCorrections featherPixels must fit inside a nonempty crop.')
            alpha = np.ones((height, width), dtype=np.float32)
            if feather:
                # Pixel centers are measured from the ROI boundary; no alpha
                # extends beyond it. A 1px feather leaves the outermost pixel
                # half opaque and reaches full opacity on the next pixel.
                dx = np.minimum(np.arange(width, dtype=np.float32) + .5, width - np.arange(width, dtype=np.float32) - .5)
                dy = np.minimum(np.arange(height, dtype=np.float32) + .5, height - np.arange(height, dtype=np.float32) - .5)
                distance = np.minimum(dy[:, None], dx[None, :])
                alpha = .5 - .5 * np.cos(np.pi * np.clip(distance / feather, 0, 1))
            record = {'index': index, 'frame': frame, 'source': label(path), 'sourceSha256': sha(path),
                      'sourceSize': [side, side], 'cropNormalized': box, 'cropOutputPixels': [x0, y0, x1, y1],
                      'sourceCropPixelSha256': hashlib.sha256(asset[y0:y1, x0:x1].tobytes()).hexdigest(),
                      'featherPixels': feather, 'feather': 'Cosine opacity within ROI only, measured at pixel centers.',
                      'operation': 'Reuse the same already aligned generated image crop; no resize, body warp or raster repaint.'}
            self.by_frame.setdefault(frame, []).append((asset, alpha, record))
            self.paths.append(path)
            self.report.append(record)

    def compose(self, path, frame):
        corrections = self.by_frame.get(frame, [])
        if not corrections:
            return []
        with Image.open(path) as opened:
            image = np.asarray(opened.convert('RGB')).copy()
        records = []
        for asset, alpha, source_record in corrections:
            before = image.copy()
            before_sha = sha(path)
            x0, y0, x1, y1 = source_record['cropOutputPixels']
            image[y0:y1, x0:x1] = WeightLayer.blend(image[y0:y1, x0:x1], asset[y0:y1, x0:x1], alpha)
            delta = np.abs(image.astype(np.int16) - before.astype(np.int16))
            outside = np.ones(image.shape[:2], dtype=bool)
            outside[y0:y1, x0:x1] = False
            outside_error = int(delta[outside].max()) if np.any(outside) else 0
            if outside_error:
                raise RuntimeError('Frame correction changed pixels outside its declared ROI.')
            Image.fromarray(image).save(path)
            records.append({**source_record, 'beforeSha256': before_sha, 'sha256': sha(path),
                            'outsideRoiMaximumPixelError': outside_error,
                            'differingPixelCount': int(np.count_nonzero(np.any(delta > 0, axis=2))),
                            'maximumPixelDifference': int(delta.max())})
        return records


def interpolation_provenance(args):
    """Record the exact local tools/model used, without importing either model."""
    if args.backend == 'practical-rife4.25':
        required = [args.python_runtime, args.batch_helper, args.integrity,
                    args.practical_model / 'train_log/flownet.pkl',
                    args.practical_model / 'train_log/IFNet_HDv3.py']
        for path in required:
            if not path.is_file():
                raise FileNotFoundError('Practical-RIFE batch dependency is not ready: ' + str(path))
        integrity = json.loads(args.integrity.read_text(encoding='utf-8-sig'))
        archive = args.integrity.parent / 'rife425.zip'
        expected_archive = integrity['rife425.zip']
        archive_record = {'file': label(archive), 'expected': expected_archive, 'available': archive.is_file()}
        if archive.is_file():
            actual = {'bytes': archive.stat().st_size, 'sha256': sha(archive)}
            archive_record['actual'] = actual
            if actual != expected_archive:
                raise RuntimeError('Practical-RIFE 4.25 archive differs from modern-models-integrity.json.')
        model_files = [path for path in args.practical_model.rglob('*')
                       if path.is_file() and path.suffix in ['.py', '.pkl'] and '__pycache__' not in path.parts]
        return {'backend': args.backend, 'model': 'Practical-RIFE 4.25', 'device': 'cpu',
                'scale': args.scale, 'threads': args.threads, 'singleBatchModelLoad': True,
                'runtime': {'file': label(args.python_runtime), 'sha256': sha(args.python_runtime)},
                'tool': {'file': label(args.batch_helper), 'sha256': sha(args.batch_helper)},
                'modelDirectory': label(args.practical_model),
                'modelFiles': {label(path): {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(model_files)},
                'integrityManifest': {'file': label(args.integrity), 'sha256': sha(args.integrity),
                                      'modelArchive': archive_record, 'provenance': integrity.get('provenance', {})}}
    if not args.binary.is_file() or not args.model.is_dir():
        raise FileNotFoundError('Official RIFE ncnn binary/model have not been prepared.')
    model_files = [path for path in args.model.rglob('*') if path.is_file()]
    return {'backend': args.backend, 'model': 'RIFE-v4.6 ncnn', 'device': 'vulkan', 'gpu': args.gpu,
            'timestepDecimal': args.timestep_decimal,
            'tool': {'file': label(args.binary), 'sha256': sha(args.binary)},
            'modelDirectory': label(args.model),
            'modelFiles': {label(path): {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(model_files)}}


def film_provenance(args):
    required = [args.python_runtime, args.film_helper, args.integrity,
                args.film_model / 'saved_model.pb', args.film_model / 'variables/variables.data-00000-of-00001']
    for path in required:
        if not path.is_file():
            raise FileNotFoundError('FILM batch dependency is not ready: ' + str(path))
    integrity = json.loads(args.integrity.read_text(encoding='utf-8-sig'))
    model_files = [path for path in args.film_model.rglob('*') if path.is_file()]
    records = {label(path): {'bytes': path.stat().st_size, 'sha256': sha(path)} for path in sorted(model_files)}
    for path in required[3:]:
        expected = integrity.get('film-model/' + path.relative_to(args.film_model).as_posix())
        if expected and records[label(path)] != expected:
            raise RuntimeError('FILM model differs from modern-models-integrity.json: ' + str(path))
    return {'engine': 'google-film-tfhub-v1', 'model': 'Google FILM TFHub v1', 'device': 'cpu',
            'depth': args.film_depth, 'quantization': 'round(requestedTimestep * 2**depth) / 2**depth',
            'sourceIntervals': sorted(args.film_intervals),
            'runtime': {'file': label(args.python_runtime), 'sha256': sha(args.python_runtime)},
            'tool': {'file': label(args.film_helper), 'sha256': sha(args.film_helper)},
            'modelDirectory': label(args.film_model), 'modelFiles': records,
            'integrityManifest': {'file': label(args.integrity), 'sha256': sha(args.integrity),
                                  'provenance': integrity.get('provenance', {})}}


def render_raw_frames(args, jobs, backend_run):
    """Interpolate the complete forward request list before any layer composition."""
    manifest_path = WORK / 'interpolation-requests.json'
    manifest_path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    backend_run['requestManifest'] = {'file': label(manifest_path), 'sha256': sha(manifest_path), 'requestCount': len(jobs)}
    started = time.monotonic()
    film_jobs = [job for job in jobs if job['engine'] == 'google-film-tfhub-v1']
    primary_jobs = [job for job in jobs if job['engine'] != 'google-film-tfhub-v1']
    primary_manifest = manifest_path
    if film_jobs:
        primary_manifest = WORK / 'interpolation-primary-requests.json'
        primary_manifest.write_text(json.dumps(primary_jobs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        backend_run['primaryRequestManifest'] = {'file': label(primary_manifest), 'sha256': sha(primary_manifest), 'requestCount': len(primary_jobs)}
    backend_run['subprocessCount'] = 0
    if args.backend == 'practical-rife4.25' and primary_jobs:
        command = [str(args.python_runtime.resolve()), str(args.batch_helper.resolve()),
                   '--manifest', str(primary_manifest.resolve()), '--model-dir', str(args.practical_model.resolve()),
                   '--threads', str(args.threads), '--scale', str(args.scale)]
        backend_run['command'] = command
        print(f'Pec deck v4: Practical-RIFE 4.25 CPU batch, {len(primary_jobs)} forward frames, scale {args.scale:g}', flush=True)
        # Inherit stdout for per-job progress while the model stays loaded once.
        result = subprocess.run(command, text=True, stderr=subprocess.PIPE)
        backend_run['subprocessCount'] = 1
        if result.returncode:
            raise RuntimeError('Practical-RIFE batch failed: ' + (result.stderr or '')[-5000:])
    elif args.backend == 'rife-ncnn-v4.6':
        for index, job in enumerate(primary_jobs):
            fraction, output = job['timestep'], Path(job['output'])
            if fraction < 1e-7 or fraction > 1 - 1e-7:
                shutil.copy2(job['input0'] if fraction < .5 else job['input1'], output)
            else:
                separator = ',' if args.timestep_decimal == 'comma' else '.'
                command = [str(args.binary.resolve()), '-0', job['input0'], '-1', job['input1'], '-o', str(output),
                           '-m', str(args.model.resolve()), '-s', f'{fraction:.9f}'.replace('.', separator),
                           '-g', args.gpu, '-j', '1:1:1', '-z']
                result = subprocess.run(command, capture_output=True, text=True)
                backend_run['subprocessCount'] += 1
                if result.returncode:
                    raise RuntimeError(f'RIFE ncnn frame {index + 1} failed: {(result.stderr or result.stdout)[-3000:]}')
            print(f'Pec deck v4: raw primary forward {index + 1}/{len(primary_jobs)} ({time.monotonic() - started:.1f}s)', flush=True)
    if film_jobs:
        film_manifest, film_report = WORK / 'interpolation-film-requests.json', WORK / 'interpolation-film-report.json'
        film_manifest.write_text(json.dumps(film_jobs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        command = [str(args.python_runtime.resolve()), str(args.film_helper.resolve()),
                   '--manifest', str(film_manifest.resolve()), '--model-dir', str(args.film_model.resolve()),
                   '--threads', str(args.threads), '--depth', str(args.film_depth), '--report', str(film_report.resolve())]
        override = backend_run['filmOverride']
        override['requestManifest'] = {'file': label(film_manifest), 'sha256': sha(film_manifest), 'requestCount': len(film_jobs)}
        override['command'] = command
        print(f'Pec deck v4: FILM CPU batch, {len(film_jobs)} forward frames, recursive depth {args.film_depth}', flush=True)
        result = subprocess.run(command, text=True, stderr=subprocess.PIPE)
        backend_run['subprocessCount'] += 1
        if result.returncode:
            raise RuntimeError('FILM batch failed: ' + (result.stderr or '')[-5000:])
        if not film_report.is_file():
            raise RuntimeError('FILM batch did not produce the requested report.')
        actual_report = json.loads(film_report.read_text(encoding='utf-8-sig'))
        actual_jobs = actual_report.get('jobs', [])
        if len(actual_jobs) != len(film_jobs):
            raise RuntimeError('FILM report does not match the requested frame count.')
        for expected, actual in zip(film_jobs, actual_jobs):
            if abs(float(actual['actualDyadicTimestep']) - expected['timestep']) > 1e-12:
                raise RuntimeError('FILM quantized timestep differs from the retiming metadata.')
            if actual.get('engine') != 'google-film-tfhub-v1' or any(
                    Path(actual[field]).resolve() != Path(expected[field]).resolve()
                    for field in ['input0', 'input1', 'output']):
                raise RuntimeError('FILM report refers to a different interpolation request.')
        override['actualReport'] = {'file': label(film_report), 'sha256': sha(film_report), 'data': actual_report}
    expected_side = (args.size, args.size)
    for index, job in enumerate(jobs):
        output = Path(job['output'])
        if not output.is_file():
            raise RuntimeError(f'Interpolator did not produce requested forward frame {index + 1}.')
        with Image.open(output) as image:
            if image.size != expected_side:
                raise RuntimeError(f'Interpolator changed frame {index + 1} dimensions to {image.size}.')
    backend_run['elapsedSeconds'] = time.monotonic() - started


def interpolated_frames(args, records, progress, positions, weight_layer=None, backend_run=None, frame_corrections=None):
    frames = WORK / 'frames'
    frames.mkdir(exist_ok=True)
    raw_frames = WORK / 'raw-frames'
    raw_frames.mkdir(exist_ok=True)
    calls, forward_hands, jobs = [], [], []
    backend_run = backend_run if backend_run is not None else interpolation_provenance(args)
    started = time.monotonic()
    for index in range(37):
        desired = (1 - math.cos(math.pi * index / 36)) / 2
        interval = max(0, min(len(progress) - 2, bisect.bisect_right(progress, desired) - 1))
        fraction = min(1., max(0., (desired - progress[interval]) / (progress[interval + 1] - progress[interval])))
        output = raw_frames / f'frame_{index + 1:04d}.png'
        a, b = ROOT / records[interval]['file'], ROOT / records[interval + 1]['file']
        if fraction < 1e-7:
            fraction = 0.
        elif fraction > 1 - 1e-7:
            fraction = 1.
        requested_fraction = fraction
        engine = args.backend
        if interval in args.film_intervals:
            engine = 'google-film-tfhub-v1'
            fraction = round(fraction * 2 ** args.film_depth) / 2 ** args.film_depth
        jobs.append({'input0': str(a.resolve()), 'input1': str(b.resolve()),
                     'timestep': fraction, 'requestedTimestep': requested_fraction,
                     'engine': engine, 'sourceInterval': [interval, interval + 1],
                     'output': str(output.resolve())})
        forward_hands.append({hand: ((1 - fraction) * values[interval] + fraction * values[interval + 1]).tolist() for hand, values in positions.items()})
        call = {'frame': index + 1, 'progress': desired, 'sourceInterval': [interval, interval + 1],
                'engine': engine, 'requestedTimestep': requested_fraction, 'actualTimestep': fraction,
                'timestepError': fraction - requested_fraction,
                'timestep': fraction, 'interpolated': 0 < fraction < 1,
                'expectedHands': forward_hands[-1], 'rawFile': label(output)}
        if engine == 'google-film-tfhub-v1':
            call['dyadicDepth'] = args.film_depth
        if 'weightTop' in records[interval] and 'weightTop' in records[interval + 1]:
            call['expectedWeightTop'] = ((1 - fraction) * np.asarray(records[interval]['weightTop']) + fraction * np.asarray(records[interval + 1]['weightTop'])).tolist()
        calls.append(call)
    render_raw_frames(args, jobs, backend_run)
    for index, call in enumerate(calls):
        raw = ROOT / call['rawFile']
        output = frames / f'frame_{index + 1:04d}.png'
        shutil.copy2(raw, output)
        call['rawSha256'] = sha(raw)
        call['sha256'] = call['rawSha256']
        if weight_layer is not None:
            call['preLayerSha256'] = call['sha256']
            call['weightLayer'] = weight_layer.compose(output, call)
            call['sha256'] = sha(output)
        if frame_corrections is not None and call['frame'] in frame_corrections.by_frame:
            call['preCorrectionSha256'] = call['sha256']
            call['frameCorrections'] = frame_corrections.compose(output, call['frame'])
            call['sha256'] = sha(output)
        print(f'Pec deck v4: composed forward {index + 1}/37 ({time.monotonic() - started:.1f}s)', flush=True)
    for frame, source_frame in enumerate(range(36, 1, -1), start=38):
        source, target = frames / f'frame_{source_frame:04d}.png', frames / f'frame_{frame:04d}.png'
        shutil.copy2(source, target)
        call = {'frame': frame, 'reusesForwardFrame': source_frame, 'sha256': sha(target)}
        if 'weightLayer' in calls[source_frame - 1]:
            call['weightLayer'] = calls[source_frame - 1]['weightLayer']
        if 'frameCorrections' in calls[source_frame - 1]:
            call['frameCorrections'] = calls[source_frame - 1]['frameCorrections']
            call['frameCorrectionReusedFromForwardFrame'] = source_frame
        calls.append(call)
    return calls, forward_hands


def motion_metrics(calls, forward_hands, config):
    paths = [WORK / 'frames' / f'frame_{index:04d}.png' for index in range(1, 73)]
    frames = [np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) for path in paths]
    if len({image.shape for image in frames}) != 1:
        raise RuntimeError('Interpolator changed the output dimensions.')
    differences = [float(np.mean(np.abs(a - b))) for a, b in zip(frames[:36], frames[1:37])]
    maximum = max(differences)
    if maximum < .01:
        raise RuntimeError('Output contains no measurable image movement.')
    quality = config.get('quality', {})
    ratio = differences[-1] / maximum
    first_ratio = differences[0] / maximum
    limit = float(quality.get('maximumEndpointStepRatio', .40))
    issues = []
    if max(ratio, first_ratio) > limit:
        issues.append({'code': 'endpoint-image-jump', 'firstOverMaximum': first_ratio, 'lastOverMaximum': ratio,
                       'blocking': True, 'message': 'An endpoint image step is too large relative to ordinary motion; review the actual interpolated frames.'})
    median_difference = float(np.median(differences))
    jump_ratio = maximum / max(median_difference, .00001)
    if jump_ratio > float(quality.get('maximumImageJumpRatio', 4.0)):
        issues.append({'code': 'interior-image-step-disparity', 'maximumOverMedian': jump_ratio,
                       'blocking': bool(quality.get('enforceImageJumpRatio', False)),
                       'message': 'An interior image interval changes much faster than the median; inspect occlusion, exposure, or source-pose changes.'})
    expected_steps = {}
    for hand in ['near', 'far']:
        values = np.asarray([frame[hand] for frame in forward_hands])
        steps = np.linalg.norm(np.diff(values, axis=0), axis=1)
        expected_steps[hand] = {'maxStepPixels': float(max(steps)), 'lastStepPixels': float(steps[-1]),
                                'firstStepPixels': float(steps[0]), 'firstOverMax': float(steps[0] / max(steps)),
                                'lastOverMax': float(steps[-1] / max(steps)),
                                'maximumOverMedianStep': float(max(steps) / max(float(np.median(steps)), .000001)),
                                'retimedStepPixels': steps.tolist()}
        if steps[-1] / max(steps) > .25:
            issues.append({'code': 'expected-hand-endpoint-jump', 'hand': hand, 'blocking': True,
                           'message': f'{hand} hand has an abrupt final step in the retiming map.'})
    symmetry = all(sha(paths[frame - 1]) == sha(paths[source - 1]) for frame, source in zip(range(38, 73), range(36, 1, -1)))
    if not symmetry:
        raise RuntimeError('Return frames are not exact copies of the outward poses.')
    loop_difference = float(np.mean(np.abs(frames[-1] - frames[0])))
    start_difference = differences[0]
    if abs(loop_difference - start_difference) > 1e-6:
        raise RuntimeError('Loop seam does not match the mirrored start interval.')
    source_expected_weight = [call['expectedWeightTop'][1] for call in calls[:37] if 'expectedWeightTop' in call]
    layer_weight = [call['weightLayer']['plateTopOutputPixels'] for call in calls[:37] if 'weightLayer' in call]
    expected_weight = layer_weight if len(layer_weight) == 37 else source_expected_weight
    weight_monotonic = bool(len(expected_weight) == 37 and max(np.diff(expected_weight)) <= .000001)
    return {'forwardPixelMAEPerStep': differences, 'lastStepOverMaximumPixelMAE': ratio,
        'firstStepOverMaximumPixelMAE': first_ratio, 'maximumToMedianPixelStepRatio': jump_ratio,
        'maximumEndpointStepRatio': limit, 'endpointJumpGatePassed': max(ratio, first_ratio) <= limit,
        'firstLastPixelMAE': loop_difference, 'firstSecondPixelMAE': start_difference, 'exactMirroredReturn': symmetry,
        'expectedRetimedHandSteps': expected_steps, 'expectedWeightTopYForward': expected_weight,
        'sourceExpectedWeightTopYForward': source_expected_weight, 'compositedWeightTopYForward': layer_weight,
        'expectedWeightMonotonicRise': weight_monotonic, 'outputQualityIssues': issues,
        'landmarkMetricLimit': 'Hand positions between sources are expected values from the retiming map, not measured anatomical verification of RIFE output.'}


def encode(backend_run, frame_correction_records=()):
    spec = importlib.util.spec_from_file_location('gymrook_media_encoder', ROOT / 'scripts/encode-3d.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The shared helper finds output/<folder>/frames. Rename only this new
    # revision's encoded outputs to the standard exercise names afterward.
    record = module.encode('pec-deck-v4', ROOT / 'output', TARGET, 24, 72)
    renamed = {}
    for field in ['video', 'gif', 'poster']:
        old = record[field]
        new = old.replace('pec-deck-v4', 'pec-deck', 1)
        (TARGET / old).replace(TARGET / new)
        record[field] = new
        renamed[new] = record['files'][old]
    record['files'], record['id'], record['render'] = renamed, 'pec-deck', 'generated-interpolated'
    record['reviewStatus'] = 'Experimental continuity/perspective review; exercise execution not validated'
    engine_label = backend_run['model'] + (' + selected-interval Google FILM' if backend_run.get('filmOverride') else '')
    manifest = {'pipeline': 'Separate generated full-resolution poses → limited global fixed-feature stabilization → both-hand retiming → '
                           + engine_label + ' → deterministic tower layers → exact mirrored return',
                'interpolation': backend_run,
                'frameCorrections': list(frame_correction_records),
                'preferredFormat': 'MP4', 'fps': 24, 'animations': [record], 'reviewStatus': record['reviewStatus']}
    (TARGET / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'docs/generated-frames-v4/pec-deck/landmarks.json')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--size', type=int, default=512)
    parser.add_argument('--backend', choices=['practical-rife4.25', 'rife-ncnn-v4.6'], default='practical-rife4.25')
    parser.add_argument('--python-runtime', type=Path, default=PRACTICAL_CACHE / 'python311/python.exe')
    parser.add_argument('--batch-helper', type=Path, default=PRACTICAL_CACHE / 'rife425-batch.py')
    parser.add_argument('--practical-model', type=Path, default=PRACTICAL_CACHE / 'rife425')
    parser.add_argument('--integrity', type=Path, default=PRACTICAL_CACHE / 'modern-models-integrity.json')
    parser.add_argument('--scale', type=float, default=1., help='Practical-RIFE inference scale (default: 1).')
    parser.add_argument('--threads', type=int, default=8, help='Practical-RIFE CPU thread count.')
    parser.add_argument('--film-intervals', default='', help='Optional comma-separated source interval start indices for FILM, e.g. 0,7.')
    parser.add_argument('--film-helper', type=Path, default=PRACTICAL_CACHE / 'film-batch.py')
    parser.add_argument('--film-model', type=Path, default=PRACTICAL_CACHE / 'film-model')
    parser.add_argument('--film-depth', type=int, default=6, help='FILM recursive dyadic interpolation depth (default: 6).')
    parser.add_argument('--binary', type=Path, default=ROOT / '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-ncnn-vulkan.exe')
    parser.add_argument('--model', type=Path, default=ROOT / '.cache/interpolation/rife-ncnn-vulkan-20221029-windows/rife-v4.6')
    parser.add_argument('--gpu', default='0')
    parser.add_argument('--timestep-decimal', choices=['comma', 'dot'], default='comma')
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    if not config_path.is_file():
        parser.error('Config is not ready: ' + str(config_path))
    if args.size < 128 or args.size % 2:
        parser.error('--size must be an even value of at least 128 pixels.')
    if not math.isfinite(args.scale) or args.scale <= 0:
        parser.error('--scale must be a finite positive number.')
    if args.threads < 1:
        parser.error('--threads must be at least 1.')
    if not 1 <= args.film_depth <= 10:
        parser.error('--film-depth must be within 1..10.')
    try:
        args.film_intervals = set(int(item.strip()) for item in args.film_intervals.split(',') if item.strip())
    except ValueError:
        parser.error('--film-intervals must be comma-separated integer indices.')
    for field in ['python_runtime', 'batch_helper', 'practical_model', 'integrity', 'binary', 'model', 'film_helper', 'film_model']:
        path = getattr(args, field)
        setattr(args, field, path if path.is_absolute() else ROOT / path)
    config = json.loads(config_path.read_text(encoding='utf-8'))
    entries, reference_index = config_entries(config, config_path)
    if any(interval < 0 or interval >= len(entries) - 1 for interval in args.film_intervals):
        parser.error('--film-intervals indices must be within 0..' + str(len(entries) - 2))
    frame_corrections = FrameCorrections(config.get('frameCorrections', []), config_path, args.size)
    snapshot = preserve(config_path, entries, frame_corrections.paths)
    WORK.mkdir(parents=True, exist_ok=True)
    report = {'id': 'pec-deck', 'revision': 'v4', 'status': 'preparing', 'config': label(config_path),
              'sourceCount': len(entries), 'referenceIndex': reference_index, 'frameSize': [args.size, args.size],
              'interpolationBackend': args.backend,
              'filmOverrideIntervals': sorted(args.film_intervals),
              'frameCorrections': frame_corrections.report,
              'preservedFiles': snapshot, 'reviewStatus': 'Experimental image continuity; human execution is not validated.'}
    try:
        records, _, limits = prepare(config, entries, reference_index, args.size)
        report.update({'anchors': records, 'alignmentLimits': limits, 'status': 'prepared-for-source-review'})
        missing = [record['index'] for record in records if set(record['hands']) != {'near', 'far'}]
        report['missingHandLandmarks'] = missing
        report['qualityGateSettings'] = config.get('quality', {})
        weight_metrics = weight_progress(records, config)
        weight_layer = WeightLayer(config['weightLayer'], config_path, args.size) if config.get('weightLayer') else None
        if weight_layer is not None:
            report['weightLayer'] = weight_layer.report
            for issue in weight_metrics['sourceQualityIssues']:
                if issue['code'] in ['insufficient-weight-lift', 'weight-top-reversal']:
                    issue['blockingBeforeComposition'] = issue['blocking']
                    issue['blocking'] = False
                    issue['resolvedBy'] = 'The original generated tower band is explicitly replaced by one fixed base and one reviewed moving sprite; source coordinates are retained only to erase it safely.'
        report['sourceWeightMetrics'] = weight_metrics
        source_issues = list(weight_metrics['sourceQualityIssues'])
        if not missing:
            progress, progress_metrics, positions = hand_progress(records, config)
            report['sourceMotionMetrics'] = progress_metrics
            source_issues += progress_metrics['sourceQualityIssues']
        report['sourceQualityIssues'] = source_issues
        if args.prepare_only:
            verify_preserved(snapshot)
            report['preservationVerified'] = True
            write_report(report)
            print('Prepared aligned sources and output/pec-deck-v4/anchors-contact.png; no interpolation/encoding performed.')
            return
        if missing:
            raise ValueError('Supply both hand landmarks before interpolation: poses ' + ', '.join(map(str, missing)))
        blocking_source_issues = [issue for issue in source_issues if issue['blocking']]
        if blocking_source_issues:
            raise ValueError('Source review required before interpolation: ' + '; '.join(issue['message'] for issue in blocking_source_issues))
        rejected = [record['index'] for record in records if not record['alignment']['accepted']]
        if rejected and not config.get('alignment', {}).get('allowUnaligned', False):
            raise ValueError(f'Fixed-feature alignment needs review for poses {rejected}; inspect prepare-only output before explicitly allowing originals.')
        backend_run = interpolation_provenance(args)
        if args.film_intervals:
            backend_run['filmOverride'] = film_provenance(args)
        report['interpolation'] = backend_run
        calls, forward_hands = interpolated_frames(args, records, progress, positions, weight_layer, backend_run, frame_corrections)
        report['frames'] = calls
        report['outputMotionMetrics'] = motion_metrics(calls, forward_hands, config)
        blocking_output_issues = [issue for issue in report['outputMotionMetrics']['outputQualityIssues'] if issue['blocking']]
        if blocking_output_issues:
            raise ValueError('Interpolated output review required: ' + '; '.join(issue['message'] for issue in blocking_output_issues))
        report.update({'fps': 24, 'frameCount': 72, 'durationSeconds': 3,
                       'toolSha256': backend_run['tool']['sha256'], 'model': backend_run['model'],
                       'manifest': encode(backend_run, [correction for call in calls[:37] for correction in call.get('frameCorrections', [])]),
                       'status': 'encoded-for-visual-review'})
        verify_preserved(snapshot)
        report['preservationVerified'] = True
        write_report(report)
        print('Pec deck v4: 72 frames, 24 fps, 3 seconds; prior sources/assets preserved. Visual review is still required.')
    except Exception as error:
        report['status'], report['error'] = 'needs-review', str(error)
        verify_preserved(snapshot)
        report['preservationVerified'] = True
        write_report(report)
        raise


if __name__ == '__main__':
    main()
