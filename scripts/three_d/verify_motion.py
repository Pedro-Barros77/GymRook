"""Verify continuity and mechanical constraints from the rendered 3D scene data."""
from pathlib import Path
from math import dist, sqrt
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
EXERCISES = ['pec-deck', 'incline-dumbbell-press', 'reverse-cable-curl', 'push-up']
rest = json.loads((ROOT / 'assets/3d/human/rest-joints.json').read_text())


def subtract(a, b):
    return [x - y for x, y in zip(a, b)]


for exercise in EXERCISES:
    path = ROOT / 'output/3d' / exercise / 'motion.json'
    data = json.loads(path.read_text())
    frames = data['frames']
    assert data['fps'] == 24 and len(frames) == data['frameCount'] == 72, exercise
    assert [frame['frame'] for frame in frames] == list(range(1, 73)), exercise
    scene = ROOT / data['scene']
    assert scene.is_file(), scene
    assert hashlib.sha256(scene.read_bytes()).hexdigest() == data['sceneSha256'], 'Saved scene changed after recording'
    assert data['humanBoneCount'] > 100 and data['humanVertexCount'] > 10000, 'Expected the actual skinned human mesh'
    first = frames[0]
    for frame in frames:
        assert frame['cameraMatrix'] == first['cameraMatrix'], 'Camera movement would introduce screenshake'
        assert frame['equipmentRootMatrix'] == first['equipmentRootMatrix'], 'Equipment base moved'
        for side in ['left', 'right']:
            for start, end in [('shoulder', 'elbow'), ('elbow', 'wrist')]:
                a, b = f'{side}_{start}', f'{side}_{end}'
                assert abs(dist(frame['joints'][a], frame['joints'][b]) - dist(rest[a], rest[b])) < .0001, 'Arm changed proportions'
        fixed = ['left_ankle', 'right_ankle', 'left_toe', 'right_toe']
        if exercise != 'push-up':
            fixed += ['pelvis', 'chest', 'head']
        for joint in fixed:
            assert dist(frame['joints'][joint], first['joints'][joint]) < .000001, f'{exercise}: support/torso drift at {joint}'
    # Check the actual loop seam against ordinary frame-to-frame velocities and
    # accelerations. A sudden return to a different bottom pose fails this test.
    for side in ['left', 'right']:
        moving_joint = f'{side}_elbow' if exercise == 'push-up' else f'{side}_wrist'
        points = [frame['joints'][moving_joint] for frame in frames]
        velocities = [subtract(points[(i + 1) % 72], points[i]) for i in range(72)]
        magnitudes = [sqrt(sum(component * component for component in v)) for v in velocities]
        assert max(magnitudes) > .001, f'{exercise}: expected joint did not move'
        assert magnitudes[-1] < max(magnitudes[:-1]) * .20, f'{exercise}: loop seam jumps'
        accelerations = [dist(velocities[(i + 1) % 72], velocities[i]) for i in range(72)]
        assert accelerations[-1] <= max(accelerations[:-1]) * 1.03 + .00001, f'{exercise}: loop acceleration spike'
    if exercise in ['pec-deck', 'reverse-cable-curl']:
        lifts = [frame['equipment']['weight_lift'] for frame in frames]
        assert abs(lifts[0]) < .000001 and lifts[36] > .05, 'Selected load must rise from the actual low-position baseline'
        assert all(a <= b + .000001 for a, b in zip(lifts[:36], lifts[1:37])), 'Load moved down during effort'
        assert all(a >= b - .000001 for a, b in zip(lifts[36:-1], lifts[37:])), 'Load moved up during return'
    if exercise == 'pec-deck':
        for frame in frames:
            left = frame['equipment']['left_handle']
            right = frame['equipment']['right_handle']
            assert abs(left[0] + right[0]) < .000001 and dist(left[1:], right[1:]) < .000001, 'Pec-deck levers lost bilateral symmetry'
    pngs = list((path.parent / 'frames').glob('frame_*.png'))
    assert len(pngs) == 72, f'{exercise}: incomplete render sequence ({len(pngs)}/72)'
    print(f'{exercise}: 72 frames, fixed camera/equipment, constant bones, stable supports and smooth loop verified.')
