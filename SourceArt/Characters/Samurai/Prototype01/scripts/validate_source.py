"""Blender background source-contract check; deliberately independent of generator."""
import bpy
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'Samurai01.blend'
assert source.is_file(), 'Missing Blender source asset'
bpy.ops.wm.open_mainfile(filepath=str(source))
required = ['SK_Body', 'CLO_Undergarment', 'CLO_Hakama', 'CLO_Footwear',
            'ARM_Chest', 'ARM_Shoulder_L', 'ARM_Shoulder_R', 'ARM_Kote_L',
            'ARM_Kote_R', 'ARM_Kusazuri', 'ARM_Suneate_L', 'ARM_Suneate_R',
            'ARM_Kabuto', 'WPN_Yumi', 'WPN_Tachi', 'WPN_Sheath', 'PROP_Quiver', 'PROP_Arrows']
for name in required:
    assert name in bpy.data.objects, f'Missing modular source object {name}'
rig = bpy.data.objects['RIG_Samurai01']
assert rig.type == 'ARMATURE'
assert len([b for b in rig.data.bones if not b.parent]) == 1
assert all(n in rig.data.bones for n in ['root', 'pelvis', 'head', 'hand_l', 'hand_r', 'foot_l', 'foot_r'])
meshes = [bpy.data.objects[n] for n in required]
for obj in meshes:
    assert obj.type == 'MESH' and len(obj.data.polygons) > 0
    assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co)
    assert all(len(v.groups) > 0 for v in obj.data.vertices), f'Unweighted vertices: {obj.name}'
    assert all(abs(sum(g.weight for g in v.groups)-1) < .001 for v in obj.data.vertices)
    assert obj.data.uv_layers, f'Missing UVs: {obj.name}'
for action in ['A_Neutral', 'A_Idle', 'A_Walk', 'A_Attack']:
    assert bpy.data.actions.get(action), f'Missing action {action}'
assert not bpy.data.objects['WPN_Tachi'].data is bpy.data.objects['SK_RuntimeBody'].data
runtime = bpy.data.objects['SK_RuntimeBody']
assert len(runtime.data.materials) == 1
assert all(bpy.path.abspath(i.filepath) and Path(bpy.path.abspath(i.filepath)).exists()
           for i in bpy.data.images if i.source == 'FILE' and not i.packed_file)
report = {'blender': bpy.app.version_string, 'source_objects': len(meshes),
          'bones': len(rig.data.bones), 'runtime_body_materials': len(runtime.data.materials),
          'validated': True}
(root / 'source-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('SHOEN_SAMURAI_SOURCE_VALIDATED', json.dumps(report))
