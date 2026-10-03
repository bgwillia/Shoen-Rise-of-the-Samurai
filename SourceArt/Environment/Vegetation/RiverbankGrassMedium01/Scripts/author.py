import bpy, math
from mathutils import Vector
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');S=R/'SourceArt/Environment/Vegetation/RiverbankGrassMedium01';O=R/'artifacts/riverbankgrassmedium01'
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.unit_settings.system='METRIC'
asset=bpy.data.collections.new('RiverbankGrass_Medium_01 • editable leaves');s.collection.children.link(asset)
palette=['526B34','496130','59723A','4C6635','617B3E','526D38','7E9B4C','897356']
im=bpy.data.images.new('T_RiverbankGrassMedium01_BaseColor',width=256,height=256,alpha=False);pix=[]
for y in range(256):
 t=y/255
 for x in range(256):
  band=x//32;v=(x%32)/31;c=[int(palette[band][k:k+2],16)/255 for k in (0,2,4)]
  fibre=.009*math.sin(v*90+t*2)+.006*math.sin(v*167);rib=.026*math.exp(-((v-.5)/.055)**2)
  pix.extend([min(1,max(0,k+fibre+rib)) for k in c]+[1])
im.pixels=pix;im.filepath_raw=str(S/'Textures/T_RiverbankGrassMedium01_BaseColor.png');im.file_format='PNG';im.save();im.pack()
mat=bpy.data.materials.new('M_RiverbankGrassMedium01');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9;bs.inputs['Specular IOR Level'].default_value=.16
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
def leaf(name,x,y,az,h,reach,drop,width,band,curve):
 a=math.radians(az);d=Vector((math.cos(a),math.sin(a),0));side=Vector((-d.y,d.x,0));vs=[];uv=[];faces=[];N=16
 # Continuous arch: the leaf spreads throughout its length, not just at the tip.
 root=Vector((x*1.4,y*1.4,-.3));p0=root;p1=root+d*(reach*.20)+Vector((0,0,h*.55));p2=root+d*(reach*.55)+side*curve+Vector((0,0,h*1.16));p3=root+d*reach+side*(curve*.4)+Vector((0,0,h-drop))
 for j in range(N+1):
  t=j/N;q=1-t;center=p0*q**3+p1*(3*q*q*t)+p2*(3*q*t*t)+p3*t**3
  tangent=((p1-p0)*(3*q*q)+(p2-p1)*(6*q*t)+(p3-p2)*(3*t*t)).normalized()
  across=(side*math.cos(t*.7)+d*math.sin(t*.7)).normalized();normal=tangent.cross(across).normalized()
  w=width*.82*(.15+1.35*math.sin(t*math.pi*.93))*(1-t)**.33 if j<N else .005
  for k in range(3):
   p=center+across*((k-1)*w*.5)+normal*(.16*w if k==1 else 0);vs.append((p.x*.95/100,p.y*.95/100,p.z*.91/100));uv.append(((band+.1+.8*k/2)/8,.02+.96*t))
 for j in range(N):
  for k in range(2):faces.append((j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.materials.append(mat);me.uv_layers.new(name='BladeAtlas')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:me.uv_layers.active.data[li].uv=uv[me.loops[li].vertex_index]
 ob=bpy.data.objects.new(name,me);asset.objects.link(ob)
# Authored clusters, offset crown and open southeast notch. Values in centimetres.
pockets=[(-3,-2,210,.84),(-1,-4,265,.91),(2,-3,312,.80),(3.8,0,15,.91),(2.5,2.5,68,1.02),(-.5,3.1,106,.93),(-3.8,1.5,154,.85),(-1.7,-.5,194,1.07),(1,-1,286,1.12),(1.1,1.3,42,1.04),(-1,1.1,126,1.15),(.1,.2,79,1.02)]
profiles=[(-32,57,22,18,1.14),(13,65,18,11,.93),(65,48,23,19,1.21),(130,43,20,18,1.08),(205,62,16,8,.97),(269,53,21,16,1.12),(318,39,22,18,1.14),(162,55,18,17,1.08),(42,47,24,19,1.05)]
for i,(x,y,a,sc) in enumerate(pockets):
 for j,(ang,h,re,dr,w) in enumerate(profiles):
  band=6 if (i,j) in [(1,1),(4,0),(6,3),(9,4),(10,1),(11,6)] else (i+j*3)%6
  if j in (1,4) and (i,j) not in [(1,1),(4,1),(8,4),(10,1),(6,4)]: h*=.76;dr+=5
  if j in (1,4): re=22;dr+=5
  if (i,j)==(10,1): ang+=65;band=2
  leaf('Leaf_%02d_%02d'%(i,j),x+.18*(j%3),y+.12*(j//3),a+ang+[0,13,-19,7][i%4],h*sc,re*(.92 if i%3==0 else 1),dr*sc,w,band,[-1.1,.6,1.7,-.5][(i+j)%4])
for i,(x,y,a,sc) in enumerate(pockets[:8]):
 leaf('CrossingLeaf_%02d'%i,x*.7,y*.7,a+137,49*sc,19,19,1.13,(i+2)%6,-2.3)
# Low green sleeves conceal the six sparse dry remnants.
for i,(x,y,a,sc) in enumerate(pockets):
 for j in range(2):leaf('LowerGreen_%02d_%d'%(i,j),x*.9,y*.9,a+j*115+27,(32+j*7)*sc,17+j*3,13+j*4,.97,(i+j)%6,.6)
for i,(x,y,a) in enumerate([(-2,-1,230),(1,-2,290),(2,0,20),(0,2,85),(-2,1,155),(0,0,195)]):leaf('ConcealedOlder_%02d'%i,x,y,a,11+i%3,6,5,.33,7,.2)
bpy.ops.object.select_all(action='DESELECT')
for ob in asset.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=list(asset.objects)[0]
bpy.ops.export_scene.fbx(filepath=str(S/'Exports/RiverbankGrass_Medium_01.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
rig=bpy.data.collections.new('REVIEW ONLY • excluded from export');s.collection.children.link(rig)
def riglink(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 rig.objects.link(ob)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0031));floor=bpy.context.object;floor.name='ReviewFloor';riglink(floor);fm=bpy.data.materials.new('Warm grey');fm.diffuse_color=(.21,.205,.19,1);floor.data.materials.append(fm)
world=bpy.data.worlds.new('Soft overcast');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.75,.82,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55
for name,loc,energy,size in [('Softbox',(1,-1,2),110,2),('Fill',(-1,.7,1.3),65,1.5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=energy;ob.data.size=size;ob.rotation_euler=(Vector((0,0,.3))-ob.location).to_track_quat('-Z','Y').to_euler();riglink(ob)
bpy.ops.object.camera_add();cam=bpy.context.object;riglink(cam);s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.80;cam.data.clip_start=.001
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
for name,loc in [('01-three-quarter',(1,-1.6,.75)),('02-side',(1.8,0,.38))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,.30))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
for ob in bpy.context.selected_objects:ob.select_set(False)
for ob in asset.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=list(asset.objects)[0]
bpy.ops.wm.save_as_mainfile(filepath=str(S/'RiverbankGrassMedium01.blend'))
vv=[v.co for ob in asset.objects for v in ob.data.vertices];print('BOUNDS_CM',[(min(v[k] for v in vv)*100,max(v[k] for v in vv)*100) for k in range(3)])
