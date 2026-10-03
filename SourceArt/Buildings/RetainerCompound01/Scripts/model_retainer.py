"""One authored RetainerCompound01 exterior, assembled from the SHŌEN rural kit."""
from pathlib import Path
import ast, math, random, sys, json
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils import noise

ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'; OUT=ROOT/'artifacts/retainercompound01'
OUT.mkdir(parents=True,exist_ok=True); (ART/'Exports').mkdir(parents=True,exist_ok=True)
random.seed(118047)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=1900; scene.render.resolution_y=1350; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
def coll(name):
 c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
src=coll('RetainerCompound_01 • editable module library')
layout=coll('RetainerCompound_01 • authored exterior assembly')
studio=coll('Review only • ground and lighting')
groups={}; modules={}; instances=[]; mats={}
for blend,names in [('Smithy01',['SH01_Timber','SH01_Thatch','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope','SM01_Ember','SM01_Charcoal']),('Market01',['MK01_Cloth','MK01_Ink','FC01_Dirt'])]:
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b): b.materials=names
 for m in b.materials:
  if m: mats[m.name.split('_',1)[1].split('.')[0]]=m
for file,names in [(KIT/'Scripts/model_house.py',{'mesh','beam','tube','lash','stone','panel'}),(ART.parent/'Storehouse01/Scripts/refine_reference_match.py',{'fieldstone'}),(ART.parent/'FarmCompound01/Scripts/model_farm.py',{'plank_roof'}),(ART.parent/'Market01/Scripts/model_market.py',{'roof_patch'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'))
kit_beam=beam
stone=fieldstone
kit_panel=panel
def panel(*args,**kwargs):
 ob=kit_panel(*args,**kwargs); mod=ob.modifiers.new('Exterior wattle thickness','SOLIDIFY'); mod.thickness=.04; return ob
def beam(name,a,b,width,depth=None,mat='Timber',group='Frame',rough=.004):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat=='Timber':
  ox=random.random(); oy=random.random()
  for v in ob.data.uv_layers.active.data: v.uv.x=v.uv.x*max(.22,width*3)+ox; v.uv.y=v.uv.y*.58+oy
 return ob
def peg(name,p,axis=(0,-1,0),radius=.015):
 p=Vector(p);return tube(name,[p,p+Vector(axis)*.025],radius,'Timber','Joinery',8)
def before(): return set(src.objects)
def collect(old,name): modules[name]=[o for o in src.objects if o not in old]
def remap(ob):
 for slot in ob.material_slots:
  if slot.material:
   family=slot.material.name.split('_',1)[-1].split('.')[0]
   if family in mats:slot.material=mats[family]
def append_objects(blend,names,scale=(1,1,1),shift=(0,0,0)):
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b):b.objects=names
 for ob in b.objects:
  if not ob:continue
  src.objects.link(ob); ob.hide_set(False); ob.hide_viewport=False; ob.hide_render=False
  ob.parent=None; ob.matrix_world.identity(); ob.data=ob.data.copy(); remap(ob)
  for v in ob.data.vertices:v.co=Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))+Vector(shift)
  ob['reused_from']=blend+' / '+ob.name
 return [o for o in b.objects if o]
def append_collection(blend,name):
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b):b.collections=[name]
 collection=b.collections[0]; obs=list(collection.all_objects)
 for ob in obs:
  for c in list(ob.users_collection):c.objects.unlink(ob)
  src.objects.link(ob); ob.hide_set(False); ob.hide_viewport=False; ob.hide_render=False
  ob.parent=None; ob.matrix_world.identity(); remap(ob)
 bpy.data.collections.remove(collection)
 return obs

