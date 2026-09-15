"""Rigid, twist-free shoulder suspension on the unchanged native skeleton.

Only the armor instance's upperarm pose is controlled; Manny's skeleton,
reference bones, clips, body and other armor remain untouched.
"""
import math
import bpy
from mathutils import Vector, Matrix


def armor_pose(body, armor):
    for bone in armor.pose.bones:
        bone.matrix_basis=body.pose.bones[bone.name].matrix_basis.copy()
    armor.matrix_world=body.matrix_world.copy()
    bpy.context.view_layer.update()
    torso=body.pose.bones['spine_05'].matrix @ body.data.bones['spine_05'].matrix_local.inverted()
    qtorso=torso.to_quaternion();qinv=qtorso.inverted()
    targets={}
    for side,sign in [('l',1),('r',-1)]:
        upper=body.data.bones['upperarm_'+side];lower=body.data.bones['lowerarm_'+side]
        rest_down=(lower.head_local-upper.head_local).normalized()
        rest_out=Vector((sign*abs(rest_down.z),0,abs(rest_down.x))).normalized()
        rest_across=rest_down.cross(rest_out).normalized()
        if rest_across.y<0:rest_across=-rest_across
        old_frame=Matrix((rest_out,rest_across,rest_down)).transposed()
        shoulder=body.pose.bones[upper.name].matrix.translation
        elbow=body.pose.bones[lower.name].matrix.translation
        direction=qinv@(elbow-shoulder).normalized()
        # Keep fore/aft swing but remove axial twist. As lateral arms pass
        # horizontal, continuously roll the shield onto the arm's upper side.
        elevation=max(0.,min(1.,(sign*direction.x-.85)/.10))
        elevation=elevation*elevation*(3-2*elevation)
        hanging=Vector((direction.x,direction.y,min(-.12,direction.z))).normalized()
        down=(hanging*(1-elevation)+direction*elevation).normalized()
        axis=Vector((sign,0,0))
        out=axis-down*axis.dot(down)
        if out.length<1e-6:out=Vector((-sign*down.z,0,sign*down.x))
        out.normalize()
        lift=max(0.,min(1.,(direction.z+.30)/.30))*elevation
        lift=lift*lift*(3-2*lift)
        over=Vector((-sign*down.z,0,sign*down.x)).normalized()
        out=(out*(1-lift)+over*lift).normalized()
        across=down.cross(out).normalized()
        # Fixed frame handedness; across need not face +Y after an overhead lift.
        if sign>0:across=-across
        new_frame=Matrix((out,across,down)).transposed()
        rotation=qtorso.to_matrix() @ new_frame @ old_frame.inverted()
        # Suspension opens laterally as the arm lifts or swings through the front edge.
        opening=8.*max(0.,(sign*direction.x-.576)/.364)+9.*max(0.,-sign*direction.x)+2.*abs(direction.y)+7.*max(0.,direction.z)
        shoulder=shoulder+qtorso@(Vector((sign*opening,0,0))+out*(4.*lift))
        # Native centimetres; stateless pose response has no simulation lag.
        target=Matrix.Translation(shoulder)@rotation.to_4x4()@Matrix.Translation(-upper.head_local)@upper.matrix_local
        armor.pose.bones[upper.name].matrix=target
        targets[side]={'opening_cm':opening,'lift_clearance_cm':4.*lift,'direction':list(direction),'target_blender_cm':[list(row) for row in target], 'upper_reference_blender_cm':[list(row) for row in upper.matrix_local], 'shoulder_blender_cm':list(body.pose.bones[upper.name].matrix.translation),'elbow_blender_cm':list(elbow),'torso_delta_blender_cm':[list(row) for row in torso]}
    bpy.context.view_layer.update()
    return targets


def review_rig(body,parts):
    armor=body.copy();armor.data=body.data.copy();armor.name='Sode_Motion_Review_Rig'
    bpy.context.scene.collection.objects.link(armor);armor.animation_data_clear();armor.hide_render=True
    for ob in parts:
        for mod in ob.modifiers:
            if mod.type=='ARMATURE':mod.object=armor
    return armor
