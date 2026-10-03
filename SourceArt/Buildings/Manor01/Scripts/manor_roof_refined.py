"""The Manor_01 roof: thick split-wood courses over a dark timber structure."""
import math
import random

from mathutils import Vector


def _paint(ob, colours):
    layer = ob.data.color_attributes.get('Color')
    if layer is None:
        layer = ob.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
    for polygon, colour in zip(ob.data.polygons, colours):
        for index in polygon.loop_indices:
            layer.data[index].color = (*colour, 1.0)
    ob.data.color_attributes.active_color = layer
    ob['preserve_authored_color'] = True
    return ob


def _timber(g, name, a, b, width, depth=None, tone=(.35, .31, .26)):
    ob = g['beam'](name, a, b, width, depth, 'Timber', 'MainRoof', .0015)
    a, b = Vector(a), Vector(b)
    direction = (b-a).normalized()
    side = direction.cross(Vector((0, 0, 1)))
    if side.length < .01:
        side = direction.cross(Vector((0, 1, 0)))
    side.normalize()
    offset = sum(ord(c) for c in name) * .173
    for loop in ob.data.loops:
        p = ob.data.vertices[loop.vertex_index].co-a
        ob.data.uv_layers.active.data[loop.index].uv = (p.dot(side)*1.6+offset, p.dot(direction)*1.12)
    return _paint(ob, [tone]*len(ob.data.polygons))


def _rail(g, name, points, width, depth, tone):
    """A continuous, subtly curved, clipped-edge timber fascia."""
    points = [Vector(p) for p in points]
    outline = [(-.40, -.5), (.40, -.5), (.5, -.40), (.5, .40),
               (.40, .5), (-.40, .5), (-.5, .40), (-.5, -.40)]
    verts, uv, faces, distance = [], [], [], 0.0
    for j, p in enumerate(points):
        if j:
            distance += (p-points[j-1]).length
        tangent = (points[min(j+1, len(points)-1)]-points[max(0, j-1)]).normalized()
        across = tangent.cross(Vector((0, 0, 1))).normalized()
        up = across.cross(tangent).normalized()
        for k, (x, z) in enumerate(outline):
            verts.append(p+across*x*width+up*z*depth)
            uv.append((k/8*.48, distance*1.05))
        if j:
            for k in range(8):
                faces.append(((j-1)*8+k, (j-1)*8+(k+1)%8, j*8+(k+1)%8, j*8+k))
    faces += [tuple(reversed(range(8))), tuple(range((len(points)-1)*8, len(points)*8))]
    ob = g['mesh'](name, verts, faces, 'Timber', uv, 'MainRoof')
    return _paint(ob, [tone]*len(faces))


