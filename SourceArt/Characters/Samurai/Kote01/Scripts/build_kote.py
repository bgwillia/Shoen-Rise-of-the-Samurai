"""Model the paired SHŌEN kote using the existing armor construction helpers."""
from pathlib import Path
import sys, math
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART.parent/'Do01/Scripts'))
import do_geometry as g
from export_do import fbx, common
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def coll(name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
fit=coll('Existing SHŌEN outfit • fit reference');source=coll('Kote01 • editable pair');studio=coll('Presentation')
with bpy.data.libraries.load(str(ART.parent/'Suneate01/Suneate01.blend'),link=False) as (a,b):
 b.objects=['root','Manny_Review','Kabuto_Review']+[n for n in a.objects if n.startswith(('Do_Review_','Sode_Review_','Kusazuri_01_','Suneate_'))]
 b.actions=['A_Idle','A_Walk','A_Run'];b.materials=['M_Kusazuri01']
for ob in b.objects:
 if ob:fit.objects.link(ob);ob.hide_set(False);ob.hide_render=ob.type=='ARMATURE'
for a in b.actions:a.use_fake_user=True
rig=bpy.data.objects['root'];body=bpy.data.objects['Manny_Review'];rig.animation_data_clear();rig.data.pose_position='REST'
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
for ob in fit.objects:
 for m in ob.modifiers:
  if m.type=='ARMATURE':m.object=rig
scene.frame_set(1);bpy.context.view_layer.update()
g.SOURCE=source;g.MATERIAL=bpy.data.materials['M_Kusazuri01'].copy();g.MATERIAL.name='M_Kote01'
for node in g.MATERIAL.node_tree.nodes:
 if node.type=='VALTORGB' and node.label.startswith('Lacquer'):
  min(node.color_ramp.elements,key=lambda e:abs(e.position-(4-.1)/15)).color=(.17,.15,.13,1)
allparts={}
# Build one anatomical construction and reflect its proportions for the mate.
shoulder,elbow,wrist=[rig.matrix_world@rig.data.bones[n+'_l'].head_local for n in ('upperarm','lowerarm','hand')]

def frame(a,b):
 d=(b-a).normalized();n=Vector((1,-.18,.25));n=(n-d*n.dot(d)).normalized();t=d.cross(n).normalized()
 # The transverse axis points toward the rear; negative theta presents front plates.
 if t.y<0:t=-t
 return d,n,t

for side,sign in [('L',1),('R',-1)]:
 groups={k:[] for k in ['Upper','Forearm','Straps','Lacing','Padding','Fittings']}
 bone='upperarm_'+side.lower()
 def reflect(p):return Vector((sign*p.x,p.y,p.z))
 def add(k,ob,bn=None):
  ob['kote_bone']=bn or bone;groups[k].append(ob);return ob
 def setup(a,b,profile):
  d,n,t=frame(a,b);length=(b-a).length
  def radius(f):
   for aa,bb in zip(profile,profile[1:]):
    if f<=bb[0]:
     v=max(0,min(1,(f-aa[0])/(bb[0]-aa[0])));return aa[1]+(bb[1]-aa[1])*v,aa[2]+(bb[2]-aa[2])*v
   return profile[-1][1:]
  def P(theta,f,off=0):
   rn,rt=radius(f);return reflect(a+d*(length*f)+n*((rn+off)*math.cos(theta))+t*((rt+off)*math.sin(theta)))
  return P,length
 def panel(name,P,ta,tb,fa,fb,tile=0,off=0,thick=.002,nx=6,ny=3,crown=0):
  vv=[];uv=[];ff=[]
  for j in range(ny+1):
   v=j/ny;f=fa+(fb-fa)*v
   for i in range(nx+1):
    u=i/nx;theta=ta+(tb-ta)*u
    vv.append(P(theta,f,off+crown*math.sin(math.pi*u)));uv.append((.04+.92*u,.96-.92*v))
  for j in range(ny):
   for i in range(nx):
    k=j*(nx+1)+i;ff.append((k,k+1,k+nx+2,k+nx+1))
  ob=g.mesh(name,vv,ff,tile,uv)
  outward=(P((ta+tb)/2,(fa+fb)/2,.01)-P((ta+tb)/2,(fa+fb)/2,0)).normalized()
  if ob.data.polygons[0].normal.dot(outward)<0:
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  return g.solid(ob,thick,.00045) if thick else ob
 def cord(name,P,angles,f,off=.008,r=.0017,tile=3):
  return g.tube(name,[P(t,f,off) for t in angles],r,tile,6)
 def hem(group,P,ta,tb,f,off=.007,r=.001,tile=2):
  return add(group,cord('Bound edge',P,[ta+(tb-ta)*i/40 for i in range(41)],f,off,r,tile))
 def trim(P,ta,tb,fa,fb):
  add('Fittings',panel('Leather backed trim',P,ta,tb,fa-.004,fb+.004,4,.006,.002,24,1))
  for j in range(10):
   a=ta+(tb-ta)*j/10;b=ta+(tb-ta)*(j+1)/10
   add('Fittings',panel('Chased bronze edging',P,a,b,fa,fb,11,.008,.0012,3,1))
  for f in [fa,fb]:hem('Fittings',P,ta,tb,f,.010,.00085)
 def lames(P,rows,cols,ta,tb,group):
  for row,(fa,fb) in enumerate(rows):
   for j in range(cols):
    a=ta+(tb-ta)*j/cols+.008;b=ta+(tb-ta)*(j+1)/cols-.008;mid=(a+b)/2
    add(group,panel('Lacquered lamellar %02d %02d'%(row,j),P,a,b,fa,fb,[8,9,13,14][(row+j)%4],.004+row*.0003,.0023,3,3,.0011))
    # Visible paired red fastening loops; woven texture supplies the fiber detail.
    f=fa+.026
    for delta in [-.031,.031]:
     pts=[P(mid+delta-.021,f-.015,.007),P(mid+delta-.024,f+.009,.010),P(mid+delta+.021,f+.012,.010),P(mid+delta+.023,f-.013,.007)]
     add('Lacing',g.tube('Dark red odoshi loop',g.path(pts,2),.0016,3,6))
    if row in [0,len(rows)-1]:add('Fittings',g.stud('Bronze plate fastening',P(mid,fb-.023,.009),.0012,2))
   hem('Lacing',P,ta,tb,fb-.009,.007,.00155,3)
 def straps(P,fs,ta=.83,tb=4.80):
  for f in fs:
   add('Straps',panel('Inner leather closure',P,ta,tb,f-.024,f+.024,4,.008,.0022,30,1))
   bt=-1.36
   add('Straps',panel('Directional strap tail',P,bt-.15,bt+.60,f-.019,f+.019,4,.013,.002,10,1))
   pts=[P(bt-.13,f-.032,.018),P(bt+.17,f-.032,.018),P(bt+.17,f+.032,.018),P(bt-.13,f+.032,.018)]
   add('Fittings',g.tube('Bronze buckle',pts,.00135,2,6,True))
   add('Fittings',g.tube('Buckle tongue',[P(bt-.11,f,.020),P(bt+.15,f,.020)],.0009,2,6))
   for t in [bt+.30,bt+.43,bt+.55]:add('Fittings',g.stud('Punched strap hole',P(t,f,.015),.0009,0))
 def crest(P,f,theta,r=.0185,length=.277):
  # The floral mon is built as a shallow curved medallion, not a floating sphere.
  def jewel(x,y,off):return P(theta+x/.076,f+y/length,off)
  for rad,off,tile in [(r,.009,11),(r*.84,.0105,2)]:
   vv=[jewel(0,0,off)];uv=[(.5,.5)]
   for i in range(40):
    a=math.tau*i/40;vv.append(jewel(rad*math.cos(a),rad*math.sin(a),off));uv.append((.5+.46*math.cos(a),.5+.46*math.sin(a)))
   ob=g.mesh('Floral crest medallion',vv,[(0,i+1,(i+1)%40+1) for i in range(40)],tile,uv);add('Fittings',g.solid(ob,.001,.0003))
  for rr in [r,.0058]:add('Fittings',g.tube('Raised crest bezel',[jewel(rr*math.cos(math.tau*i/40),rr*math.sin(math.tau*i/40),.012) for i in range(40)],.00085,2,6,True))
  for j in range(6):
   a=math.tau*j/6;pts=[]
   for i in range(14):
    b=math.tau*i/14;rr=.0088+.0051*math.cos(b);tt=.0034*math.sin(b)
    pts.append(jewel(rr*math.cos(a)-tt*math.sin(a),rr*math.sin(a)+tt*math.cos(a),.0125))
   add('Fittings',g.tube('Six-petal floral hardware',pts,.00095,2,6,True))
  add('Fittings',g.stud('Crest boss',jewel(0,0,.013),.0028,2))
 # Upper sleeve: shoulder armor remains the existing Sode, above this close sleeve.
 PU,lu=setup(shoulder,elbow,[(0,.078,.077),(.25,.077,.072),(.48,.072,.066),(.73,.064,.060),(1,.057,.055)])
 add('Padding',panel('Indigo upper sleeve',PU,-math.pi,math.pi,.075,.97,12,0,.0035,40,12))
 add('Upper',panel('Upper rounded lacquer cuff',PU,-1.70,1.83,.10,.285,0,.005,.0025,28,4))
 for f in [.105,.274]:hem('Upper',PU,-1.7,1.83,f,.008,.0014,0)
 hem('Lacing',PU,-1.70,1.83,.095,.008,.0018,3)
 crest(PU,.19,-.52,length=lu)
 lames(PU,[(.295,.433),(.432,.57),(.569,.707),(.706,.845)],13,-1.68,1.84,'Upper')
 trim(PU,-1.68,1.84,.813,.867)
 straps(PU,[.19,.81])
 # Forearm has a softer inner seam and an open elbow transition.
 bone='lowerarm_'+side.lower()
 PF,lf=setup(elbow,wrist,[(0,.055,.055),(.17,.062,.060),(.35,.061,.056),(.55,.054,.049),(.78,.043,.039),(1,.037,.034)])
 add('Padding',panel('Indigo forearm liner',PF,-math.pi,math.pi,.04,.988,12,0,.003,40,12))
 lames(PF,[(.16,.302),(.30,.442),(.44,.582),(.58,.722),(.72,.877)],12,-1.69,1.86,'Forearm')
 trim(PF,-1.72,1.88,.122,.180);trim(PF,-1.69,1.86,.85,.90)
 # Leather reinforced inner opening gives the palm side a different construction.
 for ta,tb in [(2.08,2.28),(-2.28,-2.08)]:add('Straps',panel('Inner leather reinforcing stay',PF,ta,tb,.14,.92,4,.003,.002,3,9))
 straps(PF,[.17,.52,.86])
 # Two major crossed cords, with a small indigo knot near the inner cuff.
 for phase in [-1,1]:
  points=[PF(-1.15+2.5*i/20 if phase==1 else 1.35-2.5*i/20,.41+.39*i/20,.012) for i in range(21)]
  add('Lacing',g.tube('Crossed securing cord',points,.0020,12,7))
 for delta in [-.04,.04]:
  points=[PF(-1.85+delta+.15*math.sin(math.tau*i/20),.23+.05*math.cos(math.tau*i/20),.015) for i in range(20)]
  add('Lacing',g.tube('Indigo closure knot',points,.0027,12,7,True))
 for t in [-1.88,-1.78]:add('Lacing',g.tube('Short cord tail',[PF(t,.25,.014),PF(t-.08,.32,.017),PF(t-.05,.39,.014)],.0021,12,7))
 for f in [.955,.986]:hem('Padding',PF,-math.pi,math.pi,f,.002,.0028,12)
 # The elbow liner follows the unchanged native elbow surface and weights.
 # This preserves Manny's corrective deformation through a deep arm bend.
 elbow_center=rig.matrix_world@rig.data.bones['lowerarm_'+side.lower()].head_local
 body_world=body.matrix_world.copy();normal_matrix=body_world.to_3x3().inverted().transposed()
 skin=[body_world@v.co for v in body.data.vertices]
 group_names={vg.index:vg.name for vg in body.vertex_groups};bone_names=set(rig.data.bones.keys())
 eligible={i for i,p in enumerate(skin) if p.x*sign>.20 and (p-elbow_center).length<.105}
 elbow_faces=[p for p in body.data.polygons if all(i in eligible for i in p.vertices)]
 used=sorted({i for p in elbow_faces for i in p.vertices});remap={old:new for new,old in enumerate(used)}
 vv=[skin[i]+(normal_matrix@body.data.vertices[i].normal).normalized()*.004 for i in used]
 ff=[tuple(remap[i] for i in p.vertices) for p in elbow_faces]
 soft=g.mesh('Kote_'+side+'_ElbowPadding',vv,ff,12)
 source_uv=body.data.uv_layers.active
 if source_uv:
  coords=[source_uv.data[li].uv for p in elbow_faces for li in p.loop_indices]
  u0=min(c.x for c in coords);u1=max(c.x for c in coords);v0=min(c.y for c in coords);v1=max(c.y for c in coords)
  target_uv=soft.data.uv_layers.active.data
  for old,new in zip(elbow_faces,soft.data.polygons):
   for src,dst in zip(old.loop_indices,new.loop_indices):
    c=source_uv.data[src].uv;target_uv[dst].uv=g.uvcoord(12,(c.x-u0)/max(u1-u0,1e-6),(c.y-v0)/max(v1-v0,1e-6))
 weights=[{group_names[w.group]:w.weight for w in body.data.vertices[i].groups if group_names[w.group] in bone_names} for i in used]
 g.weight(soft,rig,per_vertex=weights)
 soft['asset']='Kote_'+side+'_01';parts=[soft]
 # Merge by named system and rigid bone. Joining in rest retains clean rigid skinning.
 for key,items in groups.items():
  partitions={bn:[o for o in items if o['kote_bone']==bn] for bn in sorted(set(o['kote_bone'] for o in items))}
  for bn,selected in partitions.items():
   name='Kote_'+side+'_'+key+('_Upper' if bn.startswith('upper') and key not in ['Upper'] else '_Forearm' if bn.startswith('lower') and key not in ['Forearm'] else '')
   ob=g.merge(selected,name);g.weight(ob,rig,lambda p,bn=bn:{bn:1.});ob['asset']='Kote_'+side+'_01';parts.append(ob)
 allparts[side]=parts
 print('MODELED_SLEEVE',side,flush=True)

sys.path.insert(0,str(ART/'Scripts'))
from kote_hand import build_hands
hands=build_hands(rig,body,g)
for side in ['L','R']:allparts[side].extend(hands[side])
for side,parts in allparts.items():
 for ob in parts:
  common.surface_normals(ob)
  ob['anatomical_side']='left' if side=='L' else 'right'
  colors=ob.data.color_attributes.get('ArmorTint') or ob.data.color_attributes.new(name='ArmorTint',type='BYTE_COLOR',domain='CORNER')
  for c in colors.data:c.color=(1,1,1,1)
 # Export a joined evaluated copy, preserving editable source objects.
 copies=[];deps=bpy.context.evaluated_depsgraph_get()
 for ob in parts:
  data=bpy.data.meshes.new_from_object(ob.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
  cp=bpy.data.objects.new('export_part',data);source.objects.link(cp);cp.matrix_world=ob.matrix_world.copy()
  for group in ob.vertex_groups:cp.vertex_groups.new(name=group.name)
  copies.append(cp)
 g.select(copies);bpy.ops.object.join();cp=bpy.context.object;cp.name='Kote_'+side+'_01'
 cp.parent=rig;cp.matrix_parent_inverse=Matrix.Identity(4);cp.matrix_basis=Matrix.Identity(4)
 mod=cp.modifiers.new('Native Manny arm and hand','ARMATURE');mod.object=rig
 common.repair_edge_uvs(cp);common.surface_normals(cp)
 fbx(ART/'Exports'/('Kote_'+side+'_01.fbx'),[rig,cp])
 print('EXPORTED_KOTE',side,len(cp.data.vertices),sum(len(p.vertices)-2 for p in cp.data.polygons),flush=True)
 bpy.data.objects.remove(cp,do_unlink=True)
world=bpy.data.worlds.new('Charcoal studio');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.035,.042,.060,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35

def track(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-2,-3,3),500,3),('Fill',(2,-1,1.8),330,2.5),('Rim',(0,2,2.4),600,2)]:
 data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc;data.energy=power;data.shape='DISK';data.size=size;track(ob,(0,0,1.25))
