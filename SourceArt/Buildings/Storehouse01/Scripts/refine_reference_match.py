"""User-directed visual revision: proportions, fieldstone and controlled material wear."""
from pathlib import Path
import sys, math, random, ast
import bpy,bmesh
from mathutils import Vector
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/storehouse01'
bpy.ops.wm.open_mainfile(filepath=str(ART/'Storehouse01.blend'))
scene=bpy.context.scene;src=bpy.data.collections['Storehouse_01 • modular exterior'];props=bpy.data.collections['SH01_Props • reusable exterior pieces'];groups={}
random.seed(1187)
mats={n:bpy.data.materials['RH01_'+n] for n in ['Thatch','Timber','Plaster','Stone','Rope']};mats['Iron']=bpy.data.materials['SH01_Iron']
kit_code=(ART.parent/'RuralHouse01/Scripts/model_house.py').read_text()
for node in ast.parse(kit_code).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','tube','beam'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'ruralhouse-kit','exec'))
# Replace regular block footings; keep all the kit timber posts.
foundation=bpy.data.objects['SH01_Foundation'];bm=bmesh.new();bm.from_mesh(foundation.data)
stone_slots=[i for i,m in enumerate(foundation.data.materials) if m and m.name=='RH01_Stone']
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in stone_slots],context='FACES')
bm.to_mesh(foundation.data);bm.free()
def fieldstone(name,center,radii):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
 ob=bpy.context.object;ob.name=name
 for c in list(ob.users_collection):c.objects.unlink(ob)
 src.objects.link(ob);ob.data.materials.append(mats['Stone'])
 for v in ob.data.vertices:
  p=v.co;ang=math.atan2(p.y,p.x);r=1+.09*math.sin(ang*3+center[0]*4)+random.uniform(-.07,.07)
  p.x*=r*radii[0];p.y*=r*radii[1];p.z=max(-.77,min(.70,p.z))*radii[2]
  p+=Vector(center)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 uv=ob.data.uv_layers.new(name='UVMap')
 for f in ob.data.polygons:
  axis=max(range(3),key=lambda i:abs(f.normal[i]))
  for li in f.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   uv.data[li].uv=(p.y*2,p.z*2) if axis==0 else (p.x*2,p.z*2) if axis==1 else (p.x*2,p.y*2)
  f.use_smooth=True
 mod=ob.modifiers.new('Fieldstone broad faces','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=20
 bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
 groups.setdefault('Fieldstone',[]).append(ob)
for x in [-1.43,0,1.43]:
 for y in [-1.55,1.55]:
  fieldstone('Uneven bedded footing',(x,y,.14),(.30,.28,.18))
  fieldstone('Split upper footing',(x-.078,y+.02,.305),(.155,.22,.135))
  fieldstone('Split upper footing',(x+.105,y-.025,.30),(.14,.215,.135))
for x in [-1.43,1.43]:fieldstone('Middle fieldstone',(x,0,.16),(.29,.27,.20))
for x in [-.57,.57]:fieldstone('Stair resting slab',(x,-2.55,.062),(.21,.23,.076))
# Pointed forged hinge terminals and flattened rivets; visibly heavier closed doors.
for side in [-1,1]:
 for z in [1.22,2.26]:
  x=side*.145;y=-1.703
  mesh('Pointed hinge terminal',[(x-side*.07,y,z),(x,y,z+.045),(x+side*.05,y,z),(x,y,z-.045)],[(0,1,2,3)],'Iron',group='DoorDetail')
 for z in [1.40,1.68]:
  x=side*.15;y=-1.711
  mesh('Diamond escutcheon',[(x-.055,y,z),(x,y,z+.065),(x+.055,y,z),(x,y,z-.065)],[(0,1,2,3)],'Iron',group='DoorDetail')
 for j in range(7):
  x=side*(.10+random.random()*.51);z=1.06+random.random()*.82;length=random.uniform(.11,.34);width=random.uniform(.0018,.004)
  mesh('Timber drying split',[(x,-1.658,z),(x-width,-1.658,z+length*.4),(x+.002,-1.658,z+length),(x+width,-1.658,z+length*.55)],[(0,1,2,3)],'Iron',group='DoorDetail')
# Fine loose straw along both gable edges, small silhouette changes only.
for side in [-1,1]:
 normal=Vector((side*1.15,0,2.1)).normalized()
 for end in [-1,1]:
  for i in range(70):
   v=(i+random.random())/70
   p=Vector((side*2.1*(1-v),end*2.05,2.71+1.15*v))+normal*(.115*math.sin(v*math.pi)-random.uniform(.015,.25))
   for k in range(2):
    a=p+Vector((random.uniform(-.016,.016),end*random.uniform(.01,.052),random.uniform(-.015,.01)))
    b=a+Vector((-side*random.uniform(.025,.065),-end*.025,random.uniform(.025,.06)))
    tube('Loose gable reed',[a-Vector((0,0,random.uniform(.005,.027))),b],random.uniform(.0018,.0032),'Thatch','LooseThatch',5)
# Join only each edit's logical component.
for name,obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name='SH01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
# Narrow the near-square body, shorten roof depth, lower platform 13cm,
# and steepen the upper silhouette. Origin stays at the original ground center.
all_art=list(src.objects)+list(props.objects)
for ob in all_art:
 for v in ob.data.vertices:
  p=v.co;p.x*=.92;p.y*=.94
  if p.z>.55:p.z-=min(.13,(p.z-.55)*.5)
  if p.z>2.57:p.z=2.57+(p.z-2.57)*1.12
# Make the ridge poles visually lighter while retaining their authored joints.
# Narrow individual disconnected ridge pieces around their centres.
def islands(ob):
 parent=list(range(len(ob.data.vertices)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for e in ob.data.edges:
  a,b=map(find,e.vertices)
  if a!=b:parent[b]=a
 groups={}
 for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
 return list(groups.values())
ridge=bpy.data.objects['SH01_Ridge']
for indices in islands(ridge):
 coords=[ridge.data.vertices[i].co for i in indices];center=sum(coords,Vector())/len(coords)
 ext=[max(p[a] for p in coords)-min(p[a] for p in coords) for a in range(3)];longaxis=max(range(3),key=lambda a:ext[a])
 # Preserve central straw ridge; reduce only timber cross-section.
 for i in indices:
  p=ridge.data.vertices[i].co
  for a in range(3):
   if a!=longaxis:p[a]=center[a]+(p[a]-center[a])*.79
# Shared texture maps, per-component colour variation; no new texture set.
variants={}
for family in ['Thatch','Timber','Plaster','Stone']:
 original=mats[family];m=original.copy();m.name='SH01_'+family
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 old=p.inputs['Base Color'].links[0].from_socket
 col=n.new('ShaderNodeVertexColor');col.layer_name='Color';col.label='Broad material wear from authored mesh'
 mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1
 l.new(old,mult.inputs[1]);l.new(col.outputs['Color'],mult.inputs[2]);l.new(mult.outputs['Color'],p.inputs['Base Color'])
 for node in n:
  if node.bl_idname=='ShaderNodeNormalMap':node.inputs['Strength'].default_value=.5
 variants[family]=m
for ob in all_art:
 for slot in ob.material_slots:
  if slot.material and slot.material.name.startswith('RH01_'):
   family=slot.material.name.removeprefix('RH01_')
   if family in variants:slot.material=variants[family]
 colors=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 variation={}
 for indices in islands(ob):
  k=random.uniform(.84,1.08)
  for i in indices:variation[i]=k
 for face in ob.data.polygons:
  mat=ob.data.materials[face.material_index];family=mat.name.split('_',1)[1] if mat else ''
  for li in face.loop_indices:
   vi=ob.data.loops[li].vertex_index;p=ob.data.vertices[vi].co;k=variation.get(vi,1)
   if family=='Timber':
    damp=.83+.17*min(1,max(0,p.z)/.6);rgb=(.78*k*damp,.71*k*damp,.61*k*damp)
   elif family=='Thatch':
    k=.94+.05*math.sin(p.y*3+p.x*1.6)+.035*math.cos(p.y*5-p.x);rgb=(.78*k,.72*k,.60*k)
   elif family=='Stone':rgb=(.70*k,.70*k,.65*k)
   elif family=='Plaster':
    edge=min(abs(abs(p.x)-1.315),abs(abs(p.y)-1.45));height=max(0,min(1,(p.z-.83)/.52))
    wear=.75+.25*height;wear*=.87+.13*min(1,edge/.17)
    cloud=.965+.035*math.sin(p.x*6+p.z*3)*math.sin(p.y*4-p.z*6)
    rgb=(.96*wear*cloud,.92*wear*cloud,.82*wear*cloud)
   else:rgb=(1,1,1)
   colors.data[li].color=(*[min(1,max(0,c)) for c in rgb],1)
 ob.data.color_attributes.active_color=colors
# Neutral dark studio, warmer daylight and less ambient wash, no stage dressing.
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.23,.27,.31,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
bpy.data.lights['Daylight'].energy=1350;bpy.data.lights['Daylight'].color=(1,.87,.70);bpy.data.lights['Daylight'].size=5
bpy.data.lights['Sun'].energy=1.7;bpy.data.lights['Sun'].color=(1,.90,.77)
ground=bpy.data.materials['Review earth'];ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.039,.046,.042,1)
scene.view_settings.exposure=.35;scene.cycles.samples=48
for name in ['Front','Three-quarter','Side','Rear','Roof']:
 cam=bpy.data.objects[name];cam.data.ortho_scale*=.95
scene.camera=bpy.data.objects['Three-quarter']
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for obs,path in [(list(src.objects),'Storehouse_01.fbx'),(list(props.objects),'SH01_Props.fbx')]:
 for o in obs:o.modifiers.new('Export triangulation','TRIANGULATE')
 fbx(ART/'Exports'/path,obs)
 for o in obs:o.modifiers.remove(o.modifiers['Export triangulation'])
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Storehouse01.blend'))
for name,label in [('Three-quarter','three-quarter'),('Front','front'),('Side','side'),('Rear','rear'),('Roof','roof')]:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(OUT/('storehouse-'+label+'.png'));bpy.ops.render.render(write_still=True)
print('REFERENCE_MATCH_REVISION_SAVED',flush=True)
