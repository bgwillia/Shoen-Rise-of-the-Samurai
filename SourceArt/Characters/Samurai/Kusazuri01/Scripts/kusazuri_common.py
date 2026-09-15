"""Saved-source Kusazuri contracts; shared helpers come from committed armor code."""
import hashlib
import json
import math
import struct
from pathlib import Path
import sys

import bpy

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
SOURCE = 'Kusazuri01_Source'
FIT = 'Kusazuri01_Fit'
RUNTIME = 'Kusazuri01_Runtime'
STUDIO = 'Kusazuri01_Studio'
MATERIAL = 'M_Kusazuri01'
TINT = 'ArmorTint'
ROUND_GROUP = 'Do_Round_Surfaces'
# LOD2 uses the documented per-component policy, not a blanket collapse ratio.
REDUCTIONS = (1., .30, None)
PANEL_BONES = {
    'Kusazuri_01_Belt': 'pelvis',
    'Kusazuri_01_Front_Center': 'spine_01',
    'Kusazuri_01_Front_L': 'thigh_l',
    'Kusazuri_01_Front_R': 'thigh_r',
    'Kusazuri_01_Side_L': 'thigh_twist_01_l',
    'Kusazuri_01_Side_R': 'thigh_twist_01_r',
    'Kusazuri_01_Rear_L': 'thigh_twist_02_l',
    'Kusazuri_01_Rear_R': 'thigh_twist_02_r',
}

sys.path.insert(0, str(ART.parent / 'Kabuto01/Scripts'))
import kabuto_export_common as common
from export_kabuto import geometry_signature
sys.path.insert(0, str(ART.parent / 'Do01/Scripts'))
from export_do import normalize_reduced_weights, weight_info
common.ROUND_GROUP = ROUND_GROUP


def fbx(path, objects):
    """Native Dō FBX settings with the Kusazuri tint mask explicitly enabled."""
    for ob in objects:
        if ob.type == 'MESH':
            if list(ob.data.color_attributes.keys()) != [TINT]:
                raise RuntimeError('Runtime mesh requires one ArmorTint channel: ' + ob.name)
            ob.data.color_attributes.active_color_index = 0
            ob.data.color_attributes.render_color_index = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    common.select(objects)
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'ARMATURE'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Y', axis_up='Z',
        use_space_transform=False, bake_space_transform=False, mesh_smooth_type='FACE', use_tspace=True,
        use_mesh_modifiers=True, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
        use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=False,
        bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0,
        path_mode='RELATIVE', embed_textures=False, colors_type='LINEAR', prioritize_active_color=True)


def tint_info(mesh):
    """Measure corner-mask survival without rewriting or synthesizing colors."""
    layer = mesh.color_attributes.get(TINT)
    info = {'attribute_names': list(mesh.color_attributes.keys()), 'name': TINT,
        'domain': layer.domain if layer else None, 'data_type': layer.data_type if layer else None,
        'corners': len(layer.data) if layer else 0, 'black_corners': 0, 'white_corners': 0,
        'invalid_corners': 0, 'black_triangles': 0, 'white_triangles': 0, 'mixed_triangles': 0}
    if layer is None or layer.domain != 'CORNER' or layer.data_type != 'FLOAT_COLOR' or len(layer.data) != len(mesh.loops):
        info['valid'] = False
        return info
    labels = []
    digest = hashlib.sha256()
    for corner in layer.data:
        rgba = tuple(corner.color)
        digest.update(struct.pack('<4f', *rgba))
        finite_opaque = all(math.isfinite(value) for value in rgba) and abs(rgba[3]-1) <= 1e-6
        black = finite_opaque and all(abs(value) <= 1e-6 for value in rgba[:3])
        white = finite_opaque and all(abs(value-1) <= 1e-6 for value in rgba[:3])
        label = 'black' if black else 'white' if white else 'invalid'
        labels.append(label)
        info[label + '_corners'] += 1
    for polygon in mesh.polygons:
        values = {labels[index] for index in polygon.loop_indices}
        label = next(iter(values)) if len(values) == 1 else 'mixed'
        if label == 'invalid':
            label = 'mixed'
        info[label + '_triangles'] += len(polygon.vertices)-2
    info['color_data_sha256'] = digest.hexdigest()
    info['valid'] = info['attribute_names'] == [TINT] and not info['invalid_corners'] and not info['mixed_triangles'] and bool(labels)
    return info


def panel_name(name):
    """Resolve an editable panel or its explicitly named construction detail."""
    if name == 'Kusazuri_01_Lacing':
        return 'Kusazuri_01_Belt'
    for panel in sorted(PANEL_BONES, key=len, reverse=True):
        if name == panel or name in (panel + '_' + suffix for suffix in ('Lacing', 'Interior', 'Trim', 'Attachment')):
            return panel
    return None


