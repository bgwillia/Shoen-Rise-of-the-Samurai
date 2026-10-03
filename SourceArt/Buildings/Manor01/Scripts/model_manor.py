"""Manor01: a single authored exterior assembled from the existing SHŌEN kit."""
from pathlib import Path
import ast, math, random, sys, json
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]; OUT=ROOT/'artifacts/manor01'
OUT.mkdir(parents=True,exist_ok=True);(ART/'Exports').mkdir(parents=True,exist_ok=True)
random.seed(118056)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def coll(name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
src=coll('Manor_01 • editable local modules');layout=coll('Manor_01 • authored compound');studio=coll('Review only • not exported')
groups={};modules={};instances=[];mats={}
for blend,names in [('Smithy01',['SH01_Timber','SH01_Thatch','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope']),('Market01',['MK01_Cloth','MK01_Ink','MK01_Leaf','FC01_Dirt'])]:
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b):b.materials=names
 for m in b.materials:
  if m:mats[m.name.split('_',1)[1].split('.')[0]]=m
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash','panel'}),(ART.parent/'SmallShrine01/Scripts/model_shrine.py',{'fieldstone','block'}),(ART.parent/'Market01/Scripts/model_market.py',{'roof_patch'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'))
kit_beam=beam
kit_panel=panel
def beam(name,a,b,width,depth=None,mat='Timber',group='Frame',rough=.002):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat=='Timber':
  ox=random.random();oy=random.random()
  for v in ob.data.uv_layers.active.data:v.uv.x=v.uv.x*max(.22,width*3)+ox;v.uv.y=v.uv.y*.58+oy
 return ob
def panel(*args,**kw):
 ob=kit_panel(*args,**kw);s=ob.modifiers.new('Exterior plaster thickness','SOLIDIFY');s.thickness=.045;return ob
def before():return set(src.objects)
def collect(old,name):modules[name]=[o for o in src.objects if o not in old]
def append(blend,prefix,key):
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith(prefix)]
 obs=[]
 for ob in b.objects:
  if not ob or ob.type!='MESH':continue
  src.objects.link(ob);ob.parent=None;ob.hide_set(False);ob.hide_viewport=False;ob.hide_render=False
  ob.data=ob.data.copy();ob.matrix_world.identity()
  for slot in ob.material_slots:
   family=slot.material.name.split('_',1)[-1].split('.')[0] if slot.material else ''
   if family in mats:slot.material=mats[family]
  ob['reused_from']=blend+'/'+prefix;obs.append(ob)
 modules[key]=obs
 return obs

def cedar_roof(a,b,c,d,label,rows=5):
 a,b,c,d=map(Vector,(a,b,c,d))
 for row in range(rows):
  lo=row/rows;hi=min(1,(row+1.25)/rows);n=max(4,round((b.lerp(d,lo)-a.lerp(c,lo)).length/.22))
  for i in range(n):
   u=i/n;v=min(1,(i+1.025)/n);pp=[a.lerp(b,u).lerp(c.lerp(d,u),lo),a.lerp(b,v).lerp(c.lerp(d,v),lo),a.lerp(b,v).lerp(c.lerp(d,v),hi),a.lerp(b,u).lerp(c.lerp(d,u),hi)]
   for p in pp:p.z+=.022*(1-lo)+random.uniform(-.004,.004)
   ox=random.random();oy=random.random();ob=mesh(label+' overlapping cedar shingle',pp,[(0,1,2,3)],'Timber',[(ox,oy),(ox+.16,oy),(ox+.16,oy+.46),(ox,oy+.46)],label)
   so=ob.modifiers.new('Split cedar edge','SOLIDIFY');so.thickness=.025
 for t in [.06,.47,.87]:
  p=a.lerp(c,t)+Vector((0,0,.05));q=b.lerp(d,t)+Vector((0,0,.05))
  if (q-p).length>.02:tube(label+' straight roof batten',[p,q],.035,'Timber',label)

