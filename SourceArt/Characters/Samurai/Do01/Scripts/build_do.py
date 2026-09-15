"""Construct Dō01 only. `source` intentionally rebuilds; export saved edits separately."""
from pathlib import Path
import sys, math, json, hashlib
import bpy
import numpy as np
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[3]
sys.path.insert(0,str(ART/'Scripts'))
import do_geometry as g
from do_textures import make_atlas
from do_skin import strap_weights
KABUTO=ART.parent/'Kabuto01'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1; scene.render.fps=30
for d in ['Textures','Exports','Review/Exports','Review/Captures']:(ART/d).mkdir(parents=True,exist_ok=True)
def collection(name):
    col=bpy.data.collections.new(name); scene.collection.children.link(col); return col
source=collection('DO01 • editable components'); fit=collection('FIT ONLY • preserved mannequin and Kabuto'); runtime=collection('EXPORT ONLY • runtime LODs'); studio=collection('REVIEW • cameras and lights')
MANNY=ROOT/'SourceArt/Characters/Mannequins/Manny'
with bpy.data.libraries.load(str(MANNY/'Manny.blend'),link=False) as (a,b):
    b.objects=['FIT_Manny','root']; b.actions=['A_Idle','A_Walk','A_Run','A_Attack']
for ob in b.objects:fit.objects.link(ob); ob.hide_set(False); ob.hide_render=False
for action in b.actions:action.use_fake_user=True
body=bpy.data.objects['FIT_Manny']; rig=bpy.data.objects['root']
rig.animation_data_clear(); rig.data.pose_position='REST'; scene.frame_set(1); bpy.context.view_layer.update()
for mod in body.modifiers:
    if mod.type=='ARMATURE':mod.object=rig
