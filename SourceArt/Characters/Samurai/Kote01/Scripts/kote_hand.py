"""Fitted leather gloves and individually articulated Kote hand plates."""
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def build_hands(rig, body, g):
    """Use Manny's unchanged rest hand and native weights; return three parts/side."""
    world = body.matrix_world.copy()
    normal_matrix = world.to_3x3().inverted().transposed()
    skin = [world @ v.co for v in body.data.vertices]
    skin_normals = [(normal_matrix @ v.normal).normalized() for v in body.data.vertices]
    surface = BVHTree.FromPolygons(skin, [tuple(p.vertices) for p in body.data.polygons])
    bone_names = set(rig.data.bones.keys())
    group_names = {v.index: v.name for v in body.vertex_groups}
    source_uv = body.data.uv_layers.active
    result = {}

    def head(name):
        return rig.matrix_world @ rig.data.bones[name].head_local

    def outward(direction, across, sign):
        n = direction.cross(across).normalized()
        return n if n.x * sign > 0 else -n

    def project(p, n, clearance=.004):
        hit, _, _, _ = surface.ray_cast(p + n * .065, -n, .13)
        return (hit if hit is not None else p + n * .012) + n * clearance

    def rigid(ob, bone):
        vg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
        vg.add(list(range(len(ob.data.vertices))), 1, 'REPLACE')
        return ob

    def finish(parts, name):
        ob = g.merge(parts, name)
        names = {v.index: v.name for v in ob.vertex_groups}
        weights = [{names[v.group]: v.weight for v in vert.groups
                    if names[v.group] in bone_names} for vert in ob.data.vertices]
        g.weight(ob, rig, per_vertex=weights)
        ob['asset'] = 'Kote01'
        return ob

    for side, sign in [('L', 1), ('R', -1)]:
        suffix = side.lower()
        hand_bone = 'hand_' + suffix
        wrist = head(hand_bone)
        knuckles = [head(f + '_01_' + suffix) for f in ('index', 'middle', 'ring', 'pinky')]
        forward = ((sum(knuckles, Vector()) / 4) - wrist).normalized()
        across = (knuckles[-1] - knuckles[0]).normalized()
        dorsal = outward(forward, across, sign)
        across = dorsal.cross(forward).normalized()
        if across.dot(knuckles[-1] - knuckles[0]) < 0:
            across = -across
        plates, fittings, soft = [], [], []

        # The glove copies only the distal hand region. Its skinning, including
        # thumb and palm blends, comes from the existing body rather than a fit rig.
        eligible = {i for i, p in enumerate(skin)
                    if p.x * sign > .39 and (p - wrist).dot(forward) > -.026}
        faces = [p for p in body.data.polygons if all(i in eligible for i in p.vertices)]
        used = sorted({i for p in faces for i in p.vertices})
        remap = {old: new for new, old in enumerate(used)}
        vertices = [skin[i] + skin_normals[i] * .0019 for i in used]
        glove = g.mesh('Kote_' + side + '_Glove', vertices,
                       [tuple(remap[i] for i in p.vertices) for p in faces], 4)
        if source_uv:
            uv = glove.data.uv_layers.active.data
            hand_uv = [source_uv.data[li].uv for face in faces for li in face.loop_indices]
            u_min = min(v.x for v in hand_uv); u_max = max(v.x for v in hand_uv)
            v_min = min(v.y for v in hand_uv); v_max = max(v.y for v in hand_uv)
            for old, new in zip(faces, glove.data.polygons):
                for src, dst in zip(old.loop_indices, new.loop_indices):
                    coord = source_uv.data[src].uv
                    uv[dst].uv = g.uvcoord(4, (coord.x-u_min)/max(u_max-u_min, 1e-6),
                                          (coord.y-v_min)/max(v_max-v_min, 1e-6))
        weights = [{group_names[a.group]: a.weight for a in body.data.vertices[i].groups
                    if group_names[a.group] in bone_names} for i in used]
        g.weight(glove, rig, per_vertex=weights)
        glove['asset'] = 'Kote01'
        glove['construction'] = 'Leather shell from existing Manny hand, native hand/finger weights'

        def plate(name, a, b, width_a, width_b, bone, normal=None,
                  clearance=.0044, tile=0, hem=True, rivets=True, knuckle=False):
            direction = (b - a).normalized()
            n = normal or outward(direction, across, sign)
            cross = n.cross(direction).normalized()
            # Rounded clipped corners, a shallow central crown and a modest
            # rolled brass perimeter keep the reference's narrow iron splints.
            rows = (0, .035, .10, .22, .50, .78, .90, .965, 1)
            cols = (-1, -.55, 0, .55, 1)
            vs, uv, fs = [], [], []
            for t in rows:
                width = width_a * (1-t) + width_b * t
                corner = .50 if t in (0, 1) else .84 if t in (.035, .965) else 1
                center = a.lerp(b, t)
                for u in cols:
                    p = center + cross * (width * .5 * u * corner)
                    crown = .0011 * (1-u*u)
                    if knuckle:
                        crown += .0014 * (1-u*u) * math.exp(-((t-.18)/.22)**2)
                    vs.append(project(p, n, clearance + crown))
                    uv.append((.05 + .90 * (u+1)/2, .06 + .88*t))
            for j in range(len(rows)-1):
                for i in range(len(cols)-1):
                    k = j*len(cols)+i
                    fs.append((k, k+1, k+len(cols)+1, k+len(cols)))
            ob = g.mesh(name, vs, fs, tile, uv)
            bm = bmesh.new(); bm.from_mesh(ob.data)
            if sum((face.normal.dot(n) for face in bm.faces)) < 0:
                bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
            bm.to_mesh(ob.data); bm.free()
            rigid(g.solid(ob, .0015, .00045), bone)
            plates.append(ob)
            last = len(rows)-1
            boundary = ([i for i in range(5)] + [j*5+4 for j in range(1, last+1)] +
                        [last*5+i for i in range(3, -1, -1)] + [j*5 for j in range(last-1, 0, -1)])
            if hem:
                edge = g.tube(name + ' brass hem', [vs[i] + n*.00030 for i in boundary],
                              .00062, 2, 6, True)
                fittings.append(rigid(edge, bone))
            if rivets:
                for t in (.15, .84):
                    p = project(a.lerp(b, t), n, clearance + .0023)
                    fittings.append(rigid(g.stud(name + ' brass pin', p, .0012, 2), bone))
            return vs

        # Reinforced back-of-hand leather: its outline fans toward the four
        # knuckles and stays entirely clear of the thumb saddle and palm.
        patch_vs, patch_uv, patch_faces = [], [], []
        for j in range(5):
            t = j/4
            for i in range(5):
                u = i/4
                near = wrist + forward*.010 + across*((u-.5)*.058)
                far = knuckles[0].lerp(knuckles[-1], u) + forward*.003
                patch_vs.append(project(near.lerp(far, t), dorsal, .0030))
                patch_uv.append((u, t))
        for j in range(4):
            for i in range(4):
                k = j*5+i; patch_faces.append((k,k+1,k+6,k+5))
        patch = g.mesh('Reinforced leather back of hand', patch_vs, patch_faces, 4, patch_uv)
        bm = bmesh.new(); bm.from_mesh(patch.data)
        if sum(face.normal.dot(dorsal) for face in bm.faces) < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(patch.data); bm.free()
        soft.append(rigid(g.solid(patch, .0012, .0004), hand_bone))
        for column in (0, 4):
            seam = g.tube('Raised leather side seam', [patch_vs[j*5+column]+dorsal*.0003 for j in range(5)],
                          .00115, 0, 6)
            soft.append(rigid(seam, hand_bone))

        # Four longitudinal metacarpal plates, as in the supplied hand detail.
        for lane, (finger, wa, wb) in enumerate([('index', .014, .023), ('middle', .014, .023),
                                                ('ring', .014, .0215), ('pinky', .014, .020)]):
            base = head(finger + '_metacarpal_' + suffix)
            knuckle = head(finger + '_01_' + suffix)
            a = wrist + forward*.020 + across*((lane-1.5)*.0155)
            b = knuckle - (knuckle-base).normalized()*.0017
            plate(finger + ' metacarpal splint', a, b, wa, wb, hand_bone,
                  dorsal, clearance=.0051)
            # The next bone HEAD is the actual joint. Exported FBX tails are
            # orientation handles and must never determine the armor length.
            for segment, width in [(1, wb*.98), (2, wb*.82)]:
                start = head(finger + '_0' + str(segment) + '_' + suffix)
                end = head(finger + '_0' + str(segment+1) + '_' + suffix)
                d = (end-start).normalized()
                plate(finger + ' articulated finger ' + str(segment),
                      start + d*.0023, end - d*.0038,
                      width, width*.86, finger + '_0' + str(segment) + '_' + suffix,
                      clearance=.0040, rivets=(segment == 1), knuckle=(segment == 1))
                n = outward(d, across, sign)
                cross = n.cross(d).normalized()
                for edge_sign in (-1, 1):
                    seam_points = [project(start.lerp(end, t) + cross*(edge_sign*width*.54), n, .0025)
                                   for t in (.12, .26, .45, .64, .84)]
                    soft.append(rigid(g.tube('Dark leather finger seam', seam_points, .0009, 0, 6),
                                      finger + '_0' + str(segment) + '_' + suffix))
                if segment == 1:
                    points = [project(start + cross*(width*.57*u) + d*(.002+.002*(1-u*u)), n, .0028)
                              for u in (-1, -.75, -.4, 0, .4, .75, 1)]
                    soft.append(rigid(g.tube('Raised leather knuckle reinforcement', points, .00125, 0, 7),
                                      finger + '_01_' + suffix))

        # A single small mobile thumb plate leaves its first web joint open.
        a = head('thumb_02_' + suffix); b = head('thumb_03_' + suffix)
        d = (b-a).normalized()
        thumb_normal = (dorsal + Vector((0, -.20, .10))).normalized()
        thumb_normal = (thumb_normal - d*thumb_normal.dot(d)).normalized()
        plate('Thumb mobile guard', a+d*.004, b-d*.004, .016, .014,
              'thumb_02_' + suffix, thumb_normal, .004, rivets=False)

        # Sparse hardware at the wrist: black leather piping and a bronze
        # fastening plate repeat the wider sleeve fittings without a rigid cuff.
        edge = [patch_vs[i] + dorsal*.0010 for i in range(5)]
        soft.append(rigid(g.tube('Back-of-hand rolled leather cuff', edge, .00155, 4, 7), hand_bone))
        for i in (0, 4):
            fittings.append(rigid(g.stud('Wrist fastening pin', edge[i]+dorsal*.0014, .00165, 2), hand_bone))

        guard = finish(plates, 'Kote_' + side + '_HandGuard')
        # Keep the soft reinforcement in the same glove object. Existing native
        # weights are retained when moving it back into metre space for joining.
        for ob in soft:
            g.select([ob])
            for modifier in list(ob.modifiers):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            weights = []
            names = {v.index:v.name for v in ob.vertex_groups}
            for vert in ob.data.vertices:
                weights.append({names[w.group]:w.weight for w in vert.groups if names[w.group] in bone_names})
            g.weight(ob, rig, per_vertex=weights)
        all_soft = [glove] + soft
        joined = g.merge(all_soft, 'Kote_' + side + '_Glove')
        mod = joined.modifiers.new('Native Manny skeleton', 'ARMATURE'); mod.object = rig
        joined['asset'] = 'Kote01'
        result[side] = [guard, joined, finish(fittings, 'Kote_' + side + '_HandFittings')]
    return result
