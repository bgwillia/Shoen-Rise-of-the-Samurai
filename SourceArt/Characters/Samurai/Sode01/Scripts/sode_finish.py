"""Optional restrained rope finishing for major Sode ties only.

Uses the existing sode_geometry module and shared Dō atlas. Returned meshes
are unweighted; the caller assigns the existing shoulder or suspension weights.
Do not use geometric braids for every repeated lamellar stitch.
"""
import math
from mathutils import Vector


def _sample_polyline(points, count):
    points = [Vector(point) for point in points]
    if len(points) < 2:
        raise ValueError('A structural cord needs at least two path points')
    lengths = [0.]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1]+(b-a).length)
    if lengths[-1] <= 1e-7:
        raise ValueError('A structural cord must have a nonzero path length')
    result, segment = [], 0
    for index in range(count+1):
        distance = lengths[-1]*index/count
        while segment < len(points)-2 and lengths[segment+1] < distance:
            segment += 1
        width = lengths[segment+1]-lengths[segment]
        factor = (distance-lengths[segment])/width if width > 1e-9 else 0.
        result.append(points[segment].lerp(points[segment+1], factor))
    return result, lengths[-1]


def braided_cord(geometry, name, points, radius=.0030, *, pitch=.010,
                 strands=2, sides=5, steps_per_turn=5, tile=3, phase=0.):
    """Make one mesh with closed rope-strand islands along a supplied curve.

    Defaults add about 1,000 triangles for a 10cm structural cord. `radius` is
    the total rope radius, not the radius of each strand. Fiber-scale surface
    variation remains in the shared cord normal/roughness tile.
    """
    if radius <= 0 or pitch <= 0 or strands not in (2, 3) or sides < 4:
        raise ValueError('Use a positive rope radius/pitch, two or three strands, and at least four sides')
    original = [Vector(point) for point in points]
    length = sum((b-a).length for a, b in zip(original, original[1:]))
    count = max(8, math.ceil(length/pitch*steps_per_turn))
    path, length = _sample_polyline(original, count)
    frames, previous = [], None
    for index, center in enumerate(path):
        tangent = (path[min(index+1, count)]-path[max(0, index-1)]).normalized()
        if previous is None:
            reference = Vector((0, 0, 1)) if abs(tangent.z) < .85 else Vector((0, 1, 0))
            axis_a = tangent.cross(reference).normalized()
        else:
            axis_a = previous-tangent*previous.dot(tangent)
            if axis_a.length < 1e-7:
                reference = Vector((0, 0, 1)) if abs(tangent.z) < .85 else Vector((0, 1, 0))
                axis_a = tangent.cross(reference)
            axis_a.normalize()
        frames.append((axis_a, tangent.cross(axis_a).normalized()))
        previous = axis_a
    core_radius = radius*(.48 if strands == 2 else .52)
    strand_radius = radius-core_radius
    meshes = []
    for strand in range(strands):
        strand_path = []
        for index, (center, (axis_a, axis_b)) in enumerate(zip(path, frames)):
            angle = phase+math.tau*(strand/strands+(length*index/count)/pitch)
            strand_path.append(center+core_radius*(axis_a*math.cos(angle)+axis_b*math.sin(angle)))
        meshes.append(geometry.tube(name+' strand '+str(strand+1), strand_path,
            strand_radius, tile, sides, closed=False))
    result = geometry.merge(meshes, name)
    result['construction_detail'] = 'Two/three closed twisted structural strands; fiber relief uses shared Dō tile3'
    result['structural_rope_length_metres'] = length
    result['structural_rope_pitch_metres'] = pitch
    return result


def wrapped_knot(geometry, name, center, axis, outward, *, bundle_radius=.0048,
                 cord_radius=.00165, turns=3, spacing=.0031, tile=3):
    """Tight continuous wraps around a structural tie, with closed tube ends.

    `axis` runs along the underlying rope bundle and `outward` faces the viewer.
    Three compact wraps cost about 500 triangles. Use at the suspension exits
    and side ties; repeated plate fastenings should remain much lighter.
    """
    center, axis, outward = Vector(center), Vector(axis).normalized(), Vector(outward)
    outward -= axis*outward.dot(axis)
    if outward.length < 1e-7:
        raise ValueError('Knot outward direction must differ from the bundle axis')
    outward.normalize()
    across = axis.cross(outward).normalized()
    points = []
    segments = turns*14
    for index in range(segments+1):
        fraction = index/segments
        angle = math.tau*turns*fraction
        centerline = center+axis*((fraction-.5)*turns*spacing)
        points.append(centerline+across*(bundle_radius*math.cos(angle))+
            outward*(bundle_radius*.68*math.sin(angle)))
    result = geometry.tube(name, points, cord_radius, tile, 6, closed=False)
    result['construction_detail'] = 'Continuous compact knot wraps around structural bundle'
    return result
