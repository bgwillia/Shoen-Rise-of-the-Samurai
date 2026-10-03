"""Smithy01: one authored open workshop using the existing rural building kit."""
from pathlib import Path
import ast, math, random, sys
import bpy, bmesh
from mathutils import Vector
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'; STORE=ART.parent/'Storehouse01'; OUT=ROOT/'artifacts/smithy01'
random.seed(1189)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'; scene.view_settings.exposure=-.05
src=bpy.data.collections.new('Smithy_01 • editable exterior and open workshop'); scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • excluded from runtime'); scene.collection.children.link(studio)
groups={}
with bpy.data.libraries.load(str(STORE/'Storehouse01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope']]
mats={m.name.split('_',1)[1]:m for m in b.materials}
for name,col,rough,metal in [('Charcoal',(.009,.008,.007),.96,0),('Ember',(1,.13,.008),.65,0),('Water',(.026,.050,.052),.20,.2)]:
 m=bpy.data.materials.new('SM01_'+name); m.use_nodes=True; m.diffuse_color=(*col,1)
 p=m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value=(*col,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 if name=='Ember':p.inputs['Emission Color'].default_value=(1,.11,.004,1); p.inputs['Emission Strength'].default_value=.7
 mats[name]=m
kit_code=(KIT/'Scripts/model_house.py').read_text()
for node in ast.parse(kit_code).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','beam','tube','lash','panel','stone'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
for node in ast.parse((STORE/'Scripts/refine_reference_match.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='fieldstone':
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-storehouse-kit','exec'))
original_panel=panel
def panel(*args,**kwargs):
 ob=original_panel(*args,**kwargs)
 mod=ob.modifiers.new('Wattle panel thickness','SOLIDIFY');mod.thickness=.055
 return ob
def block(name,center,size,mat='Stone',group='Forge',bevel=.02):
 x,y,z=center; sx,sy,sz=[s/2 for s in size]
 vv=[(x+a*sx,y+b*sy,z+c*sz) for c in [-1,1] for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 ob=mesh(name,vv,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,group=group)
 if mat=='Stone':
  for v in ob.data.vertices:
   v.co.x+=random.uniform(-.013,.013);v.co.y+=random.uniform(-.014,.014);v.co.z+=random.uniform(-.008,.008)
 if bevel:
  mod=ob.modifiers.new('Worn arrises','BEVEL'); mod.width=bevel; mod.segments=2
 return ob
# Low bedded foundation, continuous at the enclosed rear and open under the work bays.
for x in [-2.35,-.75,.85,2.35]:
 for y in [-1.5,1.5]:
  fieldstone('Bedded post stone',(x,y,.11),(.24,.24,.15))
  beam('Heavy workshop post',(x,y,.19),(x,y,2.46),.19,.205,group='Frame',rough=.014)
for x in [-2.35,2.35]:
 for i in range(7):fieldstone('Side foundation',(x,-1.26+i*.425,.12),(.21,.24,.155))
for i in range(13):fieldstone('Rear low stone sill',(-2.25+i*.375,1.50,.12),(.22,.21,.16))
for y in [-1.5,1.5]:
 beam('Long eave carrying beam',(-2.53,y,2.40),(2.53,y,2.40),.23,.22,group='Frame')
for x in [-2.35,-.75,.85,2.35]:
 beam('Roof transverse tie',(x,-1.67,2.43),(x,1.67,2.43),.18,.21,group='Frame')
 for s in [-1,1]:
  beam('Workshop knee brace',(x,-1.52,1.93),(x+s*.39,-1.52,2.36),.075,.08,group='Frame')
  beam('Roof principal rafter',(x,s*1.80,2.40),(x,0,3.75),.13,.145,group='Frame')
 beam('Ridge king post',(x,0,2.43),(x,0,3.76),.13,group='Frame')
for y in [-1.43,1.43]:
 for x in [-2.35,-.75,.85,2.35]:
  tube('Visible mortise peg',[(x,y,2.4),(x,y-.12,2.4)],.019,'Timber','Frame',8)
# Rear face and side closures: one thin exterior shell, no hidden rooms.
for xa,xb in [(-2.35,-.75),(-.75,.85),(.85,2.35)]:
 panel('Rear wattle infill',(xb,1.50),(xa,1.50),.28,2.32)
for x in [-2.35,2.35]:
 panel('Side rear plaster',(x,1.48) if x<0 else (x,-.05),(x,-.05) if x<0 else (x,1.48),.28,2.32)
 for z in [.31,1.09,2.30]:beam('Side protective rail',(x,-.10,z),(x,1.57,z),.105,.095,group='Walls')
 for i in range(8):
  y=-1.46+i*.18
  if x<0:beam('Side closed plank section',(x,y,.28),(x,y,2.32),.068,.176,group='Walls',rough=.003)
 for i in range(19):
  y=-1.48+i*.164; top=3.70-abs(y)*.70
  beam('Gable weatherboards',(x,y,2.46),(x,y,top),.055,.159,group='Walls',rough=.002)
 for s in [-1,1]:beam('Gable rake timber',(x+s*.01,s*1.85,2.38),(x,0,3.80),.115,.12,group='Frame')
 beam('Gable collar tie',(x,-1.11,2.99),(x,1.11,2.99),.11,group='Frame')
for z in [.33,1.02,2.3]:beam('Rear exposed rail',(-2.42,1.55,z),(2.42,1.55,z),.105,.10,group='Walls')
# A broad two-slope gable roof from the established thatch construction.
facets=[((-2.83,-2.06,2.51),(2.83,-2.06,2.51),(-2.83,0,3.77),(2.83,0,3.77)),
        ((2.83,2.03,2.51),(-2.83,2.03,2.51),(2.83,0,3.77),(-2.83,0,3.77))]
roof_code=kit_code.split('for fi,coords in enumerate(facets):',1)[1].split('# Weathered ridge poles',1)[0]
exec('for fi,coords in enumerate(facets):'+roof_code)
# Orient the two re-axis-aligned roof surfaces before inward thatch thickness.
for ob in groups['Roof_Main']:
 bm=bmesh.new();bm.from_mesh(ob.data)
 for f in bm.faces:
  if f.normal.z<0:f.normal_flip()
 bm.to_mesh(ob.data);bm.free()
with bpy.data.libraries.load(str(KIT/'RuralHouse01.blend'),link=False) as (a,b):b.objects=['RH01_Roof_Ridge']
ridge=b.objects[0];src.objects.link(ridge);ridge.name='SM01_Ridge'
for v in ridge.data.vertices:
 p=v.co.copy(); v.co=(-p.y*1.78,p.x,p.z-.36)
for slot in ridge.material_slots:
 family=slot.material.name.split('_',1)[1]
 if family in mats:slot.material=mats[family]
ridge['reused_from']='RuralHouse01 / Roof_Ridge'
for x in [-2.28,-1.28,0,1.28,2.28]:
 for y in [-.205,.205]:lash('Ridge rope binding',(x,y,3.93),'X',.083,3)
# Low timber lean-to on left gable: closed side store, no furnished interior.
for y in [-1.35,1.22]:
 fieldstone('Lean-to foot',(-3.47,y,.08),(.20,.20,.12))
 beam('Lean-to outer upright',(-3.47,y,.14),(-3.47,y,1.94),.13,group='LeanTo')
 beam('Lean-to sloping bearer',(-3.65,y,1.92),(-2.25,y,2.47),.10,.12,group='LeanTo')
beam('Lean-to eave tie',(-3.5,-1.55,1.93),(-3.5,1.5,1.93),.14,group='LeanTo')
for i in range(18):
 y=-1.54+i*.179
 beam('Lean-to weathered roof board',(-3.64,y,1.98+random.uniform(-.01,.01)),(-2.24,y,2.52),.175,.048,group='LeanTo',rough=.003)
for xx in [-3.54,-2.98,-2.43]:beam('Roof board retaining batten',(xx,-1.61,2.03+(xx+3.64)*.386),(xx,1.56,2.03+(xx+3.64)*.386),.065,.038,group='LeanTo')
for i in range(7):
 x=-3.39+i*.147
 beam('Lean-to closed store door',(x,-1.36,.22),(x,-1.36,1.90+(x+3.47)*.35),.143,.07,group='LeanTo',rough=.002)
for z in [.5,1.58]:beam('Lean-to door crossrail',(-3.45,-1.414,z),(-2.43,-1.414,z),.065,.045,group='LeanTo')
beam('Plain store latch',(-2.77,-1.445,.94),(-2.55,-1.445,.94),.035,.023,'Iron','LeanTo',.001)
# Hand-built forge and soot chimney, authored for this exterior work bay.
fx=1.35; fy=.43
sys.path.insert(0,str(ART/'Scripts'))
from forge import build_forge
build_forge(globals())
# Reusable smithing props authored separately in the same material/geometry language.
sys.path.insert(0,str(ART/'Scripts'))
from smithing_props import build_props
build_props(globals())
# Rounded thatch end-grain closes the gables with real reed detail.
for end in [-1,1]:
 for side in [-1,1]:
  normal=Vector((0,side*1.26,2.06)).normalized()
  verts=[];uvs=[];faces=[]
  for j in range(46):
   v=j/45;y=side*2.06*(1-v);z=2.51+1.26*v
   for k in range(7):
    t=k/6
    pp=Vector((end*2.83,y,z))-normal*(.30*t)
    pp.x+=end*(.018+.045*math.sin(t*math.pi))
    pp.z+=.014*math.sin(v*24)+.022*(1-v)
    verts.append(pp);uvs.append((t*.35/1.65,(1-v)*2.42/1.65))
  for j in range(45):
   for k in range(6):q=j*7+k;faces.append((q,q+1,q+8,q+7))
  ob=mesh('Rounded layered gable thatch',verts,faces,'Thatch',uvs,'RoofGableThatch')
  for f in ob.data.polygons:f.use_smooth=True
  for i in range(125):
   v=(i+random.random())/125
   depth=random.uniform(.02,.27)
   p0=Vector((end*(2.86+random.uniform(0,.04)),side*2.06*(1-v),2.51+1.26*v))-normal*depth
   tangent=Vector((0,-side*2.06,1.26)).normalized()
   p1=p0+tangent*random.uniform(.07,.17)
   tube('Gable loose reed tuft',[p0,p0.lerp(p1,.5)+Vector((end*.012,0,-.008)),p1],random.uniform(.002,.0045),'Thatch','RoofGableThatch',5)
# Small unevenness across the layered roof avoids machine-straight planes.
for name in ['Roof_Main','Roof_ThatchLayers','Eaves','RoofGableThatch']:
 for ob in groups.get(name,[]):
  for v in ob.data.vertices:
   p=v.co;p.z+=.016*math.sin(p.x*4+p.y*1.2)+.011*math.sin(p.x*7.1-p.y*2.3)-.038*math.exp(-p.x*p.x/3)*(abs(p.y)/2.1)**2
# Restrained drying splits on the exposed front post faces.
for x in [-2.35,-.75,.85,2.35]:
 for i in range(8):
  xx=x+random.uniform(-.065,.065);z=random.uniform(.36,2.02);length=random.uniform(.12,.39)
  mesh('Dark timber drying split',[(xx,-1.613,z),(xx-.004,-1.614,z+length*.42),(xx+.005,-1.613,z+length),(xx+.003,-1.614,z+length*.55)],[(0,1,2,3)],'Charcoal',group='Frame')
for i in range(28):
 x=random.uniform(-3.5,3.3);y=random.uniform(-2.5,-1.85)
 fieldstone('Workshop apron stone chip',(x,y,.018),(random.uniform(.025,.055),random.uniform(.025,.06),random.uniform(.024,.045)))
# Merge into useful editable pieces with the same ground pivot as the rural kit.
renames={'Foundation':'ForgeMasonry','Fieldstone':'Foundations','Wall_Panel_A':'Walls','Wall_Panel_B':'Walls','Roof_Main':'Roof','Roof_ThatchLayers':'RoofBundles','Rope_Lashings':'RidgeLashings','Eaves':'RoofEaves'}
merged={}
for name,obs in groups.items():merged.setdefault(renames.get(name,name),[]).extend(obs)
for name,obs in merged.items():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='SM01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if name in ['RoofBundles']:
  for f in bm.faces:
   if f.normal.z<0:f.normal_flip()
 bm.to_mesh(ob.data);bm.free()
 ob['scope']='Exterior and visible open workshop only'
# Broad soot gradients use the existing shared rural vertex-tinted materials.
for ob in src.objects:
 colors=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for face in ob.data.polygons:
  family=ob.data.materials[face.material_index].name.split('_',1)[1]
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   k=.93+.045*math.sin(p.x*4.3+p.y*2.7+p.z*1.8)
   soot=1-.50*math.exp(-((p.x-fx)**2/.9+(p.y-fy)**2/1.1))*max(.1,min(1,(p.z-.6)/.8))
   if ob.name=='SM01_Chimney':soot=.63-.30*max(0,(p.z-3.8)/.8)
   if ob.name=='SM01_GroundApron':rgb=(.25*k,.205*k,.145*k)
   elif family=='Timber':rgb=(.54*k*soot,.45*k*soot,.34*k*soot)
   elif family=='Thatch':rgb=(.58*k,.46*k,.32*k)
   elif family=='Stone':rgb=(.76*k*soot,.74*k*soot,.68*k*soot)
   elif family=='Plaster':rgb=(.84*k*soot,.79*k*soot,.66*k*soot)
   else:rgb=(1,1,1)
   tone=ob.data.color_attributes.get('MasonryTone')
   if tone and family=='Stone' and tone.data[li].color[0]>0:rgb=tuple(rgb[a]*tone.data[li].color[a] for a in range(3))
   colors.data[li].color=(*rgb,1)
 ob.data.color_attributes.active_color=colors
components=list(src.objects)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for o in components:o.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/Smithy_01.fbx',components)
anvil=bpy.data.objects.get('SM01_Anvil')
if anvil:
 duplicate=anvil.copy();duplicate.data=anvil.data.copy();src.objects.link(duplicate)
 for v in duplicate.data.vertices:v.co.x-=.55;v.co.y+=1.95
 fbx(ART/'Exports/Anvil_01.fbx',[duplicate]);bpy.data.objects.remove(duplicate,do_unlink=True)
for o in components:o.modifiers.remove(o.modifiers['Export triangulation'])
# Studio ground and lights, excluded from runtime exports.
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review ground'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.068,.070,.059,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.40,.47,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
def light(name,kind,loc,energy,size,color):
 d=bpy.data.lights.new(name,kind);o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=energy;d.color=color
 if kind=='AREA':d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
 else:d.shadow_soft_size=size
 return o
light('Soft afternoon','AREA',(-4,-7,9),1200,5,(1,.88,.70))
light('Open workshop fill','AREA',(2,-6,3.5),210,4,(.80,.87,1))
light('Rear sky fill','AREA',(4,4,6),700,5,(.85,.91,1))
workfill=light('Work bay reflected daylight','AREA',(-1.2,-3.0,2.0),130,2,(1,.87,.72))
workfill.rotation_euler=(Vector((-1.2,.4,1.3))-workfill.location).to_track_quat('-Z','Y').to_euler()
light('Hot hearth','POINT',(fx,-.02,.98),35,.22,(1,.18,.015))
sun=bpy.data.lights.new('Afternoon sun','SUN');so=bpy.data.objects.new('Afternoon sun',sun);studio.objects.link(so);so.rotation_euler=(.4,-.5,-.55);sun.energy=2.0;sun.angle=.15
cd=bpy.data.cameras.new('Smithy three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(-8.9,-14,6.25);cam.rotation_euler=(Vector((-.18,-.1,2.12))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='PERSP';cd.lens=60;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='Smithy_01; metre scale; ground-centred pivot; rural-kit materials and roof. Exterior / open work bay only.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Smithy01.blend'))
print('SMITHY_SAVED',len(components),'editable components',flush=True)
scene.render.filepath=str(OUT/'smithy-three-quarter.png');bpy.ops.render.render(write_still=True)
print('SMITHY_COMPLETE',flush=True)
