"""Render saved Dō source and exercise existing rig. Never save source changes."""
from pathlib import Path
import math,json,sys
import bpy
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ART=Path(__file__).resolve().parents[1]; ROOT=ART.parents[3]
bpy.ops.wm.open_mainfile(filepath=str(ART/'Do01.blend'))
scene=bpy.context.scene; rig=bpy.data.objects['root']; body=bpy.data.objects['FIT_Manny']; helmet=bpy.data.objects['FIT_Kabuto01']
components=list(bpy.data.collections['DO01 • editable components'].objects)
for ob in bpy.data.collections['EXPORT ONLY • runtime LODs'].objects:ob.hide_render=True; ob.hide_set(True)
rig.hide_set(False); rig.data.pose_position='POSE'; rig.animation_data_create()
scene.cycles.samples=24; scene.render.resolution_x=1000; scene.render.resolution_y=1000
camera=scene.camera
bpy.context.view_layer.update()
root_rest=rig.matrix_world.copy()

def aim(position,target,scale):
    camera.location=position; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.ortho_scale=scale

def neutral():
    rig.animation_data.action=None
    for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
    scene.frame_set(1); rig.matrix_world=root_rest; bpy.context.view_layer.update()

def arm(name,direction):
    bone=rig.data.bones[name]; a=bone.head_local; old=rig.data.bones[name.replace('upperarm','lowerarm')].head_local-a
    q=old.rotation_difference(Vector(direction).normalized())
    rig.pose.bones[name].matrix=Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-a)@bone.matrix_local

def pose(name):
    neutral()
    if name in ('arms-forward','arms-raised'):
        for sign,suffix in [(-1,'r'),(1,'l')]:arm('upperarm_'+suffix,(sign*.13,-1,-.12) if name=='arms-forward' else (sign*.90,-.2,.10))
    elif name in ('turn','bend','head'):
        name_bone='head' if name=='head' else 'spine_04'
        rest=rig.data.bones[name_bone].matrix_local; pivot=rest.translation
        rotation=Matrix.Rotation(math.radians(20 if name=='bend' else 32 if name=='head' else 25),4,'X' if name=='bend' else 'Z')
        rig.pose.bones[name_bone].matrix=Matrix.Translation(pivot)@rotation@Matrix.Translation(-pivot)@rest
    bpy.context.view_layer.update()

def native_action_in_place(name):
    # A review-only action copy removes exported object-root channels. All
    # native bone channels remain intact; original actions are never modified.
    action=bpy.data.actions[name].copy();action.name='REVIEW_IN_PLACE_'+name
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag=strip.channelbag(slot)
                if bag:
                    for curve in list(bag.fcurves):
                        if not curve.data_path.startswith('pose.bones['):bag.fcurves.remove(curve)
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    rig.matrix_world=root_rest
    return action

def tree(objects):
    vs=[]; fs=[]; dg=bpy.context.evaluated_depsgraph_get()
    for ob in objects:
        eo=ob.evaluated_get(dg); mesh=eo.to_mesh(); offset=len(vs)
        vs.extend(eo.matrix_world@v.co for v in mesh.vertices)
        mesh.calc_loop_triangles(); fs.extend(tuple(offset+i for i in t.vertices) for t in mesh.loop_triangles); eo.to_mesh_clear()
    return BVHTree.FromPolygons(vs,fs,all_triangles=True)

def measure(label):
    armor=tree(components); bt=tree([body]); ht=tree([helmet])
    result={'pose':label,'body_intersecting_triangle_pairs':len(armor.overlap(bt)),'helmet_intersecting_triangle_pairs':len(armor.overlap(ht))}
    result['components']={ob.name:len(tree([ob]).overlap(bt)) for ob in components}
    print(json.dumps(result),flush=True); return result

def render(name):
    if '--measure-only' in sys.argv:return
    scene.render.filepath=str(ART/f'Review/Captures/{name}.png'); bpy.ops.render.render(write_still=True)

checks=[]
neutral(); body.hide_render=True; helmet.hide_render=True
if '--poses-only' not in sys.argv:
    for name,position,target,scale in [('front',(0,-2,1.34),(0,0,1.30),.72),('rear',(0,2,1.34),(0,0,1.30),.72),('left',(2,0,1.45),(0,0,1.30),.72),('right',(-2,0,1.45),(0,0,1.30),.72),('interior',(0,-.30,2.3),(0,0,1.30),.74)]:
        aim(position,target,scale);render('blender-'+name)
body.hide_render=False; helmet.hide_render=False
for name in ['neutral','arms-forward','arms-raised','turn','bend','head']:
    pose(name);checks.append(measure(name)); aim((.75,-1.7,1.76),(0,0,1.42),1.24)
    render('fit-'+name)
for action,frames in [('A_Idle',[15,110]),('A_Walk',[8,23,37]),('A_Run',[8,23,40]),('A_Attack',[6,12,20,28])]:
    neutral();native_action_in_place(action)
    for f in frames:
        scene.frame_set(f);rig.location.x=0;rig.location.y=0;bpy.context.view_layer.update();checks.append(measure(action+':'+str(f)))
        if f==frames[0]:
            aim((.75,-1.7,1.76),(0,0,1.42),1.24);render('fit-'+action.lower())
        if (action=='A_Attack' and f in (20,28)) or (action=='A_Run' and f==23):
            aim((.75,-1.7,1.76),(0,0,1.42),1.24)
            render('stress-'+action.lower()+'-'+str(f))
result={'asset':'Do01','checks':checks,'scope':'Saved Blender source and native Manny fit fixtures, actual sampled poses. Root translation/rotation channels locked on temporary action copies for in-place review. Triangle overlaps are surface intersection counts, not global penetration depths. Diagnostic poses are temporary, not exported animation assets.','run':'Original Epic MF_Unarmed_Jog_Fwd native clip; A_Run is export filename alias.','pose_definitions':{'arms-forward':'upper arms directed (±.13,-1,-.12)','arms-raised':'upper arms directed (±.90,-.2,.10)','turn':'spine_04 25 degrees around component Z','bend':'spine_04 20 degrees around component X','head':'head32 degrees around componentZ'}}
(ROOT/'artifacts/do01/pose-review.json').write_text(json.dumps(result,indent=2)+'\n')
