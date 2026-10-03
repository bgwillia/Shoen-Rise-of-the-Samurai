"""One authored Storehouse01 exterior, using the existing RuralHouse01 kit."""
from pathlib import Path
import ast, math, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]
ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'
OUT=ROOT/'artifacts/storehouse01'
random.seed(1181)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.25
src=bpy.data.collections.new('Storehouse_01 • modular exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • not exported');scene.collection.children.link(studio)
groups={}
# Append actual kit datablocks; the textures stay packed in the editable source.
with bpy.data.libraries.load(str(KIT/'RuralHouse01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n.startswith('RH01_')]
 b.objects=['RH01_Roof_Ridge','RH01_ExteriorTub']
mats={m.name.removeprefix('RH01_'):m for m in b.materials}
kit_objects={o.name:o for o in b.objects}
# Reuse the house's hewn-beam, panel, stone, tube and lashing construction.
kit_code=(KIT/'Scripts/model_house.py').read_text()
names={'mesh','beam','tube','lash','stone','panel'}
for node in ast.parse(kit_code).body:
 if isinstance(node,ast.FunctionDef) and node.name in names:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(KIT/'Scripts/model_house.py'),'exec'))
iron=bpy.data.materials.new('SH01_Iron');iron.use_nodes=True
p=iron.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.028,.026,.023,1);p.inputs['Metallic'].default_value=.65;p.inputs['Roughness'].default_value=.7
iron.diffuse_color=(.028,.026,.023,1);mats['Iron']=iron

# Low dry-stone pads, heavy short posts and an open undercroft.
for x in [-1.43,0,1.43]:
 for y in [-1.55,1.55]:
  stone('Bedded lower footing',(x,y,.13),(.23,.24,.13))
  stone('Bedded upper footing',(x+random.uniform(-.02,.02),y,.31),(.18,.19,.075))
  beam('Raised support post',(x,y,.35),(x,y,.89),.20,group='Foundation')
for x in [-1.43,1.43]:
 stone('Middle stone footing',(x,0,.15),(.23,.24,.15))
 beam('Middle support post',(x,0,.27),(x,0,.85),.19,group='Foundation')
for y in [-1.60,1.60]:beam('Platform rim beam',(-1.62,y,.76),(1.62,y,.76),.21,.21,group='Platform')
for x in [-1.44,0,1.44]:beam('Underfloor joist',(x,-1.70,.72),(x,1.71,.72),.16,.18,group='Platform')
# Only the narrow exposed platform perimeter; no furnished floor/interior.
for y in [-1.62,1.62]:
 for j in range(2):beam('Exposed edge plank',(-1.64,y+(j-.5)*.12,.883),(1.64,y+(j-.5)*.12,.883),.117,.055,group='Platform',rough=.004)
for x in [-1.57,1.57]:beam('Exposed side plank',(x,-1.52,.883),(x,1.52,.883),.17,.055,group='Platform',rough=.004)
for x in [-1.43,1.43]:
 for y in [-1.55,1.55]:beam('Hewn corner post',(x,y,.78),(x,y,2.82),.18,group='Frame')
for y in [-1.55,1.55]:
 for z in [1.0,2.65,2.8]:beam('Front rear frame tie',(-1.54,y,z),(1.54,y,z),.14 if z!=2.8 else .18,group='Frame')
for x in [-1.43,1.43]:
 for z in [1.0,2.68,2.8]:beam('Side frame tie',(x,-1.64,z),(x,1.64,z),.15,group='Frame')
# Plaster front and sides. Rear is protective plank cladding.
panel('Left front plaster',(-1.42,-1.548),(-.76,-1.548),.96,2.66)
panel('Right front plaster',(.76,-1.548),(1.42,-1.548),.96,2.66)
panel('Door head plaster',(-.76,-1.548),(.76,-1.548),2.51,2.72)
for side in [-1,1]:
 x=side*1.43
 panel('Side wattle plaster',(x,1.54) if side<0 else (x,-1.54),(x,-1.54) if side<0 else (x,1.54),.96,2.72)
 beam('Diagonal side brace',(x+side*.034,-1.40,1.10),(x+side*.034,.05,2.58),.081,.073,group='Frame')
