"""Original SHŌEN Samurai 01. Blender 5.1+, deterministic, no downloaded meshes.
Run: Blender --background --factory-startup --python scripts/build_samurai.py
Coordinates in metres: +X character left, -Y forward, +Z up. FBX uses explicit
raw-axis import contract (convert_scene=False), so Unreal = (x,-y,z)*100,
then runtime components yaw -90 degrees to face +X. VAT uses the same mapping.
"""
import bpy
import bmesh
import math
import json
import random
import sys
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / 'exports'
TEX = ROOT / 'textures'
for p in (ROOT, EXPORT, TEX): p.mkdir(parents=True, exist_ok=True)
random.seed(1180)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials): bpy.data.materials.remove(data)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
scene.render.fps=30
source=bpy.data.collections.new('SOURCE • modular clothing, armor & equipment'); scene.collection.children.link(source)
runtime=bpy.data.collections.new('EXPORT • combined body + baked crowd LODs'); scene.collection.children.link(runtime)
studio=bpy.data.collections.new('STUDIO • cameras and lighting'); scene.collection.children.link(studio)

# A sixteen-cell reusable 2048 atlas: one color/normal/ORM set for all equipment.
N=2048; S=N//4
rng=np.random.default_rng(1180)
y,x=np.mgrid[0:S,0:S].astype(np.float32); u=x/S; v=y/S
noise=rng.normal(0,1,(S,S)).astype(np.float32)
base=np.zeros((N,N,4),np.float32); base[:,:,3]=1
orm=np.ones((N,N,4),np.float32); normal=np.ones((N,N,4),np.float32)
colors=[(.042,.054,.061),(.24,.045,.024),(.025,.052,.095),(.11,.066,.038),
        (.40,.32,.19),(.23,.11,.045),(.48,.285,.18),(.47,.36,.205),
        (.38,.43,.47),(.014,.012,.01),(.54,.50,.41),(.009,.007,.005),
        (.29,.048,.026),(.029,.045,.058),(.46,.36,.22),(.033,.040,.046)]
for cell,c in enumerate(colors):
    rgb=np.empty((S,S,3),np.float32); rgb[:]=c
    height=np.zeros((S,S),np.float32); rough=np.full((S,S),.63,np.float32); metal=np.zeros((S,S),np.float32)
    variation=(noise*.025+np.sin(u*80)*.013+np.sin(v*210)*.008)
    rgb*=np.clip(1+variation[:,:,None],.65,1.2)
    if cell in (0,1):
        # Small paired laces, punched holes, metal lamella edges. Each mesh strip
        # maps to this cell once; no individual cord meshes or transparent cards.
        col=np.mod(u*20,1); edge=(col<.07)|(col>.93)
        height+=np.where(edge,-.25,.06)
        rgb[edge]*=.50
        horizontal=(np.abs(v-.06)<.013)|(np.abs(v-.92)<.018)
        rgb[horizontal]=(.22,.16,.09); height[horizontal]=.3
        for row in (.3,.63):
            lace=(np.abs(np.mod(u*20+(v-row)*.8,1)-.27)<.09)&(np.abs(v-row)<.17)
            lace|=(np.abs(np.mod(u*20-(v-row)*.8,1)-.67)<.09)&(np.abs(v-row)<.17)
            holes=((col-.27)**2/(.14**2)+(v-row-.15)**2/(.06**2)<1)
            rgb[holes]=(.008,.007,.006); height[holes]=-.7
            rgb[lace]=(.23,.047,.026); height[lace]=.6+np.sin(v[lace]*420)*.1
        rough[:]=.36; metal[:]=.22
    elif cell in (2,13):
        weave=np.sin(u*950)*np.sin(v*950)
        height=weave*.13
        # Restrained repeating gold chrysanthemum-like weave, not a historical mon.
        dx=np.mod(u*5,1)-.5; dy=np.mod(v*5,1)-.5
        a=np.arctan2(dy,dx); rad=np.sqrt(dx*dx+dy*dy)
        flower=np.abs(rad-(.18+.055*np.cos(a*8)))<.026
        stem=(np.abs(np.sin(u*math.pi*10)*.10+dy)<.014)&(rad>.29)
        rgb[flower]=(.19,.16,.095) if cell==2 else (.06,.073,.083)
        rgb[stem]*=1.8; height[flower]+=.17; rough[:]=.82
    elif cell in (4,14):
        pat=np.sin(u*90+np.sin(v*45)*3)*np.cos(v*110)
        rgb*=np.clip(.88+pat[:,:,None]*.12+noise[:,:,None]*.035,.5,1.15)
        height=pat*.10; rough[:]=.44; metal[:]=.78
    elif cell==3:
        height=noise*.3+np.sin(u*300+v*40)*.05; rough[:]=.8
    elif cell==5:
        grain=np.sin(u*420+np.sin(v*28)*4)
        rgb*=1+grain[:,:,None]*.13; height=grain*.13; rough[:]=.51
    elif cell in (7,12):
        braid=np.sin(u*200+v*110)*np.sin(u*200-v*110)
        rgb*=1+braid[:,:,None]*.16; height=braid*.3; rough[:]=.87
    elif cell==6:
        rgb*=1+noise[:,:,None]*.018; height=noise*.04; rough[:]=.70
    elif cell==8:
        metal[:]=.90; rough[:]=.29; height=np.sin(u*1300)*.07
    elif cell==15:
        metal[:]=.50; rough[:]=.39; height=noise*.045
    elif cell==9:
        height=np.sin(u*620)*.3; rough[:]=.78
    gy,gx=np.gradient(height)
    vec=np.stack((-gx*2.5,-gy*2.5,np.ones_like(gx)),axis=2)
    vec/=np.linalg.norm(vec,axis=2,keepdims=True)
    row=cell//4; col=cell%4; sl=(slice(row*S,(row+1)*S),slice(col*S,(col+1)*S))
    base[sl][:,:,:3]=np.clip(rgb,0,1)
    normal[sl][:,:,:3]=vec*.5+.5
    orm[sl][:,:,0]=1; orm[sl][:,:,1]=rough; orm[sl][:,:,2]=metal

def write_image(name, pixels, path, linear=False, exr=False):
    h,w=pixels.shape[:2]
    im=bpy.data.images.new(name,width=w,height=h,alpha=True,float_buffer=exr)
    if linear: im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(pixels.ravel())
    im.filepath_raw=str(path); im.file_format='OPEN_EXR' if exr else 'PNG'
    if exr:
        old_format=scene.render.image_settings.file_format
        scene.render.image_settings.file_format='OPEN_EXR'; scene.render.image_settings.color_depth='16'; scene.render.image_settings.exr_codec='ZIP'
        im.save_render(str(path),scene=scene)
        scene.render.image_settings.file_format=old_format
    else: im.save()
    return im
