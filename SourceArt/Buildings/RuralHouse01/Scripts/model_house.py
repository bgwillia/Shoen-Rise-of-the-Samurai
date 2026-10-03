"""RuralHouse01: one authored, exterior-only Blender modeling pass."""
from pathlib import Path
import sys, math, random, json
import bpy, bmesh
from mathutils import Vector

ART=Path(__file__).resolve().parents[1]
ROOT=ART.parents[2]
OUT=ROOT/'artifacts/ruralhouse01'
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
random.seed(1180)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def collection(name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
src=collection('RuralHouse_01 • modular exterior')
studio=collection('Review only • ground, cameras and scale figure')
groups={}
mats={}
for name,col in [('Thatch',(.29,.205,.12)),('Timber',(.105,.070,.041)),('Plaster',(.48,.405,.30)),('Stone',(.22,.215,.18)),('Rope',(.39,.28,.15))]:
 m=bpy.data.materials.new('RH01_'+name);m.diffuse_color=(*col,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.87
 for suffix in ['BaseColor','Normal','ORM']:
  path=ART/'Textures'/f'RH01_{name}_{suffix}.png'
  if not path.exists():continue
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path));tex.image.pack()
  if suffix=='BaseColor':l.new(tex.outputs['Color'],p.inputs['Base Color'])
  else:
   tex.image.colorspace_settings.name='Non-Color'
   if suffix=='Normal':
    normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8;l.new(tex.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
   else:
    sep=n.new('ShaderNodeSeparateColor');l.new(tex.outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],p.inputs['Roughness'])
 mats[name]=m
def mesh(name,verts,faces,mat,uv=None,group=None):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 ob=bpy.data.objects.new(name,data);src.objects.link(ob);data.materials.append(mats[mat])
 layer=data.uv_layers.new(name='UVMap')
 for poly in data.polygons:
  for li in poly.loop_indices:
   v=data.vertices[data.loops[li].vertex_index].co
   layer.data[li].uv=uv[data.loops[li].vertex_index] if uv else (v.x*.8+v.y*.3,v.z*.7)
 if group:groups.setdefault(group,[]).append(ob)
 return ob
def beam(name,a,b,width,depth=None,mat='Timber',group='Wall_Frame',rough=.006):
 a=Vector(a);b=Vector(b);t=(b-a).normalized();q=t.cross(Vector((0,0,1)))
 if q.length<.1:q=t.cross(Vector((0,1,0)))
 q.normalize();r=t.cross(q).normalized();depth=depth or width
 vv=[];uv=[];faces=[]
 # Clipped corners and a gently bowed middle give hand-hewn surfaces.
 outline=[(-.38,-.5),(.38,-.5),(.5,-.38),(.5,.38),(.38,.5),(-.38,.5),(-.5,.38),(-.5,-.38)]
 offsets=[random.uniform(-rough,rough) for _ in range(8)]
 for j in range(3):
  c=a.lerp(b,j/2)+q*(math.sin(j*math.pi/2)*random.uniform(-rough,rough))
  for i,(x,y) in enumerate(outline):
   vv.append(c+q*(x*width+offsets[i])+r*(y*depth+offsets[(i+3)%8]));uv.append((i/8,(b-a).length*j/2/.8))
 for j in range(2):
  for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
 faces.extend([tuple(reversed(range(8))),tuple(range(16,24))])
 return mesh(name,vv,faces,mat,uv,group)
def tube(name,points,radius,mat='Timber',group='Roof_Ridge',sides=8):
 pts=[Vector(p) for p in points];vv=[];uv=[];ff=[];dist=0
 for j,p in enumerate(pts):
  if j:dist+=(p-pts[j-1]).length
  t=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();u=t.cross(Vector((0,0,1)))
  if u.length<.01:u=t.cross(Vector((0,1,0)))
  u.normalize();v=t.cross(u).normalized()
  for i in range(sides):
   angle=math.tau*i/sides;rr=radius*(1+.05*math.sin(i*2.3+j));vv.append(p+rr*(math.cos(angle)*u+math.sin(angle)*v));uv.append((i/sides,dist/.24))
 for j in range(len(pts)-1):
  for i in range(sides):ff.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
 ff.extend([tuple(reversed(range(sides))),tuple(range((len(pts)-1)*sides,len(pts)*sides))])
 ob=mesh(name,vv,ff,mat,uv,group)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
