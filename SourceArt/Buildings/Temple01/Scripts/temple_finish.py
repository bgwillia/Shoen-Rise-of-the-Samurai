"""Temple-specific restrained weathered cedar finish, shared by source and exports."""
import math

def export_linear(path,objects):
 """Existing SHŌEN FBX settings with linear authored vertex tints for Unreal."""
 import bpy
 from export_do import common
 common.select(objects)
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
  apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',
  use_space_transform=False,bake_space_transform=False,mesh_smooth_type='FACE',use_tspace=True,
  use_mesh_modifiers=True,colors_type='LINEAR',add_leaf_bones=False,bake_anim=False,
  path_mode='RELATIVE',embed_textures=False)

def finish_materials(objects):
 for ob in objects:
  if ob.type!='MESH' or ob.get('temple_finish_v2'):continue
  colors=ob.data.color_attributes.get('Color')
  if not colors:continue
  roof_object='Temple_MainRoof_01 / TP01_MainRoof' in ob.name
  gable='Temple_MainRoof_01 / TP01_Gable' in ob.name
  gate='TempleGate_01' in ob.name
  pavilion='TempleBellPavilion_01' in ob.name
  for face in ob.data.polygons:
   material=ob.data.materials[face.material_index]
   if not material or not material.name.startswith('TP01_Cedar'):continue
   z=sum(ob.data.vertices[i].co.z for i in face.vertices)/len(face.vertices)
   roof=roof_object or ((gate or pavilion) and z>2.83)
   base=(.31,.39,.49) if roof else (.37,.41,.45)
   for li in face.loop_indices:
    p=ob.data.vertices[ob.data.loops[li].vertex_index].co
    old=colors.data[li].color
    if roof:
     # Quiet material variation rather than a patchwork of unrelated planks.
     tone=max(.94,min(1.06,1+(old[0]/.59-1)*.12))
     tone*=.985+.025*math.sin(p.x*1.7+p.y*1.1)
    else:
     tone=.91+.07*math.sin(p.x*.91+p.y*.78+p.z*.53)
     if p.z<1.5:tone*=.76+.24*max(0,min(1,p.z/1.5))
     if gable:tone*=.90
    colors.data[li].color=(*(c*tone for c in base),1)
  ob['temple_finish_v2']=True