color_im=write_image('T_Samurai_BaseColor',base,TEX/'T_Samurai_BaseColor.png')
normal_im=write_image('T_Samurai_Normal',normal,TEX/'T_Samurai_Normal.png',True)
orm_im=write_image('T_Samurai_ORM',orm,TEX/'T_Samurai_ORM.png',True)
mat=bpy.data.materials.new('M_Samurai_Atlas'); mat.use_nodes=True
nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
for im,loc in ((color_im,(-600,200)),(normal_im,(-600,-80)),(orm_im,(-600,-400))):
    n=nodes.new('ShaderNodeTexImage'); n.image=im; n.location=loc
    if im==color_im: links.new(n.outputs['Color'],bs.inputs['Base Color'])
    elif im==normal_im:
        nm=nodes.new('ShaderNodeNormalMap'); nm.location=(-260,-80); nm.inputs['Strength'].default_value=.48
        links.new(n.outputs['Color'],nm.inputs['Color']); links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    else:
        sep=nodes.new('ShaderNodeSeparateColor'); links.new(n.outputs['Color'],sep.inputs['Color'])
        links.new(sep.outputs['Green'],bs.inputs['Roughness']); links.new(sep.outputs['Blue'],bs.inputs['Metallic'])

class Builder:
    def __init__(self,name): self.name=name; self.v=[]; self.f=[]; self.uv=[]; self.b=[]; self.smooth=[]
    def surface(self,verts,faces,tile,bone,smooth=False,uvs=None):
        start=len(self.v); self.v.extend(verts); self.b.extend([bone]*len(verts))
        for face in faces:
            self.f.append(tuple(start+i for i in face)); self.smooth.append(smooth)
            if uvs: coords=[uvs[i] for i in face]
            elif len(face)==4: coords=[(0,0),(1,0),(1,1),(0,1)]
            else: coords=[(0,0),(1,0),(.5,1)][:len(face)]
            self.uv.append([((tile%4+.012+.976*a)/4,(tile//4+.012+.976*b)/4) for a,b in coords])
    def object(self):
        mesh=bpy.data.meshes.new(self.name); mesh.from_pydata(self.v,[],self.f); mesh.update()
        ob=bpy.data.objects.new(self.name,mesh); source.objects.link(ob); mesh.materials.append(mat)
        uv=mesh.uv_layers.new(name='UV_Atlas')
        for p,coords,sm in zip(mesh.polygons,self.uv,self.smooth):
            p.use_smooth=sm
            for i,co in zip(p.loop_indices,coords): uv.data[i].uv=co
        bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
        groups={b:ob.vertex_groups.new(name=b) for b in sorted(set(self.b))}
        by={b:[] for b in groups}
        for i,b in enumerate(self.b): by[b].append(i)
        for b,ids in by.items(): groups[b].add(ids,1,'REPLACE')
        return ob

B={name:Builder(name) for name in ['SK_Body','CLO_Undergarment','CLO_Hakama','CLO_Footwear',
 'ARM_Chest','ARM_Shoulder_L','ARM_Shoulder_R','ARM_Kote_L','ARM_Kote_R','ARM_Kusazuri',
 'ARM_Suneate_L','ARM_Suneate_R','ARM_Kabuto','WPN_Yumi','WPN_Tachi','WPN_Sheath','PROP_Quiver','PROP_Arrows']}

def tube(b,points,radius,tile,bone,sides=8,radii=None):
    pts=[Vector(p) for p in points]; verts=[]; uvs=[]
    for i,p in enumerate(pts):
        axis=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        ref=Vector((0,0,1)) if abs(axis.z)<.9 else Vector((0,1,0))
        xx=axis.cross(ref).normalized(); yy=axis.cross(xx).normalized()
        r=radius if radii is None else radii[i]
        for j in range(sides):
            a=2*math.pi*j/sides; verts.append(p+r*(xx*math.cos(a)+yy*math.sin(a))); uvs.append((j/sides,i/max(1,len(pts)-1)))
    faces=[]
    for i in range(len(pts)-1):
        for j in range(sides): faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(pts)-1)*sides+j for j in range(sides))])
    # cap ngon UVs use provided vertex mapping too.
    b.surface(verts,faces,tile,bone,True,uvs)

def ellipsoid(b,center,scale,tile,bone,segments=16,rings=10):
    verts=[]; uvs=[]
    for i in range(rings+1):
        a=math.pi*i/rings
        for j in range(segments+1):
            t=2*math.pi*j/segments
            verts.append((center[0]+scale[0]*math.sin(a)*math.cos(t),center[1]+scale[1]*math.sin(a)*math.sin(t),center[2]+scale[2]*math.cos(a)))
            uvs.append((j/segments,i/rings))
    faces=[]
    for i in range(rings):
        for j in range(segments):
            a=i*(segments+1)+j; faces.append((a,a+1,a+segments+2,a+segments+1))
    b.surface(verts,faces,tile,bone,True,uvs)

def profile(b,rings,tile,bone,segments=20,pleat=0):
    # rings (x,y,z,rx,ry), ring's nominal local axis is Z.
    verts=[]; uvs=[]
    for i,(x,y,z,rx,ry) in enumerate(rings):
        for j in range(segments+1):
            a=2*math.pi*j/segments; r=1+pleat*math.cos(a*8)
            verts.append((x+rx*math.cos(a)*r,y+ry*math.sin(a)*r,z)); uvs.append((j/segments,i/(len(rings)-1)))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(segments):
            a=i*(segments+1)+j; faces.append((a,a+1,a+segments+2,a+segments+1))
    faces += [tuple(range(segments,-1,-1)),tuple((len(rings)-1)*(segments+1)+j for j in range(segments+1))]
    b.surface(verts,faces,tile,bone,True,uvs)

def plate(b,points,thick,tile,bone):
    # Front-facing sculpted sheet plus thickness; arbitrary polygon.
    n=len(points); verts=list(points)+[(x,y+thick,z) for x,y,z in points]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    for j in range(n): faces.append((j,(j+1)%n,(j+1)%n+n,j+n))
    # planar mapping chosen by xz extents for silhouette plates.
    xs=[p[0] for p in points]; zs=[p[2] for p in points]
    uv=[((p[0]-min(xs))/max(.001,max(xs)-min(xs)),(p[2]-min(zs))/max(.001,max(zs)-min(zs))) for p in verts]
    b.surface(verts,faces,tile,bone,False,uv)

def band(b,z0,z1,rx0,ry0,rx1,ry1,tile,bone,start=0,end=math.tau,segments=32):
    verts=[]; uvs=[]
    for k,(z,rx,ry) in enumerate([(z0,rx0,ry0),(z1,rx1,ry1),(z1,rx1-.005,ry1-.005),(z0,rx0-.005,ry0-.005)]):
        for j in range(segments+1):
            a=start+(end-start)*j/segments; verts.append((rx*math.cos(a),ry*math.sin(a),z)); uvs.append((j/segments,1 if k in (1,2) else 0))
    faces=[]
    for k in range(4):
        for j in range(segments):
            a=k*(segments+1)+j; nxt=((k+1)%4)*(segments+1)+j; faces.append((a,a+1,nxt+1,nxt))
    b.surface(verts,faces,tile,bone,True,uvs)

