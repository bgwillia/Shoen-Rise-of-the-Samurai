"""Kabuto01 only. Run in Blender 5.1 with --background --factory-startup.

Metres; +X left, -Y front, +Z up. Existing original fit body is copied unchanged.
The saved .blend is authoritative: rebuilding intentionally replaces Kabuto01.
"""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

ART = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ART / 'Scripts'))
from kabuto_export_common import export_runtime, select, triangles
REPO = ART.parents[3]
SOURCE_BODY = ART.parent/'Prototype01/Samurai01.blend'
for d in ['Textures', 'Exports', 'Review/Exports', 'Review/Captures']:
    (ART/d).mkdir(parents=True, exist_ok=True)
PIVOT = Vector((0, 0, 1.57))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene.render.fps = 30
def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
source=collection('KABUTO01 • editable components')
fit=collection('FIT ONLY • unchanged existing male body and rig')
runtime=collection('EXPORT ONLY • evaluated helmet LODs')
studio=collection('REVIEW • cameras and lights')

# Append the actual project body and rig, never remodel anatomy from the sheet.
# On another checkout the embedded fit snapshot in the previous Kabuto01.blend
# can replace the untracked legacy source dependency.
body_file=SOURCE_BODY if SOURCE_BODY.exists() else ART/'Kabuto01.blend'
with bpy.data.libraries.load(str(body_file), link=False) as (a,b):
    names=['SK_Body','RIG_Samurai01'] if SOURCE_BODY.exists() else ['FIT_MaleBody','FIT_Rig']
    b.objects=[n for n in names if n in a.objects]
    b.actions=[n for n in ['A_Neutral','A_Idle','A_Walk'] if n in a.actions]
for action in b.actions:
    action.use_fake_user=True
for ob in b.objects:
    fit.objects.link(ob); ob.hide_set(False); ob.hide_render=False
body=next(ob for ob in b.objects if ob.type=='MESH')
rig=next(ob for ob in b.objects if ob.type=='ARMATURE')
body.name='FIT_MaleBody'; rig.name='FIT_Rig'; body.parent=rig
for mod in body.modifiers:
    if mod.type=='ARMATURE': mod.object=rig
rig.animation_data_create(); rig.animation_data.action=bpy.data.actions['A_Neutral']
rig.hide_set(False); scene.frame_set(1)
headgroup=body.vertex_groups['head'].index
headverts=[v.co.copy() for v in body.data.vertices if any(g.group==headgroup and g.weight>.5 for g in v.groups)]
fit_bounds=[[min(v[i] for v in headverts) for i in range(3)],[max(v[i] for v in headverts) for i in range(3)]]
assert abs(rig.data.bones['head'].head_local.z-PIVOT.z)<1e-5
gray=bpy.data.materials.new('M_FitMannequin_ReviewOnly'); gray.use_nodes=True
bs=gray.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.24,.27,.29,1); bs.inputs['Roughness'].default_value=.72
body.data.materials.clear(); body.data.materials.append(gray)