def lash(name,p,axis='Y',radius=.09,turns=3):
 p=Vector(p);pts=[]
 for j in range(turns*14+1):
  t=j/14*math.tau;along=(j/(turns*14)-.5)*turns*.024
  v=(radius*math.cos(t),along,radius*math.sin(t)) if axis=='Y' else (along,radius*math.cos(t),radius*math.sin(t))
  pts.append(p+Vector(v))
 return tube(name,pts,.012,'Rope','Rope_Lashings',6)
def stone(name,p,size):
 # Broad bedded faces and rounded arrises: hand-set field masonry, not pebbles.
 # Existing perimeter half-extents came from round stones; reduce their footprint
 # so rectangular blocks retain narrow joints at the 0.395 / 0.405 m spacing.
 sx,sy,sz=size
 if name=='Hand laid foundation stone':sx*=.78;sy*=.78;sz*=.86
 verts=[]
 for z in [-1,1]:
  for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
   verts.append((x*sx+random.uniform(-.025,.025)*min(sx,.3),
                 y*sy+random.uniform(-.04,.04)*min(sy,.3),
                 z*sz+random.uniform(-.035,.035)*sz))
 faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 ob=mesh(name,verts,faces,'Stone',group='Foundation');ob.location=p
 ob.rotation_euler.z=random.uniform(-.025,.025)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
 bpy.context.view_layer.objects.active=ob
 bevel=ob.modifiers.new('Soft weathered stone edges','BEVEL')
 bevel.width=min(sx,sy,sz)*random.uniform(.22,.30);bevel.segments=3
 bevel.profile=.58;bevel.harden_normals=True
 bpy.ops.object.modifier_apply(modifier=bevel.name)
 for poly in ob.data.polygons:poly.use_smooth=True
 normal=ob.modifiers.new('Broad bedded stone faces','WEIGHTED_NORMAL')
 normal.keep_sharp=True;normal.weight=70
 bpy.ops.object.modifier_apply(modifier=normal.name)
 layer=ob.data.uv_layers.active
 for poly in ob.data.polygons:
  axis=max(range(3),key=lambda i:abs(poly.normal[i]))
  for li in poly.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co
   layer.data[li].uv=((v.y,v.z) if axis==0 else (v.x,v.z) if axis==1 else (v.x,v.y))
 return ob

# Low perimeter foundation; the center remains empty, without floor or room geometry.
for side in [-1,1]:
 for i in range(10):stone('Hand laid foundation stone',(side*2.00,-1.78+i*.395,.16),(random.uniform(.22,.28),.255,random.uniform(.14,.21)))
 for i in range(10):stone('Hand laid foundation stone',(-1.83+i*.405,side*1.88,.16),(.25,.23,random.uniform(.14,.2)))
for y in [-1.89,1.89]:beam('Perimeter sill',(-2.08,y,.38),(2.08,y,.38),.17,group='Wall_Frame')
for x in [-2,2]:beam('Perimeter sill',(x,-1.94,.38),(x,1.94,.38),.17,group='Wall_Frame')
for x in [-2,2]:
 for y in [-1.88,1.88]:
  beam('Main hewn corner post',(x,y,.27),(x,y,2.39),.175,group='CornerPosts')
for y in [-1.89,1.89]:
 for z in [.62,2.10,2.32]:beam('Horizontal wall tie',(-2.11,y,z),(2.11,y,z),.12,group='Wall_Frame')