def torus_circle(b,center,radius,tube_radius,tile,bone,plane='XY',segments=28):
    pts=[]
    for i in range(segments+1):
        a=i*math.tau/segments
        off=(math.cos(a)*radius, math.sin(a)*radius,0) if plane=='XY' else (math.cos(a)*radius,0,math.sin(a)*radius)
        pts.append(tuple(center[j]+off[j] for j in range(3)))
    tube(b,pts,tube_radius,tile,bone,6)

# Body beneath garment: human proportions are retained as modular source.
profile(B['SK_Body'],[(0,0,.86,.14,.10),(0,0,1.02,.145,.09),(0,0,1.20,.17,.10),(0,0,1.40,.22,.105),(0,0,1.48,.10,.075)],6,'spine_02',20)
profile(B['SK_Body'],[(0,0,1.43,.058,.055),(0,0,1.59,.061,.06)],6,'neck_01',16)
# Shaped head rings, flatter jaw and brow; nose and lid volumes are separate detail.
profile(B['SK_Body'],[(0,-.022,1.545,.025,.038),(0,-.014,1.560,.047,.052),(0,-.004,1.591,.067,.062),
 (0,0,1.630,.078,.075),(0,0,1.668,.079,.077),(0,.007,1.706,.079,.078),(0,.009,1.745,.065,.066),(0,.009,1.771,.027,.036)],6,'head',32)
ellipsoid(B['SK_Body'],(0,.008,1.750),(.066,.066,.027),9,'head',24,8)
# Nose with bridge, rounded tip, nostril wings; cheeks, lower lip and chin.
profile(B['SK_Body'],[(0,-.078,1.622,.018,.012),(0,-.088,1.635,.017,.019),(0,-.083,1.652,.010,.017),(0,-.073,1.689,.009,.006)],6,'head',12)
for s in (-1,1):
    ellipsoid(B['SK_Body'],(s*.013,-.086,1.63),(.011,.012,.008),6,'head',12,6)
    ellipsoid(B['SK_Body'],(s*.012,-.095,1.626),(.004,.002,.0028),3,'head',8,4)
    ellipsoid(B['SK_Body'],(s*.035,-.071,1.67),(.016,.005,.004),10,'head',16,8)
    ellipsoid(B['SK_Body'],(s*.035,-.0787,1.67),(.0036,.0019,.0036),11,'head',12,8)
    for lower in (False,True):
        pts=[(s*.035+.016*math.cos(a),-.078- .0008*math.sin(a),1.67+(.0036 if lower else .005)*math.sin(a)) for a in np.linspace(math.pi if lower else 0, math.tau if lower else math.pi,12)]
        tube(B['SK_Body'],pts,.0015,6,'head',6)
    tube(B['SK_Body'],[(s*.013,-.073,1.684),(s*.026,-.077,1.69),(s*.042,-.074,1.69),(s*.057,-.067,1.684)],.0024,9,'head',6)
    ellipsoid(B['SK_Body'],(s*.078,.0,1.648),(.013,.013,.024),6,'head',12,8)
    tube(B['SK_Body'],[(s*.005,-.078,1.610),(s*.015,-.077,1.607),(s*.024,-.07,1.606)],.0032,9,'head',6)
tube(B['SK_Body'],[(-.022,-.075,1.602),(0,-.081,1.600),(.022,-.075,1.602)],.0030,6,'head',8)
tube(B['SK_Body'],[(-.017,-.074,1.596),(0,-.08,1.595),(.017,-.074,1.596)],.0030,6,'head',8)
# Trim moustache and short jaw beard, no full-face mask.
for s in (-1,1):
    tube(B['SK_Body'],[(s*.052,-.049,1.598),(s*.038,-.061,1.577),(s*.012,-.063,1.566)],.008,9,'head',7)
ellipsoid(B['SK_Body'],(0,-.064,1.567),(.021,.008,.014),9,'head',12,6)

profile(B['CLO_Undergarment'],[(0,0,1.425,.11,.086),(0,0,1.48,.077,.07),(0,0,1.548,.062,.059)],13,'neck_01',24)
# Underrobe and crossed collar, billowing sleeves and hakama gathered at knees.
profile(B['CLO_Undergarment'],[(0,.005,.96,.166,.113),(0,.0,1.15,.178,.115),(0,0,1.38,.230,.118),(0,0,1.46,.13,.096),(0,0,1.495,.094,.082),(0,0,1.525,.068,.063)],2,'spine_02',24,.025)
for s in (-1,1):
    plate(B['CLO_Undergarment'],[(s*.07,-.076,1.48),(s*.16,-.11,1.42),(-s*.035,-.126,1.25),(-s*.065,-.122,1.28)],.004,13,'spine_03')
    tube(B['CLO_Undergarment'],[(s*.07,-.083,1.48),(-s*.039,-.13,1.26)],.009,4,'spine_03',6)
    arm='l' if s==1 else 'r'
    profile(B['SK_Body'],[(s*.235,0,1.43,.061,.059),(s*.30,0,1.31,.059,.057),(s*.365,-.005,1.15,.043,.046)],6,'upperarm_'+arm,16)
    profile(B['SK_Body'],[(s*.365,-.005,1.15,.044,.046),(s*.397,-.014,1.04,.040,.041),(s*.425,-.024,.95,.027,.029)],6,'lowerarm_'+arm,16)
    profile(B['SK_Body'],[(s*.105,0,.99,.077,.086),(s*.115,.0,.77,.065,.072),(s*.112,-.014,.55,.049,.05)],6,'thigh_'+arm,16)
    profile(B['CLO_Undergarment'],[(s*.25,0,1.43,.080,.085),(s*.285,0,1.34,.086,.09),(s*.335,0,1.20,.075,.08),(s*.363,-.005,1.15,.058,.067)],2,'upperarm_'+arm,16,.06)
    profile(B['CLO_Undergarment'],[(s*.363,-.005,1.15,.06,.067),(s*.400,-.01,1.05,.061,.061),(s*.425,-.024,.94,.038,.043)],2,'lowerarm_'+arm,16,.05)
    profile(B['CLO_Hakama'],[(s*.11,.0,1.04,.092,.103),(s*.125,.01,.93,.104,.119),(s*.13,.012,.77,.116,.134),(s*.117,.0,.62,.095,.105),(s*.112,-.016,.555,.063,.063)],2,'thigh_'+arm,24,.085)
    profile(B['SK_Body'],[(s*.112,-.014,.55,.050,.05),(s*.11,.003,.38,.047,.054),(s*.105,.007,.13,.033,.038)],6,'calf_'+arm,16)
    profile(B['CLO_Undergarment'],[(s*.112,-.014,.56,.062,.063),(s*.11,.003,.40,.055,.064),(s*.105,.007,.13,.037,.042)],13,'calf_'+arm,16)
    ellipsoid(B['CLO_Footwear'],(s*.105,-.064,.083),(.047,.111,.047),13,'foot_'+arm,18,10)
    ellipsoid(B['CLO_Footwear'],(s*.105,-.059,.026),(.055,.12,.020),7,'foot_'+arm,18,6)
    # Sandal perimeter cord, ankle wraps and crossed waraji straps.
    for z in (.027,.040):
        tube(B['CLO_Footwear'],[(s*.105+.051*math.cos(a),-.059+.116*math.sin(a),z) for a in np.linspace(0,math.tau,30)],.004,7,'foot_'+arm,5)
    tube(B['CLO_Footwear'],[(s*.105-.044,-.12,.047),(s*.105,-.073,.143),(s*.105+.046,-.034,.047)],.006,7,'foot_'+arm,7)
    tube(B['CLO_Footwear'],[(s*.105+.044,-.12,.047),(s*.105,-.103,.143),(s*.105-.046,-.034,.047)],.006,7,'foot_'+arm,7)
    for z in (.155,.174):
        tube(B['CLO_Footwear'],[(s*.105+.039*math.cos(a),.005+.044*math.sin(a),z) for a in np.linspace(0,math.tau,22)],.006,7,'calf_'+arm,6)
    # Hands: gauntlet atop palm and individually shaped bent fingers.
    ellipsoid(B['SK_Body'],(s*.435,-.032,.90),(.038,.029,.056),6,'hand_'+arm,16,10)
    for j in range(4):
        px=s*(.410+j*.016); end=.813+abs(j-1.5)*.009
        pts=[(px,-.034,.873),(px+s*.005,-.041,.845),(px+s*.003,-.055,end),(px,-.068,end+.01)]
        tube(B['SK_Body'],pts,.007,6,'hand_'+arm,8,radii=[.008,.0075,.0065,.005])
    tube(B['SK_Body'],[(s*.407,-.048,.919),(s*.394,-.06,.891),(s*.401,-.076,.875)],.009,6,'hand_'+arm,8)

