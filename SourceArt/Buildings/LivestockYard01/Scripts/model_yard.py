"""One authored LivestockYard01 art pass, assembled from the existing rural kit."""
from pathlib import Path
import ast, json, math, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix

ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
FARM=ART.parent/'FarmCompound01'; SMITHY=ART.parent/'Smithy01'
OUT=ROOT/'artifacts/livestockyard01'; OUT.mkdir(parents=True,exist_ok=True)
random.seed(1180916)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=2000;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
src=bpy.data.collections.new('LivestockYard_01 • modular exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • lighting and ground');scene.collection.children.link(studio)
groups={};modules={};instances=[]
with bpy.data.libraries.load(str(FARM/'FarmCompound01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope','SM01_Water','FC01_Dirt']]
 b.collections=['FC01_WaterTrough','FC01_Baskets','FC01_HayBundles','FC01_Fence_Straight','FC01_Fence_Gate']
mats={m.name.split('_',1)[1]:m for m in b.materials}
kit_collections={c.name:c for c in b.collections}
with bpy.data.libraries.load(str(SMITHY/'Smithy01.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if n in ['SM01_Roof','SM01_RoofBundles','SM01_RoofEaves','SM01_RoofGableThatch','SM01_Ridge','SM01_RidgeLashings']]
roof_objects=list(b.objects)
# Use the same mesh-authoring helpers and export settings as FarmCompound01.
for file,names in [(ART.parent/'RuralHouse01/Scripts/model_house.py',{'mesh','beam','tube','lash','panel'}),
                   (ART.parent/'Storehouse01/Scripts/refine_reference_match.py',{'fieldstone'}),
                   (FARM/'Scripts/model_farm.py',{'plank_roof','tint'})]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:
   exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
mud=mats['Dirt'].copy();mud.name='LY01_Mud';mats['Mud']=mud
for n in mud.node_tree.nodes:
 if n.type=='VALTORGB':
  n.color_ramp.elements[0].color=(.035,.023,.013,1)
  n.color_ramp.elements[-1].color=(.16,.105,.052,1)
nodes=mud.node_tree.nodes;links=mud.node_tree.links;bs=nodes['Principled BSDF']
nodes['Noise Texture'].inputs['Scale'].default_value=.9
nodes['Noise Texture.001'].inputs['Scale'].default_value=120
nodes['Bump'].inputs['Strength'].default_value=.65
nodes['Bump'].inputs['Distance'].default_value=.032
attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='Color'
multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
links.new(nodes['Color Ramp'].outputs['Color'],multiply.inputs[1]);links.new(attr.outputs['Color'],multiply.inputs[2]);links.new(multiply.outputs[0],bs.inputs['Base Color'])
rough=nodes.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=1;rough.inputs['To Min'].default_value=.48;rough.inputs['To Max'].default_value=.95
links.new(attr.outputs['Alpha'],rough.inputs['Value']);links.new(rough.outputs['Result'],bs.inputs['Roughness'])

def start():return set(o.name for o in src.objects)
def finish(before,key):modules.setdefault(key,[]).extend(o for o in src.objects if o.name not in before)
def clone_objects(originals,key,scale=(1,1,1),shift=(0,0,0),rotation=0):
 result=[];mat=Matrix.Translation(Vector(shift))@Matrix.Rotation(math.radians(rotation),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in originals:
  ob=original.copy();ob.data=original.data.copy();ob.matrix_world=Matrix.Identity(4)
  ob.name='LY01_'+key+' • '+original.name;src.objects.link(ob)
  for v in ob.data.vertices:v.co=mat@v.co
  # Existing materials may have been appended along with geometry; share the rural originals.
  for i,m in enumerate(ob.data.materials):
   name=m.name.split('.')[0];family=name.split('_',1)[1] if '_' in name else ''
   if family in mats:ob.data.materials[i]=mats[family]
  ob['reused_from']='FarmCompound01 / Smithy01 rural kit';result.append(ob)
 return result
def kit(key):return list(kit_collections['FC01_'+key].objects)

# Broad low roof from the existing thatch system, separate from the shelter framing.
modules['Roof']=clone_objects(roof_objects,'Roof',(1.16,.88,.87))
# A low, broad weather shelter: finer reused reed texture and restrained uneven eaves.
for ob in modules['Roof']:
 for v in ob.data.vertices:
  p=v.co;p.z=2.34+(p.z-2.18)*.80+.018*math.sin(p.x*2.3+p.y*.8)
 for layer in ob.data.uv_layers:
  for uv in layer.data:uv.uv*=1.65
before=start()
for side in [-1,1]:
 for t in [.14,.51,.84]:
  y=side*1.82*(1-t);z=2.34+1.26*.87*t*.80+.11*math.sin(t*math.pi)+.03
  tube('Weathered roof retaining pole',[(-3.26,y,z),(0,y+.012,z+.026),(3.26,y-.009,z)],.026,'Timber','RoofBattens',8)
finish(before,'Roof')
before=start()
# Six structural posts leave the animal-facing front completely open.
for x in [-2.58,0,2.58]:
 for y in [-1.24,1.24]:
  fieldstone('Shelter bedded footing',(x,y,.075),(.19,.21,.115))
  beam('Shelter hewn upright',(x,y,.12),(x+random.uniform(-.012,.012),y,2.34),.17,.18,group='Shelter')
  for d in [-1,1]:
   if -2.6<x+d*.39<2.6:
    beam('Shelter pegged knee',(x,y,1.91),(x+d*.39,y,2.31),.10,.095,group='Shelter')
for y in [-1.24,1.24]:
 beam('Shelter long wall plate',(-2.80,y,2.31),(2.80,y,2.31),.20,.20,group='Shelter')
for x in [-2.58,0,2.58]:
 beam('Shelter cross tie',(x,-1.40,2.33),(x,1.40,2.33),.15,.16,group='Shelter')
 beam('Shelter king post',(x,0,2.31),(x,0,3.21),.13,group='Shelter')
 for side in [-1,1]:
  beam('Shelter roof rafter',(x,side*1.78,2.31),(x,0,3.22),.13,.14,group='Shelter')
  beam('Shelter side knee',(x,side*1.24,1.78),(x,side*.88,2.15),.085,group='Shelter')
# Partial board/wattle back breaks the wind; no enclosed room or interior floor.
for left,right in [(-2.51,-.08),(.08,2.51)]:
 ob=panel('Shelter weathered rear infill',(right,1.245),(left,1.245),.34,1.71)
 mod=ob.modifiers.new('Exterior wattle thickness','SOLIDIFY');mod.thickness=.045
for i in range(35):
 x=-2.50+i*.147
 beam('Shelter lower kickboard',(x,1.21,.18),(x,1.21,.83+random.uniform(-.04,.04)),.138,.049,group='Shelter',rough=.005)
for z in [.29,.86,1.72]:beam('Rear wall rough rail',(-2.68,1.17,z),(2.68,1.17,z),.075,.090,group='Shelter')
for x in [-2.58,2.58]:
 for z in [.30,.76,1.14]:beam('Open end sturdy rail',(x,-1.28,z),(x,1.31,z),.10,.105,group='Shelter')
 for j in range(8):
  y=.20+j*.145
  beam('Shelter end windbreak board',(x,y,.25),(x,y,1.73),.056,.14,group='Shelter',rough=.004)
for x in [-2.58,0,2.58]:
 for y in [-1.24,1.24]:
  for z in [1.83,2.10]:tube('Shelter timber joint peg',[(x,y-.105,z),(x,y+.105,z)],.017,'Timber','Shelter',7)
# Lifted feed pallet is visible exterior furniture, not an interior room.
for i in range(10):beam('Feed stack raised slat',(.70+i*.17,.58,.17),(.70+i*.17,1.10,.17),.16,.07,group='Shelter')
finish(before,'Shelter')

# Farm fence rails and lashings are reused, with stronger ground posts and thicker rails.
modules['Fence_Straight']=clone_objects([o for o in kit('Fence_Straight') if 'Light pen picket' not in o.name],'Fence_Straight',(1,1.75,1.13))
before=start()
for x in [0,2]:
 post=beam('Stock fence squared heavy post',(x,.025,.015),(x+.024,.024,1.24),.15,.16,group='Fence',rough=.014)
 for v in post.data.vertices:
  if v.co.z>1.15:v.co.z+=v.co.x*.05+random.uniform(-.018,.018)
 for z in [.328,.746,.983]:lash('Stock fence heavy lashing',(x,-.012,z),'X',.101,3)
 for z in [.34,.73]:
  tube('Fence end flush wooden peg',[(x,-.096,z),(x,-.105,z)],.014,'Timber','Fence',7)
finish(before,'Fence_Straight')
# A short L corner returns one metre in each direction; other runs share end posts.
modules['Fence_Corner']=clone_objects(modules['Fence_Straight'],'Fence_Corner',(.5,1,1))
modules['Fence_Corner']+=clone_objects(modules['Fence_Straight'],'Fence_Corner',(.5,1,1),rotation=90)
modules['PenGate']=clone_objects(kit('Fence_Gate'),'PenGate',(1,1.65,1.24))

# Roofed timber entry matches the primary reference silhouette.
before=start()
for x in [-.87,.87]:
 fieldstone('Gate bedded stone',(x,0,.058),(.18,.20,.09))
 beam('Gate tall rough post',(x,0,.08),(x,0,1.91),.18,.19,group='Gate',rough=.009)
 beam('Gate roof knee',(x,0,1.57),(x*.57,0,1.88),.088,group='Gate')
beam('Gate lintel',(-1.06,0,1.90),(1.06,0,1.90),.15,.15,group='Gate')
plank_roof(0,0,1.13,.55,1.98,2.29,'GateRoof')
for x in [-.69,.68]:beam('Gate leaf stile',(x,-.033,.17),(x,-.033,1.35),.086,.084,group='Gate')
for i in range(8):
 x=-.64+i*.183
 beam('Gate spaced rough upright',(x,-.014,.20),(x,-.014,1.29),.10,.047,group='Gate',rough=.006)
for z in [.28,1.20]:beam('Gate leaf crossrail',(-.75,-.078,z),(.75,-.078,z),.092,.086,group='Gate')
beam('Gate diagonal stay',(-.68,-.131,.34),(.66,-.131,1.16),.078,.065,group='Gate')
for z in [.31,1.21]:lash('Gate hinge rope',(-.82,-.022,z),'X',.116,4)
lash('Gate latch loop',(.76,-.025,1.13),'X',.085,3)
finish(before,'Gate')
# Worn end grain, small face checks and irregular board tips catch the sidelight.
before=start()
for x in [-.87,.87]:
 for k in range(5):
  xx=x+random.uniform(-.06,.06);z=random.uniform(.32,1.72);h=random.uniform(.13,.31)
  mesh('Gate dark timber drying check',[(xx,-.100,z),(xx-.003,-.102,z+h*.42),(xx+.002,-.101,z+h),(xx+.005,-.102,z+h*.52)],[(0,1,2,3)],'Iron',group='GateWear')
finish(before,'Gate')

# The existing lapped wood water trough becomes a larger feed trough with a low bulk fill.
modules['WaterTrough']=clone_objects(kit('WaterTrough'),'WaterTrough',(1.22,1.16,1.12))
feed_parts=[o for o in kit('WaterTrough') if not any(m and m.name.startswith('SM01_Water') for m in o.data.materials)]
modules['FeedingTrough']=clone_objects(feed_parts,'FeedingTrough',(1.72,1.22,1.18))
before=start()
vv=[];ff=[]
for j in range(4):
 for i in range(15):vv.append((-0.93+i*.133,-.20+j*.134,.397+random.uniform(-.008,.015)))
for j in range(3):
 for i in range(14):a=j*15+i;ff.append((a,a+1,a+16,a+15))
mesh('Trough dry feed bulk',vv,ff,'Thatch',group='Feed')
finish(before,'FeedingTrough')

# Open splayed hay rack: three bulk sheaves sit visibly between its timber slats.
before=start()
for x in [-1.03,1.03]:
 for side in [-1,1]:
  beam('Hay rack splayed leg',(x,side*.45,.03),(x,side*.24,1.09),.081,.083,group='HayRack')
  beam('Hay rack end cradle',(x,0,.39),(x,side*.53,1.19),.063,group='HayRack')
 beam('Hay rack end tie',(x,-.52,1.18),(x,.52,1.18),.062,group='HayRack')
for side in [-1,1]:
 beam('Hay rack upper rail',(-1.16,side*.53,1.20),(1.16,side*.53,1.20),.084,.085,group='HayRack')
 beam('Hay rack base rail',(-1.11,side*.12,.47),(1.11,side*.12,.47),.074,group='HayRack')
 for i in range(12):
  x=-1.04+i*.189
  beam('Hay rack open slat',(x,side*.115,.46),(x,side*.52,1.20),.036,.035,group='HayRack',rough=.002)
for x in [-1.03,1.03]:
 for side in [-1,1]:lash('Hay rack corner binding',(x,side*.53,1.20),'X',.071,3)
finish(before,'HayRack')
for x,y,z,sz in [(-.69,0,.49,.93),(0,.018,.49,1.01),(.69,0,.49,.88)]:
 modules['HayRack']+=clone_objects(kit('HayBundles'),'HayRack',(.99,1.02,sz),(x,y,z))
modules['HayBundles']=clone_objects(kit('HayBundles'),'HayBundles')
modules['PropGroup']=clone_objects(kit('Baskets'),'PropGroup',(1.15,1.15,1.15),(-.22,0,0))
modules['PropGroup']+=clone_objects(kit('Baskets'),'PropGroup',(.89,.89,.80),(.26,.12,0),22)

# Sculpted dirt dressing: irregular edge, worn paths, low wet hollows and coarse gravel.
# This is a single static exterior mesh, with vertex-painted dry/wet response.
before=start();NX=132;NY=98;vv=[];ff=[]
wet_centers=[(-.18,-1.8,1.15,.60),(3.60,-1.80,.94,.92),(-3.6,-1.30,.74,.67),(.38,.30,.60,.50)]
def ground_height(x,y):
 edge=max(abs(x)/5.6,abs(y)/4.12)
 return .047+.014*math.sin(x*3.7+y*3.2)+.009*math.cos(x*12.6-y*13.1)-.066*max(0,(edge-.90)/.1)
def wetness(x,y):
 w=sum(math.exp(-((x-cx)/sx)**2-((y-cy)/sy)**2) for cx,cy,sx,sy in wet_centers)
 return min(.95,w*(.70+.22*math.sin(x*8.1+y*5.4)))
for j in range(NY+1):
 for i in range(NX+1):
  x=-5.55+11.1*i/NX;y=-4.08+8.16*j/NY
  x+=.070*math.sin(y*4.1)+.038*math.sin(y*9.7)
  y+=.050*math.sin(x*3.7)+.047*math.sin(x*7.1)
  vv.append((x,y,ground_height(x,y)-wetness(x,y)*.021))
for j in range(NY):
 for i in range(NX):
  a=j*(NX+1)+i;ff.append((a,a+1,a+NX+2,a+NX+1))
ground=mesh('Sculpted damp livestock earth',vv,ff,'Mud',group='Ground')
colors=ground.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
for face in ground.data.polygons:
 face.use_smooth=True
 for li in face.loop_indices:
  p=ground.data.vertices[ground.data.loops[li].vertex_index].co;w=wetness(p.x,p.y)
  k=.90-w*.43+.06*math.sin(p.x*16+p.y*11)
  colors.data[li].color=(k,k*(1-.10*w),k*(1-.17*w),1-w)
ground.data.color_attributes.active_color=colors
for i in range(230):
 x=random.uniform(-5.42,5.42);y=random.uniform(-3.99,3.99)
 if abs(x)<1 and y<-.5 and i%3:continue
 size=random.uniform(.025,.083) if i%7 else random.uniform(.09,.15)
 ob=fieldstone('Bedded worn yard gravel',(x,y,ground_height(x,y)-.004),(size,size*random.uniform(.68,1.2),size*.52))
# Dark marks are shallow concave worn impressions, not raised spot decals.
for i in range(130):
 x=random.uniform(-4.70,4.70);y=random.uniform(-3.45,.85);a=random.uniform(0,math.tau)
 r=random.uniform(.025,.042);z=ground_height(x,y)-wetness(x,y)*.021+.003
 vv=[(x,y,z-.007)]
 for j in range(9):
  t=j*math.tau/9;vv.append((x+math.cos(t+a)*r,y+math.sin(t+a)*r*.76,z))
 ob=mesh('Worn shallow hoof impression',vv,[(0,j+1,(j+1)%9+1) for j in range(9)],'Mud',group='Ground')
 c=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for v in c.data:v.color=(.45,.41,.35,.32)
 ob.data.color_attributes.active_color=c
for i in range(220):
 x=random.uniform(-3.9,1.4);y=random.uniform(-.15,2.5);z=ground_height(x,y)+.010
 tube('Scattered pale feed straw',[(x,y,z),(x+.075,y+.033,z+.003),(x+.14,y+.05,z)],.0032,'Thatch','Ground',4)
# Fuller bent grass grows beside rails and stones; the center remains trampled.
for clump in range(590):
 a=random.uniform(0,math.tau);r=random.uniform(.905,1.015)
 x=5.5*math.copysign(abs(math.cos(a))**.30,math.cos(a))*r
 y=4.07*math.copysign(abs(math.sin(a))**.33,math.sin(a))*r
 if clump>490:
  x=random.choice([-4.9,4.9,2.23])+random.uniform(-.10,.10);y=random.uniform(-3.4,3.45)
 if abs(x)<1.15 and y<-3.25:continue
 vv=[];ff=[]
 for j in range(random.randint(5,9)):
  t=random.uniform(0,math.tau);h=random.uniform(.13,.39);w=random.uniform(.012,.033)
  p=Vector((x+random.uniform(-.13,.13),y+random.uniform(-.13,.13),ground_height(x,y)-.008))
  side=Vector((math.cos(t)*w,math.sin(t)*w,0));bend=Vector((math.sin(t)*random.uniform(.12,.25),math.cos(t)*.16,h))
  n=len(vv);vv.extend([p-side,p+side,p+bend*.40+side*.8,p+bend*.40-side*.8,p+bend*.75+side*.4,p+bend*.75-side*.4,p+bend]);ff.extend([(n,n+1,n+2,n+3),(n+3,n+2,n+4,n+5),(n+5,n+4,n+6)])
 ob=mesh('Bent verge grass and weeds',vv,ff,'Thatch',group='Ground')
 ob['grass_tone']=random.choice([(.27,.88,.075),(.48,.93,.12),(.43,.67,.13),(.68,.55,.25)])
finish(before,'GroundApron')

# Restrained, varied dark weathering keeps the shared kit textures while avoiding
# identical clean pieces. Wet feet, worn upper faces and finer roof texture read in sunlight.
for key,obs in modules.items():
 for ob in obs:
  if not ob.data.color_attributes.get('Color'):tint(ob)
  if key=='GroundApron':continue
  colors=ob.data.color_attributes['Color'];variation=random.uniform(.83,1.12)
  for face in ob.data.polygons:
   family=ob.data.materials[face.material_index].name.split('_',1)[1]
   for li in face.loop_indices:
    p=ob.data.vertices[ob.data.loops[li].vertex_index].co
    old=colors.data[li].color
    if family=='Timber':
     damp=.64+.36*min(1,max(0,p.z)/.42)
     colors.data[li].color=(old[0]*.81*variation*damp,old[1]*.72*variation*damp,old[2]*.63*variation*damp,1)
    elif family=='Thatch' and key=='Roof':
     k=.87+.10*math.sin(p.x*1.21+p.y*1.6)+.05*math.sin(p.x*3.8-p.y*2.2)
     colors.data[li].color=(old[0]*k,old[1]*k*.94,old[2]*k*.84,1)
    elif family=='Rope':
     colors.data[li].color=(old[0]*.78,old[1]*.71,old[2]*.61,1)

# Export the modular, local-pivot parts using the established SHŌEN FBX exporter.
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for key,obs in modules.items():
 for ob in obs:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  if not ob.data.color_attributes.get('Color'):tint(ob)
  ob.modifiers.new('Export triangulation','TRIANGULATE')
 fbx(ART/'Exports'/('LY01_'+key+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangulation'])

def place(key,loc,angle=0,scale=(1,1,1)):
 index=sum(1 for x in instances if x['mesh']=='LY01_'+key)
 label='LY01_'+key+('_%02d'%index if index else '')
 col=bpy.data.collections.new(label);src.children.link(col)
 matrix=Matrix.Translation(Vector(loc))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in modules[key]:
  ob=original if index==0 else original.copy()
  if index==0:
   for c in list(ob.users_collection):c.objects.unlink(ob)
  col.objects.link(ob);ob.matrix_world=matrix
 instances.append({'mesh':'LY01_'+key,'name':label,'location':list(loc),'rotation_degrees':angle,'scale':list(scale)})

place('Shelter',(-1.05,1.67,0));place('Roof',(-1.05,1.67,0))
# Closed perimeter, with the short reusable L corner used at the front left.
place('Fence_Corner',(-5,-3.6,0))
for x,y,angle,sx in [(-4,-3.6,0,1),(-2,-3.6,0,.565),(.87,-3.6,0,1.0325),(2.935,-3.6,0,1.0325),
 (-5,-2.6,90,1),(-5,-.6,90,1),(-5,1.4,90,1.1),
 (5,-3.6,90,1.2),(5,-1.2,90,1.2),(5,1.2,90,1.2),
 (-5,3.6,0,1.25),(-2.5,3.6,0,1.25),(0,3.6,0,1.25),(2.5,3.6,0,1.25),
 (2.25,-3.6,90,1),(2.25,-.40,90,.325),(2.25,.25,0,1.375)]:
 place('Fence_Straight',(x,y,0),angle,(sx,1,1))
place('Gate',(0,-3.6,0))
place('PenGate',(2.25,-1.60,0),90)
place('FeedingTrough',(-3.45,-1.50,0),90)
place('WaterTrough',(4.35,-1.88,0),90)
place('HayRack',(.45,.59,0),0)
place('HayBundles',(-3.12,2.25,.13),-14,(1.08,1.08,1.03))
place('HayBundles',(-2.48,2.33,.13),18,(1.02,1.02,.87))
place('HayBundles',(.20,2.50,.22),-18,(1.02,1.02,.95))
place('HayBundles',(.85,2.48,.22),15,(.95,.95,.89))
place('PropGroup',(1.10,1.45,0),-15)
place('GroundApron',(0,0,-.008))
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'LivestockYard_01','units':'metres','instances':instances},indent=2)+'\n')

# Remove unused appended library objects from the source scene data, preserving originals on disk.
for col in kit_collections.values():bpy.data.collections.remove(col)
for ob in roof_objects:
 if not ob.users_collection:bpy.data.objects.remove(ob)
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review ground';ground.location.z=-.075
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.048,.057,.022,1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.48,.56,1);world.node_tree.nodes['Background'].inputs[1].default_value=.26
def area(name,loc,energy,size,color,target=(0,0,1)):
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=energy;d.color=color;d.shape='DISK';d.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Warm afternoon',(-5,-7,11),1250,6,(1,.86,.67))
area('Sky fill',(4,4,8),600,8,(.79,.86,1))
area('Open shelter daylight',(-1,-5,3.5),290,5,(.90,.92,1))
d=bpy.data.lights.new('Afternoon sun','SUN');ob=bpy.data.objects.new(d.name,d);studio.objects.link(ob)
ob.rotation_euler=(.60,-.62,-.65);d.energy=3.1;d.color=(1,.88,.68);d.angle=.055
cd=bpy.data.cameras.new('LivestockYard three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam)
cam.location=(10.8,-19.0,8.6);cam.rotation_euler=(Vector((0,.05,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=51;scene.camera=cam
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='LivestockYard_01 • exterior only • reused SHŌEN farm kit • empty pens awaiting separate animal assets'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'LivestockYard01.blend'))
print('YARD_SAVED',len(instances),'module instances',flush=True)
scene.render.filepath=str(OUT/'livestockyard-three-quarter.png');bpy.ops.render.render(write_still=True)
print('YARD_COMPLETE',flush=True)
