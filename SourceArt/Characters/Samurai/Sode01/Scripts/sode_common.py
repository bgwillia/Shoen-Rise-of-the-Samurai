"""Sode source/export contracts and read-only inspection helpers."""
import hashlib
import json
import struct
from pathlib import Path
import sys

import bpy

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
SOURCE = 'Sode01_Source'
FIT = 'Sode01_Fit'
RUNTIME = 'Sode01_Runtime'
STUDIO = 'Sode01_Studio'
SIDES = ('L', 'R')
MATERIAL = 'M_Sode01'
ROUND_GROUP = 'Do_Round_Surfaces'
# Ratios are independently applied to the complete evaluated source geometry.
REDUCTIONS = (.60, .22, .07)

sys.path.insert(0, str(ART.parent / 'Kabuto01/Scripts'))
import kabuto_export_common as common
from export_kabuto import geometry_signature
sys.path.insert(0, str(ART.parent / 'Do01/Scripts'))
from export_do import fbx, normalize_reduced_weights, weight_info
common.ROUND_GROUP = ROUND_GROUP


def source_parts(side=None):
    prefix = 'Sode_' + side + '_01_' if side else 'Sode_'
    return sorted((ob for ob in bpy.data.collections[SOURCE].all_objects
                   if ob.type == 'MESH' and ob.name.startswith(prefix)), key=lambda ob: ob.name)


def fit_meshes():
    return sorted((ob for ob in bpy.data.collections[FIT].all_objects if ob.type == 'MESH'), key=lambda ob: ob.name)


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


def preservation_signature(objects, rig):
    """Mesh, UV, weights, modifier settings, rig, and saved pose identity."""
    digest = hashlib.sha256(geometry_signature(objects).encode())
    for ob in objects:
        digest.update(json.dumps([group.name for group in ob.vertex_groups]).encode())
        for vertex in ob.data.vertices:
            digest.update(json.dumps([(weight.group, weight.weight) for weight in vertex.groups]).encode())
        digest.update((ob.parent.name if ob.parent else '').encode())
        for modifier in ob.modifiers:
            props = {}
            for prop in modifier.bl_rna.properties:
                if prop.identifier == 'rna_type':
                    continue
                value = getattr(modifier, prop.identifier, None)
                if isinstance(value, (str, bool, int, float)):
                    props[prop.identifier] = value
                elif isinstance(value, bpy.types.ID):
                    props[prop.identifier] = value.name
            digest.update(json.dumps(props, sort_keys=True).encode())
    digest.update(rig_hash(rig).encode())
    for row in rig.matrix_basis:
        digest.update(struct.pack('<4f', *row))
    for bone in rig.pose.bones:
        digest.update(bone.name.encode())
        for row in bone.matrix_basis:
            digest.update(struct.pack('<4f', *row))
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
    return [[min(point[axis] for point in points) for axis in range(3)],
            [max(point[axis] for point in points) for axis in range(3)]]


def to_unreal_bounds(metres):
    low, high = metres
    lo, hi = [100*low[0], -100*high[1], 100*low[2]], [100*high[0], -100*low[1], 100*high[2]]
    return {'min': lo, 'max': hi, 'size': [b-a for a, b in zip(lo, hi)]}
