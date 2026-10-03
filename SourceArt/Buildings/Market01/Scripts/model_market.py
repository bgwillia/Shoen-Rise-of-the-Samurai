"""Market01: one authored modular exterior assembly, using the existing rural kit."""
from pathlib import Path
import ast, math, random, sys, json
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils import noise as surface_noise
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[2]
KIT=ART.parent/'RuralHouse01'; STORE=ART.parent/'Storehouse01'; OUT=ROOT/'artifacts/market01'
random.seed(118031)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def coll(n):
 c=bpy.data.collections.new(n);scene.collection.children.link(c);return c
src=coll('Market_01 • editable module library'); layout=coll('Market_01 • authored assembly');studio=coll('Review only • not exported')
groups={};modules={};instances=[]
with bpy.data.libraries.load(str(STORE/'Storehouse01.blend'),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in ['SH01_Thatch','SH01_Timber','SH01_Stone','SH01_Iron','RH01_Rope']]
mats={m.name.split('_',1)[1]:m for m in b.materials}
colors={'Cloth':(.58,.50,.37),'Pottery':(.19,.105,.058),'Leaf':(.14,.22,.055),'Root':(.68,.60,.40),'Fish':(.32,.30,.22),'Ink':(.025,.020,.014)}
for name,c in colors.items():
 m=bpy.data.materials.new('MK01_'+name);m.use_nodes=True;m.diffuse_color=(*c,1);n=m.node_tree.nodes;l=m.node_tree.links;p=n['Principled BSDF'];p.inputs['Roughness'].default_value=.88
 color=n.new('ShaderNodeVertexColor');color.layer_name='Color';mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(*c,1);l.new(color.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
 if name=='Cloth':
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(KIT/'Textures/RH01_Rope_Normal.png'));tex.image.colorspace_settings.name='Non-Color';tex.image.pack();normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.25;l.new(tex.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
 # Existing natural-fibre / stone maps add surface variation to new market accents.
 if name in ('Cloth','Pottery','Root','Fish'):
  family='Rope' if name=='Cloth' else 'Stone'
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(KIT/'Textures'/('RH01_'+family+'_BaseColor.png')));tex.image.pack()
  detail=n.new('ShaderNodeMixRGB');detail.blend_type='MIX';detail.inputs[0].default_value=.22 if name=='Cloth' else .12;detail.inputs[1].default_value=(1,1,1,1);l.new(tex.outputs['Color'],detail.inputs[2])
  product=n.new('ShaderNodeMixRGB');product.blend_type='MULTIPLY';product.inputs[0].default_value=1;l.new(mix.outputs[0],product.inputs[1]);l.new(detail.outputs[0],product.inputs[2]);l.new(product.outputs[0],p.inputs['Base Color'])
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150 if name=='Cloth' else 65;noise.inputs['Detail'].default_value=2
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.004 if name=='Cloth' else .003;l.new(noise.outputs['Fac'],bump.inputs['Height'])
  if name=='Cloth':l.new(normal.outputs[0],bump.inputs['Normal'])
  l.new(bump.outputs[0],p.inputs['Normal']);p.inputs['Specular IOR Level'].default_value=.20
 mats[name]=m
