# Original 3D equipment

`scripts/three_d/equipment.py` constructs original exercise equipment with Blender primitives, bevels, continuous curves and constant materials. No exercise pictures, external model files, trademarks or paid assets are used.

## Interface and coordinate convention

- `build_equipment(exercise_id, config=None)` returns an `Equipment` instance.
- `update(phase, joint_positions=None)` updates only articulated parts. `phase` is effort/closure from zero to one; the render driver supplies the smooth periodic timing curve.
- `hand_targets(phase)` returns `left`, `right`, `left_wrist` and `right_wrist`, in world coordinates.
- `anchors` provides the intended pelvis, shoulder and leg contact coordinates.
- `objects`, `collection`, `root` and `props` expose scene objects and mechanical metadata.
- `keyframe(frame)` persists all object transforms and all cable control-point coordinates; cables are never recreated during updates.
- `state` records the current phase, grip positions, selected-weight height, weight lift and cable length for continuity checks. `current_weight_height` is also exposed directly.
- Coordinates are metres: X lateral, anatomical left positive; Y forward; Z upward.
- Joint overrides prefer `left_grip` / `right_grip`, then `left_hand`, `left_wrist`, `wrist.L`, `leftHand` or `left` (and right equivalents). This lets a hand mesh's palm centre differ from its wrist joint.

## Pec deck

The articulated arms use fixed vertical pivot axes at X ±0.19, Y −0.03. The radial lever length is 0.45 m, rotating from 15° open to 100° closed. The right side mirrors the left. The hand height is constant, so the world-space trajectory is a genuine horizontal arc projected by the render camera.

Default grip height is 1.08 m, seat centre height 0.48 m, pelvis centre 0.61 m. The scene owner can pass `grip_z`, `seat_z` and `pelvis_z` to match the real human rig instead of stretching the torso. Overhead pivots remain 0.54 m above the grips. Hands follow handles; the machine frame, back pad, seat and feet do not animate.

Ten lower plates remain stationary. Six selected plates rise together by up to 0.24 m on two fixed chrome guide rods, leaving a visible gap below them. Their cable attachment rises with the selected block and the rendered cable remains taut. This is a visual kinematic linkage, not a dynamic simulation of stack forces.

## Incline bench and dumbbells

The back pad follows `(0, 0, .55)` to `(0, −.68, 1.23)`, exactly 45° from horizontal. Its structural frame, feet and cushions are fixed. Two rigid hex dumbbells follow the actual supplied hand/grip coordinates. Their handles, heads and surface materials do not change between frames.

## Low-cable reverse curl

The station is placed forward of the standing body, at default Y 1.25 m (`station_y` can override it). The visible low pulley is fixed at Z 0.14 m. The rigid straight bar is centred between the supplied grip coordinates and aligned to the line joining them. A continuous taut cable connects its lug to the low pulley.

The selected stack's travel is derived from the increase in the bar-to-pulley cable distance using the declared 1:1 pulley ratio. Call `calibrate_rest(actual_low_pose_grips)` before the animation to set zero lift from the real character pose; alternatively set `props.rest_cable_length` or call `set_rest_cable_length(length)`. The lower plates and guide rods remain stationary. `props.current_cable_length` and `props.current_weight_lift` are available for mechanical checks.

## Verification boundary

The render owner should verify real Blender construction, contact positions, selected-plate motion, fixed frame transforms and the final camera view. These scenes define coherent kinematics; they do not independently certify exercise technique or reproduce a particular commercial machine's exact linkage.
