"""Functional source review captures. Saved source remains unchanged."""
from pathlib import Path
import sys, json
import bpy
from mathutils import Vector
ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART/'Scripts'))
from sode_render_settings import configure
bpy.ops.wm.open_mainfile(filepath=str(ART/'Sode01.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['root'];rig.animation_data_clear();rig.data.pose_position='REST'
configure(scene)
parts=list(bpy.data.collections['Sode01_Source'].objects);fit=list(bpy.data.collections['Sode01_Fit'].objects)
for ob in bpy.data.collections['Sode01_Runtime'].objects:ob.hide_render=True
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.cycles.samples=24
cam=scene.camera
manifest=json.loads((ART/'asset-manifest.json').read_text())
def render(name,eye,target,scale):
    cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(ART/f'Review/Captures/{name}.png');bpy.ops.render.render(write_still=True)
for ob in fit:ob.hide_render=ob.type=='ARMATURE'
for ob in parts:ob.hide_render=False
render('fit-refined',(.85,-1.8,1.83),(0,0,1.43),1.27)
for ob in fit:ob.hide_render=True
for side in ['L','R']:
    for ob in parts:ob.hide_render=not ob.name.startswith('Sode_'+side+'_')
    f=manifest['side_frames'][side];p=Vector(f['pivot']);n=Vector(f['outward']);down=Vector(f['down']);across=Vector(f['across'])
    center=p+down*.085+n*.070
    # Exact outside/inside views establish wearer-side assignment and lining construction.
    render('Sode_'+side+'_01-outside',center+n*1.3-across*.26-down*.08,center,.47)
    render('Sode_'+side+'_01-inside',center-n*1.3-across*.08-down*.10,center,.47)
print('SODE01_SOURCE_VIEWS_COMPLETE')
