"""User-directed art revision: reference roof, gate, natural stone and garden finish."""
from pathlib import Path
import ast,sys,math,random,json
import bpy,bmesh
from mathutils import Vector,Matrix
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/manor01'
bpy.ops.wm.open_mainfile(filepath=str(ART/'Manor01.blend'))
scene=bpy.context.scene;src=bpy.data.collections['Manor_01 • editable local modules'];layout=bpy.data.collections['Manor_01 • authored compound'];studio=bpy.data.collections['Review only • not exported']
src.hide_render=False;src.hide_viewport=False
random.seed(118058);groups={};mats={}
for ob in src.objects:
 for m in ob.data.materials:
  if m:mats[m.name.split('_',1)[-1].split('.')[0]]=m
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash'}),(ART.parent/'SmallShrine01/Scripts/model_shrine.py',{'block'}),(ART.parent/'Storehouse01/Scripts/refine_reference_match.py',{'fieldstone'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'))
kit_beam=beam
def beam(name,a,b,width,depth=None,mat='Timber',group='Frame',rough=.003):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat=='Timber':
  ox=random.random();oy=random.random()
  for uv in ob.data.uv_layers.active.data:uv.uv.x=uv.uv.x*max(.22,width*3)+ox;uv.uv.y=uv.uv.y*.58+oy
 return ob
def before():return set(src.objects)
def tint(ob,palette=None):
 if ob.get('preserve_authored_color'):return
 palette=palette or {'Timber':(.34,.27,.19),'Thatch':(.68,.57,.40),'Stone':(.80,.82,.77),'Plaster':(1.12,1.06,.93),'Iron':(.5,.5,.5),'Rope':(.69,.62,.46),'Cloth':(1.25,1.30,1.35),'Ink':(.2,.2,.2),'Leaf':(.42,.60,.28),'Dirt':(.75,.75,.65)}
 co=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 k=random.uniform(.83,1.12)
 for f in ob.data.polygons:
  fam=ob.data.materials[f.material_index].name.split('_',1)[-1].split('.')[0]
  for li in f.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   damp=.83+.17*min(1,max(0,p.z)/.6)
   rgb=palette.get(fam,(1,1,1))
   co.data[li].color=(*(v*k*(damp if fam in ('Timber','Stone') else 1) for v in rgb),1)
 ob.data.color_attributes.active_color=co
keys=list(dict.fromkeys(i['mesh'] for i in json.loads((ART/'Exports/assembly.json').read_text())['instances']))
modules={key:[o for o in src.objects if o.name.startswith(key+'_')] for key in keys}
for ob in list(layout.objects):bpy.data.objects.remove(ob,do_unlink=True)
def remove(key,cat=None):
 for ob in list(modules[key]):
  if cat is None or ob.name.endswith('_'+cat):
   modules[key].remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
def finish_new(key,old):
 new=[o for o in src.objects if o not in old]
 for ob in new:tint(ob)
 buckets={}
 for ob in new:
  category='Stone' if all('Stone' in m.name for m in ob.data.materials) else 'Structure'
  buckets.setdefault(category,[]).append(ob)
 for category,parts in buckets.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:
   ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=key+'_'+category
  scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();modules[key].append(ob)
print('REFINE_START',flush=True)
# Stronger contrast between selected dark structural wood and maintained clay plaster.
for key in ['Manor_MainHall_01','ManorSideBuilding_01','MN01_Veranda','ManorGate_01','ManorWall_Straight_01','ManorWall_Corner_01','ManorWall_Plaster_01']:
 for ob in modules[key]:
  if ob.name.endswith('_Stone'):continue
  if ob.name.endswith('_Roof'):continue
  tint(ob)
# Replace the repeated squared masonry with bedded irregular fieldstone.
def stone_run(a,b):
 a,b=Vector((*a,0)),Vector((*b,0));v=b-a;n=Vector((-v.y,v.x,0)).normalized();t=v.normalized();length=v.length
 for row in range(2):
  x=0
  while x<length-.03:
   step=min(random.uniform(.37,.58),length-x);p=a+t*(x+step/2)+Vector((0,0,.15+row*.25+random.uniform(-.025,.025)))
   old=before();fieldstone('Bedded irregular retaining stone',p,(step*.59,.30+random.uniform(-.025,.025),.18+random.uniform(-.03,.025)))
   for ob in set(src.objects)-old:
    for vv in ob.data.vertices:
     q=vv.co-p;vv.co=p+t*q.x+n*q.y+Vector((0,0,q.z))
   x+=step
for key in ['ManorWall_Straight_01','ManorWall_Corner_01','ManorWall_Plaster_01']:
 remove(key,'Stone');old=before()
 if key=='ManorWall_Corner_01':stone_run((0,0),(1,0));stone_run((0,0),(0,1))
 else:stone_run((0,0),(2,0))
 finish_new(key,old)
