"""Construct the paired, editable shin guards using the existing armor atlas and Manny."""
from pathlib import Path
import sys, math
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART.parent/'Do01/Scripts'))
import do_geometry as g
from export_do import fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def collection(n):
 c=bpy.data.collections.new(n);scene.collection.children.link(c);return c
fit=collection('Existing_SHOEN_Outfit');source=collection('Suneate01_Editable');studio=collection('Presentation')
with bpy.data.libraries.load(str(ART.parent/'Kusazuri01/Kusazuri01.blend'),link=False) as (a,b):
 b.objects=['root','Manny_Review','Kabuto_Review']+[n for n in a.objects if n.startswith(('Do_Review_','Sode_Review_','Kusazuri_01_'))]
 b.actions=['A_Idle','A_Walk','A_Run'];b.materials=['M_Kusazuri01']
for ob in b.objects:
 if ob:
  fit.objects.link(ob);ob.hide_set(False);ob.hide_render=ob.type=='ARMATURE'
for a in b.actions:a.use_fake_user=True
rig=bpy.data.objects['root'];rig.animation_data_clear();rig.data.pose_position='REST'
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
for ob in fit.objects:
 for m in ob.modifiers:
  if m.type=='ARMATURE':m.object=rig
scene.frame_set(1);bpy.context.view_layer.update()
g.SOURCE=source;g.MATERIAL=bpy.data.materials['M_Kusazuri01'].copy();g.MATERIAL.name='M_Suneate01'
nodes=g.MATERIAL.node_tree.nodes;links=g.MATERIAL.node_tree.links
palette=next(n for n in nodes if n.type=='VALTORGB' and n.label.startswith('Lacquer'))
for tile,tint in {2:(.65,.52,.36),11:(.65,.52,.36),3:(.44,.20,.17),4:(.25,.19,.14),7:(5.,3.2,1.65)}.items():
 min(palette.color_ramp.elements,key=lambda e:abs(e.position-(tile-.1)/15)).color=(*tint,1)
cloth=next(n for n in nodes if n.label=='Kusazuri lining tile12 only')
rope=nodes.new('ShaderNodeMath');rope.operation='COMPARE';rope.inputs[1].default_value=7;rope.inputs[2].default_value=.1
links.new(cloth.inputs[0].links[0].from_socket,rope.inputs[0])
combined=nodes.new('ShaderNodeMath');combined.operation='MAXIMUM'
consumers=[l.to_socket for l in cloth.outputs[0].links]
links.new(cloth.outputs[0],combined.inputs[0]);links.new(rope.outputs[0],combined.inputs[1])
woven_channel=next(n for n in nodes if n.type=='SEPARATE_COLOR' and n.inputs[0].is_linked and n.inputs[0].links[0].from_node.type=='VERTEX_COLOR')
woven_mask=nodes.new('ShaderNodeMath');woven_mask.operation='SUBTRACT';woven_mask.inputs[0].default_value=1;links.new(woven_channel.outputs['Red'],woven_mask.inputs[1])
matte=nodes.new('ShaderNodeMath');matte.operation='MAXIMUM';links.new(combined.outputs[0],matte.inputs[0]);links.new(woven_mask.outputs[0],matte.inputs[1])
for socket in consumers:links.new(matte.outputs[0],socket)
for n in nodes:
 if n.type=='MIX_RGB' and all(abs(n.inputs[2].default_value[i]-[.08,.18,.50][i])<.0001 for i in range(3)):
  n.inputs[2].default_value=(.014,.025,.050,1)
# Textile normals stay fine; broad stamped-metal relief must not resemble fur.
strength=nodes.new('ShaderNodeMapRange');strength.inputs['From Min'].default_value=0;strength.inputs['From Max'].default_value=1;strength.inputs['To Min'].default_value=.65;strength.inputs['To Max'].default_value=.10
links.new(matte.outputs[0],strength.inputs['Value'])
for n in nodes:
 if n.type=='NORMAL_MAP':links.new(strength.outputs[0],n.inputs['Strength'])