for x in [-2,2]:
 for z in [.62,2.10,2.32]:beam('Horizontal wall tie',(x,-1.97,z),(x,1.97,z),.12,group='Wall_Frame')

def panel(name,a,b,z0=.46,z1=2.25):
 a=Vector((*a,z0));b=Vector((*b,z0));verts=[];uv=[];faces=[];N=8;M=8
 normal=Vector((b.y-a.y,a.x-b.x,0)).normalized()
 for j in range(M+1):
  for i in range(N+1):
   p=a.lerp(b,i/N);p.z=z0+(z1-z0)*j/M
   p+=normal*(.004*math.sin(i*1.4+j*.7)+random.uniform(-.003,.003))
   verts.append(p);uv.append((i/N*(b-a).length/.95,j/M*(z1-z0)/.95))
 for j in range(M):
  for i in range(N):k=j*(N+1)+i;faces.append((k,k+1,k+N+2,k+N+1))
 ob=mesh(name,verts,faces,'Plaster',uv,'Wall_Panel_A' if (b-a).length<1.3 else 'Wall_Panel_B')
 for p in ob.data.polygons:p.use_smooth=True
 return ob
# Separate infill panels with a truly closed front door and opaque shutter backs.
for a,b in [((-1.97,-1.875),(-.65,-1.875)),((.65,-1.875),(1.97,-1.875))]:panel('Front clay plaster infill',a,b)
panel('Lintel plaster',(-.65,-1.875),(.65,-1.875),2.02,2.26)
for y in [-1.875,1.875]:
 for x in [-.69,.69]:beam('Front / back upright',(x,y,.35),(x,y,2.32),.125,group='Wall_Frame')
for a,b in [((2,1.87),(.68,1.87)),((.68,1.87),(-.68,1.87)),((-.68,1.87),(-2,1.87))]:panel('Rear plaster infill',a,b)
for side in [-1,1]:
 x=side*1.995
 for y in [-.66,.65]:beam('Side hewn upright',(x,y,.35),(x,y,2.31),.13,group='Wall_Frame')
 for ya,yb in [(-1.84,-.66),(-.66,.65),(.65,1.84)]:
  panel('Side plaster infill',(x,yb) if side<0 else (x,ya),(x,ya) if side<0 else (x,yb))
# Door, head and thresholds. No interior slab behind the shell.
for x in [-.67,.67]:beam('Door jamb',(x,-1.97,.36),(x,-1.97,2.12),.14,group='DoorFrame')
for z in [.39,2.03]:beam('Door threshold / head',(-.73,-1.98,z),(.73,-1.98,z),.16,group='DoorFrame')
for i in range(8):
 x=-.565+i*.161;beam('Closed weathered door board',(x,-1.92,.44),(x,-1.92,1.99),.157,.060,group='Door',rough=.003)
for z in [.64,1.8]:beam('Door face rail',(-.63,-1.965,z),(.63,-1.965,z),.058,.08,group='Door')
beam('Small door latch',(.34,-2.019,1.16),(.52,-2.019,1.16),.033,group='Door')
for side in [-1,1]:
 x=side*2.055;y=.04
 # Solid shutter panels make the little recess dark without glass or rooms.
 for i in range(6):beam('Opaque shutter backing',(x,y-.41+i*.162,1.24),(x,y-.41+i*.162,1.87),.158,.05,group='Window',rough=.002)
 for yy in [y-.50,y+.50]:beam('Window jamb',(x+side*.045,yy,1.19),(x+side*.045,yy,1.94),.072,group='Window')
 for z in [1.19,1.94]:beam('Window sill',(x+side*.05,y-.54,z),(x+side*.05,y+.54,z),.087,group='Window')
 for i in range(7):beam('Window grille',(x+side*.082,y-.4+i*.133,1.27),(x+side*.082,y-.4+i*.133,1.86),.025,group='Window',rough=.001)
 for z in [1.44,1.70]:beam('Window lattice cross rail',(x+side*.09,y-.45,z),(x+side*.09,y+.45,z),.028,group='Window',rough=.001)