for i in range(17):
 x=-1.33+i*.167
 beam('Closed rear cladding',(x,1.56,.96),(x,1.56,2.74),.162,.06,group='WallPanels',rough=.003)
beam('Rear board tie',(-1.4,1.614,1.33),(1.4,1.614,1.33),.08,.07,group='Frame')
# Closed paired board doors, stout jambs, dark forged straps and ring pulls.
for x in [-.76,.76]:beam('Stout door jamb',(x,-1.635,.9),(x,-1.635,2.58),.16,group='Frame')
for z in [.925,2.56]:beam('Door threshold head',(-.84,-1.64,z),(.84,-1.64,z),.165,group='Frame')
for side in [-1,1]:
 for j in range(4):
  x=side*(.094+j*.177)
  beam('Heavy closed door board',(x,-1.616,1.0),(x,-1.616,2.48),.173,.076,group='Door',rough=.002)
 for z in [1.22,2.26]:
  beam('Forged hinge strap',(side*.69,-1.678,z),(side*.15,-1.678,z),.073,.02,'Iron','Door',.001)
  tube('Hinge barrel',[(side*.715,-1.7,z-.085),(side*.715,-1.7,z+.085)],.022,'Iron','Door',8)
  for x in [side*.61,side*.38,side*.20]:tube('Strap rivet',[(x,-1.69,z),(x,-1.712,z)],.018,'Iron','Door',8)
 x=side*.15
 beam('Ring escutcheon',(x,-1.675,1.49),(x,-1.675,1.70),.067,.015,'Iron','Door',.001)
 tube('Forged door pull',[(x+.053*math.cos(i*math.tau/28),-1.728,1.52+.063*math.sin(i*math.tau/28)) for i in range(29)],.011,'Iron','Door',7)
beam('Central security hasp',(-.085,-1.70,1.79),(.11,-1.70,1.79),.036,.02,'Iron','Door',.001)
# Little dark ventilation grilles only, backed by opaque dark metal.
for side in [-1,1]:
 x=side*1.483;y=.33
 mesh('Opaque vent shadow',[(x,y-.21,2.21),(x,y+.21,2.21),(x,y+.21,2.52),(x,y-.21,2.52)],[(0,1,2,3)],'Iron',group='Window')
 for yy in [y-.23,y+.23]:beam('Vent jamb',(x+side*.02,yy,2.18),(x+side*.02,yy,2.55),.046,group='Window',rough=.001)
 for z in [2.18,2.55]:beam('Vent sill',(x+side*.025,y-.25,z),(x+side*.025,y+.25,z),.058,group='Window',rough=.001)
 for j in range(6):beam('Vent narrow grille',(x+side*.033,y-.17+j*.068,2.23),(x+side*.033,y-.17+j*.068,2.51),.02,group='Window',rough=.001)
# Four modest open-riser treads and two stout stringers.
for x in [-.58,.58]:beam('Stair stringer',(x,-2.62,.08),(x,-1.67,.91),.115,.13,group='Stairs')
for j in range(4):
 y=-2.49+j*.237;z=.20+j*.205
 for offset in [-.067,.067]:beam('Stair tread',(-.68,y+offset,z),(.68,y+offset,z),.13,.066,group='Stairs',rough=.003)
for x in [-.57,.57]:stone('Stair resting stone',(x,-2.55,.065),(.16,.19,.065))
# Gable closure: visible exterior planks and practical triangular framing.
for side in [-1,1]:
 y=side*1.57
 for i in range(19):
  x=-1.43+i*.159;top=3.78-abs(x)*.52
  beam('Gable board',(x,y,2.83),(x,y,max(2.86,top)),.155,.056,group='WallPanels',rough=.002)
 for s in [-1,1]:beam('Gable sloping beam',(s*1.72,y+side*.043,2.72),(0,y+side*.043,3.89),.12,group='Frame')
 beam('Gable king post',(0,y+side*.053,2.79),(0,y+side*.053,3.87),.14,group='Frame')
 beam('Gable collar tie',(-1.05,y+side*.045,3.13),(1.05,y+side*.045,3.13),.11,group='Frame')