# Neutral fixture display; the body geometry and original asset remain unchanged.
fixture=bpy.data.materials.new('Suneate_Fit_Display');fixture.use_nodes=True
bs=fixture.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.075,.090,.11,1);bs.inputs['Roughness'].default_value=.82
bpy.data.objects['Manny_Review'].data.materials.clear();bpy.data.objects['Manny_Review'].data.materials.append(fixture)
# Profile sampled from the unmodified Manny lower leg, with a padding allowance.
profile=[(.145,.145,.015,.041,.049),(.22,.142,.017,.050,.059),(.28,.138,.019,.063,.071),(.34,.134,.019,.071,.080),(.40,.131,.006,.070,.080),(.468,.129,-.011,.062,.075)]
def shape(z):
 for a,b in zip(profile,profile[1:]):
  if z<=b[0]:
   f=max(0,min(1,(z-a[0])/(b[0]-a[0])))
   return [a[i]+f*(b[i]-a[i]) for i in range(1,5)]
 return profile[-1][1:]
allparts={}
for side,sgn in [('L',1),('R',-1)]:
 groups={k:[] for k in ['ShinPlate','SideProtection','CalfSupport','UpperTrim','LowerTrim','Straps','Fittings','Padding','Lacing']}
 def P(t,z,off=0):
  cx,cy,rx,ry=shape(z)
  return Vector((sgn*(cx+(rx+off)*math.sin(t)),cy-(ry+off)*math.cos(t),z))
 def panel(name,ta,tb,za,zb,tile=0,off=0,thick=.0025,nx=8,nz=8,crown=0):
  vv=[];uv=[];ff=[]
  for j in range(nz+1):
   v=j/nz;z=za+(zb-za)*v
   for i in range(nx+1):
    u=i/nx;t=ta+(tb-ta)*u
    vv.append(P(t,z,off+crown*math.sin(math.pi*u)));uv.append((.05+.90*u,.04+.92*v))
  for j in range(nz):
   for i in range(nx):
    k=j*(nx+1)+i;f=(k,k+1,k+nx+2,k+nx+1);ff.append(f if sgn==1 else tuple(reversed(f)))
  ob=g.mesh(name,vv,ff,tile,uv)
  # Open surfaces are outward before Solidify, on both anatomical sides.
  for f in ob.data.polygons:
   c=f.center;out=Vector((sgn*math.sin((ta+tb)/2),-math.cos((ta+tb)/2),0))
   if f.normal.dot(out)<0:
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
   break
  return g.solid(ob,thick,.00045) if thick else ob
 def add(k,o):groups[k].append(o);return o
 # A soft, open-ended sleeve; the knee and ankle stay uncovered.
 add('Padding',panel('Indigo quilted calf liner',-math.pi,math.pi,.149,.464,12,-.0005,.003,nx=48,nz=14))
 for z in [.150,.463]:
  add('Padding',g.tube('Soft rolled indigo cuff',[P(-math.pi+math.tau*i/64,z,.0015) for i in range(64)],.0032,5,8,True))
 # Continuous crowned vertical splints: longest at the front, shorter at the sides.
 front=[(-1.06+2.12*i/9,-1.06+2.12*(i+1)/9) for i in range(9)]
 outer=[(1.10+.235*i,1.10+.235*(i+1)) for i in range(3)]
 inner=[(-1.10-.20*(i+1),-1.10-.20*i) for i in range(2)]
 for k,(ta,tb) in enumerate(front+outer+inner):
  mid=(ta+tb)/2;top=.439-.014*max(0,abs(mid)-.8);bottom=.163+.006*max(0,abs(mid)-.9)
  grp='ShinPlate' if k<9 else 'SideProtection'
  add(grp,panel('Crowned lacquer splint %02d'%k,ta+.008,tb-.008,bottom,top,10,.005,.003,nx=3,nz=16,crown=.0016))
  # Preserve fine texture scale along the long splint, avoiding stretched grain.
  skin=groups[grp][-1];layer=skin.data.uv_layers.active.data
  for face in skin.data.polygons:
   band=min(3,(face.index//3)//4)
   for li,vi in zip(face.loop_indices,face.vertices):
    row,col=divmod(vi,4);u=.12+(k%4)*.16+.12*col/3;v=.10+.80*(row-band*4)/4
    layer[li].uv=g.uvcoord(10,u,v)
  add(grp,g.tube('Raised black splint edge' ,[P(ta+.014,bottom+(top-bottom)*j/14,.006) for j in range(15)],.00075,0,5))
  for z in [bottom+.008,top-.009]:add('Fittings',g.stud('Small bronze splint rivet',P(mid,z,.008),.00145,2))
  # Smooth doubled cords sit over dark lacing apertures; texture carries the fibers.
  for row,z in enumerate([.188,.245,.301,.355]):
   for dx in [-.045,.045]:
    for dz in [-.0045,.0045]:
     add('Fittings',g.stud('Dark recessed lacing aperture',P(mid+dx,z+dz,.0082),.0023,0))
   for cross in [-1,1]:
    pts=[P(mid-.061,z-cross*.005,.0086),P(mid-.031,z-cross*.003,.011),P(mid+.012,z+cross*.002,.012),P(mid+.058,z+cross*.005,.0086)]
    add('Lacing',g.tube('Rounded crossed silk tie',g.path(pts,4),.0020,3,8))
   for dx in [-.060,.060]:
    pts=[P(mid+dx+.025*math.cos(math.tau*j/12),z+.0034*math.sin(math.tau*j/12),.0115) for j in range(12)]
    add('Lacing',g.tube('Compact silk knot loop',pts,.00115,3,6,True))
   if row<3:
    add('Lacing',g.tube('Dark vertical retaining braid',[P(mid,.197+row*.055+j*.008,.0076) for j in range(6)],.00085,12,6))
 # Rear calf support stays mostly soft, with two narrow leather reinforced ribs.
 for ta,tb in [(2.20,2.36),(-2.36,-2.20)]:
  add('CalfSupport',panel('Rear reinforced leather stay',ta,tb,.167,.437,4,.002,.003,nx=2,nz=12))
 # Brocaded upper cuff and brass-bound top/bottom strips.
 add('UpperTrim',panel('Upper indigo cuff',-1.14,1.84,.439,.464,12,.002,.002,nx=24,nz=2))
 for group,za,zb in [('UpperTrim',.419,.437),('LowerTrim',.162,.179)]:
  add(group,panel('Dark leather trim backing',-1.08,1.81,za-.002,zb+.002,4,.009,.002,nx=28,nz=1))
  # The chased texture repeats in restrained panels, with thin physical metal hems.
  for i in range(12):
   ta=-1.08+2.89*i/12;tb=-1.08+2.89*(i+1)/12
   add(group,panel('Dark engraved trim field',ta,tb,za+.001,zb-.001,0,.011,.0012,nx=3,nz=1))
  for i in range(12):
   t=-1.08+2.89*(i+.5)/12;zc2=(za+zb)*.5
   # A broad diamond and interlocking tendrils echo the set's geometric goldwork.
   diamond=[P(t-.089,zc2,.013),P(t,za+.0025,.013),P(t+.089,zc2,.013),P(t,zb-.0025,.013)]
   add(group,g.tube('Bronze geometric inlay',diamond,.00065,2,6,True))
   for sign2 in [-1,1]:
    pts=[P(t+sign2*.015,zc2-.003,.013),P(t+sign2*.050,zc2-.001,.013),P(t+sign2*.015,zc2+.003,.013)]
    add(group,g.tube('Chased internal flourish',g.path(pts,3),.00045,2,5))
   add(group,g.stud('Inlay center pin',P(t,zc2,.0135),.00085,2))
  for z in [za,zb]:add(group,g.tube('Fine aged brass hem',[P(-1.08+2.89*i/48,z,.012) for i in range(49)],.00085,2,6))
 # Straps wrap the calf; buckle/tail sit on the outer side of each leg.
 for row,z in enumerate([.426,.291,.194]):
  add('Straps',panel('Leather calf strap %d'%row,.83,5.24,z-.008,z+.008,4,.009,.003,nx=48,nz=1))
  bt=1.49
  add('Straps',panel('Outward directed strap tail',bt-.25,bt+.65,z-.0065,z+.0065,4,.015,.0025,nx=12,nz=1))
  corners=[(bt-.16,z-.0105),(bt+.16,z-.0105),(bt+.16,z+.0105),(bt-.16,z+.0105)]
  add('Fittings',g.tube('Rectangular bronze buckle',[P(t,h,.019) for t,h in corners],.0017,2,8,True))
  add('Fittings',g.tube('Buckle tongue',[P(bt-.12,z,.021),P(bt+.15,z,.021)],.0011,2,6))
  for t in [bt+.30,bt+.45,bt+.59]:add('Fittings',g.stud('Recessed punched strap hole',P(t,z,.0173),.00115,0))
  add('Fittings',panel('Strap keeper',bt+.24,bt+.29,z-.009,z+.009,2,.018,.0015,nx=1,nz=1))
 # Compact six-petal family ornament follows the front curvature.
 zc=.394;rad=.021
 def jewel(x,z,off):
  rx=shape(z)[2];return P(math.asin(max(-.99,min(.99,x/rx))),z,off)
 def disc(name,r,tile,off):
  vv=[jewel(0,zc,off)];uv=[(.5,.5)]
  for i in range(48):
   a=math.tau*i/48;vv.append(jewel(r*math.cos(a),zc+r*math.sin(a),off));uv.append((.5+.47*math.cos(a),.5+.47*math.sin(a)))
  ff=[(0,i+1,(i+1)%48+1) for i in range(48)]
  if sgn<0:ff=[tuple(reversed(f)) for f in ff]
  return g.solid(g.mesh(name,vv,ff,tile,uv),.001,.0003)
 add('Fittings',disc('Round floral crest base',rad,11,.011))
 add('Fittings',disc('Recessed bronze crest field',rad*.84,2,.012))
 for r in [rad,.007]:add('Fittings',g.tube('Raised crest bezel',[jewel(r*math.cos(math.tau*i/48),zc+r*math.sin(math.tau*i/48),.014) for i in range(48)],.00085,2,6,True))
 for j in range(6):
  a=math.tau*j/6;vv=[jewel(.010*math.cos(a),zc+.010*math.sin(a),.0165)];uv=[(.5,.5)];ff=[]
  for ring in range(1,5):
   rho=ring/4
   for i in range(16):
    angle=math.tau*i/16;rr=.010+.007*rho*math.cos(angle);tt=.0043*rho*math.sin(angle)
    vv.append(jewel(rr*math.cos(a)-tt*math.sin(a),zc+rr*math.sin(a)+tt*math.cos(a),.0135+.003*(1-rho*rho)));uv.append((.50+.35*rho*math.cos(angle),.5+.35*rho*math.sin(angle)))
  for i in range(16):ff.append((0,1+i,1+(i+1)%16))
  for ring in range(3):
   for i in range(16):
    k=1+ring*16+i;n=1+ring*16+(i+1)%16;ff.append((k,k+16,n+16,n))
  if sgn<0:ff=[tuple(reversed(f)) for f in ff]
  add('Fittings',g.solid(g.mesh('Sculpted bronze flower petal',vv,ff,11,uv),.0008,.0002))
  add('Fittings',g.tube('Petal engraved vein',[jewel(r*math.cos(a),zc+r*math.sin(a),.0167) for r in [.006,.010,.014]],.00035,0,5))
 add('Fittings',g.stud('Crest central boss',jewel(0,zc,.015),.0037,2))
 parts=[]
 for key,items in groups.items():
  ob=g.merge(items,'Suneate_%s_01_%s'%(side,key));g.weight(ob,rig,lambda p:{'calf_'+side.lower():1.})
  colors=ob.data.color_attributes.new(name='ArmorTint',type='BYTE_COLOR',domain='CORNER')
  for c in colors.data:c.color=(1,1,1,1)
  ob['asset']='Suneate_'+side+'_01';ob['anatomical_side']='left' if side=='L' else 'right'
  parts.append(ob)
 allparts[side]=parts
# Footwear belongs to the same paired asset, on Manny's existing foot bones.
sys.path.insert(0,str(ART/'Scripts'))
from suneate_footwear import build_footwear
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
body=bpy.data.objects['Manny_Review'];body.data.calc_loop_triangles()
bodypoints=[body.matrix_world@v.co for v in body.data.vertices]
bodyweights=[]
for v in body.data.vertices:
 bodyweights.append({body.vertex_groups[w.group].name:w.weight for w in v.groups if body.vertex_groups[w.group].name in rig.data.bones})
for side,sgn in [('L',1),('R',-1)]:
 footwear=build_footwear(g,rig,side,sgn)
 triangles=[tuple(t.vertices) for t in body.data.loop_triangles if all(sgn*bodypoints[i].x>.035 for i in t.vertices) and min(bodypoints[i].z for i in t.vertices)<.20]
 surface=BVHTree.FromPolygons(bodypoints,triangles,all_triangles=True)
 def weight_foot(p):
  hit,normal,index,distance=surface.find_nearest(p)
  if hit is None:return {'foot_'+side.lower():1.}
  ids=triangles[index];a,b,c=[bodypoints[i] for i in ids]
  bc=barycentric_transform(hit,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  values={}
  for vi,factor in zip(ids,bc):
   for name,w in bodyweights[vi].items():values[name]=values.get(name,0)+max(0,factor)*w
  values=dict(sorted(values.items(),key=lambda item:-item[1])[:4]);total=sum(values.values())
  return {name:w/total for name,w in values.items()} if total else {'foot_'+side.lower():1.}
 for name,items in footwear.items():
  ob=g.merge(items,'Suneate_%s_01_%s'%(side,name))
  g.weight(ob,rig,weight_foot)
  colors=ob.data.color_attributes.new(name='ArmorTint',type='BYTE_COLOR',domain='CORNER')
  for c in colors.data:c.color=(0,0,0,1) if name in ('FootCovering','AnkleWraps') else (1,1,1,1)
  ob['asset']='Suneate_'+side+'_01';allparts[side].append(ob)
# Export evaluated copies with the native rig, retaining all editable components.
for side,parts in allparts.items():
 copies=[];deps=bpy.context.evaluated_depsgraph_get()
 for ob in parts:
  ev=ob.evaluated_get(deps);data=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
  cp=bpy.data.objects.new('export_part',data);source.objects.link(cp)
  cp.matrix_world=ob.matrix_world.copy()
  for group in ob.vertex_groups:cp.vertex_groups.new(name=group.name)
  copies.append(cp)
 g.select(copies);bpy.ops.object.join();cp=bpy.context.object;cp.name='Suneate_'+side+'_01'
 cp.parent=rig;cp.matrix_parent_inverse=Matrix.Identity(4);cp.matrix_basis=Matrix.Identity(4)
 mod=cp.modifiers.new('Native Manny calf','ARMATURE');mod.object=rig
 tri=cp.modifiers.new('FBX triangulation','TRIANGULATE');bpy.context.view_layer.objects.active=cp;bpy.ops.object.modifier_apply(modifier=tri.name)
 fbx(ART/'Exports'/('Suneate_'+side+'_01.fbx'),[rig,cp])
 print('EXPORTED',side,len(cp.data.vertices),sum(len(p.vertices)-2 for p in cp.data.polygons),flush=True)
 bpy.data.objects.remove(cp,do_unlink=True)
# Simple studio for saved source and clear deliverable views.
world=bpy.data.worlds.new('Charcoal studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.045,.052,.067,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
def track(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-2,-3,3),650,3),('Fill',(2,-1,1.8),450,2.5),('Rim',(0,2,2.4),750,2)]:
 data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc;data.energy=power;data.shape='DISK';data.size=size;track(ob,(0,0,.8))
data=bpy.data.cameras.new('Suneate_View');cam=bpy.data.objects.new('Suneate_View',data);studio.objects.link(cam);scene.camera=cam;data.type='ORTHO'
cam.location=(.95,-2,.95);data.ortho_scale=.91;track(cam,(0,-.035,.34))
for ob in source.objects:ob.select_set(False)
bpy.context.view_layer.objects.active=allparts['L'][0];allparts['L'][0].select_set(True)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=1.6;area.spaces.active.region_3d.view_location=Vector((0,0,.50))
   area.spaces.active.shading.type='MATERIAL'
scene.render.filepath=str(ART/'Review/source-threequarter.png')
for image in bpy.data.images:
 if image.source=='FILE':
  try:image.pack()
  except:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Suneate01.blend'))
sys.path.insert(0,str(ART.parent/'Sode01/Scripts'))
from sode_render_settings import configure
configure(scene)
bpy.ops.render.render(write_still=True)
cam.location=(0,-2,.62);data.ortho_scale=.88;track(cam,(0,-.04,.34));scene.render.filepath=str(ART/'Review/source-front.png');bpy.ops.render.render(write_still=True)
print('SUNEATE_PAIR_BUILT',flush=True)
