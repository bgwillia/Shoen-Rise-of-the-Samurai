"""Small construction helpers for editable Dō meshes, metres / -Y forward."""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

SOURCE = None
MATERIAL = None

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.hide_set(False); ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

def uvcoord(tile,u,v):
    return ((tile%4+.025+.95*u)/4,(tile//4+.025+.95*v)/4)

def mesh(name,vertices,faces,tile=0,uvs=None,smooth=True):
    data=bpy.data.meshes.new(name); data.from_pydata(vertices,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); SOURCE.objects.link(ob); data.materials.append(MATERIAL)
    layer=data.uv_layers.new(name='UV0_DoAtlas')
    for p in data.polygons:
        p.use_smooth=smooth
        for li,vi in zip(p.loop_indices,p.vertices):
            u,v=uvs[vi] if uvs else ((vertices[vi][0]+.25)/.5,(vertices[vi][2]-.98)/.52)
            layer.data[li].uv=uvcoord(tile,u,v)
    bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    return ob

def solid(ob,thickness=.0028,bevel=.0007):
    mod=ob.modifiers.new('Physical plate thickness','SOLIDIFY'); mod.thickness=thickness; mod.offset=-1
    if bevel:
        mod=ob.modifiers.new('Soft bound edges','BEVEL'); mod.width=bevel; mod.segments=2; mod.limit_method='ANGLE'; mod.angle_limit=.45
    return ob

def tube(name,points,r,tile=3,sides=6,closed=False):
    pts=[Vector(p) for p in points]; n=len(pts); vs=[]; uv=[]; fs=[]; lengths=[0.]
    for a,b in zip(pts,pts[1:]): lengths.append(lengths[-1]+(b-a).length)
    for i,p in enumerate(pts):
        t=(pts[(i+1)%n]-pts[(i-1)%n]) if closed else pts[min(n-1,i+1)]-pts[max(0,i-1)]
        t.normalize(); ref=Vector((0,0,1)) if abs(t.z)<.9 else Vector((0,1,0))
        a=t.cross(ref).normalized(); b=t.cross(a).normalized()
        for j in range(sides):
            f=j*math.tau/sides; vs.append(p+r*(a*math.cos(f)+b*math.sin(f))); uv.append((j/sides,lengths[i]/max(lengths[-1],1e-6)))
    for i in range(n if closed else n-1):
        k=(i+1)%n
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,k*sides+(j+1)%sides,k*sides+j))
    if not closed:fs.extend([tuple(reversed(range(sides))),tuple((n-1)*sides+j for j in range(sides))])
    ob=mesh(name,vs,fs,tile,uv)
    grp=ob.vertex_groups.new(name='Do_Round_Surfaces'); grp.add(list(range(len(vs))),1,'REPLACE')
    data=ob.data.uv_layers.active.data
    for face in ob.data.polygons:
        if face.index<(n if closed else n-1)*sides and face.index%sides==sides-1:
            for li,vi in zip(face.loop_indices,face.vertices):
                if vi%sides==0:data[li].uv=uvcoord(tile,1,lengths[vi//sides]/max(lengths[-1],1e-6))
    return ob

def path(points,steps=4):
    p=[Vector(points[0])]+[Vector(v) for v in points]+[Vector(points[-1])]; result=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for j in range(steps):
            t=j/steps; result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return result+[Vector(points[-1])]

def merge(objects,name):
    for ob in objects:
        select([ob])
        for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    select(objects); bpy.ops.object.join(); ob=bpy.context.object; ob.name=name
    ob.data.materials.clear(); ob.data.materials.append(MATERIAL)
    for p in ob.data.polygons:p.material_index=0
    return ob

def stud(name,p,r=.0022,tile=2):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,location=p)
    ob=bpy.context.object; ob.name=name
    for c in list(ob.users_collection):c.objects.unlink(ob)
    SOURCE.objects.link(ob)
    for v in ob.data.vertices:v.co*=r
    ob.data.materials.append(MATERIAL)
    ob.data.uv_layers.active.name='UV0_DoAtlas'
    for loop in ob.data.uv_layers.active.data:loop.uv=uvcoord(tile,*loop.uv)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def weight(ob,rig,fn=None,per_vertex=None):
    world=ob.matrix_world.copy(); ob.data.transform(world); ob.matrix_world=Matrix.Identity(4)
    # Round-surface group is only an export shading tag, not a deform bone.
    groups={'spine_02':ob.vertex_groups.get('spine_02') or ob.vertex_groups.new(name='spine_02')}
    for v in ob.data.vertices:
        values=per_vertex[v.index] if per_vertex is not None else fn(v.co) if fn else {'spine_02':1.}
        for name,w in values.items():
            if w<=1e-7:continue
            if name not in groups:groups[name]=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
            groups[name].add([v.index],w,'REPLACE')
    # Manny's original exported root retains .01 scale and centimetre data.
    # Keep that native rest skeleton unchanged and move armor data into its space.
    ob.data.transform(rig.matrix_world.inverted())
    ob.parent=rig; ob.matrix_parent_inverse=Matrix.Identity(4); ob.matrix_basis=Matrix.Identity(4)
    mod=ob.modifiers.new('Native Manny skeleton','ARMATURE'); mod.object=rig
    ob['asset']='Do01'