# Adapt the kit's thick, layered thatch construction to two gable slopes.
facets=[((-2.10,-2.0,2.71),(-2.10,2.0,2.71),(0,-2.0,3.86),(0,2.0,3.86)),
        ((2.10,2.0,2.71),(2.10,-2.0,2.71),(0,2.0,3.86),(0,-2.0,3.86))]
roof_code=kit_code.split('for fi,coords in enumerate(facets):',1)[1].split('# Weathered ridge poles',1)[0]
exec('for fi,coords in enumerate(facets):'+roof_code)
# Append/copy the RuralHouse ridge, stretching only length and placing on the new roof.
ridge=kit_objects['RH01_Roof_Ridge'];src.objects.link(ridge);ridge.name='SH01_Ridge'
for v in ridge.data.vertices:
 v.co.y*=1.25;v.co.z-=.28
ridge['reused_from']='RuralHouse01.blend / RH01_Roof_Ridge'
# Small rope bindings and visible wooden pegs from the same kit helpers.
for x in [-1.43,1.43]:
 for y in [-1.64,1.64]:
  for z in [1.0,2.65]:tube('Timber joint peg',[(x,y,z),(x,y+(.03 if y>0 else -.03),z)],.016,'Timber','Frame',7)
for x in [-1.43,1.43]:lash('Platform hemp binding',(x,-1.60,.76),'X',.125,3)
# Keep three restrained exterior props as separate editable objects and export.
props=bpy.data.collections.new('SH01_Props • reusable exterior pieces');scene.collection.children.link(props)
tub=kit_objects['RH01_ExteriorTub']
for i,(cx,cy,z,scale) in enumerate([(1.33,-1.98,0,1.13),(.99,-2.32,0,.75)]):
 ob=tub if i==0 else tub.copy()
 if i:ob.data=tub.data.copy()
 props.objects.link(ob);ob.name='SH01_Barrel' if i==0 else 'SH01_SmallTub'
 # The source tub is authored at (-1.14,-2.13,.47). Bake a local placement.
 if i==0:
  for v in ob.data.vertices:v.co=Vector(((v.co.x+1.14)*scale+cx,(v.co.y+2.13)*scale+cy,(v.co.z-.46)*scale+z))
 else:
  # Duplicate was copied after placement; remap the first barrel back into local coordinates.
  for v in ob.data.vertices:v.co=Vector(((v.co.x-1.33)/1.13*scale+cx,(v.co.y+1.98)/1.13*scale+cy,v.co.z/1.13*scale+z))
 ob['reused_from']='RuralHouse01.blend / RH01_ExteriorTub'
# A tied straw basket on the main barrel, using the shared rope material.
verts=[];uv=[];faces=[];cx=1.33;cy=-1.98
for j,(z,rr) in enumerate([(.66,.145),(.72,.18),(.92,.20),(1.08,.15),(1.13,.065)]):
 for i in range(20):
  a=i*math.tau/20;r=rr*(1+.04*math.sin(i*3+j));verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z));uv.append((i/20*2,j*.17))
for j in range(4):
 for i in range(20):faces.append((j*20+i,j*20+(i+1)%20,(j+1)*20+(i+1)%20,(j+1)*20+i))
faces.extend([tuple(reversed(range(20))),tuple(range(80,100))])
basket=mesh('SH01_TiedBasket',verts,faces,'Rope',uv)
src.objects.unlink(basket);props.objects.link(basket)
for p in basket.data.polygons:p.use_smooth=True
for z,rr in [(.78,.187),(1.06,.16)]:
 ob=tube('SH01_BasketBinding',[(cx+rr*math.cos(i*math.tau/40),cy+rr*math.sin(i*math.tau/40),z) for i in range(41)],.013,'Rope','PropBindings',6)
