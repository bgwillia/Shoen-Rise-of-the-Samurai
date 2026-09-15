"""Sample native Manny motions and diagnostic arm/bow poses on saved Sode.

Never saves source edits. `--render` additionally renders the first native
sample and each diagnostic in the source's functional three-quarter studio.
Native bone action channels are unchanged on temporary in-place action copies.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sode_common import ART, ROOT, FIT, RUNTIME, source_parts
from validate_sode import evaluated, intersection_report, is_attachment


def main():
    source = ART / 'Sode01.blend'
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if '--render' in sys.argv:
        from sode_render_settings import configure
        configure(scene)
    rig, body, helmet = [bpy.data.objects[name] for name in ('root', 'Manny_Review', 'Kabuto_Review')]
    parts = source_parts()
    do_parts = [ob for ob in bpy.data.collections[FIT].all_objects if ob.type == 'MESH' and ob.name.startswith('Do_Review')]
    fixtures = {'body': [body], 'kabuto': [helmet], 'do': do_parts}
    for ob in bpy.data.collections[RUNTIME].objects:
        ob.hide_render = True
        ob.hide_set(True)
    for ob in [rig, body, helmet, *parts, *do_parts]:
        ob.hide_set(False)
    rig.animation_data_create()
    rig.animation_data.use_nla = False
    rig.data.pose_position = 'POSE'
    root_rest = Matrix.Diagonal((.01, .01, .01, 1.))
    from sode_motion import review_rig, armor_pose
    controlled='--controlled' in sys.argv
    motion_rig=review_rig(rig,parts) if controlled else None

    def neutral():
        rig.animation_data.action = None
        for bone in rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        scene.frame_set(1)
        rig.matrix_basis = root_rest
        bpy.context.view_layer.update()

    def direct_arm(name, direction):
        bone = rig.data.bones[name]
        origin = bone.head_local
        original_direction = rig.data.bones[name.replace('upperarm', 'lowerarm')].head_local-origin
        rotation = original_direction.rotation_difference(Vector(direction).normalized())
        rig.pose.bones[name].matrix = Matrix.Translation(origin) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-origin) @ bone.matrix_local

    def diagnostic(name):
        neutral()
        if name == 'arms-forward':
            for sign, suffix in [(1, 'l'), (-1, 'r')]:
                direct_arm('upperarm_' + suffix, (sign*.13, -1, -.12))
        elif name == 'arms-raised':
            for sign, suffix in [(1, 'l'), (-1, 'r')]:
                direct_arm('upperarm_' + suffix, (sign*.90, -.2, .10))
        elif name == 'bow-diagnostic':
            direct_arm('upperarm_l', (.18, -1, .08))
            direct_arm('upperarm_r', (-.75, .6, .12))
            bpy.context.view_layer.update()
            lower = rig.pose.bones['lowerarm_r']
            current = lower.matrix.copy()
            origin = current.translation
            hand_position = rig.pose.bones['hand_r'].matrix.translation
            target = Vector((0., -4., 157.))  # Native rig local centimetres.
            rotation = (hand_position-origin).rotation_difference(target-origin)
            lower.matrix = Matrix.Translation(origin) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-origin) @ current
        bpy.context.view_layer.update()

    def native_action(name):
        neutral()
        action = bpy.data.actions[name].copy()
        action.name = 'SODE_REVIEW_IN_PLACE_' + name
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    bag = strip.channelbag(slot)
                    if bag:
                        for curve in list(bag.fcurves):
                            if not curve.data_path.startswith('pose.bones['):
                                bag.fcurves.remove(curve)
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        rig.matrix_basis = root_rest

    neutral()
    if motion_rig:armor_pose(rig,motion_rig)
    dg = bpy.context.evaluated_depsgraph_get()
    references = {}
    for ob in parts:
        if is_attachment(ob.name):
            continue
        _, points, _ = evaluated(ob, dg, inspect=False)
        stride = max(1, len(points)//64)
        pairs = [(index, (index+len(points)//2) % len(points)) for index in range(0, len(points), stride)]
        references[ob.name] = [(a, b, (points[a]-points[b]).length) for a, b in pairs]

    def measure(label, motion_type):
        bpy.context.view_layer.update()
        target_matrices=armor_pose(rig,motion_rig) if motion_rig else None
        depsgraph = bpy.context.evaluated_depsgraph_get()
        observations = intersection_report(parts, fixtures, depsgraph)
        rigidity = {}
        for ob in parts:
            if ob.name not in references:
                continue
            _, points, _ = evaluated(ob, depsgraph, inspect=False)
            rigidity[ob.name] = max(abs((points[a]-points[b]).length-distance)
                for a, b, distance in references[ob.name])
        result = {'suspension_targets':target_matrices, 'pose': label, 'type': motion_type, 'frame': scene.frame_current,
            'surface_intersections': observations,
            'rigid_shell_maximum_sample_distance_error_metres': max(rigidity.values()),
            'rigid_components_distance_errors_metres': rigidity,
            'totals': {target: {'rigid_shell_triangle_pairs': sum(info['triangle_intersections']
                for name, info in details.items() if not is_attachment(name)),
                'flexible_suspension_triangle_pairs': sum(info['triangle_intersections']
                for name, info in details.items() if is_attachment(name))}
                for target, details in observations.items()}}
        print('SODE_POSE ' + json.dumps({'pose': label, 'totals': result['totals'],
            'rigidity_error_m': result['rigid_shell_maximum_sample_distance_error_metres']}), flush=True)
        return result

    def render(label):
        if '--render' not in sys.argv:
            return None
        if '--attack-only' in sys.argv and not label.startswith('A_Attack:'):
            return None
        scene.render.resolution_x = 1100
        scene.render.resolution_y = 1100
        scene.render.resolution_percentage = 100
        scene.cycles.samples = 24
        for ob in [body, helmet, *do_parts, *parts]:
            ob.hide_render = False
        camera = scene.camera
        camera.location = Vector((1.25, -2.1, 1.85))
        target = Vector((0, 0, 1.43))
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = 1.55
        path = ART / 'Review/Captures' / ('pose-' + label.replace(':', '-') + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return str(path.relative_to(ROOT))

    checks, captures, unavailable = [], [], []
    for label in (('neutral',) if '--quick' in sys.argv else ('neutral', 'arms-forward', 'arms-raised', 'bow-diagnostic')):
        diagnostic(label)
        checks.append(measure(label, 'diagnostic; not a native animation clip'))
        image = render(label)
        if image:
            captures.append(image)
    clips = [('A_Idle', [15, 110]), ('A_Walk', [8, 23, 37]), ('A_Run', [8, 23, 40]), ('A_Attack', [6, 12, 20, 28])]
    if '--quick' in sys.argv:clips=[('A_Attack',[6,12])]
    for name, frames in clips:
        if name not in bpy.data.actions:
            unavailable.append(name)
            continue
        native_action(name)
        for frame in frames:
            scene.frame_set(frame)
            rig.matrix_basis = root_rest
            bpy.context.view_layer.update()
            label = name + ':' + str(frame)
            checks.append(measure(label, 'native Manny bone animation, root locked in place'))
            if frame == frames[0] or ('--attack-only' in sys.argv and name=='A_Attack' and frame==12):
                image = render(label)
                if image:
                    captures.append(image)
    output = ROOT / ('artifacts/sode01/pose-quick.json' if '--quick' in sys.argv else 'artifacts/sode01/pose-review.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'asset': 'Sode01', 'source_sha256': original_hash,
        'controlled_rigid_suspension':controlled,
        'source_file_unchanged': hashlib.sha256(source.read_bytes()).hexdigest() == original_hash,
        'checks': checks, 'captures': captures, 'unavailable_native_actions': unavailable,
        'native_bow_clip_available': False,
        'diagnostic_definitions': {'arms-forward': 'upper arms directed (±.13,-1,-.12)',
            'arms-raised': 'upper arms directed (±.90,-.2,.10)',
            'bow-diagnostic': 'left upper arm toward (.18,-1,.08), right toward (-.75,.6,.12), right hand toward draw point (0,-.04,1.57)m; no bow asset'},
        'scope': 'Sampled existing native Manny motions and explicit static diagnostics on saved source and preserved armor fixtures. No source is saved. Native bone channels are unchanged on temporary action copies with object-root channels removed.',
        'limitations': ['Triangle overlap counts are surface intersections, not penetration depth or continuous motion clearance.',
            'Only the suspension ties may flex; rigidity uses sampled vertex-pair lengths and does not prove every pair.',
            'A native bow-use animation is unavailable; bow pose is an explicitly labeled diagnostic, without a weapon.',
            'Blender evidence does not substitute for Unreal import/render/animation checks.']}
    result['motion_script_sha256']=hashlib.sha256((ART/'Scripts/sode_motion.py').read_bytes()).hexdigest()
    result['rigid_shell_clear_in_all_samples']=all(c['totals'][target]['rigid_shell_triangle_pairs']==0 for c in checks for target in fixtures)
    result['rigidity_preserved']=all(c['rigid_shell_maximum_sample_distance_error_metres']<1e-4 for c in checks)
    result['validated']=controlled and not unavailable and result['source_file_unchanged'] and result['rigid_shell_clear_in_all_samples'] and result['rigidity_preserved']
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('SODE01_POSE_REVIEW ' + str(output), flush=True)


if __name__ == '__main__':
    main()
