"""Tachi01 modeling pass; uses the established SHŌEN geometry/FBX helpers."""
from pathlib import Path
import sys, math, json
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART.parent/'Do01/Scripts'))
import do_geometry as g
from export_do import fbx
sys.path.insert(0,str(ART/'scripts'))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.15
def collection(name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
src=collection('Tachi_01 • editable components')
fit=collection('Existing SHŌEN samurai • fit only')
studio=collection('Presentation')
with bpy.data.libraries.load(str(ART.parent/'Kote01/Kote01.blend'),link=False) as (a,b):
 b.objects=['root','Manny_Review','Kabuto_Review']+[n for n in a.objects if n.startswith(('Do_Review_','Sode_Review_','Kusazuri_01_','Suneate_','Kote_')) and n!='Kote_View']
 b.materials=['M_Kote01']
for ob in b.objects:
 if ob:fit.objects.link(ob);ob.hide_set(False)
rig=bpy.data.objects['root'];rig.animation_data_clear();rig.data.pose_position='REST'
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
for ob in fit.objects:
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
from tachi_finish import build_material
g.SOURCE=src;g.MATERIAL=build_material(ART)
scene.frame_set(1);bpy.context.view_layer.update()
groups={n:[] for n in ('Blade','Habaki','Tsuba','Fuchi','Tsuka','TsukaWrap','Menuki','Kashira','Saya','Kojiri','Sageo','SayaFittings')}
def add(group,ob):groups[group].append(ob);return ob
def center(x):
 t=x/.79
 return .065*t*t-.033*t if x>=0 else -.040*x
def oval(x,theta,ry,rz,offset=0):return Vector((x,(ry+offset)*math.cos(theta),center(x)+(rz+offset)*math.sin(theta)))

def shell(name,a,b,ry,rz,tile=0,steps=12,thickness=0,taper=1):
 n=32;verts=[];uv=[];faces=[]
 for k in range(steps+1):
  x=a+(b-a)*k/steps;fac=1+(taper-1)*k/steps
  for j in range(n):
   theta=math.tau*j/n;verts.append(oval(x,theta,ry*fac,rz*fac));uv.append((k/steps,j/n))
 for k in range(steps):
  for j in range(n):
   q=k*n+j;r=k*n+(j+1)%n;faces.append((q,r,r+n,q+n))
 ob=g.mesh(name,verts,faces,tile,uv)
 # Open shells can be reversed by bmesh's volume heuristic. Keep thickness inward.
 if ob.data.polygons[0].normal.y<0:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 if thickness:g.solid(ob,thickness,.00035)
 return ob

def ring(name,x,ry,rz,r=.00065,tile=2):return g.tube(name,[oval(x,math.tau*i/64,ry,rz) for i in range(64)],r,tile,8,True)
def band(group,name,a,b,ry,rz,tile=11):
 ob=add(group,shell(name,a,b,ry,rz,0 if tile==11 else tile,3,.001))
 for x in (a,b):add(group,ring(name+' rolled rim',x,ry+.0003,rz+.0003))
 if tile==11:
  for x in (a+.0015,b-.0015):add(group,ring(name+' inner chased line',x,ry+.0004,rz+.0004,.00024))
 return ob
def flower(group,origin,axis_u,axis_v,radius=.009):
 origin=Vector(origin);u=Vector(axis_u);v=Vector(axis_v)
 def pt(x,y):return origin+x*u+y*v
 # Broad chased petals catch the light; narrow ridges retain the floral silhouette.
 for j in range(6):
  a=math.tau*j/6;coords=[]
  for i in range(20):
   t=math.tau*i/20;rr=radius*(.57+.37*math.cos(t));tt=radius*.235*math.sin(t)
   coords.append(pt(rr*math.cos(a)-tt*math.sin(a),rr*math.sin(a)+tt*math.cos(a)))
  ob=g.mesh('Chased floral petal',coords,[tuple(range(20))],2,[(.5+.42*math.cos(math.tau*i/20),.5+.42*math.sin(math.tau*i/20)) for i in range(20)])
  add(group,g.solid(ob,.00065,.0002))
  add(group,g.tube('Petal edge',coords,.00032,2,6,True))
 for rr in (radius*.22,radius*.30):
  add(group,g.tube('Floral heart ring',[pt(rr*math.cos(math.tau*i/24),rr*math.sin(math.tau*i/24)) for i in range(24)],.0004,2,6,True))
 add(group,g.stud('Floral heart',origin,radius*.14,2))

from tachi_ornament import flower as chased_flower, vine_frieze
def flower(group,origin,axis_u,axis_v,radius=.009):
 u=Vector(axis_u);v=Vector(axis_v);n=u.cross(v)
 if abs(n.y)>.5 and n.y*origin[1]<0:v=-v
 if abs(n.x)>.5 and n.x*origin[0]<0:v=-v
 return chased_flower(g,add,group,origin,u,v,radius)

# Blade: distinct mune, shinogi and edge planes with a tapered kissaki.
xs=[.019+i*(.714-.019)/64 for i in range(65)]+[.725,.738,.749,.761,.773,.782,.789]
verts=[];uv=[];faces=[]
for x in xs:
 t=x/.79;w=.033-.010*t
 if x>.714:w*=max(.008,(.790-x)/(.790-.714))**.62
 thick=(.0034-.0014*t)*min(1,(.792-x)/.026)
 z=center(x)+(.011*max(0,(x-.714)/(.790-.714)))
 # Cross section counterclockwise around x; edge deliberately finite.
 for y,h in [(0,-.5),(-.14,-.475),(-1,.15),(-.55,.5),(.55,.5),(1,.15),(.14,-.475)]:
  verts.append((x,y*thick,z+h*w));uv.append((x/.79,h+.5))
for i in range(len(xs)-1):
 for j in range(7):faces.append((i*7+j,i*7+(j+1)%7,(i+1)*7+(j+1)%7,(i+1)*7+j))
faces += [tuple(reversed(range(7))),tuple((len(xs)-1)*7+j for j in range(7))]
blade=add('Blade',g.mesh('Forged shinogi-zukuri blade',verts,faces,0,uv,False))
longitudinal_normals=[]
for polygon in blade.data.polygons:
 polygon.use_smooth=True
 for vi in polygon.vertices:
  if polygon.index<(len(xs)-1)*7:
   ring_index=vi//7;stripe=polygon.index%7
   adjacent=[blade.data.polygons[k*7+stripe].normal for k in (ring_index-1,ring_index) if 0<=k<len(xs)-1]
   longitudinal_normals.append(tuple(sum(adjacent,Vector()).normalized()))
  else:longitudinal_normals.append(tuple(polygon.normal))
blade.data.normals_split_custom_set(longitudinal_normals)
for polygon in blade.data.polygons:
 for li,vi in zip(polygon.loop_indices,polygon.vertices):blade.data.uv_layers.active.data[li].uv=uv[vi]
# Restrained steel grain and undulating hamon, ordinary texture inputs at runtime.
W,H=2048,256
u,v=np.meshgrid(np.linspace(0,1,W),np.linspace(0,1,H))
rng=np.random.default_rng(118001)
wave=.225+.031*np.sin(u*math.tau*24)+.014*np.sin(u*math.tau*47+.8)
line=np.exp(-((v-wave)/.014)**2)
hardened=1/(1+np.exp(np.clip((v-wave)/.008,-60,60)))
grain=.012*np.sin(v*1950+np.sin(u*22)*2)+rng.normal(0,.003,(H,W))
lum=.36+.065*hardened+.12*line+grain*.65
color=np.stack((lum*.94,lum*.97,lum),axis=2)
orm=np.stack((np.ones_like(u),.25+.035*hardened+.065*line+grain*.15,np.ones_like(u)),axis=2)
def save_texture(name,rgb,colorspace):
 im=bpy.data.images.new(name,width=W,height=H,alpha=True)
 im.colorspace_settings.name=colorspace
 im.pixels.foreach_set(np.concatenate((np.clip(rgb,0,1),np.ones((H,W,1))),axis=2).astype(np.float32).ravel())
 im.filepath_raw=str(ART/'Textures'/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
base=save_texture('T_Tachi01_Steel_BaseColor',color,'sRGB')
packed=save_texture('T_Tachi01_Steel_ORM',orm,'Non-Color')
steel=bpy.data.materials.new('M_Tachi01_Steel');steel.use_nodes=True
nodes=steel.node_tree.nodes;links=steel.node_tree.links;bs=nodes.get('Principled BSDF')
tex=nodes.new('ShaderNodeTexImage');tex.image=base;links.new(tex.outputs['Color'],bs.inputs['Base Color'])
tex=nodes.new('ShaderNodeTexImage');tex.image=packed;sep=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],sep.inputs[0]);links.new(sep.outputs['Green'],bs.inputs['Roughness']);links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
blade.data.materials.clear();blade.data.materials.append(steel)

