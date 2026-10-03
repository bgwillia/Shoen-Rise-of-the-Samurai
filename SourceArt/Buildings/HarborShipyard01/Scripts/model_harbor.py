"""One authored harbor art pass using the established rural kit and FBX export."""
from pathlib import Path
import ast,sys,math,random,json
import bpy,bmesh
from mathutils import Vector,Matrix
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/harborshipyard01'
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(118016)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
src=bpy.data.collections.new('HarborShipyard_01');scene.collection.children.link(src)
groups={};modules={};instances=[];mats={}
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash'}),(ART.parent/'Storehouse01/Scripts/refine_reference_match.py',{'fieldstone'}),(ART.parent/'FarmCompound01/Scripts/model_farm.py',{'tint'})]:
 for n in ast.parse(file.read_text()).body:
  if isinstance(n,ast.FunctionDef) and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),str(file),'exec'))
with bpy.data.libraries.load(str(ART.parent/'LumberCharcoal01/LumberCharcoal01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Timber','SH01_Thatch','SH01_Stone','SH01_Iron','RH01_Rope','FC01_Dirt','SM01_Water']]
 b.collections=['LC01_Roof','LC01_LumberRack','LC01_LogPile','LC01_WorkBench','LC01_Fence']
for m in b.materials:mats[m.name.split('_',1)[1]]=m
kit={c.name:c for c in b.collections}
with bpy.data.libraries.load(str(ART.parent/'Market01/Market01.blend'),link=False) as (a,b):
 b.objects=['MK01_Crate']
cratecol=bpy.data.collections.new('Reused market crate')
for ob in b.objects:cratecol.objects.link(ob)
def reuse(col,key,scale=(1,1,1)):
 obs=[]
 for original in col.objects:
  if original.type!='MESH':continue
  o=original.copy();o.data=original.data.copy();o.matrix_world=Matrix.Identity(4);o.name=key+' '+original.name;src.objects.link(o)
  for v in o.data.vertices:v.co=Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))
  for i,m in enumerate(o.data.materials):
   family=m.name.split('.')[0].split('_',1)[-1]
   if family in mats:o.data.materials[i]=mats[family]
  o['reused_from']=col.name;obs.append(o)
 modules[key]=obs
 return obs
def start():return set(src.objects)
def finish(before,key):modules[key]=list(set(src.objects)-before)
reuse(kit['LC01_Roof'],'HS01_Roof',(1.62,1.48,1.115))
for ob in modules['HS01_Roof']:
 for v in ob.data.vertices:
  v.co.z+=.30+.028*math.sin(v.co.x*2.7+v.co.y*3.9)
reuse(kit['LC01_LumberRack'],'HS01_LumberStacks')
reuse(kit['LC01_LogPile'],'HS01_LogPile',(.85,.85,.85))
reuse(kit['LC01_WorkBench'],'HS01_WorkBench')
reuse(kit['LC01_Fence'],'HS01_Fence')
reuse(cratecol,'HS01_Crate')
# Main open shipbuilding bay: the roof ridge follows X, water is toward -Y.
before=start()
for x in [-4.85,-1.62,1.62,4.85]:
 for y in [-2.45,2.45]:
  fieldstone('Bedded timber footing',(x,y,.09),(.28,.29,.16))
  beam('Salt weathered main post',(x,y,.13),(x,y,2.86),.24,.25)
  for s in [-1,1]:
   if abs(x+s*.65)<5.1:beam('Hewn knee brace',(x,y,2.12),(x+s*.65,y,2.80),.13,.14)
  lash('Frame joint binding',(x,y,2.75),'Y',.155,4)
for y in [-2.45,2.45]:beam('Long eave plate',(-5.15,y,2.80),(5.15,y,2.80),.24,.25)
for x in [-4.85,-1.62,1.62,4.85]:
 beam('Clear bay tie',(x,-2.6,2.84),(x,2.6,2.84),.19,.22)
 beam('King post',(x,0,2.84),(x,0,4.35),.16,.17)
 for s in [-1,1]:
  beam('Gable principal rafter',(x,s*3.1,2.78),(x,0,4.35),.16,.17)
  beam('Gable brace',(x,s*1.95,2.84),(x,0,4.18),.115,.12)
