"""Fitted tabi, ankle bindings and woven sandals, in unweighted world metres.

Uses the native Manny review surface only as a fit reference. It never changes
that surface, its skeleton, or existing armor. Tile 7 is the rope region.
"""
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _hull(points):
    pts=sorted(set((round(p[0],7),round(p[1],7)) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]


def build_footwear(g,rig,side,sign):
    """Return category -> mesh objects; caller merges and assigns bone weights.

    FootCovering, WovenSole and SandalStraps follow foot_<side>. AnkleWraps
    should blend foot to calf from z=.085 to .16. No bone groups are assigned
    here except the geometry helper's optional nondeforming shading tag.
    """
    sode_scripts=str(Path(__file__).resolve().parents[2]/'Sode01/Scripts')
    if sode_scripts not in sys.path:sys.path.insert(0,sode_scripts)
    from sode_finish import braided_cord
    groups={k:[] for k in ('FootCovering','FootEmbroidery','WovenSole','SandalStraps','AnkleWraps')}
    def add(key,ob):groups[key].append(ob);return ob
    body=bpy.data.objects['Manny_Review']
    world=[body.matrix_world@v.co for v in body.data.vertices]
    # Work in the canonical left-foot space; all output is anatomically mirrored.
    points=[Vector((abs(p.x),p.y,p.z)) for p in world]
    chosen=[f for f in body.data.polygons if all(sign*world[i].x>.035 for i in f.vertices)]
    footfaces=[tuple(f.vertices) for f in chosen if min(points[i].z for i in f.vertices)<.18]
    tree=BVHTree.FromPolygons(points,footfaces,all_triangles=False)
    def W(p):return Vector((sign*p[0],p[1],p[2]))
    def tube(key,name,ps,r,tile=7,sides=6,closed=False):
        return add(key,g.tube(side+' '+name,[W(p) for p in ps],r,tile,sides,closed))
    toe_caps=[('great toe',.139,-.193,.019,.033,.023),('outer toes',.172,-.183,.034,.041,.025)]
    def top(x,y,off=.005,include_caps=False):
        loc,normal,idx,d=tree.ray_cast(Vector((x,y,.24)),Vector((0,0,-1)),.3)
        height=loc.z if loc is not None else None
        if include_caps:
            for _,cx,cy,rx,ry,rz in toe_caps:
                radial=1-((x-cx)/rx)**2-((y-cy)/ry)**2
                if radial>=0:
                    cap=.023+rz*math.sqrt(radial)
                    height=cap if height is None else max(height,cap)
        return None if height is None else Vector((x,y,height+off))
    def cloth_uv(ob,tile):
        # Per-face projection gives upright sides their own noncollapsed islands.
        layer=ob.data.uv_layers.active.data
        for face in ob.data.polygons:
            axis=max(range(3),key=lambda i:abs(face.normal[i]))
            for li,vi in zip(face.loop_indices,face.vertices):
                p=ob.data.vertices[vi].co;x=abs(p.x)
                if axis==2:u,v=(x-.09)/.145,(p.y+.24)/.32
                elif axis==0:u,v=(p.y+.24)/.32,(p.z+.015)/.21
                else:u,v=(x-.09)/.145,(p.z+.015)/.21
                layer[li].uv=g.uvcoord(tile,max(.015,min(.985,u)),max(.015,min(.985,v)))

    # A thin padded textile covering preserves the existing fitted foot shape.
    # Separate the ankle section so it can receive a calf/foot weight transition.
    normalmat=body.matrix_world.to_3x3().inverted().transposed()
    for category,low,high in [('FootCovering',-.02,.104),('AnkleWraps',.098,.174)]:
        faces=[f for f in chosen if min(world[i].z for i in f.vertices)<high and max(world[i].z for i in f.vertices)>low and max(world[i].z for i in f.vertices)<.19]
        ids=sorted({i for f in faces for i in f.vertices});mapping={old:n for n,old in enumerate(ids)}
        vv=[];uv=[]
        for i in ids:
            p=world[i].copy();n=(normalmat@body.data.vertices[i].normal).normalized()
            # Minute tension wrinkles and softly padded fabric, not hard boot plates.
            wrinkle=.00038*math.sin(p.y*155+p.z*115)*math.sin(p.x*165)
            p+=n*(.0032+wrinkle);vv.append(p)
            uv.append(((abs(p.x)-.095)/.13,(p.y+.23)/.31))
        fs=[tuple(mapping[i] for i in f.vertices) for f in faces]
        ob=g.mesh(side+' fitted indigo tabi '+category,vv,fs,11 if category=='FootCovering' else 3,uv)
        cloth_uv(ob,11 if category=='FootCovering' else 3)
        add(category,ob)
    # Two tailored toe caps introduce the tabi split beyond the fitted body tip.
    # Their rear portions disappear into the padded shell; no body is removed.
    for name,cx,cy,rx,ry,rz in toe_caps:
        vv=[];uv=[];fs=[]
        for j in range(13):
            a=math.pi*(.015+.97*j/12)
            for i in range(32):
                t=math.tau*i/32
                p=Vector((cx+rx*math.sin(a)*math.cos(t),cy+ry*math.cos(a),.023+rz*math.sin(a)*math.sin(t)))
                vv.append(W(p));uv.append((i/32,j/12))
        for j in range(12):
            for i in range(32):
                n=(i+1)%32;fs.append((j*32+i,j*32+n,(j+1)*32+n,(j+1)*32+i))
        fs.extend([tuple(reversed(range(32))),tuple(384+i for i in range(32))])
        ob=g.mesh(side+' tailored split tabi '+name,vv,fs,11,uv)
        layer=ob.data.uv_layers.active.data
        for face in ob.data.polygons:
            for li,vi in zip(face.loop_indices,face.vertices):
                if face.index<384:
                    u=(vi%32)/32
                    if face.index%32==31 and vi%32==0:u=1
                    v=(vi//32)/12
                else:
                    p=ob.data.vertices[vi].co
                    u=.5+(abs(p.x)-cx)/(2*rx);v=.5+(p.z-.023)/(2*rz)
                layer[li].uv=g.uvcoord(11,.015+.97*u,.015+.97*v)
        add('FootCovering',ob)
    # The sole follows Manny's actual foot outline, with a narrow rope allowance.
    solepts=[p for i,p in enumerate(points) if sign*world[i].x>.035 and p.z<.028]
    outline=_hull(solepts);cent=Vector((sum(p[0] for p in outline)/len(outline),sum(p[1] for p in outline)/len(outline)))
    outline=[Vector(p)+(Vector(p)-cent).normalized()*.006 for p in outline]
    lengths=[0.]
    for i,p in enumerate(outline):lengths.append(lengths[-1]+(outline[(i+1)%len(outline)]-p).length)
    def edge(t):
        dist=(t%1)*lengths[-1]
        for i in range(len(outline)):
            if dist<=lengths[i+1]:return outline[i].lerp(outline[(i+1)%len(outline)],(dist-lengths[i])/(lengths[i+1]-lengths[i]))
        return outline[0]
    ring=[edge(i/112) for i in range(112)]
    vv=[];uv=[]
    for z in [-.0105,-.004,.0030]:
        for i,p in enumerate(ring):
            vv.append(W((p.x,p.y,z)));uv.append((i/112,(z+.0105)/.0135))
    fs=[]
    for j in range(2):
        for i in range(112):n=(i+1)%112;fs.append((j*112+i,j*112+n,(j+1)*112+n,(j+1)*112+i))
    fs.extend([tuple(reversed(range(112))),tuple(224+i for i in range(112))])
    add('WovenSole',g.mesh(side+' closely woven sandal foundation',vv,fs,7,uv))
    # Three helical strands produce an actual braided silhouette at two heights.
    for height in [-.007,.0005]:
        for strand in range(3):
            ps=[]
            for i in range(336):
                t=i/336;p=edge(t);tangent=(edge(t+.001)-edge(t-.001)).normalized();out=Vector((tangent.y,-tangent.x))
                phase=math.tau*(t*38+strand/3)
                xy=p+out*(.00135*math.cos(phase))
                ps.append((xy.x,xy.y,height+.00135*math.sin(phase)))
            tube('WovenSole','three strand braided sole edge',ps,.00115,7,5,True)
    def bounds(y):
        xs=[]
        for a,b in zip(outline,outline[1:]+outline[:1]):
            if min(a.y,b.y)<=y<max(a.y,b.y):xs.append(a.x+(b.x-a.x)*(y-a.y)/(b.y-a.y))
        return (min(xs),max(xs)) if len(xs)>=2 else None
    # Transverse weft is exposed at the edge and under the sole; fine fibers are texture.
    for row in range(45):
        y=-.213+row*.0061;ab=bounds(y)
        if not ab:continue
        a,b=ab
        ps=[(a+(b-a)*i/16,y+.00065*math.sin(i*math.pi),-.0112+.00045*math.cos(i*math.pi)) for i in range(17)]
        tube('WovenSole','closely set straw weft',ps,.00125,7,5)
    # Sewn split-toe construction: a recessed dark seam between two raised welt edges.
    seam=[]
    for j in range(22):
        y=-.220+j*.0030;ab=bounds(y)
        if ab:
            x=.153+.035*(y+.207);p=top(x,y,.0047,include_caps=True)
            if p is not None:seam.append(p)
    if len(seam)>2:
        tube('FootCovering','split toe stitched recess',seam,.00165,4,7)
        for delta in [-.0024,.0024]:
            tube('FootCovering','split toe raised indigo welt',[(p.x+delta,p.y,p.z+.0003) for p in seam],.00075,12,5)
        for p in seam[2:-2:2]:
            tube('FootEmbroidery','fine split toe stitch',[(p.x-.0027,p.y,p.z+.0008),(p.x+.0027,p.y,p.z+.0008)],.00032,7,4)
    # Restrained, stitched diamond brocade panels on the indigo vamp.
    for row,yc in enumerate([-.173,-.139,-.105]):
        xc=.155-.035*(yc+.14)
        for column in [-1,1]:
            cx=xc+column*.0175;ps=[]
            for a in range(40):
                t=math.tau*a/40;x=cx+.012*math.cos(t);y=yc+.019*math.sin(t)
                p=top(x,y,.0045)
                if p is not None:ps.append(p)
            if len(ps)==40:
                tube('FootEmbroidery','ochre stitched leaf medallion',ps,.00036,7,4,True)
                ps=[]
                for x,y in [(cx,yc-.014),(cx+.008,yc),(cx,yc+.014),(cx-.008,yc)]:
                    p=top(x,y,.0046)
                    if p is not None:ps.append(p)
                if len(ps)==4:tube('FootEmbroidery','fine diamond embroidery',ps,.00034,7,4,True)
    # Genuine crossing sandal cords follow the upper foot surface.
    def fitted_path(coords,lift=.008):
        path=g.path([(x,y,0) for x,y in coords],6);result=[]
        for p in path:
            q=top(p.x,p.y,lift)
            if q is not None:result.append(q)
        return result
    for coords in [[(.143,-.173),(.151,-.149),(.172,-.116),(.196,-.081)],[(.143,-.173),(.143,-.143),(.134,-.111),(.121,-.074)],[(.120,-.092),(.141,-.075),(.166,-.060),(.186,-.045)],[(.191,-.091),(.170,-.074),(.146,-.058),(.118,-.036)]]:
        path=fitted_path(coords)
        if len(path)>2:
            add('SandalStraps',braided_cord(g,side+' twisted crossing sandal cord',
                [W(p) for p in path],radius=.0028,pitch=.008,strands=2,sides=5,tile=7))
    # Ankle contours are sampled from the actual unchanged body at each height.
    edge_ids={tuple(sorted((a,b))) for f in chosen for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]) if min(world[a].z,world[b].z)<.19 and max(world[a].z,world[b].z)>.075}
    slices=[]
    for j in range(20):
        z=.075+j*.0055;inter=[]
        for a,b in edge_ids:
            p,q=points[a],points[b]
            if min(p.z,q.z)<=z<max(p.z,q.z):inter.append(p.lerp(q,(z-p.z)/(q.z-p.z)))
        slices.append((z,_hull(inter)))
    def ankle(theta,z,off=.0045):
        d=Vector((math.sin(theta),-math.cos(theta)));center=Vector((.143,.010));radii=[]
        for h,poly in slices:
            radius=.04
            for a,b in zip(poly,poly[1:]+poly[:1]):
                a=Vector(a)-center;b=Vector(b)-center;e=b-a
                den=d.x*e.y-d.y*e.x
                if abs(den)<1e-8:continue
                t=(a.x*e.y-a.y*e.x)/den;u=(a.x*d.y-a.y*d.x)/den
                if t>0 and 0<=u<=1:radius=max(radius,t)
            radii.append(radius)
        f=max(0,min(len(slices)-1.001,(z-.075)/.0055));k=int(f);radius=radii[k]*(1-(f-k))+radii[k+1]*(f-k)
        p=center+d*(radius+off);return Vector((p.x,p.y,z))
    # Wide, overlapping textile bindings with a real rolled edge at each wrap.
    for row in range(4):
        za=.088+row*.018
        vv=[];uv=[]
        for j in range(3):
            for i in range(81):
                t=math.tau*i/80;z=za+j*.0065+.005*math.sin(t+.5)
                vv.append(W(ankle(t,z,.0045+row*.0002)));uv.append((i/80,j/2))
        fs=[(j*81+i,j*81+i+1,(j+1)*81+i+1,(j+1)*81+i) for j in range(2) for i in range(80)]
        add('AnkleWraps',g.mesh(side+' overlapped indigo ankle binding',vv,fs,3,uv))
        tube('AnkleWraps','soft bound wrap seam',[ankle(math.tau*i/96,za+.013+.005*math.sin(math.tau*i/96+.5),.0053) for i in range(96)],.0009,12,6,True)
    # Heel retaining cords climb from the sole to the ankle bindings.
    for angle in [1.7,-1.7]:
        ps=[ankle(angle,.083,.007),ankle(angle+.25,.105,.007),ankle(angle+.75,.125,.007),ankle(angle+1.15,.141,.007)]
        tube('AnkleWraps','heel retaining rope',g.path(ps,7),.0021,7,6)
    # Compact outer knot and two short ends, clearly tied to the wrapping.
    for phase in [0,math.pi]:
        ps=[]
        for i in range(33):
            t=math.tau*i/32;ps.append(ankle(1.5+.16*math.sin(t),.130+.009*math.sin(t+phase),.010+.003*math.cos(t)))
        tube('AnkleWraps','outer ankle tie knot',ps,.0018,12,6)
    for delta in [-.07,.07]:
        tube('AnkleWraps','short bound knot tail',g.path([ankle(1.5,.13,.011),ankle(1.5+delta,.119,.010),ankle(1.5+delta*2,.108,.008)],5),.0018,12,6)
    return groups