data=bpy.data.cameras.new('Kote_View');cam=bpy.data.objects.new('Kote_View',data);studio.objects.link(cam);scene.camera=cam;data.type='ORTHO'
cam.location=(1.9,-3,1.8);data.ortho_scale=1.62;track(cam,(0,-.04,1.26))
for ob in source.objects:ob.select_set(False)
allparts['L'][1].select_set(True);bpy.context.view_layer.objects.active=allparts['L'][1]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=2.6;area.spaces.active.region_3d.view_location=Vector((0,0,1.2));area.spaces.active.shading.type='MATERIAL'
for im in bpy.data.images:
 if im.source=='FILE':
  try:im.pack()
  except:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Kote01.blend'))
sys.path.insert(0,str(ART.parent/'Sode01/Scripts'))
from sode_render_settings import configure
configure(scene)
scene.render.filepath=str(ART/'Review/source-threequarter.png');bpy.ops.render.render(write_still=True)
# A clear arm-only view makes inner / outer construction readable in one source image.
for ob in fit.objects:ob.hide_render=True
cam.location=(1.5,-3,1.9);data.ortho_scale=1.40;track(cam,(0,-.1,1.19))
scene.render.filepath=str(ART/'Review/source-pair.png');bpy.ops.render.render(write_still=True)
print('KOTE_PAIR_BUILT',flush=True)