# Exterior porch: narrow weathered platform, supported by stones, and shallow plank awning.
for x in [-1.54,1.54]:
 stone('Porch foot stone',(x,-2.48,.13),(.24,.23,.16))
 beam('Porch upright',(x,-2.48,.22),(x,-2.48,2.10),.11,group='Porch_Posts')
for y in [-2.47,-2.03]:beam('Porch support joist',(-1.7,y,.31),(1.7,y,.31),.14,group='Porch_Beam')
for i in range(15):
 x=-1.63+i*.232;beam('Exterior porch plank',(x,-2.54,.43),(x,-1.99,.43),.227,.065,group='Porch_Platform',rough=.004)
stone('Entry upper stone tread',(0,-2.69,.22),(.65,.225,.11))
stone('Entry lower shallow slab',(0,-3.02,.075),(.72,.21,.075))
beam('Awning front tie',(-1.72,-2.52,2.04),(1.72,-2.52,2.04),.12,group='Porch_Beam')
for x in [-1.55,-.8,0,.8,1.55]:beam('Awning rafter',(x,-1.86,2.33),(x,-2.72,2.045),.073,group='Porch_Roof')
for i in range(19):
 x=-1.74+i*.193;beam('Weathered awning board',(x,-1.86,2.385),(x,-2.73,2.08+random.uniform(-.013,.013)),.188,.052,group='Porch_Roof',rough=.004)
for x in [-1.54,1.54]:
 beam('Porch knee brace',(x,-2.48,1.66),(x*.73,-2.48,2.045),.068,group='Porch_Beam')
 lash('Porch tied joint',(x,-2.48,2.05),'X',.087,3)

# Dominant hipped thatch roof. Four convex slopes, broken eaves, short long-axis ridge.
facets=[((-2.6,-2.4,2.34),(-2.6,2.4,2.34),(0,-1.20,4.13),(0,1.20,4.13)),
        ((2.6,2.4,2.34),(2.6,-2.4,2.34),(0,1.20,4.13),(0,-1.20,4.13)),
        ((2.6,-2.4,2.34),(-2.6,-2.4,2.34),(0,-1.20,4.13),(0,-1.20,4.13)),
        ((-2.6,2.4,2.34),(2.6,2.4,2.34),(0,1.20,4.13),(0,1.20,4.13))]
