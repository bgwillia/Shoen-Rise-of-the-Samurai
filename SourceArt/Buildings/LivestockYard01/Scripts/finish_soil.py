"""Finish the current visual correction: textured soil and a terrain-seated apron."""
from pathlib import Path
import sys, json
import bpy
from mathutils import Matrix

ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ART/'LivestockYard01.blend'))
scene=bpy.context.scene
mat=bpy.data.materials['LY01_Mud'];nodes=mat.node_tree.nodes;links=mat.node_tree.links
texture=nodes.get('Livestock soil albedo') or nodes.new('ShaderNodeTexImage')
texture.name='Livestock soil albedo'
texture.image=bpy.data.images.load(str(ART/'Textures/LY01_Soil_BaseColor.png'),check_existing=True)
texture.image.pack()
multiply=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
links.new(texture.outputs['Color'],multiply.inputs[1])
ground=bpy.data.collections['LY01_GroundApron']
for ob in ground.objects:
 if ob.type!='MESH':continue
 uv=ob.data.uv_layers.active
 for face in ob.data.polygons:
  if ob.data.materials[face.material_index]!=mat:continue
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(p.x*.4,p.y*.4)
bpy.data.objects['Review ground'].location.z=-.012
# Same rural-kit FBX settings; linear authored weather colors remain linear in Unreal.
# Export one instance of each module at its local pivot, then restore source placement.
assembly=json.loads((ART/'Exports/assembly.json').read_text());done=set()
for item in assembly['instances']:
 if item['mesh'] in done:continue
 done.add(item['mesh'])
 obs=list(bpy.data.collections[item['name']].objects)
 transforms=[ob.matrix_world.copy() for ob in obs]
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  ob.matrix_world=Matrix.Identity(4);ob.select_set(True)
  ob.modifiers.new('Export triangulation','TRIANGULATE')
 bpy.context.view_layer.objects.active=obs[0]
 bpy.ops.export_scene.fbx(filepath=str(ART/'Exports'/(item['mesh']+'.fbx')),
  use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',
  axis_forward='-Y',axis_up='Z',use_space_transform=False,bake_space_transform=False,
  mesh_smooth_type='FACE',use_tspace=True,use_mesh_modifiers=True,colors_type='LINEAR',
  add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',embed_textures=False)
 for ob,matrix in zip(obs,transforms):
  ob.matrix_world=matrix;ob.modifiers.remove(ob.modifiers['Export triangulation'])
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'LivestockYard01.blend'))
scene.render.filepath=str(ROOT/'artifacts/livestockyard01/livestockyard-three-quarter.png')
if '--export-only' not in sys.argv:bpy.ops.render.render(write_still=True)
print('SOIL_FINISH_SAVED',len(done),'linear-color modules',flush=True)
