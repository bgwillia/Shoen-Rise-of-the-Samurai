"""Author one finite continuous replacement for the existing segmented ford surface."""
import bpy,json,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');S=R/'SourceArt/Environment/Ground/RiverGravel01'
data=json.loads(Path('/tmp/gravel-joins.json').read_text());segments=data['segments'];ground=data['ground']
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def profile(s):
 t=(s+1000)/100;i=max(0,min(19,int(t)));t=max(0,min(1,t-i));z0=segments[i]['p'][2];z1=segments[i]['q'][2]
 prev=segments[max(0,i-1)]['p'][2];nxt=segments[min(19,i+1)]['q'][2]
 m0=(z1-prev)*.5 if i else z1-z0;m1=(nxt-z0)*.5 if i<19 else z1-z0
 return (2*t**3-3*t*t+1)*z0+(t**3-2*t*t+t)*m0+(-2*t**3+3*t*t)*z1+(t**3-t*t)*m1
verts=[];alphas=[];faces=[]
for i,row in enumerate(ground):
 s=-1080+i*20
 for j,(x,y,h) in enumerate(row):
  side=-440+j*20
  edge=330+18*math.sin(s*.009)+10*math.sin(s*.023+1.1)
  core=1-smooth(190,edge,abs(side));end=1-smooth(960,1080,abs(s));lift=core*end*(1-smooth(620,1010,abs(s)))
  z=h-2.75+(max(h+.25,profile(s))-h+2.75)*lift
  alpha=(1-smooth(edge-75,edge+55,abs(side)))*(1-smooth(960,1080,abs(s)))
  verts.append(((x+23600)/100,-(y+6300)/100,(z-650)/100));alphas.append(alpha)
for i in range(len(ground)-1):
 for j in range(len(ground[0])-1):
  a=i*45+j;faces.append((a,a+1,a+46,a+45))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new('RiverGravel01_FlushApproaches');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('RiverGravel01_FlushApproaches',mesh);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for poly in mesh.polygons:poly.use_smooth=True
# UVs are continuous; shading detail is world-mapped in Unreal.
uv=mesh.uv_layers.new(name='UVMap')
for poly in mesh.polygons:
 for li in poly.loop_indices:
  co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co.x/0.78,-co.y/0.78)
col=mesh.color_attributes.new(name='BankEdge',type='FLOAT_COLOR',domain='CORNER')
for li,loop in enumerate(mesh.loops):col.data[li].color=(1,1,1,alphas[loop.vertex_index])
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(S/'RiverGravel01_FlushApproaches.blend'))
bpy.ops.export_scene.fbx(filepath=str(S/'Exports/RiverGravel01_FlushApproaches.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',object_types={'MESH'},bake_anim=False)
print('Continuous bank authored:',len(verts),'vertices;',len(faces),'quads')
