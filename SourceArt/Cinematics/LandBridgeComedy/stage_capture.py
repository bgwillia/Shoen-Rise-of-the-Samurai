import unreal as u,math,json,time
from pathlib import Path
es=u.get_editor_subsystem(u.EditorActorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);V=u.Vector
anim=u.load_asset('/Game/Cinematics/LandBridgeComedy/A_Manny_BridgeComedy')
for a in es.get_all_level_actors():
 if a.get_actor_label().startswith('CineComedy_'):es.destroy_actor(a)
assets=['/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple','/Game/Art/Characters/Samurai/Do01/SK_Do01','/Game/Art/Characters/Samurai/Kusazuri01/SK_Kusazuri01','/Game/Art/Characters/Samurai/Sode01/SK_Sode_L_01','/Game/Art/Characters/Samurai/Sode01/SK_Sode_R_01','/Game/Art/Characters/Samurai/Kote01/SK_Kote_L_01','/Game/Art/Characters/Samurai/Kote01/SK_Kote_R_01','/Game/Art/Characters/Samurai/Suneate01/SK_Suneate_L_01','/Game/Art/Characters/Samurai/Suneate01/SK_Suneate_R_01']
actors=[];comps=[]
for i,path in enumerate(assets):
 a=es.spawn_actor_from_class(u.SkeletalMeshActor,V(-23600,-6300,680));a.set_actor_label('CineComedy_'+str(i));a.set_folder_path('Cinematics/TemporaryComedy')
 c=a.get_component_by_class(u.SkeletalMeshComponent);c.set_skeletal_mesh_asset(u.load_asset(path));c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE);c.set_animation(anim);c.set_update_animation_in_editor(True);c.stop()
 actors.append(a);comps.append(c)
helmet=es.spawn_actor_from_class(u.StaticMeshActor,V(-23600,-6300,850));helmet.set_actor_label('CineComedy_Helmet');helmet.get_component_by_class(u.StaticMeshComponent).set_static_mesh(u.load_asset('/Game/Art/Characters/Samurai/Kabuto01/SM_Kabuto01'))
actors.append(helmet)
ref=json.loads(Path('/private/tmp/cine-native-poses.json').read_text())['ref_head'];refhead=u.Transform(location=V(*ref[0]),rotation=u.Quat(*ref[1]).rotator())
helmetRef=u.Transform(location=V(0,2.5,159.8));helmetRel=u.MathLibrary.make_relative_transform(helmetRef,refhead)
world=ed.get_editor_world()
def ground(x,y):
 h=u.SystemLibrary.line_trace_single(world,V(x,y,1600),V(x,y,200),u.TraceTypeQuery.ECC_VISIBILITY,True,actors,u.DrawDebugTrace.NONE,True)
 return h.to_tuple()[5].z if h and h.to_tuple()[0] else 654
heights=[]
for i in range(141):
 t=i/30;d=min(t,4.1)*100+max(0,min(t-4.1,.6))*100*(1-max(0,min((t-4.1)/.6,1))*.5)
 x=-23600+.42*(d-425);y=-6300+.907524*(d-425);heights.append(ground(x,y))
base=heights[-1]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def setframe(frame):
 t=frame/30
 # Integrated eased walking speed, then fixed centre for the performance.
 tt=max(0,min((t-4.1)/.6,1));d=min(t,4.1)*100+60*(tt-tt*tt*.5)
 x=-23600+.42*(d-440);y=-6300+.907524*(d-440)
 yaw=-math.degrees(math.asin(.42))-28*smooth((t-5.1)/1.1)
 z=heights[min(140,round(min(t,4.666)*30))]+.5
 for a,c in zip(actors,comps):
  a.set_actor_location(V(x,y,z),False,False);a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False);c.set_position(t,False)
 # Use evaluated head pose so attachment does not lag the manually sampled frame.
 opt=u.AnimPoseEvaluationOptions();opt.optional_skeletal_mesh=comps[0].skeletal_mesh
 pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opt);head=u.AnimPoseExtensions.get_bone_pose(pose,'head',u.AnimPoseSpaces.WORLD)
 hw=u.MathLibrary.compose_transforms(head,actors[0].get_actor_transform());ht=u.MathLibrary.compose_transforms(helmetRel,hw)
 helmet.set_actor_transform(ht,False,False)
loc=V(-22780,-6040,base+310);target=V(-23660,-6430,base+95)
le.eject_pilot_level_actor();le.editor_set_game_view(True);le.editor_set_viewport_realtime(True)
ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,target));le.set_level_viewport_fov(48,le.get_active_viewport_config_key())
setframe(240)
Path('/private/tmp/cine-stage-ready.txt').write_text(str(heights))