beam('Visible ridge',(-5.4,0,4.35),(5.4,0,4.35),.20,.23)
for i in range(51):
 x=-4.8+i*.188
 beam('Partial rear weatherboard',(x,2.45,.24),(x,2.45,1.9+random.uniform(-.08,.08)),.18,.052)
for z in [.4,1.3,1.92]:beam('Rear wall rail',(-5,2.49,z),(5,2.49,z),.12,.10)
# One gable has a low boarded windbreak; the work bay stays visibly open.
for i in range(19):
 y=-.9+i*.17
 beam('Gable lower board',(4.85,y,.23),(4.85,y,1.24),.16,.045)
for ob in set(src.objects)-before:
 for v in ob.data.vertices:
  if v.co.z>2.05:v.co.z+=.30*min(1,(v.co.z-2.05)/.65)
finish(before,'HS01_Frame')
# Reusable rope-wrapped timber mooring post, bottom below waterline.
before=start()
tube('Heavy weathered mooring pile',[(0,0,-1.7),(0,0,.05),(.012,0,1.05)],.145,sides=12)
for j in range(7):
 pts=[(.158*math.cos(t*math.tau/24),.158*math.sin(t*math.tau/24),.60+j*.026) for t in range(25)]
 tube('Post rope winding',pts,.014,'Rope',sides=6)
beam('Mooring cross pin',(-.24,0,.84),(.24,0,.84),.066,.073)
finish(before,'MooringPost_01')
# Dock modules are local-pivot pieces, 2m wide and 3m long.
for key,end in [('Dock_Straight_01',False),('Dock_End_01',True)]:
 before=start()
 for x in [-.83,.83]:
  beam('Dock underside stringer',(x,-1.55,-.22),(x,1.55,-.22),.19,.23)
  for y in [-1.35,1.35]:
   tube('Dock wet support pile',[(x,y,-1.8),(x,y,.73)],.115,sides=10)
   lash('Dock bearer lashing',(x,y,-.10),'Y',.16,4)
  beam('Dock diagonal bracing',(x,-1.35,-1.30),(x,1.35,-.24),.11,.12)
 for j in range(16):
  y=-1.5+j*.195
  beam('Uneven heavy dock plank',(-1.02+random.uniform(-.035,.025),y,random.uniform(-.012,.012)),(1.02+random.uniform(-.025,.035),y,random.uniform(-.012,.012)),.185,.083,rough=.008)
  for x in [-.83,.83]:tube('Dark peg',[(x,y,.038),(x,y,.048)],.013,'Iron',sides=6)
 if end:beam('Dock end cross bearer',(-1.04,-1.56,-.12),(1.04,-1.56,-.12),.16,.19)
 finish(before,key)
# Slipway is 7m long with paired continuous rails and widely legible sleepers.
before=start()
for x in [-.80,.80]:beam('Continuous slipway rail',(x,0,.16),(x,-7,-1.05),.18,.20)
for i in range(19):
 y=-i*7/18;z=.02+y*1.21/7
 beam('Slipway cross sleeper',(-1.17,y,z),(1.17,y,z),.18,.15)
 if i%4==0:
  for x in [-.83,.83]:beam('Slipway bed support',(x,y,z-.7),(x,y,z),.15,.17)
finish(before,'Slipway_01')
# Primitive hand winch and its visible rope drum.
before=start()
for x in [-.65,.65]:
 beam('Winch upright',(x,0,0),(x,0,1.75),.16,.18)
 beam('Winch splayed brace',(x,-.62,0),(x,0,1.12),.1,.11)
 beam('Winch foot',(x,-.75,.07),(x,.52,.07),.16,.16)