with bpy.data.libraries.load(str(KABUTO/'Kabuto01.blend'),link=False) as (a,b):b.objects=['SM_Kabuto01_LOD0']
helmet=b.objects[0]; fit.objects.link(helmet); helmet.name='FIT_Kabuto01'
# Approved helmet geometry stays unchanged; fit only its rigid attachment.
helmet.parent=None; helmet.matrix_world=Matrix.Identity(4)
helmet.data.transform(Matrix.Translation((0,-.025,1.598)))
helmet.modifiers.clear(); helmet.vertex_groups.clear()
g.weight(helmet,rig,lambda p:{'head':1.})
body.hide_render=True; helmet.hide_render=True
# Load the same material-family source pixels used by Kabuto; author a separate Do atlas.
im=bpy.data.images.load(str(KABUTO/'Textures/Source/Kabuto01_MaterialSwatches.png'),check_existing=False); im.colorspace_settings.name='Non-Color'
w,h=im.size; px=np.empty(len(im.pixels),np.float32); im.pixels.foreach_get(px); px=px.reshape(h,w,4)[:,:,:3]
px=np.where(px<=.04045,px/12.92,((px+.055)/1.055)**2.4)
surfaces={}
for kind,quad in [(0,px[h//2:,:w//2]),(2,px[h//2:,w//2:]),(3,px[:h//2,:w//2]),(4,px[:h//2,w//2:])]:
    quad=quad[3:-3,3:-3]; yy=np.linspace(0,quad.shape[0]-1,512); xx=np.linspace(0,quad.shape[1]-1,512)
    y0=yy.astype(int); x0=xx.astype(int); y1=np.minimum(y0+1,quad.shape[0]-1); x1=np.minimum(x0+1,quad.shape[1]-1)
    fy=(yy-y0)[:,None,None]; fx=(xx-x0)[None,:,None]
    surfaces[kind]=((1-fy)*((1-fx)*quad[y0[:,None],x0]+fx*quad[y0[:,None],x1])+fy*((1-fx)*quad[y1[:,None],x0]+fx*quad[y1[:,None],x1])).astype(np.float32)
bpy.data.images.remove(im)
detail_image=bpy.data.images.load(str(ART/'Textures/Source/Do01_MaterialSources.png'),check_existing=False)
detail_image.colorspace_settings.name='Non-Color'
dw,dh=detail_image.size; detail_pixels=np.empty(len(detail_image.pixels),np.float32); detail_image.pixels.foreach_get(detail_pixels)
detail_pixels=detail_pixels.reshape(dh,dw,4)[:,:,:3]
detail_pixels=np.where(detail_pixels<=.04045,detail_pixels/12.92,((detail_pixels+.055)/1.055)**2.4)
bpy.data.images.remove(detail_image)
arrays=make_atlas(surfaces,detail_sheet=detail_pixels)
images=[]
for suffix,pixels,linear in zip(['BaseColor','Normal','ORM'],arrays,[False,True,True]):
    encoded=pixels.copy()
    if not linear:
        c=encoded[:,:,:3]; encoded[:,:,:3]=np.where(c<=.0031308,c*12.92,1.055*np.power(c,1/2.4)-.055)
    im=bpy.data.images.new('T_Do01_'+suffix,width=2048,height=2048,alpha=True); im.colorspace_settings.name='Non-Color'; im.pixels.foreach_set(encoded.ravel())
    path=ART/'Textures'/('T_Do01_'+suffix+'.png'); im.filepath_raw=str(path); im.file_format='PNG'; im.save(); bpy.data.images.remove(im)
    im=bpy.data.images.load(str(path),check_existing=False); im.name='T_Do01_'+suffix; im.colorspace_settings.name='Non-Color' if linear else 'sRGB'; im.pack(); images.append(im)
mat=bpy.data.materials.new('M_Do01'); mat.use_nodes=True; nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
for i,im in enumerate(images):
    tex=nodes.new('ShaderNodeTexImage'); tex.image=im; tex.location=(-600,250-i*250)
    if i==0:links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    elif i==1:
        node=nodes.new('ShaderNodeNormalMap'); node.inputs['Strength'].default_value=.65; links.new(tex.outputs['Color'],node.inputs['Color']); links.new(node.outputs['Normal'],bs.inputs['Normal'])
    else:
        sep=nodes.new('ShaderNodeSeparateColor'); links.new(tex.outputs['Color'],sep.inputs['Color']); links.new(sep.outputs['Green'],bs.inputs['Roughness']); links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
g.SOURCE=source; g.MATERIAL=mat
# Cross sections derive from measured body rings. Maintained padding allowance,
# with a slightly flared lower rim and controlled chest taper.
# Measured Manny torso rings and modest padding. Slightly squared sections
# preserve the broad lamellar silhouette without making the shell cylindrical.
RING_Z=[1.,1.08,1.18,1.28,1.34,1.40,1.48]
RING_X=[.184,.177,.181,.198,.201,.188,.182]
RING_FRONT=[.161,.163,.171,.188,.190,.182,.164]
RING_BACK=[.130,.115,.107,.151,.175,.162,.149]
POWER=3.5
def radii(z):
    return float(np.interp(z,RING_Z,RING_X)),float(np.interp(z,RING_Z,(np.array(RING_FRONT)+RING_BACK)/2))
def center_y(z):return float(np.interp(z,RING_Z,(np.array(RING_BACK)-RING_FRONT)/2))
def shell(t,z,offset=0):
    rx,ry=radii(z); sn,cs=math.sin(t),math.cos(t)
    return Vector(((rx+offset)*math.copysign(abs(sn)**(2/POWER),sn),center_y(z)-(ry+offset)*math.copysign(abs(cs)**(2/POWER),cs),z))
def front_y(x,z):
    rx,ry=radii(z);return center_y(z)-ry*max(.001,1-abs(x/rx)**POWER)**(1/POWER)
def row_shell(t,z,offset=0):
    # Upper rows scoop beneath Manny's real armpit volumes.
    side=max(0,(abs(math.sin(t))-.75)/.25)**1.5
    z-=.045*max(0,min(1,(z-1.285)/.071))*side
    return shell(t,z,offset)
def normal(t):
    return Vector((math.sin(t),-math.cos(t),0)).normalized()
parts={n:[] for n in ['Do_Main','Do_Back','Do_Side_L','Do_Side_R','Do_Upper','Do_Straps','Do_Edge','Do_Lacing','Do_Fittings','Do_Lining']}
# Six physical rows, each assembled from overlapping lamella islands. Fine
# holes/stitchwork use the atlas; a subset of actual cords carries relief.
row_step=.055; row_height=.066; base_z=1.015
for row in range(6):
    z0=base_z+row*row_step
    for side,start,end,count,name in [('front',-1.43,1.43,26,'Do_Main'),('back',math.pi-1.43,math.pi+1.43,26,'Do_Back')]:
        for k in range(count):
            ta=start+(end-start)*k/count+.0015; tb=start+(end-start)*(k+1)/count-.0015
            vs=[]; uv=[]; faces=[]
            for j in range(5):
                f=j/4; z=z0+row_height*f
                # Upper portion tucks under the next row; lower edge stands proud.
                inset=.0055*(f**4); crown=.0008*math.sin(f*math.pi)
                for i in range(3):
                    u=i/2; t=ta+(tb-ta)*u; v=row_shell(t,z,.003-inset+crown+.0006*math.sin(u*math.pi)); vs.append(v); uv.append((u,f))
            for j in range(4):
                for i in range(2):a=j*3+i; faces.append((a,a+1,a+4,a+3))
            ob=g.solid(g.mesh('Lamella',vs,faces,[8,9,13,14][(k+row*3)%4],uv),.0023,0); parts[name].append(ob)
            # Every third lamella receives a single geometric pair; other
            # paired fastening detail is relief in the texture, not tiny meshes.
            if k%4==1:
                for u in [.33,.65]:
                    tc=ta+(tb-ta)*u
                    for top,bottom in [(.90,.65),(.45,.20)]:
                        pts=[row_shell(tc,z0+row_height*top,.002),row_shell(tc-.002,z0+row_height*(top*.67+bottom*.33),.005),row_shell(tc+.002,z0+row_height*(top*.33+bottom*.67),.0055),row_shell(tc,z0+row_height*bottom,.003)]
                        parts['Do_Lacing'].append(g.tube('Main fastening cord',g.path(pts,1),.0016,3,6))
        # Rolled lower binding and thin horizontal construction seam.
        for hgt,rad,tile,off in [(z0+.0015,.0032,0,.004),(z0+.0024,.00055,2,.0073),(z0+row_height-.002,.001,0,-.0018)]:
            pts=[row_shell(float(t),hgt,off) for t in np.linspace(start,end,33)]
            parts['Do_Edge'].append(g.tube('Row binding',pts,rad,tile,6))
        # A few larger structural rivets, clearly distinct from painted micro rivets.
        for t in np.linspace(start+.09,end-.09,7):parts['Do_Fittings'].append(g.stud('Row tack',row_shell(float(t),z0+.009,.0047),.0017))
    # Side closures are separate layered leather-backed panels.
    for sign,name in [(1,'Do_Side_L'),(-1,'Do_Side_R')]:
        tc=sign*math.pi/2; vs=[]; uv=[]; fs=[]
        for j in range(3):
            f=j/2
            for i in range(5):
                t=tc-.165+.33*i/4; vs.append(row_shell(t,z0+row_height*f,.001-.005*f**4)); uv.append((i/4,f))
        for j in range(2):
            for i in range(4):a=j*5+i; fs.append((a,a+1,a+6,a+5))
        parts[name].append(g.solid(g.mesh('Side overlap',vs,fs,4,uv),.003,.0007))
        parts['Do_Edge'].append(g.tube('Side hem',[row_shell(tc-.15+.30*i/8,z0+.002,.003) for i in range(9)],.0013,2,6))
# Curved reinforcing bibs with a low central neck edge and cut-away arm openings.
for back in [False,True]:
    vs=[]; uv=[]; fs=[]; offset=math.pi if back else 0
    for j in range(5):
        f=j/4
        for i in range(25):
            u=i/24; halfspan=.68 if back else .87; t=offset+halfspan*(2*u-1)
            lower=1.337+.003*math.cos(t)
            upper=1.463+.021*(abs(2*u-1)**2)+(0.010 if back else 0)
            z=lower+(upper-lower)*f
            vs.append(shell(t,z,.003)); uv.append((u,f))
    for j in range(4):
        for i in range(24):a=j*25+i; fs.append((a,a+1,a+26,a+25))
    parts['Do_Upper'].append(g.solid(g.mesh('Rear reinforcing bib' if back else 'Front reinforcing bib',vs,fs,10,uv),.004,.0011))
    perimeter=[vs[i] for i in range(25)]+[vs[j*25+24] for j in range(1,5)]+[vs[4*25+i] for i in range(23,-1,-1)]+[vs[j*25] for j in range(3,0,-1)]
    parts['Do_Edge'].append(g.tube('Bib bound lacquer edge',perimeter,.0032,0,8,True))
    parts['Do_Edge'].append(g.tube('Bib fine brass rim',[v+normal(math.atan2(v.x,-v.y))*.002 for v in perimeter],.001,2,6,True))
    for i in [2,6,12,18,22]:parts['Do_Fittings'].append(g.stud('Bib rivet',vs[2*25+i]+normal(offset)*.003,.0022))
# Interior liner follows the lower body volume; a high cutout leaves shoulders free.
vs=[]; uv=[]; fs=[]; n=64
# Include the waist profile knots so the liner cannot bridge outside a
# concave row. Extra upper samples follow the curved armpit cutaway.
lining_heights=[1.025,1.08,1.13,1.18,1.235,1.28,1.30,1.32,1.337]
for j,z in enumerate(lining_heights):
    f=(z-1.025)/.312
    for i in range(n):
        t=math.tau*i/n; vs.append(row_shell(t,z,-.005)); uv.append((i/n,f))
for j in range(len(lining_heights)-1):
    for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
parts['Do_Lining'].append(g.solid(g.mesh('Quilted lower lining',vs,fs,12,uv),.004,0))
# Shoulder straps belong to the chest component, with reserved outer sode room.
strap_paths=[]
for sign in [-1,1]:
    center=g.path([(sign*.148,-.153,1.414),(sign*.150,-.134,1.470),(sign*.148,-.089,1.521),(sign*.145,-.034,1.547),(sign*.143,.020,1.554),(sign*.146,.074,1.540),(sign*.149,.118,1.487),(sign*.148,.145,1.425)],4)
    strap_paths.append(center); vs=[]; uv=[]; fs=[]
    for j,p in enumerate(center):
        for i in range(3):
            v=p+Vector(((i/2-.5)*.044,0,0)); vs.append(v); uv.append((i/2,j/(len(center)-1)))
    for j in range(len(center)-1):
        for i in range(2):a=j*3+i; fs.append((a,a+1,a+4,a+3))
    ob=g.solid(g.mesh('Armored shoulder strap',vs,fs,0,uv),.005,.001); parts['Do_Straps'].append(ob)
    for side in [-1,1]:
        edge=[p+Vector((side*.021,0,.001)) for p in center]
        parts['Do_Straps'].append(g.tube('Strap rolled edge',edge,.0022,0,6))
        parts['Do_Straps'].append(g.tube('Strap brass binding',[p+Vector((side*.022,0,.002)) for p in center],.0009,2,5))
    # Visible cord rows follow the strap curvature in small repeated over/under groups.
    for j in range(2,len(center)-3,3):
        p=center[j]; q=center[j+2]; tangent=(q-p).normalized(); norm=Vector((1,0,0)).cross(tangent).normalized()
        for off in [-.009,.009]:
            pts=[p+Vector((off,0,0))+norm*.003,(p+q)/2+Vector((off,0,0))+norm*.006,q+Vector((off,0,0))+norm*.003]
            parts['Do_Straps'].append(g.tube('Strap lacing',pts,.0019,3,6))
# Closure rings and tied red cords: one closure mechanism on each side.
for sign in [-1,1]:
    tc=sign*math.pi/2
    for z in [1.085,1.185,1.285]:
        x=shell(tc,z).x
        for yy in [-.023,.023]:
            pts=[(x+sign*.008,yy+.009*math.sin(t),z+.012*math.cos(t)) for t in np.linspace(0,math.tau,17)[:-1]]
            parts['Do_Fittings'].append(g.tube('Closure ring',pts,.0022,2,7,True))
        knotx=x+sign*.013
        for flip in [-1,1]:
            pts=[(knotx,0,z),(knotx+sign*.004,flip*.021,z+.007),(knotx,flip*.026,z-.004),(knotx,flip*.007,z-.009),(knotx,0,z)]
            parts['Do_Lacing'].append(g.tube('Closure tie loop',g.path(pts,3),.0026,3,7))
            parts['Do_Lacing'].append(g.tube('Closure tie tail',g.path([(knotx,flip*.003,z),(knotx+sign*.002,flip*.008,z-.02),(knotx,flip*.009,z-.042)],3),.0023,3,6))
# Raised metal plaques with recessed botanical engraving supplied by the atlas.
def plaque(name,center,width,height,tile=11,flower=False,conform=False):
    c=Vector(center); vs=[c]; uv=[(.5,.5)]; fs=[]; seg=36
    for i in range(seg):
        t=math.tau*i/seg; scale=(.84+.16*math.cos(3*(t-math.pi/2))) if flower else 1
        vs.append(c+Vector((width*.5*math.cos(t)*scale,0,height*.5*math.sin(t)*scale))); uv.append((.5+.5*math.cos(t)*scale,.5+.5*math.sin(t)*scale))
    if conform:
        for v in vs:
            v.y=front_y(v.x,v.z)-.006
    for i in range(seg):fs.append((0,i+1,(i+1)%seg+1))
    return g.solid(g.mesh(name,vs,fs,tile,uv,smooth=False),.0025,.0006)
def ornament_relief(cx,cz,width,height,petals,plane_y=None):
    def front(x,z,extra=0):
        if plane_y is not None:return plane_y-extra
        return front_y(x,z)-.009-extra
    pts=[]
    for i in range(49):
        t=math.tau*i/48; f=(.84+.16*math.cos(3*(t-math.pi/2))) if petals==3 else 1
        x=cx+width*.49*math.cos(t)*f; z=cz+height*.49*math.sin(t)*f
        pts.append((x,front(x,z),z))
    parts['Do_Fittings'].append(g.tube('Chased raised border',pts[:-1],.0011,2,6,True))
    for i in range(petals):
        t=math.pi/2+math.tau*i/petals; reach=.006 if petals==3 else .0042
        x=cx+math.cos(t)*reach;z=cz+math.sin(t)*reach
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(x,front(x,z,.001),z))
        ob=bpy.context.object;ob.name='Raised floral leaf'
        for col in list(ob.users_collection):col.objects.unlink(ob)
        source.objects.link(ob);ob.data.materials.append(mat)
        for v in ob.data.vertices:
            v.co.x*=.0035 if petals==3 else .0019;v.co.y*=.0018;v.co.z*=.007 if petals==3 else .0048
        ob.rotation_euler.y=math.pi/2-t
        ob.data.uv_layers.active.name='UV0_DoAtlas'
        for loop in ob.data.uv_layers.active.data:loop.uv=g.uvcoord(2,*loop.uv)
        for poly in ob.data.polygons:poly.use_smooth=True
        parts['Do_Fittings'].append(ob)
    parts['Do_Fittings'].append(g.stud('Ornament boss',(cx,front(cx,cz,.002),cz),.0023))

for sign in [-1,1]:
    parts['Do_Fittings'].append(plaque('Trefoil chest fitting',(sign*.105,-.123,1.416),.048,.038,11,True,True))
    parts['Do_Fittings'].append(plaque('Trefoil recessed enamel',(sign*.105,-.123,1.416),.037,.029,0,True,True))
    # Enamel sits ahead of the bronze base; raised border and leaves catch real light.
    recess=parts['Do_Fittings'][-1]
    for v in recess.data.vertices:v.co.y-=.001
    ornament_relief(sign*.105,1.416,.048,.038,3)
    parts['Do_Fittings'].append(plaque('Shoulder mount medallion',(sign*.149,-.150,1.458),.028,.026))
    ornament_relief(sign*.149,1.458,.028,.026,8,plane_y=-.154)
    # Small attachments terminate at the bib, leaving the outer shoulder uncovered.
    for z in [1.410,1.450]:parts['Do_Fittings'].append(g.stud('Mount pin',(sign*.148,front_y(sign*.148,z)-.016,z),.0023))
# Derive row weights from Manny's actual skin, then share each row's weights
# around its rigid plate islands. Four existing spine influences maximum.
torso=[]
for vertex in body.data.vertices:
    weights={body.vertex_groups[w.group].name:w.weight for w in vertex.groups if body.vertex_groups[w.group].name.startswith('spine_')}
    if sum(weights.values())>.7:torso.append((body.matrix_world@vertex.co,weights))
def torso_weight_at(z):
    near=[w for p,w in torso if abs(p.z-z)<.025]
    if not near:near=[w for p,w in sorted(torso,key=lambda item:abs(item[0].z-z))[:48]]
    sums={}
    for weights in near:
        for n,w in weights.items():sums[n]=sums.get(n,0)+w
    sums=dict(sorted(sums.items(),key=lambda item:item[1],reverse=True)[:4]);total=sum(sums.values())
    return {n:w/total for n,w in sums.items() if w/total>.0001}
row_weights=[torso_weight_at(base_z+row_step*i+row_height*.5) for i in range(6)]
def body_weights(p):
    if p.z<1.349:
        index=max(0,min(5,round((p.z-base_z-row_height*.5)/row_step)))
        return row_weights[index]
    return {'spine_05':1.}
components=[]
for name,objects in parts.items():
    if not objects:continue
    ob=g.merge(objects,name)
    sys.path.insert(0,str(KABUTO/'Scripts'))
    import kabuto_export_common as surface_helpers
    surface_helpers.ROUND_GROUP='Do_Round_Surfaces'
    surface_helpers.surface_normals(ob)
    if name=='Do_Straps':
        # Smooth mounting arch; front/back ends remain on the chest bib.
        g.weight(ob,rig,strap_weights)
    elif name in ['Do_Main','Do_Back']:
        adjacency=[[] for v in ob.data.vertices]
        for edge in ob.data.edges:
            a,b=edge.vertices;adjacency[a].append(b);adjacency[b].append(a)
        assigned={};visited=set()
        for vertex in ob.data.vertices:
            if vertex.index in visited:continue
            pending=[vertex.index];island=[];visited.add(vertex.index)
            while pending:
                i=pending.pop();island.append(i)
                for j in adjacency[i]:
                    if j not in visited:visited.add(j);pending.append(j)
            z=sum((ob.matrix_world@ob.data.vertices[i].co).z for i in island)/len(island)
            weights=body_weights(Vector((0,0,z)))
            for i in island:assigned[i]=weights
        g.weight(ob,rig,per_vertex=assigned)
    else:g.weight(ob,rig,body_weights)
    components.append(ob)
# Studio renders expose actual construction; nothing is generated as a beauty image.
def aim(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('Key',(-1.2,-1.7,2.5),125,1.1,(1,.88,.75)),('Fill',(1.4,-.8,2.0),85,1.2,(.77,.87,1)),('Rim',(0,.8,2.3),145,1,(1,.89,.72))]:
    light=bpy.data.lights.new(name,'AREA'); light.energy=power; light.shape='DISK'; light.size=size; light.color=color
    ob=bpy.data.objects.new(name,light); studio.objects.link(ob); ob.location=loc; aim(ob,(0,0,1.30))
world=bpy.data.worlds.new('Do review neutral'); world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.145,.18,1); world.node_tree.nodes['Background'].inputs[1].default_value=.5; scene.world=world
camdata=bpy.data.cameras.new('Do review'); cam=bpy.data.objects.new('Do review',camdata); studio.objects.link(cam); scene.camera=cam; camdata.type='ORTHO'; camdata.ortho_scale=.72
cam.location=(.65,-1.25,1.69); aim(cam,(0,0,1.29))
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True; scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
scene.frame_start=1; scene.frame_end=61; rig.hide_render=True
# Viewport opens on the component itself. Source file retains unchanged fit assets.
g.select([components[0]])
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=.8; area.spaces.active.region_3d.view_location=(0,0,1.26)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Do01.blend'))
manifest={'asset':'Do01','blender_version':bpy.app.version_string,'source_components':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in components},'source_component_objects':len(components),'source_materials':1,'runtime_materials':1,'texture_dimensions':[2048,2048],'skeleton_source':'SourceArt/Characters/Mannequins/Manny/Manny.blend','skeleton_source_sha256':hashlib.sha256((MANNY/'Manny.blend').read_bytes()).hexdigest(),'source_bone_count':len(rig.data.bones),'weighting':'Rigid horizontal rows share weights derived from the measured Manny torso skin. Upper bib and fittings follow spine_05; strap arches blend smoothly between spine_05 and the same-side clavicle. Each lamella island uses a consistent row blend. Maximum four normalized influences.','existing_actions':['A_Idle','A_Walk','A_Run','A_Attack'],'unavailable_actions':['bow draw'],'reference_priority':'Supplied Do01 sheet: 3/4 hero, front, side, rear, construction, decorative microdetails.','source_blend_sha256':hashlib.sha256((ART/'Do01.blend').read_bytes()).hexdigest()}
manifest['review_contract']={'body_component_yaw_degrees':-90,'helmet_offset_from_head_cm':[0,1.8368773,-2.77510097],'helmet_rotation_degrees':[0,0,0],'helmet_scale':[1,1,1],'pose_turn_bone':'spine_04','pose_bend_bone':'spine_04'}
manifest['row_skin_weights']=row_weights
manifest['source_triangles_before_modifiers']=sum(manifest['source_components'].values())
(ART/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--no-render' not in sys.argv:
    scene.render.filepath=str(ART/'Review/Captures/blender-hero.png'); bpy.ops.render.render(write_still=True)
    body.hide_render=False; helmet.hide_render=False; camdata.ortho_scale=1.16; cam.location=(.8,-1.8,1.83); aim(cam,(0,0,1.40))
    scene.render.filepath=str(ART/'Review/Captures/blender-fit.png'); bpy.ops.render.render(write_still=True)
print('DO01_SOURCE_COMPLETE '+json.dumps(manifest))
