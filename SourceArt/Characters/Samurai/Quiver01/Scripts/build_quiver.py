"""Quiver01 authored construction, using the existing SHŌEN mesh/material helpers."""
from pathlib import Path
import sys, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART.parent/'Do01/Scripts'))
sys.path.insert(0,str(ART/'Scripts'))
import do_geometry as g
from export_do import fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def coll(n):
 c=bpy.data.collections.new(n);scene.collection.children.link(c);return c
fit=coll('Existing SHŌEN samurai • fit reference');source=coll('Quiver01 • editable components');arrows=coll('Arrow bundle • linked Arrow01');studio=coll('Presentation')
with bpy.data.libraries.load(str(ART.parent/'Kote01/Kote01.blend'),link=False) as (a,b):
 b.objects=['root','Manny_Review','Kabuto_Review']+[n for n in a.objects if n.startswith(('Do_Review_','Sode_Review_','Kusazuri_01_','Suneate_','Kote_'))]
 b.materials=['M_Kote01']
for ob in b.objects:
 if ob:fit.objects.link(ob);ob.hide_set(False);ob.hide_render=ob.type=='ARMATURE'
rig=bpy.data.objects['root'];rig.animation_data_clear();rig.data.pose_position='REST'
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
for ob in fit.objects:
 for m in ob.modifiers:
  if m.type=='ARMATURE':m.object=rig
scene.frame_set(1);bpy.context.view_layer.update()
g.SOURCE=source;g.MATERIAL=bpy.data.materials['M_Kote01']
groups={n:[] for n in ['Body','TopRim','BottomCap','Lacing','Textile','Hardware','Emblem','ShoulderStrap','WaistStrap']}
def add(n,o):groups[n].append(o);return o
base=Vector((-.015,.220,.885));rot=Matrix.Rotation(math.radians(-15),4,'Y');H=.73
def Q(x,y,z):return base+rot@Vector((x,y,z))
def rad(z):
 f=max(0,min(1,z/H));return .049+.013*f,.034+.010*f
def P(t,z,off=0):
 rx,ry=rad(z);c=math.cos(t);s=math.sin(t)
 return Q((rx+off)*math.copysign(abs(c)**.48,c),(ry+off)*math.copysign(abs(s)**.48,s),z)
def panel(n,ta,tb,za,zb,tile=0,off=0,thick=.002,nx=12,nz=1):
 vv=[];uv=[];ff=[]
 for j in range(nz+1):
  for i in range(nx+1):
   u=i/nx;v=j/nz;vv.append(P(ta+(tb-ta)*u,za+(zb-za)*v,off));uv.append((.035+.93*u,.035+.93*v))
 for j in range(nz):
  for i in range(nx):
   k=j*(nx+1)+i;ff.append((k,k+1,k+nx+2,k+nx+1))
 ob=g.mesh(n,vv,ff,tile,uv);return g.solid(ob,thick,.0005) if thick else ob
def ring(n,z,r=.0014,tile=3,off=.002):return g.tube(n,[P(math.tau*i/64,z,off) for i in range(64)],r,tile,8,True)
# A hollow wooden/leather shell with broad flat faces, eight softened corners, and real depth.
add('Body',panel('Hollow leather inner wall',0,math.tau,.012,H-.006,4,-.003,.003,64,8))
for j in range(8):
 za=.035+j*.080;zb=min(H-.038,za+.078)
 for i in range(14):
  a=math.tau*i/14+.012;b=math.tau*(i+1)/14-.012
  add('Body',panel('Narrow lacquer stave %02d %02d'%(j,i),a,b,za,zb,0,.0006,.0022,4,1))
  if j in [0,3,7]:add('Hardware',g.stud('Restrained bronze rivet',P((a+b)/2,za+.009,.0032),.0014,2))