# Broader, orderly hall. The original smithy's roof, joinery and stonework are reused.
old=before()
append_objects('Smithy01',['SM01_Frame','SM01_Foundations'],(1.20,1.05,1.04))
roof_patch((-3.42,-2.13,2.63),(3.42,-2.13,2.63),(-3.42,0,4.02),(3.42,0,4.02),'Main south thatch',10)
roof_patch((3.42,2.13,2.63),(-3.42,2.13,2.63),(3.42,0,4.02),(-3.42,0,4.02),'Main north thatch',10)
for y in [-.16,.16]:tube('Main roof weathered ridge restraint',[(-3.60,y,4.105),(-1.7,y,4.135),(0,y,4.13),(1.7,y,4.135),(3.60,y,4.105)],.061,'Timber','Ridge',9)
tube('Main roof bound straw ridge',[(-3.48,0,4.02),(0,0,4.055),(3.48,0,4.02)],.12,'Thatch','Ridge',12)
for x in [-3.2,-2.4,-1.5,-.6,.5,1.45,2.35,3.16]:
 tube('Crossed ridge peg',[(x,-.34,4.16),(x,.34,4.16)],.034,'Timber','Ridge',8)
 for y in [-.16,.16]:lash('Main ridge hemp knot',(x,y,4.13),'X',.085,3)
# Small raised roof vent gives the reference's distinctive roofline.
for x in [-.83,.83]:
 for y in [-.48,.48]:beam('Ridge vent corner',(x,y,3.85),(x,y,4.21),.07,group='RoofVent')
for y in [-.48,.48]:
 for z in [3.96,4.20]:beam('Vent louvre frame',(-.90,y,z),(.90,y,z),.074,group='RoofVent')
 for i in range(18):beam('Dark open vent grille',(-.82+i*.096,y,3.99),(-.82+i*.096,y,4.18),.027,group='RoofVent')
roof_patch((-1.03,-.72,4.22),(1.03,-.72,4.22),(-1.03,0,4.57),(1.03,0,4.57),'Ridge vent front',4)
roof_patch((1.03,.72,4.22),(-1.03,.72,4.22),(1.03,0,4.57),(-1.03,0,4.57),'Ridge vent rear',4)
tube('Vent ridge timber',[(-1.16,0,4.61),(1.16,0,4.61)],.055,'Timber','RoofVent')
for y in [-1.575,1.575]:
 for z in [.31,.98,2.42]:beam('Hall horizontal wall tie',(-2.84,y,z),(2.84,y,z),.12,.11)
 for i in range(33):
  x=-2.72+i*.17
  if y<0 and abs(x)<.68:continue
  beam('Hall lower weatherboard',(x,y,.30),(x,y,1.04),.166,.055,group='HallWalls')
 if y>0:panel('Hall rear wattle',(-2.82,y),(2.82,y),1.05,2.40)
 else:
  for a,b in [(-2.82,-.68),(.68,2.82)]:panel('Hall front wattle',(a,y),(b,y),1.05,2.40)
for x in [-2.82,2.82]:
 panel('Hall side wattle',(x,-1.57),(x,1.57),.3,2.42)
 for y in [-1.575,0,1.575]:beam('Hall side upright',(x,y,.28),(x,y,2.5),.18)
 for z in [.33,1.0,2.42]:beam('Hall side weather rail',(x,-1.64,z),(x,1.64,z),.11)
 for i in range(21):
  y=-1.575+i*.1575; top=3.88-abs(y)*.68
  beam('Retainer gable board',(x,y,2.50),(x,y,top),.055,.153,group='Gable')
for x in [-.7,.7]:beam('Hall entrance jamb',(x,-1.65,.25),(x,-1.65,2.40),.17)
for i in range(9):
 x=-.61+i*.153
 beam('Closed retainer hall door',(x,-1.62,.31),(x,-1.62,2.28),.15,.05,group='Door')
for s in [-1,1]:
 for z in [.63,1.90]:beam('Simple forged door strap',(s*.07,-1.66,z),(s*.57,-1.66,z),.045,.013,'Iron','Door')
 tube('Door ring pull',[(s*.15+.046*math.cos(i*math.tau/24),-1.70,1.28+.05*math.sin(i*math.tau/24)) for i in range(25)],.008,'Iron','Door',6)
for cx in [-1.75,1.75]:
 for i in range(7):beam('Closed dark lattice backing',(cx-.45+i*.15,-1.606,1.24),(cx-.45+i*.15,-1.606,2.12),.146,.04,group='Window')
 for z in [1.22,2.15]:beam('Lattice sill',(cx-.57,-1.68,z),(cx+.57,-1.68,z),.085)
 for i in range(9):beam('Window grille',(cx-.48+i*.12,-1.70,1.25),(cx-.48+i*.12,-1.70,2.12),.028,rough=.001)
