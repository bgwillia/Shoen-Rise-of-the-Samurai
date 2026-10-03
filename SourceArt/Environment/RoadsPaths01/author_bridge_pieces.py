import bpy
from pathlib import Path
root=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/RoadsPaths01');out=root/'Exports';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,dims in [('Plank',(.26,3.6,.16)),('Beam',(4,.24,.32)),('Post',(.28,.28,3)),('Rail',(4,.12,.14))]:
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name='RP01_'+name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bevel=o.modifiers.new('Worn timber edges','BEVEL');bevel.width=.007 if name=='Plank' else .009;bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name)
 # Export all timbers at unit bounding dimensions, matching existing actor scales.
 for v in o.data.vertices:
  for j in range(3):v.co[j]/=dims[j]
 bpy.ops.export_scene.fbx(filepath=str(out/(o.name+'.fbx')),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',object_types={'MESH'},bake_anim=False)
 bpy.ops.object.select_all(action='DESELECT')
# Reusable sloped fill, top at Z=0; spline deforms longitudinal X.
verts=[(x,y,z) for x in [-.5,.5] for y,z in [(-5,-3),(-1.8,0),(1.8,0),(5,-3)]]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
m=bpy.data.meshes.new('RP01_Approach');m.from_pydata(verts,[],[face[::-1] for face in faces]);m.update();o=bpy.data.objects.new('RP01_Approach',m);bpy.context.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(out/'RP01_Approach.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',object_types={'MESH'},bake_anim=False)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=.5)
o=bpy.context.object;o.name='RP01_FordStone'
import random
rng=random.Random(1180)
for v in o.data.vertices:
 v.co*=rng.uniform(.89,1.08)
for p in o.data.polygons:p.use_smooth=True
bpy.ops.export_scene.fbx(filepath=str(out/'RP01_FordStone.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',object_types={'MESH'},bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'TimberBridge_01_pieces.blend'))