for fi,coords in enumerate(facets):
 a,b,c,d=map(Vector,coords);normal=(b-a).cross(c-a).normalized()
 if normal.z<0:normal=-normal
 def surf(u,v):
  p=a.lerp(b,u).lerp(c.lerp(d,u),v)
  # Adjacent hip slopes share their boundary exactly; the soft convex shape
  # fades to zero there so the roof stays one continuous exterior surface.
  p+=normal*((.115+.008*math.sin(u*36+v*8))*math.sin(v*math.pi)*math.sin(u*math.pi))
  p.z+=(1-v)*(.035*(abs(p.x)/2.6)**3+.025*(abs(p.y)/2.4)**3+.013*math.sin(p.x*5.3+p.y*3.2))
  return p
 nu=40;nv=18;vv=[];uv=[];ff=[]
 for j in range(nv+1):
  v=j/nv
  for i in range(nu+1):
   u=i/nu;p=surf(u,v)
   if j==0:p+=normal*random.uniform(-.015,.02);p.z+=random.uniform(-.037,.018)
   vv.append(p);uv.append((u*((b-a).length*(1-v)+(d-c).length*v)/1.65,(1-v)*3.0/1.65))
 for j in range(nv):
  for i in range(nu):k=j*(nu+1)+i;ff.append((k,k+1,k+nu+2,k+nu+1))
 ff=[tuple(reversed(f)) for f in ff]
 ob=mesh('Bulk thatch slope %d'%fi,vv,ff,'Thatch',uv,'Roof_Main')
 solid=ob.modifiers.new('Thick thatch edge','SOLIDIFY');solid.thickness=.30;solid.offset=-1
 # Rows of broad irregular straw bundles, 4 faces per clump; fine straw is textured.
 for row in range(10):
  v0=row/10;v1=min(1,v0+random.uniform(.15,.22));width=(b-a).length*(1-v0)+(d-c).length*v0
  count=max(3,int(width/.10))
  for k in range(count):
   u=(k+random.uniform(-.12,.12))/count;du=random.uniform(1.13,1.35)/count
   low=max(0,v0+random.uniform(-.036,.024));high=min(.996,v1+random.uniform(-.016,.023))
   verts=[];uvs=[]
   for jj,v in enumerate([low,low+(high-low)*.32,high]):
    for ii in range(5):
     uu=u+du*ii/4
     p=surf(uu,v)+normal*([.016,.027,.003][jj]+(.004 if ii%2 else 0))
     if jj==0:p.z+=random.uniform(-.036,.018)
     verts.append(p);uvs.append((uu*width/1.65,(1-v)*3/1.65))
   faces=[]
   for j in range(2):
    for i in range(4):q=j*5+i;faces.append((q+5,q+6,q+1,q))
   bundle=mesh('Layered dry thatch bundle',verts,faces,'Thatch',uvs,'Eaves' if row==0 else 'Roof_ThatchLayers')
   for p in bundle.data.polygons:p.use_smooth=True
 # A textured hanging fringe follows the full depth of the thatch, closing
 # the rough edge without exposing a straight timber-sized tube perimeter.
 fringe_v=[];fringe_uv=[];fringe_f=[];segments=int((b-a).length/.032)
 for j in range(3):
  for k in range(segments+1):
   u=k/segments
   if j==0:p=surf(u,.074)+normal*.022
   elif j==1:p=surf(u,.007)+normal*.019-Vector((0,0,.065))
   else:p=surf(u,0)+normal*.007-Vector((0,0,random.uniform(.155,.235)))
   fringe_v.append(p);fringe_uv.append((u*(b-a).length/1.65,.33-j*.165))
 for j in range(2):
  for k in range(segments):q=j*(segments+1)+k;fringe_f.append((q,q+1,q+segments+2,q+segments+1))
 fringe=mesh('Dense hanging thatch fringe',fringe_v,fringe_f,'Thatch',fringe_uv,'Eaves')
 for p in fringe.data.polygons:p.use_smooth=True
 # A dense bundled edge supplies the thick silhouette. These are clusters,
 # not a strand/hair system; the surface texture carries fine reed shafts.
 length=(b-a).length
 for k in range(int(length/.038)):
  u=(k+.5)/int(length/.038);p=surf(u,0);q=surf(u,random.uniform(.050,.12))
  drop=random.uniform(.11,.24)
  aa=p-Vector((0,0,drop));bb=q-normal*.055
  tube('Eave reed bundle',[aa,aa.lerp(bb,.35)+normal*.009,bb],random.uniform(.005,.012),'Thatch','Eaves',5)
  if k%2==0:
   for tip in [-1,1]:
    start=aa+Vector((random.uniform(-.02,.02),random.uniform(-.02,.02),random.uniform(-.045,.015)))
    tube('Broken bundled straw tip',[start,start.lerp(bb,.36)],random.uniform(.002,.004),'Thatch','Eaves',4)
 # The timber ring is tucked into the underside of the heavy thatch.
 tube('Dark eave support',[a.lerp(c,.035)-Vector((0,0,.24)),b.lerp(d,.035)-Vector((0,0,.24))],.052,'Timber','Eaves')
 for k in range(13):
  u=(k+.5)/13;p=surf(u,0);q=surf(u,.16)
  beam('Short exposed rafter',p-Vector((0,0,.26)),q-Vector((0,0,.24)),.061,group='Eaves')