# Covered exterior veranda, without interior floor or furnishing.
for i in range(34):
 x=-2.83+i*.172
 beam('Veranda weathered board',(x,-2.22,.28),(x,-1.57,.28),.169,.045,group='Porch')
for x in [-2.74,-.79,.79,2.74]:
 stone('Veranda bedded footing',(x,-2.13,.09),(.17,.19,.10))
 beam('Veranda post',(x,-2.13,.15),(x,-2.13,2.17),.13,group='Porch')
 for s in [-1,1]:beam('Veranda knee brace',(x,-2.13,1.85),(x+s*.25,-2.13,2.12),.062,group='Porch')
 for z in [.32,2.10]:peg('Hall visible pegged mortise',(x,-2.206,z))
 lash('Porch post roof binding',(x,-2.13,2.10),'X',.092,3)
beam('Long veranda eave',(-3,-2.18,2.16),(3,-2.18,2.16),.15,.15,group='Porch')
for i in range(38):
 x=-3.04+i*.164
 beam('Shallow porch roof board',(x,-2.40,2.18),(x,-1.25,2.64),.162,.036,group='PorchRoof')
for y,z in [(-2.28,2.265),(-1.58,2.545)]:tube('Porch roof retaining pole',[(-3.12,y,z),(3.12,y,z)],.038,'Timber','PorchRoof')
for x in [-2.75,-2.10,-1.40,-.7,0,.7,1.4,2.1,2.75]:
 beam('Veranda exposed rafter',(x,-2.52,2.13),(x,-1.31,2.62),.074,.085,group='PorchRoof')
 for y,z in [(-2.25,2.29),(-1.6,2.55)]:lash('Porch roof tie',(x,y,z),'X',.054,2)
for j in range(2):beam('Broad hall entrance step',(-.78,-2.56+j*.19,.10+j*.09),(.78,-2.56+j*.19,.10+j*.09),.22,.09,group='Porch')
collect(old,'RetainerCompound_01')

# Practical roofed gate. The open panels follow the inside of the fence.
old=before()
for x in [-1.47,1.47]:
 stone('Gate broad stone socket',(x,0,.10),(.27,.25,.13))
 beam('Gate heavy timber post',(x,0,.13),(x,0,2.73),.26,.27,group='Gate')
 for y in [-.12,.12]:beam('Gate post iron foot',(x,y,.29),(x,y,.53),.27,.021,'Iron','Gate')
 for s in [-1,1]:beam('Gate shoulder brace',(x,0,2.15),(x+s*.43,0,2.64),.13,group='Gate')
beam('Gate broad lintel',(-1.84,0,2.63),(1.84,0,2.63),.26,.28,group='Gate')
roof_patch((-1.98,-.88,2.78),(1.98,-.88,2.78),(-1.98,0,3.31),(1.98,0,3.31),'Gate front thatch',6)
roof_patch((1.98,.88,2.78),(-1.98,.88,2.78),(1.98,0,3.31),(-1.98,0,3.31),'Gate rear thatch',6)
for y in [-.115,.115]:tube('Gate ridge restraint',[(-2.12,y,3.40),(0,y,3.42),(2.12,y,3.40)],.047,'Timber','GateRoof',9)
for x in [-1.75,-.85,0,.85,1.75]:
 tube('Gate ridge retaining crosspiece',[(x,-.28,3.44),(x,.28,3.44)],.028,'Timber','GateRoof')
 for y in [-.115,.115]:lash('Gate ridge lash',(x,y,3.40),'X',.066,3)
for x in [-1.48,1.48]:
 for s in [-1,1]:beam('Gate end rafter',(x,s*.91,2.73),(x,0,3.30),.11,.13,group='GateRoof')
 beam('Gate gable tie',(x,-.76,2.78),(x,.76,2.78),.13,group='GateRoof')
 beam('Gate king stud',(x,0,2.79),(x,0,3.32),.11,group='GateRoof')
 for z in [.54,2.13,2.65]:peg('Gate tenon peg',(x,-.145,z),radius=.022)
 lash('Heavy gate lintel tie',(x,0,2.62),'X',.165,4)