# Traditional broad crossing folds over a flattened grip; small red diamond windows.
add('Tsuka',shell('Red pebbled samegawa',-.239,-.018,.0097,.0153,1,32,.002,taper=.95))
for side in (-1,1):
 for index in range(12):
  cx=-.227+index*.0176
  for slope in (-1,1):
   vv=[];tu=[];ff=[];rows=32;cols=8
   for i in range(rows+1):
    t=i/rows;z=-.0173+.0346*t
    for j in range(cols+1):
     across=(j/cols-.5)*.0093
     x=cx+slope*(t-.5)*.0256+across
     # Tangential silk folds touch the grip; shallow alternating over-under crossing.
     fy=math.sqrt(max(.05,1-(z/.0180)**4))*.0104
     ridge=.00085*math.sin(math.pi*j/cols)**.7
     crossing=.00085*math.exp(-((t-.5)/.22)**2) if (index+(slope==1))%2 else 0
     vv.append((x,side*(fy+.00045+ridge+crossing),center(x)+z))
     tu.append((j/cols,t))
   for i in range(rows):
    for j in range(cols):
     q=i*(cols+1)+j;ff.append((q,q+1,q+cols+2,q+cols+1))
   ob=g.mesh('Folded black silk tsukamaki',vv,ff,4,tu)
   if ob.data.polygons[0].normal.y*side<0:
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
   add('TsukaWrap',g.solid(ob,.00065,.00012))
