import unreal as u,json,math
from pathlib import Path
es=u.get_editor_subsystem(u.EditorActorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);V=u.Vector
actors=es.get_all_level_actors();grass=sorted([a for a in actors if a.get_actor_label().startswith('VillageRoad40_Grass_')],key=lambda a:a.get_actor_label())
assert len(grass)==30
short=[a for a in grass if 'Medium' not in a.get_component_by_class(u.StaticMeshComponent).static_mesh.get_path_name()]
tall=[a for a in grass if 'Medium' in a.get_component_by_class(u.StaticMeshComponent).static_mesh.get_path_name()]
segments=json.loads(Path('/private/tmp/village-road-built.json').read_text())['segments']
ignore=[a for a in actors if not isinstance(a,u.Landscape)]
world=ed.get_editor_world()
def at(s,offset):
 for a,b,start,length in segments:
  if s<=start+length:
   t=max(0,min(1,(s-start)/length));dx=(b[0]-a[0])/length;dy=(b[1]-a[1])/length
   return a[0]+(b[0]-a[0])*t-dy*offset,a[1]+(b[1]-a[1])*t+dx*offset
 raise RuntimeError('Outside section')
def height(x,y):
 hit=u.SystemLibrary.line_trace_single(world,V(x,y,5000),V(x,y,-2000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True)
 assert hit is not None
 h=hit.to_tuple();assert h[0];return h[5].z
shapes=[[(0,15),(-45,-10),(36,-22),(-82,8),(74,0),(-26,51),(27,63),(66,48),(-65,64),(106,32),(-103,42)],[(0,25),(-39,-4),(28,-18),(61,12),(-73,23),(-22,61),(35,70),(89,52)],[(0,18),(-32,-16),(43,-5),(-71,15),(79,31),(-21,62),(23,52),(-58,76),(62,87),(113,59),(-103,53)]]
records=[];centers=[]
for gi,(station,side) in enumerate([(1920,255),(3200,-275),(4550,265)]):
 group=[tall[gi]]+[short.pop(0) for _ in range(len(shapes[gi])-1)]
 for j,(a,(ds,do)) in enumerate(zip(group,shapes[gi])):
  offset=side+(do if side>0 else -do);x,y=at(station+ds,offset);z=height(x,y)
  yaw=(gi*83+j*137.507+19)%360
  rootDepth=1.4+.2*((gi+j)%4)
  c=a.get_component_by_class(u.StaticMeshComponent);minz=c.get_local_bounds()[0].z*a.get_actor_scale3d().z
  a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False)
  a.set_actor_location(V(x,y,z-rootDepth-minz),False,False)
  records.append({'label':a.get_actor_label(),'group':gi,'ground':z,'lowestRoot':z-rootDepth,'yaw':yaw,'pitch':a.get_actor_rotation().pitch,'roll':a.get_actor_rotation().roll,'offset':offset})
  if j==0:centers.append([x,y,z])
le.save_current_level()
Path('/private/tmp/grass-regroup-result.json').write_text(json.dumps({'plants':records,'centers':centers}))