for x in [-1.72,-1.1,-.56,0,.56,1.1,1.72]:
 for s in [-1,1]:beam('Gate short eave rafter',(x,s*.96,2.59),(x,s*.52,2.84),.068,.094,group='GateRoof')
for x in [-1.47,1.47]:
 for j in range(7):
  y=.13+j*.156;beam('Open gate panel board',(x,y,.20),(x,y,2.19),.055,.15,group='GatePanels')
 for z in [.50,1.85]:beam('Gate panel rail',(x-.025,.09,z),(x-.025,1.16,z),.085,group='GatePanels')
 beam('Gate diagonal panel brace',(x-.032,.11,.42),(x-.032,1.14,1.97),.08,group='GatePanels')
collect(old,'RetainerGate_01')

def fence(a,b,label,end_post=True):
 a,b=Vector((*a,0)),Vector((*b,0));v=b-a;length=v.length;t=v.normalized();normal=Vector((-t.y,t.x,0))
 for p in [a,b] if end_post else [a]:
  stone('Fence stone footing',p+Vector((0,0,.075)),(.13,.13,.10))
  beam('Palisade stout post',p+Vector((0,0,.11)),p+Vector((0,0,1.68)),.14,group=label)
 for z in [.45,1.22]:beam('Palisade continuous back rail',a+normal*.065+Vector((0,0,z)),b+normal*.065+Vector((0,0,z)),.074,.09,group=label)
 for i in range(round(length/.28)):
  p=a+v*((i+.5)/round(length/.28))
  stone('Low coursed palisade fieldstone',p+Vector((0,0,.105)),(.16,.15,.13))
 count=round(length/.17)
 for i in range(count):
  p=a+v*((i+.5)/count);h=1.48+random.uniform(-.10,.15)
  ob=beam('Rough split timber paling',p+Vector((0,0,.19)),p+Vector((random.uniform(-.013,.013),0,h)),.14+random.uniform(-.017,.017),.061,group=label,rough=.008)
  # The module can turn the corner without turning its boards into square bars.
  if abs(t.y)>.5:
   for vv in ob.data.vertices:
    q=vv.co-p;vv.co=p+Vector((-q.y,q.x,q.z))
  for vv in ob.data.vertices:
   if vv.co.z>h-.015:vv.co.z+=random.uniform(-.026,.055)
  for z in [.45,1.22]:
   q=p-normal*.038+Vector((0,0,z));peg('Palisade weathered nail',q,-normal,.008)
  for j in range(2):
   xx=random.uniform(-.045,.045);zz=random.uniform(.38,1.22);hh=random.uniform(.10,.36)
   points=[p+t*(xx-.002)-normal*.035+Vector((0,0,zz)),p+t*(xx-.004)-normal*.036+Vector((0,0,zz+hh*.45)),p+t*(xx+.001)-normal*.035+Vector((0,0,zz+hh)),p+t*(xx+.002)-normal*.036+Vector((0,0,zz+hh*.45))]
   mesh('Fine split in pale timber',points,[(0,1,2,3)],'Ink',group=label)
 for p in [a,b]:
  for z in [.45,1.22]:lash('Palisade rope fastening',p+Vector((0,0,z)),'X',.10,2)
old=before();fence((0,0),(2,0),'Fence');collect(old,'RetainerFence_Straight_01')
old=before();fence((0,0),(1,0),'Corner',False);fence((0,0),(0,1),'Corner',False);collect(old,'RetainerFence_Corner_01')

# Small observation tower: open braced base, closed half-wall below its lookout.
old=before()
for x in [-.78,.78]:
 for y in [-.78,.78]:
  stone('Tower pad stone',(x,y,.12),(.23,.25,.15))
  beam('Tower continuous main support',(x*1.12,y*1.12,.22),(x,y,4.79),.195,group='TowerFrame')
