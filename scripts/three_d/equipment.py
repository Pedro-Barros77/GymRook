"""Original, mechanically articulated gym equipment for offline Blender renders.

Axes: X = lateral (anatomical left is positive), Y = subject forward, Z = up.
`phase` always means effort/closure in [0, 1], not elapsed loop time.
No generated exercise images or textures are used by these scene objects.
"""
import math
import bpy
from mathutils import Vector


def _mat(name, color, roughness=.4, metallic=0):
    material = bpy.data.materials.get('GymRook equipment / ' + name)
    if material:
        return material
    material = bpy.data.materials.new('GymRook equipment / ' + name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    return material


def _materials():
    return {
        'frame': _mat('warm graphite powder coat', (.19, .205, .19), .33, .65),
        'trim': _mat('satin silver edge', (.43, .46, .43), .27, .78),
        'chrome': _mat('brushed steel guide rods', (.58, .62, .61), .23, .9),
        'pad': _mat('charcoal upholstery', (.035, .041, .036), .66, 0),
        'rubber': _mat('rubber feet and handles', (.022, .026, .023), .78, 0),
        'weights': _mat('cast iron weight plates', (.09, .105, .095), .51, .6),
        'cable': _mat('coated steel cable', (.055, .065, .058), .39, .45),
        'accent': _mat('muted olive selector accents', (.39, .47, .25), .5, .2),
    }


class Equipment:
    def __init__(self, exercise, config=None):
        self.exercise = exercise
        self.config = config or {}
        self.materials = _materials()
        self.objects = []
        self.props = {}
        self.anchors = {}
        self.phase = 0.
        self.state = {}
        self.current_weight_height = None
        self.collection = bpy.data.collections.new('Equipment / ' + exercise)
        bpy.context.scene.collection.children.link(self.collection)
        self.root = bpy.data.objects.new('Equipment root / ' + exercise, None)
        self.collection.objects.link(self.root)
        self.objects.append(self.root)
        self.root.empty_display_type = 'PLAIN_AXES'
        self.root.empty_display_size = .12
        self._updater = lambda phase, joints: None
        self._targets = lambda phase: {}

    def _collect(self, obj, material=None):
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        self.collection.objects.link(obj)
        self.objects.append(obj)
        if material:
            obj.data.materials.append(self.materials.get(material, material))
        return obj

    def cube(self, name, center, size, material='frame', bevel=.018):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center)
        obj = bpy.context.object
        obj.name = name
        obj.dimensions = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            modifier = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
            modifier.width = min(bevel, min(size) * .28)
            modifier.segments = 3
            modifier = obj.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')
            modifier.keep_sharp = True
        return self._collect(obj, material)

    def beam(self, name, start, end, width=.065, depth=None, material='frame', bevel=.012):
        start, end = Vector(start), Vector(end)
        obj = self.cube(name, (start + end) / 2, (width, depth or width, (end - start).length), material, bevel)
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = (end - start).to_track_quat('Z', 'Y')
        return obj

    def cylinder(self, name, start, end, radius=.024, material='chrome', vertices=48):
        start, end = Vector(start), Vector(end)
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=(end - start).length, location=(start + end) / 2)
        obj = bpy.context.object
        obj.name = name
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = (end - start).to_track_quat('Z', 'Y')
        for polygon in obj.data.polygons:
            polygon.use_smooth = len(polygon.vertices) == 4
        modifier = obj.modifiers.new('Machined rim bevel', 'BEVEL')
        modifier.width = min(.005, radius * .16)
        modifier.segments = 2
        return self._collect(obj, material)

    def curve(self, name, points, radius=.005, material='cable'):
        data = bpy.data.curves.new(name, 'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 1
        data.bevel_depth = radius
        data.bevel_resolution = 3
        spline = data.splines.new('POLY')
        spline.points.add(len(points) - 1)
        for item, point in zip(spline.points, points):
            item.co = (*point, 1)
        obj = bpy.data.objects.new(name, data)
        self.collection.objects.link(obj)
        self.objects.append(obj)
        data.materials.append(self.materials[material])
        return obj

    @staticmethod
    def set_curve(obj, points):
        spline = obj.data.splines[0]
        if len(spline.points) != len(points):
            raise ValueError('Dynamic cable topology must remain constant')
        for item, point in zip(spline.points, points):
            item.co = (*point, 1)

    def empty(self, name, location=(0, 0, 0)):
        obj = bpy.data.objects.new(name, None)
        obj.location = location
        self.collection.objects.link(obj)
        self.objects.append(obj)
        return obj

    @staticmethod
    def parent_keep(obj, parent):
        bpy.context.view_layer.update()
        matrix = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = matrix

    def update(self, phase, joint_positions=None):
        self.phase = max(0., min(1., float(phase)))
        self._updater(self.phase, joint_positions or {})
        self.state['phase'] = self.phase

    def keyframe(self, frame):
        """Persist transforms and cable control points to a playable .blend."""
        for obj in self.objects:
            obj.keyframe_insert(data_path='location', frame=frame)
            obj.keyframe_insert(data_path='scale', frame=frame)
            data_path = 'rotation_quaternion' if obj.rotation_mode == 'QUATERNION' else 'rotation_euler'
            obj.keyframe_insert(data_path=data_path, frame=frame)
            if obj.type == 'CURVE':
                for spline in obj.data.splines:
                    for point in spline.points:
                        point.keyframe_insert(data_path='co', frame=frame)

    def set_rest_cable_length(self, length):
        if self.exercise != 'reverse-cable-curl':
            raise ValueError('Rest cable calibration applies only to the cable curl')
        self.props['rest_cable_length'] = max(0., float(length))

    def calibrate_rest(self, joint_positions):
        """Calibrate the low position from the actual human grip coordinates."""
        if self.exercise != 'reverse-cable-curl':
            return None
        targets = self.hand_targets(0)
        left = self.joint(joint_positions, 'left', targets['left'])
        right = self.joint(joint_positions, 'right', targets['right'])
        direction = (left - right).normalized()
        rotation = Vector((1, 0, 0)).rotation_difference(direction)
        lug = (left + right) / 2 + rotation @ Vector((0, .04, -.035))
        self.set_rest_cable_length((lug - self.props['low_pulley']).length)
        return self.props['rest_cable_length']

    def hand_targets(self, phase):
        targets = self._targets(max(0., min(1., float(phase))))
        if 'left' in targets:
            targets['left_wrist'] = targets['left']
        if 'right' in targets:
            targets['right_wrist'] = targets['right']
        return targets

    @staticmethod
    def joint(joints, side, fallback):
        aliases = [side + '_grip', side + '_hand', side + '_wrist', 'wrist.' + ('L' if side == 'left' else 'R'), side + 'Hand', side]
        for key in aliases:
            if key in joints:
                return Vector(joints[key])
        return Vector(fallback)

    def foot(self, x, y, width=.13, depth=.17):
        return self.cube('Textured rubber machine foot', (x, y, .042), (width, depth, .07), 'rubber', .014)

    def bolt(self, point, axis=(0, 1, 0), radius=.012):
        point, axis = Vector(point), Vector(axis)
        return self.cylinder('Recessed steel hex fastener', point - axis * .006, point + axis * .006, radius, 'trim', 6)


def _weight_stack(eq, xy, top_z=1.74, travel=.24):
    x, y = xy
    bottom = .15
    plate_h = .023
    base_count, selected_count = 10, 6
    eq.cube('Weight tower lower steel tray', (x, y, bottom - .04), (.40, .34, .08), 'frame')
    for i in range(base_count):
        eq.cube('Stationary unselected plate %02d' % (i + 1), (x, y, bottom + (i + .5) * plate_h), (.30, .26, plate_h - .0025), 'weights', .004)
    selected = eq.empty('Selected weight block / only this block rises', (x, y, bottom + base_count * plate_h))
    for i in range(selected_count):
        obj = eq.cube('Selected weight plate %02d' % (i + 1), (x, y, bottom + (base_count + i + .5) * plate_h), (.30, .26, plate_h - .0025), 'weights', .004)
        eq.parent_keep(obj, selected)
    pin = eq.cylinder('Olive selector pin', (x, y + .125, bottom + (base_count + 2) * plate_h), (x, y + .175, bottom + (base_count + 2) * plate_h), .014, 'accent')
    eq.parent_keep(pin, selected)
    for dx in (-.105, .105):
        eq.cylinder('Fixed chrome weight guide rod', (x + dx, y, bottom), (x + dx, y, top_z), .0095, 'chrome')
        eq.cube('Weight tower fixed upright', (x + dx * 1.65, y - .10, .90), (.055, .07, 1.62), 'frame')
    eq.cube('Weight tower top bridge', (x, y - .03, top_z), (.42, .19, .09), 'frame')
    connector = eq.cylinder('Weight cable central connector', (x, y, bottom + (base_count + selected_count) * plate_h), (x, y, bottom + (base_count + selected_count) * plate_h + .04), .011, 'chrome')
    eq.parent_keep(connector, selected)
    selected_start = selected.location.copy()
    # Return exact selected block and cable attachment heights to the scene owner.
    return {
        'selected': selected,
        'rest': selected_start,
        'travel': travel,
        'attachment': Vector((x, y, bottom + (base_count + selected_count) * plate_h + .04)),
        'pulley': Vector((x, y, top_z - .04)),
        'plateHeight': plate_h,
    }


def _pec_deck(config):
    eq = Equipment('pec-deck', config)
    grip_z = float(config.get('grip_z', 1.08))
    seat_z = float(config.get('seat_z', .48))
    pelvis_z = float(config.get('pelvis_z', seat_z + .13))
    pivot_z = grip_z + .54
    radius = .45
    eq.anchors = {
        'pelvis': (0, 0, pelvis_z), 'chest': (0, -.015, grip_z - .015),
        'left_shoulder': (.205, -.025, grip_z), 'right_shoulder': (-.205, -.025, grip_z),
        'left_hip': (.10, 0, pelvis_z - .01), 'right_hip': (-.10, 0, pelvis_z - .01),
        'left_knee': (.16, .42, .52), 'right_knee': (-.16, .42, .52),
        'left_ankle': (.16, .56, .08), 'right_ankle': (-.16, .56, .08),
        'left_toe': (.16, .66, .04), 'right_toe': (-.16, .66, .04),
    }
    # Fixed frame, seat and padded back. No component of this set is animated.
    for x in (-.36, .36):
        eq.beam('Fixed rear machine column', (x, -.24, .10), (x, -.24, pivot_z + .06), .075)
        eq.beam('Stable forward base rail', (x, -.40, .09), (x, .62, .09), .075)
        eq.foot(x, .58)
        eq.foot(x, -.37)
    eq.beam('Fixed rear floor cross brace', (-.40, -.34, .10), (.40, -.34, .10), .075)
    eq.beam('Fixed top bridge', (-.38, -.24, pivot_z + .06), (.38, -.24, pivot_z + .06), .075)
    eq.beam('Seat support column', (0, .04, .10), (0, .04, seat_z - .03), .085)
    eq.cube('Pec deck rounded seat upholstery', (0, .045, seat_z), (.39, .40, .105), 'pad', .035)
    eq.cube('Pec deck tall back upholstery', (0, -.145, grip_z - .18), (.35, .115, .58), 'pad', .04)
    for z in (seat_z - .04, grip_z - .22):
        eq.beam('Back pad concealed steel support', (0, -.29, z), (0, -.12, z), .055)
    levers = {}
    for side, sign in [('left', 1), ('right', -1)]:
        pivot = (sign * .19, -.03, pivot_z)
        eq.beam('Fixed bearing bracket ' + side, (sign * .19, -.24, pivot_z), pivot, .06)
        eq.cylinder('Fixed vertical pivot housing ' + side, (pivot[0], pivot[1], pivot_z - .035), (pivot[0], pivot[1], pivot_z + .035), .07, 'frame')
        lever = eq.empty('Pec deck articulated lever ' + side, pivot)
        angle = math.radians(15)
        end = (sign * (.19 + radius * math.cos(angle)), -.03 + radius * math.sin(angle), pivot_z)
        objects = [
            eq.beam('Rigid overhead radial boom ' + side, pivot, end, .052, .065),
            eq.beam('Rigid vertical lever drop ' + side, end, (end[0], end[1], grip_z + .10), .048, .055),
            eq.cylinder('Vertical grip steel core ' + side, (end[0], end[1], grip_z - .105), (end[0], end[1], grip_z + .105), .016, 'chrome'),
            eq.cylinder('Vertical ergonomic rubber grip ' + side, (end[0], end[1], grip_z - .08), (end[0], end[1], grip_z + .08), .023, 'rubber'),
            eq.cylinder('Rotating drive cam ' + side, (pivot[0], pivot[1], pivot_z - .055), (pivot[0], pivot[1], pivot_z - .025), .087, 'weights'),
        ]
        for obj in objects:
            eq.parent_keep(obj, lever)
        eq.bolt((pivot[0], pivot[1], pivot_z + .038), (0, 0, 1), .022)
        levers[side] = lever
    stack = _weight_stack(eq, (-.69, -.28), top_z=pivot_z + .04, travel=.24)
    cable = eq.curve('Pec deck taut selected-weight cable', [stack['attachment'], stack['pulley'], (-.19, -.03, pivot_z - .04)])
    eq.props.update({'levers': levers, 'weight_stack': stack, 'cable': cable, 'pivot_radius': radius, 'grip_z': grip_z, 'seat_z': seat_z})

    def targets(phase):
        angle = math.radians(15 + 85 * phase)
        return {side: (sign * (.19 + radius * math.cos(angle)), -.03 + radius * math.sin(angle), grip_z)
                for side, sign in [('left', 1), ('right', -1)]}

    def update(phase, joints):
        for side, sign in [('left', 1), ('right', -1)]:
            levers[side].rotation_euler.z = sign * math.radians(85 * phase)
        lift = stack['travel'] * phase
        stack['selected'].location = stack['rest'] + Vector((0, 0, lift))
        point = stack['attachment'] + Vector((0, 0, lift))
        eq.set_curve(cable, [point, stack['pulley'], Vector((-.19, -.03, pivot_z - .04))])
        eq.current_weight_height = stack['selected'].location.z
        eq.state.update({'selected_weight_height': eq.current_weight_height, 'weight_lift': lift,
                         'left_handle': targets(phase)['left'], 'right_handle': targets(phase)['right'],
                         'cable_length': (stack['pulley'] - point).length + (stack['pulley'] - Vector((-.19, -.03, pivot_z - .04))).length})

    eq._targets, eq._updater = targets, update
    eq.update(0)
    return eq


def _dumbbell(eq, name, center):
    root = eq.empty(name, center)
    x, y, z = center
    parts = [eq.cylinder(name + ' steel grip', (x - .066, y, z), (x + .066, y, z), .015, 'chrome')]
    for sign in (-1, 1):
        # Three-layer hexagonal cast head, with an inset end cap and hub.
        parts.append(eq.cylinder(name + ' cast hex head', (x + sign * .073, y, z), (x + sign * .125, y, z), .085, 'weights', 6))
        parts.append(eq.cylinder(name + ' inset hex face', (x + sign * .126, y, z), (x + sign * .131, y, z), .067, 'rubber', 6))
        parts.append(eq.cylinder(name + ' center steel hub', (x + sign * .132, y, z), (x + sign * .136, y, z), .014, 'trim'))
    for obj in parts:
        eq.parent_keep(obj, root)
    return root


def _incline(config):
    eq = Equipment('incline-dumbbell-press', config)
    lower = Vector((0, 0, .55))
    upper = Vector((0, -.68, 1.23))
    pad = eq.beam('45 degree inclined backrest upholstery', lower, upper, .33, .105, 'pad', .032)
    eq.beam('Incline backrest steel spine', (0, -.04, .49), (0, -.71, 1.16), .085)
    eq.cube('Incline bench rounded seat', (0, .15, .535), (.33, .32, .105), 'pad', .035)
    eq.beam('Bench lower longitudinal frame', (0, -.70, .12), (0, .41, .12), .085)
    eq.beam('Bench seat support', (0, .14, .14), (0, .14, .48), .085)
    eq.beam('Bench rear diagonal brace', (0, -.59, .14), (0, -.38, .82), .07)
    for y in (-.67, .38):
        eq.beam('Bench wide floor crossbar', (-.35, y, .10), (.35, y, .10), .075)
        eq.foot(-.32, y, .12, .16)
        eq.foot(.32, y, .12, .16)
    for z in (.40, .48, .56):
        eq.cylinder('Backrest adjustment rail hole', (-.044, -.48, z), (.044, -.48, z), .013, 'rubber')
    eq.bolt((.052, -.38, .69), (1, 0, 0), .022)
    eq.anchors = {
        'pelvis': (0, .10, .64), 'chest': (0, -.18, .92),
        'left_shoulder': (.19, -.24, 1.00), 'right_shoulder': (-.19, -.24, 1.00),
        'neck': (0, -.36, 1.12), 'head': (0, -.46, 1.24),
        'left_hip': (.10, .10, .64), 'right_hip': (-.10, .10, .64),
        'left_knee': (.18, .49, .51), 'right_knee': (-.18, .49, .51),
        'left_ankle': (.18, .54, .07), 'right_ankle': (-.18, .54, .07),
    }
    def targets(phase):
        return {side: (sign * (.36 - .18 * phase), -.10 - .13 * phase, 1.03 + .51 * phase)
                for side, sign in [('left', 1), ('right', -1)]}
    dumbbells = {side: _dumbbell(eq, 'Incline dumbbell ' + side, point) for side, point in targets(0).items()}
    eq.props.update({'dumbbells': dumbbells, 'bench_angle_degrees': 45, 'backrest': pad})
    def update(phase, joints):
        for side, fallback in targets(phase).items():
            dumbbells[side].location = eq.joint(joints, side, fallback)
    eq._targets, eq._updater = targets, update
    eq.update(0)
    return eq


def _curl(config):
    eq = Equipment('reverse-cable-curl', config)
    station_y = float(config.get('station_y', 1.25))
    low = Vector((0, station_y - .17, .14))
    tower_x = -.13
    for x in (-.27, .27):
        eq.beam('Low cable machine fixed rear column', (x, station_y + .12, .10), (x, station_y + .12, 1.96), .07)
        eq.beam('Cable station stable base rail', (x, station_y - .35, .09), (x, station_y + .32, .09), .075)
        eq.foot(x, station_y - .31)
        eq.foot(x, station_y + .28)
    eq.beam('Cable station top fixed bridge', (-.30, station_y + .12, 1.96), (.30, station_y + .12, 1.96), .075)
    eq.cylinder('Low pulley grooved wheel', (-.045, low.y, low.z), (.045, low.y, low.z), .067, 'weights')
    eq.cylinder('Low pulley bearing hub', (-.053, low.y, low.z), (.053, low.y, low.z), .020, 'chrome')
    eq.beam('Low pulley fork mounting', (-.075, low.y, .10), (-.075, low.y, .22), .04)
    eq.beam('Low pulley fork mounting', (.075, low.y, .10), (.075, low.y, .22), .04)
    stack = _weight_stack(eq, (tower_x, station_y + .07), top_z=1.90, travel=.30)
    def targets(phase):
        return {side: (sign * .22, .135 + .20 * math.sin(phase * math.pi * .72), .79 + .52 * phase)
                for side, sign in [('left', 1), ('right', -1)]}
    root = eq.empty('Rigid reverse-curl straight bar')
    parts = [eq.cylinder('Straight bar chrome shaft', (-.31, 0, 0), (.31, 0, 0), .015, 'chrome')]
    for sign in (-1, 1):
        parts.append(eq.cylinder('Pronated grip rubber sleeve', (sign * .15, 0, 0), (sign * .29, 0, 0), .022, 'rubber'))
        parts.append(eq.cylinder('Bar sleeve end cap', (sign * .30, 0, 0), (sign * .32, 0, 0), .025, 'weights'))
    parts.append(eq.cylinder('Bar central cable attachment lug', (0, .005, 0), (0, .04, -.035), .021, 'chrome'))
    for obj in parts:
        eq.parent_keep(obj, root)
    rest_hands = targets(0)
    rest_center = (Vector(rest_hands['left']) + Vector(rest_hands['right'])) / 2
    rest_lug = rest_center + Vector((0, .04, -.035))
    rest_cable_len = (rest_lug - low).length
    cable = eq.curve('Continuous taut cable from straight bar to low pulley', [rest_lug, low])
    back_cable = eq.curve('Fixed lower pulley return to tower top', [low, (low.x, station_y + .1, .14), (low.x, station_y + .1, 1.86), stack['pulley'], stack['attachment']])
    eq.anchors = {
        'pelvis': (0, 0, .96), 'chest': (0, 0, 1.43),
        'left_shoulder': (.205, 0, 1.45), 'right_shoulder': (-.205, 0, 1.45),
        'left_elbow': (.22, .02, 1.17), 'right_elbow': (-.22, .02, 1.17),
        'left_ankle': (.13, 0, .08), 'right_ankle': (-.13, 0, .08),
    }
    eq.props.update({'bar': root, 'cable': cable, 'weight_stack': stack, 'low_pulley': low, 'pulley_ratio': 1., 'rest_cable_length': rest_cable_len})
    def update(phase, joints):
        points = targets(phase)
        left = eq.joint(joints, 'left', points['left'])
        right = eq.joint(joints, 'right', points['right'])
        center = (left + right) / 2
        root.location = center
        # Align the rigid bar with the actual two grip targets. No changing length.
        direction = (left - right).normalized()
        root.rotation_mode = 'QUATERNION'
        root.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(direction)
        lug = center + root.rotation_quaternion @ Vector((0, .04, -.035))
        eq.set_curve(cable, [lug, low])
        cable_length = (lug - low).length
        lift = max(0., min(.75, (cable_length - eq.props['rest_cable_length']) * eq.props['pulley_ratio']))
        stack['selected'].location = stack['rest'] + Vector((0, 0, lift))
        eq.set_curve(back_cable, [low, (low.x, station_y + .1, .14), (low.x, station_y + .1, 1.86), stack['pulley'], stack['attachment'] + Vector((0, 0, lift))])
        eq.props['current_cable_length'] = cable_length
        eq.props['current_weight_lift'] = lift
        eq.current_weight_height = stack['selected'].location.z
        eq.state.update({'selected_weight_height': eq.current_weight_height, 'weight_lift': lift,
                         'cable_length': cable_length, 'left_handle': tuple(left), 'right_handle': tuple(right)})
    eq._targets, eq._updater = targets, update
    eq.update(0)
    return eq


def self_test():
    """Run inside Blender with --background --factory-startup --python ... -- --self-test."""
    for exercise in ('pec-deck', 'incline-dumbbell-press', 'push-up', 'reverse-cable-curl'):
        eq = build_equipment(exercise)
        object_count = len(eq.objects)
        topology = [(obj.name, len(obj.data.vertices)) for obj in eq.objects if obj.type == 'MESH']
        bpy.context.view_layer.update()
        root_matrix = eq.root.matrix_world.copy()
        fixed = {obj.name: obj.matrix_world.copy() for obj in eq.objects
                 if any(term in obj.name.lower() for term in ('fixed', 'stationary', 'upholstery', 'machine foot'))}
        heights = []
        for index, phase in enumerate((0., .5, 1.)):
            eq.update(phase)
            bpy.context.view_layer.update()
            assert len(eq.objects) == object_count, f'{exercise}: object count changed'
            assert topology == [(obj.name, len(obj.data.vertices)) for obj in eq.objects if obj.type == 'MESH'], f'{exercise}: topology changed'
            assert max(abs(eq.root.matrix_world[i][j] - root_matrix[i][j]) for i in range(4) for j in range(4)) < 1e-8, f'{exercise}: root moved'
            for obj in eq.objects:
                if obj.name in fixed:
                    assert max(abs(obj.matrix_world[i][j] - fixed[obj.name][i][j]) for i in range(4) for j in range(4)) < 1e-8, f'{exercise}: fixed part moved: {obj.name}'
            if eq.current_weight_height is not None:
                heights.append(eq.current_weight_height)
            eq.keyframe(index * 12 + 1)
        if heights:
            assert heights[0] < heights[1] < heights[2], f'{exercise}: weight block failed to rise: {heights}'
        if exercise == 'reverse-cable-curl':
            actual = {'left_grip': (.22, .135, .85), 'right_grip': (-.22, .135, .85)}
            eq.calibrate_rest(actual)
            eq.update(0, actual)
            assert abs(eq.state['weight_lift']) < 1e-8, 'Curl calibration failed'
        assert all(obj.type != 'CAMERA' for obj in eq.objects), 'Equipment must not own a camera'
        print('EQUIPMENT_SMOKE_OK', exercise, object_count, 'weights', heights)


def build_equipment(exercise, config=None):
    """Create one equipment scene. `config` optionally adjusts anthropometry.

    Pec deck accepts grip_z, seat_z and pelvis_z; curl accepts station_y.
    Returned .objects and .collection contain only equipment, never a human.
    Parent all top-level objects to .root after construction so the scene owner
    can translate the complete assembly without modifying its articulation.
    """
    config = config or {}
    builders = {'pec-deck': _pec_deck, 'incline-dumbbell-press': _incline, 'reverse-cable-curl': _curl}
    if exercise == 'push-up':
        eq = Equipment(exercise, config)
        eq.anchors = {'floor_z': 0.}
    elif exercise in builders:
        eq = builders[exercise](config)
    else:
        raise ValueError('Unsupported equipment: ' + exercise)
    for obj in eq.objects:
        if obj is not eq.root and obj.parent is None:
            eq.parent_keep(obj, eq.root)
    return eq


if __name__ == '__main__':
    import sys
    if '--self-test' in sys.argv:
        self_test()