# Closed base and visible padded interior floor, well below the arrow mouths.
vv=[Q(0,0,.016)]+[P(math.tau*i/64,.016,-.004) for i in range(64)]
add('BottomCap',g.solid(g.mesh('Closed leather bottom',vv,[(0,i+1,(i+1)%64+1) for i in range(64)],4),.006,.0007))
for key,za,zb in [('TopRim',H-.035,H),('BottomCap',.006,.040)]:
 add(key,panel('Leather bound rim',0,math.tau,za-.004,zb+.004,4,.004,.005,64,1))
 # Small dark inset fields and fine brass borders, matching the armor's restrained trim.
 for i in range(16):
  a=math.tau*i/16;b=math.tau*(i+1)/16
  add(key,panel('Dark chased rim field',a+.005,b-.005,za+.004,zb-.004,0,.009,.0015,4,1))
  mid=(a+b)/2;zc=(za+zb)/2
  for sign in [-1,1]:
   vine=[P(mid+sign*.015,zc-.007,.012),P(mid+sign*.100,zc-.003,.012),P(mid+sign*.115,zc+.006,.012),P(mid+sign*.052,zc+.009,.012),P(mid+sign*.040,zc+.004,.012)]
   add(key,g.tube('Bronze botanical rim inlay',g.path(vine,3),.00072,2,6))
  add(key,g.stud('Small flower heart',P(mid,zc,.012),.0016,2))
 for z in [za,zb]:add(key,ring('Raised brass rim piping',z,.0011,2,.011))
 for z in [za-.006,zb+.006]:add('Lacing',ring('Red rim binding',z,.0018,3,.006))
 for i in range(12):
  t=math.tau*(i+.3)/12
  add('Lacing',g.tube('Rim silk stitch',[P(t-.036,za-.007,.008),P(t,za-.009,.012),P(t+.030,za+.002,.010)],.00155,3,7))
# The top exposes the actual inner lip; no false lid or arrow-floating platform.
vs=[];uv=[];fs=[]
for off in [.009,-.007]:
 for i in range(64):vs.append(P(math.tau*i/64,H,off));uv.append((i/64,0 if off>0 else 1))
for i in range(64):fs.append((i,(i+1)%64,(i+1)%64+64,i+64))
add('TopRim',g.mesh('Visible thick opening lip',vs,fs,4,uv))
# Long indigo brocade strips break the stave construction on both narrow faces.
for t in [0,math.pi]:
 for j in range(6):
  za=.060+j*.102;zb=za+.100
  add('Textile',panel('Indigo woven side panel',t-.25,t+.25,za,zb,12,.0038,.0015,5,1))
  # Readable repeating lozenges, with finer engraving carried by the existing atlas.
  for z in [za+.025,za+.074]:
   diamond=[P(t-.18,z,.006),P(t,z+.019,.006),P(t+.18,z,.006),P(t,z-.019,.006)]
   add('Textile',g.tube('Brocade bronze lozenge',diamond,.00065,2,5,True))
 for s in [-1,1]:add('Textile',g.tube('Brocade leather seam',[P(t+s*.27,.054+i*.010,.005) for i in range(63)],.0013,4,6))
# Crossed red odoshi, enough mass to read at tactical distance.
for z in [.065,.150,.236,.322,.408,.580,.651]:
 add('Lacing',ring('Horizontal retaining cord',z,.00165,3,.005))
 for t in [math.pi*.28,math.pi*.50,math.pi*.72,math.pi*1.28,math.pi*1.50,math.pi*1.72]:
  for dx in [-.066,.066]:
   for dz in [-.009,.009]:add('Hardware',g.stud('Dark lacing eye',P(t+dx,z+dz,.0038),.0021,0))
  for s in [-1,1]:
   pts=[P(t-.082,z-s*.010,.005),P(t-.035,z-s*.005,.010),P(t+.036,z+s*.005,.010),P(t+.080,z+s*.010,.005)]
   add('Lacing',g.tube('Raised crossed crimson silk',g.path(pts,3),.0020,3,8))
  add('Lacing',g.tube('Compact knot',[P(t-.018,z-.002,.011),P(t+.019,z+.002,.011)],.00215,3,8))
for t in [.20,math.pi-.20,math.pi+.20,math.tau-.20]:
 add('Lacing',g.tube('Long edge retaining lace',[P(t,.035+i*.011,.004) for i in range(62)],.00165,3,7))