for z in [.4,2.25,3.40]:
 for x in [-.82,.82]:beam('Tower cross frame',(x,-.9,z),(x,.9,z),.15,group='TowerFrame')
 for y in [-.82,.82]:beam('Tower cross frame',(-.9,y,z),(.9,y,z),.15,group='TowerFrame')
for y in [-.82,.82]:
 beam('Tower lower diagonal',(-.85,y,.45),(.8,y,2.24),.125,group='TowerFrame')
 beam('Tower return diagonal',(.85,y,.45),(-.8,y,2.24),.125,group='TowerFrame')
for x in [-.82,.82]:beam('Tower side diagonal',(x,-.85,.45),(x,.80,2.24),.12,group='TowerFrame')
for y in [-.83,.83]:
 for i in range(12):beam('Tower upper protective boarding',(-.77+i*.14,y,2.30),(-.77+i*.14,y,3.37),.135,.045,group='TowerWalls')
for x in [-.83,.83]:
 for i in range(12):beam('Tower upper side boarding',(x,-.77+i*.14,2.30),(x,-.77+i*.14,3.37),.045,.135,group='TowerWalls')
for i in range(14):beam('Lookout deck plank',(-1.03,-.98+i*.151,3.48),(1.03,-.98+i*.151,3.48),.148,.062,group='TowerPlatform')
for x in [-.99,.99]:
 for y in [-.99,0,.99]:beam('Lookout railing upright',(x,y,3.46),(x,y,4.27),.075,group='TowerRails')
 for z in [3.79,4.22]:beam('Lookout side rail',(x,-1.08,z),(x,1.08,z),.078,group='TowerRails')
for y in [-.99,.99]:
 for z in [3.79,4.22]:beam('Lookout front rail',(-1.08,y,z),(1.08,y,z),.078,group='TowerRails')
for x in [-.99,.99]:
 for y in [-.99,.99]:
  for z in [3.79,4.22]:lash('Lookout railing rope joint',(x,y,z),'X',.057,3)
for x in [-.78,.78]:
 for z in [.43,2.25,3.4,4.74]:
  for y in [-.83,.83]:peg('Tower frame tenon',(x,y,z),axis=(0,-1 if y<0 else 1,0),radius=.018)
for y in [-.78,.78]:beam('Tower roof plate',(-.95,y,4.73),(.95,y,4.73),.16,group='TowerFrame')
for x in [-.78,.78]:
 beam('Tower roof tie',(x,-.94,4.73),(x,.94,4.73),.14,group='TowerFrame')
 for s in [-1,1]:beam('Lookout small knee',(x,s*.78,4.37),(x,s*.46,4.72),.075,group='TowerFrame')
# Four shallow hipped timber slopes, like the rural kit's split-board sheds.
for a,b,c,d in [((-1.30,-1.30,4.86),(1.30,-1.30,4.86),(-.55,0,5.48),(.55,0,5.48)),((1.30,1.30,4.86),(-1.30,1.30,4.86),(.55,0,5.48),(-.55,0,5.48)),((-1.30,1.30,4.86),(-1.30,-1.30,4.86),(-.55,0,5.48),(-.55,0,5.48)),((1.30,-1.30,4.86),(1.30,1.30,4.86),(.55,0,5.48),(.55,0,5.48))]:
 a,b,c,d=map(Vector,(a,b,c,d))
 for row in range(5):
  lo=row/5;hi=min(1,(row+1.28)/5);n=max(4,round((b.lerp(d,lo)-a.lerp(c,lo)).length/.17))
  for i in range(n):
   u=i/n;v=(i+1.025)/n;pts=[a.lerp(b,u).lerp(c.lerp(d,u),lo),a.lerp(b,v).lerp(c.lerp(d,v),lo),a.lerp(b,v).lerp(c.lerp(d,v),hi),a.lerp(b,u).lerp(c.lerp(d,u),hi)]
   for p in pts:p.z+=.018*(1-lo)+random.uniform(-.007,.007)
   ox=random.random();oy=random.random()
   ob=mesh('Overlapping split cedar roof shingle',pts,[(0,1,2,3)],'Timber',[(ox,oy),(ox+.11,oy),(ox+.11,oy+.5),(ox,oy+.5)],'TowerRoof');m=ob.modifiers.new('Board edge thickness','SOLIDIFY');m.thickness=.025
 for v in [.08,.50,.87]:
  p=a.lerp(c,v)+Vector((0,0,.055));q=b.lerp(d,v)+Vector((0,0,.055))
  if (q-p).length>.05:tube('Tower shingle retaining batten',[p,q],.023,'Timber','TowerRoof')
