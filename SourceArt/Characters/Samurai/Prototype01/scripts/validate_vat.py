"""Check persisted half-float VAT texels against the saved rig, independently of bake."""
import bpy
import json
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Samurai01.blend'))
manifest=json.loads((ROOT/'asset-manifest.json').read_text())
rig=bpy.data.objects['RIG_Samurai01']
worst=0.0; samples=0
for info in manifest['vat']:
    lod=info['lod']; mesh=bpy.data.objects[f'SM_Crowd_LOD{lod}']; width=info['texture_width']; rows=info['rows_per_frame']
    im=bpy.data.images.load(str(ROOT/f'textures/T_VAT_Position_LOD{lod}.exr'),check_existing=False)
    im.colorspace_settings.name='Non-Color'
    pixels=np.asarray(im.pixels[:],dtype=np.float32).reshape((info['texture_height'],width,4))
    ids=np.linspace(0,len(mesh.data.vertices)-1,200,dtype=int)
    for clip,(name,end) in enumerate([('A_Idle',61),('A_Walk',31),('A_Attack',46)]):
        rig.animation_data.action=bpy.data.actions[name]
        for sample in (0,6,12,18,23):
            at=1+sample*(end-1)/(23 if clip==2 else 24)
            bpy.context.scene.frame_set(int(at),subframe=at-int(at)); bpy.context.view_layer.update()
            transforms={pb.name:pb.matrix @ pb.bone.matrix_local.inverted() for pb in rig.pose.bones}
            for index in ids:
                vert=mesh.data.vertices[int(index)]; expected=Vector((0,0,0))
                for group in vert.groups:
                    expected += (transforms[mesh.vertex_groups[group.group].name] @ vert.co)*group.weight
                delta=(expected-vert.co)*100
                want=np.array((delta.x,-delta.y,delta.z))
                actual=pixels[(clip*24+sample)*rows+index//width,index%width,:3]
                error=float(np.max(np.abs(want-actual))); worst=max(worst,error); samples+=1
                assert error<.13, f'LOD{lod} {name} sample{sample} vertex{index}: {actual} != {want}, error {error}cm'
    uv=mesh.data.uv_layers['UV_VAT']
    for loop in mesh.data.loops:
        coord=uv.data[loop.index].uv; index=loop.vertex_index
        assert abs(coord.x-(index%width+.5)/width)<1e-6
        assert abs(coord.y-(index//width+.5)/info['texture_height'])<1e-6
report={'samples':samples,'worst_position_error_cm':worst,'half_float_vat_matches_saved_rig':True}
(ROOT/'vat-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('SHOEN_VAT_VALIDATED',json.dumps(report))