# Restore a few broader worn capstones and varied body footing stones under the hall.
remove('MN01_StoneBase');old=before()
for a,b in [((-4.65,-2.8),(4.65,-2.8)),((-4.65,2.8),(4.65,2.8)),((-4.65,-2.8),(-4.65,2.8)),((4.65,-2.8),(4.65,2.8))]:stone_run(a,b)
for y in [-2.8,2.8]:
 for i in range(12):
  fieldstone('Broad worn foundation cap',(-4.32+i*.79,y,.575),(.43,.28,.085))
finish_new('MN01_StoneBase',old)
# Replace main and gate roofing with the same individually laid cedar/bark treatment.
sys.path.insert(0,str(ART/'Scripts'))
from manor_roof_refined import build_roof,roof_patch
remove('MN01_MainRoof');old=before();build_roof(globals());finish_new('MN01_MainRoof',old)
remove('ManorGate_01','Roof');old=before()
roof_patch(globals(),(-2.52,-1.15,3.03),(2.52,-1.15,3.03),(-2.52,0,3.72),(2.52,0,3.72),'Gate roof south',rows=5)
roof_patch(globals(),(2.52,1.15,3.03),(-2.52,1.15,3.03),(2.52,0,3.72),(-2.52,0,3.72),'Gate roof north',rows=5)
for y in [-.14,.14]:tube('Gate heavy dressed ridge',[(-2.69,y,3.77),(0,y,3.81),(2.69,y,3.77)],.063,'Timber','GateDetail',10)
for x in [-2.4,-1.2,0,1.2,2.4]:
 tube('Gate pegged ridge retaining bar',[(x,-.33,3.84),(x,.33,3.84)],.037,'Timber','GateDetail')
 for y in [-.14,.14]:lash('Gate hemp ridge tie',(x,y,3.81),'X',.078,3)
# Deeper capital stacks, carved bracket shoulders, exposed ends and pegs.
for x in [-1.72,1.72]:
 for z,width,depth in [(2.69,.39,.43),(2.84,.58,.49),(2.96,.77,.55)]:block('Gate layered bracket block',(x,0,z),(width,depth,.135),group='GateDetail',bevel=.018)
 for s in [-1,1]:
  outline=[(0,2.48),(.16,2.58),(.35,2.72),(.57,2.78),(.62,2.91),(0,2.91)]
  vv=[(x+s*xx,yy,zz) for yy in [-.19,.19] for xx,zz in outline];n=len(outline)
  ob=mesh('Gate curved carved shoulder',vv,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],'Timber',group='GateDetail')
  mod=ob.modifiers.new('Softened bracket arrises','BEVEL');mod.width=.014;mod.segments=3
 for z in [.47,.61,2.28,2.48,2.86]:tube('Gate dark timber pegs',[(x,-.17,z),(x,-.21,z)],.019,'Timber','GateDetail',10)
 for z in [.55,2.39]:
  for xx in [-.09,.09]:tube('Gate iron strap rivet',[(x+xx,-.17,z),(x+xx,-.185,z)],.012,'Iron','GateDetail',8)
# Two broad short crest curtains. Reuse the existing banner's linen, folds and emblem geometry.
for s in [-1,1]:
 for banner in modules['MN01_Banners']:
  ob=banner.copy();ob.data=banner.data.copy();src.objects.link(ob);ob.name='Gate short crest curtain'
  bm=bmesh.new();bm.from_mesh(ob.data)
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if not any(k in ob.data.materials[f.material_index].name for k in ['Cloth','Ink'])],context='FACES')
  bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
  bm.to_mesh(ob.data);bm.free()
  if not len(ob.data.vertices):bpy.data.objects.remove(ob,do_unlink=True);continue
  ink=set()
  for face in ob.data.polygons:
   if 'Ink' in ob.data.materials[face.material_index].name:ink.update(face.vertices)
  for v in ob.data.vertices:
   if v.index in ink:v.co=Vector((s*.77+v.co.x*1.33,-.21+v.co.y*.4,(v.co.z-2.205)*1.33+2.40))
   else:v.co=Vector((s*.77+v.co.x*2.15,-.20+v.co.y*.55,(v.co.z-2.735)*.48+2.79))
  ob['preserve_authored_color']=True