def roof_patch(g, a, b, c, d, label, rows=8, material='Thatch', tint=(.91, .77, .58)):
    """One authored roof face, also used by the manor's small gate roof.

    a/b are the eave corners and c/d their corresponding upper corners.
    Every shingle is a closed editable mesh island with its own grain crop,
    split butt, taper, restrained cup and overlapping tail.
    """
    a, b, c, d = map(Vector, (a, b, c, d))
    rng = random.Random(118056 + sum((i+1)*ord(ch) for i, ch in enumerate(label)))
    normal = (b-a).cross(c-a).normalized()
    slope_length = ((c+d-a-b)/2).length
    corner_lift = .055 if (b-a).length < 6 else .09

    def surface(u, t):
        p = a.lerp(b, u).lerp(c.lerp(d, u), t)
        # The rise is visible at the eave corners without temple-like curls.
        p.z += corner_lift * abs(2*u-1)**7 * max(0, 1-t)**3
        p.z -= .026*math.sin(math.pi*u)*max(0, 1-t)**2
        p.z -= .025*math.sin(math.pi*max(0, min(1, t)))
        return p

    # Dark timber sheathing gives real depth below the lapped, chipped edges.
    deck_v, deck_uv, deck_f = [], [], []
    for j in range(5):
        for i in range(17):
            deck_v.append(surface(i/16, j/4)-normal*.025)
            deck_uv.append((i/16*(b-a).length*.8, j/4*slope_length*1.2))
    for j in range(4):
        for i in range(16):
            k = j*17+i
            deck_f.append((k, k+1, k+18, k+17))
    deck = g['mesh'](label+' dark sheathing beneath cedar', deck_v, deck_f, 'Timber', deck_uv, 'MainRoof')
    solid = deck.modifiers.new('Actual sheathing thickness', 'SOLIDIFY')
    solid.thickness = .048
    _paint(deck, [(.27, .245, .205)]*len(deck_f))

    verts, uv, faces, colours = [], [], [], []
    cross = (0., .19, .51, .79, 1.)
    length_stations = (0., .17, .57, 1.)
    boundary = [0, 1, 2, 3, 4, 9, 14, 19, 18, 17, 16, 15, 10, 5]
    for row in range(rows):
        course_t = row/rows
        course_width = (a.lerp(c, course_t)-b.lerp(d, course_t)).length
        cursor = -rng.uniform(.05, .22) if row else -.015
        while cursor < course_width:
            width = rng.uniform(.175, .315)
            left = max(0., cursor)/course_width
            right = min(course_width, cursor+width-.0025)/course_width
            cursor += width
            if right-left < .004:
                continue
            jitter = rng.uniform(-.024, .024)/max(.5, slope_length)
            lo = course_t+jitter
            hi = min(1.012, course_t+rng.uniform(1.73, 2.06)/rows)
            thickness = rng.uniform(.024, .039)
            roll, cup = rng.uniform(-.004, .004), rng.uniform(.001, .005)
            front_edge = [rng.uniform(-.006, .007)/slope_length for _ in cross]
            if rng.random() < .30:
                front_edge[rng.choice((1, 2, 3))] += rng.uniform(.012, .035)/slope_length
            crop_x, crop_y = rng.uniform(0, 8), rng.uniform(0, 8)
            grain_width = width*rng.uniform(1.4, 2.0)
            grain_length = (hi-lo)*slope_length*rng.uniform(.82, 1.35)
            start = len(verts)
            for underside in (False, True):
                for r in length_stations:
                    for col, q in enumerate(cross):
                        u = left+(right-left)*q
                        t = lo+(hi-lo)*r+front_edge[col]*(1-r)**3
                        p = surface(u, t)
                        taper = .006+thickness*(1-r)**1.35
                        warp = roll*(q-.5)+cup*math.sin(q*math.pi)*math.sin(r*math.pi)
                        # Split fibre arrises give occasional narrow, shallow channels.
                        fissure = -.0025 if col in (1, 3) else .0
                        height = .009 if underside else .009+taper+warp+fissure
                        verts.append(p+normal*height)
                        uv.append((crop_x+q*grain_width, crop_y+r*grain_length))
            weather = rng.uniform(.81, 1.16)
            hue = (rng.uniform(.97, 1.035), rng.uniform(.975, 1.025), rng.uniform(.96, 1.04))
            base = tuple(min(1., tint[k]*weather*hue[k]) for k in range(3))
            for back in (False, True):
                offset = start+(20 if back else 0)
                for r in range(3):
                    for col in range(4):
                        k = offset+r*5+col
                        face = (k, k+1, k+6, k+5)
                        faces.append(tuple(reversed(face)) if back else face)
                        shade = .73 if back else rng.uniform(.96, 1.035)
                        if not back and col in (0, 3):
                            shade *= .97
                        colours.append(tuple(min(1., v*shade) for v in base))
            for j, index in enumerate(boundary):
                other = boundary[(j+1)%len(boundary)]
                faces.append((start+index, start+20+index, start+20+other, start+other))
                colours.append(tuple(v*.70 for v in base))
    ob = g['mesh'](label+' individually split overlapping cedar courses', verts, faces, material, uv, 'MainRoof')
    _paint(ob, colours)
    return ob


