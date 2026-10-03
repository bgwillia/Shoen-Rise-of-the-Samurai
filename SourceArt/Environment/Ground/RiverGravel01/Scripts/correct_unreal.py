import unreal as u,math
from pathlib import Path
es=u.get_editor_subsystem(u.EditorActorSubsystem);actors=es.get_all_level_actors();V=u.Vector;L=u.MaterialEditingLibrary;D='/Game/Art/Environment/Ground/RiverGravel01';mat=u.load_asset(D+'/M_RiverGravel_01');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
# Apply to the existing raised ford ribbon as well as the landscape below it.
ribbons=[]
for a in actors:
 if a.get_actor_label().startswith('RP01_SubmergedGravelBed_'):
  origin,extent=a.get_actor_bounds(False)
  if abs(origin.x+23530)<extent.x+600 and abs(origin.y+6610)<extent.y+500:
   c=a.get_component_by_class(u.SplineMeshComponent);c.set_material(0,mat);ribbons.append((a,c))
 if a.get_actor_label() in ['WaterBase_01_Tributary','WaterBase_01_MainRiver']:
  a.set_is_temporarily_hidden_in_editor(False)
land=next(a for a in actors if isinstance(a,u.Landscape));ignore=[a for a in actors if a!=land]
def gh(x,y):
 h=u.SystemLibrary.line_trace_single(world,V(x,y,20000),V(x,y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple()[5].z
 for a,c in ribbons:
  p=a.get_actor_location()+c.get_start_position();q=a.get_actor_location()+c.get_end_position();dx=q.x-p.x;dy=q.y-p.y;t=max(0,min(1,((x-p.x)*dx+(y-p.y)*dy)/(dx*dx+dy*dy)))
  dist=math.hypot(x-p.x-t*dx,y-p.y-t*dy)
  if dist<min(c.get_start_scale().x,c.get_end_scale().x)*49:h=max(h,p.z+t*(q.z-p.z))
 return h
for a in actors:
 if a.get_actor_label().startswith('RiverGravel01_EmbeddedFragment_'):
  p=a.get_actor_location();a.set_actor_location(V(p.x,p.y,gh(p.x,p.y)-1.0),False,False)
# Dry swatch kept clear of the water, while the bank remains in its real setting.
patch=next(a for a in actors if a.get_actor_label()=='RiverGravel_01_1mReviewPatch');px,py=-23360,-6870;ph=gh(px,py)+1.5;patch.set_actor_location(V(px,py,ph),False,False)
rock=next(a for a in actors if a.get_actor_label()=='RiverRock_01');rp=rock.get_actor_location();target=rp+V(35,0,14)
views=[('01-overhead-1m',V(px,py,ph),V(0,0,137)),('02-low-oblique',V(px,py,ph),V(25,-112,53)),('03-close-detail',V(px-25,py+10,ph),V(15,-57,48)),('04-rocks-embedded',target,V(65,-245,135)),('05-dry-damp-shoreline',target,V(250,-420,280)),('06-strategy',target,V(1100,-1600,1800)),('07-larger-area',target,V(250,-950,1120))]
for name,target,off in views:
 cam=next(a for a in actors if a.get_actor_label()=='RiverGravel01_'+name);cam.set_actor_location(target+off,False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/tmp/gravel-correction.txt').write_text(str([(a.get_actor_label(),str(a.get_actor_location())) for a,c in ribbons])+'\npatch '+str(patch.get_actor_location()))
exec(open('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/Ground/RiverGravel01/Scripts/capture_unreal.py').read())