def wall_body(w,d,base,top,label):
 for y in [-d/2,d/2]:
  panel(label+' maintained plaster',(-w/2,y),(w/2,y),base+.48,top-.12)
  for x in [-w/2,-w/4,0,w/4,w/2]:beam(label+' selected timber upright',(x,y,base),(x,y,top),.18,group=label)
  for z in [base+.06,base+.58,top-.3,top]:beam(label+' continuous tie',(-w/2-.08,y,z),(w/2+.08,y,z),.13,.17,group=label)
  n=round(w/.19)
  for i in range(n):
   x=-w/2+(i+.5)*w/n;beam(label+' lower weatherboard',(x,y,base+.1),(x,y,base+.56),w/n-.005,.052,group=label)
 for x in [-w/2,w/2]:
  panel(label+' side plaster',(x,-d/2),(x,d/2),base+.16,top-.10)
  for y in [-d/2,0,d/2]:beam(label+' side post',(x,y,base),(x,y,top),.18,group=label)
  for z in [base+.12,base+.6,top-.3,top]:beam(label+' side tie',(x,-d/2-.08,z),(x,d/2+.08,z),.13,.14,group=label)
 # Opaque closed entrance and lattice shutters; empty nonplayable shell behind.
 for i in range(12):
  x=-.91+i*.165;beam(label+' closed entrance board',(x,-d/2-.055,base+.06),(x,-d/2-.055,top-.38),.160,.058,group=label)
 for x in [-1.04,0,1.04]:beam(label+' door jamb',(x,-d/2-.13,base),(x,-d/2-.13,top-.28),.12,.13,group=label)
 for z in [base+.10,top-.28]:beam(label+' entry head and sill',(-1.11,-d/2-.14,z),(1.11,-d/2-.14,z),.14,.17,group=label)
 for s in [-1,1]:
  for z in [base+.38,top-.58]:beam(label+' modest iron hinge',(s*.14,-d/2-.098,z),(s*.9,-d/2-.098,z),.043,.012,'Iron',label)
  tube(label+' ring pull',[(s*.18+.05*math.cos(i*math.tau/24),-d/2-.155,base+1.0+.055*math.sin(i*math.tau/24)) for i in range(25)],.008,'Iron',label,6)
 if w>6:
  for cx in [-3.1,3.1]:
   block('Dark opaque lattice backing',(cx,-d/2-.065,base+1.23),(1.32,.035,1.07),'Timber',label,.005)
   for z in [base+.67,base+1.79]:beam('Window sill',(cx-.73,-d/2-.13,z),(cx+.73,-d/2-.13,z),.08,.10,group=label)
   for i in range(13):beam('Fine straight window grille',(cx-.65+i*.108,-d/2-.15,base+.73),(cx-.65+i*.108,-d/2-.15,base+1.74),.028,.026,group=label)

# Broad raised main hall; front gable and a low roof skirt match the hero reference.
old=before();wall_body(9.3,5.6,.72,3.45,'MainHall');collect(old,'Manor_MainHall_01')
old=before()
for row in range(3):
 for y in [-2.8,2.8]:
  for i in range(23):fieldstone('Hall deliberate coursed stone',(-4.43+i*.403,y,.10+row*.17),(.22,.23,.115))
 for x in [-4.65,4.65]:
  for i in range(14):fieldstone('Hall return foundation',(x,-2.61+i*.40,.10+row*.17),(.23,.225,.115))
for y in [-2.8,2.8]:block('Hall long stone coping',(0,y,.58),(9.5,.44,.15),'Stone','StoneBase',.025)
for x in [-4.65,4.65]:block('Hall side stone coping',(x,0,.58),(.44,5.2,.15),'Stone','StoneBase',.025)
collect(old,'MN01_StoneBase')
old=before()
# Hipped lower skirt, steep plain front/rear gable above; no castle finials.
for a,b,c,d in [((-5.6,-3.7,3.58),(5.6,-3.7,3.58),(-3.95,-2.53,4.36),(3.95,-2.53,4.36)),((5.6,3.7,3.58),(-5.6,3.7,3.58),(3.95,2.53,4.36),(-3.95,2.53,4.36)),((-5.6,3.7,3.58),(-5.6,-3.7,3.58),(-3.95,2.53,4.36),(-3.95,-2.53,4.36)),((5.6,-3.7,3.58),(5.6,3.7,3.58),(3.95,-2.53,4.36),(3.95,2.53,4.36))]:
 roof_patch(a,b,c,d,'Main roof lower hip',5)
