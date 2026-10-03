import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/RiverGravel01';es=u.get_editor_subsystem(u.EditorActorSubsystem);aa=es.get_all_level_actors();bank=next(a for a in aa if a.get_actor_label()=='RiverGravel01_ContinuousBank');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();bc=bank.static_mesh_component
bc.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY);bc.set_collision_profile_name('BlockAll');ignore=[a for a in aa if a!=bank]
def height(x,y):
 h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,20000),u.Vector(x,y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple()
 return h[5].z if h[0] else None
stones=[]
for a in aa:
 label=a.get_actor_label()
 if not (label.startswith('RP01_FordCobble_') or label.startswith('RiverGravel01_EmbeddedFragment_') or label in ['RiverRock_01','RiverRock_02','RiverRock_03']):continue
 p=a.get_actor_location();s=(p.x+23600)*.42+(p.y+6300)*.907524
 if not 600<abs(s)<1100:continue
 h=height(p.x,p.y)
 if h is None:continue
 center,ext=a.get_actor_bounds(False)
 if abs(center.z-ext.z-h)<12:stones.append((a,p,h))
t=u.AssetImportTask();t.filename=str(R/'SourceArt/Environment/Ground/RiverGravel01/Exports/RiverGravel01_FlushApproaches.fbx');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE;t.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);mesh=u.load_asset(D+'/RiverGravel01_FlushApproaches');bc.set_static_mesh(mesh)
for a,p,h in stones:
 new=height(p.x,p.y)
 if new is not None:a.set_actor_location(p+u.Vector(0,0,new-h),False,False)
bc.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
# Capture the same connection and context for direct visual comparison.
out=R/'artifacts/landbridge-road50/leveled-gravel';out.mkdir(exist_ok=True)
s=(R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_landbridge_road50.py').read_text().replace('artifacts/landbridge-road50','artifacts/landbridge-road50/leveled-gravel')
exec(s,{'__name__':'__main__'})
