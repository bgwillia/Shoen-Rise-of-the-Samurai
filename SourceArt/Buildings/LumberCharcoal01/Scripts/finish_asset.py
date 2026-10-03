"""Keep the authored yard colors linear in the existing SHŌEN FBX workflow."""
from pathlib import Path
import sys
import bpy
from mathutils import Matrix

ART=Path(__file__).resolve().parents[1]
ROOT=ART.parents[2]
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))

def export_linear(path,objects):
 from export_do import common
 common.select(objects)
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
  apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',
  use_space_transform=False,bake_space_transform=False,mesh_smooth_type='FACE',use_tspace=True,
  use_mesh_modifiers=True,colors_type='LINEAR',add_leaf_bones=False,bake_anim=False,
  path_mode='RELATIVE',embed_textures=False)

if __name__=='__main__':
 import json
 bpy.ops.wm.open_mainfile(filepath=str(ART/'LumberCharcoal01.blend'))
 src=bpy.data.collections['LumberCharcoal_01 • modular exterior']
 assembly=json.loads((ART/'Exports/assembly.json').read_text())
 unique={}
 for item in assembly['instances']:
  if item['mesh'] not in unique:unique[item['mesh']]=list(bpy.data.collections[item['name']].objects)
 base=bpy.data.collections['Reusable base logs • excluded from yard display']
 key=None
 for ob in base.objects:
  if ob.name.startswith('Rough bark log '):key='LC01_Log_%02d'%(int(ob.name.rsplit(' ',1)[-1])+1)
  if key is None:raise RuntimeError('Unexpected base log ordering')
  unique.setdefault(key,[]).append(ob)
 for key,objects in unique.items():
  transforms=[o.matrix_world.copy() for o in objects]
  for o in objects:
   o.hide_set(False);o.matrix_world=Matrix.Identity(4);o.modifiers.new('FBX triangles','TRIANGULATE')
  export_linear(ART/'Exports'/(key+'.fbx'),objects)
  for o,m in zip(objects,transforms):o.modifiers.remove(o.modifiers['FBX triangles']);o.matrix_world=m
 assembled=[o for c in src.children for o in c.objects if o.type=='MESH']
 for o in assembled:o.modifiers.new('FBX triangles','TRIANGULATE')
 export_linear(ART/'Exports/LumberCharcoal_01.fbx',assembled)
 # Convenient full shed, including its roof, at a local ground-centred pivot.
 shed=unique['LC01_MainShed']+unique['LC01_Roof']
 for o in shed:o.matrix_world=Matrix.Identity(4)
 export_linear(ART/'Exports/LumberShed_01.fbx',shed)
 print('LINEAR_EXPORT_COMPLETE',flush=True)