roof_patch((-4.12,2.80,4.32),(-4.12,-2.80,4.32),(0,2.80,6.0),(0,-2.80,6.0),'Main upper west',9)
roof_patch((4.12,-2.80,4.32),(4.12,2.80,4.32),(0,-2.80,6.0),(0,2.80,6.0),'Main upper east',9)
for y in [-2.73,2.73]:
 for i in range(42):
  x=-3.92+i*.191;top=5.95-abs(x)*.405
  beam('MN01 gable cedar infill',(x,y,4.30),(x,y,top),.186,.048,group='Gable')
 for s in [-1,1]:beam('MN01 dark gable verge',(s*4.17,y,4.31),(0,y,6.04),.135,.17,group='Gable')
 for z in [4.39,4.85]:
  half=(5.94-z)/.405;beam('MN01 front gable cross tie',(-half,y-.055,z),(half,y-.055,z),.12,.13,group='Gable')
 for x in [-2.25,0,2.25]:beam('MN01 gable framing',(x,y-.06,4.36),(x,y-.06,5.95-abs(x)*.405),.12,.13,group='Gable')
for x in [-.14,.14]:tube('MN01 restrained ridge timber',[(x,-3.08,6.07),(x,0,6.11),(x,3.08,6.07)],.065,'Timber','Ridge',9)
for y in [-2.88,-1.90,-.93,0,.93,1.90,2.88]:
 tube('MN01 pegged ridge crosspiece',[(-.37,y,6.14),(.37,y,6.14)],.036,'Timber','Ridge')
 for x in [-.14,.14]:lash('MN01 ridge binding',(x,y,6.10),'Y',.082,3)
for y in [-3.7,3.7]:beam('Main long eave fascia',(-5.65,y,3.43),(5.65,y,3.43),.13,.19,group='Roof')
for x in [-5.6,5.6]:beam('Main side eave fascia',(x,-3.74,3.43),(x,3.74,3.43),.14,.18,group='Roof')
collect(old,'MN01_MainRoof')
# Wraparound exterior walkway, visibly above the stone base.
old=before()
for i in range(55):
 x=-5.08+i*.188;beam('Manor veranda dressed plank',(x,-3.66,.73),(x,-2.79,.73),.182,.065,group='Veranda')
for x in [-5.10,5.10]:
 for i in range(35):
  y=-2.72+i*.18;beam('Side veranda dressed plank',(x-.41,y,.73),(x+.41,y,.73),.172,.065,group='Veranda')
for x in [-4.92,-3.15,-1.19,1.19,3.15,4.92]:
 fieldstone('Veranda stone pad',(x,-3.50,.19),(.23,.22,.20))
 beam('Formal porch upright',(x,-3.5,.28),(x,-3.5,3.33),.14,.15,group='Veranda')
 block('Porch bracket capital',(x,-3.5,3.24),(.36,.30,.12),group='Veranda',bevel=.012)
 for s in [-1,1]:beam('Porch bracket arm',(x,-3.5,2.97),(x+s*.30,-3.5,3.23),.074,.085,group='Veranda')
for z in [.64,3.24]:beam('Veranda full-width beam',(-5.22,-3.50,z),(5.22,-3.5,z),.15,.19,group='Veranda')
for a,b in [(-5.13,-1.28),(1.28,5.13)]:
 for z in [1.06,1.44]:beam('Restrained veranda railing',(a,-3.62,z),(b,-3.62,z),.06,.08,group='Veranda')
 n=round((b-a)/.56)
 for i in range(n+1):
  x=a+(b-a)*i/n;beam('Veranda railing post',(x,-3.62,.75),(x,-3.62,1.50),.064,group='Veranda')
for x in [-5.49,5.49]:
 for z in [1.06,1.44]:beam('Veranda side handrail',(x,-3.5,z),(x,2.8,z),.065,.08,group='Veranda')
 for i in range(11):beam('Veranda side baluster',(x,-3.4+i*.61,.75),(x,-3.4+i*.61,1.49),.064,group='Veranda')
collect(old,'MN01_Veranda')
old=before()
for j in range(4):
 for s in [-1,1]:block('Broad entrance stone tread',(s*.61,-4.61+j*.27,.09+j*.18),(1.20,.32,.18),'Stone','Steps',.025)