finish_new('ManorGate_01',old)
print('REFINE_ROOF_GATE_STONE_READY',flush=True)
# Denser three-dimensional pine needle sprays, with natural irregular rocks.
from manor_garden_refined import build_garden
remove('MN01_GardenElements');old=before();build_garden(globals())
for ob in set(src.objects)-old:ob['preserve_authored_color']=True
finish_new('MN01_GardenElements',old)
# Break the perfect earth-disc edge and add restrained natural contact with the site.
remove('MN01_GroundApron');old=before()
outline=[]
for i in range(15):outline.append((-9.25+18.5*i/14,-7.33+random.uniform(-.10,.08)))
for i in range(1,12):outline.append((9.24+random.uniform(-.10,.08),-7.3+14.55*i/11))
for i in range(1,15):outline.append((9.25-18.5*i/14,7.25+random.uniform(-.10,.08)))
for i in range(1,11):outline.append((-9.25+random.uniform(-.10,.08),7.25-14.55*i/11))
mesh('Maintained compound packed earth',[(0,0,.009)]+[(x,y,.009) for x,y in outline],[(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))],'Dirt',uv=[(0,0)]+[(x*.35,y*.35) for x,y in outline],group='Ground')
# Approach has softly ragged shoulders and an irregular stepping-stone rhythm.
mesh('Earth approach apron',[(-2.4,-7.25,.01),(-2.32,-8.4,.007),(-1.92,-9.0,.003),(2.0,-9.1,.003),(2.45,-8.35,.007),(2.3,-7.25,.01)],[(0,1,2,3,4,5)],'Dirt',group='Ground')
for i in range(8):
 x=random.uniform(-.27,.27);y=-8.45+i*.74
 fieldstone('Worn approach paving',(x,y,.035),(.90+random.uniform(-.09,.15),.43+random.uniform(-.04,.04),.055))
# Gravel and grass concentrate at enclosure feet; the quiet center stays clear.
for i in range(250):
 if i%3==0:x=random.choice([-1,1])*random.uniform(8.85,9.65);y=random.uniform(-7.5,7.35)
 else:x=random.uniform(-9.3,9.3);y=-7.35+random.uniform(-.32,.14)
 if abs(x)<2.25 and y<0:continue
 radius=random.uniform(.018,.065)
 if i%4==0:fieldstone('Ground contact pebble',(x,y,.015),(radius*1.2,radius,radius*.55))
 if i%2==0:
  vv=[];ff=[]
  for j in range(random.randint(5,10)):
   a=random.random()*math.tau;h=random.uniform(.06,.24);w=random.uniform(.006,.012);cx=x+random.uniform(-.05,.05);cy=y+random.uniform(-.05,.05);dx=math.cos(a);dy=math.sin(a);k=len(vv)
   vv += [(cx-dy*w,cy+dx*w,0),(cx+dy*w,cy-dx*w,0),(cx+dx*h*.2-dy*w*.6,cy+dy*h*.2+dx*w*.6,h*.7),(cx+dx*h*.2+dy*w*.6,cy+dy*h*.2-dx*w*.6,h*.7),(cx+dx*h*.7,cy+dy*h*.7,h)]
   ff += [(k,k+1,k+3,k+2),(k+2,k+3,k+4)]
  mesh('Sparse grass at stone foot',vv,ff,'Leaf',group='Ground')
finish_new('MN01_GroundApron',old)
print('REFINE_GARDEN_GROUND_READY',flush=True)
# Re-export the same useful modules, then rebuild the authored arrangement once.
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for key,obs in modules.items():
 for ob in obs:ob.modifiers.new('Export triangles','TRIANGULATE')
 fbx(ART/'Exports'/(key+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangles'])
assembly=json.loads((ART/'Exports/assembly.json').read_text())
assembly['instances']=[i for i in assembly['instances'] if not(i['mesh']=='MN01_Banners' and i['location'][1]<0)]
for item in assembly['instances']:
 for source in modules[item['mesh']]:
  ob=source.copy();ob.data=source.data;layout.objects.link(ob);ob.name=item['name']+' / '+source.name;ob.location=item['location'];ob.rotation_euler.z=math.radians(item.get('rotation_degrees',0));ob.scale=item.get('scale',[1,1,1])
(ART/'Exports/assembly.json').write_text(json.dumps(assembly,indent=2)+'\n')
for ob in layout.objects:ob.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/Manor_01.fbx',list(layout.objects))
for ob in layout.objects:ob.modifiers.remove(ob.modifiers['Export triangles'])
src.hide_render=True;src.hide_viewport=True
# Lower hero angle puts emphasis on the entrance composition and the broad roof.
scene.camera.location=(23,-40,10.8);scene.camera.rotation_euler=(Vector((0,0,2.35))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=56
scene.render.resolution_x=1900;scene.render.resolution_y=1200;scene.cycles.samples=48
# Clear daylight with warm key light and soft blue sky fill, like the reference.
for ob in studio.objects:
 if ob.type=='LIGHT' and ob.data.type=='SUN':ob.rotation_euler=(.68,-.4,-.55);ob.data.energy=3.0;ob.data.color=(1,.88,.72);ob.data.angle=.065
 if ob.type=='LIGHT' and ob.data.type=='AREA':ob.data.energy*=1.2
world=scene.world;world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.56,.78,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Manor01.blend'))
print('REFINED_MANOR_SAVED',flush=True)
scene.render.filepath=str(OUT/'manor-three-quarter.png');bpy.ops.render.render(write_still=True)
print('REFINED_MANOR_COMPLETE',flush=True)
