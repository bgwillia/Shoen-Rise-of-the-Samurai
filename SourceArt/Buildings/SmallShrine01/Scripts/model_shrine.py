"""SmallShrine01: authored exterior using the established SHŌEN rural material kit."""
from pathlib import Path
import ast, math, random, sys, json
import bpy, bmesh
from mathutils import Vector
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'; STORE=ART.parent/'Storehouse01'; OUT=ROOT/'artifacts/smallshrine01'
random.seed(1180)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=64; scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
src=bpy.data.collections.new('SmallShrine_01 • editable exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • excluded from runtime');scene.collection.children.link(studio)
groups={}
with bpy.data.libraries.load(str(STORE/'Storehouse01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Stone','SH01_Iron','RH01_Rope']]
mats={m.name.split('_',1)[1]:m for m in b.materials}
m=bpy.data.materials.new('SR01_Paper');m.use_nodes=True;m.diffuse_color=(.72,.68,.56,1)
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.72,.68,.56,1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.93;mats['Paper']=m
for node in ast.parse((KIT/'Scripts/model_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','beam','tube','lash','stone'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
for node in ast.parse((STORE/'Scripts/refine_reference_match.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='fieldstone':
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-storehouse-kit','exec'))
def block(name,center,size,mat='Timber',group='MainShrine',bevel=.01):
 x,y,z=center;sx,sy,sz=[s/2 for s in size]
 vv=[(x+a*sx,y+b*sy,z+c*sz) for c in [-1,1] for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 ob=mesh(name,vv,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,group=group)
 # Box projected UVs keep the reused stone and wood grain legible on horizontal faces.
 for f in ob.data.polygons:
  axis=max(range(3),key=lambda i:abs(f.normal[i]))
  for li in f.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   ob.data.uv_layers.active.data[li].uv=(p.y,p.z) if axis==0 else (p.x,p.z) if axis==1 else (p.x,p.y)
 if bevel:
  mod=ob.modifiers.new('Softened hand cut edges','BEVEL');mod.width=bevel;mod.segments=2
 return ob
# Consistent real-world wood grain, with a different crop on each hand-cut piece.
kit_beam=beam
def beam(name,a,b,width,depth=None,mat='Timber',group='Wall_Frame',rough=.003):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat=='Timber':
  offx=random.uniform(0,1);offy=random.uniform(0,1)
  for item in ob.data.uv_layers.active.data:
   item.uv.x=item.uv.x*max(.24,width*3.0)+offx
   item.uv.y=item.uv.y*.58+offy
 return ob
# Angular weathered fieldstone replaces the rounded placeholder masonry.
def fieldstone(name,center,radii):
 sx,sy,sz=radii;cx,cy,cz=center
 ring=[(-1,-.67),(-.66,-1),(.56,-1),(1,-.68),(1,.65),(.66,1),(-.67,1),(-1,.63)]
 vv=[]
 for h in [-.90,.63]:
  for x,y in ring:
   vv.append((cx+x*sx*random.uniform(.92,1.04),cy+y*sy*random.uniform(.92,1.04),cz+h*sz+random.uniform(-.018,.018)))
 faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
 ob=mesh(name,vv,faces,'Stone',group='Fieldstone')
 for f in ob.data.polygons:
  axis=max(range(3),key=lambda i:abs(f.normal[i]))
  for li in f.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   ob.data.uv_layers.active.data[li].uv=(p.y*2,p.z*2) if axis==0 else (p.x*2,p.z*2) if axis==1 else (p.x*2,p.y*2)
 bevel=ob.modifiers.new('Weather softened stone arrises','BEVEL');bevel.width=.018;bevel.segments=3
 normal=ob.modifiers.new('Broad natural stone faces','WEIGHTED_NORMAL');normal.keep_sharp=True
 tone=ob.data.color_attributes.new(name='ArtTint',type='FLOAT_COLOR',domain='CORNER')
 k=random.uniform(.65,1.12)
 for c in tone.data:c.color=(k,k*.98,k*.95,1)
 return ob
# Small, three-course dry stone plinth; no massive temple terrace.
for row in range(3):
 z=.105+row*.165+random.uniform(-.009,.009)
 for side in [-1,1]:
  for i in range(9):
   x=-1.48+i*.365+(row%2)*.05+random.uniform(-.027,.027)
   fieldstone('Bedded fieldstone',(x,side*1.37,z),(.205+random.uniform(-.015,.02),.21,random.uniform(.115,.145)))
  for i in range(6):
   fieldstone('Side plinth fieldstone',(side*1.52,-1.01+i*.40,z),(.21,.235,.13))
# Stone cap and timber bearers, deliberately separate from the wall shell.
for i in range(8):
 for y in [-1.40,1.40]:block('Plinth coping',(-1.41+i*.403,y,.53),(.395,.36,.12),'Stone','Platform',.028)
for x in [-1.51,1.51]:block('Side coping',(x,0,.53),(.35,2.48,.12),'Stone','Platform',.028)
for x in [-1.29,0,1.29]:
 for y in [-1.19,1.18]:beam('Platform short support',(x,y,.54),(x,y,.79),.18,group='Platform')
for y in [-1.20,0,1.20]:beam('Platform bearer',(-1.64,y,.71),(1.64,y,.71),.17,.19,group='Platform')
for i in range(19):
 x=-1.575+i*.175
 beam('Raised veranda floorboard',(x,-1.49,.815),(x,1.47,.815),.170,.075,group='Platform',rough=.002)
for y in [-1.48,1.48]:beam('Veranda front fascia',(-1.67,y,.76),(1.67,y,.76),.14,.16,group='Platform')
# Five modest treads, 16 cm rises; worn shoulders frame the entry.
for i in range(5):
 y=-2.70+i*.275;h=.16*(i+1)
 for side in [-1,1]:
  block('Stair split stone tread',(side*.335,y,h-.075),(.66,.305,.15),'Stone','Steps',.025)
  block('Stair cheek stone',(side*.79,y,h-.10),(.22,.29,.20),'Stone','Steps',.025)
# Narrow shrine body, plank exterior and a closed double door.
for x in [-1.045,1.045]:
 for y in [-.72,1.02]:beam('Shrine principal post',(x,y,.85),(x,y,2.69),.16,.17,group='MainShrine',rough=.003)
for y in [-.72,1.02]:
 for z in [.99,2.39,2.63]:beam('Shrine wall crossrail',(-1.13,y,z),(1.13,y,z),.115,.15,group='MainShrine',rough=.003)
for x in [-1.045,1.045]:
 for z in [.98,1.62,2.39,2.63]:beam('Shrine side rail',(x,-.79,z),(x,1.10,z),.11,.13,group='MainShrine',rough=.002)
 for i in range(12):
  y=-.665+i*.146
  beam('Side vertical cedar board',(x,y,1.03),(x,y,2.57),.064,.143,group='WallBoards',rough=.002)
for i in range(14):
 x=-.965+i*.1485
 beam('Rear cedar weatherboard',(x,1.023,1.03),(x,1.023,2.57),.145,.055,group='WallBoards',rough=.002)
for x in [-.985,-.845,.845,.985]:beam('Front outside board',(x,-.727,1.03),(x,-.727,2.57),.14,.065,group='WallBoards',rough=.002)
for x in [-.737,.737]:beam('Entrance jamb',(x,-.805,.98),(x,-.805,2.40),.135,.16,group='Door')
for z in [1.015,2.335]:beam('Door sill and head',(-.805,-.816,z),(.805,-.816,z),.14,.13,group='Door')
for i in range(10):
 x=-.654+i*.145
 beam('Closed shrine door plank',(x,-.752,1.075),(x,-.752,2.29),.140,.069,group='Door',rough=.002)
for side in [-1,1]:
 for z in [1.21,2.14]:
  beam('Door panel rail',(side*.08,-.807,z),(side*.68,-.807,z),.075,.051,group='Door')
  block('Restrained iron hinge',(side*.625,-.841,z),(.18,.012,.035),'Iron','Door',.003)
 for z in [1.54,1.73]:block('Door handle plate',(side*.1,-.802,z),(.045,.018,.066),'Iron','Door',.005)
 tube('Door forged handle',[(side*.10,-.83,1.55),(side*.1,-.87,1.58),(side*.1,-.87,1.69),(side*.1,-.83,1.72)],.009,'Iron','Door',6)
# Structural porch columns, bracket blocks and exposed joinery.
for x in [-1.27,1.27]:
 beam('Porch upright',(x,-1.25,.85),(x,-1.25,2.57),.13,.14,group='MainShrine',rough=.003)
 block('Porch bracket capital',(x,-1.25,2.57),(.29,.27,.11),group='RoofTimber')
 for side in [-1,1]:beam('Timber bracket arm',(x,-1.25,2.43),(x+side*.25,-1.25,2.65),.08,.07,group='RoofTimber')
beam('Porch header',(-1.47,-1.25,2.63),(1.47,-1.25,2.63),.14,.19,group='RoofTimber')
# Primary reference: long-eave entrance, side gables and layered roof.
sys.path.insert(0,str(ART/'Scripts'))
from shrine_roof import build_roof
build_roof(globals())
# Low, intentional veranda railing with a clear opening above the stair.
for x in [-1.52,1.52]:
 for y in [-1.39,-.50,.48,1.36]:
  beam('Veranda baluster',(x,y,.82),(x,y,1.42),.072,group='Railing',rough=.001)
  block('Baluster cap',(x,y,1.435),(.11,.11,.045),group='Railing',bevel=.008)
 for z in [1.03,1.32]:beam('Side veranda rail',(x,-1.44,z),(x,1.44,z),.055,.072,group='Railing',rough=.002)
for y in [-1.39,1.36]:
 segments=[(-1.53,-.72),(.72,1.53)] if y<0 else [(-1.53,1.53)]
 for xa,xb in segments:
  for z in [1.03,1.32]:beam('End veranda rail',(xa,y,z),(xb,y,z),.055,.072,group='Railing')
  n=max(1,round((xb-xa)/.38))
  for i in range(n+1):beam('End rail upright',(xa+(xb-xa)*i/n,y,.83),(xa+(xb-xa)*i/n,y,1.39),.05,group='Railing',rough=.001)
# A few visible pegged joints, without ornamental carving.
for x in [-1.05,1.05]:
 for z in [1.02,2.39,2.63]:tube('Hand driven timber peg',[(x,-.79,z),(x,-.815,z)],.014,'Timber','MainShrine',8)
sys.path.insert(0,str(ART/'Scripts'))
from shrine_props import build_props
prop_pivots=build_props(globals())
from shrine_finish import finish_shrine
finish_shrine(globals())
# Join by useful source component, retaining all separate buildings and props.
for name,obs in list(groups.items()):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object
 ob.name=name if name.startswith(('SR01_','Torii_','OfferingBox_','StoneLantern_')) else 'SR01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 ob['scope']='Exterior only; authored modular shrine'
# Reuse the established vertex-tinted rural materials with slightly richer timber.
for ob in src.objects:
 color=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for face in ob.data.polygons:
  family=ob.data.materials[face.material_index].name.split('_',1)[1]
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.93+.05*math.sin(p.x*4.4+p.y*3.1+p.z*1.7)
   if family=='Timber':rgb=(.53*k,.45*k,.35*k)
   elif family=='Thatch':rgb=(.43*k,.34*k,.24*k)
   elif family=='Stone':
    moss=max(0,.5+.5*math.sin(p.x*8+p.y*7+p.z*14))*.22 if p.z<.7 else .035
    rgb=(.73*k-moss*.65,.72*k-moss*.20,.67*k-moss*.70)
   else:rgb=(1,1,1)
   tone=ob.data.color_attributes.get('ArtTint')
   if tone and tone.data[li].color[3]>.5:rgb=tuple(rgb[a]*tone.data[li].color[a] for a in range(3))
   color.data[li].color=(*rgb,1)
 ob.data.color_attributes.active_color=color
# Runtime exports stay separate from the editable source arrangement.
components=list(src.objects)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
props_prefixes=('Torii_','OfferingBox_','StoneLantern_','SR01_Fence','SR01_Banner')
main=[o for o in components if not o.name.startswith(props_prefixes)]
def export(name,objects,pivot=(0,0,0)):
 copies=[]
 for ob in objects:
  copy=ob.copy();copy.data=ob.data.copy();src.objects.link(copy)
  for colors in list(copy.data.color_attributes):
   if colors.name!='Color':copy.data.color_attributes.remove(colors)
  for v in copy.data.vertices:v.co-=Vector(pivot)
  copy.modifiers.new('Export triangles','TRIANGULATE');copies.append(copy)
 fbx(ART/'Exports'/f'{name}.fbx',copies)
 for ob in copies:bpy.data.objects.remove(ob,do_unlink=True)
export('SmallShrine_01',main)
# Prop export membership/pivots are provided alongside their authored arrangement.
instances=[{'name':'Main shrine','mesh':'SmallShrine_01','location':[0,0,0]}]
for name,pivot in prop_pivots.items():
 if name in ('SR01_Shimenawa','SR01_Shimenawa_Shides'):continue
 mesh_name='StoneLantern_01' if name=='StoneLantern_02' else name
 if name!='StoneLantern_02':export(mesh_name,[bpy.data.objects[name]],pivot)
 instances.append({'name':name,'mesh':mesh_name,'location':list(pivot)})
(ART/'Exports/assembly.json').write_text(json.dumps({'instances':instances},indent=2))
# Simple source review daylight, not exported.
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review earth'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.085,.091,.073,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Soft rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.48,.56,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
for name,loc,power,size,color in [('Large warm daylight',(-3,-6,9),1200,5,(1,.91,.79)),('Sky fill',(5,-4,5),950,6,(.83,.9,1)),('Ridge separation',(2,5,7),850,4,(1,.94,.82))]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;d.color=color;o.rotation_euler=(Vector((0,-.5,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
sun=bpy.data.lights.new('Afternoon sun','SUN');so=bpy.data.objects.new('Afternoon sun',sun);studio.objects.link(so);so.rotation_euler=(.35,-.45,-.6);sun.energy=2.5;sun.angle=.13
cd=bpy.data.cameras.new('Shrine three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(-11.3,-11.5,4.8);cam.rotation_euler=(Vector((0,-.6,1.9))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='PERSP';cd.lens=58;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='SmallShrine_01; exterior only; compact rural shrine, reused village materials; modular Torii, lantern, offering box, fence.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'SmallShrine01.blend'))
print('SHRINE_SAVED',len(components),'editable components',flush=True)
scene.render.filepath=str(OUT/'shrine-three-quarter.png');bpy.ops.render.render(write_still=True)
print('SHRINE_COMPLETE',flush=True)