collect(old,'MN01_Steps')
# Modest side structure; lower roof and fewer bays keep hierarchy clear.
old=before();wall_body(3.1,3.7,.31,2.62,'SideBuilding')
for y in [-1.85,1.85]:
 for i in range(9):fieldstone('Side building low footing',(-1.48+i*.37,y,.13),(.21,.23,.17))
roof_patch((-2.03,-2.31,2.73),(2.03,-2.31,2.73),(-2.03,0,3.83),(2.03,0,3.83),'Side building front roof',7)
roof_patch((2.03,2.31,2.73),(-2.03,2.31,2.73),(2.03,0,3.83),(-2.03,0,3.83),'Side building back roof',7)
for x in [-1.57,1.57]:
 for i in range(21):
  y=-1.78+i*.178;beam('Side building gable board',(x,y,2.6),(x,y,3.79-abs(y)*.475),.06,.172,group='SideBuilding')
for y in [-.13,.13]:tube('Side building ridge',[(-2.18,y,3.93),(2.18,y,3.93)],.053,'Timber','SideBuilding')
for x in [-1.9,-.94,0,.94,1.9]:lash('Side building ridge tie',(x,0,3.92),'X',.19,3)
collect(old,'ManorSideBuilding_01')
# Roofed gate: stronger paired posts, cedar shingles, open leaves and quiet joinery.
old=before()
for x in [-1.72,1.72]:
 block('Gate stone shoe',(x,0,.17),(.52,.58,.34),'Stone','Gate',.045)
 beam('Gate squared primary post',(x,0,.24),(x,0,2.97),.28,.30,group='Gate')
 for s in [-1,1]:beam('Gate bracket shoulder',(x,0,2.39),(x+s*.43,0,2.89),.12,.14,group='Gate')
 for z in [.55,2.39]:block('Gate forged iron band',(x,-.157,z),(.295,.018,.09),'Iron','Gate',.004)
beam('Gate deep lintel',(-2.11,0,2.91),(2.11,0,2.91),.27,.29,group='Gate')
for s in [-1,1]:
 cedar_roof((-2.45,s*1.12,3.03),(2.45,s*1.12,3.03),(-2.45,0,3.68),(2.45,0,3.68),'GateRoof',5)
 beam('Gate dressed eave',(-2.5,s*1.12,2.96),(2.5,s*1.12,2.96),.12,.15,group='Gate')
 for x in [-2.12,-1.42,-.72,0,.72,1.42,2.12]:beam('Gate exposed rafter',(x,s*1.19,2.93),(x,0,3.61),.072,.11,group='Gate')
for x in [-2.12,2.12]:
 for s in [-1,1]:beam('Gate plain gable verge',(x,s*1.15,3.04),(x,0,3.71),.105,.13,group='Gate')
 beam('Gate gable tie',(x,-.94,3.08),(x,.94,3.08),.10,.15,group='Gate')
 beam('Gate gable king post',(x,0,3.07),(x,0,3.69),.10,group='Gate')
for y in [-.12,.12]:tube('Gate straight ridge cap',[(-2.61,y,3.76),(2.61,y,3.76)],.048,'Timber','Gate')
for x in [-2.27,-1.1,0,1.1,2.27]:
 tube('Gate ridge crosspiece',[(x,-.26,3.80),(x,.26,3.80)],.028,'Timber','Gate')
for x in [-1.72,1.72]:
 for i in range(9):beam('Gate open inward leaf',(x,.16+i*.15,.24),(x,.16+i*.15,2.58),.055,.146,group='Gate')
 for z in [.54,2.23]:beam('Gate leaf brace rail',(x-.035,.11,z),(x-.035,1.44,z),.084,.10,group='Gate')
 beam('Gate leaf diagonal',(x-.035,.13,.58),(x-.035,1.38,2.20),.08,group='Gate')
