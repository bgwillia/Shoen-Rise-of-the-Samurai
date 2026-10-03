"""One visual correction pass: pine tint and inward-facing side-building entrance."""
from pathlib import Path
import bpy, math, json, sys
from mathutils import Vector
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/manor01'
bpy.ops.wm.open_mainfile(filepath=str(ART/'Manor01.blend'))
scene=bpy.context.scene;src=bpy.data.collections['Manor_01 • editable local modules'];layout=bpy.data.collections['Manor_01 • authored compound']
src.hide_viewport=False;src.hide_render=False
for ob in src.objects:
 if not ob.name.startswith('MN01_GardenElements'):continue
 col=ob.data.color_attributes.get('Color')
 for f in ob.data.polygons:
  if 'Leaf' in ob.data.materials[f.material_index].name:
   for li in f.loop_indices:
    p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.90+.13*math.sin(p.x*4+p.y*3+p.z*2)
    col.data[li].color=(.52*k,.67*k,.35*k,1)
for ob in layout.objects:
 if ob.name.startswith('ManorSideBuilding_01_'):ob.rotation_euler.z=math.radians(90)
assembly=json.loads((ART/'Exports/assembly.json').read_text())
for item in assembly['instances']:
 if item['mesh']=='ManorSideBuilding_01':item['rotation_degrees']=90
(ART/'Exports/assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
obs=[o for o in src.objects if o.name.startswith('MN01_GardenElements')]
for o in obs:o.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/MN01_GardenElements.fbx',obs)
for o in obs:o.modifiers.remove(o.modifiers['Export triangles'])
for o in layout.objects:o.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/Manor_01.fbx',list(layout.objects))
for o in layout.objects:o.modifiers.remove(o.modifiers['Export triangles'])
src.hide_viewport=True;src.hide_render=True
scene.camera.location=(23,-36,12.6)
scene.camera.rotation_euler=(Vector((0,0,2.3))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.lens=52
scene.render.resolution_y=1200
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Manor01.blend'))
scene.render.filepath=str(OUT/'manor-three-quarter.png');bpy.ops.render.render(write_still=True)
print('MANOR_VISUAL_CORRECTION_COMPLETE',flush=True)