# Group logical components with the existing kit convention.
renames={'Wall_Frame':'Frame','CornerPosts':'Frame','Wall_Panel_A':'WallPanels','Wall_Panel_B':'WallPanels','Roof_Main':'Roof','Roof_ThatchLayers':'ThatchLayers','Roof_Ridge':'RidgeDetails','Rope_Lashings':'Lashings'}
merged={}
for name,obs in groups.items():merged.setdefault(renames.get(name,name),[]).extend(obs)
for name,obs in merged.items():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='SH01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if name=='WallPanels':
  for f in bm.faces:
   c=f.calc_center_median()
   if f.normal.x*c.x+f.normal.y*c.y<0:f.normal_flip()
 if name=='ThatchLayers':
  for f in bm.faces:
   if f.normal.z<0:f.normal_flip()
 bm.to_mesh(ob.data);bm.free()
 ob['scope']='Exterior only; authored Storehouse01 kit component'
 if name=='PropBindings':src.objects.unlink(ob);props.objects.link(ob)
components=list(src.objects);prop_objects=list(props.objects)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for obs,path in [(components,'Storehouse_01.fbx'),(prop_objects,'SH01_Props.fbx')]:
 for ob in obs:ob.modifiers.new('Export triangulation','TRIANGULATE')
 fbx(ART/'Exports'/path,obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Export triangulation'])
# Native scale figure and restrained studio setup (excluded from exports).
with bpy.data.libraries.load(str(ROOT/'SourceArt/Characters/Mannequins/Manny/Manny.blend'),link=False) as (a,b):b.objects=['root','FIT_Manny']
for ob in b.objects:
 if ob:studio.objects.link(ob);ob.hide_set(False)
rig=bpy.data.objects.get('root')
if rig:
 rig.animation_data_clear();rig.location=(2.8,-.9,0)
 for p in rig.pose.bones:p.rotation_mode='XYZ'
 for n,ang in [('upperarm_l',-.48),('upperarm_r',.48)]:
  if n in rig.pose.bones:rig.pose.bones[n].rotation_euler.y=ang
bpy.ops.mesh.primitive_plane_add(size=200);ground=bpy.context.object;ground.name='Review ground'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.105,.115,.095,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Soft daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.65,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
ld=bpy.data.lights.new('Daylight','AREA');light=bpy.data.objects.new('Daylight',ld);studio.objects.link(light);light.location=(-4,-6,10);ld.energy=1700;ld.shape='DISK';ld.size=7;light.rotation_euler=(Vector((0,0,1.6))-light.location).to_track_quat('-Z','Y').to_euler()
sun=bpy.data.lights.new('Sun','SUN');so=bpy.data.objects.new('Sun',sun);studio.objects.link(so);so.rotation_euler=(.38,-.5,-.48);sun.energy=1.4;sun.angle=.13
def camera(name,pos,target,ortho):
 cd=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,cd);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=ortho;return o
cams=[camera('Front',(0,-13,3.5),(0,0,1.95),6.6),camera('Three-quarter',(7.8,-12,5.7),(.35,-.1,1.9),7.25),camera('Side',(12,0,4),(0,0,2),6.5),camera('Rear',(-6,11,4.7),(0,0,1.95),6.5),camera('Roof',(4,-5,14),(0,0,1.8),6.5)]
scene.camera=cams[1]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
for ob in components:ob.select_set(True)
bpy.context.view_layer.objects.active=components[0]
scene['asset_note']='Storehouse_01; exterior only; ground-centred metre scale; RuralHouse01 materials and kit reused.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Storehouse01.blend'))
print('STOREHOUSE_SAVED',len(components),'components',flush=True)
if '--no-render' not in sys.argv:
 for cam,label in [(cams[1],'storehouse-three-quarter'),(cams[0],'storehouse-front'),(cams[2],'storehouse-side'),(cams[3],'storehouse-rear'),(cams[4],'storehouse-roof')]:
  scene.camera=cam;scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
print('STOREHOUSE_COMPLETE',flush=True)