tube('Tower ridge cap',[(-.71,0,5.53),(.71,0,5.53)],.058,'Timber','TowerRoof')
for s in [-1,1]:
 for i in range(8):
  t=-1.10+i*.315
  beam('Exposed tower eave rafter',(t,s*1.34,4.76),(t,s*.59,5.06),.052,.075,group='TowerRoof')
  beam('Exposed tower side rafter',(s*1.34,t,4.76),(s*.64,t*.48,5.12),.052,.075,group='TowerRoof')
for x in [-.53,0,.53]:lash('Tower ridge binding',(x,0,5.52),'X',.07,3)
for x in [-.32,.32]:
 beam('Tower access ladder stile',(x,1.40,.08),(x,.47,3.50),.064,group='TowerLadder')
for i in range(12):
 t=(i+1)/13;beam('Tower ladder rung',(-.34,1.40-.93*t,.08+3.42*t),(.34,1.40-.93*t,.08+3.42*t),.046,group='TowerLadder')
collect(old,'Watchtower_01')

# Reuse a small farm shed; no new building type or furnishings.
old=before();append_collection('FarmCompound01','FC01_ToolShed');collect(old,'RC01_LeanTo')
old=before();append_objects('Market01',['MK01_Crate']);collect(old,'RC01_Crate')
old=before();append_collection('FarmCompound01','FC01_Cart');collect(old,'RC01_Cart')
old=before();append_collection('FarmCompound01','FC01_GroundApron')
for ob in list(src.objects):
 if ob not in old:
  if 'Packed earth compound apron' in ob.name:
   bpy.data.objects.remove(ob,do_unlink=True);continue
  for v in ob.data.vertices:v.co.y*=1.38
collect(old,'RC01_GroundApron')
# Packed training space and a short worn entrance path, edged with occasional stones.
old=before()
for label,cx,cy,w,d in [('Training yard',0,0,12.7,10.25),('Gate approach',0,-5.0,3.15,4.1)]:
 verts=[];uv=[];faces=[];nx=100 if label=='Training yard' else 42;ny=90 if label=='Training yard' else 50
 for j in range(ny+1):
  for i in range(nx+1):
   u=i/nx;v=j/ny;x=cx+(u-.5)*w;y=cy+(v-.5)*d
   edge=min(u,1-u,v,1-v);fade=min(1,edge*18)
   x+=(.065*math.sin(y*3.6)+.035*math.sin(y*14.2))*(abs(u-.5)*2)**5
   y+=(.10*math.sin(x*5.6)+.040*math.sin(x*18.2))*(abs(v-.5)*2)**5
   if label=='Gate approach':x*=.69+.31*v
   p=Vector((x*1.5,y*1.5,0));z=-.021+fade*(.022+.025*noise.noise_vector(p)[0]+.009*noise.noise_vector(p*12)[1])
   if label=='Gate approach':z-=.009
   z=max(.015,z+.036)
   verts.append((x,y,z));uv.append((x,y))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
 ob=mesh(label+' packed dirt',verts,faces,'Dirt',uv,'Ground')
 colors=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for face in ob.data.polygons:
  face.use_smooth=True
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   variation=.88+.14*noise.noise_vector(p*3)[0]+.10*noise.noise_vector(p*31)[1]
   colors.data[li].color=(variation,variation*.98,variation*.91,1)
 ob.data.color_attributes.active_color=colors
for i in range(240):
 x=random.uniform(-6.2,6.2);y=random.uniform(-5.3,4.8)
 if abs(x)<1.5 and y>-.2:continue
 if random.random()<.6 and abs(x)<4.8 and abs(y)<3.6:continue
 rr=random.uniform(.013,.057);stone('Scattered yard aggregate',(x,y,rr*.12),(rr,rr*random.uniform(.6,1.2),rr*.33))
