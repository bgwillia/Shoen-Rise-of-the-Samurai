"""One authored LumberCharcoal01 art pass, assembled from the existing rural kit."""
from pathlib import Path
import ast, json, math, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix

ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
FARM=ART.parent/'FarmCompound01'; SMITHY=ART.parent/'Smithy01'
OUT=ROOT/'artifacts/lumbercharcoal01'; OUT.mkdir(parents=True,exist_ok=True)
random.seed(1180916)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.render.resolution_x=2000;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
src=bpy.data.collections.new('LumberCharcoal_01 • modular exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • lighting and ground');scene.collection.children.link(studio)
groups={};modules={};instances=[]
with bpy.data.libraries.load(str(FARM/'FarmCompound01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope','SM01_Water','FC01_Dirt']]
 b.collections=['FC01_WaterTrough','FC01_Baskets','FC01_HayBundles','FC01_Fence_Straight']
mats={m.name.split('_',1)[1]:m for m in b.materials}
kit_collections={c.name:c for c in b.collections}
with bpy.data.libraries.load(str(SMITHY/'Smithy01.blend'),link=False) as (a,b):
 b.materials=['SM01_Charcoal']
 b.objects=[n for n in a.objects if n in ['SM01_Roof','SM01_RoofBundles','SM01_RoofEaves','SM01_RoofGableThatch','SM01_Ridge','SM01_RidgeLashings']]
