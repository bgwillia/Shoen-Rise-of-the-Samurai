"""Build only Kusazuri01. Use export_kusazuri.py to export later manual edits."""
from pathlib import Path
import sys, math, json, hashlib
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[3]
DO=ART.parent/'Do01'; SODE=ART.parent/'Sode01'
sys.path.insert(0,str(DO/'Scripts'))
import do_geometry as g
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
source=collection('Kusazuri01_Source');fit=collection('Kusazuri01_Fit');runtime=collection('Kusazuri01_Runtime');studio=collection('Kusazuri01_Studio')
with bpy.data.libraries.load(str(SODE/'Sode01.blend'),link=False) as (a,b):
    b.objects=['root','Manny_Review','Kabuto_Review']+[n for n in a.objects if n.startswith(('Do_Review_','Sode_L_01_','Sode_R_01_'))]
    b.actions=['A_Idle','A_Walk','A_Run','A_Attack'];b.materials=['M_Sode01']
for ob in b.objects:
    if ob:
        fit.objects.link(ob);ob.hide_set(False);ob.hide_render=ob.type=='ARMATURE'
        if ob.name.startswith('Sode_'):ob.name='Sode_Review_'+ob.name[5:]
for a in b.actions:a.use_fake_user=True
rig=bpy.data.objects['root'];rig.animation_data_clear();rig.data.pose_position='REST';scene.frame_set(1)
for ob in fit.objects:
    for mod in ob.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
bpy.context.view_layer.update()
g.SOURCE=source;g.MATERIAL=bpy.data.materials.get('M_Sode01')
if g.MATERIAL is None:
    sys.path.insert(0,str(SODE/'Scripts'))
    from sode_material import build_material
    g.MATERIAL=build_material(bpy.data.materials['M_Do01'])
g.MATERIAL=g.MATERIAL.copy();g.MATERIAL.name='M_Kusazuri01'
# Indigo lining and woven obi reuse the unchanged shared atlas pixels.
for node in g.MATERIAL.node_tree.nodes:
    if node.type=='VALTORGB' and node.label.startswith('Lacquer'):
        min(node.color_ramp.elements,key=lambda e:abs(e.position-(12-.1)/15)).color=(.10,.18,.48,1)