for i in range(70):
 x=random.choice([-1,1])*random.uniform(1.12,1.67);y=random.uniform(-6.95,-4.7);rr=random.uniform(.025,.075)
 stone('Gateway worn verge stone',(x,y,rr*.09),(rr,rr*.74,rr*.37))
modules['RC01_GroundApron'].extend([o for o in src.objects if o not in old])
# Existing earth and rural stone grain, varied by the authored ground vertices.
earth=mats['Dirt']; nodes=earth.node_tree.nodes;links=earth.node_tree.links;p=nodes['Principled BSDF']
previous=p.inputs['Base Color'].links[0].from_socket
vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='Color'
mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;links.new(previous,mul.inputs[1]);links.new(vc.outputs['Color'],mul.inputs[2]);links.new(mul.outputs[0],p.inputs['Base Color'])

sys.path.insert(0,str(ART/'Scripts'))
from retainer_props import build_props
modules.update(build_props(globals()))

# Preserve construction groups within large modules, with separate local source pivots.
for name,obs in list(modules.items()):
 buckets={}
 for o in obs:
  if name not in ('RC01_Cart','RC01_GroundApron','RC01_Crate'):
   colors=o.data.color_attributes.get('Color') or o.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
   wood_board=any(w in o.name.lower() for w in ['board','paling','shingle','door','lattice','grille'])
   tone=random.uniform(.79,1.16) if wood_board else random.uniform(.91,1.08)
   palette={'Timber':(.78,.74,.65) if wood_board else (.39,.31,.23),'Thatch':(.67,.57,.41),'Stone':(.66,.68,.62),'Plaster':(.85,.84,.78),'Rope':(.74,.69,.54),'Cloth':(1.25,1.34,1.50),'Ink':(.18,.18,.18),'Iron':(.62,.65,.65),'Ember':(1,1,1),'Charcoal':(1,1,1)}
   for f in o.data.polygons:
    family=o.data.materials[f.material_index].name.split('_',1)[-1].split('.')[0]
    if family not in palette:continue
    for li in f.loop_indices:colors.data[li].color=(*(v*tone for v in palette[family]),1)
   o.data.color_attributes.active_color=colors
  if name in ('RetainerCompound_01','Watchtower_01'):
   cat='Roof' if 'roof' in o.name.lower() or 'ridge' in o.name.lower() or any(m and 'Thatch' in m.name for m in o.data.materials) else 'Stone' if all(m and 'Stone' in m.name for m in o.data.materials) else 'Structure'
  elif name=='ArmorStand_01':cat='Armor' if o.get('reused_armor') or any(m and ('Atlas' in m.name or 'Kabuto' in m.name or 'Do01' in m.name) for m in o.data.materials) else 'Stand'
  else:cat=name
  buckets.setdefault(cat,[]).append(o)
 joined=[]
 for cat,parts in buckets.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:
   ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):
    if mod.type=='ARMATURE':ob.modifiers.remove(mod)
    else:bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object
  ob.name=(('RC01_MainBuilding' if name=='RetainerCompound_01' else name)+'_'+cat)
  scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  joined.append(ob)
 modules[name]=joined