collect(old,'ManorGate_01')
# Deliberately straight privacy screens on a low two-course retaining base.
def fence(length=2.0,plaster=False):
 for row in range(2):
  for i in range(round(length/.40)):
   x=(i+.5)*length/round(length/.40)
   fieldstone('Wall deliberate fieldstone',(x,0,.12+row*.24),(.22,.29,.16))
 block('Wall weathered stone coping',(length/2,0,.54),(length+.025,.53,.13),'Stone','Wall',.025)
 for x in [0,length]:
  beam('Wall squared post',(x,0,.59),(x,0,2.01),.15,.17,group='Wall')
  block('Wall post weather cap',(x,0,2.05),(.22,.25,.07),group='Wall',bevel=.012)
 for z in [.68,1.79,1.98]:beam('Wall continuous cedar rail',(0,0,z),(length,0,z),.11,.16,group='Wall')
 if plaster:panel('Wall sheltered plaster',(0,.025),(length,.025),.73,1.84)
 else:
  n=round(length/.13)
  for i in range(n):
   x=(i+.5)*length/n;beam('Wall refined vertical paling',(x,0,.72),(x,0,1.90),.084,.052,group='Wall')
 cedar_roof((-.09,-.25,2.03),(length+.09,-.25,2.03),(-.09,0,2.17),(length+.09,0,2.17),'WallCap',2)
 cedar_roof((length+.09,.25,2.03),(-.09,.25,2.03),(length+.09,0,2.17),(-.09,0,2.17),'WallCap',2)
old=before();fence();collect(old,'ManorWall_Straight_01')
old=before();fence(2,True);collect(old,'ManorWall_Plaster_01')
old=before();fence(1);first=set(src.objects)-old
old2=before();fence(1)
for ob in set(src.objects)-old2:
 for v in ob.data.vertices:v.co=Vector((-v.co.y,v.co.x,v.co.z))
collect(old,'ManorWall_Corner_01')
# Reuse existing lantern mesh and temporary clan emblem/banner verbatim.
append('SmallShrine01','StoneLantern_01','StoneLantern_01')
# Shrine lantern's source coordinates include its original arrangement pivot.
for ob in modules['StoneLantern_01']:
 for v in ob.data.vertices:v.co-=Vector((-2.05,-1.90,0))
append('RetainerCompound01','RetainerBanner_01_RetainerBanner_01','MN01_Banners')
# Fine-tune source prefix if Blender's saved name is shorter.
if not modules['MN01_Banners']:append('RetainerCompound01','RetainerBanner_01','MN01_Banners')
sys.path.insert(0,str(ART/'Scripts'))
from manor_garden import build_garden
old=before();build_garden(globals());collect(old,'MN01_GardenElements')
# Packed-earth compound base and uncluttered approach. Reuses the farm dirt material.
old=before()
outline=[(-9.25,-7.30),(-4.0,-7.35),(-2.0,-8.6),(2.0,-8.6),(3.8,-7.30),(9.3,-7.30),(9.25,7.2),(-9.25,7.2)]
mesh('Maintained earth courtyard',[(0,0,.008)]+[(x,y,.008+random.uniform(-.003,.003)) for x,y in outline],[(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))],'Dirt',group='Ground')
for j in range(8):
 for s in [-1,1]:block('Quiet approach stepping stone',(s*.64,-6.65+j*.63,.055),(1.22,.51,.09),'Stone','Ground',.036)
collect(old,'MN01_GroundApron')

# Keep the main structural subassemblies editable, with ordinary local ground origins.
for key,obs in list(modules.items()):
 buckets={}
 for ob in obs:
  if not ob.get('reused_from'):
   co=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
   tone=random.uniform(.88,1.08)
   palette={'Timber':(.70,.62,.50),'Thatch':(.73,.64,.48),'Plaster':(1.01,.98,.90),'Stone':(.72,.74,.69),'Rope':(.82,.78,.66),'Cloth':(1.30,1.37,1.47),'Ink':(.18,.18,.18),'Iron':(.64,.67,.68),'Dirt':(.95,.93,.87),'Leaf':(.55,.68,.42)}
   for f in ob.data.polygons:
    family=ob.data.materials[f.material_index].name.split('_',1)[-1].split('.')[0]
    col=palette.get(family,(1,1,1))
    # Garden author supplies varied needle tint; keep it.
    if key=='MN01_GardenElements' and family=='Leaf':col=(.52,.67,.35)
    for li in f.loop_indices:co.data[li].color=(*(v*tone for v in col),1)
   ob.data.color_attributes.active_color=co
  cat='Stone' if all(m and 'Stone' in m.name for m in ob.data.materials) else 'Roof' if any(w in ob.name.lower() for w in ['roof','ridge','thatch','gable']) else 'Structure'
  buckets.setdefault(cat,[]).append(ob)
 joined=[]
 for cat,parts in buckets.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:
   ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=key+'_'+cat
  scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  joined.append(ob)
 modules[key]=joined
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for key,obs in modules.items():
 for o in obs:o.modifiers.new('Export triangles','TRIANGULATE')
 fbx(ART/'Exports'/(key+'.fbx'),obs)
 for o in obs:o.modifiers.remove(o.modifiers['Export triangles'])