beam('Winch top tie',(-.8,0,1.72),(.8,0,1.72),.16,.17)
tube('Winch drum axle',[(-.91,0,.95),(.91,0,.95)],.105,sides=12)
for x in [-.42,.42]:tube('Drum timber cheek',[(x-.042,0,.95),(x+.042,0,.95)],.32,sides=16)
pts=[]
for i in range(460):
 a=i/20*math.tau;pts.append((-.38+i/459*.76,.21*math.cos(a),.95+.21*math.sin(a)))
tube('Heavy wound hemp drum',pts,.020,'Rope',sides=6)
beam('Winch turning lever',(.88,-.65,.95),(.88,.65,.95),.065,.073)
tube('Winch pulling cable',[(0,-.21,.95),(0,-.65,.3),(0,-2.0,.10)],.022,'Rope',sides=7)
finish(before,'ShipyardWinch_01')
# Boat strakes, overlapping as real wooden planks, open hull with cross seats.
before=start();N=32
# Longitudinal direction Y. Beam tapers to raised bow and stern.
def hull(t,h,side):
 y=t*2.55;shape=max(.015,1-t*t)**.60
 return (side*(.23+.62*h)*shape,y,.08+.78*h+.30*abs(t)**4)
for side in [-1,1]:
 for row in range(6):
  vv=[];ff=[]
  for i in range(N+1):
   t=-.99+i/N*1.98
   for h in [row/6,(row+1)/6-.008]:vv.append(hull(t,h,side))
  for i in range(N):ff.append((i*2,i*2+1,i*2+3,i*2+2))
  o=mesh('Curved overlapping hull strake',vv,ff,'Timber');sol=o.modifiers.new('Solid plank thickness','SOLIDIFY');sol.thickness=.027
  tube('Worn upper gunwale',[hull(-.99+i/N*1.98,1,side) for i in range(N+1)],.043,sides=8)
beam('Long keel',(0,-2.51,.35),(0,2.51,.35),.14,.14)
for i in range(15):
 y=-2.25+i*.32;t=y/2.55
 pts=[hull(t,h,s) for s,hs in [(-1,[.92,.65,.3,0]),(1,[0,.3,.65,.92])] for h in hs]
 tube('Exposed hull rib',[(x*.965,yy,z+.024) for x,yy,z in pts],.034,sides=6)
for y in [-1.4,-.35,.80,1.65]:
 w=hull(y/2.55,.82,1)[0]
 beam('Boat cross seat',(-w,y,.75),(w,y,.75),.28,.060,rough=.004)
for y in [-2.53,2.53]:beam('Raised bow stern stem',(0,y,.30),(0,y,1.24),.075,.11)
for j in range(5):
 x=(j-2)*.082
 beam('Bottom floorboard',(x,-1.9,.27),(x,1.9,.27),.077,.03,rough=.002)
finish(before,'WorkBoat_01')
# Hanging net is sparse opaque rope geometry, no expensive cutout sheets.
before=start()
for x in [-1.12,1.12]:beam('Net rack upright',(x,0,0),(x,0,2.12),.095,.11)
beam('Net rack upper bar',(-1.3,0,2.08),(1.3,0,2.08),.10,.11)
def netpos(u,v):return ((u-.5)*2.10,-.09-.14*math.sin(u*math.pi)*math.sin(v*math.pi),1.94-v*1.45-.31*math.sin(u*math.pi))
for i in range(19):tube('Hanging net warp',[netpos(i/18,j/14) for j in range(15)],.005,'Rope',sides=4)
for j in range(15):tube('Hanging net weft',[netpos(i/18,j/14) for i in range(19)],.005,'Rope',sides=4)
for x in [-.9,.9]:
 for k in range(5):
  tube('Hanging coil',[(x+.17*math.cos(i*math.tau/32),-.15+k*.018,1.35+.53*math.sin(i*math.tau/32)) for i in range(33)],.014,'Rope',sides=6)
finish(before,'HS01_RopeNetStorage')
# Shore stone retaining face, open working earth apron, irregular coastal toe.
before=start()
mesh('Work yard earth',[(-7,-4,-.04),(7,-4,-.04),(7,4,-.04),(-7,4,-.04)],[(0,1,2,3)],'Dirt')
for row in range(3):
 for i in range(34):
  x=-7+i*.42+(row%2)*.2
  fieldstone('Dry stacked shore stone',(x,-4.0+random.uniform(-.13,.13),-.18-row*.27),(.27,.32,.20))
