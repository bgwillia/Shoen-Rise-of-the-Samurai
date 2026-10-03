import bpy,json,math
from pathlib import Path
D=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/RiverEdge01')
rows=json.loads((D/'bank-contact.json').read_text());verts=[];alpha=[];faces=[]
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
# One fixed six-metre shelf, feathered into the existing bank at its perimeter.
for i,row in enumerate(rows):
 s=-180+i*20;crest=rows[i][-1][2];end=smooth(0,70,i*20)*(1-smooth(530,600,i*20))
 for j,(x,y,h) in enumerate(row):
  t=-560+j*20;d=-t-120
  offset=12*math.sin(i*.37)+7*math.sin(i*.83)
  profile=crest-max(0,d-offset)*.20
  fade=smooth(-560,-490,t)*(1-smooth(-160,-120,t))*end
  z=h+.65+max(0,profile-h)*fade
  verts.append(((x+23600)/100,-(y+6300)/100,(z-650)/100));alpha.append(fade)
for i in range(30):
 for j in range(22):
  a=i*23+j;faces.append((a,a+1,a+24,a+23))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
me=bpy.data.meshes.new('RiverEdge01_ShallowShelf');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('RiverEdge01_ShallowShelf',me);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for p in me.polygons:p.use_smooth=True
uv=me.uv_layers.new(name='UVMap');col=me.color_attributes.new(name='BankEdge',type='FLOAT_COLOR',domain='CORNER')
for li,l in enumerate(me.loops):
 co=me.vertices[l.vertex_index].co;uv.data[li].uv=(co.x/.78,-co.y/.78);col.data[li].color=(1,1,1,alpha[l.vertex_index])
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.wm.save_as_mainfile(filepath=str(D/'RiverEdge01.blend'))
bpy.ops.export_scene.fbx(filepath=str(D/'RiverEdge01_ShallowShelf.fbx'),use_selection=True,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',object_types={'MESH'},bake_anim=False)
