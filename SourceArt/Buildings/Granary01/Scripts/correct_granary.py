"""Single visual correction: visible high vents, steeper roof, complete framing."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ART/'Granary01.blend'))
scene=bpy.context.scene;src=bpy.data.collections['Granary_01 • editable exterior']
for v in bpy.data.objects['GR01_Vents'].data.vertices:v.co.z-=.30
for name in ['GR01_Roof','GR01_RoofBundles','GR01_Eaves','GR01_Ridge','GR01_RidgeLashings']:
 for v in bpy.data.objects[name].data.vertices:
  v.co.x*=.965;v.co.y*=.985
  if v.co.z>2.72:v.co.z=2.72+(v.co.z-2.72)*1.13
cam=bpy.data.objects['Granary three-quarter'];cam.location=(7,-11,5.1)
cam.rotation_euler=(Vector((0,-.15,1.96))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=6.35
scene.camera=cam
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
components=list(src.objects)
for o in components:o.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/Granary_01.fbx',components)
for o in components:o.modifiers.remove(o.modifiers['Export triangulation'])
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Granary01.blend'))
scene.render.filepath=str(ROOT/'artifacts/granary01/granary-three-quarter.png');bpy.ops.render.render(write_still=True)
print('GRANARY_VISUAL_CORRECTION_COMPLETE',flush=True)