def build_roof(g):
    """Create only Manor_MainRoof geometry in the caller's existing collection."""
    skirt = [
        ((-5.6, -3.7, 3.58), (5.6, -3.7, 3.58), (-3.95, -2.53, 4.36), (3.95, -2.53, 4.36), 'front'),
        ((5.6, 3.7, 3.58), (-5.6, 3.7, 3.58), (3.95, 2.53, 4.36), (-3.95, 2.53, 4.36), 'rear'),
        ((-5.6, 3.7, 3.58), (-5.6, -3.7, 3.58), (-3.95, 2.53, 4.36), (-3.95, -2.53, 4.36), 'west'),
        ((5.6, -3.7, 3.58), (5.6, 3.7, 3.58), (3.95, -2.53, 4.36), (3.95, 2.53, 4.36), 'east'),
    ]
    for a, b, c, d, label in skirt:
        roof_patch(g, a, b, c, d, 'Manor lower '+label, 6)
        a, b, c, d = map(Vector, (a, b, c, d))
        count = round((b-a).length/.32)
        for i in range(count+1):
            t = i/count
            outer = a.lerp(b, t)+Vector((0, 0, -.135+.09*abs(2*t-1)**7))
            inner = c.lerp(d, t)+Vector((0, 0, -.13))
            _timber(g, 'Manor exposed roof rafter '+label+str(i), outer, inner, .092, .12, (.42, .36, .28))
        for depth, height, width, tone in [(.19, -.125, .15, (.29, .25, .20)),
                                             (.064, -.255, .17, (.23, .21, .18)),
                                             (.065, -.020, .11, (.43, .36, .28))]:
            points = []
            for i in range(17):
                t = i/16
                p = a.lerp(b, t)
                p.z += height+.09*abs(2*t-1)**7-.026*math.sin(math.pi*t)
                points.append(p)
            _rail(g, 'Manor layered roof fascia '+label+str(height), points, width, depth, tone)

    roof_patch(g, (-4.12, 2.80, 4.32), (-4.12, -2.80, 4.32), (0, 2.80, 6.0), (0, -2.80, 6.0), 'Manor upper west', 15)
    roof_patch(g, (4.12, -2.80, 4.32), (4.12, 2.80, 4.32), (0, -2.80, 6.0), (0, 2.80, 6.0), 'Manor upper east', 15)

    # Fine board joints remain in shadow behind the heavy gable framing.
    rng = random.Random(56118)
    for sign in (-1, 1):
        y = sign*2.735
        x = -4.03
        while x < 4.02:
            width = min(rng.uniform(.15, .245), 4.03-x)
            x0, x1 = x+.002, x+width-.002
            z0, z1 = 5.98-abs(x0)*.403, 5.98-abs(x1)*.403
            verts = [(x0, y-.025, 4.30), (x1, y-.025, 4.30), (x1, y-.025, z1), (x0, y-.025, z0),
                     (x0, y+.025, 4.30), (x1, y+.025, 4.30), (x1, y+.025, z1), (x0, y+.025, z0)]
            crop = rng.uniform(0, 8)
            uv = [((p[0]-x)*1.8+crop, (p[2]-4.30)*1.15) for p in verts]
            faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            ob = g['mesh']('Manor roof gable shadowed cedar infill', verts, faces, 'Timber', uv, 'MainRoof')
            value = rng.uniform(.83, 1.1)
            _paint(ob, [(.43*value, .36*value, .28*value)]*6)
            x += width
        outward = y+sign*.075
        for side in (-1, 1):
            _timber(g, 'Manor roof gable carved verge', (side*4.22, outward, 4.28), (0, outward, 6.05), .16, .19, (.29, .245, .20))
            _timber(g, 'Manor roof gable inner verge', (side*3.9, outward+sign*.014, 4.45), (0, outward+sign*.014, 6.04), .065, .07, (.46, .37, .27))
        _timber(g, 'Manor roof gable main tie', (-4.15, outward, 4.36), (4.15, outward, 4.36), .18, .19)
        _timber(g, 'Manor roof gable upper tie', (-2.75, outward, 4.87), (2.75, outward, 4.87), .115, .135)
        for x in (-2.62, -1.31, 0, 1.31, 2.62):
            _timber(g, 'Manor roof gable upright', (x, outward, 4.36), (x, outward, 5.95-abs(x)*.403), .11 if x else .17, .13)
        # Smaller joinery, deliberately subordinate to the roof's broad shape.
        for side in (-1, 1):
            _timber(g, 'Manor roof gable diagonal brace', (side*.16, outward, 4.94), (side*1.25, outward, 5.41), .075, .085, (.40, .33, .25))

    # Paired ridge timbers, pegged cap and close rope binding; height stays 6.3 m.
    for x in (-.115, .115):
        _rail(g, 'Manor substantial bound roof ridge', [(x, -3.13, 6.075), (x, 0, 6.11), (x, 3.13, 6.075)], .145, .145, (.33, .27, .205))
    _rail(g, 'Manor weather cap over ridge', [(0, -3.15, 6.17), (0, 0, 6.195), (0, 3.15, 6.17)], .39, .075, (.48, .385, .275))
    for j, y in enumerate((-2.89, -1.93, -.98, 0, .97, 1.92, 2.88)):
        z = 6.235-.018*abs(y)/3
        _timber(g, 'Manor ridge restraining crosspiece '+str(j), (-.31, y, z), (.31, y, z), .095, .075, (.39, .305, .22))
        for x in (-.115, .115):
            ob = g['lash']('Manor tight ridge fibre binding', (x, y, 6.105-.018*abs(y)/3), 'Y', .090, 3)
            _paint(ob, [(.61, .49, .33)]*len(ob.data.polygons))
    for y in (-3.03, 3.03):
        _timber(g, 'Manor restrained crossed roof end joinery A', (-.35, y, 5.92), (.35, y, 6.245), .09, .105, (.29, .235, .175))
        _timber(g, 'Manor restrained crossed roof end joinery B', (.35, y-.045, 5.92), (-.35, y-.045, 6.245), .09, .105, (.29, .235, .175))