# Reuse the existing six-petal Suneate crest mesh, including its engraved atlas UVs.
original=bpy.data.objects['Suneate_L_01_Fittings'];deps=bpy.context.evaluated_depsgraph_get()
data=bpy.data.meshes.new_from_object(original.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
data.transform(original.matrix_world)
bm=bmesh.new();bm.from_mesh(data)
remove=[v for v in bm.verts if not (.109<v.co.x<.154 and .372<v.co.z<.417 and v.co.y<-.039)]
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(data);bm.free()
crest=bpy.data.objects.new('Reused SHŌEN floral crest',data);source.objects.link(crest)
points=[v.co for v in data.vertices];cx=(min(p.x for p in points)+max(p.x for p in points))/2;cz=(min(p.z for p in points)+max(p.z for p in points))/2;cy=max(p.y for p in points)
for v in data.vertices:
 x,y,z=v.co;v.co=Q((x-cx)*1.48,.057+(cy-y)*1.48,.503+(z-cz)*1.48)
crest.data.materials.clear();crest.data.materials.append(g.MATERIAL);add('Emblem',crest)
# Dark square backing, corner pins, and a slightly raised floral medallion.
add('Emblem',panel('Crest lacquer mount',math.pi*.31,math.pi*.69,.461,.547,0,.006,.003,12,1))
for x in [-.033,.033]:
 for z in [.469,.539]:add('Emblem',g.stud('Crest corner brass pin',Q(x,.051,z),.0021,2))
# Attachment rings are physically joined to small lacquer and bronze leather tabs.
attachments={}
for name,z,t in [('Upper',.613,math.pi*.92),('Lower',.162,math.pi*.93),('Waist',.268,.10)]:
 p=P(t,z,.013);attachments[name]=p
 add('Hardware',panel('Reinforced strap tab',t-.11,t+.11,z-.031,z+.024,4,.012,.004,4,1))
 pts=[p+rot@Vector((.008*math.cos(math.tau*i/32),.003,.012*math.sin(math.tau*i/32))) for i in range(32)]
 add('Hardware',g.tube('Aged bronze suspension ring',pts,.0022,2,8,True))
 add('Hardware',g.stud('Ring anchor rivet',p+rot@Vector((0,0,.024)),.0024,2))
def ribbon(name,anchors,width,key):
 pts=g.path(anchors,6);vv=[];uv=[];fs=[];sides=[]
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  # Transverse is horizontal over torso, turning smoothly around the shoulder.
  outward=Vector((p.x*1.8,p.y*2, .12 if p.z>1.48 else 0)).normalized()
  side=tangent.cross(outward).normalized();sides.append(side)
  for sign in [-1,1]:vv.append(p+side*width*.5*sign);uv.append((.08 if sign<0 else .92,(i%6)/6*.88+.06))
 for i in range(len(pts)-1):fs.append((2*i,2*i+1,2*i+3,2*i+2))
 add(key,g.solid(g.mesh(name,vv,fs,12,uv),.0032,.00065))
 for sign in [-1,1]:
  add(key,g.tube('Dark leather strap selvedge',[p+s*width*.48*sign for p,s in zip(pts,sides)],.0021,4,7))
  add(key,g.tube('Fine brass stitch line',[p+s*width*.36*sign for p,s in zip(pts,sides)],.0006,2,5))
 return pts,sides
upper=attachments['Upper'];lower=attachments['Lower'];waist=attachments['Waist']
shoulder=[upper,(-.10,.177,1.48),(.065,.161,1.492),(.151,.105,1.515),(.163,-.018,1.525),(.141,-.153,1.467),(.047,-.193,1.353),(-.101,-.178,1.223),(-.205,-.094,1.150),(-.213,.055,1.095),(-.158,.157,1.064),lower]
ribbon('Fitted indigo shoulder sling',shoulder,.029,'ShoulderStrap')
waistpath=[waist,(-.16,.166,1.126),(-.202,.04,1.115),(-.184,-.102,1.115),(-.070,-.175,1.115),(.090,-.172,1.115),(.198,-.065,1.115),(.195,.090,1.115),(.101,.173,1.115),(-.04,.182,1.115),waist]
ribbon('Fitted waist stabilizing belt',waistpath,.018,'WaistStrap')
# Visible buckle on the chest section of the shoulder sling.
c=Vector((.060,-.200,1.369));a=Vector((.64,0,.768));b=Vector((-.768,0,.64))
corners=[c+a*.018*sa+b*.022*sb for sa,sb in [(-1,-1),(-1,1),(1,1),(1,-1)]]
add('Hardware',g.tube('Shoulder sling bronze buckle',corners,.0024,2,8,True))
add('Hardware',g.tube('Buckle tongue',[c-b*.022,c+b*.015],.0016,2,7))
for k in [-1,1]:add('Hardware',g.stud('Buckle corner rivet',c+a*k*.013, .0018,2))
# Small red attachment knots and relaxed tails, kept close to the case.
for p in [upper,lower]:
 for s in [-1,1]:
  pts=[p,p+Vector((s*.012,.008,.004)),p+Vector((s*.018,.008,-.006)),p+Vector((0,.006,-.005))]
  add('Lacing',g.tube('Suspension silk bow',g.path(pts,3),.0023,3,8))
  add('Lacing',g.tube('Short knot tail',g.path([p,p+Vector((s*.008,.008,-.025)),p+Vector((s*.011,.007,-.047))],4),.0019,3,7))
parts=[]
for key,items in groups.items():
 ob=g.merge(items,'Quiver_01_'+key)
 color=ob.data.color_attributes.new(name='ArmorTint',type='BYTE_COLOR',domain='CORNER')
 for c in color.data:c.color=(1,1,1,1)
 ob['asset']='Quiver_01';parts.append(ob)
# One arrow model, linked duplicates with a compact, deliberately irregular fletching fan.
from arrow_geometry import build_arrow
arrow=build_arrow(g)
arrow.name='Arrow_01'
tri=arrow.modifiers.new('Clean export triangles','TRIANGULATE');g.select([arrow]);bpy.ops.object.modifier_apply(modifier=tri.name)
fbx(ART/'Exports/Arrow_01.fbx',[arrow])
source.objects.unlink(arrow);arrows.objects.link(arrow)
rng=random.Random(1180);bundle=[]
spots=[(-.029,-.015),(-.009,-.018),(.015,-.016),(.032,.002),(.012,.016),(-.010,.015),(-.032,.009)]
for i,(x,y) in enumerate(spots):
 ob=arrow if i==0 else bpy.data.objects.new('Arrow_01_linked_%02d'%i,arrow.data)
 if i:arrows.objects.link(ob)
 ob.matrix_world=Matrix.Translation(Q(x,y,.018+rng.uniform(0,.052)))@rot@Matrix.Rotation(rng.uniform(-.036,.036),4,'Y')@Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')
 ob['source_asset']='Arrow_01';bundle.append(ob)
# Ordinary static FBX export preserves the fitted coordinates and editable source components.
fbx(ART/'Exports/Quiver_01.fbx',parts)
# Evaluate one combined export copy; the saved scene retains linked arrow instances.
copies=[]
for ob in bundle:
 cp=ob.copy();cp.data=ob.data.copy();arrows.objects.link(cp);copies.append(cp)
g.select(copies);bpy.ops.object.join();cp=bpy.context.object;cp.name='ArrowBundle_01_Export'
fbx(ART/'Exports/ArrowBundle_01.fbx',[cp]);bpy.data.objects.remove(cp,do_unlink=True)
world=bpy.data.worlds.new('Existing outfit studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.040,.049,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def track(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Soft rear key',(-2,3,3.3),650,2.6),('Warm edge',(2,1,2.8),550,2),('Front fill',(0,-3,2),380,3)]:
 d=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,d);studio.objects.link(ob);ob.location=loc;d.energy=power;d.shape='DISK';d.size=size;track(ob,(0,0,1.2))
d=bpy.data.cameras.new('Quiver_View');cam=bpy.data.objects.new('Quiver_View',d);studio.objects.link(cam);scene.camera=cam;d.type='ORTHO'
views=[('back',(0,3,1.35),(0,0,1.02),2.08),('threequarter',(-2.2,3,1.85),(-.06,.04,1.10),1.96),('close',(-.80,1.60,2.0),(-.16,.22,1.57),.67),('front',(0,-3,1.4),(0,0,1.02),2.08),('side',(-3,.05,1.4),(0,0,1.02),2.08)]
cam.location=views[1][1];d.ortho_scale=views[1][3];track(cam,views[1][2])
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except:pass
g.select(parts)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=2.7;area.spaces.active.region_3d.view_location=Vector((0,.1,1.1));area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Quiver01.blend'))
sys.path.insert(0,str(ART.parent/'Sode01/Scripts'))
from sode_render_settings import configure
configure(scene)
for name,loc,target,scale in views:
 cam.location=loc;d.ortho_scale=scale;track(cam,target);scene.render.filepath=str(ART/'Review'/('source-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('QUIVER01_MODELED_AND_EXPORTED',flush=True)
