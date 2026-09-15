"""Rebuild the matched Sode01 source. Saved-source export is a separate operation."""
from pathlib import Path
import sys, math, json, hashlib
import bpy, bmesh
from mathutils import Vector, Matrix
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[3]
sys.path.insert(0,str(ART/'Scripts'))
import sode_geometry as g
from sode_finish import braided_cord, wrapped_knot
from sode_material import build_material
DO=ART.parent/'Do01'; MANNY=ROOT/'SourceArt/Characters/Mannequins/Manny'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1; scene.render.fps=30
for d in ['Textures','Exports','Review/Exports','Review/Captures']:(ART/d).mkdir(parents=True,exist_ok=True)
def collection(name):
    col=bpy.data.collections.new(name);scene.collection.children.link(col);return col
source=collection('Sode01_Source');fit=collection('Sode01_Fit');runtime=collection('Sode01_Runtime');studio=collection('Sode01_Studio')
# Append the existing fit rig, body, helmet, and source Dō without changing them.
with bpy.data.libraries.load(str(DO/'Do01.blend'),link=False) as (a,b):
    b.objects=['root','FIT_Manny','FIT_Kabuto01']+[n for n in a.objects if n.startswith('Do_') and not n.startswith('Do review')]
    b.actions=['A_Idle','A_Walk','A_Run','A_Attack'];b.materials=['M_Do01']
for ob in b.objects:
    if ob is not None:fit.objects.link(ob);ob.hide_set(False);ob.hide_render=False
for action in b.actions:action.use_fake_user=True
rig=bpy.data.objects['root'];body=bpy.data.objects['FIT_Manny'];helmet=bpy.data.objects['FIT_Kabuto01']
body.name='Manny_Review';helmet.name='Kabuto_Review'
for ob in fit.objects:
    if ob.name.startswith('Do_'):ob.name='Do_Review_'+ob.name[3:]
    for mod in ob.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