for i in range(90):
 x=random.uniform(-8,8);y=random.uniform(-4.9,-4.3)
 fieldstone('Tidal shoreline rubble',(x,y,-.90),(.15+random.random()*.24,.18+random.random()*.2,.12+random.random()*.15))
for i in range(135):
 x=random.uniform(-22,22)
 if abs(x)<7:continue
 fieldstone('Scattered natural shore boulder',(x,-4.15+random.uniform(-.60,.23),-.57),(.22+random.random()*.42,.23+random.random()*.3,.20+random.random()*.28))
for ob in set(src.objects)-before:
 if ob.type=='MESH':
  for f in ob.data.polygons:f.use_smooth=False
finish(before,'HS01_Shoreline')
# Reference-led gable canopy: layered split shingles, exposed rafters and irregular edges.
before=start()
for side in [-1,1]:
 for row in range(9):
  y0=side*(3.22-row*.355);y1=side*(3.22-row*.355-.52)
  for j in range(14):
   x=-6.13+j*.201+(row%2)*.09+random.uniform(-.016,.016)
   z0=4.79-abs(y0)*.49+row*.008;z1=4.79-abs(y1)*.49+row*.008
   o=beam('Weather silvered split shingle',(x,y0,z0),(x+random.uniform(-.018,.018),y1,z1),random.uniform(.187,.218),random.uniform(.024,.038),rough=.009)
   o['shingle']=True
 for x in [-6.17,-3.42]:
  beam('Gable canopy rafter',(x,side*3.3,3.12),(x,0,4.85),.145,.16)
beam('Canopy ridge timber',(-6.30,0,4.86),(-3.2,0,4.86),.13,.16)
for y in [-2.58,2.58]:
 beam('Front gable supporting upright',(-5.97,y,.1),(-5.97,y,3.18),.22,.23)
 beam('Gable canopy knee',(-5.97,y,2.52),(-5.22,y,3.12),.12,.13)
 fieldstone('Canopy bedded stone',(-5.97,y,.05),(.31,.29,.18))
beam('Front gable cross tie',(-5.97,-2.7,3.12),(-5.97,2.7,3.12),.20,.22)
beam('Front gable kingpost',(-5.97,0,3.12),(-5.97,0,4.80),.16,.17)
for side in [-1,1]:beam('Gable diagonal truss',(-5.97,side*2.20,3.14),(-5.97,0,4.58),.12,.13)
# Weathered pegs and long drying splits catch grazing light on the front-facing posts.
for x in [-5.97,-4.85,-1.62,1.62,4.85]:
 for y in [-2.45,2.45]:
  for z in [2.83,3.04]:tube('Exposed joint peg',[(x,y-.15,z),(x,y-.12,z)],.024,sides=7)
  for j in range(6):
   xx=x+random.uniform(-.085,.085);z=random.uniform(.28,2.6);ln=random.uniform(.12,.45)
   mesh('Post weather split',[(xx,y-.127,z),(xx-.003,y-.128,z+ln*.4),(xx+.001,y-.128,z+ln),(xx+.005,y-.128,z+ln*.35)],[(0,1,2,3)],'Iron')
modules['HS01_Roof']+=list(set(src.objects)-before)
# Restrained nautical dressing: loose coils, trailed mooring lines and dock repairs.
before=start()
for cx,cy,cz in [(-4.9,-5.0,.03),(4.8,-8.1,.03),(3.75,-3.0,.08)]:
 pts=[]
 for j in range(200):
  a=j/24*math.tau;r=.08+j/199*.27;pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r,cz+.014))
 tube('Loose working rope coil',pts,.015,'Rope',sides=6)
for a,b in [((-3.8,-8.9,.60),(-.55,-10.10,-.16)),((5.83,-7,.6),(3.25,-10.25,-.12))]:
 av=Vector(a);bv=Vector(b)
 tube('Slack mooring line',[av.lerp(bv,j/24)+Vector((0,0,-.35*math.sin(j/24*math.pi))) for j in range(25)],.017,'Rope',sides=6)
