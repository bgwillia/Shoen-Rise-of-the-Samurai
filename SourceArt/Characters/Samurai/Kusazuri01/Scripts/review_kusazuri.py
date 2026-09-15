"""Measure saved Kusazuri and render functional reviews without saving the source.

Blender --background --factory-startup --python-exit-code 1 --python THIS -- [options]
Default: every integer frame of the four saved native actions and static diagnostics.
--quick: bounded samples, written to separate *-quick.json reports.
--render: measure first, then component views and measured motion captures.
--motions: measure first, then motion captures only. --views: component views only.
--render-only: use matching existing measurements, then render without measuring again.

The native body and existing upper armor keep their original rig and animations.
Temporary same-skeleton armor instances drive Kusazuri and the Sode review fixtures.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
OUTPUT = ROOT / 'artifacts/kusazuri01'
CAPTURES = ART / 'Review/Captures'
sys.path.insert(0, str(ART / 'Scripts'))
from kusazuri_motion import armor_pose, review_rig

CLIPS = ('A_Idle', 'A_Walk', 'A_Run', 'A_Attack')
DIAGNOSTICS = {
    'neutral': 'Unchanged native reference pose.',
    'wide-step': 'Left thigh directed (.12,-.80,-.59), right (-.10,.48,-.87); calves (.02,-.08,-1) and (-.02,.35,-.94).',
    'wide-stance': 'Thighs directed (±.52,-.10,-.85), calves (±.10,.10,-.99); pelvis lowered 7 cm.',
    'knee-lift': 'Left thigh directed (.08,-.98,-.15), left calf (0,.10,-.99).',
    'crouch': 'Thighs directed (±.15,-.60,-.80), calves (±.06,.58,-.82); pelvis lowered 14 cm; torso forward 12 degrees.',
    'combat-stance': 'Left thigh (.30,-.48,-.83), right (-.40,.18,-.90), calves (±.08,.35,-.94); pelvis lowered 5 cm; torso turned 12 degrees.',
    'torso-turn': 'spine_01 rotates 35 degrees around native +Z at its current origin; pelvis and legs retain reference pose.',
    'hip-rotation': 'Pelvis rotates 35 degrees about +Z and 12 degrees about +Y; all descendants follow.',
    'bow-diagnostic': 'Wide combat stance; left upper arm (.18,-1,.08), right (-.75,.6,.12), right hand toward (0,-4,157) native cm. No native bow clip or weapon.',
}
QUICK_DIAGNOSTICS = ('neutral', 'wide-step', 'knee-lift', 'crouch', 'hip-rotation')
RIGID_TOLERANCE_M = 2e-5


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_rows(matrix):
    return [list(row) for row in matrix]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')


def leg_contact(record):
    """Separate leg contact from hands when selecting motion review frames."""
    pairs, depth = 0, 0.
    for part in record['surface_intersections']['body'].values():
        pairs += sum(count for bone, count in part['contact_triangle_pairs_by_dominant_target_bone'].items()
                     if bone.startswith(('thigh_', 'calf_', 'foot_', 'ball_')))
        depth = max(depth, max((value for bone, value in
            part['maximum_contact_penetration_estimate_mm_by_dominant_target_bone'].items()
            if bone.startswith(('thigh_', 'calf_', 'foot_', 'ball_'))), default=0.))
    return pairs, depth


def evaluated(ob, depsgraph, polygon_output=None):
    """Triangulated evaluated geometry in world metres; always release temp meshes."""
    obj = ob.evaluated_get(depsgraph)
    mesh = obj.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
    try:
        mesh.calc_loop_triangles()
        if polygon_output is not None:
            polygon_output.extend(tuple(polygon.vertices) for polygon in mesh.polygons)
        return ([obj.matrix_world @ vertex.co for vertex in mesh.vertices],
                [tuple(triangle.vertices) for triangle in mesh.loop_triangles])
    finally:
        obj.to_mesh_clear()


def tree_from(objects, depsgraph):
    points, faces = [], []
    for ob in objects:
        vertices, triangles = evaluated(ob, depsgraph)
        offset = len(points)
        points.extend(vertices)
        faces.extend(tuple(offset + index for index in face) for face in triangles)
    if not faces:
        raise RuntimeError('Empty intersection fixture: ' + ', '.join(ob.name for ob in objects))
    return BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.)


def intersects(geometry, trees, target_regions=None):
    """Exhaustive surface pairs plus sampled signed nearest-surface depth.

    Depth is evaluated at every vertex of an intersecting armor triangle and
    up to 256 uniformly spaced additional vertices per component. A nearest
    triangle's outward normal gives the sign. This is not an exact solid
    intersection depth: nonconvex/open/overlapping target shells can make the
    sign ambiguous, and extrema inside a triangle need not occur at a vertex.
    """
    output = {label: {} for label in trees}
    for name, (points, faces) in geometry.items():
        armor_tree = BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.)
        for label, tree in trees.items():
            overlaps = tree.overlap(armor_tree)
            regions = (target_regions or {}).get(label)
            region_pairs, region_depths = {}, {}
            if regions:
                for target_face, _ in overlaps:
                    region = regions[target_face]
                    region_pairs[region] = region_pairs.get(region, 0) + 1
            overlap_faces = sorted({pair[1] for pair in overlaps})
            contact_indices = {index for face in overlap_faces for index in faces[face]}
            indices = set(range(0, len(points), max(1, math.ceil(len(points) / 256))))
            indices.update(contact_indices)
            depth, clearance, inward, deepest, negative_distance = 0., math.inf, 0, None, 0.
            for index in sorted(indices):
                point = points[index]
                location, normal, triangle, distance = tree.find_nearest(point)
                if location is None:
                    continue
                clearance = min(clearance, distance)
                signed = (point - location).dot(normal)
                if signed < -1e-7:
                    inward += 1
                    negative_distance = max(negative_distance, distance)
                    if index in contact_indices and distance > depth:
                        depth = distance
                        deepest = {'armor_vertex': index, 'target_triangle': triangle,
                                   'point_metres': list(point), 'surface_metres': list(location)}
                    if index in contact_indices and regions:
                        region = regions[triangle]
                        region_depths[region] = max(region_depths.get(region, 0.), distance * 1000)
            output[label][name] = {
                'triangle_intersections': len(overlaps),
                'intersecting_armor_triangles': len(overlap_faces),
                'examples': [list(pair) for pair in overlaps[:5]],
                'depth_sample_vertices': len(indices),
                'vertices_on_negative_nearest_normal_side': inward,
                'maximum_sampled_penetration_estimate_mm': depth * 1000,
                'maximum_negative_nearest_normal_sample_distance_mm': negative_distance * 1000,
                'minimum_unsigned_sample_clearance_mm': clearance * 1000 if math.isfinite(clearance) else None,
                'deepest_sample': deepest,
                'contact_triangle_pairs_by_dominant_target_bone': region_pairs,
                'maximum_contact_penetration_estimate_mm_by_dominant_target_bone': region_depths,
            }
    return output


def all_action_curves(action):
    """Handle the saved layered actions and older Blender action representations."""
    if hasattr(action, 'layers') and len(action.layers):
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    bag = strip.channelbag(slot)
                    if bag:
                        yield bag.fcurves
    elif hasattr(action, 'fcurves'):
        yield action.fcurves


class Review:
    def __init__(self, cardinal_front_probe=False, gated_front_probe=False):
        self.cardinal_front_probe = cardinal_front_probe
        self.gated_front_probe = gated_front_probe
        self.controller_variant = ('experimental Front_L/R radial-to-cardinal smoothstep sagittal 50-75 degrees, all-panel .02 rad margin'
            if gated_front_probe else 'experimental cardinal Front_L/R, .05 rad margin'
            if cardinal_front_probe else 'production kusazuri_motion.armor_pose')
        self.source = ART / 'Kusazuri01.blend'
        self.source_hash = sha256(self.source)
        self.motion_hash = sha256(ART / 'Scripts/kusazuri_motion.py')
        bpy.ops.wm.open_mainfile(filepath=str(self.source))
        self.scene = bpy.context.scene
        self.rig = bpy.data.objects['root']
        self.parts = sorted((ob for ob in bpy.data.collections['Kusazuri01_Source'].all_objects
                             if ob.type == 'MESH'), key=lambda ob: ob.name)
        self.fit = sorted((ob for ob in bpy.data.collections['Kusazuri01_Fit'].all_objects
                           if ob.type == 'MESH'), key=lambda ob: ob.name)
        self.body = bpy.data.objects['Manny_Review']
        self.body_vertex_weights = [
            {self.body.vertex_groups[group.group].name: group.weight for group in vertex.groups}
            for vertex in self.body.data.vertices]
        self.body_face_regions = {}
        self.do = [ob for ob in self.fit if ob.name.startswith('Do_Review')]
        sode = [ob for ob in self.fit if ob.name.startswith('Sode_Review')]
        if len(self.parts) != 30 or not self.do or not sode or len(self.rig.data.bones) != 88:
            raise RuntimeError('Saved source does not match the 30-part Kusazuri/native-Manny/upper-armor contract')
        self.rig.animation_data_create()
        self.rig.animation_data.use_nla = False
        self.rig.data.pose_position = 'POSE'
        self.root_rest = Matrix.Diagonal((.01, .01, .01, 1.))
        for collection in bpy.data.collections:
            if collection.name.startswith('Kusazuri01_Runtime'):
                for ob in collection.all_objects:
                    ob.hide_render = True
                    ob.hide_set(True)
        for ob in self.parts + self.fit + [self.rig]:
            ob.hide_set(False)
        self.neutral()
        self.armor = review_rig(self.rig, self.parts)
        # Sode is a preview dependency only; its helper does not participate in
        # Kusazuri geometry, clearance, target generation, or export.
        sys.path.insert(0, str(ART.parent / 'Sode01/Scripts'))
        import sode_motion
        self.sode_pose = sode_motion.armor_pose
        self.sode = sode_motion.review_rig(self.rig, sode)
        self.sode_motion_hash = sha256(ART.parent / 'Sode01/Scripts/sode_motion.py')
        self.actions = {}
        self.references = {}
        self.captures = []
        self.update_armor()

    def neutral(self):
        self.rig.animation_data.action = None
        for bone in self.rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        self.scene.frame_set(1)
        self.rig.matrix_basis = self.root_rest
        bpy.context.view_layer.update()

    def direct(self, bone_name, child_name, direction):
        bpy.context.view_layer.update()
        bone = self.rig.pose.bones[bone_name]
        current = bone.matrix.copy()
        pivot = current.translation
        original = self.rig.pose.bones[child_name].matrix.translation - pivot
        rotation = original.rotation_difference(Vector(direction).normalized())
        bone.matrix = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ current
        bpy.context.view_layer.update()

    def rotate(self, bone_name, degrees, axis):
        bone = self.rig.pose.bones[bone_name]
        current = bone.matrix.copy()
        pivot = current.translation
        bone.matrix = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(-pivot) @ current
        bpy.context.view_layer.update()

    def lower_pelvis(self, centimetres):
        bone = self.rig.pose.bones['pelvis']
        matrix = bone.matrix.copy()
        matrix.translation.z -= centimetres
        bone.matrix = matrix
        bpy.context.view_layer.update()

    def legs(self, thighs, calves):
        for side, thigh, calf in zip(('l', 'r'), thighs, calves):
            self.direct('thigh_' + side, 'calf_' + side, thigh)
            self.direct('calf_' + side, 'foot_' + side, calf)

    def diagnostic(self, name):
        if name not in DIAGNOSTICS:
            raise RuntimeError('Unknown diagnostic ' + name)
        self.neutral()
        if name == 'wide-step':
            self.legs(((.12, -.80, -.59), (-.10, .48, -.87)), ((.02, -.08, -1), (-.02, .35, -.94)))
        elif name == 'wide-stance':
            self.legs(((.52, -.10, -.85), (-.52, -.10, -.85)), ((.10, .10, -.99), (-.10, .10, -.99)))
            self.lower_pelvis(7)
        elif name == 'knee-lift':
            self.direct('thigh_l', 'calf_l', (.08, -.98, -.15))
            self.direct('calf_l', 'foot_l', (0, .10, -.99))
        elif name == 'crouch':
            self.legs(((.15, -.60, -.80), (-.15, -.60, -.80)), ((.06, .58, -.82), (-.06, .58, -.82)))
            self.lower_pelvis(14)
            self.rotate('spine_01', 12, 'X')
        elif name in ('combat-stance', 'bow-diagnostic'):
            self.legs(((.30, -.48, -.83), (-.40, .18, -.90)), ((.08, .35, -.94), (-.08, .35, -.94)))
            self.lower_pelvis(5)
            self.rotate('spine_01', -12, 'Z')
            if name == 'bow-diagnostic':
                self.direct('upperarm_l', 'lowerarm_l', (.18, -1, .08))
                self.direct('upperarm_r', 'lowerarm_r', (-.75, .6, .12))
                elbow = self.rig.pose.bones['lowerarm_r'].matrix.translation
                self.direct('lowerarm_r', 'hand_r', Vector((0, -4, 157)) - elbow)
        elif name == 'torso-turn':
            self.rotate('spine_01', 35, 'Z')
        elif name == 'hip-rotation':
            self.rotate('pelvis', 35, 'Z')
            self.rotate('pelvis', 12, 'Y')

    def native(self, name, frame):
        self.neutral()
        if name not in self.actions:
            action = bpy.data.actions[name].copy()
            action.name = 'KUSAZURI_REVIEW_IN_PLACE_' + name
            for curves in all_action_curves(action):
                for curve in list(curves):
                    if not curve.data_path.startswith('pose.bones['):
                        curves.remove(curve)
            self.actions[name] = action
        action = self.actions[name]
        self.rig.animation_data.action = action
        if hasattr(action, 'slots') and action.slots:
            self.rig.animation_data.action_slot = action.slots[0]
        self.scene.frame_set(frame)
        self.rig.matrix_basis = self.root_rest
        bpy.context.view_layer.update()

    def apply(self, record):
        if record.get('clip'):
            self.native(record['clip'], record['frame'])
        else:
            self.diagnostic(record['pose'])
        return self.update_armor()

    def update_armor(self):
        targets = armor_pose(self.rig, self.armor)
        if self.cardinal_front_probe or self.gated_front_probe:
            # Diagnostic override only. Keep production source/controller
            # untouched, and write probe reports under separate filenames.
            delta = Matrix(targets['pelvis_pose_blender_cm']) @ Matrix(targets['pelvis_reference_blender_cm']).inverted()
            for panel in targets['panels']:
                front_quarter = panel['panel'] in ('Front_L', 'Front_R')
                if self.cardinal_front_probe and not front_quarter:
                    continue
                side = 'l' if panel['theta'] > 0 else 'r'
                direction = Vector(targets['thigh_directions_pelvis_blender'][side])
                radial = Vector((math.sin(panel['theta']), -math.cos(panel['theta']), 0.))
                blend = 1. if self.cardinal_front_probe else 0.
                if self.gated_front_probe and front_quarter:
                    sagittal = math.degrees(math.atan2(max(0., -direction.y), max(.08, -direction.z)))
                    blend = max(0., min(1., (sagittal - 50.) / 25.))
                    blend = blend * blend * (3. - 2. * blend)
                normal = radial.lerp(Vector((0., -1., 0.)), blend).normalized()
                sides = ('l', 'r') if panel['panel'] == 'Front_Center' else (side,)
                directions = [Vector(targets['thigh_directions_pelvis_blender'][side]) for side in sides]
                flex = max(math.atan2(max(0., direction.dot(normal)), max(.08, -direction.z)) for direction in directions)
                margin = .02 if self.gated_front_probe else .05
                angle = max(0., min(math.pi / 2, flex - margin))
                pivot = Vector(panel['hinge_pivot_cm'])
                axis = Vector((normal.y, -normal.x, 0.))
                target = delta @ Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-pivot) @ Matrix(panel['reference_blender_cm'])
                panel.update({'angle_radians': angle, 'target_blender_cm': matrix_rows(target),
                              'experimental_hinge_normal_blender': list(normal),
                              'experimental_cardinal_blend': blend, 'experimental_margin_radians': margin})
            # Reapply all seven targets in parent-before-child order. Setting a
            # thigh after its twist descendants otherwise invalidates them.
            for panel in targets['panels']:
                self.armor.pose.bones[panel['bone']].matrix = Matrix(panel['target_blender_cm'])
                bpy.context.view_layer.update()
        self.sode_pose(self.rig, self.sode)
        bpy.context.view_layer.update()
        return targets

    def bone_delta(self, ob):
        bone = str(ob.get('rigid_bone', ''))
        if bone not in self.armor.pose.bones:
            raise RuntimeError('Missing explicit rigid_bone on ' + ob.name)
        return (self.armor.matrix_world @ self.armor.pose.bones[bone].matrix @
                self.armor.data.bones[bone].matrix_local.inverted() @ self.armor.matrix_world.inverted())

    def prepare_reference(self):
        self.neutral()
        self.update_armor()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for ob in self.parts:
            polygons = []
            points, faces = evaluated(ob, depsgraph, polygons)
            pairs = [(i, (i + len(points) // 2) % len(points))
                     for i in range(0, len(points), max(1, math.ceil(len(points) / 128)))]
            self.references[ob.name] = {
                'points': points, 'faces': faces, 'delta': self.bone_delta(ob),
                'polygons': polygons,
                'pairs': [(a, b, (points[a] - points[b]).length) for a, b in pairs],
                'normals': [(points[b] - points[a]).cross(points[c] - points[a]) for a, b, c in faces],
            }

    def deformation(self, ob, points, faces, polygons):
        ref = self.references[ob.name]
        if len(points) != len(ref['points']) or polygons != ref['polygons']:
            raise RuntimeError('Evaluated topology changes during motion: ' + ob.name)
        transform = self.bone_delta(ob) @ ref['delta'].inverted()
        rotation = transform.to_3x3()
        pair_error = max(abs((points[a] - points[b]).length - distance) for a, b, distance in ref['pairs'])
        vertex_error = max((point - transform @ original).length for point, original in zip(points, ref['points']))
        reversed_faces, collapsed, minimum_area_ratio = 0, 0, math.inf
        # Blender may choose another diagonal for a nearly coplanar ngon after
        # rigid motion. Compare actual polygon connectivity above and freeze
        # triangulation only for this deformation/orientation comparison.
        for (a, b, c), original in zip(ref['faces'], ref['normals']):
            normal = (points[b] - points[a]).cross(points[c] - points[a])
            expected = rotation @ original
            if original.length <= 1e-14:
                continue
            ratio = normal.length / original.length
            minimum_area_ratio = min(minimum_area_ratio, ratio)
            collapsed += ratio < .1
            reversed_faces += normal.dot(expected) < 0
        return {'sample_pair_count': len(ref['pairs']), 'maximum_pair_distance_error_metres': pair_error,
                'maximum_all_vertex_rigid_transform_error_metres': vertex_error,
                'rigid_transform_determinant': rotation.determinant(),
                'reversed_triangles_relative_to_rigid_transform': reversed_faces,
                'collapsed_triangles_relative_to_reference': collapsed,
                'evaluation_retriangulated_without_polygon_changes': faces != ref['faces'],
                'minimum_triangle_area_ratio': minimum_area_ratio if math.isfinite(minimum_area_ratio) else None,
                'finite_vertices': all(math.isfinite(value) for point in points for value in point)}

    def measure(self, record):
        start = time.perf_counter()
        targets = self.apply(record)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        polygons = {ob.name: [] for ob in self.parts}
        geometry = {ob.name: evaluated(ob, depsgraph, polygons[ob.name]) for ob in self.parts}
        body_points, body_faces = evaluated(self.body, depsgraph)
        if len(body_points) != len(self.body_vertex_weights):
            raise RuntimeError('Evaluated Manny vertex count differs from source skin weights')
        for face in body_faces:
            if face not in self.body_face_regions:
                weights = {}
                for vertex in face:
                    for bone, weight in self.body_vertex_weights[vertex].items():
                        weights[bone] = weights.get(bone, 0.) + weight
                self.body_face_regions[face] = max(weights, key=weights.get) if weights else 'unweighted'
        intersections = intersects(geometry, {
            'body': BVHTree.FromPolygons(body_points, body_faces, all_triangles=True, epsilon=0.),
            'do': tree_from(self.do, depsgraph)},
            {'body': [self.body_face_regions[face] for face in body_faces]})
        deformation = {ob.name: self.deformation(ob, *geometry[ob.name], polygons[ob.name]) for ob in self.parts}
        target_error = max(abs(value - expected) for panel in targets['panels']
                           for row, wanted in zip(self.armor.pose.bones[panel['bone']].matrix, panel['target_blender_cm'])
                           for value, expected in zip(row, wanted))
        totals = {label: {
            'triangle_intersections': sum(part['triangle_intersections'] for part in details.values()),
            'maximum_sampled_penetration_estimate_mm': max(part['maximum_sampled_penetration_estimate_mm'] for part in details.values()),
            'intersecting_components': [name for name, part in details.items() if part['triangle_intersections']],
        } for label, details in intersections.items()}
        result = {**record, 'surface_intersections': intersections, 'totals': totals,
                  'deformation': deformation, 'hinge_targets': targets,
                  'maximum_target_readback_error_native_cm': target_error,
                  'maximum_pair_distance_error_metres': max(value['maximum_pair_distance_error_metres'] for value in deformation.values()),
                  'maximum_all_vertex_rigid_transform_error_metres': max(value['maximum_all_vertex_rigid_transform_error_metres'] for value in deformation.values()),
                  'inverted_or_collapsed_triangles': sum(value['reversed_triangles_relative_to_rigid_transform'] + value['collapsed_triangles_relative_to_reference'] for value in deformation.values()),
                  'measurement_seconds': time.perf_counter() - start}
        print('KUSAZURI_POSE ' + json.dumps({'pose': result['pose'], 'totals': totals,
              'rigidity_error_m': result['maximum_pair_distance_error_metres'],
              'inverted_or_collapsed_triangles': result['inverted_or_collapsed_triangles']}), flush=True)
        return result

    def visibility(self, outfit):
        for ob in self.fit:
            ob.hide_render = not outfit
        for ob in self.parts:
            ob.hide_render = False

    def render(self, name, eye, target, scale, **metadata):
        scene, camera = self.scene, self.scene.camera
        camera.location = Vector(eye)
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = scale
        prefix = 'probe-gated-fronts-' if self.gated_front_probe else 'probe-cardinal-fronts-' if self.cardinal_front_probe else ''
        scene.render.filepath = str(CAPTURES / (prefix + name + '.png'))
        bpy.ops.render.render(write_still=True)
        self.captures.append({'file': str(Path(scene.render.filepath).relative_to(ROOT)),
                              'eye_metres': list(eye), 'target_metres': list(target),
                              'orthographic_span_metres': scale, **metadata})

    def views(self):
        self.diagnostic('neutral')
        self.update_armor()
        self.visibility(False)
        target = (0, -.015, .845)
        views = {
            'front': ((0, -2.5, .845), .69), 'back': ((0, 2.5, .845), .69),
            'left': ((2.5, 0, .845), .69), 'right': ((-2.5, 0, .845), .69),
            'threequarter-front': ((1.4, -2.3, 1.20), .73),
            'threequarter-rear': ((1.4, 2.3, 1.20), .73),
            'top-interior': ((.06, -.09, 2.4), .73),
            'underside': ((.10, -.12, -.9), .73),
        }
        for name, (eye, scale) in views.items():
            self.render(name, eye, target, scale, kind='component', pose='neutral')
        # Temporary object offsets expose source construction; modifiers and
        # skinning remain intact and each original world matrix is restored.
        original = {ob.name: ob.matrix_world.copy() for ob in self.parts}
        angles = {panel['panel']: panel['theta'] for panel in armor_pose(self.rig, self.armor)['panels']}
        try:
            for ob in self.parts:
                panel = str(ob.get('panel', ''))
                matrix = original[ob.name].copy()
                if panel in angles:
                    theta = angles[panel]
                    radial = Vector((math.sin(theta), -math.cos(theta), 0))
                    separation = .16
                    if ob.name.endswith('_Interior'):
                        separation -= .08
                    elif ob.name.endswith('_Lacing'):
                        separation += .055
                    elif ob.name.endswith('_Trim'):
                        separation += .095
                    matrix.translation += radial * separation
                else:
                    matrix.translation.z += .14
                ob.matrix_world = matrix
            bpy.context.view_layer.update()
            self.render('exploded-construction', (1.6, -2.5, 1.85), (0, 0, .9), 1.18,
                        kind='exploded component inspection', pose='neutral',
                        note='Temporary radial layer offsets and raised belt; no source edits saved.')
        finally:
            for ob in self.parts:
                ob.matrix_world = original[ob.name]
            bpy.context.view_layer.update()
        self.visibility(True)
        for name, eye in [('outfit-front', (0, -3, 1.0)), ('outfit-back', (0, 3, 1.0)),
                          ('outfit-threequarter', (1.5, -3, 1.7))]:
            self.render(name, eye, (0, 0, .93), 2.05, kind='complete current armor fixture', pose='neutral')
        self.render('tactical-distance', (5.5, -8.5, 7.5), (0, 0, .85), 8.5,
                    kind='single figure tactical-distance readability', pose='neutral',
                    note='Functional Blender orthographic capture; no performance measurement.')

    def motion_views(self, checks):
        self.visibility(True)
        chosen = {}
        for record in checks:
            if not record.get('clip'):
                chosen[record['pose']] = (record, 'requested static diagnostic')
        for clip in CLIPS:
            group = [record for record in checks if record.get('clip') == clip]
            if not group:
                continue
            for target in ('body', 'do'):
                worst = max(group, key=lambda record: (
                    record['totals'][target]['triangle_intersections'],
                    record['totals'][target]['maximum_sampled_penetration_estimate_mm']))
                chosen.setdefault(worst['pose'], (worst, target + ': maximum triangle intersections; contact depth breaks ties'))
                deepest = max(group, key=lambda record: (
                    record['totals'][target]['maximum_sampled_penetration_estimate_mm'],
                    record['totals'][target]['triangle_intersections']))
                chosen.setdefault(deepest['pose'], (deepest, target + ': maximum sampled contact penetration estimate'))
            deepest_leg = max(group, key=lambda record: tuple(reversed(leg_contact(record))))
            if any(leg_contact(deepest_leg)):
                previous = chosen.get(deepest_leg['pose'])
                reason = 'leg: maximum sampled contact penetration estimate; triangle intersections break ties'
                chosen[deepest_leg['pose']] = (deepest_leg, previous[1] + '; ' + reason if previous else reason)
            openest = max(group, key=lambda record: max(panel['angle_radians'] for panel in record['hinge_targets']['panels']))
            chosen.setdefault(openest['pose'], (openest, 'maximum measured panel hinge opening'))
        # Keep direct before/after evidence for the frames that motivated the
        # controller and tassel corrections, even after their contacts clear.
        regressions = {'A_Walk:19', 'A_Run:22', 'A_Run:32', 'A_Run:39', 'A_Attack:13'}
        for record in checks:
            if record['pose'] in regressions:
                chosen.setdefault(record['pose'], (record, 'previously failing leg-contact regression frame'))
        for record, reason in chosen.values():
            self.apply(record)
            self.render('pose-' + record['pose'].replace(':', '-'), (1.5, -2.6, 1.5), (0, 0, .96), 2.15,
                        kind='motion', pose=record['pose'], selection_reason=reason,
                        measured_totals=record['totals'])
        return [{'pose': record['pose'], 'selection_reason': reason} for record, reason in chosen.values()]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--views', action='store_true', help='Render source views without motion measurement')
    parser.add_argument('--motions', action='store_true', help='Render measured motion samples without component views')
    parser.add_argument('--render-only', action='store_true', help='Use existing matching full/quick measurements')
    parser.add_argument('--frame-step', type=int, default=1)
    parser.add_argument('--resolution', type=int, default=1100)
    parser.add_argument('--samples', type=int, default=24)
    parser.add_argument('--probe-cardinal-fronts', action='store_true',
                        help='Experimental Front_L/R sagittal hinge, .05 rad margin; separate report files, no controller save')
    parser.add_argument('--probe-gated-fronts', action='store_true',
                        help='Experimental Front_L/R sagittal 50-75 degree smoothstep blend, all-panel .02 rad margin')
    parser.add_argument('--fail-on-contact', action='store_true', help='Exit nonzero if any measured body/Do surface contact remains')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if args.frame_step < 1 or args.resolution < 64 or args.samples < 1:
        parser.error('frame-step/samples must be positive; resolution must be at least 64')
    if args.views and args.motions:
        parser.error('Use --render for both source and motion views')
    if args.probe_cardinal_fronts and args.probe_gated_fronts:
        parser.error('Choose only one experimental hinge variant')
    return args


def main():
    args = arguments()
    review = Review(args.probe_cardinal_fronts, args.probe_gated_fronts)
    suffix = '-quick' if args.quick else ''
    if args.probe_cardinal_fronts:
        suffix += '-probe-cardinal-fronts'
    if args.probe_gated_fronts:
        suffix += '-probe-gated-fronts'
    report_path = OUTPUT / ('motion-validation' + suffix + '.json')
    hinge_path = OUTPUT / ('hinge-reference-poses' + suffix + '.json')
    report = None
    render_requested = args.render or args.views or args.motions or args.render_only
    if args.render_only:
        report = json.loads(report_path.read_text())
        if report['source_sha256'] != review.source_hash or report['motion_script_sha256'] != review.motion_hash:
            raise RuntimeError('Existing motion report does not match saved source/controller; measure again before rendering')
        if report.get('controller_variant', 'production kusazuri_motion.armor_pose') != review.controller_variant:
            raise RuntimeError('Existing motion report uses a different controller variant')
    elif not args.views:
        review.prepare_reference()
        diagnostics = QUICK_DIAGNOSTICS if args.quick else DIAGNOSTICS
        checks = [review.measure({'pose': name, 'type': 'static diagnostic; not a native clip', 'frame': 1, 'clip': None})
                  for name in diagnostics]
        unavailable, coverage = [], {}
        for clip in CLIPS:
            if clip not in bpy.data.actions:
                unavailable.append(clip)
                continue
            action = bpy.data.actions[clip]
            first, last = math.ceil(action.frame_range[0]), math.floor(action.frame_range[1])
            if args.quick:
                frames = sorted({first, round(first + (last - first) * .25), round(first + (last - first) * .5),
                                 round(first + (last - first) * .75), last})
            else:
                frames = sorted(set(range(first, last + 1, args.frame_step)) | {last})
            coverage[clip] = {'saved_action_frame_range': list(action.frame_range), 'sampled_frames': frames,
                              'all_integer_frames': frames == list(range(first, last + 1))}
            for frame in frames:
                checks.append(review.measure({'pose': clip + ':' + str(frame), 'clip': clip, 'frame': frame,
                                               'type': 'native Manny bone animation; object root locked in place'}))
        contacts = any(value['triangle_intersections'] for check in checks for value in check['totals'].values())
        rigid = all(check['maximum_pair_distance_error_metres'] <= RIGID_TOLERANCE_M and
                    check['maximum_all_vertex_rigid_transform_error_metres'] <= RIGID_TOLERANCE_M and
                    not check['inverted_or_collapsed_triangles'] and
                    all(item['finite_vertices'] and item['rigid_transform_determinant'] > 0 for item in check['deformation'].values())
                    for check in checks)
        targets_reproduced = all(check['maximum_target_readback_error_native_cm'] <= .002 for check in checks)
        report = {'schema_version': 1, 'asset': 'Kusazuri01', 'source_sha256': review.source_hash,
                  'controller_variant': review.controller_variant,
                  'motion_script_sha256': review.motion_hash, 'review_script_sha256': sha256(Path(__file__)),
                  'sode_preview_motion_sha256': review.sode_motion_hash, 'blender_version': bpy.app.version_string,
                  'command_arguments': sys.argv, 'quick': args.quick, 'coverage': coverage,
                  'checks': checks, 'unavailable_native_actions': unavailable,
                  'diagnostic_definitions': DIAGNOSTICS, 'native_bow_clip_available': False,
                  'source_file_unchanged': sha256(review.source) == review.source_hash,
                  'controlled_rigid_hinges': True, 'rigidity_preserved': rigid,
                  'controller_targets_reproduced': targets_reproduced,
                  'surface_clear_in_all_samples': not contacts,
                  'validated': rigid and targets_reproduced and not contacts and not unavailable,
                  'limits': ['Integer-frame sampling does not prove continuous or subframe clearance.',
                            'Triangle overlap counts are exhaustive surface pairs for source components against body and Do, not penetration depth.',
                            'Maximum sampled penetration is a signed nearest-surface estimate at vertices of intersecting armor triangles. Up to 256 uniform additional vertices per part contribute unsigned clearance and a separate negative-normal distance diagnostic, not contact depth. Neither is a solid Boolean depth or an exhaustive interior-triangle extremum; overlapping/open target shells can make sign ambiguous.',
                            'Rigid pair distances are sampled; all evaluated vertices additionally check the expected bone rigid transform and all triangles check orientation and collapse.',
                            'Diagnostic poses are explicitly authored checks, not native crouch, bow, mounted or combat animation clips.',
                            'Sode uses its existing same-skeleton preview suspension; body and Do are independently evaluated from native animation.',
                            'Body contact region labels use the largest summed original skin-bone influence across each contacted triangle; these labels distinguish fingers from legs without changing the native pose.',
                            'Blender captures and source measurements do not establish Unreal rendering, animation, or crowd performance.']}
        report['validated'] = report['validated'] and report['source_file_unchanged']
        write_json(report_path, report)
        write_json(hinge_path, {'schema_version': 1, 'asset': 'Kusazuri01',
            'controller_variant': review.controller_variant,
            'source_sha256': review.source_hash, 'motion_script_sha256': review.motion_hash,
            'units': 'Native Blender armature centimetres; matrices are row arrays acting on column vectors',
            'blender_to_unreal_basis': [[1, 0, 0], [0, -1, 0], [0, 0, 1]],
            'basis_note': 'Convert local cm transforms by C @ M @ inverse(C), C=diag(1,-1,1,1). Object root .01 applies only for Blender world metres.',
            'root_world_matrix': matrix_rows(review.root_rest),
            'rest_bone_matrices': {bone.name: matrix_rows(bone.matrix_local) for bone in review.rig.data.bones},
            'poses': [{key: check[key] for key in ('pose', 'type', 'frame', 'clip')} | check['hinge_targets'] for check in checks],
            'expected_target_source': 'Temporary front-hinge diagnostic override; not production Unreal expectations.' if args.probe_cardinal_fronts or args.probe_gated_fronts else 'Unmodified armor_pose return values, frozen before Unreal verification.',
            'maximum_target_readback_error_native_cm': max(check['maximum_target_readback_error_native_cm'] for check in checks)})
        print('KUSAZURI01_MOTION_REPORT ' + str(report_path), flush=True)
    if render_requested:
        CAPTURES.mkdir(parents=True, exist_ok=True)
        review.scene.render.resolution_x = args.resolution
        review.scene.render.resolution_y = args.resolution
        review.scene.render.resolution_percentage = 100
        review.scene.render.image_settings.file_format = 'PNG'
        review.scene.cycles.samples = args.samples
        if args.views or args.render or (args.render_only and not args.motions):
            review.views()
        selected = review.motion_views(report['checks']) if report and not args.views else []
        write_json(OUTPUT / ('capture-manifest' + suffix + '.json'), {
            'controller_variant': review.controller_variant,
            'source_sha256': review.source_hash, 'motion_script_sha256': review.motion_hash,
            'review_script_sha256': sha256(Path(__file__)),
            'blender_version': bpy.app.version_string, 'resolution': args.resolution,
            'cycles_samples': args.samples, 'captures': review.captures, 'motion_selection': selected,
            'source_file_unchanged': sha256(review.source) == review.source_hash,
            'scope': 'Functional Blender source/still-pose captures; no Unreal or performance claim.'})
    if sha256(review.source) != review.source_hash:
        raise RuntimeError('Source file changed during review; do not claim preservation')
    if report and (not report['rigidity_preserved'] or not report['controller_targets_reproduced'] or report['unavailable_native_actions']):
        raise RuntimeError('Motion review failed rigidity, orientation, or required native action availability')
    if report and args.fail_on_contact and not report['surface_clear_in_all_samples']:
        raise RuntimeError('Measured body/Do surface intersections remain; see motion report')
    print('KUSAZURI01_REVIEW_COMPLETE ' + json.dumps({'captures': len(review.captures),
          'measured_poses': len(report['checks']) if report else 0,
          'surface_clear': report['surface_clear_in_all_samples'] if report else None}), flush=True)


if __name__ == '__main__':
    main()