rig.animation_data_clear();rig.data.pose_position='REST';scene.frame_set(1);bpy.context.view_layer.update()
mat=build_material(bpy.data.materials['M_Do01']);g.SOURCE=source;g.MATERIAL=mat
# Reuse the exact Dō atlas pixels, retained packed in the editable source.
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image:node.image.pack()
parts={};frames={}
for side,sign in [('L',1),('R',-1)]:
    bone='upperarm_'+side.lower();shoulder=rig.matrix_world@rig.data.bones[bone].head_local
    elbow=rig.matrix_world@rig.data.bones['lowerarm_'+side.lower()].head_local
    down=(elbow-shoulder).normalized(); outward=Vector((sign*abs(down.z),0,abs(down.x))).normalized()
    # Front/back axis is projected perpendicular to the arm so both authored sides have positive transforms.
    across=down.cross(outward).normalized()
    if across.y<0:across=-across
    frames[side]={'pivot':list(shoulder),'down':list(down),'outward':list(outward),'across':list(across)}
    groups={k:[] for k in ['MainPlateRows','LowerEdgeRow','UpperAttachment','Lacing','InteriorPadding','Bindings','Fittings']}
    def solid(ob,thickness=.0028,bevel=.0007):
        # Open front grids must face outward on both authored sides before thickness.
        if sum(p.normal.dot(outward) for p in ob.data.polygons)<0:
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
        return g.solid(ob,thickness,bevel)
    def point(y,t,offset=0):
        # 25.2 cm wide shallow wrap, open along front and rear for arm movement.
        radius=.110-.060*(y/.126)**2 + .010*max(0,t)/.25
        return shoulder+down*t+across*y+outward*(radius+offset)
    def plate(name,ya,yb,ta,tb,tile,offset=0,thickness=.0032,cols=3,rows=3):
        vs=[];uv=[];fs=[]
        for j in range(rows+1):
            f=j/rows
            for i in range(cols+1):
                u=i/cols;y=ya+(yb-ya)*u;t=ta+(tb-ta)*f
                crown=.00045*math.sin(math.pi*u)**2
                vs.append(point(y,t,offset-.006*(1-f)**4+crown))
                # Preserve the complete braid proportions and lacquer interval
                # from Dō's atlas; half-tile crops stretch the fastenings.
                uv.append((.06+.88*u,.04+.92*(1-f)) if tile in (8,9,13,14) else (.10+.75*u,.08+.84*(1-f)))
        for j in range(rows):
            for i in range(cols):
                a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
        return solid(g.mesh(name,vs,fs,tile,uv),thickness,.0006)
    # Formed lacquer lamellae reuse Dō's lacquer, punched holes, braid and wear.
    # Sparse physical braids reinforce that same tier without a second pattern.
    count=22
    for row in range(5):
        top=.010+row*.044;bottom=top+.054
        group='LowerEdgeRow' if row==4 else 'MainPlateRows'
        for k in range(count):
            ya=-.126+.252*k/count+.00018;yb=-.126+.252*(k+1)/count-.00018
            groups[group].append(plate('Crowned lamella %s %d %02d'%(side,row+1,k+1),ya,yb,top,bottom,[8,9,13,14][(k+row*3)%4],offset=row*.0012))
            y=(ya+yb)*.5
            # Paired fine over-under ties concentrate near each row's seam.
            if k%4==1:
                for u in [(.34-.06)/.88,(.64-.06)/.88]:
                    yy=ya+(yb-ya)*u
                    pts=[point(yy,top+.0035,row*.0012-.0048),point(yy-.0003,top+.008,row*.0012+.0004),point(yy+.0003,top+.013,row*.0012+.001),point(yy,top+.0182,row*.0012-.0007)]
                    groups['Lacing'].append(g.tube('Silk fastening over matching atlas braid',pts,.0011,3,6))
        for t,rad,tile in [(bottom,.0023,0),(bottom-.001,.00065,2)]:
            groups['Bindings'].append(g.tube('Rolled overlapping row edge',[point(-.126+.252*i/28,t,row*.0012+.0016) for i in range(29)],rad,tile,7))
        for k in [0,5,11,16,21]:
            y=-.120+.240*k/21
            groups['Fittings'].append(g.stud('Small peened row tack',point(y,bottom-.006,row*.0012+.004),.00135))
        for y in [-.123,.123]:
            groups['Fittings'].append(plate('Chased narrow side staple',y-.0022,y+.0022,top+.004,bottom-.006,11,.0045,thickness=.0014,cols=1,rows=2))
            for t in [top+.009,bottom-.010]:groups['Fittings'].append(g.stud('Staple pin',point(y,t,.006),.0015))
            c=point(y,top+.022,.006)
            groups['Lacing'].append(g.tube('Side cross fastening',[c-across*.004-down*.004,c+outward*.0015,c+across*.004+down*.004],.0012,3,6))
    # Asymmetric upper profile: high forward tab and low rear attachment.
    ys=[-.126,-.111,-.100,-.078,-.054,-.031,.0,.034,.070,.102,.126]
    ts=[-.007,-.048,-.075,-.081,-.069,-.026,-.015,-.015,-.018,-.022,-.008]
    profile=g.path([(y,t,0) for y,t in zip(ys,ts)],4)
    ys=[p.x for p in profile];ts=[p.y for p in profile]
    vs=[];uv=[];fs=[]
    for j in range(3):
        f=j/2
        for i,(y,top) in enumerate(zip(ys,ts)):
            vs.append(point(y,top*(1-f)+.014*f,.002));uv.append((i/(len(ys)-1),1-f))
    n=len(ys)
    for j in range(2):
        for i in range(n-1):a=j*n+i;fs.append((a,a+1,a+n+1,a+n))
    groups['UpperAttachment'].append(solid(g.mesh('Crowned upper plate',vs,fs,10,uv),.004,.001))
    outline=vs[:n]+[vs[2*n-1],vs[3*n-1]]+list(reversed(vs[2*n:3*n-1]))+[vs[n]]
    groups['Bindings'].append(g.tube('Upper black rolled rim',outline,.0027,0,7,True))
    groups['Bindings'].append(g.tube('Upper narrow brass rim',[p+outward*.002 for p in outline],.0009,2,5,True))
    # Shallow quilted cushion: real lobes with inset seams, inside the
    # established padding envelope. It is not a box carrying a quilt decal.
    vv=[];uu=[];ff=[];nx=24;ny=28
    for j in range(ny+1):
        f=j/ny;t=-.002+.239*f
        for i in range(nx+1):
            u=i/nx;y=-.119+.238*u
            puff=.0028*(math.sin(math.pi*u*6)**2)*(math.sin(math.pi*f*7)**2)
            vv.append(point(y,t,-.0065-puff));uu.append((u,f))
    for j in range(ny):
        for i in range(nx):a=j*(nx+1)+i;ff.append((a,a+1,a+nx+2,a+nx+1))
    groups['InteriorPadding'].append(solid(g.mesh('Quilted cushion lobes',vv,ff,12,uu),.0025,.0004))
    for i in range(1,6):
        y=-.119+.238*i/6
        groups['InteriorPadding'].append(g.tube('Inset vertical cushion seam',[point(y,-.002+.239*j/28,-.0092) for j in range(29)],.00042,4,5))
    for j in range(1,7):
        t=-.002+.239*j/7
        groups['InteriorPadding'].append(g.tube('Inset horizontal cushion seam',[point(-.119+.238*i/24,t,-.0092) for i in range(25)],.00042,4,5))
    perimeter=[point(-.119+.238*i/24,-.002,-.008) for i in range(25)]+[point(.119,.237,-.008)]+[point(.119-.238*i/24,.237,-.008) for i in range(1,25)]
    groups['InteriorPadding'].append(g.tube('Soft leather piping',perimeter,.0028,4,8,True))
    # Flush, chased floral mounting plate. Every layer follows the crowned
    # header curvature so no medallion cuts through the interior.
    cy,ct=-.077,-.046
    def jewel(y,t,offset):return point(y,t,offset)
    def disc(name,r,tile,offset,thickness=.0012):
        vv=[jewel(cy,ct,offset)];uu=[(.5,.5)];ff=[]
        for i in range(40):
            a=math.tau*i/40;yy=cy+r*math.cos(a);tt=ct+r*math.sin(a)
            vv.append(jewel(yy,tt,offset));uu.append((.5+.5*math.cos(a),.5+.5*math.sin(a)))
        for i in range(40):ff.append((0,i+1,(i+1)%40+1))
        return solid(g.mesh(name,vv,ff,tile,uu),thickness,.0002)
    groups['Fittings'].append(disc('Engraved bronze mounting plate',.021,11,.007))
    groups['Fittings'].append(disc('Inset lacquer medallion field',.0177,0,.0085,.0008))
    for radius,wire in [(.0200,.0010),(.0080,.00065)]:
        groups['Fittings'].append(g.tube('Chased floral bezel',[jewel(cy+radius*math.cos(math.tau*i/48),ct+radius*math.sin(math.tau*i/48),.010) for i in range(48)],wire,2,6,True))
    for i in range(8):
        a=math.tau*i/8;vv=[];uu=[];ff=[]
        # Tapered raised petal with a central ridge, smaller than the outer bezel.
        for u,v,h in [(0,-.0020,0),(.0042,0,.0011),(0,.0020,0),(-.0037,0,.0007)]:
            radial=.011+u;yy=cy+radial*math.cos(a)-v*math.sin(a);tt=ct+radial*math.sin(a)+v*math.cos(a)
            vv.append(jewel(yy,tt,.010+h));uu.append((.5+u/.009,.5+v/.0045))
        vv.append(jewel(cy+.011*math.cos(a),ct+.011*math.sin(a),.012));uu.append((.5,.5))
        for j in range(4):ff.append((j,(j+1)%4,4))
        groups['Fittings'].append(solid(g.mesh('Chased relief petal',vv,ff,2,uu),.001,.0003))
    groups['Fittings'].append(disc('Engraved central boss',.006,11,.012,.0015))
    groups['Fittings'].append(g.stud('Peened center stud',point(cy,ct,.014),.002))
    for y,t in [(-.114,-.028),(-.100,-.065),(-.041,-.025),(.022,-.004),(.09,-.006)]:groups['Fittings'].append(g.stud('Header rivet',point(y,t,.0065),.0018))
    # Two load-bearing ties connect to the existing Dō shoulder strap, not the neck.
    for y in [-.070,.075]:
        mount=Vector((sign*.167,-.125 if y<0 else .118,1.503 if y<0 else 1.518))
        target=point(y,-.046 if y<0 else -.017,.006)
        for shift in [-.004,.004]:
            a=mount+across*shift;b=target+across*shift
            pts=g.path([a,a+Vector((sign*.035,0,.020)),b+Vector((-sign*.010,0,.020)),b],4)
            ob=braided_cord(g,'Twisted shoulder suspension',pts,radius=.0024,pitch=.012,strands=2)
            # Each vertex blends by distance along the span, using only existing bones.
            def cord_weight(p,mount=mount,target=target):
                f=max(0,min(1,(p-mount).dot(target-mount)/(target-mount).length_squared))
                return {'spine_05':1-f,bone:f}
            g.weight(ob,rig,cord_weight);ob['attachment_flexible']=True
            parts.setdefault('Sode_'+side+'_01_Suspension',[]).append(ob)
        groups['Lacing'].append(wrapped_knot(g,'Compact crossed suspension knot',target+down*.005+outward*.006,down,outward,bundle_radius=.0048,cord_radius=.0016,turns=3))
        c=point(-.133 if y<0 else .133,.015,.007)
        tail=g.path([target,c,c+down*.045+outward*.004,c+down*.083],4)
        groups['Lacing'].append(braided_cord(g,'Weighted side tie',tail,radius=.0024,pitch=.010,strands=2))
        groups['Lacing'].append(wrapped_knot(g,'Bound tassel neck',tail[-1]-down*.004,down,outward,bundle_radius=.003,cord_radius=.0010,turns=3))
        # Gathered short silk fringe, tapering individually rather than blunt prongs.
        for k in range(7):
            off=(k-3)*.0009
            pts=[tail[-1]+across*off,tail[-1]+down*.010+across*(off*1.25),tail[-1]+down*(.016+.0015*math.sin(k*2))+across*(off*1.1)]
            groups['Lacing'].append(g.tube('Fine gathered fringe',pts,.00048,3,5))
    for key,obs in groups.items():
        ob=g.merge(obs,'Sode_'+side+'_01_'+key)
        g.weight(ob,rig,lambda p,bone=bone:{bone:1.})
        ob['asset']='Sode_'+side+'_01';ob['wearer_side']='left' if side=='L' else 'right';ob['construction']=key
        parts[ob.name]=[ob]