# Lamellar cuirass: nine overlapping bands and sculpted upper breast panel.
for i in range(9):
    z=1.054+i*.039; rx=.182+(i/8)*.04; ry=.125+(i/8)*.007
    band(B['ARM_Chest'],z,z+.046,rx+.008,ry+.008,rx,ry,0,'spine_02',segments=32)
band(B['ARM_Chest'],1.385,1.444,.224,.138,.225,.126,3,'spine_03',segments=32)
for z in (1.06,1.401,1.44): band(B['ARM_Chest'],z,z+.010,.230 if z>1.4 else .19,.138 if z>1.4 else .139,.230 if z>1.4 else .19,.138 if z>1.4 else .139,4,'spine_02',segments=32)
# Chest hanging silk ties, shoulder straps and ornamental metal studs, kept sparse.
for s in (-1,1):
    tube(B['ARM_Chest'],[(s*.145,-.11,1.43),(s*.145,-.02,1.487),(s*.145,.12,1.43)],.013,3,'spine_03',8)
    torus_circle(B['ARM_Chest'],(s*.144,-.144,1.368),.021,.004,4,'spine_03','XZ',18)
    tube(B['ARM_Chest'],[(s*.145,-.150,1.362),(s*.143,-.158,1.295),(s*.14,-.159,1.26)],.007,12,'spine_02',6)
    profile(B['ARM_Chest'],[(s*.14,-.159,1.273,.012,.01),(s*.14,-.159,1.225,.018,.011)],12,'spine_02',10)
    for z in (1.412,1.074):
        for x0 in (.04,.10,.16): ellipsoid(B['ARM_Chest'],(s*x0,-.139,z),(.005,.003,.005),4,'spine_02',8,4)
# Thick white waist sash with irregular braided turns and knot.
for i in range(3):
    tube(B['ARM_Chest'],[(.195*math.cos(a),.146*math.sin(a),1.065+i*.016+.004*math.sin(a*3)) for a in np.linspace(0,math.tau,40)],.009,7,'pelvis',7)
for s in (-1,1):
    tube(B['ARM_Chest'],[(0,-.16,1.083),(s*.09,-.177,1.116),(s*.10,-.178,1.073),(0,-.163,1.08),(s*.056,-.164,.99)],.011,7,'pelvis',7)

# Four kusazuri skirt sectors with depth and separated corners.
for idx,center in enumerate((-math.pi/2,0,math.pi/2,math.pi)):
    bone=['skirt_front','skirt_l','skirt_back','skirt_r'][idx]
    for i in range(8):
        t=i/8; z=1.049-i*.041; rx=.207+t*.086; ry=.151+t*.067
        band(B['ARM_Kusazuri'],z-.044,z+.007,rx+.010,ry+.007,rx,ry,0,bone,center-.64,center+.64,10)
    band(B['ARM_Kusazuri'],.711,.731,.301,.224,.298,.222,4,bone,center-.64,center+.64,10)

# Broad o-sode, articulated sleeves and lamellar shin guards.
for s in (-1,1):
    side='L' if s==1 else 'R'; arm=side.lower(); b=B['ARM_Shoulder_'+side]
    for i in range(8):
        top=1.505-i*.037; xx=.245+i*.015
        # forward face is a real raised slab, with side wrapping profile.
        pts=[(s*(xx-.058),-.143,top),(s*(xx+.083),-.117,top-.015),
             (s*(xx+.091),-.119,top-.058),(s*(xx-.05),-.145,top-.044)]
        plate(b,pts,.025,0,'sode_'+arm)
        points=[(s*(xx+.083),-.117,top-.015),(s*(xx+.102),.025,top-.006),(s*(xx+.080),.155,top-.016),(s*(xx+.088),.155,top-.058),(s*(xx+.110),.025,top-.050),(s*(xx+.091),-.119,top-.058)]
        verts=points+[(x-s*.005,y,z) for x,y,z in points]
        faces=[(0,1,4,5),(1,2,3,4),(11,10,7,6),(10,9,8,7)]+[(j,(j+1)%6,(j+1)%6+6,j+6) for j in range(6)]
        b.surface(verts,faces,0,'sode_'+arm,False,[(0,1),(.5,1),(1,1),(1,0),(.5,0),(0,0)]*2)
    plate(b,[(s*.17,-.137,1.511),(s*.33,-.111,1.489),(s*.34,-.108,1.466),(s*.178,-.14,1.488)],.02,4,'sode_'+arm)
    plate(b,[(s*.292,-.145,1.203),(s*.451,-.116,1.187),(s*.451,-.116,1.172),(s*.292,-.145,1.187)],.023,4,'sode_'+arm)
    for j in range(3): ellipsoid(b,(s*(.204+.042*j),-.153,1.483),(.009,.004,.009),4,'sode_'+arm,10,6)
    # Kote includes three long splints, a wrist cuff and hand plate.
    k=B['ARM_Kote_'+side]
    for j in range(3):
        xoff=(j-1)*.024
        plate(k,[(s*(.373+xoff),-.064,1.136),(s*(.391+xoff),-.073,1.126),(s*(.438+xoff*.6),-.068,.952),(s*(.422+xoff*.6),-.073,.947)],.008,0,'lowerarm_'+arm)
    for z,xx in ((1.12,.375),(.965,.425)):
        tube(k,[(s*xx+.049*math.cos(a),-.012+.062*math.sin(a),z) for a in np.linspace(0,math.tau,20)],.008,12,'lowerarm_'+arm,6)
    plate(k,[(s*.402,-.059,.94),(s*.463,-.055,.935),(s*.458,-.064,.880),(s*.419,-.067,.874)],.009,0,'hand_'+arm)
    ellipsoid(k,(s*.438,-.072,.906),(.016,.004,.017),4,'hand_'+arm,10,6)
    shin=B['ARM_Suneate_'+side]
    for j in range(5):
        a=-math.pi/2+(j-2)*.29; px=s*.11+math.cos(a)*.055; py=math.sin(a)*.064
        plate(shin,[(px-.009,py,.529),(px+.009,py,.529),(px+.006,py*.70,.196),(px-.006,py*.70,.196)],.009,0,'calf_'+arm)
        tube(shin,[(px,py-.005,.53),(px,py*.70-.005,.20)],.0022,4,'calf_'+arm,5)
    for z in (.49,.24):
        tube(shin,[(s*.11+.061*math.cos(a),.0+.069*math.sin(a),z) for a in np.linspace(0,math.tau,24)],.006,7,'calf_'+arm,6)
    ellipsoid(shin,(s*.11,-.044,.565),(.058,.042,.043),3,'calf_'+arm,16,8)

