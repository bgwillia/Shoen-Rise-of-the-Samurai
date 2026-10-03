import unreal as u, math, time, traceback
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');S=R/'SourceArt/Environment/Vegetation/RiverbankGrassMedium01';O=R/'artifacts/riverbankgrassmedium01';D='/Game/Art/Environment/Vegetation/Grass/RiverbankGrassMedium01';V=u.Vector;L=u.MaterialEditingLibrary
try:
 es=u.get_editor_subsystem(u.EditorActorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);world=ed.get_editor_world();actors=es.get_all_level_actors()
 tasks=[]
 for f in [S/'Exports/RiverbankGrass_Medium_01.fbx',S/'Textures/T_RiverbankGrassMedium01_BaseColor.png']:
  t=u.AssetImportTask();t.filename=str(f);t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
  if f.suffix=='.fbx':
   t.destination_name='RiverbankGrass_Medium_01';opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;t.options=opt
  tasks.append(t)
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
 tex=u.load_asset(D+'/T_RiverbankGrassMedium01_BaseColor');tex.set_editor_property('srgb',True)
 mat=u.load_asset(D+'/M_RiverbankGrassMedium01') or u.AssetToolsHelpers.get_asset_tools().create_asset('M_RiverbankGrassMedium01',D,u.Material,u.MaterialFactoryNew());L.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True);mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
 tx=L.create_material_expression(mat,u.MaterialExpressionTextureSample);tx.texture=tex;L.connect_material_property(tx,'RGB',u.MaterialProperty.MP_BASE_COLOR)
 mul=L.create_material_expression(mat,u.MaterialExpressionMultiply);strength=L.create_material_expression(mat,u.MaterialExpressionConstant);strength.r=.24;L.connect_material_expressions(strength,'',mul,'B');L.connect_material_expressions(tx,'RGB',mul,'A');L.connect_material_property(mul,'',u.MaterialProperty.MP_SUBSURFACE_COLOR)
 for value,prop in [(.9,u.MaterialProperty.MP_ROUGHNESS),(.16,u.MaterialProperty.MP_SPECULAR)]:
  n=L.create_material_expression(mat,u.MaterialExpressionConstant);n.r=value;L.connect_material_property(n,'',prop)
 L.recompile_material(mat)
 mesh=u.load_asset(D+'/RiverbankGrass_Medium_01');mesh.set_material(0,mat);u.get_editor_subsystem(u.StaticMeshEditorSubsystem).remove_collisions(mesh)
 body=mesh.get_editor_property('body_setup');bi=body.get_editor_property('default_instance');bi.set_editor_property('collision_profile_name','NoCollision');bi.set_editor_property('collision_enabled',u.CollisionEnabled.NO_COLLISION);body.set_editor_property('default_instance',bi)
 u.EditorAssetLibrary.save_directory(D)

except: u.log_error(traceback.format_exc())
