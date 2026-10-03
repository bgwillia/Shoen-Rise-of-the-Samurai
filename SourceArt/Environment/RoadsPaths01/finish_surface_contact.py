import unreal as u,traceback
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai')
exec((R/'SourceArt/Environment/RoadsPaths01/revise_finish.py').read_text().split('try:run()')[0])
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 w=u.EditorLoadingAndSavingUtils.load_map(str(R/'game/Content/Art/Environment/TerrainBase01/TerrainBase_01.umap'));a=u.get_editor_subsystem(u.EditorActorSubsystem);actors=a.get_all_level_actors();land=next(x for x in actors if isinstance(x,u.Landscape));ignore=[x for x in actors if x!=land]
 t=u.AssetImportTask();t.filename=str(S/'Exports/RP01_Approach.fbx');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
 opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;t.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
 surface=land.get_editor_property('landscape_material');surface.set_editor_property('used_with_spline_meshes',True);L.recompile_material(surface);u.EditorAssetLibrary.save_loaded_asset(surface,False)
 for act in actors:
  if act.get_actor_label().startswith('RP01_GradedEarthApproach_'):act.get_component_by_class(u.SplineMeshComponent).set_material(0,land.get_editor_property('landscape_material'));act.get_component_by_class(u.SplineMeshComponent).update_mesh()
 m=u.load_asset(D+'/M_RP01_FordBed');p=node(m,u.MaterialExpressionWorldPosition)
 tex=next(e for e in L.get_material_expressions(m) if isinstance(e,u.MaterialExpressionTextureSample) and e.get_editor_property('texture').get_name().endswith('diff_2k'))
 edge=custom(m,'''float2 q=W.xy-float2(-23600,-6300);
 float t=dot(q,float2(.42,.907524));float s=dot(q,float2(-.907524,.42));
 return saturate((250-abs(s))/95)*saturate((1000-abs(t))/290)-Noise*.23;''',['W','Noise'],u.CustomMaterialOutputType.CMOT_FLOAT1);connect(p,'',edge,'W');connect(tex,'R',edge,'Noise');L.connect_material_property(edge,'',u.MaterialProperty.MP_OPACITY_MASK);m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('opacity_mask_clip_value',.15);L.recompile_material(m)
 trib=next(x for x in actors if x.get_actor_label()=='WaterBase_01_Tributary');bc=trib.get_water_body_component();source=bc.get_editor_property('water_static_mesh_material');u.log('FORD_WATER_SOURCE '+source.get_path_name())
 water=u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D+'/M_RP01_TributaryFordSurface')
 old=L.get_material_property_input_node(water,u.MaterialProperty.MP_OPACITY);oldout=L.get_material_property_input_node_output_name(water,u.MaterialProperty.MP_OPACITY)
 if old:
  p=node(water,u.MaterialExpressionWorldPosition);opacity=custom(water,'''float2 q=W.xy-float2(-23600,-6300);
 float t=dot(q,float2(.42,.907524));float s=dot(q,float2(-.907524,.42));
 float f=(1-smoothstep(750,1200,abs(t)))*(1-smoothstep(180,340,abs(s)));
 return Base*(1-f*.86);''',['W','Base'],u.CustomMaterialOutputType.CMOT_FLOAT1);connect(p,'',opacity,'W');connect(old,oldout,opacity,'Base');L.connect_material_property(opacity,'',u.MaterialProperty.MP_OPACITY);L.recompile_material(water);bc.set_water_static_mesh_material(water)
 
 for actor in actors:
  if isinstance(actor,(u.DirectionalLight,u.SkyLight)):
   c=actor.get_component_by_class(u.LightComponentBase);u.log('LIGHT_SETTING '+actor.get_actor_label()+' '+str(c.get_editor_property('intensity')))
 u.EditorAssetLibrary.save_directory(D);u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Art/Environment/TerrainBase01/TerrainBase_01');capture()
except:u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