# Kabuto: ribbed iron bowl, flared multi-layer shikoro, fukigaeshi and kuwagata.
helm=B['ARM_Kabuto']
profile(helm,[(0,.015,1.734,.125,.120),(0,.015,1.77,.131,.126),(0,.018,1.82,.110,.105),
              (0,.019,1.863,.066,.068),(0,.019,1.882,.022,.025)],15,'head',32)
for j in range(16):
    a=math.tau*j/16
    pts=[(rx*math.cos(a),.017+ry*math.sin(a),z) for z,rx,ry in [(1.74,.126,.12),(1.77,.133,.127),(1.82,.112,.107),(1.86,.069,.071),(1.88,.022,.025)]]
    tube(helm,pts,.0025,4 if j%4==0 else 15,'head',5)
    ellipsoid(helm,(.129*math.cos(a),.015+.123*math.sin(a),1.762),(.004,.004,.004),4,'head',8,4)
for i in range(5):
    z=1.735-i*.037; r=.133+i*.014
    # shift the neck guard slightly backward to leave the face open.
    start=len(helm.v)
    band(helm,z-.047,z+.003,r+.013,r+.015,r,r+.005,0,'head',-.36,math.pi+.36,22)
    for index in range(start,len(helm.v)): helm.v[index]=Vector(helm.v[index])+Vector((0,.021,0))
# Visor crescent and gold hem.
plate(helm,[(-.128,-.07,1.753),(-.109,-.145,1.749),(-.061,-.175,1.744),(.061,-.175,1.744),(.109,-.145,1.749),(.128,-.07,1.753)],.019,0,'head')
tube(helm,[(-.119,-.139,1.747),(-.065,-.176,1.742),(0,-.185,1.741),(.065,-.176,1.742),(.119,-.139,1.747)],.004,4,'head',7)
for s in (-1,1):
    plate(helm,[(s*.105,-.086,1.753),(s*.164,-.065,1.72),(s*.181,-.078,1.655),(s*.124,-.111,1.669)],.018,4,'head')
    ellipsoid(helm,(s*.143,-.107,1.706),(.020,.009,.021),3,'head',12,8)
    torus_circle(helm,(s*.143,-.118,1.705),.019,.003,4,'head','XZ',16)
    # Tall leaf-like horns. Designed as broad sheet silhouettes, not antlers.
    plate(helm,[(s*.024,-.146,1.775),(s*.053,-.155,1.849),(s*.074,-.153,1.932),
               (s*.078,-.145,2.013),(s*.122,-.135,2.093),(s*.183,-.131,2.107),
               (s*.138,-.133,2.066),(s*.124,-.139,1.980),(s*.100,-.148,1.887),
               (s*.061,-.152,1.800)],.007,4,'head')
    # Chin cord and side loops in muted red silk.
    tube(helm,[(s*.112,-.049,1.70),(s*.094,-.077,1.611),(s*.034,-.052,1.542),(0,-.060,1.532)],.0065,12,'head',7)
    tube(helm,[(0,-.066,1.536),(s*.031,-.078,1.510),(s*.047,-.07,1.543),(0,-.066,1.536),(s*.028,-.071,1.477)],.005,12,'head',6)
ellipsoid(helm,(0,-.151,1.792),(.033,.009,.033),3,'head',20,10)
torus_circle(helm,(0,-.161,1.793),.029,.0037,4,'head','XZ',24)
for a in (math.pi/2,math.pi/2+math.tau/3,math.pi/2+2*math.tau/3):
    ellipsoid(helm,(.013*math.cos(a),-.163,1.793+.013*math.sin(a)),(.010,.003,.010),4,'head',12,6)

# Asymmetric yumi, held at its lower third. Grip has its own logical pivot.
bow=B['WPN_Yumi']; bow_points=[]
for i in range(25):
    z=.075+2.02*i/24
    y=-.14+.115*math.sin(math.pi*i/24)-.07*math.sin(math.tau*i/24)
    bow_points.append((.452,y,z))
tube(bow,bow_points,.010,5,'bow_socket',10,radii=[.006+.007*math.sin(math.pi*i/24)**.6 for i in range(25)])
tube(bow,[bow_points[0],(.452,-.235,.81),bow_points[-1]],.0017,7,'bow_socket',5)
for i in range(13):
    z=.837+i*.010
    t=(z-.075)/2.02; by=-.14+.115*math.sin(math.pi*t)-.07*math.sin(math.tau*t)
    tube(bow,[(.452+.015*math.cos(a),by+.015*math.sin(a),z) for a in np.linspace(0,math.tau,12)],.0022,3,'bow_socket',5)
for i in (2,7,14,20):
    p=bow_points[i]; tube(bow,[(p[0]+.014*math.cos(a),p[1]+.014*math.sin(a),p[2]) for a in np.linspace(0,math.tau,12)],.003,4,'bow_socket',5)
# Tachi suspended edge down at left hip; sheath and blade remain separate.
path=[(.21,-.30,1.072),(.215,-.15,1.03),(.222,.00,.985),(.232,.17,.931),(.245,.36,.866),(.263,.54,.791),(.282,.70,.700)]
tube(B['WPN_Tachi'],path,.013,8,'sword_socket',8,radii=[.014,.014,.014,.014,.013,.011,.001])
tube(B['WPN_Tachi'],path[:2],.023,3,'sword_socket',10)
for t in np.linspace(0,1,10):
    p=Vector(path[0]).lerp(Vector(path[1]),float(t));
    tube(B['WPN_Tachi'],[(p.x-.020,p.y-.004,p.z),(p.x,p.y-.012,p.z+.02),(p.x+.02,p.y+.004,p.z),(p.x,p.y+.012,p.z-.02),(p.x-.020,p.y-.004,p.z)],.003,7,'sword_socket',5)
