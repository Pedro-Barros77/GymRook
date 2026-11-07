"""Render approved material-v3 pec-deck equipment with connection-v4 shaft tracking.

The fixed curved mesh is shared by both arms and every frame. Only yaw changes; yaw follows the actual observed rubber-shaft axis.
Source-generated silver supplies one stable material profile. The renderer never
renders or warps the human, and every output pixel at y>=164 is transparent.
Run with --help for the self-contained source and motion snapshot paths.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, json, math, hashlib, argparse
root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description='Render the approved rigid pec-deck silver levers without rendering or warping the human.')
parser.add_argument('--output', type=Path, default=root / 'docs/generated-frames-v5/pec-deck/rigid-levers')
parser.add_argument('--canonical-source', type=Path, default=root / 'docs/generated-frames-v5/pec-deck/rigid-levers/canonical-source-512.png')
parser.add_argument('--motion-report', type=Path, default=root / 'docs/generated-frames-v5/pec-deck/rigid-levers/motion-37.json')
parser.add_argument('--axis-fits', type=Path, default=root / 'docs/generated-frames-v5/pec-deck/rigid-levers/shaft-axis-fits-smoothed.json')
parser.add_argument('--frames', help='Optional comma-separated forward frame numbers, for example1,12,20,37. Default: all37.')
args = parser.parse_args()
dest = args.output.resolve()
frames = dest / 'frames'
frames.mkdir(exist_ok=True, parents=True)
canonical_source = args.canonical_source.resolve()
motion_path = args.motion_report.resolve()
reference = np.asarray(Image.open(canonical_source).convert('RGB'))
if reference.shape != (512, 512, 3):
    raise ValueError('Canonical source must be512x512RGB.')
report = json.loads(motion_path.read_text(encoding='utf-8-sig'))
axis_document = json.loads(args.axis_fits.read_text(encoding='utf-8-sig'))
axis_by_frame = {r['frame']: r['hands'] for r in axis_document['frames']}
selected = set(map(int, args.frames.split(','))) if args.frames else None
forward = [f for f in report['frames'][:37] if selected is None or f['frame'] in selected]
if not forward or len({f['frame'] for f in forward}) != len(forward):
    raise ValueError('Frame selection is empty or duplicates frame numbers.')
source_points = np.array([[246, 43], [329, 92], [354, 121], [358, 145]], float)
world_points = np.array([[0.03 * 150, 9, 0], [0.76 * 150, 61, 0], [0.99 * 150, 91, 0], [150, 118, 0]], float)

def catmull(points, count):
    padded = np.vstack((points[0] + (points[0] - points[1]), points, points[-1] + (points[-1] - points[-2])))
    result = []
    for t in np.linspace(0, len(points) - 1, count):
        i = min(int(t), len(points) - 2)
        u = t - i
        p0, p1, p2, p3 = padded[i:i + 4]
        result.append(0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u))
    return np.asarray(result)
source = catmull(source_points, 256)
st = np.gradient(source, axis=0)
st /= np.linalg.norm(st, axis=1)[:, None]
sn = np.stack((-st[:, 1], st[:, 0]), axis=1)
xs = np.linspace(-11, 11, 33)
coords = source[:, None, :] + sn[:, None, :] * xs[None, :, None]
ix = np.clip(np.rint(coords[:, :, 0]).astype(int), 0, 511)
iy = np.clip(np.rint(coords[:, :, 1]).astype(int), 0, 511)
atlas = reference[iy, ix].copy()
for row in atlas:
    good = (row.max(1) - row.min(1) < 24) & (row.mean(1) > 65) & (row.mean(1) < 235)
    if good.any():
        ids = np.flatnonzero(good)
        for i in np.flatnonzero(~good):
            row[i] = row[ids[np.abs(ids - i).argmin()]]
patch = reference[125:143, 344:366].astype(float)
stripe = np.median(patch, axis=0)
stripe = np.stack([np.interp(np.linspace(0, len(stripe) - 1, 33), np.arange(len(stripe)), stripe[:, c]) for c in range(3)], axis=1)
atlas = np.repeat(np.clip(stripe, 65, 200).astype(np.uint8)[None, :, :], 256, axis=0)
Image.fromarray(atlas).resize((132, 1024)).save(dest / 'canonical-material-atlas.png')
over = Image.fromarray(reference)
d = ImageDraw.Draw(over)
d.line([tuple(x) for x in source], fill='#ff00aa', width=2)
over.save(dest / 'material-source-guide.png')

def monotone_profile():
    ys = world_points[:, 1]
    xs = world_points[:, 0].copy()
    xs[2] = 150
    slopes = np.diff(xs) / np.diff(ys)
    m = np.zeros(4)
    m[0] = slopes[0]
    for j in [1, 2]:
        m[j] = 0 if slopes[j - 1] * slopes[j] <= 0 else 2 / (1 / slopes[j - 1] + 1 / slopes[j])
    result = []
    for y in np.linspace(ys[0], ys[-1], 65):
        i = min(np.searchsorted(ys, y, side='right') - 1, 2)
        i = max(i, 0)
        h = ys[i + 1] - ys[i]
        t = (y - ys[i]) / h
        x = (2 * t ** 3 - 3 * t * t + 1) * xs[i] + (t ** 3 - 2 * t * t + t) * h * m[i] + (-2 * t ** 3 + 3 * t * t) * xs[i + 1] + (t ** 3 - t * t) * h * m[i + 1]
        result.append([x, y, 0])
    return np.asarray(result)
profile = monotone_profile()
tangent = np.gradient(profile, axis=0)
tangent /= np.linalg.norm(tangent, axis=1)[:, None]
normal = np.stack((-tangent[:, 1], tangent[:, 0], np.zeros(len(profile))), axis=1)
section = np.array([[-7, -7], [-4, -10], [4, -10], [7, -7], [7, 7], [4, 10], [-4, 10], [-7, 7]], float)
verts = np.stack([profile + normal * dn + np.array([0, 0, dz]) for dn, dz in section], axis=1)
faces = []
uvs = []
for i in range(len(profile) - 1):
    for j in range(len(section)):
        k = (j + 1) % len(section)
        a = i * 8 + j
        b = i * 8 + k
        c = (i + 1) * 8 + j
        d0 = (i + 1) * 8 + k
        uj = (section[j, 0] + 7) / 14
        uk = (section[k, 0] + 7) / 14
        faces.extend([(a, b, c), (b, d0, c)])
        uvs.extend([[(uj, i / 64), (uk, i / 64), (uj, (i + 1) / 64)], [(uk, i / 64), (uk, (i + 1) / 64), (uj, (i + 1) / 64)]])
normal_verts = np.stack([normal * (dn / 7) + np.array([0, 0, dz / 10]) for dn, dz in section], axis=1).reshape(-1, 3)
normal_verts /= np.linalg.norm(normal_verts, axis=1)[:, None]
verts = verts.reshape(-1, 3)
start = len(verts)
ring = []
ring_normals = []
ring_kinds = []

def add_ring_group(kind, r0, r1, y0, y1):
    base = start + len(ring)
    for radius, y in [(r0, y0), (r1, y1)]:
        for a in np.linspace(0, 2 * math.pi, 33)[:-1]:
            ring.append([150 + radius * math.cos(a), y, radius * math.sin(a)])
            if kind == 1:
                ring_normals.append([math.cos(a), 0, math.sin(a)])
            elif kind == 2:
                ring_normals.append([0, -1, 0])
            elif kind == 3:
                ring_normals.append([0, 1, 0])
            else:
                ring_normals.append([-math.cos(a), 0, -math.sin(a)])
    for j in range(32):
        k = (j + 1) % 32
        a = base + j
        b = base + k
        c = base + 32 + j
        d0 = base + 32 + k
        faces.extend([(a, b, c), (b, d0, c)])
        uvs.extend([[([0.5][0], 0.96), (0.5, 0.96), (0.5, 1)], [(0.5, 0.96), (0.5, 1), (0.5, 1)]])
        ring_kinds.extend([kind, kind])
add_ring_group(1, 12, 12, 115, 121)
add_ring_group(2, 12, 9.5, 115, 115)
add_ring_group(3, 12, 9.5, 121, 121)
add_ring_group(4, 9.5, 9.5, 115, 121)
normal_verts = np.vstack((normal_verts, np.asarray(ring_normals)))
verts = np.vstack((verts, np.asarray(ring)))
faces = np.asarray(faces)
uvs = np.asarray(uvs)
mesh_hash = hashlib.sha256(verts.tobytes() + faces.tobytes()).hexdigest()
S = 3
W = H = 512 * S

def raster(points, zs, color_uv, normals, is_ring, rgba, zbuf):
    xmin = max(0, int(np.floor(points[:, 0].min())))
    xmax = min(W - 1, int(np.ceil(points[:, 0].max())))
    ymin = max(0, int(np.floor(points[:, 1].min())))
    ymax = min(H - 1, int(np.ceil(points[:, 1].max())))
    if xmin > xmax or ymin > ymax:
        return
    x, y = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
    a, b, c = points
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-08:
        return
    w0 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / den
    w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
    w2 = 1 - w0 - w1
    depth = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
    zb = zbuf[ymin:ymax + 1, xmin:xmax + 1]
    mask = (w0 >= -1e-05) & (w1 >= -1e-05) & (w2 >= -1e-05) & (depth < zb)
    if not mask.any():
        return
    uv = w0[:, :, None] * color_uv[0] + w1[:, :, None] * color_uv[1] + w2[:, :, None] * color_uv[2]
    u = np.clip(np.rint(uv[:, :, 0] * 32).astype(int), 0, 32)
    v = np.clip(np.rint(uv[:, :, 1] * 255).astype(int), 0, 255)
    nn = w0[:, :, None] * normals[0] + w1[:, :, None] * normals[1] + w2[:, :, None] * normals[2]
    nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-08)
    ndotl = np.maximum(0, nn @ light)
    ndoth = np.maximum(0, nn @ half_light)
    spec = ndoth ** (22 if is_ring else 28)
    base = (rubber_atlas if is_ring == 5 else atlas)[v, u].astype(float)
    if is_ring == 5:
        color = base * (0.95 + 0.05 * ndotl[:, :, None]) + 8 * spec[:, :, None]
    elif is_ring:
        vv = np.clip((uv[:, :, 1] - 0.96) / 0.04, 0, 1)
        rim = 0.82 + 0.18 * np.sin(np.pi * vv)
        color = base * (1.15 + 0.3 * ndotl[:, :, None]) * rim[:, :, None] + 85 * spec[:, :, None] + 18 * (ndoth ** 4)[:, :, None]
        if is_ring == 2:
            color = base * (1.6 + 0.2 * ndotl[:, :, None]) + 38 * spec[:, :, None]
        elif is_ring == 3:
            color = base * (1.0 + 0.2 * ndotl[:, :, None]) + 35 * spec[:, :, None]
        elif is_ring == 4:
            color = base * (0.65 + 0.2 * ndotl[:, :, None])
    else:
        color = 1.12 * base * (0.7 + 0.45 * ndotl[:, :, None]) + 56 * spec[:, :, None] + 10 * (ndoth ** 4)[:, :, None]
    color = np.clip(color, 0, 255).astype(np.uint8)
    sub = rgba[ymin:ymax + 1, xmin:xmax + 1]
    sub[mask, :3] = color[mask]
    sub[mask, 3] = 255
    zb[mask] = depth[mask]
light = np.array([-0.45, -0.55, -1.0])
light /= np.linalg.norm(light)
half_light = light + np.array([0.0, 0.0, -1.0])
half_light /= np.linalg.norm(half_light)

def render_arm(frame, instance, rgba, zbuf):
    scale = instance['scale']
    pivot = np.array(instance['pivot'])
    axis = axis_by_frame[frame['frame']][instance['hand']]
    collar_y = float(pivot[1] + 118 * scale)
    hx = axis['smoothedXAt149'] + axis['smoothedSlopeDxDy'] * (collar_y - 149)
    dx = hx - pivot[0]
    theta = math.asin(np.clip(dx / (150 * scale), -0.9999, 0.9999))
    si, co = (math.sin(theta), math.cos(theta))
    rot = np.array([[si, 0, co], [0, 1, 0], [-co, 0, si]])
    world = verts @ rot.T * scale
    normals = normal_verts @ rot.T
    beta = math.radians(10)
    cb, sb = (math.cos(beta), math.sin(beta))
    center = np.array([150, 118, 0]) @ rot.T * scale
    rel = world[520:] - center
    yy = rel[:, 1].copy()
    zz0 = rel[:, 2].copy()
    world[520:, 1] = center[1] + cb * yy - sb * zz0
    world[520:, 2] = center[2] + sb * yy + cb * zz0
    yy = normals[520:, 1].copy()
    zz0 = normals[520:, 2].copy()
    normals[520:, 1] = cb * yy - sb * zz0
    normals[520:, 2] = sb * yy + cb * zz0
    xy = (world[:, :2] + pivot) * S
    zz = world[:, 2] + instance['depth']
    for face_index, (face, uv) in enumerate(zip(faces, uvs)):
        tri = world[face]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        n /= max(np.linalg.norm(n), 1e-06)
        shade = 0.96 + 0.1 * max(0, float(n @ light))
        if face.min() >= 65 * 8:
            shade = 1.35 + 0.08 * max(0, float(n @ light))
        if face_index < 1024:
            j = face_index // 2 % 8
            k = (j + 1) % 8
            edge = section[k] - section[j]
            section_normal = np.array([edge[1], -edge[0]])
            section_normal /= np.linalg.norm(section_normal)
            ns = []
            for vid in face:
                ii = int(vid) // 8
                local = normal[ii] * section_normal[0] + np.array([0, 0, section_normal[1]])
                ns.append(local @ rot.T)
            ns = np.asarray(ns)
            kind = 0
        else:
            ns = normals[face]
            kind = ring_kinds[face_index - 1024]
        raster(xy[face], zz[face], uv, ns, kind, rgba, zbuf)
    return dict(hand=instance['hand'], pivot=pivot.tolist(), yawRadians=theta, collarCenter=[float(hx), float(pivot[1] + 118 * scale)], requestedHandCenter=frame['expectedHands'][instance['hand']], worldMeshSha256=mesh_hash, scale=scale)
rubber_vertices = []
rubber_normals = []
rubber_faces = []
rubber_uvs = []
for y in [4.0, 18.0]:
    for angle in np.linspace(0, 2 * math.pi, 33)[:-1]:
        rubber_vertices.append([8 * math.cos(angle), y, 8 * math.sin(angle)])
        rubber_normals.append([math.cos(angle), 0, math.sin(angle)])
for j in range(32):
    k = (j + 1) % 32
    a = j
    b = k
    c = 32 + j
    dd = 32 + k
    uj = (math.cos(2 * math.pi * j / 32) + 1) / 2
    uk = (math.cos(2 * math.pi * k / 32) + 1) / 2
    rubber_faces.extend([(a, b, c), (b, dd, c)])
    rubber_uvs.extend([[(uj, 0), (uk, 0), (uj, 1)], [(uk, 0), (uk, 1), (uj, 1)]])
rubber_vertices = np.asarray(rubber_vertices)
rubber_normals = np.asarray(rubber_normals)
rubber_faces = np.asarray(rubber_faces)
rubber_uvs = np.asarray(rubber_uvs)
rubber_mesh_sha256 = hashlib.sha256(rubber_vertices.tobytes() + rubber_faces.tobytes()).hexdigest()
canonical_axis = axis_by_frame[37]['near']
stripes = []
for yy in range(160, 170):
    center = canonical_axis['xAt164'] + canonical_axis['slopeDxDy'] * (yy - 164)
    xx = center + np.linspace(-7.5, 7.5, 33)
    left = np.floor(xx).astype(int)
    fraction = xx - left
    stripes.append(reference[yy, left] * (1 - fraction[:, None]) + reference[yy, left + 1] * fraction[:, None])
rubber_atlas = np.repeat(np.median(np.asarray(stripes), axis=0).astype(np.uint8)[None, :, :], 256, axis=0)
Image.fromarray(rubber_atlas).resize((132, 1024)).save(dest / 'rubber-material-atlas.png')

def render_rubber(frame, instance, rgba, zbuf):
    axis = axis_by_frame[frame['frame']][instance['hand']]
    scale = instance['scale']
    slope = axis['smoothedSlopeDxDy']
    origin_y = float(instance['pivot'][1] + 118 * scale)
    origin_x = axis['smoothedXAt149'] + slope * (origin_y - 149)
    dx = origin_x - instance['pivot'][0]
    theta = math.asin(np.clip(dx / (150 * scale), -0.9999, 0.9999))
    origin_z = instance['depth'] - 150 * scale * math.cos(theta)
    angle = -math.atan(slope)
    cc, ss = (math.cos(angle), math.sin(angle))
    rotation = np.array([[cc, -ss, 0], [ss, cc, 0], [0, 0, 1]])
    positions = rubber_vertices @ rotation.T * scale + np.array([origin_x, origin_y, origin_z])
    normals = rubber_normals @ rotation.T
    for face, uv in zip(rubber_faces, rubber_uvs):
        raster(positions[face, :2] * S, positions[face, 2], uv, normals[face], 5, rgba, zbuf)
    return dict(hand=instance['hand'], fixedMeshSha256=rubber_mesh_sha256, origin=[origin_x, origin_y, origin_z], rigidRotationZRadians=angle, scale=scale, sourceAxisAt149=axis['smoothedXAt149'], sourceAxisAt164=axis['smoothedXAt164'], actualInterfaceDrift=axis['smoothingDriftAt164'])
instances = [dict(hand='far', pivot=[335, 40], scale=109 / 118, collarXOffset=0.7, depth=300), dict(hand='near', pivot=[239, 31], scale=1, collarXOffset=1.5, depth=0)]
metadata = []
for f in forward:
    rgba = np.zeros((H, W, 4), np.uint8)
    zbuf = np.full((H, W), np.inf)
    transforms = [render_arm(f, i, rgba, zbuf) for i in instances]
    rgba[:35 * S, :300 * S, 3] = 0
    rgba[:45 * S, 300 * S:, 3] = 0
    rubber_transforms = [render_rubber(f, instance, rgba, zbuf) for instance in instances]
    image = Image.fromarray(rgba, 'RGBA').resize((512, 512), Image.Resampling.LANCZOS)
    arr = np.array(image)
    arr[164:, :, 3] = 0
    image = Image.fromarray(arr, 'RGBA')
    image.save(frames / f"frame_{f['frame']:04d}.png")
    metadata.append(dict(frame=f['frame'], instances=transforms, rubberConnectors=rubber_transforms))
    print('rendered', f['frame'], flush=True)
canonical_profile = world_points.tolist()
canonical_profile[2][0] = 150.0
metadata_document = dict(status='approved-rigid-levers-material-v3-connection-v4', version=4, meshSha256=mesh_hash, source=str(canonical_source.relative_to(root)) if canonical_source.is_relative_to(root) else str(canonical_source), sourceSha256=hashlib.sha256(canonical_source.read_bytes()).hexdigest(), motionReport=str(motion_path.relative_to(root)) if motion_path.is_relative_to(root) else str(motion_path), motionReportSha256=hashlib.sha256(motion_path.read_bytes()).hexdigest(), materialSampling='Single transverse RGB profile sampled from canonical generated silver, continuous across broad flat faces. Fixed-world softbox with narrow bevel highlights and reduced specular.', geometry='Single fixed beveled rectangular curved tube; per-frame yaw only, fixed weak-perspective instances. Annular collars use constant10degree local view.', camera='Fixed orthographic on booms; fixed10degree view on collars about their own centers.', canonicalProfile=canonical_profile, profileSamplingMethod='Monotone cubic in height. Radial extent reachesR150 byheight91 and remainsconstantthroughlowerverticalend.', crossSection=section.tolist(), collarProjectionElevationDegrees=10, sourceMetalPatchPixels=[344, 125, 366, 143], rubberSamplePatchPixels=[361, 164, 366, 169], light=light.tolist(), halfVector=half_light.tolist(), instances=instances, includes='Silver moving booms, rigid annular collars and short sampled-rubber connectors. No human pixels or fixed pivot drums.', protectedRows=[164, 512], limitations=['CollarY149 is fixed while independently generated source collars vary by a few pixels.', 'Far instance uses a fixed weak-perspective scale109/118.', 'Material reuses generated silver pixels with deterministic lighting; it is not a calibrated multi-view BRDF.', 'Compose over the upper clean plate before evaluating removal of the old silver arms.'], frames=metadata)
metadata_document['rubberGeometrySha256'] = rubber_mesh_sha256
metadata_document['rubberMaterialSampling'] = 'One stable transverse RGB profile from the generated canonical rubber shaft; fixed cylinder and rigid Z rotation only.'
metadata_document['rubberGeometry'] = {'type': 'one fixed radius8 height14 cylinder mesh, perframe rigidZ rotation only, fixedweakperspectiveinstance scale', 'protectedBoundary': 'Geometry extends below164 during supersampling; final alpha is zeroed only after downsampling so row163 stays fully connected.'}
metadata_document['axisFits'] = {'file': args.axis_fits.name, 'sha256': hashlib.sha256(args.axis_fits.read_bytes()).hexdigest(), 'method': axis_document['method'], 'temporalRegularization': axis_document['temporalRegularization'], 'sourceProvenance': axis_document['sourceProvenance']}
(dest / 'metadata.json').write_text(json.dumps(metadata_document, indent=2) + '\n', encoding='utf-8')
frame_manifest = []
for item in metadata:
    number = item['frame']
    path = frames / f'frame_{number:04d}.png'
    rgba = np.asarray(Image.open(path))
    ys, xs = np.nonzero(rgba[:, :, 3])
    if rgba.shape != (512, 512, 4) or not len(xs) or rgba[164:, :, 3].any():
        raise RuntimeError('Invalid RGBA or protected-row coverage in ' + str(path))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    approved = report.get('approvedConnectionPreviewSha256', {}).get(str(number))
    if approved and metadata_document['sourceSha256'] == report.get('canonicalSourceSha256') and (hashlib.sha256(args.axis_fits.read_bytes()).hexdigest() == report.get('axisFitsSmoothedSha256')) and (digest != approved):
        raise RuntimeError('Approved connection preview did not reproduce exactly for frame' + str(number))
    frame_manifest.append(dict(frame=number, file=path.relative_to(dest).as_posix(), sha256=digest, alphaBounds=[int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)], protectedRows164To511AlphaMaximum=0, transform=item['instances'], rubberConnectors=item['rubberConnectors']))
manifest = dict(engine='rigid-equipment-material-v3-connection-v4', status='approved-connection-v4-frozen', geometrySha256=mesh_hash, sourceTexture='canonical-material-atlas.png', sourceTextureSha256=hashlib.sha256((dest / 'canonical-material-atlas.png').read_bytes()).hexdigest(), textureOriginal=metadata_document['source'], textureOriginalSha256=metadata_document['sourceSha256'], frameCount=len(frame_manifest), frameSize=[512, 512], hasAlpha=True, geometryInvariant='One fixed world vertex buffer and cross section; fixed pivots; per-frame yaw only; constant cap projection.', modelDescription='Curved beveled rectangular silver tube and annular collar. No humanoid mesh, human rendering or human warping.', generator='scripts/render-pec-deck-rigid-levers.py', generatorSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), metadata='metadata.json', axisRawFits='shaft-axis-fits.json', axisRawFitsSha256=hashlib.sha256((args.axis_fits.parent / 'shaft-axis-fits.json').read_bytes()).hexdigest(), axisFits=args.axis_fits.name, axisFitsSha256=hashlib.sha256(args.axis_fits.read_bytes()).hexdigest(), rubberGeometrySha256=rubber_mesh_sha256, frames=frame_manifest)
manifest['rubberMaterial'] = 'rubber-material-atlas.png'
manifest['rubberMaterialSha256'] = hashlib.sha256((dest / 'rubber-material-atlas.png').read_bytes()).hexdigest()
manifest['axisSourceProvenance'] = axis_document['sourceProvenance']
(dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(output=str(dest), frameCount=len(frame_manifest), geometrySha256=mesh_hash, protectedRowsAlphaMaximum=0)), flush=True)
for source_path in [args.axis_fits, args.axis_fits.parent / 'shaft-axis-fits.json']:
    destination = dest / source_path.name
    if source_path.resolve() != destination.resolve():
        destination.write_bytes(source_path.read_bytes())