# A few laid-out boatyard beams reuse the timber rack rather than a new lumber library.
finish(before,'HS01_WorkingRopes')

# Use the existing linear color and FBX export exactly as the other buildings.
sys.path.insert(0,str(ART.parent/'LumberCharcoal01/Scripts'))
from finish_asset import export_linear as fbx
for key,obs in modules.items():
 for o in obs:
  if not o.data.color_attributes.get('Color'):tint(o)
  # Salt-grey variation and a restrained darker waterline on the existing timber.
  if any(m.name=='SH01_Timber' for m in o.data.materials):
   for face in o.data.polygons:
    for li in face.loop_indices:
     p=o.data.vertices[o.data.loops[li].vertex_index].co;c=o.data.color_attributes['Color'].data[li];r,g,b,a=c.color
     wet=.52 if p.z<-.25 and key in ['Dock_Straight_01','Dock_End_01','MooringPost_01','Slipway_01'] else 1
     c.color=(r*1.22*wet,g*1.30*wet,b*1.40*wet,a)
  for mod in list(o.modifiers):
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  o.modifiers.new('Export triangles','TRIANGULATE')
 fbx(ART/'Exports'/(key+'.fbx'),obs)
 for o in obs:o.modifiers.remove(o.modifiers['Export triangles'])
for o in modules['HS01_Frame']+modules['HS01_Roof']:o.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/ShipyardShed_01.fbx',modules['HS01_Frame']+modules['HS01_Roof'])
for o in modules['HS01_Frame']+modules['HS01_Roof']:o.modifiers.remove(o.modifiers['Export triangles'])
def place(key,loc,angle=0,scale=(1,1,1)):
 label=key+'_%02d'%sum(i['mesh']==key for i in instances)
 col=bpy.data.collections.new(label);src.children.link(col)
 mat=Matrix.Translation(Vector(loc))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in modules[key]:
  o=original.copy();o.data=original.data;col.objects.link(o);o.matrix_world=mat
 instances.append(dict(mesh=key,name=label,location=list(loc),rotation_degrees=angle,scale=list(scale)))
place('HS01_WorkingRopes',(0,0,0));place('HS01_Frame',(0,0,0));place('HS01_Roof',(0,0,0));place('HS01_Shoreline',(0,0,0))
for x in [-5.0,5.0]:
 place('Dock_Straight_01',(x,-5.4,-.08));place('Dock_End_01',(x,-8.4,-.08))
place('Dock_Straight_01',(-2.5,-8.5,-.08),90)
place('Slipway_01',(0,-2.9,0));place('ShipyardWinch_01',(-1.65,-2.95,.02))
place('WorkBoat_01',(.15,-.45,.28),90)
# One reusable boat design, with an additional moored instance.
place('WorkBoat_01',(1.25,-10.35,-1.05),78)
place('HS01_LumberStacks',(-3.25,1.35,0),0,(.78,.78,.83));place('HS01_LumberStacks',(4.2,1.5,0),90,(.8,.8,.8))
place('HS01_LogPile',(6.0,1.1,0),0,(.75,1,.8))
place('HS01_WorkBench',(-3.2,-2.9,0),-8)
place('HS01_RopeNetStorage',(3.2,-2.9,0),-7)
for loc in [(-5.85,-4.15,-.08),(-5.85,-9.65,-.08),(-3.8,-8.9,-.08),(5.83,-7,-.08),(5.85,-9.65,-.08)]:place('MooringPost_01',loc)
for x,y,r in [(-6.1,-2,12),(-5.8,-1,3),(5.7,-2.9,-10)]:place('HS01_Crate',(x,y,0),r)
for x in [-5.7,-3.4,3.5,5.8]:place('HS01_Fence',(x,3.5,0))
for obs in modules.values():
 for o in obs:bpy.data.objects.remove(o,do_unlink=True)