# Oval guard lies perpendicular to sword direction, approximately XZ.
torus_circle(B['WPN_Tachi'],path[1],.035,.008,4,'sword_socket','XZ',20)
tube(B['WPN_Sheath'],path[1:],.026,3,'sheath_socket',12,radii=[.026,.025,.025,.024,.021,.012])
for index in (1,2,4,6):
    p=path[index]
    torus_circle(B['WPN_Sheath'],p,.026 if index<6 else .012,.004,4,'sheath_socket','XZ',16)
for y0,z0 in ((.02,.98),(.30,.888)):
    tube(B['WPN_Sheath'],[(.19,y0,1.07),(.23,y0,z0)],.009,12,'sheath_socket',7)
# Quiver: weathered leather tube on the right/back, separately replaceable.
q0=Vector((-.188,.15,1.04)); q1=Vector((-.245,.21,1.68)); axis=(q1-q0).normalized()
tube(B['PROP_Quiver'],[q0,q1],.056,3,'quiver_socket',16,radii=[.043,.060])
for t in (.04,.18,.89,.97):
    p=q0.lerp(q1,t)
    torus_circle(B['PROP_Quiver'],p,.048+t*.012,.005,4,'quiver_socket','XY',18)
for s in (-1,1):
    tube(B['PROP_Quiver'],[(s*.14,.142,1.10),(-s*.14,.152,1.44)],.012,3,'quiver_socket',7)
for i in range(12):
    a=i*2.39996; r=.010+.034*math.sqrt(i/12)
    start=q0+Vector((r*math.cos(a),r*math.sin(a),.04))
    tip=q1+Vector((r*math.cos(a),r*math.sin(a),.15+(i%3)*.025))
    tube(B['PROP_Arrows'],[start,tip],.0026,5,'quiver_socket',5)
    for k in range(3):
        aa=k*math.tau/3; dx=.014*math.cos(aa); dy=.014*math.sin(aa)
        verts=[tuple(tip+Vector((0,0,-.085))),tuple(tip+Vector((dx,dy,-.065))),tuple(tip+Vector((dx,dy,-.01))),tuple(tip)]
        B['PROP_Arrows'].surface(verts,[(0,1,2,3),(3,2,1,0)],7,'quiver_socket',False,[(0,0),(1,.2),(1,.9),(0,1)])

objects=[b.object() for b in B.values()]
# Rig: standard humanoid naming plus four armor pivots and explicit weapon sockets.
armdata=bpy.data.armatures.new('SKEL_Samurai01'); rig=bpy.data.objects.new('RIG_Samurai01',armdata); source.objects.link(rig)
bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
bones={}
def bone(name,head,tail,parent=None):
    b=armdata.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=bones[parent]
    bones[name]=b
bone('root',(0,0,0),(0,0,.15)); bone('pelvis',(0,0,.94),(0,0,1.08),'root')
bone('spine_01',(0,0,1.08),(0,0,1.20),'pelvis'); bone('spine_02',(0,0,1.20),(0,0,1.34),'spine_01'); bone('spine_03',(0,0,1.34),(0,0,1.46),'spine_02')
bone('neck_01',(0,0,1.46),(0,0,1.57),'spine_03'); bone('head',(0,0,1.57),(0,0,1.78),'neck_01')
for s in (-1,1):
    a='l' if s==1 else 'r'
    bone('clavicle_'+a,(s*.035,0,1.425),(s*.235,0,1.425),'spine_03')
    bone('upperarm_'+a,(s*.235,0,1.425),(s*.365,-.005,1.15),'clavicle_'+a)
    bone('lowerarm_'+a,(s*.365,-.005,1.15),(s*.425,-.025,.95),'upperarm_'+a)
    bone('hand_'+a,(s*.425,-.025,.95),(s*.44,-.035,.866),'lowerarm_'+a)
    for j,f in enumerate(('thumb','index','middle','ring','pinky')):
        for k in range(3):
            x=s*(.406+j*.012); z=.889-k*.022
            bone(f'{f}_{k+1:02d}_{a}',(x,-.036,z),(x,-.037,z-.022),'hand_'+a if k==0 else f'{f}_{k:02d}_{a}')
    bone('thigh_'+a,(s*.11,0,.98),(s*.112,-.014,.555),'pelvis')
    bone('calf_'+a,(s*.112,-.014,.555),(s*.105,.007,.15),'thigh_'+a)
    bone('foot_'+a,(s*.105,.007,.15),(s*.105,-.13,.055),'calf_'+a)
    bone('ball_'+a,(s*.105,-.13,.055),(s*.105,-.17,.055),'foot_'+a)
    bone('sode_'+a,(s*.235,0,1.44),(s*.30,0,1.30),'clavicle_'+a)
for name,pos in [('front',(0,-.14,1.04)),('back',(0,.14,1.04)),('l',(.2,0,1.04)),('r',(-.2,0,1.04))]:
    bone('skirt_'+name,pos,(pos[0],pos[1],pos[2]-.20),'pelvis')
bone('bow_socket',(.452,-.08,.89),(.452,-.08,.99),'hand_l')
bone('sword_socket',path[0],path[1],'pelvis')
bone('sheath_socket',path[1],path[2],'pelvis')
bone('quiver_socket',q0,q1,'spine_03')
bpy.ops.object.mode_set(mode='OBJECT'); rig.select_set(False); rig.show_in_front=True
for ob in objects:
    ob.parent=rig; mod=ob.modifiers.new('Skin • rigid armor / weighted cloth','ARMATURE'); mod.object=rig
# Blend joint rings of cloth/body by proximity to named joints; rigid armor stays 1 bone.
for ob in (B['CLO_Undergarment'],): pass
# Separate meshes share seam positions; use forearm/upperarm dual weighting near elbow.
cloth=bpy.data.objects['CLO_Undergarment']
for vert in cloth.data.vertices:
    x,y,z=vert.co
    if abs(x)>.27 and abs(z-1.15)<.055:
        a='l' if x>0 else 'r'; t=max(0,min(1,(z-1.095)/.11))
        for g in list(vert.groups): cloth.vertex_groups[g.group].remove([vert.index])
        for name,w in [('upperarm_'+a,t),('lowerarm_'+a,1-t)]:
            vg=cloth.vertex_groups.get(name) or cloth.vertex_groups.new(name=name)
            if w>0: vg.add([vert.index],w,'REPLACE')