for name,obs in modules.items():
 if name in ('RC01_Cart','RC01_GroundApron','RC01_Crate'):continue
 for ob in obs:
  tint=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
  for face in ob.data.polygons:
   mat=ob.data.materials[face.material_index]; family=mat.name.split('_',1)[-1].split('.')[0]
   if family not in ('Timber','Thatch','Stone','Plaster','Rope','Cloth','Iron','Ink','Ember','Charcoal'):continue
   for li in face.loop_indices:
    p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.94+.035*math.sin(p.x*7+p.y*3+p.z*4)+.025*math.sin(p.x*25+p.z*31)
    if family=='Timber':k*=.72+.28*min(1,max(0,p.z)/.6)
    rgb=tint.data[li].color[:3];tint.data[li].color=(*(c*k for c in rgb),1)
  ob.data.color_attributes.active_color=tint
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for name,obs in modules.items():
 for ob in obs:ob.modifiers.new('Export triangles','TRIANGULATE')
 fbx(ART/'Exports'/(name+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangles'])
def place(key,loc=(0,0,0),yaw=0,scale=(1,1,1),name=None):
 name=name or key+'_'+str(len(instances));instances.append({'name':name,'mesh':key,'location':list(loc),'rotation_degrees':yaw,'scale':list(scale)})
 for source in modules[key]:
  ob=source.copy();ob.data=source.data;layout.objects.link(ob);ob.name=name+' / '+source.name
  ob.location=loc;ob.rotation_euler.z=math.radians(yaw);ob.scale=scale
place('RC01_GroundApron',(0,0,-.014))
place('RetainerCompound_01',(-1.70,2.35,0),name='Main retainer hall')
place('RetainerGate_01',(0,-4.75,0),name='Compound entry')
place('Watchtower_01',(4.37,1.60,0),name='Small observation tower')
place('RC01_LeanTo',(-4.55,-1.2,0),90,name='Exterior equipment shelter')
# Corner modules terminate each adjoining run; all intermediate fence pieces share one mesh.
for p,r in [((-6,-4.75,0),0),((6,-4.75,0),90),((6,4.75,0),180),((-6,4.75,0),270)]:place('RetainerFence_Corner_01',p,r)
for x,length in [(-5,2),(-3,1.45),(1.55,1.45),(3,2)]:place('RetainerFence_Straight_01',(x,-4.75,0),scale=(length/2,1,1))
for x in [-5,-3,-1,1,3]:place('RetainerFence_Straight_01',(x,4.75,0))
for x in [-6,6]:
 for y in [-3.75,-1.875,0,1.875]:place('RetainerFence_Straight_01',(x,y,0),90,(.9375,1,1))
for x in [-1.97,1.97]:place('RetainerBanner_01',(x,-5.65,0),name='Gate clan banner '+str(x))
place('RetainerBanner_01',(5.02,.44,2.00),0,(.82,.82,.90),name='Tower clan banner')
place('TrainingDummy_01',(1.15,-.90,0),-8)
place('TrainingDummy_01',(2.62,-.70,0),8)
place('WeaponRack_01',(4.50,-2.80,0),-12)
place('WeaponRack_01',(-3.20,.09,.29),0,(.85,.85,.85))
place('ArmorStand_01',(-.65,.05,.29),0)
for x in [-1.91,1.91]:place('Brazier_01',(x,-6.21,0),0,(.9,.9,.9))
for p,r in [((3.83,-3.95,0),3),((4.60,-3.97,0),-5),((-5.00,-2.40,0),90)]:place('RC01_Crate',p,r)
place('RC01_Crate',(4.59,-3.96,.49),2)
place('RC01_Cart',(4.36,3.55,0),90,(.80,.80,.80))
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'RetainerCompound_01','units':'metres','instances':instances},indent=2)+'\n')
src.hide_render=True;src.hide_viewport=True
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review earth only'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground);ground.location.z=-.035
gm=bpy.data.materials.new('Review neutral earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.115,.112,.087,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.40,.52,.74,1);world.node_tree.nodes['Background'].inputs[1].default_value=.36
for name,loc,power,size in [('Warm sky',(-6,-8,12),1200,8),('Yard fill',(3,-5,8),500,7)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Afternoon sun','SUN');o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.58,-.48,-.55);d.energy=3.0;d.angle=.065;d.color=(1,.93,.82)
cd=bpy.data.cameras.new('Compound three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(12,-22,8.1);cam.rotation_euler=(Vector((0,-.3,1.95))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=49;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='RetainerCompound_01: one authored modular exterior; rural kit, existing armor and weapons reused; no interior or gameplay.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'RetainerCompound01.blend'))
print('RETAINER_SAVED',len(modules),'modules',len(instances),'instances',flush=True)
scene.render.filepath=str(OUT/'retainer-three-quarter.png');bpy.ops.render.render(write_still=True)
print('RETAINER_COMPLETE',flush=True)