for node in ast.parse((KIT/'Scripts/model_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','beam','tube','lash','stone'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-rural-kit','exec'))
kit_beam=beam
def beam(name,a,b,width,depth=None,mat='Timber',group='Frame',rough=.004):
 ob=kit_beam(name,a,b,width,depth,mat,group,rough)
 if mat=='Timber':
  ox=random.random();oy=random.random()
  for p in ob.data.uv_layers.active.data:p.uv.x=p.uv.x*max(.22,width*3)+ox;p.uv.y=p.uv.y*.58+oy
 return ob
def before():return set(src.objects)
def collect(old,name):modules[name]=[o for o in src.objects if o not in old]
def cloth(name,width,depth,back=2.38,front=2.08,group='Canopy',sag=.18):
 vv=[];uv=[];ff=[];nx=28;ny=16
 for j in range(ny+1):
  v=j/ny
  for i in range(nx+1):
   u=i/nx;x=(u-.5)*width;y=(v-.5)*depth
   z=front+(back-front)*v-sag*math.sin(math.pi*u)*(.42+.58*math.sin(math.pi*v))
   z+=.048*math.sin(u*math.pi*7+v*3)*math.sin(v*math.pi)+.026*math.sin(u*22+v*3)*math.sin(math.pi*u)
   # Radial gathering fades away from the four tied cloth corners.
   for cu,cv in [(0,0),(1,0),(0,1),(1,1)]:
    du=u-cu;dv=v-cv;rr=math.sqrt((du*width)**2+(dv*depth)**2);angle=math.atan2(dv*depth,du*width)
    z+=.055*math.sin(angle*13+rr*2)*math.exp(-rr*3.0)*min(1,rr*8)
   x+=.018*math.sin(v*11+u*2)*math.sin(math.pi*u);y+=.045*math.sin(u*12+1.4)*(1-v)**3
   vv.append((x,y,z));uv.append((u*width*2,v*depth*2))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;ff.append((k,k+1,k+nx+2,k+nx+1))
 ob=mesh(name,vv,ff,'Cloth',uv,group);so=ob.modifiers.new('Rough woven cloth thickness','SOLIDIFY');so.thickness=.009
 for p in ob.data.polygons:p.use_smooth=True
 # Hems follow the same sag, with restrained stitched panel seams.
 for j in [0,ny]:tube('Rolled cloth selvage',[vv[j*(nx+1)+i] for i in range(nx+1)],.009,'Cloth',group,5)
 for i in [0,14,28]:tube('Cloth panel stitched seam',[Vector(vv[j*(nx+1)+i])+Vector((0,0,.004)) for j in range(ny+1)],.004,'Rope',group,4)
 return ob
# Six perimeter posts leave the center and all four sides open.
old=before()
for x in [-2.35,0,2.35]:
 for y in [-1.65,1.65]:
  if x==0 and y<0:continue
  stone('Pavilion bedded footing',(x,y,.105),(.22,.21,.14))
  beam('Market hewn upright',(x,y,.14),(x,y,2.39),.18,group='MainFrame')
  lash('Pavilion beam binding',(x,y,2.29),'X',.117,4)
  for s in [-1,1]:
   if abs(x+s*.42)<2.5:beam('Open pavilion knee brace',(x,y,1.89),(x+s*.42,y,2.31),.085,group='MainFrame')
for y in [-1.65,1.65]:
 beam('Long market wall plate',(-2.57,y,2.31),(2.57,y,2.31),.19,.20,group='MainFrame')
 beam('Merchant hanging rail',(-2.39,y,2.04),(2.39,y,2.04),.064,group='MainFrame')
for x in [-2.35,0,2.35]:
 beam('Open market cross tie',(x,-1.81,2.31),(x,1.81,2.31),.14,.17,group='MainFrame')
 for s in [-1,1]:beam('Roof bearer',(x,s*1.81,2.33),(x*.47,0,3.56),.09,.12,group='RoofFrame')
# Two-stage irimoya roof: broad hipped skirt, then a short, readable gabled crown.
# All faces and loose reeds are authored here in final space using the rural materials.
def roof_patch(a,b,c,d,label,rows=9):
 a,b,c,d=map(Vector,(a,b,c,d));normal=(b-a).cross(c-a).normalized()
 if normal.z<0:normal=-normal
 def surface(u,v):
  p=a.lerp(b,u).lerp(c.lerp(d,u),v)
  p+=normal*(.08*math.sin(v*math.pi)*math.sin(u*math.pi))
  p.z+=(1-v)*(.025*math.sin(p.x*4.7+p.y*5.3))
  return p
 nu=44;nv=16;vv=[];uv=[];ff=[]
 for j in range(nv+1):
  for i in range(nu+1):
   u=i/nu;v=j/nv;p=surface(u,v)
   if j==0:p.z+=random.uniform(-.035,.008)
   vv.append(p);uv.append((u*((b-a).length*(1-v)+(d-c).length*v)*1.65,v*3.8))
 for j in range(nv):
  for i in range(nu):k=j*(nu+1)+i;ff.append((k,k+1,k+nu+2,k+nu+1))
 if (vv[1]-vv[0]).cross(vv[nu+1]-vv[0]).z<0:ff=[tuple(reversed(f)) for f in ff]
 ob=mesh(label+' deep thatch',vv,ff,'Thatch',uv,'MarketRoof');sol=ob.modifiers.new('Dense thatch thickness','SOLIDIFY');sol.thickness=.17;sol.offset=-1
 for f in ob.data.polygons:f.use_smooth=True
 # Broad straw courses catch light as overlapped layers, underneath fine reed clumps.
 for row in range(rows):
  low=row/rows;high=min(.999,(row+1.45)/rows);verts=[];tex=[];faces=[];segments=88
  for j,v in enumerate([low,low+(high-low)*.34,high]):
   for i in range(segments+1):
    u=i/segments;vvv=v
    if j==0:vvv=max(0,v+.009*math.sin(i*1.7+row*4)+.004*math.sin(i*4.2))
    p=surface(u,vvv)+normal*([.029,.027,.002][j]+.006*math.sin(i*2.3+row))
    verts.append(p);tex.append((u*(b-a).length*1.65,v*3.8))
  for j in range(2):
   for i in range(segments):k=j*(segments+1)+i;faces.append((k,k+1,k+segments+2,k+segments+1))
  ob=mesh('Broad overlapping straw course',verts,faces,'Thatch',tex,'MarketRoof')
  for f in ob.data.polygons:f.use_smooth=True
 # Detached short stalks run downslope, interrupting the perfect shingle courses.
 for i in range(int((b-a).length*80)):
  u=random.uniform(.005,.995);v=random.uniform(.015,.94);p=surface(u,v)+normal*.047;q=surface(u,min(.995,v+random.uniform(.10,.22)))+normal*.035
  tube('Loose sun-dried roof stalk',[p-Vector((0,0,.035 if v<.1 else 0)),p.lerp(q,.4)+normal*.008,q],random.uniform(.002,.004),'Thatch','MarketReeds',4)
 for i in range(int((b-a).length/.022)):
  u=(i+.5)/int((b-a).length/.022);p=surface(u,0);q=surface(u,random.uniform(.06,.15))
  tube('Thick broken thatch eave',[p-Vector((0,0,random.uniform(.11,.22))),p+normal*.018,q],random.uniform(.006,.010),'Thatch','MarketReeds',5)
 # Rafter ends remain exposed in shadow below the reed fringe.
 for i in range(max(4,int((b-a).length/.29))):
  u=(i+.5)/max(4,int((b-a).length/.29));p=surface(u,0)-Vector((0,0,.20));q=surface(u,.25)-Vector((0,0,.21))
  beam('Dark rough eave rafter',p,q,.055,.075,group='RoofFrame')
# Low hipped skirt stays broad but leaves the crown distinctly legible.
roof_patch((-3.02,-2.28,2.52),(3.02,-2.28,2.52),(-1.52,-.55,3.29),(1.52,-.55,3.29),'Front skirt')
roof_patch((3.02,2.28,2.52),(-3.02,2.28,2.52),(1.52,.55,3.29),(-1.52,.55,3.29),'Rear skirt')
roof_patch((-3.02,2.28,2.52),(-3.02,-2.28,2.52),(-1.52,.55,3.29),(-1.52,-.55,3.29),'West hip')
roof_patch((3.02,-2.28,2.52),(3.02,2.28,2.52),(1.52,-.55,3.29),(1.52,.55,3.29),'East hip')
roof_patch((-1.78,-.81,3.28),(1.78,-.81,3.28),(-1.78,0,4.02),(1.78,0,4.02),'Upper front',6)
roof_patch((1.78,.81,3.28),(-1.78,.81,3.28),(1.78,0,4.02),(-1.78,0,4.02),'Upper rear',6)
for side in [-1,1]:
 x=side*1.69
 for i in range(9):
  y=-.54+i*.135;top=3.95-abs(y)*.83
  beam('Upper gable weathered slat',(x,y,3.23),(x,y,top),.128,.036,group='GableVent',rough=.004)
 for s in [-1,1]:beam('Upper gable verge',(x,s*.80,3.25),(x,0,4.055),.086,.10,group='GableVent')
 beam('Upper gable crossbeam',(x,-.72,3.34),(x,.72,3.34),.085,group='GableVent')
 beam('Gable king stud',(x,0,3.28),(x,0,3.99),.084,group='GableVent')
for y in [-.15,.15]:tube('Ridge timber restraint',[(-1.93,y,4.10),(0,y,4.13),(1.93,y,4.10)],.052,'Timber','Ridge',9)
tube('Bundled straw ridge',[(-1.82,0,4.02),(0,0,4.055),(1.82,0,4.02)],.11,'Thatch','Ridge',10)
for x in [-1.71,-.94,-.16,.64,1.55]:
 tube('Ridge crossed timber',[(x,-.35,4.135),(x,.35,4.135)],.038,'Timber','Ridge',7)
 for y in [-.17,.17]:lash('Ridge rough hemp',(x,y,4.13),'X',.07,3)
collect(old,'Market_01')
# One reusable side stall: four lightly crooked poles and a sagging fabric roof.
old=before()
for x in [-1.05,1.05]:
 for y in [-.70,.70]:
  h=2.34 if y>0 else 2.12
  tube('Side stall round post',[(x,y,.02),(x+.017,y-.013,h)],.048,'Timber','SideStall',8)
  lash('Side stall cloth lashing',(x,y,h-.035),'X',.070,3)
for y,h in [(-.70,2.12),(.70,2.34)]:tube('Side stall light cross pole',[(-1.15,y,h),(1.15,y,h+.015)],.037,'Timber','SideStall',8)
cloth('Side stall hanging cloth',2.27,1.64,2.36,2.13,'SideStall',.16)
collect(old,'MarketStall_Open_01')
old=before()
for x in [-1.32,1.32]:
 tube('Awning upright',[(x,-.77,.03),(x+.02,-.78,2.13)],.046,'Timber','AwningPosts',8)
 lash('Awning rope tie',(x,-.77,2.06),'X',.070,3)
 tube('Awning tie rope',[(x,-.77,2.09),(x,.82,2.40)],.009,'Rope','AwningPosts',5)
tube('Awning goods crosspole',[(-1.36,-.77,2.07),(1.36,-.77,2.07)],.034,'Timber','AwningPosts',7)
collect(old,'MK01_AwningPosts')
old=before();cloth('Long naturally sagging awning',2.72,1.65,2.42,2.13,'CanopyA',.20);collect(old,'MK01_Canopy_A')
old=before();cloth('Short patched cloth canopy',2.16,1.55,2.37,2.10,'CanopyB',.19);collect(old,'MK01_Canopy_B')
for name,w,d,h in [('MK01_Table_A',1.82,.72,.83),('MK01_Table_B',1.12,.58,.63)]:
 old=before()
 for x in [-w*.41,w*.41]:
  for y in [-d*.36,d*.36]:beam('Merchant trestle leg',(x,y,.02),(x*.95,y*.95,h-.06),.085,group=name)
  beam('Trestle end brace',(x,-d*.40,h*.38),(x,d*.40,h*.38),.061,group=name)
 beam('Trestle longitudinal stretcher',(-w*.41,0,.26),(w*.41,0,.26),.074,group=name)
 for j in range(5):beam('Weathered merchant table board',(-w*.5,-d*.4+j*d*.2,h),(w*.5,-d*.4+j*d*.2,h),d*.194,.05,group=name,rough=.004)
 collect(old,name)
old=before()
for x in [0,1,2]:tube('Loose boundary stake',[(x,0,.02),(x+.012,0,1.0+random.uniform(-.06,.05))],.048,'Timber','Fence',7)
for z in [.30,.66,.89]:
 tube('Crooked fence rail',[(-.03,-.035,z),(1,-.045,z-.035),(2.04,-.045,z+.012)],.031,'Timber','Fence',7)
 for x in [0,1,2]:lash('Fence rope joint',(x,-.015,z),'X',.064,2)
collect(old,'MK01_Fence')
# Upright hemp banner with a hand-drawn 市 mark, a plain public-market marker.
old=before()
tube('Market banner post',[(0,0,.03),(.015,0,3.03)],.049,'Timber','Banner',8)
tube('Market banner hanging bar',[(-.09,0,2.97),(.80,0,2.97)],.024,'Timber','Banner',7)
vv=[];uv=[];ff=[];nx=12;ny=24
for j in range(ny+1):
 for i in range(nx+1):
  x=.11+.63*i/nx;z=1.06+1.83*j/ny;yy=.032*math.sin(i*.35+j*.18)+.026*math.sin(j*.35)
  vv.append((x,yy,z));uv.append((i/nx*1.4,j/ny*3.7))
for j in range(ny):
 for i in range(nx):k=j*(nx+1)+i;ff.append((k,k+1,k+nx+2,k+nx+1))
ob=mesh('Unbleached hanging market banner',vv,ff,'Cloth',uv,'Banner');mod=ob.modifiers.new('Banner thickness','SOLIDIFY');mod.thickness=.009
# Black painted strokes modeled as thin ribbon strips conforming to the cloth.
def ink(points,width=.028):
 vertices=[]
 for index,(x,z) in enumerate(points):
  previous=Vector(points[max(0,index-1)]);following=Vector(points[min(len(points)-1,index+1)]);tangent=(following-previous).normalized();cross=Vector((-tangent.y,tangent.x))*width*.5
  yy=.032*math.sin((x-.11)/.63*12*.35+(z-1.06)/1.83*24*.18)+.026*math.sin((z-1.06)/1.83*24*.35)
  vertices.extend([(x-cross.x,yy-.018,z-cross.y),(x+cross.x,yy-.018,z+cross.y)])
 mesh('Hand painted market mark',vertices,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],'Ink',group='Banner')
ink([(.42,2.40),(.46,2.28)],.040)
ink([(.22,2.23),(.42,2.25),(.67,2.22)],.038)
ink([(.44,2.21),(.43,1.69)],.038)
ink([(.27,1.84),(.28,2.06),(.60,2.06),(.60,1.83),(.54,1.84)],.030)
ink([(.435+.28*math.cos(i*math.tau/64),2.045+.45*math.sin(i*math.tau/64)) for i in range(65)],.017)
for z in [2.94,2.05,1.08]:lash('Banner tie',(0,0,z),'X',.065,2)
collect(old,'MK01_Banner')
# Goods use the same timber/rope surfaces and only a few muted market accents.
sys.path.insert(0,str(ART/'Scripts'))
from market_props import build_props
modules.update(build_props(globals()))
# Reuse the farm's low earth apron, gravel and verge to bed the market into the village.
with bpy.data.libraries.load(str(ART.parent/'FarmCompound01/FarmCompound01.blend'),link=False) as (a,b):b.collections=['FC01_GroundApron']
apron=b.collections[0];apron_objects=[]
for ob in list(apron.all_objects):
 if ob.type!='MESH':continue
 if 'Packed earth compound apron' in ob.name:
  bpy.data.objects.remove(ob,do_unlink=True);continue
 for c in list(ob.users_collection):c.objects.unlink(ob)
 src.objects.link(ob);ob.matrix_world.identity();ob.name='Market reused '+ob.name
 for v in ob.data.vertices:v.co.x*=.90;v.co.y*=1.08
 for slot in ob.material_slots:
  if slot.material:
   family=slot.material.name.split('_',1)[-1].split('.')[0]
   if family in mats:slot.material=mats[family]
 apron_objects.append(ob)
bpy.data.collections.remove(apron);modules['MK01_GroundApron']=apron_objects
# Join modules while keeping the pavilion's major construction pieces separate and editable.
for key,obs in list(modules.items()):
 if key=='Market_01':
  buckets={}
  for o in obs:
   category='Roof' if any(m and m.name=='SH01_Thatch' for m in o.data.materials) else 'Stone' if any(m and m.name=='SH01_Stone' for m in o.data.materials) else 'Frame'
   buckets.setdefault(category,[]).append(o)
 else:buckets={key:obs}
 joined=[]
 for category,parts in buckets.items():
  bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:
   ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object
  ob.name=('MK01_MainStall_'+category) if key=='Market_01' else key
  scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  joined.append(ob)
 modules[key]=joined
for module_name,obs in modules.items():
 if module_name=='MK01_GroundApron':continue
 for ob in obs:
  tint=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
  for face in ob.data.polygons:
   family=ob.data.materials[face.material_index].name.split('_',1)[1]
   for li in face.loop_indices:
    p=ob.data.vertices[ob.data.loops[li].vertex_index].co;k=.93+.045*math.sin(p.x*5.1+p.y*4.7+p.z*2.2)+.025*math.sin(p.x*17+p.y*29)
    rgb={'Timber':(.53,.44,.33),'Thatch':(.64,.51,.33),'Stone':(.75,.74,.67),'Rope':(.8,.73,.59)}.get(family,(1,1,1))
    if family in ('Cloth','Pottery','Fish'):
     coarse=.5+.5*surface_noise.noise_vector(p*2.1)[0];medium=.5+.5*surface_noise.noise_vector(p*9.0+Vector((7,2,1)))[1]
     if family=='Cloth':
      k*=.43+.42*coarse+.16*medium;rgb=(1,.92+.05*coarse,.75+.16*coarse)
     elif family=='Pottery':
      k*=.53+.56*coarse+.12*medium;rgb=(1,.80+.19*coarse,.60+.32*coarse)
     else:k*=.69+.25*coarse
    tint.data[li].color=(*(c*k for c in rgb),1)
  ob.data.color_attributes.active_color=tint
# Runtime exports: established FBX settings, local useful pivots, no new pipeline.
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for name,obs in modules.items():
 for ob in obs:ob.modifiers.new('Runtime export triangles','TRIANGULATE')
 fbx(ART/'Exports'/f'{name}.fbx',obs)
 for ob in obs:ob.modifiers.remove(ob.modifiers['Runtime export triangles'])
def place(mesh_name,loc=(0,0,0),yaw=0,scale=(1,1,1),name=None):
 index=len(instances);name=name or mesh_name+'_'+str(index)
 instances.append({'name':name,'mesh':mesh_name,'location':list(loc),'rotation_degrees':yaw,'scale':list(scale)})
 for source in modules[mesh_name]:
  ob=source.copy();ob.data=source.data;layout.objects.link(ob);ob.name=name+' / '+source.name
  ob.location=loc;ob.rotation_euler.z=math.radians(yaw);ob.scale=scale
place('MK01_GroundApron',(0,0,-.012))
place('Market_01',(0,.35,0),name='Main covered market')
# Three reusable smaller stalls flank an open public approach; no perimeter enclosure.
for p,rot,label in [((-4.02,.10,0),90,'West produce stall'),((4.03,.45,0),-90,'East pottery stall'),((2.50,3.52,0),180,'Rear cloth stall')]:
 place('MarketStall_Open_01',p,rot,name=label)
for p,rot in [((-1.65,-2.26,0),-2),((1.65,-2.27,0),2)]:
 place('MK01_AwningPosts',p,rot,scale=(.78,1,1));place('MK01_Canopy_A',p,rot,scale=(.78,1,1))
place('MK01_AwningPosts',(-3.90,2.56,.03),30,scale=(.80,1,1))
place('MK01_Canopy_B',(-3.90,2.56,.03),30)
# Tables leave a 1.1m main aisle and visible trading floor under the roof.
for p,yaw in [((-1.43,-1.03,0),0),((1.42,-1.02,0),0),((-1.28,1.78,0),0),((1.15,1.78,0),0),((-4.10,.12,0),90),((4.05,.43,0),-90),((2.50,3.60,0),180)]:place('MK01_Table_A',p,yaw)
place('MK01_Table_B',(-2.3,-2.76,0),-7);place('MK01_Table_B',(2.50,-2.73,0),8)
for p,rot in [((-5.0,-2.6,0),90),((-5.0,.9,0),90),((5.04,-2.45,0),90),((5.04,1.05,0),90),((-3.2,3.1,0),0),((-5.0,-3.45,0),0),((3.0,-3.46,0),0)]:place('MK01_Fence',p,rot)
place('MK01_Banner',(3.50,-3.14,0),-6)
for p in [(-1.90,-1.0,.86),(-1.26,-1.04,.86),(-4.12,-.33,.86),(-4.10,.28,.86),(-2.30,-2.76,.66)]:place('MK01_BasketProduce',p,random.uniform(-20,20))
for p in [(-.73,-1.04,.86),(-4.13,.79,.86),(-2.52,-1.38,0),(-3.0,-2.70,0)]:place('MK01_BasketEmpty',p,random.uniform(-10,20))
for p in [(1.04,-1.03,.86),(4.05,.78,.86),(4.06,.12,.86),(2.48,-2.73,.66)]:place('MK01_Pottery',p,random.uniform(0,50))
for p in [(2.03,-1.02,.86),(2.88,-1.58,0),(4.12,1.52,0)]:place('MK01_PotteryTall',p,random.uniform(-10,20))
for p in [(-2.13,1.11,0),(-1.91,1.52,0),(2.07,1.16,0),(-3.81,2.30,0),(3.85,2.01,0)]:place('MK01_Crate',p,random.uniform(-12,12))
place('MK01_Crate',(-2.09,1.10,.48),6)
for p in [(1.18,1.8,.86),(-1.45,1.83,.86),(-2.23,2.17,0),(3.67,3.37,0)]:place('MK01_Sacks',p,random.uniform(-15,15))
for p in [(2.25,3.60,.86),(2.87,3.63,.86),(.36,1.8,.86)]:place('MK01_ClothBundle',p,random.uniform(-15,15))
for p in [(-1.65,-3.03,2.04),(1.65,-3.04,2.04),(-2.2,1.95,2.09)]:place('MK01_HangingGoods',p)
(ART/'Exports/assembly.json').write_text(json.dumps({'asset':'Market_01','instances':instances},indent=2)+'\n')
src.hide_render=True;src.hide_viewport=True
# Reuse the existing neutral review ground and daylight, solely for the source image.
bpy.ops.mesh.primitive_plane_add(size=2000);ground=bpy.context.object;ground.name='Review packed earth'
for c in list(ground.users_collection):c.objects.unlink(ground)
studio.objects.link(ground)
m=bpy.data.materials.new('Review packed earth');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.13,.112,.079,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=1;ground.data.materials.append(m);ground.location.z=-.02
world=bpy.data.worlds.new('Rural daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.43,.50,.62,1);world.node_tree.nodes['Background'].inputs[1].default_value=.38
for name,loc,power,size in [('Warm daylight',(-5,-7,10),1100,7),('Sky fill',(7,-3,7),900,8)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('Afternoon sun','SUN');o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.5,-.45,-.5);d.energy=2;d.angle=.10
cd=bpy.data.cameras.new('Market three-quarter');cam=bpy.data.objects.new(cd.name,cd);studio.objects.link(cam);cam.location=(12,-18,5.6);cam.rotation_euler=(Vector((0,.1,1.65))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=51;scene.camera=cam
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
scene['asset_note']='Market_01: exterior public trading area, local-meter modular source and assembly; no interior, physics, simulation or NPCs.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Market01.blend'))
print('MARKET_SAVED',len(modules),'modules',len(instances),'placed pieces',flush=True)
scene.render.filepath=str(OUT/'market-three-quarter.png');bpy.ops.render.render(write_still=True)
print('MARKET_COMPLETE',flush=True)
