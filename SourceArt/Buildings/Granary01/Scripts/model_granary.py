"""One authored exterior granary, assembled with the existing SHŌEN rural kit."""
from pathlib import Path
import ast, math, random, sys
import bpy, bmesh
from mathutils import Vector
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01';STORE=ART.parent/'Storehouse01';OUT=ROOT/'artifacts/granary01'
random.seed(1188)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.4
src=bpy.data.collections.new('Granary_01 • editable exterior');scene.collection.children.link(src)
studio=bpy.data.collections.new('Review only • excluded from export');scene.collection.children.link(studio)
groups={}
with bpy.data.libraries.load(str(STORE/'Storehouse01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Plaster','SH01_Stone','SH01_Iron','RH01_Rope']]
mats={m.name.split('_',1)[1]:m for m in b.materials}
with bpy.data.libraries.load(str(KIT/'RuralHouse01.blend'),link=False) as (a,b):b.objects=['RH01_Roof_Ridge']
ridge=b.objects[0]
kit_code=(KIT/'Scripts/model_house.py').read_text()
for node in ast.parse(kit_code).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','beam','tube','lash','panel'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
# Reuse the storehouse's hand-set fieldstone form and rural stone material.
for node in ast.parse((STORE/'Scripts/refine_reference_match.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='fieldstone':
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-storehouse-kit','exec'))
# Six stout supports and two intermediate bearing stones leave a broad visible air gap.
for x in [-1.28,0,1.28]:
 for y in [-1.27,1.27]:
  fieldstone('Bedded fieldstone footing',(x,y,.145),(.29,.27,.18))
  fieldstone('Split bearing stone',(x-.07,y+.018,.28),(.17,.20,.105))
  fieldstone('Split bearing stone',(x+.09,y-.015,.28),(.13,.19,.105))
  beam('Stout granary support',(x,y,.30),(x,y,1.10),.235,.235,group='SupportPosts')
for x in [-1.28,1.28]:
 fieldstone('Intermediate fieldstone',(x,0,.145),(.26,.25,.18))
 beam('Intermediate support',(x,0,.26),(x,0,1.08),.21,group='SupportPosts')
for y in [-1.33,1.33]:beam('Raised platform rim',(-1.48,y,.94),(1.48,y,.94),.20,.22,group='Platform')
for x in [-1.28,0,1.28]:beam('Bearing crossbeam',(x,-1.46,.88),(x,1.46,.88),.19,.20,group='Platform')
for y in [-1.43,1.42]:
 for j in range(2):beam('Exposed platform board',(-1.47,y+(j-.5)*.12,1.075),(1.47,y+(j-.5)*.12,1.075),.116,.065,group='Platform',rough=.003)
for x in [-1.41,1.41]:beam('Narrow side ledge',(x,-1.32,1.075),(x,1.32,1.075),.16,.065,group='Platform',rough=.003)
# A single exterior underside closes the shell; no modeled room or interior floor.
mesh('Opaque exterior underside',[(-1.3,-1.29,1.025),(-1.3,1.29,1.025),(1.3,1.29,1.025),(1.3,-1.29,1.025)],[(0,1,2,3)],'Timber',group='Platform')
for x in [-1.28,1.28]:
 for y in [-1.27,1.27]:beam('Storage body corner post',(x,y,1.00),(x,y,2.77),.17,group='Frame')
for y in [-1.27,1.27]:
 for z in [1.16,2.62,2.76]:beam('Front rear wall tie',(-1.40,y,z),(1.40,y,z),.12 if z==1.16 else .15,group='Frame')
for x in [-1.28,1.28]:
 for z in [1.16,1.61,2.64,2.76]:beam('Side wall tie',(x,-1.36,z),(x,1.36,z),.11 if z==1.61 else .14,group='Frame')
# Plain wattle/plaster facade around a compact closed store door.
panel('Front left infill',(-1.26,-1.269),(-.61,-1.269),1.13,2.65)
panel('Front right infill',(.61,-1.269),(1.26,-1.269),1.13,2.65)
panel('Door head infill',(-.61,-1.269),(.61,-1.269),2.48,2.70)
for side in [-1,1]:
 x=side*1.278
 panel('Closed side plaster',(x,1.26) if side<0 else (x,-1.26),(x,-1.26) if side<0 else (x,1.26),1.13,2.70)
 # Low paired braces keep the high vent readable.
 for sy in [-1,1]:beam('Low storage-body brace',(x+side*.036,sy*1.17,1.63),(x+side*.036,sy*.40,1.20),.075,.069,group='Frame')
for i in range(16):
 x=-1.205+i*.1607
 beam('Protective rear plank',(x,1.273,1.14),(x,1.273,2.70),.157,.065,group='WallPanels',rough=.0025)
beam('Rear board retaining rail',(-1.28,1.327,1.66),(1.28,1.327,1.66),.085,.065,group='Frame')
# Narrow solid door with dark forged straps, one ring, and a simple securing bar.
for x in [-.61,.61]:beam('Door jamb',(x,-1.353,1.065),(x,-1.353,2.55),.145,group='Door')
for z in [1.095,2.515]:beam('Door head and threshold',(-.68,-1.356,z),(.68,-1.356,z),.14,group='Door')
for i in range(7):
 x=-.474+i*.158
 beam('Closed stout door plank',(x,-1.326,1.145),(x,-1.326,2.47),.155,.071,group='Door',rough=.002)
for z in [1.35,2.27]:
 beam('Door face crossrail',(-.53,-1.376,z),(.53,-1.376,z),.062,.045,group='Door')
 beam('Forged strap hinge',(-.57,-1.409,z),(-.04,-1.409,z),.046,.015,'Iron','Door',.001)
 tube('Hinge barrel',[(-.566,-1.421,z-.058),(-.566,-1.421,z+.058)],.016,'Iron','Door',8)
 for x in [-.48,-.29,-.12]:tube('Flattened hinge rivet',[(x,-1.418,z),(x,-1.429,z)],.012,'Iron','Door',7)
beam('Door ring plate',(.34,-1.401,1.65),(.34,-1.401,1.82),.07,.018,'Iron','Door',.001)
tube('Single forged ring pull',[(.34+.054*math.cos(i*math.tau/30),-1.45,1.684+.063*math.sin(i*math.tau/30)) for i in range(31)],.01,'Iron','Door',7)
beam('Short security hasp',(.32,-1.412,1.92),(.61,-1.412,1.92),.037,.019,'Iron','Door',.001)
# Small upper vents: dark closed backing and substantial vertical timber slats.
for side in [-1,1]:
 x=side*1.312;y=.04
 verts=[(x,y-.29,2.18),(x,y+.29,2.18),(x,y+.29,2.49),(x,y-.29,2.49)]
 mesh('Recessed vent darkness',verts,[(0,1,2,3) if side>0 else (3,2,1,0)],'Iron',group='Vents')
 for yy in [y-.315,y+.315]:beam('Vent jamb',(x+side*.016,yy,2.15),(x+side*.016,yy,2.52),.052,group='Vents',rough=.001)
 for z in [2.15,2.52]:beam('Vent head sill',(x+side*.025,y-.34,z),(x+side*.025,y+.34,z),.06,group='Vents',rough=.001)
 for j in range(7):beam('High narrow ventilation slat',(x+side*.038,y-.25+j*.0833,2.20),(x+side*.038,y-.25+j*.0833,2.47),.028,.037,group='Vents',rough=.001)
# Five narrow, steep open treads reinforce the raised grain-store character.
for x in [-.38,.38]:
 beam('Ladder stringer',(x,-2.29,.10),(x,-1.48,1.12),.095,.11,group='Stairs')
 fieldstone('Ladder landing stone',(x,-2.26,.055),(.17,.19,.065))
for j in range(5):
 y=-2.21+j*.166;z=.23+j*.193
 beam('Compact open stair tread',(-.435,y,z),(.435,y,z),.18,.052,group='Stairs',rough=.003)
# Four hipped slopes reuse the exact kit thatch construction with a shorter ridge.
facets=[((-1.93,-1.82,2.72),(-1.93,1.82,2.72),(0,-.61,3.78),(0,.61,3.78)),
        ((1.93,1.82,2.72),(1.93,-1.82,2.72),(0,.61,3.78),(0,-.61,3.78)),
        ((1.93,-1.82,2.72),(-1.93,-1.82,2.72),(0,-.61,3.78),(0,-.61,3.78)),
        ((-1.93,1.82,2.72),(1.93,1.82,2.72),(0,.61,3.78),(0,.61,3.78))]
roof_code=kit_code.split('for fi,coords in enumerate(facets):',1)[1].split('# Weathered ridge poles',1)[0]
exec('for fi,coords in enumerate(facets):'+roof_code)
# Reuse ridge as a component, adapting its length to the compact hipped roof.
src.objects.link(ridge);ridge.name='GR01_Ridge'
for v in ridge.data.vertices:v.co.y*=.51;v.co.z-=.35
for slot in ridge.material_slots:
 family=slot.material.name.split('_',1)[1]
 if family in mats:slot.material=mats[family]
ridge['reused_from']='RuralHouse01.blend / RH01_Roof_Ridge'
for y in [-1.28,-.72,0,.72,1.28]:
 for x in [-.205,.205]:lash('Ridge hemp fastening',(x,y*.51,3.935),'Y',.082,3)
for x in [-1.28,1.28]:
 for y in [-1.34,1.34]:
  for z in [1.16,2.63]:tube('Exposed timber peg',[(x,y,z),(x,y+(.025 if y>0 else -.025),z)],.014,'Timber','Frame',7)
# Group the authored parts into clear editable objects.
renames={'Fieldstone':'StoneFootings','Wall_Panel_A':'WallPanels','Wall_Panel_B':'WallPanels','Roof_Main':'Roof','Roof_ThatchLayers':'RoofBundles','Rope_Lashings':'RidgeLashings'}
merged={}
for name,obs in groups.items():merged.setdefault(renames.get(name,name),[]).extend(obs)
for name,obs in merged.items():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='GR01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if name in ['WallPanels','Vents']:
  for f in bm.faces:
   c=f.calc_center_median()
   if f.normal.x*c.x+f.normal.y*c.y<0:f.normal_flip()
 if name=='RoofBundles':
  for f in bm.faces:
   if f.normal.z<0:f.normal_flip()
 bm.to_mesh(ob.data);bm.free()
 ob['scope']='Exterior only; editable rural-kit component'
# Match the storehouse's existing vertex-tinted shared materials.
for ob in src.objects:
 colors=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for face in ob.data.polygons:
  family=ob.data.materials[face.material_index].name.split('_',1)[1]
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   k=.96+.04*math.sin(p.x*4.8+p.y*2.4+p.z*2.0)
   if family=='Timber':
    damp=.86+.14*min(1,p.z/.6);rgb=(.80*k*damp,.73*k*damp,.64*k*damp)
   elif family=='Thatch':rgb=(.81*k,.75*k,.63*k)
   elif family=='Stone':rgb=(.71*k,.71*k,.67*k)
   elif family=='Plaster':
    wear=.80+.20*max(0,min(1,(p.z-1.10)/.48));rgb=(.96*wear*k,.93*wear*k,.84*wear*k)
   else:rgb=(1,1,1)
   colors.data[li].color=(*rgb,1)
 ob.data.color_attributes.active_color=colors
components=list(src.objects)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for o in components:o.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/Granary_01.fbx',components)
for o in components:o.modifiers.remove(o.modifiers['Export triangulation'])
# Restrained standalone studio view, excluded from runtime export.
bpy.ops.mesh.primitive_plane_add(size=200);ground=bpy.context.object;ground.name='Review ground'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
gm=bpy.data.materials.new('Review earth');gm.use_nodes=True;gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.039,.046,.042,1);gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(gm)
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.34,.39,1);world.node_tree.nodes['Background'].inputs[1].default_value=.40
ld=bpy.data.lights.new('Daylight','AREA');light=bpy.data.objects.new('Daylight',ld);studio.objects.link(light);light.location=(-3,-6,9);ld.energy=1550;ld.color=(1,.90,.78);ld.shape='DISK';ld.size=5;light.rotation_euler=(Vector((0,0,1.6))-light.location).to_track_quat('-Z','Y').to_euler()
ld=bpy.data.lights.new('Side soft fill','AREA');light=bpy.data.objects.new('Side soft fill',ld);studio.objects.link(light);light.location=(6,0,5);ld.energy=650;ld.size=5;light.rotation_euler=(Vector((0,0,1.8))-light.location).to_track_quat('-Z','Y').to_euler()
sun=bpy.data.lights.new('Sun','SUN');so=bpy.data.objects.new('Sun',sun);studio.objects.link(so);so.rotation_euler=(.38,-.5,-.48);sun.energy=1.7;sun.color=(1,.91,.80);sun.angle=.13
def camera(name,pos,target,ortho):
 cd=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,cd);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=ortho;return o
cam=camera('Granary three-quarter',(7,-11,5.9),(0,-.12,1.95),5.7)
camera('Granary front',(0,-12,3.6),(0,-.1,1.96),5.4)
scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
for ob in components:ob.select_set(True)
bpy.context.view_layer.objects.active=components[0]
scene['asset_note']='Granary_01: exterior only, metre scale, ground-centred pivot. Shared rural materials, hipped thatch, ridge, hewn framing and fieldstones reused.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Granary01.blend'))
print('GRANARY_SAVED',len(components),'components',flush=True)
scene.render.filepath=str(OUT/'granary-three-quarter.png');bpy.ops.render.render(write_still=True)
print('GRANARY_COMPLETE',flush=True)