nodes=g.MATERIAL.node_tree.nodes;links=g.MATERIAL.node_tree.links;bs=nodes.get('Principled BSDF')
base=next(n for n in nodes if n.type=='TEX_IMAGE' and 'BaseColor' in n.image.name)
prior=bs.inputs['Base Color'].links[0].from_socket
mask=nodes.new('ShaderNodeVertexColor');mask.layer_name='ArmorTint'
sep=nodes.new('ShaderNodeSeparateColor');links.new(mask.outputs['Color'],sep.inputs[0])
gray=nodes.new('ShaderNodeVectorMath');gray.operation='DOT_PRODUCT';gray.inputs[1].default_value=(.3,.59,.11);links.new(base.outputs['Color'],gray.inputs[0])
blue=nodes.new('ShaderNodeMixRGB');blue.blend_type='MULTIPLY';blue.inputs[0].default_value=1;blue.inputs[2].default_value=(.08,.18,.50,1);links.new(gray.outputs['Value'],blue.inputs[1])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(sep.outputs['Red'],mix.inputs[0]);links.new(blue.outputs[0],mix.inputs[1]);links.new(prior,mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
# Restrict the cloth response to quilted tile12. At the underside's grazing
# angles even specular .05 washed out the indigo; zero retains the cloth color.
# The original lacquer, brass, cords, leather and normal strength stay intact.
palette=next(n for n in nodes if n.type=='VALTORGB' and n.label.startswith('Lacquer'))
tile_index=nodes.new('ShaderNodeMath');tile_index.operation='MULTIPLY';tile_index.inputs[1].default_value=15
links.new(palette.inputs[0].links[0].from_socket,tile_index.inputs[0])
lining_mask=nodes.new('ShaderNodeMath');lining_mask.operation='COMPARE';lining_mask.label='Kusazuri lining tile12 only'
lining_mask.inputs[1].default_value=12;lining_mask.inputs[2].default_value=.1
links.new(tile_index.outputs[0],lining_mask.inputs[0])
for field,value in [('Roughness',.90),('Metallic',0.),('Specular IOR Level',0.)]:
    socket=bs.inputs[field];original=socket.links[0].from_socket if socket.is_linked else None
    response=nodes.new('ShaderNodeMixRGB');response.blend_type='MIX';response.label='Kusazuri lining '+field
    links.new(lining_mask.outputs[0],response.inputs[0])
    if original:links.new(original,response.inputs[1])
    else:response.inputs[1].default_value=(socket.default_value,)*3+(1,)
    response.inputs[2].default_value=(value,value,value,1)
    links.new(response.outputs[0],socket)
for node in nodes:
    if node.type=='TEX_IMAGE' and node.image:node.image.pack()
POWER=2.8
PANELS=[('Front_Center','spine_01',0,.34),('Front_L','thigh_l',.84,.41),('Front_R','thigh_r',-.84,.41),('Side_L','thigh_twist_01_l',1.70,.40),('Side_R','thigh_twist_01_r',-1.70,.40),('Rear_L','thigh_twist_02_l',2.64,.45),('Rear_R','thigh_twist_02_r',-2.64,.45)]
def ring(theta,z,rx=.184,ry=.148,offset=0):
    sn,cs=math.sin(theta),math.cos(theta)
    return Vector(((rx+offset)*math.copysign(abs(sn)**(2/POWER),sn),-.014-(ry+offset)*math.copysign(abs(cs)**(2/POWER),cs),z))
def outward(theta):return Vector((math.sin(theta),-math.cos(theta),0)).normalized()
def closed_surface(name,vs,fs,tile,uv,n,thickness=.003,bevel=.00045):
    ob=g.mesh(name,vs,fs,tile,uv,smooth=tile in (8,9,13,14))
    if sum(p.normal.dot(n) for p in ob.data.polygons)<0:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    result=g.solid(ob,thickness,bevel)
    for mod in result.modifiers:
        if mod.type=='BEVEL':mod.segments=1
    return result
def finish(obs,name,bone,panel):
    ob=g.merge(obs,'Kusazuri_01_'+name)
    g.weight(ob,rig,lambda p:{bone:1.})
    ob['asset']='Kusazuri01';ob['panel']=panel;ob['rigid_bone']=bone
    attr=ob.data.color_attributes.new(name='ArmorTint',type='FLOAT_COLOR',domain='CORNER')
    rgba=(0,0,0,1) if name=='Lacing' else (1,1,1,1)
    for c in attr.data:c.color=rgba
    return ob
def fast_merge(objects,name):
    # Evaluate each modifier stack once; applying operators per primitive
    # rebuilt the shared material/fixture dependency graph thousands of times.
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();copies=[]
    for ob in objects:
        data=bpy.data.meshes.new_from_object(ob.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
        data.transform(ob.matrix_world)
        copy=bpy.data.objects.new(ob.name+'_evaluated',data);source.objects.link(copy)
        for group in ob.vertex_groups:copy.vertex_groups.new(name=group.name)
        copies.append(copy)
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
    g.select(copies)
    if len(copies)>1:bpy.ops.object.join()
    result=bpy.context.object;result.name=name;result.data.materials.clear();result.data.materials.append(g.MATERIAL)
    for poly in result.data.polygons:poly.material_index=0
    return result

def direct_stud(name,p,r=.0022,tile=2):
    p=Vector(p);vs=[p+Vector((0,0,r))];uv=[(.5,1)];fs=[]
    for j in range(1,4):
        phi=math.pi*j/4
        for i in range(8):
            a=math.tau*i/8;vs.append(p+Vector((r*math.sin(phi)*math.cos(a),r*math.sin(phi)*math.sin(a),r*math.cos(phi))))
            uv.append((i/8,1-j/4))
    vs.append(p+Vector((0,0,-r)));uv.append((.5,0))
    for i in range(8):fs.append((0,1+i,1+(i+1)%8))
    for j in range(2):
        for i in range(8):a=1+j*8+i;b=1+j*8+(i+1)%8;fs.append((a,a+8,b+8,b))
    for i in range(8):fs.append((25,17+(i+1)%8,17+i))
    ob=g.mesh(name,vs,fs,tile,uv,True)
    group=ob.vertex_groups.new(name='Do_Round_Surfaces');group.add(list(range(len(vs))),1,'REPLACE')
    return ob

g.merge=fast_merge;g.stud=direct_stud
components=[];records=[]
for name,bone,theta,half in PANELS:
    print('Building panel '+name,flush=True)
    n=outward(theta);groups={k:[] for k in ['Shell','Lacing','Interior','Trim']}
    height=.324 if name.startswith('Side') else .338 if name.startswith('Rear') else .332
    pivot=ring(theta,1.006)
    def point(u,v,offset=0):
        # Each shield widens slightly as it falls away from the hips.
        t=theta+u*half*(1+.025*v)
        p=ring(t,1.006-height*v,.184+.070*v,.148+.054*v,offset)
        return p
    def plate(label,ua,ub,va,vb,tile=0,offset=0,thick=.003,cols=2):
        vs=[];uv=[];fs=[];detailed=tile in (8,9,13,14);rows=4 if detailed else 1
        for j in range(rows+1):
            f=j/rows;v=va+(vb-va)*f
            for i in range(cols+1):
                u=i/cols;across=ua+(ub-ua)*u
                relief=(-.0055*(1-f)**4+.0008*math.sin(f*math.pi)+.0006*math.sin(u*math.pi)) if detailed else -.0025*(1-f)
                vs.append(point(across,v,offset+relief));uv.append((u,1-f))
        for j in range(rows):
            for i in range(cols):
                a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
        return closed_surface(label,vs,fs,tile,uv,n,.0023 if detailed else thick,0 if detailed else .00045)
    # Seven courses with overlapping lower edges. Slender lamellae are real
    # closed shells; fine cord texture is reused from the established atlas.
    cols=11 if name!='Front_Center' else 10
    for row in range(7):
        va=.045+row*.126;vb=va+.151;off=row*.0009
        for col in range(cols):
            ua=-1+2*col/cols+.006;ub=-1+2*(col+1)/cols-.006
            groups['Shell'].append(plate('Formed lacquer lamella',ua,ub,va,vb,[8,9,13,14][(col+row*3)%4],off))
            # A sparse physical braid pair aligns with the detailed atlas;
            # tiny fibers, holes and most fastenings remain normal-map detail.
            if col%4==1:
                for f in [.34,.64]:
                    u=ua+(ub-ua)*f
                    for first,last in [(.10,.35),(.55,.80)]:
                        pts=[point(u,va+(vb-va)*first,off+.001),point(u-.0008,va+(vb-va)*(first*.67+last*.33),off+.0037),point(u+.0008,va+(vb-va)*(first*.33+last*.67),off+.004),point(u,va+(vb-va)*last,off+.002)]
                        groups['Lacing'].append(g.tube('Fine silk braid over atlas fastening',g.path(pts,2),.00125,3,6))
        edge=[point(-1+2*i/18,vb,off+.0014) for i in range(19)]
        groups['Trim'].append(g.tube('Black rolled course edge',edge,.0021,0,6))
        if row in [0,6]:
            groups['Trim'].append(g.tube('Muted brass tracer',[p+n*.0013 for p in edge],.00065,2,5))
        for u in [-.95,.95]:
            groups['Trim'].append(plate('Bound side edge',u-.025,u+.025,va+.012,vb-.012,11,off+.002,.0014,1))
            for v in [va+.025,vb-.024]:groups['Trim'].append(g.stud('Peened edge rivet',point(u,v,off+.004),.00165))
    # One broad, restrained chased hem matching the sheet's gold lower border.
    groups['Trim'].append(plate('Chased lower reinforcement',-.985,.985,.941,.997,10,.009,.0016,12))
    for v in [.943,.994]:groups['Trim'].append(g.tube('Hem border',[point(-.985+1.97*i/22,v,.011) for i in range(23)],.00085,2,5))
    for u in [-.65,-.22,.22,.65]:
        diamond=[point(u-.09,.969,.012),point(u,.951,.012),point(u+.09,.969,.012),point(u,.987,.012)]
        groups['Trim'].append(g.tube('Raised diamond hem motif',diamond,.00085,2,5,True))
        groups['Trim'].append(g.stud('Small ornament boss',point(u,.969,.013),.0015))
    for u in [-.91,.91]:groups['Trim'].append(g.stud('Hem rivet',point(u,.969,.013),.0023))
    # Simplified closed lining, with a subtle quilt profile and bound perimeter.
    vs=[];uv=[];fs=[];nx=8;ny=14
    for j in range(ny+1):
        v=-.015+1.009*j/ny
        for i in range(nx+1):
            u=-.975+1.95*i/nx
            puff=.0015*math.sin(math.pi*i/2)**2*math.sin(math.pi*j/2)**2
            vs.append(point(u,v,-.006-puff));uv.append((i/nx,j/ny))
    for j in range(ny):
        for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
    groups['Interior'].append(closed_surface('Indigo padded backing',vs,fs,12,uv,n,.002,.00035))
    for u in [-.98,.98]:groups['Interior'].append(g.tube('Leather-bound inner edge',[point(u,-.015+1.007*i/14,-.007) for i in range(15)],.0021,4,6))
    # Visible short suspension tabs disappear underneath the independent belt.
    for u in [-.67,.67]:groups['Trim'].append(plate('Upper leather suspension',u-.08,u+.08,-.005,.102,4,-.003,.002,1))
    for key,obs in groups.items():
        ob=finish(obs,name if key=='Shell' else name+'_'+key,bone,name);components.append(ob)
    records.append({'name':name,'bone':bone,'theta':theta,'half_angle':half,'height_m':height,'hinge_metres':list(pivot),'radial_blender':list(n),'rows':7,'lamellae_per_row':cols})
# Separate belt under the Dō, tucked 8mm into its lower edge. Narrow reveal
# avoids a double-thickness waist; it supports the seven hanging shields.
belt=[];cords=[]
for j in range(48):
    a=math.tau*j/48;b=math.tau*(j+1)/48
    vs=[ring(a,1.023,.182,.145),ring(b,1.023,.182,.145),ring(b,1.009,.184,.148),ring(a,1.009,.184,.148)]
    belt.append(closed_surface('Bound lacquer and leather attachment belt',vs,[(0,1,2,3)],10,[(0,1),(1,1),(1,0),(0,0)],outward((a+b)/2),.0035,.0004))
# Fine chased facing on the exposed upper belt; supported by the leather core.
for j in range(32):
    a=math.tau*j/32;b=math.tau*(j+1)/32
    vs=[ring(a,1.021,.185,.149),ring(b,1.021,.185,.149),ring(b,1.014,.185,.149),ring(a,1.014,.185,.149)]
    belt.append(closed_surface('Chased upper belt facing',vs,[(0,1,2,3)],11,[(0,1),(1,1),(1,0),(0,0)],outward((a+b)/2),.001,0))
for z,r,tile in [(1.021,.001,2),(1.010,.0014,0)]:
    belt.append(g.tube('Belt binding',[ring(math.tau*i/80,z,.186,.149) for i in range(80)],r,tile,6,True))
# Two physically braided obi cords. Woven atlas3 is selectively indigo via
# the vertex mask, so it has cord fibers instead of leather/quilted texture.
sys.path.insert(0,str(SODE/'Scripts'))
from sode_finish import braided_cord,wrapped_knot
for dz in [-.0045,.0045]:
    pts=[ring(math.tau*i/96,1.017+dz,.191,.155) for i in range(97)]
    cords.append(braided_cord(g,'Indigo braided obi',pts,radius=.0045,pitch=.014,strands=2,sides=5,steps_per_turn=5,tile=3))
center=Vector((0,-.181,1.017))
for sign in [-1,1]:
    pts=g.path([center,center+Vector((sign*.025,-.010,.018)),center+Vector((sign*.055,-.002,.009)),center+Vector((sign*.042,-.005,-.006)),center+Vector((sign*.010,-.012,-.005))],6)
    cords.append(braided_cord(g,'Braided obi loop',pts,radius=.005,pitch=.012,strands=2,tile=3))
    pts=g.path([center+Vector((sign*.006,-.007,0)),center+Vector((sign*.022,-.021,-.026)),center+Vector((sign*.020,-.016,-.052)),center+Vector((sign*.032,-.018,-.065))],5)
    cords.append(braided_cord(g,'Hanging obi tail',pts,radius=.004,pitch=.010,strands=2,tile=3))
    cords.append(wrapped_knot(g,'Tassel binding',pts[-1]+Vector((0,0,.004)),(0,0,1),(0,-1,0),bundle_radius=.004,cord_radius=.0008,turns=4,spacing=.0015,tile=3))
    for k in range(11):
        off=(k-5)*.0007
        tip=pts[-1]+Vector((off*1.5,-.001,-.013-.0015*math.sin(k*1.7)))
        cords.append(g.tube('Gathered silk tassel',[pts[-1]+Vector((off,0,0)),(pts[-1]+tip)/2+Vector((0,-.001,0)),tip],.00038,3,5))
cords.append(wrapped_knot(g,'Obi central bound knot',center+Vector((0,-.010,0)),(0,0,1),(0,-1,0),bundle_radius=.010,cord_radius=.0025,turns=4,spacing=.0031,tile=3))
components.append(finish(belt,'Belt','pelvis','Belt'));components.append(finish(cords,'Lacing','pelvis','Belt'))
# Reuse established export shading conventions without changing source weights.
sys.path.insert(0,str(ART.parent/'Kabuto01/Scripts'))
import kabuto_export_common as common
common.ROUND_GROUP='Do_Round_Surfaces'
for ob in components:common.surface_normals(ob)
def aim(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,color in [('Key',(-1.2,-1.6,2.1),160,1.1,(1,.88,.75)),('Fill',(1.4,-.8,1.7),110,1.2,(.77,.87,1)),('Rim',(0,.8,2.1),160,1,(1,.89,.72))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc;aim(ob,(0,0,.95))
world=bpy.data.worlds.new('Neutral armor review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.145,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
camdata=bpy.data.cameras.new('Kusazuri review');cam=bpy.data.objects.new('Kusazuri review',camdata);studio.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=1.9
cam.location=(1.0,-2.5,1.65);aim(cam,(0,0,1.13))
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=1.9;area.spaces.active.region_3d.view_location=(0,0,1.05)
g.select([components[0]])
manifest={'asset':'Kusazuri01','blender_version':bpy.app.version_string,'source_collection':source.name,'source_components':{o.name:common.triangles(o) for o in components},'source_component_objects':len(components),'source_triangles_before_modifiers':sum(common.triangles(o) for o in components),'source_materials':1,'runtime_materials':1,'shared_material':'M_Kusazuri01','material_base':'M_Sode01','material_variant':'Indigo quilted tile12 and woven obi masked by ArmorTint vertex color; existing textures unchanged','texture_dimensions':[2048,2048],'source_bone_count':len(rig.data.bones),'native_reference_bone_count':89,'panels':records,'major_panel_count':7,'attachment_method':'Seven rigid leaf panels and pelvis belt; armor-only stateless hinge poses use unchanged native spine_01 and thigh/twist channels. One full-weight influence per rigid section. No skeleton edit or physics.','review_contract':json.loads((DO/'asset-manifest.json').read_text())['review_contract'],'dependencies':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DO/'Do01.blend',SODE/'Sode01.blend',ROOT/'SourceArt/Characters/Mannequins/Manny/Manny.blend',ART.parent/'Kabuto01/Kabuto01.blend']}}
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Kusazuri01.blend'))
manifest['source_blend_sha256']=hashlib.sha256((ART/'Kusazuri01.blend').read_bytes()).hexdigest()
(ART/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--no-render' not in sys.argv:
    scene.render.filepath=str(ART/'Review/Captures/fit-initial.png');bpy.ops.render.render(write_still=True)
    for ob in fit.objects:ob.hide_render=True
    cam.data.ortho_scale=.73;cam.location=(.65,-1.5,1.25);aim(cam,(0,0,.86))
    scene.render.filepath=str(ART/'Review/Captures/component-initial.png');bpy.ops.render.render(write_still=True)
print('KUSAZURI_SOURCE_COMPLETE '+json.dumps({'source_triangles':manifest['source_triangles_before_modifiers'],'panels':7,'objects':len(components)}),flush=True)
