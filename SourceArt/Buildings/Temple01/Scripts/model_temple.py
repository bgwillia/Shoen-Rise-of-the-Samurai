"""One authored Temple_01 exterior, assembled with the established SHŌEN art kit."""
from pathlib import Path
import ast, math, random, sys, json
import bpy, bmesh
from mathutils import Vector

ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/temple01'
OUT.mkdir(parents=True,exist_ok=True);(ART/'Exports').mkdir(parents=True,exist_ok=True)
random.seed(118001)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=2000;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def coll(name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
src=coll('TP01 • editable modules at local ground origins')
layout=coll('Temple_01 • authored exterior assembly');studio=coll('Review only • excluded from export')
groups={};modules={};instances=[];mats={}
for blend,names in [('Smithy01',['SH01_Timber','SH01_Thatch','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope']),('Market01',['MK01_Cloth','MK01_Ink','MK01_Leaf','FC01_Dirt'])]:
 with bpy.data.libraries.load(str(ART.parent/blend/(blend+'.blend')),link=False) as (a,b):b.materials=names
 for m in b.materials:
  if m:mats[m.name.split('_',1)[1].split('.')[0]]=m
cedar=mats['Timber'].copy();cedar.name='TP01_Cedar'
for node in cedar.node_tree.nodes:
 if node.type=='TEX_IMAGE' and node.image:
  suffix=next((s for s in ['BaseColor','Normal','ORM'] if s in node.image.name),None)
  if suffix:
   node.image=bpy.data.images.load(str(ART/'Textures'/('TP01_Cedar_'+suffix+'.png')),check_existing=True)
   if suffix!='BaseColor':node.image.colorspace_settings.name='Non-Color'
   node.image.pack()
 if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.38
mats['Cedar']=cedar
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash'}),(ART.parent/'SmallShrine01/Scripts/model_shrine.py',{'fieldstone','block'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(file),'exec'))
kit_beam=beam
def beam(name,a,b,width,depth=None,mat='Cedar',group='Frame',rough=.0015):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat in ['Timber','Cedar']:
  ox=random.random();oy=random.random()
  for v in ob.data.uv_layers.active.data:v.uv.x=v.uv.x*max(.20,width*2.8)+ox;v.uv.y=v.uv.y*.56+oy
 return ob
kit_block=block
def block(name,center,size,mat='Cedar',group='MainHall',bevel=.01):
 return kit_block(name,center,size,mat,group,bevel)
def before():return set(src.objects)
def collect(old,name):modules[name]=[o for o in src.objects if o not in old]
def tint(ob,rgb):
 co=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for item in co.data:item.color=(*rgb,1)
 ob.data.color_attributes.active_color=co;ob['authored_tint']=True
 return ob

# Deliberate coursed foundation: low enough for an approachable community hall.
old=before()
block('Recessed stone hall footings',(0,0,.23),(10.7,7.5,.45),'Stone','TP01_Foundation',.03)
for row in range(2):
 z=.12+row*.20
 for y in [-3.78,3.78]:
  for i in range(21):fieldstone('Hall foundation stone',(-5.15+i*.514,y,z),(.263,.255,.14))
 for x in [-5.40,5.40]:
  for i in range(14):fieldstone('Hall return foundation stone',(x,-3.47+i*.53,z),(.24,.277,.14))
# Individual bedded stones carry the exposed timber platform, like the reference.
for x in [-6.55,-4.36,-2.18,0,2.18,4.36,6.55]:
 for y in [-4.8,4.8]:
  fieldstone('Broad veranda ground footing',(x,y,.13),(.37,.36,.18))
  block('Dressed column base',(x,y,.36),(.46,.46,.23),'Stone','TP01_Foundation',.042)
for x in [-6.55,6.55]:
 for y in [-2.4,0,2.4]:fieldstone('Veranda return footing',(x,y,.17),(.39,.34,.22))
collect(old,'Temple_Foundation_01')

old=before()
for y in [-4.85,-3.5,0,3.5,4.85]:beam('Raised veranda bearer',(-6.82,y,1.11),(6.82,y,1.11),.21,.24,group='TP01_Veranda')
for x in [-6.55,-4.36,-2.18,0,2.18,4.36,6.55]:
 for y in [-4.8,4.8]:
  beam('Exposed veranda support',(x,y,.46),(x,y,1.24),.25,group='TP01_Veranda')
for x in [-6.55,6.55]:
 for y in [-2.4,0,2.4]:beam('Exposed return support',(x,y,.35),(x,y,1.24),.25,group='TP01_Veranda')
for y in [-4.8,4.8]:
 beam('Lower long platform stretcher',(-6.65,y,.64),(6.65,y,.64),.13,.15,group='TP01_Veranda')
 for x in [-5.45,-3.25,3.25,5.45]:beam('Veranda diagonal underbrace',(x-.6,y,.62),(x+.6,y,1.1),.12,.12,group='TP01_Veranda')
for x in [-6.55,6.55]:beam('Lower return stretcher',(x,-4.9,.64),(x,4.9,.64),.13,.15,group='TP01_Veranda')
for i in range(65):
 x=-6.74+i*.211
 # The platform has no hidden interior floor: only the visible veranda ring.
 for y0,y1 in [(-5.10,-3.75),(3.75,5.10)]:beam('Front and back deck plank',(x,y0,1.265),(x,y1,1.265),.205,.073,group='TP01_Veranda')
for s in [-1,1]:
 for i in range(36):
  y=-3.68+i*.211;beam('Side deck plank',(s*5.38,y,1.265),(s*6.87,y,1.265),.204,.073,group='TP01_Veranda')
for y in [-5.12,5.12]:beam('Deep veranda fascia',(-6.98,y,1.18),(6.98,y,1.18),.14,.23,group='TP01_Veranda')
for x in [-6.94,6.94]:beam('Veranda return fascia',(x,-5.10,1.18),(x,5.10,1.18),.14,.23,group='TP01_Veranda')
collect(old,'Temple_Veranda_01')

# Five bays, restrained timber panels, closed central entrance; exterior only.
old=before()
for y in [-3.80,3.80]:
 for i in range(60):
  x=-5.32+i*.18
  beam('Fitted hall cedar boards',(x,y,1.33),(x,y,4.35),.177,.055,group='TP01_MainHall')
for x in [-5.40,5.40]:
 for i in range(42):
  y=-3.71+i*.181
  beam('Fitted side cedar boards',(x,y,1.33),(x,y,4.35),.055,.177,group='TP01_MainHall')
for y in [-3.87,3.87]:
 for x in [-5.40,-3.24,-1.08,1.08,3.24,5.40]:beam('Main facade pillar',(x,y,1.27),(x,y,4.59),.27,.29,group='TP01_MainHall')
 for z in [1.39,2.11,3.86,4.37]:beam('Continuous facade crossrail',(-5.55,y,z),(5.55,y,z),.16,.22,group='TP01_MainHall')
for x in [-5.44,5.44]:
 for y in [-3.80,-1.90,0,1.90,3.80]:beam('Main side pillar',(x,y,1.27),(x,y,4.57),.27,.28,group='TP01_MainHall')
 for z in [1.39,2.11,3.86,4.37]:beam('Hall return rail',(x,-3.9,z),(x,3.9,z),.17,.22,group='TP01_MainHall')
# Recessed shutter grilles with broad framed lower panels.
for cx in [-4.32,-2.16,2.16,4.32]:
 block('Opaque shutter backing',(cx,-3.863,2.99),(1.79,.042,1.30),'Timber','TP01_MainHall',.004)
 for i in range(12):beam('Refined shutter upright',(cx-.825+i*.15,-3.95,2.38),(cx-.825+i*.15,-3.95,3.63),.035,.035,group='TP01_MainHall')
 for z in [2.30,2.65,3.02,3.40,3.72]:beam('Shutter cross frame',(cx-.90,-3.975,z),(cx+.90,-3.975,z),.057,.061,group='TP01_MainHall')
for x in [-1.04,0,1.04]:beam('Closed entry heavy jamb',(x,-3.99,1.33),(x,-3.99,3.91),.12,.15,group='TP01_MainHall')
for side in [-1,1]:
 for z in [1.73,3.44]:
  beam('Door leaf dressed frame',(side*.09,-3.975,z),(side*.94,-3.975,z),.115,.055,group='TP01_MainHall')
  block('Forged door hinge',(side*.78,-4.015,z),(.36,.025,.065),'Iron','TP01_MainHall',.006)
 for z in [2.02,2.73]:block('Inset door panel',(side*.52,-3.94,z),(.76,.065,.51),'Timber','TP01_MainHall',.012)
 tube('Door pull ring',[(side*.17+.065*math.cos(j*math.tau/24),-4.046,2.54+.074*math.sin(j*math.tau/24)) for j in range(25)],.011,'Iron','TP01_MainHall',8)
# Pale lime-plaster spandrels break up the timber mass while preserving the kit.
for s in [-1,1]:
 for y in [-2.82,.98]:
  block('Side sheltered plaster field',(s*5.438,y,3.09),(.045,1.62,1.36),'Plaster','TP01_MainHall',.008)
  for z in [2.38,3.8]:beam('Side plaster framing',(s*5.49,y-.85,z),(s*5.49,y+.85,z),.10,.12,group='TP01_MainHall')
 for x in [s*4.33]:
  block('Front pale plaster infill',(x,-3.91,2.94),(1.64,.045,1.16),'Plaster','TP01_MainHall',.006)
  for z in [2.32,3.59]:beam('Front plaster border',(x-.88,-3.97,z),(x+.88,-3.97,z),.10,.13,group='TP01_MainHall')
def carved_arm(x,y,z):
 outline=[(-.67,.12),(-.46,.17),(-.28,.12),(.28,.12),(.46,.17),(.67,.12),(.70,.02),(.57,-.105),(.43,-.11),(.29,-.035),(.15,-.06),(0,-.19),(-.15,-.06),(-.29,-.035),(-.43,-.11),(-.57,-.105),(-.70,.02)]
 vv=[(x+a,y+d,z+b) for d in [-.11,.11] for a,b in outline];n=len(outline)
 ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 ob=mesh('Scalloped carved temple bracket',vv,ff,'Cedar',group='TP01_Brackets')
 mod=ob.modifiers.new('Carved bracket softened ridges','BEVEL');mod.width=.016;mod.segments=3
 ob.modifiers.new('Carved broad face normals','WEIGHTED_NORMAL')
# Broad round veranda columns on stone shoes, two visible tiers of bracket arms.
columns=[(x,y) for y in [-4.66,4.66] for x in [-6.15,-4.10,-2.05,2.05,4.10,6.15]]
columns += [(x,y) for x in [-6.15,6.15] for y in [-2.33,0,2.33]]
for x,y in columns:
 block('Column pedestal',(x,y,1.35),(.48,.48,.16),'Stone','TP01_MainHall',.026)
 tube('Temple round pillar',[(x,y,1.41),(x,y,4.24)],.165,'Cedar','TP01_MainHall',20)
 carved_arm(x,y-.04,4.14);carved_arm(x,y-.025,4.46)
 for z,w in [(4.23,.44),(4.42,.70),(4.58,.94)]:
  block('Stepped bracket capital',(x,y,z),(w,.31,.16),'Timber','TP01_Brackets',.014)
  block('Cross bracket arm',(x,y,z+.055),(.31,w,.13),'Timber','TP01_Brackets',.010)
 for s in [-1,1]:
  beam('Bracket rising shoulder',(x,y,3.99),(x+s*.46,y,4.43),.105,.12,group='TP01_Brackets')
  beam('Bracket return shoulder',(x,y,4.04),(x,y+s*.42,4.43),.10,.11,group='TP01_Brackets')
 # Major raised curl shape, deliberately no microscopic carving.
 for side in [-1,1]:
  tube('Restrained bracket scroll',[(x+side*(.12+.32*t),y-.185,4.31+.11*math.sin(t*math.pi)) for t in [i/12 for i in range(13)]],.037,'Timber','TP01_Brackets',6)
for y in [-4.66,4.66]:
 for z in [4.22,4.68]:beam('Continuous temple purlin',(-6.65,y,z),(6.65,y,z),.22,.20,group='TP01_MainHall')
for x in [-6.15,6.15]:beam('Continuous return purlin',(x,-4.93,4.68),(x,4.93,4.68),.22,.20,group='TP01_MainHall')
collect(old,'Temple_MainHall_01')

# A high front gable over a continuous curved hip skirt: the defining silhouette.
old=before()
def lower_point(side,u,t):
 # u follows the eave; t runs from eave to the upper rectangle.
 z=4.83+.76*t*t+.23*abs(2*u-1)**6*(1-t)
 if side in [0,2]:
  x=(u*2-1)*(7.80-3.55*t);y=(-1 if side==0 else 1)*(6.05-2.72*t)
 else:
  x=(-1 if side==1 else 1)*(7.80-3.55*t);y=(u*2-1)*(6.05-2.72*t)
 return Vector((x,y,z))
def upper_point(side,u,t):
 # Lower-edge to ridge; a restrained concave upward sweep.
 return Vector((side*4.25*(1-t),(2*u-1)*3.33,5.59+2.24*(.60*t+.40*t*t)))
def roof_surface(point,label,rows,width):
 # Authored shingle courses: real overlapping edges and per-shingle colour.
 vv=[];ff=[];uv=[];tones=[]
 for row in range(rows):
  lo=row/rows;hi=min(1.003,(row+1.18)/rows)
  n=max(4,round(width/.19));offset=.47 if row%2 else 0
  for i in range(n+1):
   ua=max(0,(i-offset)/n);ub=min(1,(i+1-offset)/n)
   if ub-ua<.001:continue
   start=len(vv);ox=random.random();oy=random.random();shade=random.uniform(.74,1.16)
   for lower in [0,1]:
    for j in range(4):
     t=lo+(hi-lo)*j/3
     for u in [ua,ub-.00035]:
      p=point(u,t);p.z+=.055+.039*(1-j/3)-.036*lower+random.uniform(-.005,.005)
      vv.append(p);uv.append((ox+(u-ua)*width*.65,oy+(t-lo)*1.2));tones.append(shade)
   for j in range(3):
    k=start+j*2;ff.append((k,k+1,k+3,k+2));ff.append((k+10,k+11,k+9,k+8))
   ff.extend([(start,start+8,start+9,start+1),(start+6,start+7,start+15,start+14)])
   for j in range(3):
    k=start+j*2;ff.extend([(k,k+2,k+10,k+8),(k+1,k+9,k+11,k+3)])
 ob=mesh(label,vv,ff,'Cedar',uv,'TP01_MainRoof')
 co=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for f in ob.data.polygons:
  for li in f.loop_indices:
   k=tones[ob.data.loops[li].vertex_index];co.data[li].color=(.55*k,.65*k,.76*k,1)
 ob.data.color_attributes.active_color=co;ob['authored_tint']=True
 return ob
def roof_bed(point,label):
 nx,nt=60,16;vv=[];ff=[]
 for lower in [0,1]:
  for j in range(nt+1):
   for i in range(nx+1):vv.append(point(i/nx,j/nt)+Vector((0,0,-.035-.16*lower)))
 n=(nx+1)*(nt+1)
 for j in range(nt):
  for i in range(nx):
   k=j*(nx+1)+i;ff.extend([(k,k+1,k+nx+2,k+nx+1),(n+k+nx+1,n+k+nx+2,n+k+1,n+k)])
 for i in range(nx):ff.append((i,n+i,n+i+1,i+1))
 ob=mesh(label,vv,ff,'Cedar',group='TP01_MainRoof');tint(ob,(.48,.56,.62))
for side in range(4):
 roof_bed(lambda u,t,s=side:lower_point(s,u,t),'Deep continuous hip roof bed')
 roof_surface(lambda u,t,s=side:lower_point(s,u,t),'TP01 sweeping hip shingles '+str(side),12,15.6 if side in [0,2] else 12.1)
 for lift,r in [(-.08,.115),(-.25,.085)]:tube('Layered sweeping eave fascia',[lower_point(side,i/64,0)+Vector((0,0,lift)) for i in range(65)],r,'Cedar','TP01_MainRoof',4)
 for lift in [-.015,-.067,-.121]:tube('Dense shingle cut eave layers',[lower_point(side,i/96,0)+Vector((0,0,lift)) for i in range(97)],.018,'Cedar','TP01_MainRoof',6)
 # Close under the eave with visible rectangular rafter tails.
 n=40 if side in [0,2] else 32
 for j in range(n+1):
  u=j/n
  pts=[lower_point(side,u,t)-Vector((0,0,.17)) for t in [k*.63/10 for k in range(11)]]
  tube('Closely spaced exposed rafter',pts,.063,'Timber','TP01_MainRoof',4)
for side in [-1,1]:
 roof_bed(lambda u,t,s=side:upper_point(s,u,t),'Deep upper roof bed')
 roof_surface(lambda u,t,s=side:upper_point(s,u,t),'TP01 upper gable shingles '+str(side),22,6.66)
# Swept hip corner curb timbers and front/back gable bargeboards.
for s in [-1,1]:
 for q in [-1,1]:
  pts=[Vector((s*(7.8-3.55*t),q*(6.05-2.72*t),4.83+.76*t*t+.23*(1-t)+.09)) for t in [i/24 for i in range(25)]]
  tube('Curved hip corner timber',pts,.093,'Timber','TP01_MainRoof',8)
for y in [-3.40,3.40]:
 for s in [-1,1]:
  pts=[Vector((s*4.29*(1-t),y,5.59+2.24*(.60*t+.40*t*t))) for t in [i/40 for i in range(41)]]
  tube('Deep sweeping gable bargeboard',pts,.12,'Timber','TP01_Gable',4)
  tube('Gable lower raised molding',[p-Vector((0,0,.22)) for p in pts],.055,'Timber','TP01_Gable',6)
 # Closed gable triangle, faced with timber boards and formal bracketed truss.
 for i in range(43):
  x=-4.10+i*.196;t=1-abs(x)/4.25;top=5.59+2.24*(.60*t+.40*t*t)-.15
  beam('Gable fitted board',(x,y,5.46),(x,y,top),.191,.068,group='TP01_Gable')
 for z,half in [(5.63,4.15),(6.18,2.77),(6.73,1.80)]:beam('Gable horizontal tier',(-half,y-.055,z),(half,y-.055,z),.13,.16,group='TP01_Gable')
 for x in [-2.25,0,2.25]:
  t=1-abs(x)/4.25;top=5.59+2.24*(.60*t+.40*t*t)
  beam('Gable principal upright',(x,y-.055,5.5),(x,y-.055,top-.10),.17,.14,group='TP01_Gable')
 for s in [-1,1]:beam('Gable rising truss',(s*3.36,y-.04,5.66),(s*.12,y-.04,7.61),.16,.15,group='TP01_Gable')
# Layered restrained ridge, no shrine's crossed chigi or palace ornaments.
for x,z,w in [(-.21,7.85,.13),(.21,7.85,.13),(0,7.99,.38),(0,8.12,.25)]:beam('Layered temple ridge',(x,-3.63,z),(x,3.63,z),w,.14,group='TP01_Ridge')
for y in [-3.72,3.72]:
 sign=-1 if y<0 else 1
 tube('Raised ridge end crest',[(0,y-sign*.34,7.96),(0,y,8.13),(0,y+sign*.20,8.37),(0,y+sign*.12,8.50)],.088,'Timber','TP01_Ridge',8)
 for s in [-1,1]:tube('Restrained ridge scroll',[(s*.18,y,7.93),(s*.38,y+sign*.10,8.05),(s*.34,y+sign*.17,8.22),(s*.20,y+sign*.15,8.26)],.055,'Timber','TP01_Ridge',6)
for y in [-2.6,-1.3,0,1.3,2.6]:beam('Ridge joint strap',(-.32,y,8.09),(.32,y,8.09),.09,.065,group='TP01_Ridge')
collect(old,'Temple_MainRoof_01')

# Useful reusable 2 m veranda rail with its origin at the left ground end.
old=before()
for x in [0,2]:
 beam('Railing dressed post',(x,0,0),(x,0,.86),.125,group='TP01_Railing')
 block('Railing softened cap',(x,0,.88),(.20,.20,.095),group='TP01_Railing',bevel=.017)
for z in [.20,.61,.79]:beam('Clean veranda crossrail',(-.05,0,z),(2.05,0,z),.075,.10,group='TP01_Railing')
for x in [.4,.8,1.2,1.6]:beam('Simple square baluster',(x,0,.17),(x,0,.78),.053,group='TP01_Railing')
collect(old,'Temple_Railing_01')
old=before()
for i in range(8):
 y=-2.30+i*.30;h=.16*(i+1)
 for j in range(4):block('Broad worn entrance tread',(-1.32+j*.88,y,h/2),(.871,.315,h),'Stone','TP01_Steps',.023)
 for s in [-1,1]:block('Stair stone shoulder',(s*1.92,y,h/2),(.30,.33,h+.09),'Stone','TP01_Steps',.022)
collect(old,'Temple_Steps_01')

# Five static linen curtains. Subtle folds and a simple circular three-leaf crest.
old=before()
for cx in [-3.9,0,3.9]:
 nx=24;nz=12;vv=[];ff=[];uv=[]
 for j in range(nz+1):
  t=j/nz
  for i in range(nx+1):
   u=i/nx;x=cx+(u-.5)*1.74;z=3.97-t*.93-.055*math.sin(u*math.pi)**2
   if j==nz:z+=.045*math.cos(u*math.tau*2)
   y=-4.71-.08*math.sin(u*math.pi*6)*(.45+.55*t)
   vv.append((x,y,z));uv.append((u,t))
 for j in range(nz):
  for i in range(nx):
   a=j*(nx+1)+i;ff.append((a,a+1,a+nx+2,a+nx+1))
 ob=mesh('Hanging unbleached temple curtain',vv,ff,'Cloth',uv,'TP01_Curtains');so=ob.modifiers.new('Woven hem thickness','SOLIDIFY');so.thickness=.012;tint(ob,(1.38,1.36,1.26))
 for x in [cx-.70,cx+.70]:tube('Linen suspension loop',[(x,-4.67,4.04),(x,-4.74,3.97)],.012,'Rope','TP01_Curtains',6)
 # Printed crest follows the curtain's front surface; geometry stands in for ink.
 def cloth_y(x):return -4.728-.08*math.sin(((x-cx)/1.74+.5)*math.pi*6)*.73
 tube('Temple circular ink crest',[(cx+.24*math.cos(a),cloth_y(cx+.24*math.cos(a)),3.52+.24*math.sin(a)) for a in [i*math.tau/64 for i in range(65)]],.016,'Ink','TP01_Curtains',5)
 for angle in [math.pi/2,math.pi/2+math.tau/3,math.pi/2+2*math.tau/3]:
  center=Vector((cx+.105*math.cos(angle),0,3.52+.105*math.sin(angle)))
  verts=[(center.x,cloth_y(center.x)-.004,center.z)]+[(center.x+.081*math.cos(a),cloth_y(center.x+.081*math.cos(a))-.004,center.z+.081*math.sin(a)) for a in [i*math.tau/24 for i in range(24)]]
  mesh('Restrained ink crest leaf',verts,[(0,i+1,(i+1)%24+1) for i in range(24)],'Ink',group='TP01_Curtains')
beam('Curtain suspension rod',(-5.25,-4.65,4.03),(5.25,-4.65,4.03),.048,group='TP01_Curtains')
collect(old,'Temple_Curtains_01')

sys.path.insert(0,str(ART/'Scripts'))
from temple_props import build_props
prop_info=build_props(globals())
# Reuse the authored shrine lantern mesh verbatim, resetting its arrangement origin.
with bpy.data.libraries.load(str(ART.parent/'SmallShrine01/SmallShrine01.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n=='StoneLantern_01']
lantern=b.objects[0];src.objects.link(lantern);lantern.data=lantern.data.copy();lantern.matrix_world.identity()
for v in lantern.data.vertices:v.co-=Vector((-2.05,-1.90,0))
lantern['authored_tint']=True;lantern['reused_from']='SmallShrine01/StoneLantern_01';modules['StoneLantern_01']=[lantern]

old=before()
# Open communal precinct, with a continuous clear route from gate to stairs.
# The approach sits directly on the settlement terrain; no rectangular ground card.
for j in range(11):
 y=-9.6+j*.47
 for s in [-1,1]:block('Formal approach stepping stone',(s*.67,y,.059),(1.30,.445,.095),'Stone','TP01_Approach',.027)
# Discreet boundary stones and grass tufts beyond the main sightline.
for x,y in [(-8.2,6.9),(-7.9,-4.7),(8.5,6.5),(11.5,-7.1),(8.0,-8.7)]:
 fieldstone('Precinct weathered stone',(x,y,.10),(.32,.26,.18))
 for k in range(9):
  a=random.random()*math.tau;r=random.uniform(.15,.5);bx=x+math.cos(a)*r;by=y+math.sin(a)*r;h=random.uniform(.13,.36)
  mesh('Restrained boundary grass',[(bx-.017,by,.025),(bx+.017,by,.025),(bx+math.cos(a)*.10,by+math.sin(a)*.10,h)],[(0,1,2)],'Leaf',group='TP01_Approach')
collect(old,'Temple_Approach_01')

# The existing manor planting is reused as a quiet framing element at two corners.
with bpy.data.libraries.load(str(ART.parent/'Manor01/Manor01.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith('MN01_GardenElements_') and '/' not in n]
plant_sources=[o for o in b.objects if o and o.type=='MESH'];planting=[]
for source in plant_sources:
 for x,y,s in [(-8.05,5.8,1.60),(9.35,6.5,1.82)]:
  ob=source.copy();ob.data=source.data.copy();src.objects.link(ob);ob.matrix_world.identity()
  for v in ob.data.vertices:v.co=v.co*s+Vector((x,y,0))
  ob['authored_tint']=True;ob['reused_from']='Manor01/MN01_GardenElements';planting.append(ob)
for source in plant_sources:bpy.data.objects.remove(source,do_unlink=True)
if planting:modules['Temple_Planting_01']=planting

# Consolidate into useful editable components, preserving source modular origins.
for key,obs in list(modules.items()):
 buckets={}
 for ob in obs:
  if not ob.get('authored_tint') and not ob.get('temple_tint'):
   co=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
   tone=random.uniform(.90,1.07)
   palette={'Cedar':(.65,.68,.73),'Timber':(.86,.76,.59),'Plaster':(1.20,1.18,1.11),'Stone':(.86,.86,.80),'Iron':(.65,.68,.61),'Rope':(.88,.82,.69),'Cloth':(1.35,1.32,1.23),'Ink':(.16,.16,.16),'Dirt':(.97,.95,.88),'Leaf':(.60,.66,.38)}
   for f in ob.data.polygons:
    family=ob.data.materials[f.material_index].name.split('_',1)[-1].split('.')[0];rgb=palette.get(family,(1,1,1))
    for li in f.loop_indices:co.data[li].color=(*(c*tone for c in rgb),1)
   ob.data.color_attributes.active_color=co
  label=next((g for g,items in groups.items() if ob in items),key)
  buckets.setdefault(label,[]).append(ob)
 joined=[]
 for category,parts in buckets.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:
   ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=key+' / '+category
  scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  joined.append(ob)
 modules[key]=joined
 print('TEMPLE_COMPONENT',key,len(joined),flush=True)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from temple_finish import finish_materials, export_linear as fbx
finish_materials(list(src.objects))
for key,obs in modules.items():
 if key=='StoneLantern_01':continue
 for ob in obs:ob.modifiers.new('Export triangles','TRIANGULATE')
 fbx(ART/'Exports'/(key+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangles'])
def place(key,loc=(0,0,0),yaw=0,scale=(1,1,1),name=None):
 name=name or key+'_'+str(len(instances));instances.append({'name':name,'mesh':key,'location':list(loc),'rotation_degrees':yaw,'scale':list(scale)})
 for source in modules[key]:
  ob=source.copy();ob.data=source.data;layout.objects.link(ob);ob.name=name+' / '+source.name;ob.location=loc;ob.rotation_euler.z=math.radians(yaw);ob.scale=scale
for key in ['Temple_MainHall_01','Temple_MainRoof_01','Temple_Foundation_01','Temple_Veranda_01','Temple_Curtains_01']:place(key,(0,2.5,0))
place('Temple_Steps_01',(0,-2.6,0))
for x in [-6.3,-4.25,2.25,4.3]:place('Temple_Railing_01',(x,-2.45,1.3))
for x in [-6.3,-4.25,-2.2,-.15,1.9,3.95]:place('Temple_Railing_01',(x,7.45,1.3))
for x in [-6.7,6.7]:
 for y in [-2.3,-.25,1.8,3.85,5.9]:place('Temple_Railing_01',(x,y,1.3),90)
place('TempleGate_01',(0,-10,0))
place('TempleBellPavilion_01',(10,-3.4,0))
place('TempleBell_01',(10,-3.4,1.3))
for x,y in [(-2.7,-5.8),(2.7,-5.8),(-3.1,-10.2),(3.1,-10.2)]:place('StoneLantern_01',(x,y,0),0,(1.07,1.07,1.07))
for x in [-7.3,-5.3,-3.3,3.3,5.3,7.3,9.3,11.3]:place('Temple_Fence_01',(x,-9.5,0))
place('Temple_Approach_01')
if 'Temple_Planting_01' in modules:place('Temple_Planting_01')
collision={'Temple_MainHall_01':[[0,0,2.9,10.8,7.6,3.2]],'Temple_Foundation_01':[[0,0,.23,10.7,7.5,.45]],'Temple_Steps_01':[[0,-1.25,.64,3.82,2.7,1.28]]}
collision['TempleGate_01']=[[x,y,1.42,.34,.34,2.84] for x in [-2.15,2.15] for y in [-.39,.39]]
collision['TempleBellPavilion_01']=[[x,y,1.45,.30,.30,2.9] for x in [-1.02,1.02] for y in [-1.02,1.02]]
if isinstance(prop_info,dict):collision.update(prop_info.get('collision_boxes',{}))
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'Temple_01','units':'metres','instances':instances,'collision_boxes':collision},indent=2)+'\n')
# Bake only the combined export copy so repeated linked rails keep their slots.
bpy.context.view_layer.update()
copies=[]
for ob in list(layout.objects):
 copy=ob.copy();copy.data=ob.data.copy();layout.objects.link(copy)
 copy.data.transform(copy.matrix_world);copy.matrix_world.identity();copies.append(copy)
bpy.ops.object.select_all(action='DESELECT')
for ob in copies:ob.select_set(True)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();combined=bpy.context.object
combined.name='Temple_01';combined.modifiers.new('Export triangles','TRIANGULATE')
fbx(ART/'Exports/Temple_01.fbx',[combined]);bpy.data.objects.remove(combined,do_unlink=True)
src.hide_render=True;src.hide_viewport=True
# Daylight source review. No studio geometry is included in any runtime export.
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review earth only'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground);ground.location.z=-.026
gm=bpy.data.materials.new('Review neutral earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.135,.093,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Temple rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.46,.58,.80,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32
for name,loc,power,size in [('Warm facade daylight',(-10,-16,18),4200,10),('Front sky fill',(8,-10,12),2200,12)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Afternoon sun','SUN');o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.58,-.65,-.95);d.energy=3.6;d.angle=.075;d.color=(1,.92,.78)
cd=bpy.data.cameras.new('Temple three quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(-25,-33,6.4);cam.rotation_euler=(Vector((1,-.8,3.1))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=50;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');scene['asset_note']='Temple_01: one exterior Buddhist temple group. Closed hall, raised veranda, swept shingle roof, roofed gate, bell pavilion. Existing SHŌEN materials and shrine lantern reused.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Temple01.blend'))
print('TEMPLE_SAVED',len(modules),'modules',len(instances),'instances',flush=True)
scene.render.filepath=str(OUT/'temple-three-quarter.png');bpy.ops.render.render(write_still=True)
print('TEMPLE_COMPLETE',flush=True)