# Merge suspension while preserving weights and avoid applying the Armature modifier.
for side in ['L','R']:
    name='Sode_'+side+'_01_Suspension';obs=parts[name]
    for ob in obs:ob.modifiers.clear()
    g.select(obs);bpy.ops.object.join();ob=bpy.context.object;ob.name=name
    mod=ob.modifiers.new('Native Manny skeleton','ARMATURE');mod.object=rig
    ob['asset']='Sode_'+side+'_01';ob['wearer_side']='left' if side=='L' else 'right';ob['attachment_flexible']=True
components=list(source.objects)
sys.path.insert(0,str(ART.parent/'Kabuto01/Scripts'))
import kabuto_export_common as surface_helpers
surface_helpers.ROUND_GROUP='Do_Round_Surfaces'
for ob in components:surface_helpers.surface_normals(ob)
# Source round-surface tags and flat plate boundaries are compatible with existing export helpers.
for ob in components:ob['asset']='Sode01'
for name,loc,power,size,color in [('Key',(-1.2,-1.7,2.7),135,1.1,(1,.88,.75)),('Fill',(1.4,-.8,2.0),95,1.2,(.77,.87,1)),('Rim',(0,.8,2.4),145,1,(1,.89,.72))]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;light.color=color
    ob=bpy.data.objects.new(name,light);studio.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.40))-ob.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Neutral armor review');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.145,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
