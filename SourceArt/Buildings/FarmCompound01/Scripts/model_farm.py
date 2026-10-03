"""One FarmCompound01 modeling pass, reusing the SHŌEN rural kit."""
from pathlib import Path
import ast, json, math, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'; SMITHY=ART.parent/'Smithy01'; STORE=ART.parent/'Storehouse01'
OUT=ROOT/'artifacts/farmcompound01'; OUT.mkdir(parents=True,exist_ok=True)
random.seed(1188)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.02
src=bpy.data.collections.new('FarmCompound_01 • modular exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • ground and lighting');scene.collection.children.link(studio)
groups={};modules={};instances=[]
with bpy.data.libraries.load(str(SMITHY/'Smithy01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope','SM01_Water']]
 b.objects=[n for n in a.objects if n in ['SM01_Frame','SM01_Walls','SM01_Foundations','SM01_Roof','SM01_RoofBundles','SM01_RoofEaves','SM01_RoofGableThatch','SM01_Ridge','SM01_RidgeLashings','SM01_Workbench']]
mats={m.name.split('_',1)[1]:m for m in b.materials};kit_objects={o.name:o for o in b.objects}
# Reuse plain earth already in the authored rural review scene, with a dedicated runtime name.
with bpy.data.libraries.load(str(SMITHY/'Smithy01.blend'),link=False) as (a,b):b.materials=['Review earth']
earth=b.materials[0];earth.name='FC01_Dirt';earth.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.16,.115,.067,1);mats['Dirt']=earth
n=earth.node_tree.nodes;l=earth.node_tree.links;bs=n['Principled BSDF'];bs.inputs['Roughness'].default_value=.98
coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.8;noise.inputs['Detail'].default_value=3.0;l.new(coord.outputs['Geometry'] if 'Geometry' in coord.outputs else coord.outputs['Object'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.16;ramp.color_ramp.elements[0].color=(.075,.052,.032,1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(.22,.17,.10,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=85;fine.inputs['Detail'].default_value=2.5;l.new(coord.outputs['Object'],fine.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.022;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
for path,names in [(KIT/'Scripts/model_house.py',{'mesh','beam','tube','lash','panel'}),(STORE/'Scripts/refine_reference_match.py',{'fieldstone'})]:
 for node in ast.parse(path.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
def reuse(name,target,scale=(1,1,1),shift=(0,0,0)):
 ob=kit_objects[name].copy();ob.data=kit_objects[name].data.copy();src.objects.link(ob)
 ob.name=target+'_'+name.removeprefix('SM01_');ob['reused_from']='Smithy01 / rural building kit'
 for v in ob.data.vertices:v.co=Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))+Vector(shift)
 return ob
def collect_since(before,key):
 obs=[o for o in src.objects if o.name not in before];modules.setdefault(key,[]).extend(obs);return obs
def start():return set(o.name for o in src.objects)
def infill(name,a,b,z0,z1):
 ob=panel(name,a,b,z0,z1);mod=ob.modifiers.new('Thin exterior wattle','SOLIDIFY');mod.thickness=.05;return ob
def plank_roof(cx,cy,halfx,halfy,eave,ridge,group):
 for x in [cx-halfx+.13,cx+halfx-.13]:
  for s in [-1,1]:beam('Shed gable bearer',(x,cy+s*halfy,eave-.06),(x,cy,ridge-.04),.10,.12,group=group)
 for s in [-1,1]:
  for i in range(int(halfx*2/.16)+1):
   x=cx-halfx+i*(halfx*2/int(halfx*2/.16))
   beam('Split timber roof board',(x,cy+s*halfy,eave+random.uniform(-.015,.015)),(x,cy,ridge),.165,.045,group=group,rough=.003)
  for t in [.17,.70]:
   y=cy+s*halfy*t;z=ridge+(eave-ridge)*t+.048
   tube('Rough roof retaining batten',[(cx-halfx-.02,y,z),(cx+halfx+.02,y,z)],.035,'Timber',group)
 tube('Wood roof ridge cap',[(cx-halfx-.1,cy,ridge+.05),(cx+halfx+.1,cy,ridge+.05)],.065,'Timber',group)
def tint(ob):
 colors=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for face in ob.data.polygons:
  family=ob.data.materials[face.material_index].name.split('_',1)[1]
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.86+.10*math.sin(p.x*1.43+p.y*2.7+p.z*.8)+.04*math.sin(p.x*8.3+p.y*4.7+p.z*5.8)
   # Keep shared rural texture coloration; a little earth staining at ground level.
   k*=.88+.12*min(1,max(0,p.z)/.4)
   rgb={'Timber':(.48,.40,.295),'Thatch':(.66,.51,.315),'Stone':(.76,.74,.68),'Plaster':(.9,.85,.73)}.get(family,(1,1,1))
   if 'Straw sheaf' in ob.name and family=='Thatch':rgb=(.96,.77,.39)
   if ob.get('grass_tone'):rgb=ob['grass_tone']
   colors.data[li].color=(*(v*k for v in rgb),1)
 ob.data.color_attributes.active_color=colors
# Main farm shelter: authentic reused roof/frame, closed household bay plus an open working bay.
before=start()
for name in ['Frame','Walls','Foundations','Roof','RoofBundles','RoofEaves','RoofGableThatch','Ridge','RidgeLashings']:
 reuse('SM01_'+name,'FC01_MainHouse',(.9,.9,1))
infill('Farm front plaster',(-2.11,-1.358),(-.70,-1.358),.27,2.3)
# A broad open agricultural bay replaces the residential door frontage.
for x in [-.70,2.07]:beam('Open farm bay jamb',(x,-1.40,.18),(x,-1.40,2.36),.14,group='FarmFront')
beam('Open farm bay lintel',(-.83,-1.40,2.31),(2.20,-1.40,2.31),.16,.18,group='FarmFront')
# A few stacked shutters at the bay edge imply practical enclosure without a room.
for i in range(4):
 x=-.91+i*.080
 beam('Stacked rough farm shutter',(x,-1.43,.30),(x+.015,-1.43,2.05),.076,.045,group='FarmDoor',rough=.005)
for z in [.51,1.59]:beam('Stacked shutter crossrail',(-.95,-1.47,z),(-.61,-1.47,z),.065,.038,group='FarmDoor')
# Small dark shutter with timber grille, a readable feature on the plaster front.
for i in range(6):beam('Shut window board',(-1.84+i*.136,-1.397,1.09),(-1.84+i*.136,-1.397,1.78),.132,.026,group='FarmWindow')
for z in [1.07,1.79]:beam('Window sill',(-1.94,-1.44,z),(-1.06,-1.44,z),.067,group='FarmWindow')
for i in range(6):beam('Window grille',(-1.89+i*.156,-1.46,1.11),(-1.89+i*.156,-1.46,1.76),.025,group='FarmWindow',rough=.001)
# Low board awning across the working front, far thinner than the main roof.
for x in [-2.05,.62,2.08]:
 fieldstone('Awning footing',(x,-1.98,.08),(.17,.18,.12))
 beam('Awning post',(x,-1.98,.13),(x,-1.98,2.0),.105,group='FarmAwning')
 beam('Awning knee',(x,-1.98,1.67),(x+.25,-1.98,1.98),.066,group='FarmAwning')
beam('Awning eave',(-2.26,-2.02,2.01),(2.29,-2.02,2.01),.12,group='FarmAwning')
for i in range(27):
 x=-2.27+i*.177
 beam('Front split roof board',(x,-1.28,2.40),(x,-2.20,2.04+random.uniform(-.01,.01)),.175,.046,group='FarmAwning',rough=.002)
# A reused workbench in the exterior-visible open bay.
for x in [-.34,1.26]:
 for y in [-1.16,-.64]:beam('Farm workbench hewn leg',(x,y,.08),(x,y,.86),.095,group='FarmWorkbench')
for j in range(4):beam('Farm workbench worn plank',(-.48,-1.18+j*.185,.90),(1.41,-1.18+j*.185,.90),.18,.065,group='FarmWorkbench',rough=.007)
beam('Farm bench lower stretcher',(-.36,-.85,.25),(1.30,-.85,.25),.079,group='FarmWorkbench')
# A rough shelf on the exposed back wall catches baskets and tool silhouettes.
for z in [.73,1.38]:
 for j in range(3):beam('Open bay shallow wall shelf',(-.30,.98+j*.12,z),(1.78,.98+j*.12,z),.116,.055,group='FarmShelf',rough=.004)
for x in [-.22,1.65]:beam('Open bay shelf upright',(x,1.33,.19),(x,1.33,1.59),.08,group='FarmShelf')
# A low lean-to store and external toolwork give the left gable an agricultural silhouette.
for y in [-.97,1.09]:
 fieldstone('Lean to bedded stone',(-2.94,y,.07),(.18,.2,.105))
 beam('Crooked lean to post',(-2.94,y,.11),(-2.98,y+.02,1.80),.13,group='FarmLeanTo')
 beam('Lean to roof bearer',(-3.19,y,1.80),(-2.05,y,2.31),.09,.11,group='FarmLeanTo')
beam('Lean to low eave',(-3.05,-1.25,1.82),(-3.05,1.45,1.82),.12,group='FarmLeanTo')
for i in range(17):
 y=-1.20+i*.164
 beam('Lean to rough split roof',(-3.22,y,1.83+random.uniform(-.024,.01)),(-2.01,y,2.35),.160,.045,group='FarmLeanTo',rough=.005)
for x in [-3.11,-2.24]:
 z=1.84+(x+3.22)*.43+.05
 beam('Lean to roof holding lath',(x,-1.28,z),(x,1.5,z),.048,.036,group='FarmLeanTo')
for i in range(5):
 x=-2.90+i*.161
 beam('Farm lean to front board',(x,-1.02,.18),(x,-1.02,1.80+(x+2.94)*.40),.155,.045,group='FarmLeanTo',rough=.007)
for z in [.43,1.39]:beam('Lean to cross rail',(-3.01,-1.08,z),(-2.15,-1.08,z),.078,.04,group='FarmLeanTo')
# Exposed pegs, worn notches and irregular upright grain catch the daylight.
for x in [-2.1,-.67,.33,1.91]:
 for j in range(7):
  xx=x+random.uniform(-.032,.032);z=random.uniform(.43,1.95);h=random.uniform(.09,.29)
  mesh('Fine dark drying split',[(xx,-1.445,z),(xx-.0025,-1.446,z+h*.3),(xx+.002,-1.445,z+h),(xx+.003,-1.446,z+h*.55)],[(0,1,2,3)],'Iron',group='FarmWear')
collect_since(before,'MainHouse')
# Freestanding modest tool shed, with two open sides and rear board wall.
before=start()
for x in [-1.03,1.03]:
 for y in [-.78,.78]:
  fieldstone('Tool shed foot',(x,y,.075),(.18,.17,.10))
  beam('Tool shed upright',(x,y,.11),(x,y,1.95),.12,group='ShedFrame')
for y in [-.78,.78]:beam('Tool shed wall plate',(-1.17,y,1.94),(1.17,y,1.94),.14,group='ShedFrame')
for i in range(13):
 x=-1.0+i*.166
 beam('Tool shed rear board',(x,.81,.20),(x,.81,2.02),.158,.043,group='ShedWalls',rough=.003)
for z in [.35,1.55]:beam('Tool shed rear rail',(-1.1,.77,z),(1.1,.77,z),.080,group='ShedFrame')
for x in [-1.03,1.03]:
 beam('Tool shed knee',(x,-.78,1.55),(x*.64,-.78,1.93),.07,group='ShedFrame')
for j in range(4):beam('Partial side boards',(-1.04,.20+j*.165,.22),(-1.04,.20+j*.165,1.94),.07,.16,group='ShedWalls',rough=.003)
plank_roof(0,0,1.30,1.09,2.04,2.74,'ShedRoof')
collect_since(before,'ToolShed')
# Open hay shelter: smaller copy of the farm's roof, with separate light framing.
before=start()
for name in ['Roof','RoofBundles','RoofEaves','RoofGableThatch','Ridge','RidgeLashings']:
 reuse('SM01_'+name,'FC01_HayShelter',(.55,.62,.78))
for x in [-1.19,1.19]:
 for y in [-.9,.9]:
  fieldstone('Hay shelter footing',(x,y,.075),(.18,.2,.11))
  beam('Hay shelter upright',(x,y,.13),(x,y,1.96),.13,group='HayFrame')
for y in [-.9,.9]:beam('Hay shelter eave tie',(-1.35,y,1.91),(1.35,y,1.91),.15,group='HayFrame')
for x in [-1.19,1.19]:
 beam('Hay shelter cross tie',(x,-1.05,1.94),(x,1.05,1.94),.12,group='HayFrame')
 for s in [-1,1]:
  beam('Hay shelter knee',(x,s*.9,1.57),(x,s*.56,1.92),.07,group='HayFrame')
  beam('Hay gable rafter',(x,s*1.11,1.98),(x,0,2.90),.095,group='HayFrame')
 beam('Hay gable king post',(x,0,1.94),(x,0,2.9),.095,group='HayFrame')
# Rear half wall and slatted pallet keep straw lifted and readable through the open front.
for i in range(12):beam('Rear shelter wattle slat',(-1.1+i*.20,.94,.23),(-1.1+i*.20,.94,1.54),.10,.04,group='HayWall')
for z in [.30,1.44]:beam('Hay rear rail',(-1.27,.90,z),(1.27,.90,z),.09,group='HayWall')
for i in range(12):beam('Straw drying pallet',(-1.16+i*.211,-.70,.19),(-1.16+i*.211,.78,.19),.2,.055,group='HayPallet',rough=.003)
collect_since(before,'HayShelter')
# Separate open work canopy; lighter plank roof and a sparse exterior table.
before=start()
for x in [-.93,.93]:
 for y in [-.70,.70]:
  fieldstone('Work shelter footing',(x,y,.07),(.16,.17,.10))
  beam('Work shelter post',(x,y,.11),(x,y,1.94),.105,group='WorkFrame')
for y in [-.70,.70]:beam('Work shelter eave rail',(-1.05,y,1.96),(1.05,y,1.96),.13,group='WorkFrame')
plank_roof(0,0,1.18,1.03,2.01,2.56,'WorkRoof')
for x in [-.55,.55]:
 for y in [-.26,.26]:beam('Work table foot',(x,y,.07),(x,y,.78),.075,group='WorkTable')
for j in range(5):beam('Work table board',(-.67,-.33+j*.166,.82),(.67,-.33+j*.166,.82),.16,.05,group='WorkTable',rough=.003)
collect_since(before,'WorkShelter')
# One reusable two metre fence segment; origin at its first post.
before=start()
for x in [0,1.0,2.0]:tube('Rustic fence main stake',[(x,0,.02),(x+.014,-.005,.62),(x+random.uniform(-.03,.03),.008,1.02+random.uniform(-.04,.04))],.047,'Timber','Fence',7)
for z in [.29,.66,.87]:
 tube('Uneven horizontal fence rail',[(-.06,-.045,z),(1,-.047,z-.018),(2.10,-.038,z+.016)],.033,'Timber','Fence',7)
 for x in [0,1,2]:lash('Fence hemp binding',(x,-.02,z),'X',.060,2)
for x in [.38,.71,1.34,1.69]:tube('Light pen picket',[(x,-.032,.12),(x+.025,-.045,.91)],.021,'Timber','Fence',6)
collect_since(before,'Fence_Straight')
before=start()
for x in [0,1.2]:tube('Gate side stake',[(x,0,.04),(x,0,.91)],.035,'Timber','Gate')
for z in [.22,.58,.82]:tube('Gate rail',[(0,-.04,z),(1.22,-.04,z+.015)],.028,'Timber','Gate')
tube('Gate diagonal',[(.04,-.02,.2),(1.18,-.02,.8)],.024,'Timber','Gate')
for x in [0,1.2]:
 for z in [.22,.82]:lash('Gate binding',(x,-.02,z),'X',.051,2)
collect_since(before,'Fence_Gate')
# Loose bundled reeds interrupt the kit's orderly thatch courses and eave silhouettes.
for key,sx,sy,sz in [('MainHouse',.9,.9,1),('HayShelter',.55,.62,.78)]:
 before=start()
 for side in [-1,1]:
  for i in range(185 if key=='MainHouse' else 95):
   u=random.uniform(.012,.988);v=random.uniform(.01,.89);xx=(-2.83+5.66*u)*sx
   for strand in range(random.randint(2,4)):
    vv=v+random.uniform(-.015,.015);x=xx+random.uniform(-.022,.022);y=side*2.06*(1-vv)*sy
    z=(2.51+1.26*vv+.115*math.sin(vv*math.pi)*math.sin(u*math.pi))*sz
    normal=Vector((0,side*1.26/sy,2.06/sz)).normalized();p=Vector((x,y,z))+normal*.026
    tangent=Vector((0,-side*2.06*sy,1.26*sz)).normalized();length=random.uniform(.13,.29)
    q=p+tangent*length
    reed_start=p-tangent*random.uniform(.02,.05)
    if vv<.08:reed_start.z-=random.uniform(.055,.15)
    tube('Weathered loose roof reed',[reed_start,p+normal*.012,q],random.uniform(.002,.0045),'Thatch','LooseRoofReeds',5)
 collect_since(before,key)
# Make roof edges lightly uneven without shifting their framing connections.
for key in ['MainHouse','HayShelter','ToolShed','WorkShelter']:
 for ob in modules[key]:
  if 'roof board' in ob.name.lower() or 'split roof' in ob.name.lower():
   for v in ob.data.vertices:
    p=v.co;p.z+=.014*math.sin(p.x*14.3+p.y*5.7)+.009*math.sin(p.x*5.1-p.y*8.7)
# Props are separately authored local meshes in the exact same kit materials.
sys.path.insert(0,str(ART/'Scripts'))
from farm_props import build_props
before=start();build_props(globals())
for key in ['Cart','WaterTrough','ToolRack','Baskets','HayBundles']:
 modules[key]=list(groups[key])
# The irregular packed earth is a thin site dressing surface, not new landscape infrastructure.
before=start();verts=[(0,.3,.017)];N=96;rings=7;faces=[]
for ring in range(1,rings+1):
 for i in range(N):
  a=i/N*math.tau;c=math.cos(a);si=math.sin(a);r=ring/rings
  edge=.965+.018*math.sin(a*17)+.015*math.sin(a*29)
  verts.append((6.22*math.copysign(abs(c)**.37,c)*r*edge,3.83*math.copysign(abs(si)**.4,si)*r*edge+.4,.017+random.uniform(0,.012)*(1-r)))
for i in range(N):faces.append((0,i+1,(i+1)%N+1))
for ring in range(rings-1):
 for i in range(N):
  a=1+ring*N+i;b=1+ring*N+(i+1)%N;faces.append((a,b,b+N,a+N))
mesh('Packed earth compound apron',verts,faces,'Dirt',group='GroundApron')
for i in range(105):
 x=random.uniform(-5.85,5.5);y=random.uniform(-3.15,3.8)
 # Small, partly buried gravel; concentration close to building foundations.
 fieldstone('Small bedded yard gravel',(x,y,.021),(random.uniform(.018,.046),random.uniform(.018,.050),random.uniform(.012,.028)))
for i in range(95):
 x=random.uniform(2.25,5.25);y=random.uniform(-1.2,1.8)
 tube('Spilled straw on yard',[(x,y,.03),(x+.13,y+.05,.035),(x+.22,y+.08,.026)],.0035,'Thatch','GroundApron',4)
# Sparse short grass and dry stalks feather the site into the existing green terrain.
for clump in range(440):
 a=random.uniform(0,math.tau);c=math.cos(a);si=math.sin(a);r=random.uniform(.92,1.025)
 x=6.22*math.copysign(abs(c)**.37,c)*r;y=3.83*math.copysign(abs(si)**.4,si)*r+.4
 if -2.4<x<1.7 and y<-2.7:continue
 vv=[];ff=[]
 for blade in range(random.randint(4,7)):
  theta=random.uniform(0,math.tau);h=random.uniform(.11,.34);w=random.uniform(.009,.021);lean=random.uniform(.04,.15)
  base=Vector((x+random.uniform(-.09,.09),y+random.uniform(-.08,.08),.017));side=Vector((math.cos(theta)*w,math.sin(theta)*w,0));bend=Vector((math.sin(theta)*lean,math.cos(theta)*lean,0));j=len(vv)
  vv += [base-side,base+side,base+Vector((0,0,h*.6))+bend*.4+side*.45,base+Vector((0,0,h*.6))+bend*.4-side*.45,base+Vector((0,0,h))+bend]
  ff += [(j,j+1,j+2,j+3),(j+3,j+2,j+4)]
 ob=mesh('Grass verge tuft',vv,ff,'Thatch',group='GroundApron');ob['grass_tone']=(.24,.80,.10) if clump%4 else (.68,.55,.25)
collect_since(before,'GroundApron')
# Keep architecture parts editable; export modules together at sensible ground pivots.
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for key,obs in modules.items():
 for ob in obs:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  tint(ob)
  ob.modifiers.new('Export triangulation','TRIANGULATE')
 fbx(ART/'Exports'/('FC01_'+key+'.fbx'),obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangulation'])
# Place the local modules as one intentionally composed farm, preserving reusable source pieces.
def place(key,loc,angle=0,scale=(1,1,1),name=None):
 index=sum(1 for x in instances if x['mesh']=='FC01_'+key)
 label=name or ('FC01_'+key+('_%02d'%index if index else ''))
 col=bpy.data.collections.new(label);src.children.link(col)
 matrix=Matrix.Translation(Vector(loc))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Diagonal((*scale,1))
 for original in modules[key]:
  if index==0:ob=original
  else:ob=original.copy();ob.data=original.data
  for c in list(ob.users_collection):
   if index==0:c.objects.unlink(ob)
  col.objects.link(ob)
  # Geometry is at module local origin; instances share editable mesh data.
  ob.matrix_world=matrix
 instances.append({'mesh':'FC01_'+key,'name':label,'location':list(loc),'rotation_degrees':angle,'scale':list(scale)})
place('MainHouse',(-2.62,.70,0))
place('ToolShed',(1.0,2.87,0))
place('HayShelter',(4.16,.90,0))
place('WorkShelter',(.85,.52,0))
place('Cart',(-1.0,-2.23,0),-18, (.86,.86,.86))
place('WaterTrough',(-4.16,-2.25,0),0)
place('ToolRack',(1.02,3.18,0),0)
place('ToolRack',(-5.80,.78,0),90,(.83,.83,.85))
place('ToolRack',(-1.15,1.4,0),0,(.8,.8,.88))
place('Baskets',(.36,.27,.86),0,(.62,.62,.62))
place('Baskets',(-2.27,-.27,.94),-12,(.75,.75,.85))
place('Baskets',(-1.01,1.77,1.42),28,(.72,.72,.65))
place('Baskets',(-.30,-.65,0),24,(.73,.73,.85))
for x,y,sc in [(3.3,.92,1.15),(4.06,1.15,1.23),(4.87,1.09,1.11),(3.36,.28,1.0),(4.12,.39,1.15),(4.91,.35,1.04),(3.2,1.57,.9),(4.72,1.57,.93)]:
 place('HayBundles',(x,y,.22),random.uniform(-20,20),(sc,sc,sc))
place('HayBundles',(3.72,.96,.73),72,(1.22,1.10,.90))
place('HayBundles',(4.51,.86,.72),-43,(1.10,1.07,.84))
place('HayBundles',(-1.42,-2.06,.56),12,(.51,.51,.48))
place('Baskets',(-1.72,-2.27,.56),-16,(.78,.78,.84))
# Low boundary fronts, open household gateway and a separate empty livestock pen.
for x,y,angle,s in [(-5.95,-3.18,0,1.12),(-5.95,-3.18,90,1.13),(-5.95,-.92,90,1.12),(-5.95,1.32,90,1.0),(3.55,-3.18,0,1.1),(5.75,-3.18,90,1.0),(5.75,-1.18,90,1.0),(5.75,.82,90,.87),(2.31,-3.18,90,.90),(2.31,-1.38,90,.60)]:
 place('Fence_Straight',(x,y,0),angle,(s,1,.84))
place('Fence_Gate',(2.31,-3.18,0),63,(1,1,.84))
place('GroundApron',(0,0,-.008))
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'FarmCompound_01','units':'metres','instances':instances},indent=2)+'\n')
# Studio only: restrained daylight, all excluded from runtime meshes.
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review ground'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Farm review ground');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.055,.068,.037,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.48,.56,1);world.node_tree.nodes['Background'].inputs[1].default_value=.30
def area(name,loc,energy,size,color,target=(0,0,1)):
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=energy;d.color=color;d.shape='DISK';d.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Warm afternoon',(-5,-7,11),1100,7,(1,.88,.71))
area('Sky fill',(4,4,8),700,8,(.79,.86,1))
area('Open shed reflected daylight',(1,-6,4),240,5,(.90,.92,1))
sun=bpy.data.lights.new('Afternoon sun','SUN');so=bpy.data.objects.new('Afternoon sun',sun);studio.objects.link(so);so.rotation_euler=(.40,-.50,-.55);sun.energy=2.4;sun.color=(1,.91,.79);sun.angle=.10
cd=bpy.data.cameras.new('FarmCompound three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(-12.0,-20.5,6.85);cam.rotation_euler=(Vector((-.2,.25,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='PERSP';cd.lens=55;scene.camera=cam
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT');scene['asset_note']='FarmCompound_01 • exterior only • separate editable modules • metre scale • reused SHŌEN rural kit'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'FarmCompound01.blend'))
print('FARM_SAVED',len(instances),'instances',flush=True)
scene.render.filepath=str(OUT/'farmcompound-three-quarter.png');bpy.ops.render.render(write_still=True)
print('FARM_COMPLETE',flush=True)