assembled=[o for c in src.children for o in c.objects]
for o in assembled:o.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/HarborShipyard_01.fbx',assembled)
for o in assembled:o.modifiers.remove(o.modifiers['Export triangles'])
(ART/'Exports/assembly.json').write_text(json.dumps(dict(asset='HarborShipyard_01',units='metres',instances=instances),indent=2))
# Simple review coastline, excluded from exported harbor asset.
studio=bpy.data.collections.new('Review only - coast and lighting');scene.collection.children.link(studio)
def plane(name,loc,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for c in list(o.users_collection):c.objects.unlink(o)
 studio.objects.link(o)
plane('Land behind quay',(0,498,-.65),(2000,1004,1.2),mats['Dirt'])
# Static rippled sea surface: authored mesh only, no water simulation.
vv=[];ff=[];nx=260;ny=220
for j in range(ny+1):
 y=-4.01-j*.36
 for i in range(nx+1):
  x=-48+i*.36;z=-.94+.025*math.sin(x*2.5+y*3.8)+.016*math.sin(x*5.8-y*2.0)+.012*math.sin(y*11+x*4)
  vv.append((x,y,z))
for j in range(ny):
 for i in range(nx):
  a=j*(nx+1)+i;ff.append((a,a+1,a+nx+2,a+nx+1))
water=mesh('Static rippled coastal surface',vv,ff,'Water')
for f in water.data.polygons:f.use_smooth=True
for c in list(water.users_collection):c.objects.unlink(water)
studio.objects.link(water)
# Reuse two existing buildings behind the harbor for a real coastal work district.
for filename,prefix,loc,ang in [('RuralHouse01','RH01_',(-10,10,0),.12),('Smithy01','SM01_',(5,13,0),-.17)]:
 with bpy.data.libraries.load(str(ART.parent/filename/(filename+'.blend')),link=False) as (a,b):
  b.objects=[n for n in a.objects if n.startswith(prefix)]
 for ob in b.objects:
  if ob.type!='MESH':continue
  studio.objects.link(ob);ob.hide_render=False;ob.hide_set(False)
  ob.matrix_world=Matrix.Translation(Vector(loc))@Matrix.Rotation(ang,4,'Z')@ob.matrix_world
# Patchy shoreline vegetation and gravel keep the scene from reading as a pedestal.
for i in range(750):
 x=random.uniform(-24,24);y=random.uniform(-3.8,23)
 if -7<x<7 and y<4:continue
 h=random.uniform(.06,.24);vv=[];ff=[]
 for k in range(5):
  az=random.uniform(0,math.tau);p=Vector((x+random.uniform(-.06,.06),y+random.uniform(-.06,.06),.01));w=Vector((math.cos(az)*.016,math.sin(az)*.016,0));top=p+Vector((math.cos(az)*h*.4,math.sin(az)*h*.4,h));a=len(vv);vv.extend([p-w,p+w,top]);ff.append((a,a+1,a+2))
 ob=mesh('Sparse coastal grass',vv,ff,'Thatch');ob['grass_tone']=(.28,.36,.13);tint(ob)
 for c in list(ob.users_collection):c.objects.unlink(ob)
 studio.objects.link(ob)

world=bpy.data.worlds.new('Coastal daylight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.59,.72,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,loc,power,size in [('Soft coastal sun',(-7,-10,15),3300,7),('Open bay fill',(0,-6,5),900,8)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Sun','SUN');o=bpy.data.objects.new('Sun',d);studio.objects.link(o);o.rotation_euler=(.45,-.6,-.4);d.energy=2;d.angle=.13
cd=bpy.data.cameras.new('Harbor three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(-25,-24,12.7);cam.rotation_euler=(Vector((0,-2.5,1))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=52;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
# Remove unused source-kit collections from display/data; keep their actual source files intact.
for col in list(kit.values())+[cratecol]:bpy.data.collections.remove(col)
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(ART/'HarborShipyard01.blend'))
scene.render.filepath=str(OUT/'harbor-three-quarter.png');bpy.ops.render.render(write_still=True)
print('HARBOR_SAVED_AND_RENDERED',flush=True)
