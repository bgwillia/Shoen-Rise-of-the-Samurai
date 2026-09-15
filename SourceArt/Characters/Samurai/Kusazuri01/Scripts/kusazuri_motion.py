"""Rigid panel hinges on an armor-only instance of the existing native Manny rig.

No animation, body pose, rest hierarchy or skeleton asset is changed. Angles
come directly from the current thigh directions, with no physics or lag.
"""
import math
import bpy
from mathutils import Matrix, Vector

PANELS=[('Front_Center','spine_01',0),('Front_L','thigh_l',.84),('Front_R','thigh_r',-.84),('Side_L','thigh_twist_01_l',1.70),('Side_R','thigh_twist_01_r',-1.70),('Rear_L','thigh_twist_02_l',2.64),('Rear_R','thigh_twist_02_r',-2.64)]

def hinge_pivot(theta):
    sn,cs=math.sin(theta),math.cos(theta)
    return Vector((18.4*math.copysign(abs(sn)**(2/2.8),sn),-1.4-14.8*math.copysign(abs(cs)**(2/2.8),cs),100.6))

def smoothstep(value):
    value=max(0.,min(1.,value))
    return value*value*(3.-2.*value)

def armor_pose(body,armor):
    for bone in armor.pose.bones:bone.matrix_basis=body.pose.bones[bone.name].matrix_basis.copy()
    armor.matrix_world=body.matrix_world.copy()
    bpy.context.view_layer.update()
    delta=body.pose.bones['pelvis'].matrix@body.data.bones['pelvis'].matrix_local.inverted()
    directions={}
    for side in ['l','r']:
        knee=body.pose.bones['calf_'+side].matrix.translation
        hip=body.pose.bones['thigh_'+side].matrix.translation
        directions[side]=delta.to_quaternion().inverted()@(knee-hip).normalized()
    records=[]
    for name,bone,theta in PANELS:
        n=Vector((math.sin(theta),-math.cos(theta),0));pivot=hinge_pivot(theta)
        sides=['l','r'] if name=='Front_Center' else ['l' if theta>0 else 'r']
        direction=directions[sides[0]]
        sagittal_flex=math.atan2(max(0,-direction.y),max(.08,-direction.z))
        if name in ['Front_L','Front_R']:
            azimuth=math.atan2(abs(direction.x),max(0,-direction.y))
            blend=smoothstep((sagittal_flex-math.radians(50))/math.radians(25))
            blend*=1-smoothstep((azimuth-math.radians(15))/math.radians(20))
            n=n.lerp(Vector((direction.x,direction.y,0)).normalized(),blend).normalized()
        flex=max(math.atan2(max(0,directions[s].dot(n)),max(.08,-directions[s].z)) for s in sides)
        angle=max(0,min(math.pi/2,flex-.02))
        if name in ['Side_L','Side_R']:
            angle=max(angle,.08*sagittal_flex)
        axis=Vector((n.y,-n.x,0))
        panel_delta=delta@Matrix.Translation(pivot)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-pivot)
        target=panel_delta@body.data.bones[bone].matrix_local
        armor.pose.bones[bone].matrix=target
        bpy.context.view_layer.update()
        records.append({'panel':name,'bone':bone,'theta':theta,'angle_radians':angle,'target_blender_cm':[list(r) for r in target],'reference_blender_cm':[list(r) for r in body.data.bones[bone].matrix_local],'hinge_pivot_cm':list(pivot)})
    return {'panels':records,'pelvis_reference_blender_cm':[list(r) for r in body.data.bones['pelvis'].matrix_local],'pelvis_pose_blender_cm':[list(r) for r in body.pose.bones['pelvis'].matrix],'thigh_directions_pelvis_blender':{s:list(d) for s,d in directions.items()},'posed_bones_blender_cm':{n:[list(r) for r in body.pose.bones[n].matrix] for n in ['thigh_l','thigh_r','calf_l','calf_r']}}

def review_rig(body,parts):
    armor=body.copy();armor.data=body.data.copy();armor.name='Kusazuri_Motion_Review_Rig';armor.animation_data_clear()
    bpy.context.scene.collection.objects.link(armor);armor.hide_render=True
    for ob in parts:
        for mod in ob.modifiers:
            if mod.type=='ARMATURE':mod.object=armor
    return armor