roof_objects=list(b.objects)
mats['Charcoal']=b.materials[0]
# Use the same mesh-authoring helpers and export settings as FarmCompound01.
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash','panel'}),
                   (ART.parent/'Storehouse01/Scripts/refine_reference_match.py',{'fieldstone'}),
                   (FARM/'Scripts/model_farm.py',{'plank_roof','tint'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:
   exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
def start():return set(o.name for o in src.objects)
def finish(before,key):modules.setdefault(key,[]).extend(o for o in src.objects if o.name not in before)
def clone_objects(originals,key,scale=(1,1,1),shift=(0,0,0),rotation=0):
 result=[];mat=Matrix.Translation(Vector(shift))@Matrix.Rotation(math.radians(rotation),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in originals:
  ob=original.copy();ob.data=original.data.copy();ob.matrix_world=Matrix.Identity(4)
  ob.name='LC01_'+key+' • '+original.name;src.objects.link(ob)
  for v in ob.data.vertices:v.co=mat@v.co
  # Existing materials may have been appended along with geometry; share the rural originals.
  for i,m in enumerate(ob.data.materials):
   name=m.name.split('.')[0];family=name.split('_',1)[1] if '_' in name else ''
   if family in mats:ob.data.materials[i]=mats[family]
  ob['reused_from']='FarmCompound01 / Smithy01 rural kit';result.append(ob)
 return result
def kit(key):return list(kit_collections['FC01_'+key].objects)

# Broad open lumber shed; the Smithy thatch is reused without its enclosed forge shell.
modules['Roof']=clone_objects(roof_objects,'Roof',(1.18,1.03,1.03))
for ob in modules['Roof']:
 for v in ob.data.vertices:
  p=v.co;p.z+=.028*math.sin(p.x*3.4+p.y*2.1)+.019*math.sin(p.x*7.6-p.y*1.7)
 ob['roof_weathering']=True
before=start()
for x in [-2.8,-.92,.92,2.8]:
 for y in [-1.55,1.55]:
  fieldstone('Shed bedded footing',(x,y,.09),(.22,.24,.13))
  beam('Shed hewn post',(x,y,.17),(x,y,2.55),.20,.21,group='MainShed')
  for sign in [-1,1]:
   if abs(x+sign*.43)<2.9:beam('Shed knee brace',(x,y,2.02),(x+sign*.43,y,2.50),.10,.11,group='MainShed')
for y in [-1.55,1.55]:beam('Long eave plate',(-3,y,2.49),(3,y,2.49),.22,.23,group='MainShed')
for x in [-2.8,-.92,.92,2.8]:
 beam('Open gable tie',(x,-1.78,2.51),(x,1.78,2.51),.17,.19,group='MainShed')
 beam('Ridge king post',(x,0,2.51),(x,0,3.90),.14,group='MainShed')
 for side in [-1,1]:
  beam('Principal rafter',(x,side*2.05,2.54),(x,0,3.90),.14,.15,group='MainShed')
  beam('Gable diagonal',(x,side*1.25,2.52),(x,0,3.60),.095,group='MainShed')
for i in range(35):
 x=-2.72+i*.16
 beam('Rear partial weatherboard',(x,1.54,.24),(x,1.54,1.80+random.uniform(-.05,.05)),.151,.045,group='MainShed')
for z in [.32,1.05,1.81]:beam('Rear wall rail',(-2.91,1.51,z),(2.91,1.51,z),.11,.09,group='MainShed')
finish(before,'MainShed')
# A low open plank lean-to tucks against the right-hand gable.
before=start()
for y in [-1.2,1.35]:
 for x,h in [(-.8,2.43),(.8,1.96)]:
  fieldstone('Lean-to footing',(x,y,.07),(.17,.18,.1))
  beam('Lean-to upright',(x,y,.12),(x,y,h),.13,.14,group='LeanTo')
 beam('Lean-to sloped bearer',(-.98,y,2.47),(.99,y,1.93),.12,.14,group='LeanTo')
for x,h in [(-.8,2.43),(.8,1.96)]:beam('Lean-to long plate',(x,-1.38,h),(x,1.55,h),.14,.15,group='LeanTo')
for i in range(19):
 y=-1.48+i*.174
 beam('Lean-to rough overlapping roof plank',(-1.0,y,2.53),(1.03,y,1.97),.181,.049,group='LeanTo',rough=.004)
for x in [-.86,0,.88]:beam('Lean-to roof retainer',(x,-1.55,2.57-(x+1)*.276),(x,1.72,2.57-(x+1)*.276),.056,.045,group='LeanTo')
finish(before,'LeanTo')
# Primitive earthen charcoal kiln, with a real dark recessed mouth and low soot vent.
before=start();n=64;rows=20;vv=[];ff=[]
for j in range(rows+1):
 t=j/rows*math.pi/2;rr=1.39*math.cos(t);z=.04+1.48*math.sin(t)
 for i in range(n):
  a=i/n*math.tau;w=1+.045*math.sin(a*7+t*4)+.025*math.sin(a*17-t*11)
  vv.append((rr*math.cos(a)*w,rr*math.sin(a)*w,z+.016*math.sin(a*11)*math.cos(t)))
for j in range(rows):
 for i in range(n):
  # Door-sized missing patch at the front of the dome.
  a=(i+.5)/n*math.tau
  if j<5 and abs(a-1.5*math.pi)<.28:continue
  q=j*n+i;r=j*n+(i+1)%n;ff.append((q,r,r+n,q+n))
ob=mesh('Hand packed earth kiln dome',vv,ff,'Plaster',group='CharcoalKiln')
for f in ob.data.polygons:f.use_smooth=True
# Recess is deliberately shallow and exterior-only.
mesh('Soot-black kiln mouth',[(x,y,z) for y in [-1.30,-1.26] for x,z in [(-.29,.045),(.29,.045),(.27,.60),(-.27,.60)]],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'Charcoal',group='CharcoalKiln')
for side in [-1,1]:
 for j in range(3):fieldstone('Kiln mouth stone cheek',(side*.36,-1.20+j*.035,.13+j*.20),(.11,.20,.12))
fieldstone('Kiln mouth lintel',(0,-1.12,.70),(.42,.20,.09))
for i in range(23):
 a=i/23*math.tau
 if abs(a-1.5*math.pi)<.36:continue
 fieldstone('Kiln bedded perimeter',(1.22*math.cos(a),1.22*math.sin(a),.09),(.15,.15,.115))
# Vent is a rough short stone collar, with black opening, not a factory chimney.
for i in range(10):
 a=i/10*math.tau;fieldstone('Rough smoke vent rim',(.16*math.cos(a),.16*math.sin(a),1.53),(.075,.075,.075))
mesh('Black vent throat',[(.145*math.cos(i*math.tau/24),.145*math.sin(i*math.tau/24),1.53) for i in range(24)],[tuple(range(24))],'Charcoal',group='CharcoalKiln')
for i in range(3):beam('Kiln loose access boards',(.66+i*.13,-1.19,.04),(.58+i*.13,-.75,1.00),.12,.045,group='CharcoalKiln')
finish(before,'CharcoalKiln')
# Three reusable bark logs with pale cut ends and modest concentric grain relief.
for variant,(radius,length) in enumerate([(.16,2.35),(.19,2.6),(.135,2.15)]):
 before=start();sides=24;vv=[];ff=[]
 for j in range(5):
  y=-length/2+j*length/4
  for i in range(sides):
   a=i*math.tau/sides;r=radius*(1+.10*math.sin(i*5.1+variant)+.045*math.sin(j*2+i))
   vv.append((r*math.cos(a)+.018*math.sin(j),y,r*math.sin(a)+radius))
 for j in range(4):
  for i in range(sides):q=j*sides+i;r=j*sides+(i+1)%sides;ff.append((q,r,r+sides,q+sides))
 bark=mesh('Rough bark log '+str(variant),vv,ff,'Timber',group='Log')
 bark['bark']=True
 for end in [0,4]:
  vs=[vv[end*sides+i] for i in range(sides)]
  cap=mesh('Pale cut end',vs,[tuple(range(sides))],'Timber',group='Log');cap['cut_end']=True
  for ring in [.33,.60,.84]:
   points=[]
   for i in range(29):
    a=i*math.tau/28;r=radius*ring*(1+.04*math.sin(a*5))
    points.append((r*math.cos(a),(-length/2-.001) if end==0 else (length/2+.001),radius+r*math.sin(a)))
   line=tube('Cut growth ring',points,.0018,'Timber','Log',4);line['bark']=True
 for i in range(23):
  a=i*math.tau/23
  pts=[((radius+.002)*math.cos(a)+.005*math.sin(j*2+i),-length/2+j*length/4,(radius+.002)*math.sin(a)+radius) for j in range(5)]
  ob=tube('Long bark fissure',pts,.007,'Timber','Log',5);ob['bark']=True
 # Ragged bark plates share one reusable log mesh, duplicated throughout stacks.
 for i in range(70):
  a=random.uniform(0,math.tau);y=random.uniform(-length*.47,length*.47);ln=random.uniform(.09,.38);w=random.uniform(.025,.063)
  radial=Vector((math.cos(a),0,math.sin(a)));tangent=Vector((-math.sin(a),0,math.cos(a)))
  center=Vector((radius*math.cos(a),y,radius+radius*math.sin(a)))
  points=[center-tangent*w+Vector((0,-ln/2,0)),center+tangent*w*.4+Vector((0,-ln/2-.018,0)),center+tangent*w+Vector((0,ln/2,0)),center-tangent*w*.65+Vector((0,ln/2+.028,0)),center+radial*.018]
  o=mesh('Lifted fissured bark plate',points,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Timber',group='Log');o['bark']=True
 for end in [-1,1]:
  for a in [.4,2.8,4.8]:
   pts=[(radius*r*math.cos(a+.06*math.sin(r*8)),end*(length/2+.003),radius+radius*r*math.sin(a+.06*math.sin(r*8))) for r in [.2,.45,.7,.99]]
   ob=tube('Radial endgrain drying split',pts,.003,'Timber','Log',4);ob['bark']=True
 finish(before,'Log_%02d'%(variant+1))
 key='Log_%02d'%(variant+1);pieces=modules[key]
 for piece in pieces:
  tint(piece);rgb=(.34,.29,.215) if piece.get('bark') else (.93,.70,.39);factor=random.uniform(.80,1.12)
  for c in piece.data.color_attributes['Color'].data:c.color=(*(v*factor for v in rgb),1)
 bpy.ops.object.select_all(action='DESELECT')
 for piece in pieces:piece.select_set(True)
 bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();log=bpy.context.object;log.name='Rough bark log '+str(variant)
 for prop in ['bark','cut_end']:
  if prop in log:del log[prop]
 modules[key]=[log]

modules['LogPile']=[]
for row,count in enumerate([6,5,4,3]):
 for i in range(count):
  modules['LogPile']+=clone_objects(modules['Log_%02d'%((row+i)%3+1)],'LogPile',scale=(random.uniform(.92,1.08),random.uniform(.86,1.10),random.uniform(.92,1.08)),shift=((i-(count-1)/2)*.35,random.uniform(-.18,.18),row*.28),rotation=random.uniform(-2,2))
# Processed plank rack with loose lengths and spacer battens.
before=start()
for x in [-1.35,1.35]:
 for y in [-.36,.36]:beam('Lumber rack post',(x,y,.02),(x,y,1.70),.105,.11,group='LumberRack')
 for z in [.18,.69,1.20]:beam('Rack bearer',(x,-.56,z),(x,.56,z),.11,.12,group='LumberRack')
for tier in range(3):
 for layer in range(3):
  for j in range(5):
   y=-.41+j*.195;z=.27+tier*.51+layer*.074
   beam('Stacked seasoned rough plank',(-1.64+random.uniform(-.13,.10),y,z),(1.65+random.uniform(-.15,.15),y,z),.18,.060,group='LumberRack',rough=.004)
 for x in [-1.2,1.2]:beam('Air drying spacer',(x,-.50,.49+tier*.51),(x,.51,.49+tier*.51),.036,.032,group='LumberRack')
finish(before,'LumberRack')
# Simple reusable chopping station and sawhorse work support.
before=start()
modules['ChoppingBlock']=clone_objects(modules['Log_02'],'ChoppingBlock',(.0+1.70,.25,1.70),rotation=0)
# Orient the log onto its end, centred on ground.
for ob in modules['ChoppingBlock']:
 for v in ob.data.vertices:
  x,y,z=v.co.copy();v.co=(x,z-.323,y+.325)
beam('Axe ash handle',(.06,-.07,.62),(.39,-.17,1.27),.035,.04,group='Work')
mesh('Simple wedge axe head',[(-.06,-.11,.68),(.16,-.11,.70),(.18,-.11,.58),(-.07,-.11,.56),(-.06,-.16,.68),(.16,-.16,.70),(.18,-.16,.58),(-.07,-.16,.56)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'Iron',group='Work')
finish(before,'ChoppingBlock')
# Deduplicate pieces already registered above.
modules['ChoppingBlock']=list(dict.fromkeys(modules['ChoppingBlock']))
before=start()
for x in [-.83,.83]:
 for side in [-1,1]:beam('Sawhorse splayed leg',(x,side*.40,.025),(x,side*.12,.86),.078,.08,group='WorkBench')
 beam('Sawhorse cross brace',(x,-.35,.24),(x,.35,.24),.068,group='WorkBench')
beam('Sawhorse worn trestle',(-1.04,0,.84),(1.04,0,.84),.18,.16,group='WorkBench')
for y in [-.17,.03,.23]:beam('Work bench loose plank',(-1.26,y,.96),(1.20,y,.96),.19,.078,group='WorkBench')
finish(before,'WorkBench')
modules['CharcoalStorage']=clone_objects(kit('Baskets'),'CharcoalStorage',(1.25,1.25,1.25))
modules['CharcoalStorage']+=clone_objects(kit('Baskets'),'CharcoalStorage',(.95,.95,1.40),(.55,.12,0))
before=start()
for cx,cy,cz,r in [(0,0,.51,.20),(.55,.12,.57,.16)]:
 for i in range(22):
  a=random.uniform(0,math.tau);rr=random.uniform(0,r)
  ob=fieldstone('Basket lump charcoal',(cx+rr*math.cos(a),cy+rr*math.sin(a),cz+random.uniform(-.02,.04)),(.045,.042,.035))
  ob=groups['Fieldstone'][-1];ob.data.materials.clear();ob.data.materials.append(mats['Charcoal'])
finish(before,'CharcoalStorage')
modules['Fence']=clone_objects(kit('Fence_Straight'),'Fence')
# Shallow dirt apron, soot around the kiln and split-wood dressing.
before=start();vv=[(0,0,.021)]
for i in range(100):
 a=i*math.tau/100;c=math.cos(a);s=math.sin(a);r=1+.014*math.sin(a*17)
 vv.append((5.8*math.copysign(abs(c)**.40,c)*r,3.5*math.copysign(abs(s)**.44,s)*r,.004))
mesh('Packed dirt work yard',vv,[(0,i+1,(i+1)%100+1) for i in range(100)],'Dirt',group='GroundApron')
for i in range(115):
 x=random.uniform(-4.8,4.5);y=random.uniform(-3.1,-1.1)
 ob=beam('Scattered split wood chip',(x,y,.025),(x+random.uniform(.04,.19),y+random.uniform(-.09,.09),.03),random.uniform(.018,.045),.012,group='GroundApron',rough=.002);ob['cut_end']=True
for i in range(42):
 x=random.uniform(3.0,5.2);y=random.uniform(-2.1,.2)
 ob=fieldstone('Spilled charcoal',(x,y,.026),(.025,.033,.022));ob=groups['Fieldstone'][-1];ob.data.materials.clear();ob.data.materials.append(mats['Charcoal'])
finish(before,'GroundApron')
# Correction pass: concentrated working detail, rough surfaces, grounded edges.
before=start()
# Hewn joinery on front posts: visible pegs, long splits and bindings.
for x in [-2.8,-.92,.92,2.8]:
 for z in [2.31,2.49]:
  tube('Hewn joint exposed peg',[(x,-1.69,z),(x,-1.43,z)],.018,'Timber','MainShed',7)
 for i in range(5):
  xx=x+random.uniform(-.075,.075);z=random.uniform(.42,1.90);ln=random.uniform(.16,.52)
  mesh('Deep post drying fissure',[(xx,-1.659,z),(xx-.003,-1.659,z+ln*.37),(xx+.005,-1.659,z+ln),(xx+.004,-1.659,z+ln*.48)],[(0,1,2,3)],'Charcoal',group='MainShed')
 for yy in [-1.55,1.55]:lash('Framing cross tie hemp',(x,yy,2.51),'Y',.13,3)
# Tall loose boards at the right open bay read clearly below the eaves.
for i in range(8):
 x=1.45+i*.16;y=.95+random.uniform(-.10,.1);h=random.uniform(1.25,2.00)
 beam('Loose leaning rough board',(x,y-.48,.055),(x+random.uniform(-.12,.12),y,h),.14,.047,group='MainShed',rough=.009)
finish(before,'MainShed')
# Roof silhouette: thin irregular hanging reeds and exposed lashings, not another roof.
before=start()
for side in [-1,1]:
 for i in range(210):
  x=-3.30+i*.0315+random.uniform(-.018,.018);y=side*2.09;z=2.49+.032*math.sin(x*3.4)
  ln=random.uniform(.055,.17)
  tube('Loose broken eave straw',[(x,y-side*.09,z+.07),(x+.012,y+side*.023,z-.025),(x+.02,y+side*.06,z-ln)],random.uniform(.002,.004),'Thatch','RoofWeather',4)
finish(before,'Roof')
# Uneven log-end supports and several longer square-cut beams at the rack foot.
before=start()
for i in range(4):
 y=-.52+i*.24
 beam('Long stored hewn timber',(-1.98+random.uniform(-.15,.15),y,.095),(1.88+random.uniform(-.2,.2),y,.095),.20,.16,group='LumberRack',rough=.014)
finish(before,'LumberRack')
# A half-worked beam, mallet and offcut are visible on the outdoor trestle.
before=start()
beam('Half-worked bench timber',(-1.36,-.03,1.08),(1.38,.02,1.08),.17,.14,group='WorkBench',rough=.013)
beam('Small wooden mallet handle',(.12,-.22,1.07),(.47,-.37,1.07),.027,group='WorkBench')
beam('Small hewn mallet head',(.06,-.29,1.09),(.16,-.16,1.09),.068,.085,group='WorkBench')
finish(before,'WorkBench')
# Kiln abrasion: hairline cracks across clay, conforming to the handmade mound.
before=start()
for i in range(45):
 a=random.uniform(0,math.tau);t=random.uniform(.25,1.32);ln=random.uniform(.07,.20);pts=[]
 for j in range(5):
  tj=t+(j/4-.5)*ln;aj=a+.022*math.sin(j*1.7+i)
  r=1.39*math.cos(tj)*(1+.045*math.sin(aj*7+tj*4)+.025*math.sin(aj*17-tj*11))+.003
  pts.append((r*math.cos(aj),r*math.sin(aj),.04+1.48*math.sin(tj)+.016*math.sin(aj*11)*math.cos(tj)))
 tube('Kiln fine dried clay fissure',pts,.0025,'Charcoal','CharcoalKiln',4)
finish(before,'CharcoalKiln')
# Ground dressing in authored work zones: coarse chips, split billets, irregular gravel.
before=start()
for cx,cy,sx,sy in [(.12,-2.38,.8,.57),(-1.0,-2.5,1.45,.65),(-3.1,-2.3,1.1,.40)]:
 for i in range(100):
  x=random.gauss(cx,sx*.42);y=random.gauss(cy,sy*.42);a=random.uniform(0,math.tau);ln=random.uniform(.016,.09)
  p=Vector((x,y,.035));d=Vector((math.cos(a)*ln,math.sin(a)*ln,.008));w=Vector((-math.sin(a)*ln*.3,math.cos(a)*ln*.3,0))
  ob=mesh('Fresh split timber chip',[p-w,p+w,p+d+w*.3,p+d-w*.3],[(0,1,2,3)],'Timber',group='GroundApron');ob['cut_end']=True
for i in range(13):
 x=random.uniform(.15,1.2);y=random.uniform(-2.6,-1.7);ln=random.uniform(.25,.49)
 ob=beam('Chopped split billet',(x,y,.08),(x+random.uniform(-.2,.2),y+ln,.08),random.uniform(.055,.11),.07,group='GroundApron',rough=.014);ob['cut_end']=True
for i in range(145):
 x=random.uniform(-5.35,5.3);y=random.uniform(-3.2,3.0)
 if -4.5<x<1.5 and y>-.3:continue
 fieldstone('Fine yard gravel',(x,y,.015),(random.uniform(.015,.04),random.uniform(.018,.045),random.uniform(.015,.033)))
# Sparse trampled grass breaks the hard diorama edge with the existing shared thatch.
for i in range(320):
 a=random.uniform(0,math.tau);c=math.cos(a);ss=math.sin(a);r=random.uniform(.95,1.055)
 x=5.75*math.copysign(abs(c)**.40,c)*r;y=3.48*math.copysign(abs(ss)**.44,ss)*r
 if -2<x<2 and y<0:continue
 vv=[];ff=[]
 for j in range(random.randint(4,8)):
  az=random.uniform(0,math.tau);h=random.uniform(.045,.18);w=random.uniform(.006,.016)
  p=Vector((x+random.uniform(-.08,.08),y+random.uniform(-.08,.08),.012));d=Vector((math.cos(az)*.07,math.sin(az)*.07,h));cross=Vector((-math.sin(az)*w,math.cos(az)*w,0));k=len(vv)
  vv.extend([p-cross,p+cross,p+d*.6+cross*.35,p+d*.6-cross*.35,p+d]);ff.extend([(k,k+1,k+2,k+3),(k+3,k+2,k+4)])
 ob=mesh('Trampled sparse verge',vv,ff,'Thatch',group='GroundApron');ob['grass_tone']=(.30,.41,.14) if i%3 else (.62,.49,.25)
finish(before,'GroundApron')
# Reduce the kit's rounded pebble look at the kiln and exposed footings.
for ob in src.objects:
 if any(label in ob.name for label in ['Kiln mouth','Kiln bedded','Rough smoke','Shed bedded','Lean-to footing']):
  for p in ob.data.polygons:p.use_smooth=False
  for v in ob.data.vertices:v.co.z+=random.uniform(-.013,.013)

# Export the modular, local-pivot parts using the established SHŌEN FBX exporter.
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
sys.path.insert(0,str(ART/'Scripts'))
from finish_asset import export_linear as fbx
for key,obs in modules.items():
 print('EXPORTING',key,len(obs),flush=True)
 for ob in obs:
  if ob.modifiers:
   bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  if not ob.data.color_attributes.get('Color'):tint(ob)
  colors=ob.data.color_attributes['Color']
  if ob.get('bark') or ob.get('cut_end'):
   rgb=(.34,.29,.215) if ob.get('bark') else (.93,.70,.39)
   factor=random.uniform(.80,1.12)
   for c in colors.data:c.color=(*(v*factor for v in rgb),1)
  if 'kiln dome' in ob.name:
   for face in ob.data.polygons:
    for li in face.loop_indices:
     p=ob.data.vertices[ob.data.loops[li].vertex_index].co
     soot=max(math.exp(-((p.x/.43)**2+((p.y+1.15)/.42)**2))*max(0,1-p.z/1.45),math.exp(-((p.x/.47)**2+(p.y/.47)**2))*max(0,(p.z-1)/.5))
     k=(.78+.11*math.sin(p.x*12+p.z*10)*math.sin(p.y*13-p.z*7))*(1-.87*soot)
     colors.data[li].color=(.45*k,.365*k,.255*k,1)
  if ob.get('roof_weathering'):
   for face in ob.data.polygons:
    for li in face.loop_indices:
     p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.77+.10*math.sin(p.x*3.3+p.y*2.3)+.035*math.sin(p.x*26+p.y*8)
     old=colors.data[li].color;colors.data[li].color=(old[0]*k,old[1]*k*1.02,old[2]*k*1.05,1)
  ob.modifiers.new('Export triangulation','TRIANGULATE')
 fbx(ART/'Exports'/('LC01_'+key+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangulation'])

fbx(ART/'Exports/LumberShed_01.fbx',modules['MainShed']+modules['Roof'])

def place(key,loc,angle=0,scale=(1,1,1)):
 index=sum(1 for x in instances if x['mesh']=='LC01_'+key)
 label='LC01_'+key+('_%02d'%index if index else '')
 col=bpy.data.collections.new(label);src.children.link(col)
 matrix=Matrix.Translation(Vector(loc))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in modules[key]:
  ob=original if index==0 else original.copy()
  if index==0:
   for c in list(ob.users_collection):c.objects.unlink(ob)
  col.objects.link(ob);ob.matrix_world=matrix
 instances.append({'mesh':'LC01_'+key,'name':label,'location':list(loc),'rotation_degrees':angle,'scale':list(scale)})


place('MainShed',(-1.50,.90,0));place('Roof',(-1.50,.90,0))
place('LeanTo',(2.27,.90,0))
place('CharcoalKiln',(4.13,-.48,0))
place('LumberRack',(-1.38,1.48,0))
place('LogPile',(-3.10,-1.13,0),0,(1.03,1.04,1.03))
place('LogPile',(2.26,.88,0),0,(.60,.78,.82))
place('ChoppingBlock',(.10,-2.40,0),-15)
place('WorkBench',(-1.05,-2.50,0),-7)
place('CharcoalStorage',(2.38,-1.23,0),-15)
place('CharcoalStorage',(3.15,1.50,0),20,(.85,.85,.85))
for x,y,r,sx in [(-5.02,-2.3,90,1.12),(-5.02,.0,90,1.30),(-4.90,2.94,0,1.25),(-2.40,2.94,0,1.25),(.1,2.94,0,1.25),(2.6,2.94,0,1.32),(5.42,.50,90,1.2)]:
 place('Fence',(x,y,0),r,(sx,1,1))
place('GroundApron',(0,0,-.008))
# Base log meshes are kept in their own excluded reusable-source collection.
base=bpy.data.collections.new('Reusable base logs • excluded from yard display');scene.collection.children.link(base)
for key in ['Log_01','Log_02','Log_03']:
 for ob in modules[key]:
  for c in list(ob.users_collection):c.objects.unlink(ob)
  base.objects.link(ob);ob.hide_render=True;ob.hide_set(True)
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'LumberCharcoal_01','units':'metres','instances':instances},indent=2)+'\n')
# An assembled static mesh is also supplied for quick placement.
assembled=[o for c in src.children for o in c.objects if o.type=='MESH']
for ob in assembled:ob.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/LumberCharcoal_01.fbx',assembled)
for ob in assembled:ob.modifiers.remove(ob.modifiers['Export triangulation'])
# Remove unused appended library objects from the source scene data, preserving originals on disk.
for col in kit_collections.values():bpy.data.collections.remove(col)
for ob in roof_objects:
 if not ob.users_collection:bpy.data.objects.remove(ob)
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review ground'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.038,.045,.029,1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.48,.56,1);world.node_tree.nodes['Background'].inputs[1].default_value=.36
def area(name,loc,energy,size,color,target=(0,0,1)):
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=energy;d.color=color;d.shape='DISK';d.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Warm afternoon',(-5,-7,11),1900,5,(1,.91,.78))
area('Sky fill',(4,4,8),850,8,(.79,.86,1))
area('Open shelter daylight',(-1,-5,3.5),550,5,(.90,.92,1))
d=bpy.data.lights.new('Afternoon sun','SUN');ob=bpy.data.objects.new(d.name,d);studio.objects.link(ob)
ob.rotation_euler=(.40,-.50,-.55);d.energy=2.7;d.color=(1,.93,.82);d.angle=.10
cd=bpy.data.cameras.new('LumberCharcoal three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam)
cam.location=(-12.4,-19.5,7.7);cam.rotation_euler=(Vector((.10,.18,1.48))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=52;scene.camera=cam
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='LumberCharcoal_01 • exterior only • reused SHŌEN farm kit • open shed, earthen kiln, timber processing yard'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'LumberCharcoal01.blend'))
print('YARD_SAVED',len(instances),'module instances',flush=True)
scene.render.filepath=str(OUT/'lumbercharcoal-three-quarter.png');bpy.ops.render.render(write_still=True)
print('YARD_COMPLETE',flush=True)
