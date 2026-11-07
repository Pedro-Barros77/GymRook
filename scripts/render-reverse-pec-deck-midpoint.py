"""Compose one raster-human reference with a small native equipment layer.

No human is rendered or deformed. The only parametric object is the distant
lever/grip. Original closed-pose hand pixels may be translated behind the
opaque human mask. This is one candidate key pose, not an animation renderer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT/'docs/generated-frames-bc-v1/reverse-pec-deck/midpoint-native-v1'
S = 4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    return path.resolve().relative_to(ROOT).as_posix()


def transverse_profile(source, box, low, high):
    x0, y0, x1, y1 = box
    profile = np.median(source[y0:y1, x0:x1].astype(float), axis=0)
    valid = ((profile.max(1)-profile.min(1) < 30)
             & (profile.mean(1) >= low) & (profile.mean(1) <= high))
    good = np.flatnonzero(valid)
    if not len(good):
        raise ValueError('No source material pixels in the declared sample patch.')
    for i in np.flatnonzero(~valid):
        profile[i] = profile[good[np.abs(good-i).argmin()]]
    u = np.linspace(0, len(profile)-1, 65)
    return np.clip(np.stack([np.interp(u, np.arange(len(profile)), profile[:, c])
                             for c in range(3)], axis=1), 0, 255).astype(np.uint8)


def lever_layer(control, half_width, material):
    t = np.linspace(0, 1, 257)[:, None]
    path = ((1-t)**3*control[0] + 3*(1-t)**2*t*control[1]
            + 3*(1-t)*t*t*control[2] + t**3*control[3])
    tangent = np.gradient(path, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    normal = np.stack([-tangent[:, 1], tangent[:, 0]], axis=1)
    lo = np.floor(path.min(0)-half_width-2).astype(int)
    hi = np.ceil(path.max(0)+half_width+2).astype(int)
    lo, hi = np.maximum(lo, 0), np.minimum(hi, 512)
    x, y = np.meshgrid((np.arange(lo[0]*S, hi[0]*S)+.5)/S,
                       (np.arange(lo[1]*S, hi[1]*S)+.5)/S)
    points = np.stack([x, y], axis=-1)
    delta = points[:, :, None, :]-path[None, None, :, :]
    closest = np.argmin(np.sum(delta*delta, axis=-1), axis=-1)
    relative = points-path[closest]
    side = np.sum(relative*normal[closest], axis=-1)
    distance = np.linalg.norm(relative, axis=-1)
    keep = ((distance <= half_width)
            & (np.sum((points-path[0])*tangent[0], axis=-1) >= 0)
            & (np.sum((points-path[-1])*tangent[-1], axis=-1) <= 0))
    u = np.clip(np.rint((side/half_width+1)*.5*(len(material)-1)).astype(int), 0, len(material)-1)
    patch = np.zeros((*x.shape, 4), np.uint8)
    patch[:, :, :3] = material[u]
    patch[:, :, 3] = keep.astype(np.uint8)*255
    layer = Image.new('RGBA', (512*S, 512*S))
    layer.paste(Image.fromarray(patch), (int(lo[0]*S), int(lo[1]*S)))
    return layer.resize((512, 512), Image.Resampling.LANCZOS), path


def grip_layer(center, metal, rubber):
    cx, cy = center
    layer = Image.new('RGBA', (512*S, 512*S))
    draw = ImageDraw.Draw(layer)
    radius, length = 8, 56
    for x in range(round((cx-radius)*S), round((cx+radius)*S)):
        u = min(len(rubber)-1, max(0, round(((x/S-cx)/radius+1)*.5*(len(rubber)-1))))
        draw.line((x, round((cy-length/2)*S), x, round((cy+length/2)*S)),
                  fill=(*map(int, rubber[u]), 255))
    for yy in [cy-length/2, cy+length/2]:
        draw.ellipse(((cx-radius-1)*S, (yy-3)*S, (cx+radius+1)*S, (yy+3)*S), fill=(163, 161, 158, 255))
        draw.arc(((cx-radius-1)*S, (yy-3)*S, (cx+radius+1)*S, (yy+3)*S), 180, 360,
                 fill=(*map(int, metal[len(metal)//2]), 255), width=S)
    return layer.resize((512, 512), Image.Resampling.LANCZOS)


def hand_layer(source, target, directory):
    polygon = [(315, 174), (317, 166), (322, 161), (327, 159),
               (335, 160), (341, 162), (344, 167), (343, 174)]
    mask_image = Image.new('L', (512, 512))
    ImageDraw.Draw(mask_image).polygon(polygon, fill=255)
    a = source.astype(np.int16)
    warm = (a[:, :, 0]-a[:, :, 2] > 25) & (a[:, :, 0]-a[:, :, 1] > 10) & (a.mean(2) > 40)
    mask = (np.asarray(mask_image) > 0) & warm
    Image.fromarray(mask.astype(np.uint8)*255).save(directory/'far-hand-source-mask.png')
    rgba = np.dstack([source, mask.astype(np.uint8)*255])
    hand = Image.fromarray(rgba)
    delta = np.rint(np.asarray(target)-[329, 168]).astype(int)
    result = Image.new('RGBA', (512, 512))
    result.paste(hand, tuple(map(int, delta)))
    return result, {'sourceHandCenter': [329, 168], 'targetHandCenter': list(target),
                    'integerTranslationPixels': delta.tolist(), 'sourcePolygon': polygon,
                    'method': 'Copy source RGB pixels with a binary skin mask; integer translation only, no resampling or hand drawing.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-dir', type=Path, default=DEFAULT)
    parser.add_argument('--gear-only', action='store_true')
    parser.add_argument('--grip-y', type=float, default=167)
    parser.add_argument('--pose', choices=['midpoint', 'quarter-closed', 'quarter-open'], default='midpoint')
    args = parser.parse_args()
    directory = args.assets_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    prefix = '' if args.pose == 'midpoint' else args.pose+'-'
    source_path = directory/'source-closed-512.png'
    if not source_path.exists():
        sheet_path = directory.parent/'sheet-v6-annotated-repair-candidate.png'
        with Image.open(sheet_path) as image:
            image.convert('RGB').crop((2, 2, 416, 416)).resize((512, 512), Image.Resampling.LANCZOS).save(source_path)
    source = np.asarray(Image.open(source_path).convert('RGB'))
    if source.shape != (512, 512, 3):
        raise ValueError('Closed source must be512x512RGB.')
    metal_box, rubber_box = [321, 110, 336, 126], [321, 141, 338, 155]
    metal = transverse_profile(source, metal_box, 60, 220)
    rubber = transverse_profile(source, rubber_box, 10, 100)
    Image.fromarray(np.repeat(metal[None], 32, axis=0)).save(directory/'material-profile.png')
    Image.fromarray(np.repeat(rubber[None], 32, axis=0)).save(directory/'rubber-profile.png')
    # One immutable world-space centerline. At yaw0 its weak-perspective
    # projection is exactly the already-reviewed midpoint centerline. Only a
    # rigid yaw and the fixed camera projection change for the quarter poses.
    camera_depth_y = .14
    radial = np.array([16., 45., 90., 90.])
    transverse = np.array([-10., -4., 1., 1.])
    midpoint_y = np.array([48., 60., 88., float(args.grip_y)-28])
    world_control = np.stack([radial, midpoint_y-34+camera_depth_y*radial, transverse], axis=1)
    target_x = {'midpoint': 252., 'quarter-closed': 290.5, 'quarter-open': 214.}[args.pose]
    yaw = math.asin((target_x-251)/math.hypot(90, 1))-math.atan2(1, 90)
    if args.pose == 'midpoint':
        yaw = 0.
    sine, cosine = math.sin(yaw), math.cos(yaw)
    def project(points):
        depth = points[:, 0]*cosine-points[:, 2]*sine
        return np.stack([251+points[:, 0]*sine+points[:, 2]*cosine,
                         34+points[:, 1]-camera_depth_y*depth], axis=1)
    control = project(world_control)
    grip_world = np.array([[90., float(args.grip_y)-34+camera_depth_y*90, 1.]])
    grip = project(grip_world)[0].tolist()
    metal_layer, centerline = lever_layer(control, 7., metal)
    black_layer = grip_layer(grip, metal, rubber)
    hand, hand_meta = hand_layer(source, grip, directory)
    metal_layer.save(directory/f'{prefix}metal-layer.png')
    black_layer.save(directory/f'{prefix}grip-layer.png')
    hand.save(directory/f'{prefix}far-hand-layer.png')
    metadata = {'status': 'single equipment-only midpoint candidate; source/motion review required',
                'generator': label(Path(__file__)), 'generatorSha256': sha(Path(__file__)),
                'source': label(source_path), 'sourceSha256': sha(source_path),
                'size': [512, 512], 'supersampling': S,
                'pose': args.pose,
                'geometry': {'type': 'Fixed world-space curved tube, fixed section and source-sampled transverse material; rigid yaw with a fixed weak-perspective camera.',
                             'controlPoints512': control.tolist(), 'halfWidthPixels': 7,
                             'fixedPivotCapCenterApprox512': [251, 34], 'mountExit512': [241, 48],
                             'gripCenter512': grip, 'gripRadiusPixels': 8, 'gripLengthPixels': 56,
                             'worldControlRadialVerticalTransverse': world_control.tolist(),
                             'worldGripCenter': grip_world.tolist(), 'yawRadians': yaw,
                             'yawDegrees': math.degrees(yaw), 'cameraDepthYFactor': camera_depth_y,
                             'worldGeometrySha256': hashlib.sha256(world_control.tobytes()+grip_world.tobytes()+np.array([7., 8., 56.]).tobytes()).hexdigest(),
                             'projectionSha256': hashlib.sha256(control.tobytes()+centerline.tobytes()).hexdigest(),
                             'geometryInvariant': 'World control points, tube section, grip and camera stay fixed. No screen-space control-point interpolation or metal length scaling.'},
                'material': {'metalPatchPixels': metal_box, 'rubberPatchPixels': rubber_box,
                             'method': 'One median transverse source RGB profile; no changing noise, lighting or texture.'},
                'hand': hand_meta,
                'coordinateNote': 'Root guide pivot196,20 and grip206,143 in418px. Actual fixed cap is near251,34 in the512 reference; attachment exits its underside. Grip raised about6source pixels for camera elevation.',
                'layers': ['clean-plate', 'metal', 'rubber-grip', 'translated-original-far-hand', 'opaque-original-human', 'fixed-original-cap']}
    if not args.gear_only:
        plate_path, mask_path = directory/'clean-plate.png', directory/'foreground-human-mask.png'
        plate = np.asarray(Image.open(plate_path).convert('RGB'))
        mask = np.asarray(Image.open(mask_path).convert('L'))
        if plate.shape != source.shape or mask.shape != (512, 512) or not set(np.unique(mask)).issubset({0, 255}):
            raise ValueError('Plate must be RGB512 and the opaque human mask must be binary L512.')
        result = Image.fromarray(plate).convert('RGBA')
        for layer in [metal_layer, black_layer, hand]:
            result = Image.alpha_composite(result, layer)
        final = np.asarray(result.convert('RGB')).copy()
        final[mask > 0] = plate[mask > 0]
        cap_path = directory/'fixed-cap-mask.png'
        if cap_path.exists():
            cap = np.asarray(Image.open(cap_path).convert('L')) > 0
        else:
            yy, xx = np.indices(mask.shape)
            cap = ((xx >= 228) & (xx < 276) & (yy >= 5) & (yy < 64)
                   & (plate.max(2)-plate.min(2) < 35) & (plate.mean(2) < 230))
            Image.fromarray(cap.astype(np.uint8)*255).save(cap_path)
        final[cap] = plate[cap]
        if not np.array_equal(final[mask > 0], plate[mask > 0]):
            raise RuntimeError('Opaque original human pixels changed.')
        output_path = directory/f'{args.pose}.png'
        Image.fromarray(final).save(output_path)
        metadata.update({'cleanPlate': label(plate_path), 'cleanPlateSha256': sha(plate_path),
                         'humanMask': label(mask_path), 'humanMaskSha256': sha(mask_path),
                         'fixedCapMaskSha256': sha(cap_path), 'midpointSha256': sha(output_path),
                         'humanPixelsPreserved': int(np.count_nonzero(mask)),
                         'status': 'composed candidate; root and independent source QA required'})
    metadata['outputs'] = {f'{prefix}{name}-layer.png': sha(directory/f'{prefix}{name}-layer.png')
                           for name in ['metal', 'grip', 'far-hand']}
    metadata_name = 'midpoint-metadata.json' if args.pose == 'midpoint' else f'{args.pose}-metadata.json'
    (directory/metadata_name).write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print('Rendered equipment only.' if args.gear_only else f'Composed {directory / (args.pose+".png")}', flush=True)


if __name__ == '__main__':
    main()