# Weathered ridge poles, pegs, ridge saddle and visible hemp binding.
for x in [-.18,.18]:tube('Long ridge restraint',[(x,-1.51,4.23),(x,-.7,4.28),(x,.6,4.27),(x,1.51,4.22)],.060)
tube('Central straw ridge',[ (0,-1.33,4.13),(0,0,4.20),(0,1.33,4.13)],.145,'Thatch')
for y in [-1.28,-.72,0,.72,1.28]:
 tube('Ridge crossbar',[(-.40,y,4.29),(.4,y,4.29)],.043)
 for x in [-.205,.205]:
  tube('Ridge upright pin',[(x,y,4.19),(x,y,4.42+random.uniform(-.018,.018))],.024)
  lash('Ridge hemp fastening',(x,y,4.285),'Y',.084,3)
# Small front/rear gable markers strengthen the silhouette without ornate decoration.
for side in [-1,1]:
 y=side*1.39
 for sign in [-1,1]:beam('Plain ridge fork',(sign*.43,y,3.82),(-sign*.055,y,4.27),.058,group='Roof_Ridge')
 # Opaque, inset timber triangle underneath the ridge; exterior closure only.
 tri=[(-.33,y+side*.008,3.88),(.33,y+side*.008,3.88),(0,y+side*.008,4.22)]
 mesh('Small closed timber gable',tri,[(0,1,2) if side<0 else (2,1,0)],'Timber',[(0,0),(1,0),(.5,1)],'Roof_Ridge')
 beam('Gable foot tie',(-.36,y+side*.027,3.86),(.36,y+side*.027,3.86),.048,group='Roof_Ridge')

# Pegged mortise joints and restrained weather splits on prominent hewn beams.
for x in [-2,-.69,.69,2]:
 for y in [-1.965,1.965]:
  for z in [.63,2.10]:
   side=-1 if y<0 else 1
   tube('Timber joint peg',[(x,y,z),(x,y+side*.029,z)],.014,'Timber','Wall_Frame',7)

# A single reusable exterior rack beside the door, and a compact rear drying fence.
def rack(cx,cy,width,height):
 for x in [cx-width/2,cx+width/2]:beam('Rack upright',(x,cy,.17),(x,cy,height),.054,group='ExteriorRack')
 for z in [.30,height-.10]:beam('Rack cross rail',(cx-width*.59,cy,z),(cx+width*.59,cy,z),.045,group='ExteriorRack')
 for i in range(7):beam('Rack thin stave',(cx-width*.46+i*width*.153,cy-.027,.20),(cx-width*.46+i*width*.153,cy-.027,height+.015),.028,group='ExteriorRack',rough=.002)
 for x in [cx-width/2,cx+width/2]:lash('Rack tie',(x,cy,height-.1),'X',.045,2)
rack(1.32,-2.16,.48,1.05);rack(.80,2.17,1.26,1.20)
# One modest exterior timber tub under the porch edge.
cx=-1.14;cy=-2.13
for i in range(16):
 t=math.tau*i/16;vv=[];uv=[];ff=[]
 for j in range(5):
  z=.47+.565*j/4;rr=.183+.038*math.sin(math.pi*j/4)
  for aa,off in [(t-.182,0),(t+.182,0),(t+.182,-.022),(t-.182,-.022)]:
   vv.append((cx+(rr+off)*math.cos(aa),cy+(rr+off)*math.sin(aa),z));uv.append((.11*(aa-t+.2),j*.18))
 for j in range(4):
  for k in range(4):ff.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
 ff.extend([(3,2,1,0),(16,17,18,19)])
 stave=mesh('Curved storage tub stave',vv,ff,'Timber',uv,'ExteriorTub')
 for p in stave.data.polygons:p.use_smooth=True