# Tight continuous folds around the narrow edges, with no loose loops above the grip.
for sign in (-1,1):
 vv=[];tu=[];ff=[]
 for i in range(49):
  x=-.239+.220*i/48
  for j in range(17):
   theta=sign*math.pi/2-.68+1.36*j/16
   vv.append(oval(x,theta,.0109,.0174));tu.append((i/48,j/16))
 for i in range(48):
  for j in range(16):q=i*17+j;ff.append((q,q+1,q+18,q+17))
 add('TsukaWrap',g.solid(g.mesh('Tight silk edge fold',vv,ff,4,tu),.00055,.0001))
band('Fuchi','Fuchi engraved collar',-.019,-.005,.0128,.0183)
band('Kashira','Kashira end cap',-.250,-.237,.0118,.0176)
add('Kashira',g.mesh('Kashira closed end',[oval(-.250,math.tau*i/32,.0118,.0176) for i in range(32)],[tuple(range(32))],11,[(.5+.45*math.cos(math.tau*i/32),.5+.45*math.sin(math.tau*i/32)) for i in range(32)]))
flower('Kashira',(-.251,0,center(-.25)),(0,1,0),(0,0,1),.010)
for side in (-1,1):
 flower('Menuki',(-.110,side*.0137,center(-.11)),(1,0,0),(0,0,1),.0065)
 flower('Menuki',(-.154,side*.0137,center(-.154)),(1,0,0),(0,0,1),.005)
band('Habaki','Solid brass habaki',.004,.028,.0045,.0170,2)
for side in (-1,1):flower('Habaki',(.017,side*.0057,center(.017)),(1,0,0),(0,0,1),.0060)
# Oval iron tsuba has a central opening and brass rim, vines and eight flowers per face.
n=96;vv=[];uv=[];ff=[]
for x in (-.0028,.0028):
 for inner in (False,True):
  for i in range(n):
   t=math.tau*i/n;y=(.006 if inner else .032)*math.cos(t);z=(.018 if inner else .037)*math.sin(t)
   vv.append((x,y,z));uv.append((.5+y/.072,.5+z/.082))
for i in range(n):
 j=(i+1)%n
 ff.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