# Actions use bone-local X for limb swing, subtle Z sway for rigid plates.
rig.animation_data_create()
def action(name,frames,kind):
    act=bpy.data.actions.new(name); act.use_fake_user=True; rig.animation_data.action=act
    for f in range(1,frames+1):
        phase=(f-1)/(frames-1)*math.tau
        for pb in rig.pose.bones: pb.rotation_mode='XYZ'; pb.rotation_euler=(0,0,0); pb.location=(0,0,0)
        if kind=='idle':
            rig.pose.bones['spine_02'].rotation_euler.x=.009*math.sin(phase)
            rig.pose.bones['head'].rotation_euler.y=.022*math.sin(phase)
            for a,s in [('l',1),('r',-1)]: rig.pose.bones['lowerarm_'+a].rotation_euler.x=.02*math.sin(phase+s)
        if kind=='walk':
            rig.pose.bones['pelvis'].location.y=.015*(1-math.cos(phase*2))
            for a,s in [('l',1),('r',-1)]:
                wave=math.sin(phase)*s
                rig.pose.bones['thigh_'+a].rotation_euler.x=.40*wave
                rig.pose.bones['calf_'+a].rotation_euler.x=max(0,-wave)*.64
                rig.pose.bones['foot_'+a].rotation_euler.x=-max(0,-wave)*.30
                rig.pose.bones['upperarm_'+a].rotation_euler.x=-.21*wave
                rig.pose.bones['lowerarm_'+a].rotation_euler.x=-.11-.11*wave
                rig.pose.bones['sode_'+a].rotation_euler.x=-.08*wave
            rig.pose.bones['skirt_front'].rotation_euler.x=-.15*(.5+.5*math.sin(phase*2))
            rig.pose.bones['skirt_back'].rotation_euler.x=.12*(.5+.5*math.sin(phase*2))
        if kind=='attack':
            # A controlled forward thrust/test guard motion; no claim of archery release.
            t=(f-1)/(frames-1); wave=math.sin(math.pi*t)**2
            rig.pose.bones['spine_02'].rotation_euler.y=-.12*wave
            rig.pose.bones['upperarm_r'].rotation_euler.x=-1.00*wave
            rig.pose.bones['lowerarm_r'].rotation_euler.x=-.55*wave
            rig.pose.bones['sode_r'].rotation_euler.x=-.44*wave
            rig.pose.bones['head'].rotation_euler.y=.07*wave
            rig.pose.bones['thigh_l'].rotation_euler.x=.12*wave
        if kind=='walk':
            # Keep the lower sole planted. Knee/hip swing otherwise shortens both
            # legs and floats the character; compute compensation from the rig.
            bpy.context.view_layer.update()
            lowest=10.0
            for side,sign in [('l',1),('r',-1)]:
                pb=rig.pose.bones['foot_'+side]
                deform=pb.matrix @ pb.bone.matrix_local.inverted()
                for foot_y in (-.15,-.06,.025):
                    lowest=min(lowest,(deform @ Vector((sign*.105,foot_y,.02))).z)
            rig.pose.bones['root'].location.y=.012-lowest
        for pb in rig.pose.bones:
            pb.keyframe_insert(data_path='rotation_euler',frame=f,group=pb.name)
            if pb.name in ('pelvis','root'): pb.keyframe_insert(data_path='location',frame=f,group=pb.name)
    return act
acts={name:action(name,n,k) for name,n,k in [('A_Neutral',2,'neutral'),('A_Idle',61,'idle'),('A_Walk',31,'walk'),('A_Attack',46,'attack')]}
rig.animation_data.action=acts['A_Neutral']; scene.frame_set(1)

# Combine duplicates only. Original named component meshes remain editable.
def combined(obs,name):
    bpy.ops.object.select_all(action='DESELECT'); dup=[]
    for ob in obs:
        copy=ob.copy(); copy.data=ob.data.copy(); runtime.objects.link(copy); copy.select_set(True); dup.append(copy)
        if ob.name=='SK_Body':
            covered={g.index for g in ob.vertex_groups if g.name.startswith(('spine_', 'thigh_', 'calf_', 'upperarm_', 'lowerarm_'))}
            bm=bmesh.new(); bm.from_mesh(copy.data); deform=bm.verts.layers.deform.active
            remove=[v for v in bm.verts if deform and any(i in covered for i in v[deform].keys())]
            bmesh.ops.delete(bm,geom=remove,context='VERTS'); bm.to_mesh(copy.data); bm.free()
    bpy.context.view_layer.objects.active=dup[0]; bpy.ops.object.join(); ob=bpy.context.object; ob.name=name
    # All components share exactly one material; collapse duplicate slots if any.
    ob.data.materials.clear(); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.material_index=0
    return ob
body=combined([ob for ob in objects if not ob.name.startswith(('WPN_','PROP_'))],'SK_RuntimeBody')
crowd=combined(objects,'SM_CrowdSource')
# Export current skeletal body; weapons will attach to exported socket bones.
def select_only(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs: ob.hide_set(False); ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
def fbx(path,obs,animation=False):
    select_only(obs)
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','ARMATURE'},
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',
        use_space_transform=False,bake_space_transform=False,mesh_smooth_type='FACE',use_mesh_modifiers=True,
        add_leaf_bones=False,primary_bone_axis='Y',secondary_bone_axis='X',use_armature_deform_only=False,
        bake_anim=animation,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,path_mode='RELATIVE',embed_textures=False)
fbx(EXPORT/'SK_Samurai01.fbx',[rig,body])
for name,act in acts.items():
    rig.animation_data.action=act; scene.frame_start=1; scene.frame_end=61 if name=='A_Idle' else 31 if name=='A_Walk' else 46 if name=='A_Attack' else 2
    fbx(EXPORT/(name+'.fbx'),[rig],True)
rig.animation_data.action=acts['A_Neutral']; scene.frame_set(1)
# Weapons export at authored position relative to root; export pivot metadata allows
# Unreal to convert their transform relative to socket. Source origins are set below.
for name,asset in [('WPN_Yumi','SM_Yumi'),('WPN_Tachi','SM_Tachi'),('WPN_Sheath','SM_Sheath'),('PROP_Quiver','SM_Quiver'),('PROP_Arrows','SM_Arrows')]:
    ob=bpy.data.objects[name]
    cp=ob.copy(); cp.data=ob.data.copy(); runtime.objects.link(cp); cp.parent=None
    cp.modifiers.clear()
    socket={'WPN_Yumi':'bow_socket','WPN_Tachi':'sword_socket','WPN_Sheath':'sheath_socket','PROP_Quiver':'quiver_socket','PROP_Arrows':'quiver_socket'}[name]
    pivot=rig.data.bones[socket].head_local.copy()
    for vert in cp.data.vertices: vert.co-=pivot
    cp.location=(0,0,0)
    fbx(EXPORT/(asset+'.fbx'),[cp]); bpy.data.objects.remove(cp,do_unlink=True)

