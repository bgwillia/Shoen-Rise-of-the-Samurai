"""Single visual correction: textured gable thatch edges, lower vents, ridge ties."""
from pathlib import Path
import sys, math, random, ast
import bpy, bmesh
from mathutils import Vector
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2];OUT=ROOT/'artifacts/storehouse01'
bpy.ops.wm.open_mainfile(filepath=str(ART/'Storehouse01.blend'))
scene=bpy.context.scene;src=bpy.data.collections['Storehouse_01 • modular exterior'];groups={}
mats={n:bpy.data.materials['RH01_'+n] for n in ['Thatch','Timber','Plaster','Stone','Rope']}
random.seed(1182)
kit_code=(ART.parent/'RuralHouse01/Scripts/model_house.py').read_text()
for node in ast.parse(kit_code).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'mesh','tube','lash'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'ruralhouse-kit','exec'))
for side in [-1,1]:
 normal=Vector((side*1.15,0,2.10)).normalized()
 def surface(v,y):
  p=Vector((side*2.1*(1-v),y,2.71+1.15*v))
  p+=normal*(.115*math.sin(v*math.pi)+.008*math.sin(v*8))
  p.z+=(1-v)*(.035*(abs(p.x)/2.6)**3+.025*(abs(p.y)/2.4)**3+.013*math.sin(p.x*5.3+p.y*3.2))
  return p
 for end in [-1,1]:
  verts=[];uv=[];faces=[];N=100
  for j in range(5):
   for i in range(N+1):
    v=i/N;p=surface(v,end*2.019)-normal*(j*.077)
    p.y+=end*(.009*math.sin(i*2.7)+.01)
    if j==4:p+=normal*random.uniform(-.015,.012)
    verts.append(p);uv.append((j*.11,(1-v)*1.68))
  for j in range(4):
   for i in range(N):q=j*(N+1)+i;faces.append((q,q+1,q+N+2,q+N+1))
  ob=mesh('Bound gable thatch edge',verts,faces,'Thatch',uv,'GableThatch')
  for f in ob.data.polygons:f.use_smooth=True
  for i in range(90):
   v=(i+.4)/90
   for depth in [.045,.125,.205,.272]:
    p=surface(v,end*2.043)-normal*depth
    q=surface(min(1,v+random.uniform(.02,.047)),end*2.045)-normal*depth
    tube('Gable reed ends',[p,q],random.uniform(.003,.006),'Thatch','GableThatch',5)
# Existing vent component moves lower, clear of the thick overhang.
for v in bpy.data.objects['SH01_Window'].data.vertices:v.co.z-=.26
# Actual house ridge geometry is reused; add its omitted separate hemp bindings.
for y in [-1.6,-.9,0,.9,1.6]:
 for x in [-.205,.205]:lash('Ridge hemp fastening',(x,y,4.005),'Y',.084,3)
for name,obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name='SH01_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
components=list(src.objects)
sys.path.insert(0,str(ROOT/'SourceArt/Characters/Samurai/Do01/Scripts'))
from export_do import fbx
for o in components:o.modifiers.new('Export triangulation','TRIANGULATE')
fbx(ART/'Exports/Storehouse_01.fbx',components)
for o in components:o.modifiers.remove(o.modifiers['Export triangulation'])
scene.camera=bpy.data.objects['Three-quarter']
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Storehouse01.blend'))
for name,label in [('Three-quarter','three-quarter'),('Front','front'),('Side','side'),('Rear','rear'),('Roof','roof')]:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(OUT/('storehouse-'+label+'.png'));bpy.ops.render.render(write_still=True)
print('STOREHOUSE_CORRECTION_COMPLETE',flush=True)