# One 2K atlas with material-specific wear and detailed, repeated lacing.
from kabuto_textures import make_atlas
N=2048
swatch_path=ART/'Textures/Source/Kabuto01_MaterialSwatches.png'
swatch_image=bpy.data.images.load(str(swatch_path),check_existing=False)
swatch_image.colorspace_settings.name='Non-Color'
swatch_width,swatch_height=swatch_image.size
swatch_pixels=np.empty(len(swatch_image.pixels),np.float32)
swatch_image.pixels.foreach_get(swatch_pixels)
swatch_pixels=swatch_pixels.reshape(swatch_height,swatch_width,4)[:,:,:3]
swatch_pixels=np.where(swatch_pixels<=.04045,swatch_pixels/12.92,((swatch_pixels+.055)/1.055)**2.4)
surfaces={}
for kind,quad in [(0,swatch_pixels[swatch_height//2:,:swatch_width//2]),
                  (2,swatch_pixels[swatch_height//2:,swatch_width//2:]),
                  (3,swatch_pixels[:swatch_height//2,:swatch_width//2]),
                  (4,swatch_pixels[:swatch_height//2,swatch_width//2:])]:
    quad=quad[3:-3,3:-3]
    sy=np.linspace(0,quad.shape[0]-1,512); sx=np.linspace(0,quad.shape[1]-1,512)
    y0=sy.astype(int); x0=sx.astype(int); y1=np.minimum(y0+1,quad.shape[0]-1); x1=np.minimum(x0+1,quad.shape[1]-1)
    fy=(sy-y0)[:,None,None]; fx=(sx-x0)[None,:,None]
    surfaces[kind]=((1-fy)*((1-fx)*quad[y0[:,None],x0]+fx*quad[y0[:,None],x1])+
                    fy*((1-fx)*quad[y1[:,None],x0]+fx*quad[y1[:,None],x1])).astype(np.float32)
bpy.data.images.remove(swatch_image)
base, normal, orm = make_atlas(surfaces)
def save_image(name,pixels,linear=False):
    im=bpy.data.images.new(name,width=N,height=N,alpha=True)
    # Byte images accept encoded channel values. Material colors above are
    # linear reflectance, so encode them explicitly before writing sRGB PNGs.
    encoded=pixels.copy()
    if not linear:
        c=encoded[:,:,:3]
        encoded[:,:,:3]=np.where(c<=.0031308,c*12.92,1.055*np.power(c,1/2.4)-.055)
    im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(encoded.ravel()); path=ART/'Textures'/(name+'.png')
    im.filepath_raw=str(path); im.file_format='PNG'; im.save()
    bpy.data.images.remove(im)
    im=bpy.data.images.load(str(path),check_existing=False); im.name=name
    im.colorspace_settings.name='Non-Color' if linear else 'sRGB'
    im.pack(); return im
images=[save_image('T_Kabuto01_BaseColor',base),save_image('T_Kabuto01_Normal',normal,True),save_image('T_Kabuto01_ORM',orm,True)]
mat=bpy.data.materials.new('M_Kabuto01'); mat.use_nodes=True
nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
for i,im in enumerate(images):
    tex=nodes.new('ShaderNodeTexImage'); tex.image=im; tex.location=(-600,200-i*300)
    if i==0: links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    elif i==1:
        n=nodes.new('ShaderNodeNormalMap'); n.inputs['Strength'].default_value=.65
        links.new(tex.outputs['Color'],n.inputs['Color']); links.new(n.outputs['Normal'],bs.inputs['Normal'])
    else:
        s=nodes.new('ShaderNodeSeparateColor'); links.new(tex.outputs['Color'],s.inputs['Color'])
        links.new(s.outputs['Green'],bs.inputs['Roughness']); links.new(s.outputs['Blue'],bs.inputs['Metallic'])

def uvcoord(tile,u,v): return ((tile%4+.025+.95*u)/4,(tile//4+.025+.95*v)/4)
def mesh(name,verts,faces,tile=0,uvs=None,smooth=True,col=source):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); col.objects.link(ob); data.materials.append(mat)
    layer=data.uv_layers.new(name='UV0_ArmorAtlas')
    for p in data.polygons:
        p.use_smooth=smooth
        for li,vi in zip(p.loop_indices,p.vertices):
            co=uvs[vi] if uvs else ((verts[vi][0]+.2)/.4,(verts[vi][2]-1.48)/.45)
            layer.data[li].uv=uvcoord(tile,*co)
    bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    return ob
def solid(ob,thickness=.0025,bevel=.0007):
    m=ob.modifiers.new('Plate thickness • editable','SOLIDIFY'); m.thickness=thickness; m.offset=-1
    if bevel:
        m=ob.modifiers.new('Soft maintained edges','BEVEL'); m.width=bevel; m.segments=3; m.limit_method='ANGLE'; m.angle_limit=.52
    return ob
def tube(name,points,r,tile=2,sides=6,closed=False,col=source):
    vs=[]; fs=[]; uv=[]; pts=[Vector(p) for p in points]; count=len(pts)
    lengths=[0.]
    for p,q in zip(pts,pts[1:]): lengths.append(lengths[-1]+(q-p).length)
    for i,p in enumerate(pts):
        tangent=(pts[(i+1)%count]-pts[(i-1)%count]) if closed else pts[min(i+1,count-1)]-pts[max(i-1,0)]
        tangent.normalize(); ref=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        a=tangent.cross(ref).normalized(); b=tangent.cross(a).normalized()
        for j in range(sides):
            angle=j*math.tau/sides
            radius=r
            q=p+radius*(a*math.cos(angle)+b*math.sin(angle)); vs.append(q); uv.append((j/sides,lengths[i]/max(.00001,lengths[-1])))
    for i in range(count if closed else count-1):
        ni=(i+1)%count
        for j in range(sides): fs.append((i*sides+j,i*sides+(j+1)%sides,ni*sides+(j+1)%sides,ni*sides+j))
    if not closed: fs.extend([tuple(reversed(range(sides))),tuple((count-1)*sides+j for j in range(sides))])
    ob=mesh(name,vs,fs,tile,uv,col=col)
    group=ob.vertex_groups.new(name='Kabuto_Runtime_Round_Surfaces')
    group.add(list(range(len(vs))),1.,'REPLACE')
    # Keep the longitudinal texture seam local to the closing polygon.
    layer=ob.data.uv_layers.active.data
    side_faces=(count if closed else count-1)*sides
    for face in ob.data.polygons:
        if face.index<side_faces and face.index%sides==sides-1:
            for li,vi in zip(face.loop_indices,face.vertices):
                if vi%sides==0:
                    layer[li].uv=uvcoord(tile,1,lengths[vi//sides]/max(.00001,lengths[-1]))
    return ob
def ellipsoid(name,p,r,tile=2,seg=12,rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=p)
    ob=bpy.context.object; ob.name=name
    for c in list(ob.users_collection): c.objects.unlink(ob)
    source.objects.link(ob)
    for vert in ob.data.vertices:
        vert.co.x*=r[0]; vert.co.y*=r[1]; vert.co.z*=r[2]
    ob.data.materials.append(mat)
    ob.data.uv_layers.active.name='UV0_ArmorAtlas'
    for l in ob.data.uv_layers.active.data: l.uv=uvcoord(tile,*l.uv)
    for f in ob.data.polygons: f.use_smooth=True
    return ob
def merge(obs,name):
    # Joins details inside one logical component, preserving seven modular parts.
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True); bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active=obs[0]; bpy.ops.object.join(); ob=bpy.context.object; ob.name=name
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index=0
    return ob

def bound_edge(name, points, normal, width=.003, depth=.0012, tile=2, closed=False):
    """A bevelled metal binding with a visible face, rather than a wire outline."""
    pts=[Vector(p) for p in points]; normal=Vector(normal).normalized()
    vs=[]; fs=[]; uv=[]; center=sum(pts,Vector())/len(pts)
    for i,p in enumerate(pts):
        tangent=(pts[(i+1)%len(pts)]-pts[(i-1)%len(pts)]) if closed else pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]
        inward=normal.cross(tangent).normalized()
        if inward.dot(center-p)<0: inward=-inward
        for fraction,height in [(0,0),(.15,depth),(1,depth*.7),(1,-depth),(.15,-depth),(0,-depth*.5)]:
            vs.append(p+inward*width*fraction+normal*height)
            uv.append((i/max(1,len(pts)-1),fraction))
    for i in range(len(pts) if closed else len(pts)-1):
        n=(i+1)%len(pts)
        for j in range(6): fs.append((i*6+j,i*6+(j+1)%6,n*6+(j+1)%6,n*6+j))
    if not closed: fs += [tuple(reversed(range(6))),tuple((len(pts)-1)*6+j for j in range(6))]
    return mesh(name,vs,fs,tile,uv)

# Smooth 24-plate bowl, actual open crown aperture and inward metal thickness.
vs=[]; fs=[]; uv=[]; seg=120; rings=20
for j in range(rings+1):
    a=.075+(math.pi/2-.075)*j/rings
    for i in range(seg):
        t=math.tau*i/seg; ridge=.0013*(.5+.5*math.cos(t*24))
        vs.append(((.106+ridge)*math.sin(a)*math.sin(t),.005-(.115+ridge)*math.sin(a)*math.cos(t),1.694+.119*math.cos(a)))
        uv.append((i/seg,1-j/rings))
for j in range(rings):
    for i in range(seg): fs.append((j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i))
hachi=solid(mesh('Hachi',vs,fs,0,uv),.0028,.00045)
details=[]
for i in range(24):
    t=math.tau*i/24
    pts=[]
    for j in range(12):
        a=.12+(math.pi/2-.12)*j/11
        pts.append((.1082*math.sin(a)*math.sin(t),.005-.1172*math.sin(a)*math.cos(t),1.694+.1193*math.cos(a)))
    details.append(tube('Plate rib',pts,.0009,0,6))
    for a in [.43,.72,1.00,1.30,1.49]:
        radius=.002 if a>.5 else .0015
        details.append(ellipsoid('Bowl rivet',(.1085*math.sin(a)*math.sin(t),.005-.1175*math.sin(a)*math.cos(t),1.694+.120*math.cos(a)),(radius,radius,radius),2 if i%3==0 else 0,10,5))
for z,rx,ry,r in [(1.694,.1075,.1165,.0018),(1.712,.1063,.1153,.0012)]:
    details.append(tube('Bowl band',[(rx*math.sin(t),.005-ry*math.cos(t),z) for t in np.linspace(0,math.tau,97)[:-1]],r,2,6,True))
for rad,z,r in [(.010,1.812,.0023),(.015,1.809,.0015),(.007,1.815,.0011)]:
    details.append(tube('Tehen fitting',[(rad*math.sin(t),.005+rad*math.cos(t),z) for t in np.linspace(0,math.tau,33)[:-1]],r,2,6,True))
bowl_details=merge(details,'Hachi_Fittings')

# Swept brow: eye line 167cm stays below the brim at 168.8cm.
vs=[]; uv=[]; fs=[]; n=40
for row in range(3):
    for i in range(n+1):
        t=-1.06+2.12*i/n; f=row/2
        rx=.106+f*.022; ry=.116+f*.036
        vs.append((rx*math.sin(t),.005-ry*math.cos(t),1.695-.007*f+.012*abs(math.sin(t))*f)); uv.append((i/n,f))
for j in range(2):
    for i in range(n): a=j*(n+1)+i; fs.append((a,a+1,a+n+2,a+n+1))
mabisashi=solid(mesh('Mabisashi',vs,fs,0,uv),.003,.0006)
brow_parts=[bound_edge('Visor bound lip',[vs[2*(n+1)+i] for i in range(n+1)],(0,-.3,1),.0035,.0013)]
for i in [3,8,14,20,26,32,37]:
    x,y,z=vs[2*(n+1)+i]
    brow_parts.append(ellipsoid('Visor rivet',(x,y+.004,z+.0014),(.0015,.0015,.0012),2,10,5))
browedge=merge(brow_parts,'Mabisashi_Edge')

# Five separate overlapped lames; recessed upper edges make the shadow gaps real.
def lame_point(row,t,f):
    top=1.697-row*.028; rx=.110+row*.0105; ry=.121+row*.012
    inset=-.004*(1-f)
    return Vector(((rx+.014*f+inset)*math.sin(t),.006-(ry+.016*f+inset)*math.cos(t),top-.041*f-.004*math.sin(t)**2))
rows=[]; edges=[]; laces=[]
for row in range(5):
    vs=[]; fs=[]; uv=[]; count=72
    fractions=[0,.15,.55,.88,1]
    for f in fractions:
        for i in range(count+1):
            t=.90+(math.tau-1.80)*i/count
            vs.append(lame_point(row,t,f)); uv.append((i/count,1-f))
    for j in range(len(fractions)-1):
        for i in range(count): a=j*(count+1)+i; fs.append((a,a+1,a+count+2,a+count+1))
    ob=solid(mesh('Shikoro row '+str(row+1),vs,fs,1,uv),.0028,.00065)
    # Six copies of a high-resolution three-pair lace panel around each plate.
    # Shared geometric vertices retain separate UV values at panel seams.
    layer=ob.data.uv_layers.active.data
    for face in ob.data.polygons:
        i=face.index%count; panel=i//12
        for li,vi in zip(face.loop_indices,face.vertices):
            col=vi%(count+1); j=vi//(count+1)
            layer[li].uv=uvcoord(1,(col-panel*12)/12,1-fractions[j])
    rows.append(ob)
    rolled=[lame_point(row,.90+(math.tau-1.80)*i/count,1) for i in range(count+1)]
    edges.append(tube('Lacquered rolled lower lip',rolled,.0016,0,8))
    bandvs=[]; banduv=[]; bandfs=[]
    for f in [.925,1]:
        for i in range(count+1):
            t=.9+(math.tau-1.8)*i/count
            bandvs.append(lame_point(row,t,f)+Vector((math.sin(t),-math.cos(t),0))*.00065)
            banduv.append((i/count,0 if f<1 else 1))
    for i in range(count): bandfs.append((i,i+1,i+count+2,i+count+1))
    edges.append(solid(mesh('Lame burnished binding',bandvs,bandfs,2,banduv),.0008,.00025))
    for t in [.9,math.tau-.9]:
        edges.append(tube('Lame side return',[lame_point(row,t,f) for f in fractions],.0017,0,8))
    # Major fastenings have simplified volume; the other lacing and all fibers
    # remain in the repeating normal/color panel.
    for cell in range(6):
        for offset in [-.043,.043]:
            u=(cell+.5+offset)/6; t=.9+(math.tau-1.8)*u
            pts=[]
            for index,f in enumerate([.27,.32,.42,.57,.68,.75]):
                lift=.0012+.002*math.sin(math.pi*index/5)
                pts.append(lame_point(row,t,f)+Vector((math.sin(t),-math.cos(t),0))*lift)
            laces.append(tube('Major paired odoshi fastening',pts,.00165,3,8))
shikoro=merge(rows+edges+laces,'Shikoro')

# Fukigaeshi sweep back from the shikoro ends and turn outward toward the viewer.
turnbacks=[]
for side,label in [(1,'L'),(-1,'R')]:
    vs=[]; uv=[]; fs=[]; nx=8; nz=6
    for j in range(nz+1):
        v=j/nz
        for i in range(nx+1):
            u=i/nx
            vs.append((side*(.099+.060*u+.008*v),-.062-.024*math.sin(u*math.pi*.8)-.006*v,1.665+.065*v+.026*u))
            uv.append((u,v))
    for j in range(nz):
        for i in range(nx): a=j*(nx+1)+i; fs.append((a,a+1,a+nx+2,a+nx+1))
    ob=solid(mesh('Fukigaeshi_'+label,vs,fs,5,uv),.003,.001)
    border=[vs[i] for i in range(nx+1)]+[vs[j*(nx+1)+nx] for j in range(1,nz+1)]+[vs[nz*(nx+1)+i] for i in range(nx-1,-1,-1)]+[vs[j*(nx+1)] for j in range(nz-1,0,-1)]
    trim=bound_edge('Turnback bound edge',[(x,y-.0018,z) for x,y,z in border],(0,-1,0),.0032,.0011,2,True)
    ties=[]
    def panel_point(u,v):
        return Vector((side*(.099+.060*u+.008*v),-.062-.024*math.sin(u*math.pi*.8)-.006*v-.0025,1.665+.065*v+.026*u))
    for center_v in [.26,.50,.74]:
        for offset in [-.027,.027]:
            points=[panel_point(.78+offset+.038*math.sin(t),center_v+.061*math.cos(t)) for t in np.linspace(0,math.tau,21)[:-1]]
            ties.append(tube('Turnback silk fastening',points,.0017,3,8,True))
    turnbacks.append(merge([ob,trim]+ties,'Fukigaeshi_'+label))

# Crescent plate, shaped with two continuously curving tapered horns.
def bezier(a,b,c,d,n=12):
    return [tuple((1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t*t*np.array(c)+t**3*np.array(d)) for t in np.linspace(0,1,n,endpoint=False)]
right=bezier((0,1.723),(.058,1.717),(.125,1.758),(.119,1.889))
right+=bezier((.119,1.889),(.119,1.903),(.116,1.914),(.114,1.912),6)
right+=bezier((.114,1.912),(.106,1.849),(.088,1.791),(.027,1.765))
right+=bezier((.027,1.765),(.018,1.760),(.006,1.759),(0,1.759),5)+[(0,1.759)]
outline=right+[(-x,z) for x,z in reversed(right[1:-1])]
verts=[(x,-.128-.014*(z-1.72)/.2,z) for x,z in outline]
maedate=solid(mesh('Maedate',verts,[tuple(range(len(verts)))],2,smooth=False),.004,.0013)
crestpieces=[maedate]
# Bent mounting shoe bridges the bowl and back of the crescent. Its rear
# saddle bears on the iron shell; the ornament no longer floats in side view.
mount_profile=[(-.1025,1.729),(-.1085,1.740),(-.1265,1.740)]
mount_vertices=[(x,y,z) for x in [-.012,.012] for y,z in mount_profile]
mount_faces=[(0,1,4,3),(1,2,5,4)]
crestpieces.append(solid(mesh('Crest mounting shoe',mount_vertices,mount_faces,2,smooth=False),.0035,.0006))
for x in [-.008,.008]:
    crestpieces.append(ellipsoid('Mount saddle bolt',(x,-.1053,1.734),(.0018,.0014,.0018),2,10,5))
# Embossed rosette: real rounded petals, a recessed field and burnished bezel.
zc=1.766; rc=.030
vs=[(0,-.148,zc)]+[(rc*math.sin(t),-.146,zc+rc*math.cos(t)) for t in np.linspace(0,math.tau,49)[:-1]]
uv=[(.5,.5)]+[(.5+.48*math.sin(t),.5+.48*math.cos(t)) for t in np.linspace(0,math.tau,49)[:-1]]
disk=solid(mesh('Medallion',vs,[(0,i+1,(i+1)%48+1) for i in range(48)],6,uv),.004,.0007); crestpieces.append(disk)
crestpieces.append(tube('Medallion rim',[(rc*math.sin(t),-.148,zc+rc*math.cos(t)) for t in np.linspace(0,math.tau,65)[:-1]],.0018,2,10,True))
crestpieces.append(tube('Inner recessed bezel',[(.0265*math.sin(t),-.1485,zc+.0265*math.cos(t)) for t in np.linspace(0,math.tau,65)[:-1]],.0007,0,8,True))
for i in range(8):
    t=math.tau*i/8
    petal=ellipsoid('Embossed chrysanthemum petal',(.0132*math.sin(t),-.1485,zc+.0132*math.cos(t)),(.0053,.0018,.0105),2,16,8)
    petal.rotation_euler.y=t
    crestpieces.append(petal)
    vein=[(.0065*math.sin(t),-.1500,zc+.0065*math.cos(t)),(.012*math.sin(t),-.15045,zc+.012*math.cos(t)),(.0195*math.sin(t),-.1497,zc+.0195*math.cos(t))]
    crestpieces.append(tube('Petal chased center',vein,.00032,6,6))
crestpieces.append(ellipsoid('Rosette center boss',(0,-.1505,zc),(.0044,.0021,.0044),2,20,10))
for side in [-1,1]: crestpieces.append(ellipsoid('Crest mounting rivet',(side*.040,-.136,1.739),(.003,.002,.003),2,10,5))
maedate=merge(crestpieces,'Maedate')
maedate['variant_role']='Replace this crest independently in source; runtime master is combined for batching.'

# Padded annulus, open below and at the crown. Padding sits outside skull envelope.
vs=[]; uv=[]; fs=[]; n=64
for j in range(4):
    z=1.690+j*.019; factor=[1,1,.97,.87][j]
    for i in range(n):
        t=math.tau*i/n
        vs.append((.097*factor*math.sin(t),.006-.102*factor*math.cos(t),z)); uv.append((i/n,j/3))
for j in range(3):
    for i in range(n): fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
uchiwa=solid(mesh('Uchiwa',vs,fs,7,uv),.006,.0018)
rim=tube('Padding rolled rim',[(.095*math.sin(t),.006-.100*math.cos(t),1.691) for t in np.linspace(0,math.tau,65)[:-1]],.004,4,8,True)

# One simplified pair of chin cords and a tied knot; fibers live in the atlas.
cords=[]
def smooth_path(points,steps=5):
    p=[Vector(points[0])]+[Vector(q) for q in points]+[Vector(points[-1])]; result=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for t in np.linspace(0,1,steps,endpoint=False):
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return result+[Vector(points[-1])]
for s in [-1,1]:
    points=[(s*.098,-.048,1.674),(s*.086,-.062,1.625),(s*.063,-.076,1.58),(s*.03,-.080,1.542),(0,-.080,1.532)]
    cords.append(tube('Main chin cord',smooth_path(points),.004,3,8))
    points=[(0,-.083,1.531),(s*.018,-.088,1.537),(s*.035,-.085,1.539),(s*.029,-.086,1.525),(s*.009,-.087,1.525),(0,-.083,1.531)]
    cords.append(tube('Knot loop',smooth_path(points),.0037,3,8))
    cords.append(tube('Knot tail',smooth_path([(s*.004,-.082,1.53),(s*.008,-.085,1.506),(s*.011,-.079,1.483)]),.0035,3,8))
# An overlapping central tie gives the knot a readable over/under structure.
for flip in [-1,1]:
    points=[]
    for t in np.linspace(0,math.tau,49)[:-1]:
        points.append((.008*math.sin(t),-.089-.0055*math.cos(t),1.531+flip*.006*math.sin(t)+.003*math.cos(t)))
    cords.append(tube('Interwoven knot core',points,.0035,3,10,True))
for offset in [-.003,.003]:
    cords.append(tube('Knot wrap',[(.009*math.sin(t),-.089-.0075*math.cos(t),1.531+offset+.002*math.sin(t)) for t in np.linspace(0,math.tau,25)[:-1]],.002,3,6,True))
shinhimo=merge(cords,'ShinHimo')

components=[hachi,bowl_details,mabisashi,browedge,shikoro,*turnbacks,maedate,uchiwa,rim,shinhimo]
for ob in components:
    # Consistent head attachment pivots with unit transforms; source remains fitted.
    world=ob.matrix_world.copy(); ob.data.transform(world); ob.matrix_world=Matrix.Identity(4)
    ob.data.transform(Matrix.Translation(-PIVOT)); ob.location=PIVOT
    ob['attachment_bone']='head'; ob['units']='metres'; ob['asset']='Kabuto01'

lods, evaluated_source_triangles = export_runtime(components, runtime, ART, PIVOT, body, rig)
helmet = lods[0]

report={'asset':'Kabuto01','blender_version':bpy.app.version_string,'source_components':{o.name:triangles(o) for o in components},'source_triangles_before_modifiers':sum(triangles(o) for o in components),'evaluated_source_and_export_triangles':triangles(helmet),'runtime_lod_triangles':[triangles(o) for o in lods],'runtime_materials':1,'source_materials':1,'surface_classes':['lacquered iron','aged brass','dark red cord','leather padding'],'source_component_objects':len(components),'head_bounds_metres':fit_bounds,'head_pivot_metres':list(PIVOT),'source_fit_file':str(SOURCE_BODY.relative_to(REPO)),'source_fit_sha256':hashlib.sha256(body_file.read_bytes()).hexdigest(),'fit_body_geometry_unchanged':True,'helmet_bounds_head_relative_metres':[[min(v.co[i] for v in helmet.data.vertices) for i in range(3)],[max(v.co[i] for v in helmet.data.vertices) for i in range(3)]],'texture_dimensions':[2048,2048],'fbx_import':{'convert_scene':False,'convert_scene_unit':True,'source_to_unreal':[100,-100,100],'component_yaw':-90},'reference_priority':'3D sheet hero silhouette, crescent and red cord; turnaround bowl/neck construction. Dimensions in generated sheets are approximate.'}
report.pop('evaluated_source_and_export_triangles')
report['evaluated_source_triangles']=evaluated_source_triangles
report['exported_triangles']=triangles(helmet)
(ART/'asset-manifest.json').write_text(json.dumps(report,indent=2)+'\n')

def aim(ob,p): ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,energy,size,color in [('Key',(-1.2,-1.6,2.8),95,1.3,(1,.86,.71)),('Fill',(1.4,-.9,2.2),65,1.1,(.75,.84,1)),('Rim',(0,1,2.5),125,1,(1,.90,.74))]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size; data.color=color
    ob=bpy.data.objects.new(name,data); studio.objects.link(ob); ob.location=loc; aim(ob,(0,0,1.7))
world=bpy.data.worlds.new('Review neutral'); world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.17,.20,1); world.node_tree.nodes['Background'].inputs[1].default_value=.55; scene.world=world
data=bpy.data.cameras.new('CloseReview'); cam=bpy.data.objects.new('CloseReview',data); studio.objects.link(cam); scene.camera=cam; data.type='ORTHO'; data.ortho_scale=.53
cam.location=(.62,-1.0,1.98); aim(cam,(0,.015,1.70))
scene.render.engine='CYCLES'; scene.cycles.samples=64; scene.cycles.use_denoising=True
scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
body.hide_render=True; rig.hide_render=True; rig.hide_set(True)
select([hachi]); scene.frame_start=1; scene.frame_end=61
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=.65; area.spaces.active.region_3d.view_location=(0,0,1.70)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Kabuto01.blend'))
if '--no-render' in sys.argv:
    print('KABUTO01_SOURCE_COMPLETE '+json.dumps(report)); sys.exit(0)
scene.render.filepath=str(ART/'Review/Captures/blender-hero.png'); bpy.ops.render.render(write_still=True)
body.hide_render=False
scene.render.filepath=str(ART/'Review/Captures/blender-fit.png'); bpy.ops.render.render(write_still=True)
for ob in components: ob.hide_render=True
helmet.hide_render=False; helmet.location=PIVOT
scene.render.filepath=str(ART/'Review/Captures/blender-runtime-fit.png'); bpy.ops.render.render(write_still=True)
print('KABUTO01_SOURCE_COMPLETE '+json.dumps(report))