camdata=bpy.data.cameras.new('Sode review');cam=bpy.data.objects.new('Sode review',camdata);studio.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=1.27
cam.location=(.85,-1.8,1.83);cam.rotation_euler=(Vector((0,0,1.43))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
rig.hide_render=True
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=1.7;area.spaces.active.region_3d.view_location=(0,0,1.4)
g.select([components[0]])
manifest={'asset':'Sode01','blender_version':bpy.app.version_string,'source_collection':'Sode01_Source','source_components':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in components},'source_materials':1,'runtime_materials':1,'shared_material':'M_Sode01','shared_textures':'unchanged Do01 BaseColor, Normal, ORM','texture_dimensions':[2048,2048],'skeleton_source':str(MANNY.relative_to(ROOT)/'Manny.blend'),'source_bone_count':len(rig.data.bones),'native_reference_bone_count':89,'left_right_assignment':{'Sode_L_01':'wearer left, +X in Blender, upperarm_l','Sode_R_01':'wearer right, -X in Blender, upperarm_r'},'construction':{'rows':5,'lamellae_per_row':22,'panel_width_metres':.252,'panel_height_metres':.337},'attachment_method':'Rigid panels 100% upperarm_l/r; only two suspension braids interpolate between spine_05 at the Dō strap and same-side upperarm. No new bones or physics.','reference_priority':'3/4 silhouette, front, outer side, inner/back, exploded, decorative details','review_contract':json.loads((DO/'asset-manifest.json').read_text())['review_contract'],'side_frames':frames,'existing_actions':['A_Idle','A_Walk','A_Run','A_Attack'],'unavailable_actions':['native bow-use clip'],'dependencies':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DO/'Do01.blend',MANNY/'Manny.blend',ART.parent/'Kabuto01/Kabuto01.blend']}}
manifest['source_triangles_before_modifiers']=sum(manifest['source_components'].values())
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Sode01.blend'))
manifest['source_blend_sha256']=hashlib.sha256((ART/'Sode01.blend').read_bytes()).hexdigest()
(ART/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if '--no-render' not in sys.argv:
    scene.render.filepath=str(ART/'Review/Captures/fit-initial.png');bpy.ops.render.render(write_still=True)
print('SODE01_SOURCE_COMPLETE '+json.dumps(manifest),flush=True)