for z,rr in [(.54,.201),(.91,.208)]:
 tube('Hemp tub binding',[(cx+rr*math.cos(math.tau*i/40),cy+rr*math.sin(math.tau*i/40),z) for i in range(41)],.018,'Rope','ExteriorTub',6)
for i in range(5):
 x=(i-2)*.073;length=math.sqrt(max(0,.19**2-x*x))
 beam('Closed tub lid',(cx+x,cy-length,1.045),(cx+x,cy+length,1.045),.071,.029,group='ExteriorTub',rough=.001)

# Keep named modular source objects, joining only each logical component group.
for name,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in objects:
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='RH01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 # Consistent outward normals for solid timber and thin, upward-facing roof patches.
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if name.startswith('Wall_Panel'):
  for f in bm.faces:
   c=f.calc_center_median()
   if f.normal.x*c.x+f.normal.y*c.y<0:f.normal_flip()
 if name=='Roof_ThatchLayers':
  for f in bm.faces:
   if f.normal.z<0:f.normal_flip()
 bm.to_mesh(ob.data);bm.free()
 ob['scope']='Exterior only; reusable RuralHouse01 component'
components=list(src.objects)
for ob in components:ob.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/RuralHouse_01.fbx',components)
for ob in components:ob.modifiers.remove(ob.modifiers['Export triangulation'])

# Native Manny reference retained at established 1.805m, no rescaling of character geometry.
with bpy.data.libraries.load(str(ROOT/'SourceArt/Characters/Mannequins/Manny/Manny.blend'),link=False) as (a,b):b.objects=['root','FIT_Manny']
for ob in b.objects:
 if ob:studio.objects.link(ob);ob.hide_set(False)
rig=bpy.data.objects.get('root');body=bpy.data.objects.get('FIT_Manny')
if rig:
 rig.animation_data_clear();rig.location=(3.18,-1.75,0)
 # Relax upper arms to present useful standing architectural scale.
 for p in rig.pose.bones:p.rotation_mode='XYZ'
 for n,ang in [('upperarm_l',-.48),('upperarm_r',.48)]:
  if n in rig.pose.bones:rig.pose.bones[n].rotation_euler.y=ang

# Plain inspection lighting and ground; these never enter the runtime export.
bpy.ops.mesh.primitive_plane_add(size=200)
ground=bpy.context.object;ground.name='Review ground • not exported'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.diffuse_color=(.105,.115,.095,1);gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.105,.115,.095,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Soft daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.65,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
ld=bpy.data.lights.new('Daylight','AREA');light=bpy.data.objects.new('Daylight',ld);studio.objects.link(light);light.location=(-5,-7,11);ld.energy=1800;ld.shape='DISK';ld.size=7;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
sun=bpy.data.lights.new('Sun','SUN');so=bpy.data.objects.new('Sun',sun);studio.objects.link(so);so.rotation_euler=(.38,-.5,-.48);sun.energy=1.5;sun.angle=.13
def camera(name,pos,target,ortho):
 cd=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,cd);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=ortho;return o
cams=[camera('Front',(0,-13,3.25),(0,0,2.1),7.5),camera('Three-quarter',(8.5,-13,5.5),(.3,0,1.95),8.6),camera('Side and rear',(-9,11,5.5),(0,0,2),8),camera('Roof',(5,-7,14),(0,0,1.7),8)]
scene.view_settings.exposure=.35
scene.camera=cams[1]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
for ob in components:ob.select_set(True)
bpy.context.view_layer.objects.active=components[0]
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'RuralHouse01.blend'))
print('HOUSE_SAVED',len(components),'components',sum(len(p.vertices)-2 for o in components for p in o.data.polygons),'triangles',flush=True)
if '--no-render' not in sys.argv:
 for cam,label in [(cams[1],'house-three-quarter'),(cams[0],'house-front'),(cams[2],'house-side-rear'),(cams[3],'house-roof')]:
  scene.camera=cam;scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
print('HOUSE_COMPLETE',flush=True)