def place(key,loc=(0,0,0),yaw=0,scale=(1,1,1),name=None):
 name=name or key+'_'+str(len(instances));instances.append({'name':name,'mesh':key,'location':list(loc),'rotation_degrees':yaw,'scale':list(scale)})
 for source in modules[key]:
  ob=source.copy();ob.data=source.data;layout.objects.link(ob);ob.name=name+' / '+source.name;ob.location=loc;ob.rotation_euler.z=math.radians(yaw);ob.scale=scale
for key in ['Manor_MainHall_01','MN01_MainRoof','MN01_StoneBase','MN01_Veranda','MN01_Steps']:place(key,(.35,2.8,0))
place('ManorGate_01',(0,-7,0));place('ManorSideBuilding_01',(-6.75,-.05,0),90)
for p,yaw in [((-9,-7,0),0),((9,-7,0),90),((9,7,0),180),((-9,7,0),270)]:place('ManorWall_Corner_01',p,yaw)
for x in [-8,-6,-4,2,4,6]:place('ManorWall_Plaster_01' if x in [-4,2] else 'ManorWall_Straight_01',(x,-7,0))
for x in [-8,-6,-4,-2,0,2,4,6]:place('ManorWall_Straight_01',(x,7,0))
for x in [-9,9]:
 for y in [-6,-4,-2,0,2,4]:place('ManorWall_Straight_01',(x,y,0),90)
place('MN01_GroundApron')
place('MN01_GardenElements',(-6.55,-4.05,0),24,(1,1,1))
place('MN01_GardenElements',(6.4,-1.6,0),-50,(1.12,1.12,1.08))
for x in [-2.65,2.65]:place('StoneLantern_01',(x,-7.45,0),0,(1,1,1))
for x in [-6.6,7.2]:place('MN01_Banners',(x,3.6,0),0,(1.12,1.12,1.66))
for x in [-1.95,1.95]:place('MN01_Banners',(x,-7.3,0),0,(.84,.84,.9))
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'Manor_01','units':'metres','instances':instances},indent=2)+'\n')
# A full-compound placement mesh complements, rather than replaces, the reusable pieces.
for o in layout.objects:o.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/Manor_01.fbx',list(layout.objects))
for o in layout.objects:o.modifiers.remove(o.modifiers['Export triangles'])
src.hide_render=True;src.hide_viewport=True
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review earth only'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground);ground.location.z=-.025
gm=bpy.data.materials.new('Review neutral earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.13,.14,.10,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Manor rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.46,.56,.74,1);world.node_tree.nodes['Background'].inputs[1].default_value=.46
for name,loc,power,size in [('Warm daylight',(-8,-12,15),1900,9),('Courtyard fill',(5,-10,10),1000,9)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Rural afternoon sun','SUN');o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.50,-.45,-.6);d.energy=2.7;d.angle=.055;d.color=(1,.94,.83)
cd=bpy.data.cameras.new('Manor three quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(23,-35,15.2);cam.rotation_euler=(Vector((0,0,1.85))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=48;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');scene['asset_note']='Manor_01: one modest authored rural exterior, reused SHŌEN kit, no interiors or gameplay.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Manor01.blend'))
print('MANOR_SAVED',len(modules),'modules',len(instances),'instances',flush=True)
scene.render.filepath=str(OUT/'manor-three-quarter.png');bpy.ops.render.render(write_still=True)
print('MANOR_COMPLETE',flush=True)