def source_parts():
    collection = bpy.data.collections.get(SOURCE)
    return sorted((ob for ob in collection.all_objects if ob.type == 'MESH'), key=lambda ob: ob.name) if collection else []


def fit_meshes():
    collection = bpy.data.collections.get(FIT)
    return sorted((ob for ob in collection.all_objects if ob.type == 'MESH'), key=lambda ob: ob.name) if collection else []


def geometry_hash(ob):
    digest = hashlib.sha256()
    for vertex in ob.data.vertices:
        digest.update(struct.pack('<I3f', vertex.index, *vertex.co))
    for face in ob.data.polygons:
        digest.update(struct.pack('<I', len(face.vertices)))
        digest.update(struct.pack('<' + 'I' * len(face.vertices), *face.vertices))
    return digest.hexdigest()


def rig_hash(ob):
    digest = hashlib.sha256()
    for bone in ob.data.bones:
        digest.update((bone.name + '\0' + (bone.parent.name if bone.parent else '') + '\0').encode())
        digest.update(struct.pack('<16f', *(value for row in bone.matrix_local for value in row)))
        digest.update(struct.pack('<6f?', *bone.head_local, *bone.tail_local, bone.use_deform))
    return digest.hexdigest()


def scalar_properties(owner):
    result = {}
    for prop in owner.bl_rna.properties:
        if prop.identifier == 'rna_type':
            continue
        value = getattr(owner, prop.identifier, None)
        if isinstance(value, (str, bool, int, float)):
            result[prop.identifier] = value
        elif isinstance(value, bpy.types.ID):
            result[prop.identifier] = value.name
    return result


def preservation_signature(objects, rig):
    """Hash authored geometry, UVs, weights, modifiers, fixtures, rig and saved pose."""
    objects = sorted(objects, key=lambda ob: ob.name)
    digest = hashlib.sha256(geometry_signature(objects).encode())
    for ob in objects:
        digest.update(json.dumps([group.name for group in ob.vertex_groups]).encode())
        for vertex in ob.data.vertices:
            digest.update(json.dumps([(weight.group, weight.weight) for weight in vertex.groups]).encode())
        colors = ob.data.color_attributes
        digest.update(json.dumps([colors.active_color_index, colors.render_color_index]).encode())
        for layer in colors:
            digest.update(json.dumps([layer.name, layer.domain, layer.data_type]).encode())
            for corner in layer.data:
                digest.update(struct.pack('<4f', *corner.color))
        digest.update((ob.parent.name if ob.parent else '').encode())
        for matrix in (ob.matrix_basis, ob.matrix_parent_inverse):
            digest.update(struct.pack('<16f', *(value for row in matrix for value in row)))
        for modifier in ob.modifiers:
            digest.update(json.dumps(scalar_properties(modifier), sort_keys=True).encode())
        digest.update(json.dumps(sorted(collection.name for collection in ob.users_collection)).encode())
    digest.update(rig_hash(rig).encode())
    digest.update(struct.pack('<16f', *(value for row in rig.matrix_basis for value in row)))
    for bone in rig.pose.bones:
        digest.update(bone.name.encode())
        digest.update(struct.pack('<16f', *(value for row in bone.matrix_basis for value in row)))
        for constraint in bone.constraints:
            digest.update(json.dumps(scalar_properties(constraint), sort_keys=True).encode())
    animation = rig.animation_data
    scene = bpy.context.scene
    digest.update(json.dumps({'action': animation.action.name if animation and animation.action else None,
        'action_slot': animation.action_slot.identifier if animation and animation.action_slot else None,
        'use_nla': animation.use_nla if animation else None,
        'pose_position': rig.data.pose_position,
        'frame': scene.frame_current, 'subframe': scene.frame_subframe,
        'range': [scene.frame_start, scene.frame_end]}).encode())
    return digest.hexdigest()


def bounds(ob):
    points = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
    if not points:
        raise RuntimeError('Cannot measure empty armor mesh: ' + ob.name)
    return [[min(point[axis] for point in points) for axis in range(3)],
            [max(point[axis] for point in points) for axis in range(3)]]


def to_unreal_bounds(metres):
    low, high = metres
    lo, hi = [100*low[0], -100*high[1], 100*low[2]], [100*high[0], -100*low[1], 100*high[2]]
    return {'min': lo, 'max': hi, 'size': [b-a for a, b in zip(lo, hi)]}


def expected_exports():
    return [f'{folder}/{prefix}_Kusazuri01{suffix}.fbx'
            for folder, prefix in [('Exports', 'SK'), ('Review/Exports', 'SM')]
            for suffix in ('', '_LOD1', '_LOD2')]