# Bake actual rig positions and normals into three independent LOD VAT sets.
# UV1 stores vertex column and row within one frame; shader supplies frame-row offset.
# Positions are offsets in Unreal raw-import cm, so FBX vertex reordering is harmless.
vat_info=[]
for lod,ratio in [(0,1.0),(1,.48),(2,.15)]:
    select_only([crowd]); ob=crowd.copy(); ob.data=crowd.data.copy(); runtime.objects.link(ob); ob.name=f'SM_Crowd_LOD{lod}'
    bpy.context.view_layer.objects.active=ob; crowd.select_set(False); ob.select_set(True)
    # Keep armature modifier last so decimation runs on neutral source geometry.
    if ratio<1:
        dec=ob.modifiers.new('Measured distance reduction','DECIMATE'); dec.ratio=ratio; dec.use_collapse_triangulate=True
        bpy.ops.object.modifier_move_up(modifier=dec.name)
        bpy.ops.object.modifier_apply(modifier=dec.name)
    tri=ob.modifiers.new('Stable triangulation','TRIANGULATE'); bpy.ops.object.modifier_move_up(modifier=tri.name); bpy.ops.object.modifier_apply(modifier=tri.name)
    V=len(ob.data.vertices); width=2048; rows=math.ceil(V/width)
    total_frames=24+24+24; h=rows*total_frames
    pos=np.zeros((h,width,4),np.float32); pos[:,:,3]=1
    nor=np.zeros((h,width,4),np.float32); nor[:,:,3]=1
    rest=np.array([tuple(v.co) for v in ob.data.vertices],dtype=np.float32)
    uv=ob.data.uv_layers.new(name='UV_VAT')
    for loop in ob.data.loops:
        idx=loop.vertex_index; uv.data[loop.index].uv=((idx%width+.5)/width,(idx//width+.5)/h)
    frame_index=0
    for act_name,source_end in [('A_Idle',61),('A_Walk',31),('A_Attack',46)]:
        rig.animation_data.action=acts[act_name]
        for n in range(24):
            # Loop includes start, omits duplicate end for idle/walk; attack keeps end.
            at=1+n*(source_end-1)/(23 if act_name=='A_Attack' else 24)
            scene.frame_set(int(at),subframe=at-int(at)); bpy.context.view_layer.update()
            evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh()
            if len(mesh.vertices)!=V: raise RuntimeError('VAT topology changed')
            xyz=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float32)
            nn=np.array([tuple(v.normal) for v in mesh.vertices],dtype=np.float32)
            delta=(xyz-rest)*np.array([100,-100,100],np.float32)
            nn*=np.array([1,-1,1],np.float32)
            flat=pos[frame_index*rows:(frame_index+1)*rows].reshape((-1,4)); flat[:V,:3]=delta
            flatn=nor[frame_index*rows:(frame_index+1)*rows].reshape((-1,4)); flatn[:V,:3]=nn*.5+.5
            evaluated.to_mesh_clear(); frame_index+=1
    rig.animation_data.action=acts['A_Neutral']; scene.frame_set(1)
    write_image(f'T_VAT_Position_LOD{lod}',pos,TEX/f'T_VAT_Position_LOD{lod}.exr',True,True)
    write_image(f'T_VAT_Normal_LOD{lod}',nor,TEX/f'T_VAT_Normal_LOD{lod}.exr',True,True)
    # Export raw neutral static geometry; retain rigged crowd source in .blend.
    arm_mod=next((m for m in ob.modifiers if m.type=='ARMATURE'),None)
    if arm_mod: ob.modifiers.remove(arm_mod)
    ob.parent=None
    fbx(EXPORT/f'SM_Samurai01_LOD{lod}.fbx',[ob])
    ob.hide_render=True; ob.hide_set(True)
    vat_info.append({'lod':lod,'vertices':V,'triangles':len(ob.data.polygons),'texture_width':width,'texture_height':h,'rows_per_frame':rows,'frames_per_clip':24,'clips':['idle','walk','attack'],'clip_seconds':[2,1,1.5],'source_to_unreal_position':[100,-100,100]})

# Readable source scene: authoring pieces shown, runtime copies hidden.
for ob in runtime.objects: ob.hide_render=True; ob.hide_set(True)
rig.animation_data.action=acts['A_Idle']; scene.frame_start=1; scene.frame_end=61; scene.frame_set(1)
for ob in objects: ob.hide_render=False; ob.hide_set(False)
select_only([rig]); rig.hide_set(True)
# Studio sweep, warm key and cool fill; camera only renders actual source geometry.
def move_to(ob,col):
    for coll in list(ob.users_collection): coll.objects.unlink(ob)
    col.objects.link(ob)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003)); floor=bpy.context.object; floor.name='Studio floor'; move_to(floor,studio)
fm=bpy.data.materials.new('Studio • slate'); fm.diffuse_color=(.075,.085,.10,1); fm.use_nodes=True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.085,.10,1); fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.87; floor.data.materials.append(fm)
def track(obj,p): obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('Key',(-3,-4,5),550,4,(1,.84,.66)),('Fill',(3,-1,3),350,3,(.69,.81,1)),('Rim',(1,3,4),700,3,(1,.91,.75))]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; data.color=color
    ob=bpy.data.objects.new(name,data); studio.objects.link(ob); ob.location=loc; track(ob,(0,0,1))
data=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',data); studio.objects.link(cam); scene.camera=cam
cam.location=(3.0,-5.4,2.8); track(cam,(0,.03,1.06)); data.type='ORTHO'; data.ortho_scale=2.55
scene.world.color=(.14,.14,.14)
scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
scene.render.resolution_x=1100; scene.render.resolution_y=1300; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# All generated data is reported, including hidden underlying source geometry.
def tris(ob): return sum(max(0,len(p.vertices)-2) for p in ob.data.polygons)
report={'asset':'SHOEN Samurai Prototype01','blender_version':bpy.app.version_string,
 'source_triangles':sum(tris(ob) for ob in objects),'skeletal_body_triangles':tris(body),'bones':len(rig.data.bones),
 'runtime_body_materials':1,'runtime_body_sections_expected':1,'source_components':{ob.name:tris(ob) for ob in objects},
 'textures':'2048x2048 shared BaseColor + tangent Normal + ORM','vat':vat_info,
 'fbx_import':{'convert_scene':False,'convert_scene_unit':True,'force_front_x_axis':False,'runtime_yaw_degrees':-90,'unit':'centimetres in Unreal'},
 'weapon_pivots_blender_metres':{n:list(rig.data.bones[n].head_local) for n in ['bow_socket','sword_socket','sheath_socket','quiver_socket']},
 'limitations':['Original parametric human, no scan or purchased mesh; face is prototype detail.', 'No certified mannequin retarget compatibility: shared humanoid names, original proportions.', 'Attack is a simple guard/thrust motion test; archery release, hit and death are future work.', 'Crowd uses rig-baked vertex animation; skeletal body retained for conventional animation proof.']}
(ROOT/'asset-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
# Give original weapon objects meaningful origins without baking them into body.
for name,socket in [('WPN_Yumi','bow_socket'),('WPN_Tachi','sword_socket'),('WPN_Sheath','sheath_socket'),('PROP_Quiver','quiver_socket'),('PROP_Arrows','quiver_socket')]:
    ob=bpy.data.objects[name]; pivot=rig.data.bones[socket].head_local.copy()
    ob.data.transform(Matrix.Translation(-pivot)); ob.location=pivot
    ob['attachment_bone']=socket
# Pack atlas so .blend remains self-contained; keep external files for engine import.
for im in (color_im,normal_im,orm_im): im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Samurai01.blend'))
scene.render.filepath=str(ROOT/'preview-three-quarter.png')
bpy.ops.render.render(write_still=True)
cam.location=(0,-6,1.4); track(cam,(0,0,1.08)); scene.render.filepath=str(ROOT/'preview-front.png'); bpy.ops.render.render(write_still=True)
cam.location=(2.8,5,2.3); track(cam,(0,.05,1.06)); scene.render.filepath=str(ROOT/'preview-back.png'); bpy.ops.render.render(write_still=True)
print('SHOEN_SAMURAI_GENERATED',json.dumps(report))