guard=add('Tsuba',g.mesh('Blackened oval iron guard',vv,ff,0,uv))
for side in (-1,1):
 points=[(x,side*.0145+.0036*math.cos(math.tau*i/32),.0088*math.sin(math.tau*i/32)) for x in (-.009,.009) for i in range(32)]
 faces=[(i,(i+1)%32,(i+1)%32+32,i+32) for i in range(32)]+[tuple(reversed(range(32))),tuple(range(32,64))]
 cutter=g.mesh('Tsuba hitsu-ana cutter',points,faces,0)
 mod=guard.modifiers.new('Hollow hitsu-ana','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
 g.select([guard]);bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 for x in (-.0032,.0032):
  add('Tsuba',g.tube('Chased aperture lip',[(x,side*.0145+.0036*math.cos(math.tau*i/40),.0088*math.sin(math.tau*i/40)) for i in range(40)],.00032,2,6,True))
bevel=guard.modifiers.new('Soft iron guard edge','BEVEL');bevel.width=.0004;bevel.segments=3
for x in (-.0034,.0034):
 add('Tsuba',ring('Tsuba gold outer rim',x,.0317,.0367,.00085))
 add('Tsuba',ring('Tsuba inlaid fine border',x,.0285,.0335,.00038))
 for i in range(8):
  t=math.tau*(i+.5)/8;y=.022*math.cos(t);z=.027*math.sin(t)
  flower('Tsuba',(x*1.08,y,z),(0,1,0),(0,0,1),.0034)
  pts=[]
  for j in range(30):
   a=t-.23+j*.46/29;r=1+.08*math.sin(j/29*math.pi)
   pts.append((x*1.09,.017*r*math.cos(a),.024*r*math.sin(a)))
  add('Tsuba',g.tube('Gold vine',pts,.0004,2,6))
  for direction in (-1,1):
   points=[]
   for j in range(24):
    a=math.tau*j/23;r=.0028*(1-j/30)
    points.append((x*1.10,y*.79+r*math.cos(a),z*.82+direction*r*math.sin(a)))
   add('Tsuba',g.tube('Chased tendril',points,.0003,2,6))

# The hollow saya follows the same curve, with 2.2mm wall outside the blade envelope.
saya=add('Saya',shell('Hollow black lacquer saya',.030,.799,.0103,.0210,0,96,.0022,taper=.79))
layer=saya.data.uv_layers.active.data
for face in saya.data.polygons:
 block=(face.index//32)//12
 for li,vi in zip(face.loop_indices,face.vertices):
  k,j=divmod(vi,32);layer[li].uv=g.uvcoord(0,(k-block*12)/12,j/32)
band('SayaFittings','Saya mouth koiguchi',.029,.046,.0109,.0214,11)
band('SayaFittings','First hanging ashi',.099,.114,.0108,.0211,11)
band('SayaFittings','Second hanging ashi',.312,.328,.0100,.0198,11)
band('SayaFittings','Lower engraved band',.641,.657,.0090,.0183,11)
band('Kojiri','Kojiri bronze end',.764,.801,.0089,.0180,11)
add('Kojiri',g.mesh('Kojiri sealed tip',[oval(.801,math.tau*i/32,.0089,.018) for i in range(32)],[tuple(range(32))],11,[(.5+.43*math.cos(math.tau*i/32),.5+.43*math.sin(math.tau*i/32)) for i in range(32)]))
for side in (-1,1):
 for x,w,h,ry in ((-.012,.010,.028,.0133),(-.244,.010,.028,.0125),(.0375,.013,.032,.0118),(.1065,.012,.032,.0117),(.320,.012,.031,.0108),(.649,.013,.029,.0097),(.782,.030,.029,.0100)):
  group='Fuchi' if x==-.012 else 'Kashira' if x<0 else 'SayaFittings'
  vine_frieze(g,add,group,(x,side*ry,center(x)),(1,0,0),(0,0,-side),w,h)
 for x,r in ((.064,.009),(.649,.0063),(.780,.009)):
  flower('SayaFittings',(x,side*(.0106 if x<.1 else .0098),center(x)),(1,0,0),(0,0,1),r)
 # End fittings sweep into a restrained decorative spear-point over lacquer.
 for x,direction in ((.046,1),(.764,-1)):
  pts=[(x,side*.0115,center(x)+.016),(x+direction*.018,side*.0115,center(x)+.009),(x+direction*.025,side*.0115,center(x)),(x+direction*.018,side*.0115,center(x)-.009),(x,side*.0115,center(x)-.016)]
  add('SayaFittings',g.tube('Curled end fitting tracer',g.path(pts,6),.0006,2,6))

# Braided silk sageo: a rounded core plus three visible laid strands, no cloth system.
def braid(name,points,r=.0019,closed=False):
 pts=[Vector(p) for p in points]
 core=g.tube(name,pts,r*.72,3,8,closed);add('Sageo',core)
 lengths=[0.]
 for a,b in zip(pts,pts[1:]):lengths.append(lengths[-1]+(b-a).length)
 for strand in range(3):
  curve=[]
  for i,p in enumerate(pts):
   tangent=(pts[(i+1)%len(pts)]-pts[(i-1)%len(pts)]) if closed else pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
   tangent.normalize();axis=tangent.cross(Vector((0,1,0))).normalized()
   if axis.length<.1:axis=tangent.cross(Vector((1,0,0))).normalized()
   cross=tangent.cross(axis);angle=lengths[i]/.008*math.tau+strand*math.tau/3
   curve.append(p+r*.59*(axis*math.cos(angle)+cross*math.sin(angle)))
  add('Sageo',g.tube(name+' laid silk strand',curve,r*.43,3,6,closed))
 return core
def cord_ring(x):
 return braid('Braided securing turn',[oval(x,math.tau*i/112,.013,.024) for i in range(112)],.0019,True)
for x in (.106,.321):
 add('SayaFittings',g.tube('Suspension ring',[(x+.009*math.cos(math.tau*i/32),0,center(x)+.027+.006*math.sin(math.tau*i/32)) for i in range(32)],.0014,2,8,True))
for x in (.073,.082,.141,.149,.453,.461):
 cord_ring(x)
for delta in (-.0024,.0024):
 points=[(.079,-.014,center(.079)-.009+delta),(.16,-.017,-.034+delta),(.28,-.018,-.047+delta),(.40,-.016,-.037+delta),(.459,-.014,center(.459)-.008+delta)]
 braid('Sagging paired sageo',g.path(points,64),.0018)
for x in (.08,.146):
 for direction in (-1,1):
  points=[]
  for i in range(48):
   a=math.tau*i/48;points.append((x+direction*.014*(1-math.cos(a)),-.015-.004*math.sin(a),center(x)+.021+.009*math.sin(a)))
  braid('Sageo tied bow loop',g.path(points+[points[0]],3)[:-1],.0022,True)
 for i in range(3):
  points=[(x-.005+i*.004,-.019+.007*math.cos(math.tau*j/24),center(x)+.002+.020*math.sin(math.tau*j/24)) for j in range(24)]
  braid('Bound knot',g.path(points+[points[0]],3)[:-1],.0022,True)
 for delta in (-.004,.004):
  p=[(x+delta,-.020,center(x)),(x+.009+delta,-.024,-.035),(x+.003+delta,-.023,-.064)]
  braid('Short knotted tail',g.path(p,32),.002)
  for f in (-1,0,1):add('Sageo',g.tube('Tassel end',[(x+.003+delta+f*.0012,-.023,-.063),(x+.005+delta+f*.002,-.023,-.075)],.00075,3,6))

# One editable mesh for each logical system. No geometry is taken from fit objects.
parts={}
for name,objects in groups.items():
 if name=='Blade':ob=objects[0];ob.name='Tachi_01_Blade'
 else:ob=g.merge(objects,'Tachi_01_'+name)
 ob['asset']='Tachi_01';ob['component']=name;parts[name]=ob
 colors=ob.data.color_attributes.new(name='ArmorTint',type='BYTE_COLOR',domain='CORNER')
 colors.data.foreach_set('color',np.ones(len(colors.data)*4,dtype=np.float32))
 # Existing armor also suppresses cloth grazing sheen. Encode only dielectric specular.
 if name!='Blade':
  uvdata=ob.data.uv_layers.active.data
  for polygon in ob.data.polygons:
   for li in polygon.loop_indices:
    tex=uvdata[li].uv;tile=min(3,int(tex.x*4))+4*min(3,int(tex.y*4))
    spec={0:.28,1:.12,3:.06,4:.012}.get(tile,.5)
    colors.data[li].color=(spec,1,1,1)
 # Weld only coincident per-component vertices and preserve the sharp blade planes.
 if name!='Blade':
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
sword=[ob for name,ob in parts.items() if name not in ('Saya','Kojiri','Sageo','SayaFittings')]
scabbard=[parts[n] for n in ('Saya','Kojiri','Sageo','SayaFittings')]
for ob in parts.values():ob.modifiers.new('Export triangulation','TRIANGULATE')
for name,objects in [('Drawn',sword),('Saya',scabbard),('Sheathed',sword+scabbard)]:
 fbx(ART/'exports'/('SM_Tachi01_'+name+'.fbx'),objects)
 print('TACHI_EXPORTED',name,flush=True)
for ob in parts.values():ob.modifiers.remove(ob.modifiers['Export triangulation'])

# Simple charcoal product lighting and a reusable camera for the requested views.
world=bpy.data.worlds.new('Charcoal');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.032,.030,.027,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35
def track(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
lights=[]
for name,loc,power,size in [('Key',(.05,-.9,1.3),110,.8),('Softbox',(.7,1.0,.8),150,1.0),('Rim',(-.6,-.2,.5),80,.6),('Steel reflection',(.25,-1.2,-.65),65,1.2)]:
 data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc;data.energy=power;data.shape='DISK';data.size=size;track(ob,(.27,0,0));lights.append(ob)
data=bpy.data.cameras.new('Tachi_View');cam=bpy.data.objects.new('Tachi_View',data);studio.objects.link(cam);scene.camera=cam;data.type='ORTHO'
scene.render.resolution_x=2400;scene.render.resolution_y=950
cam.location=(.12,-1.9,.20);data.ortho_scale=1.20;track(cam,(.273,0,0))
for ob in fit.objects:ob.hide_render=True;ob.hide_set(True)
for ob in src.objects:ob.select_set(False)
parts['Saya'].select_set(True);bpy.context.view_layer.objects.active=parts['Saya']
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=1.3;area.spaces.active.region_3d.view_location=Vector((.27,0,0));area.spaces.active.shading.type='MATERIAL'
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Tachi01.blend'))
sys.path.insert(0,str(ART.parent/'Sode01/Scripts'))
from sode_render_settings import configure
configure(scene)
scene.render.filepath=str(ART/'Review/tachi-side.png');bpy.ops.render.render(write_still=True)
for ob in scabbard:ob.hide_render=True
cam.location=(.10,-1.65,.45);track(cam,(.27,0,0));scene.render.filepath=str(ART/'Review/tachi-unsheathed.png');bpy.ops.render.render(write_still=True)
for ob in scabbard:ob.hide_render=False
scene.render.resolution_x=1800;scene.render.resolution_y=1100
cam.location=(-.37,-.72,.30);data.ortho_scale=.43;track(cam,(-.065,0,0))
scene.render.filepath=str(ART/'Review/tachi-craft-detail.png');bpy.ops.render.render(write_still=True)
# Left hip: hilt forward/reachable, saya slopes behind the skirt outside the leg.
angle=math.radians(17.5);c=math.cos(angle);s=math.sin(angle)
fit_matrix=Matrix(((0,-1,0,.255),(c,0,s,-.12),(-s,0,c,.97),(0,0,0,1)))
for ob in parts.values():ob.matrix_world=fit_matrix@ob.matrix_world
for ob in fit.objects:ob.hide_render=ob.type=='ARMATURE';ob.hide_set(False)
for ob in lights:ob.location.z+=1;track(ob,(0,0,1.1))
scene.render.resolution_x=1500;scene.render.resolution_y=1700;data.ortho_scale=2.05
cam.location=(2.6,-3.8,1.8);track(cam,(0,0,1.00))
scene.render.filepath=str(ART/'Review/tachi-on-character-source.png');bpy.ops.render.render(write_still=True)
print('TACHI_MODEL_COMPLETE',flush=True)
