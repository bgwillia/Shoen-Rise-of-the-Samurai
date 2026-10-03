import unreal as u,math,random,traceback
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai')
# Reuse the revision's material and camera helpers without repeating its scene edits.
exec((R/'SourceArt/Environment/RoadsPaths01/revise_finish.py').read_text().split('try:run()')[0])
try:
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 w=u.EditorLoadingAndSavingUtils.load_map(str(R/'game/Content/Art/Environment/TerrainBase01/TerrainBase_01.umap'));a=u.get_editor_subsystem(u.EditorActorSubsystem);actors=a.get_all_level_actors();land=next(x for x in actors if isinstance(x,u.Landscape));ignore=[x for x in actors if x!=land]
 mesh=u.load_asset(D+'/RP01_Approach');extent=mesh.get_bounds().box_extent;axis=u.SplineMeshAxis.X if extent.x<extent.y else u.SplineMeshAxis.Y;u.log('APPROACH_IMPORT_BOUNDS '+str(extent)+' FORWARD '+str(axis))
 for act in actors:
  if act.get_actor_label().startswith('RP01_GradedEarthApproach_'):act.get_component_by_class(u.SplineMeshComponent).set_forward_axis(axis,True)
 t=u.AssetImportTask();t.filename=str(S/'Exports/RP01_FordStone.fbx');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
 opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;t.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);rock=u.load_asset(D+'/RP01_FordStone');stone=u.load_asset('/Game/Art/Buildings/Rural/RuralHouse01/M_RH01_Stone')
 stream=next(x for x in actors if x.get_actor_label()=='WaterBase_01_Tributary').get_water_spline();plane=u.load_asset('/Engine/BasicShapes/Plane');gravel=u.load_asset(D+'/M_RP01_FordBed')
 # Remove the regular rows of the initial placeholder stones.
 for act in actors:
  if act.get_actor_label().startswith('RP01_FordGravel_'):a.destroy_actor(act)
 actors=a.get_all_level_actors();ignore=[x for x in actors if x!=land]
 dx=.42;dy=.907524
 for i in range(20):
  s=-1000+i*100;ex=s+100;x=-23600+dx*s;y=-6300+dy*s;xx=-23600+dx*ex;yy=-6300+dy*ex
  z=max(height(x,y)+2,stream.find_location_closest_to_world_location(V(x,y,650),u.SplineCoordinateSpace.WORLD).z-4)
  zz=max(height(xx,yy)+2,stream.find_location_closest_to_world_location(V(xx,yy,650),u.SplineCoordinateSpace.WORLD).z-4)
  act=a.spawn_actor_from_class(u.SplineMeshActor,V(x,y,z));act.set_actor_label('RP01_SubmergedGravelBed_'+str(i));act.set_folder_path('RoadsPaths_01/ShallowFord_01');c=act.get_component_by_class(u.SplineMeshComponent);c.set_static_mesh(plane);c.set_material(0,gravel);delta=V(xx-x,yy-y,zz-z);c.set_start_and_end(V(0,0,0),delta,delta,delta,False);c.set_start_scale(u.Vector2D(4.4+.45*math.sin(i*.52),1),False);c.set_end_scale(u.Vector2D(4.4+.45*math.sin((i+1)*.52),1),True);c.set_cast_shadow(False);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
 rng=random.Random(91180)
 for i in range(112):
  along=rng.uniform(-950,950);side=rng.uniform(-235,235);x=-23600+dx*along-dy*side;y=-6300+dy*along+dx*side
  z=max(height(x,y),stream.find_location_closest_to_world_location(V(x,y,650),u.SplineCoordinateSpace.WORLD).z-3)
  size=rng.uniform(.1,.43);act=a.spawn_actor_from_class(u.StaticMeshActor,V(x,y,z),u.Rotator(yaw=rng.uniform(0,360)));act.set_actor_label('RP01_FordCobble_'+str(i));act.set_folder_path('RoadsPaths_01/ShallowFord_01');act.static_mesh_component.set_static_mesh(rock);act.static_mesh_component.set_material(0,stone);act.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);act.set_actor_scale3d(V(size,size*rng.uniform(.65,1.3),size*rng.uniform(.2,.4)))
 u.EditorAssetLibrary.save_directory(D);u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Art/Environment/TerrainBase01/TerrainBase_01');capture()
except:u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
