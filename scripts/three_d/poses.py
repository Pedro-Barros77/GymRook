"""Deterministic world-space exercise poses; meters, +Y forward, +Z up.

The same continuous phase drives the human, machine levers, cable and weights.
No pose is inferred from an independently generated image.
"""
from pathlib import Path
from math import sin, cos, pi, sqrt
import json
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
REST = {key: Vector(value) for key, value in json.loads((ROOT / 'assets/3d/human/rest-joints.json').read_text()).items()}
UPPER = (REST['left_elbow'] - REST['left_shoulder']).length
LOWER = (REST['left_wrist'] - REST['left_elbow']).length
THIGH = (REST['left_knee'] - REST['left_hip']).length
SHIN = (REST['left_ankle'] - REST['left_knee']).length


def phase_at(frame, total=72):
    # Sample a periodic cosine without duplicating the first pose at the end.
    # First derivative is zero at both reversals, eliminating bottom-pose snaps.
    return (1.0 - cos(2 * pi * (frame - 1) / total)) * .5


def two_bone(origin, target, pole, first=UPPER, second=LOWER):
    origin, target, pole = Vector(origin), Vector(target), Vector(pole)
    delta = target - origin
    distance = min(max(delta.length, abs(first - second) + .012), first + second - .001)
    direction = delta.normalized()
    target = origin + direction * distance
    along = (first * first - second * second + distance * distance) / (2 * distance)
    height = sqrt(max(0.0, first * first - along * along))
    bend = pole - origin
    bend = bend - direction * bend.dot(direction)
    if bend.length < .001:
        bend = direction.cross(Vector((1, 0, 0)))
    elbow = origin + along * direction + height * bend.normalized()
    return elbow, target


def transformed_rest(pelvis, rotation=None):
    rotation = rotation or Matrix.Identity(3)
    return {key: Vector(pelvis) + rotation @ (value - REST['pelvis']) for key, value in REST.items()}


def seated_legs(joints, ankle_y=.55):
    for side, sign in [('left', 1), ('right', -1)]:
        hip = joints[f'{side}_hip']
        ankle = Vector((sign * .16, ankle_y, .085))
        knee, ankle = two_bone(hip, ankle, (sign * .18, .7, .58), THIGH, SHIN)
        joints[f'{side}_knee'] = knee
        joints[f'{side}_ankle'] = ankle
        joints[f'{side}_toe'] = ankle + Vector((0, .145, -.04))


def exercise_pose(exercise, phase, equipment):
    grip, hand_roll, palm_normals = 1.0, {'left': 0.0, 'right': 0.0}, {}
    if exercise == 'pec-deck':
        joints = transformed_rest((0, 0, .61))
        seated_legs(joints)
        targets = equipment.hand_targets(phase)
        for side, sign in [('left', 1), ('right', -1)]:
            shoulder = joints[f'{side}_shoulder']
            # The handle is held just beyond the wrist. The elbow follows a
            # stable outward bend plane and the torso is never re-positioned.
            palm = Vector(targets[side])
            elbow, palm = two_bone(shoulder, palm, shoulder + Vector((sign * .32, .20, -.08)), UPPER, LOWER + .096)
            wrist = elbow + (palm - elbow).normalized() * LOWER
            joints[f'{side}_elbow'], joints[f'{side}_wrist'] = elbow, wrist
            joints[f'{side}_hand'] = palm
            joints[f'{side}_grip'] = palm
            hand_axis = (palm - wrist).normalized()
            palm_normals[side] = tuple(sign * Vector((-hand_axis.y, hand_axis.x, 0)))
    elif exercise == 'incline-dumbbell-press':
        rotation = Matrix.Rotation(pi / 4, 3, 'X')
        joints = transformed_rest((0, .10, .64), rotation)
        seated_legs(joints, .68)
        for side, sign in [('left', 1), ('right', -1)]:
            shoulder = joints[f'{side}_shoulder']
            low = Vector((sign * .43, -.04, 1.18))
            high = Vector((sign * .18, -.20, 1.59))
            palm = low.lerp(high, phase)
            elbow, palm = two_bone(shoulder, palm, shoulder + Vector((sign * .35, .10, -.35)), UPPER, LOWER + .096)
            wrist = elbow + (palm - elbow).normalized() * LOWER
            joints[f'{side}_elbow'], joints[f'{side}_wrist'] = elbow, wrist
            joints[f'{side}_hand'] = palm
            joints[f'{side}_grip'] = joints[f'{side}_hand']
            palm_normals[side] = (0, 1, 0)
    elif exercise == 'reverse-cable-curl':
        joints = transformed_rest(REST['pelvis'])
        angle = .12 + phase * 1.93
        for side, sign in [('left', 1), ('right', -1)]:
            shoulder = joints[f'{side}_shoulder']
            elbow = shoulder + Vector((sign * .008, .018, -sqrt(UPPER * UPPER - .008 ** 2 - .018 ** 2)))
            wrist = elbow + Vector((0, sin(angle) * LOWER, -cos(angle) * LOWER))
            joints[f'{side}_elbow'], joints[f'{side}_wrist'] = elbow, wrist
            palm = wrist + (wrist - elbow).normalized() * .096
            joints[f'{side}_hand'] = palm
            joints[f'{side}_grip'] = palm
            palm_normals[side] = (0, -cos(angle), -sin(angle))
    elif exercise == 'push-up':
        grip = 0.0
        slope = .02 + phase * .20
        rotation = Matrix.Rotation(-pi / 2 + slope, 3, 'X')
        # Fixed toes/ankles anchor the rigid body line; only its pitch changes.
        ankle_mid = (REST['left_ankle'] + REST['right_ankle']) * .5
        anchor = Vector((0, -.85, .2312))
        joints = {key: anchor + rotation @ (value - ankle_mid) for key, value in REST.items()}
        for side, sign in [('left', 1), ('right', -1)]:
            joints[f'{side}_ankle'] = Vector((sign * .16, -.85, .2312))
            joints[f'{side}_toe'] = Vector((sign * .16, -.81, .0862))
            shoulder = joints[f'{side}_shoulder']
            wrist = Vector((sign * .285, .26, .055))
            elbow, wrist = two_bone(shoulder, wrist, shoulder + Vector((sign * .30, -.40, .02)))
            joints[f'{side}_elbow'], joints[f'{side}_wrist'] = elbow, wrist
            joints[f'{side}_hand'] = Vector((sign * .285, .348, .035))
            joints[f'{side}_grip'] = joints[f'{side}_hand']
            palm_normals[side] = (0, 0, -1)
    else:
        raise ValueError(exercise)
    return joints, {'grip': grip, 'hand_roll': hand_roll, 'palm_normals': palm_normals}


def validate_joints(joints):
    errors = {}
    for side in ('left', 'right'):
        upper = (joints[f'{side}_elbow'] - joints[f'{side}_shoulder']).length
        lower = (joints[f'{side}_wrist'] - joints[f'{side}_elbow']).length
        errors[side] = {'upperarmError': abs(upper - UPPER), 'forearmError': abs(lower - LOWER)}
        assert errors[side]['upperarmError'] < .0001, errors
        assert errors[side]['forearmError'] < .0001, errors
    return errors
