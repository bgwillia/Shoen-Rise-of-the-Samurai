"""Low-relief chased metalwork for Tachi01; axes U × V face out of the fitting."""
import math

from mathutils import Vector


def _frame(origin, axis_u, axis_v):
    origin = Vector(origin)
    u = Vector(axis_u).normalized()
    v = Vector(axis_v)
    v = (v - u * u.dot(v)).normalized()
    n = u.cross(v).normalized()
    return origin, u, v, n


def _point(frame, x, y, z):
    o, u, v, n = frame
    return o + x * u + y * v + z * n


def _relief(g, name, frame, petals, radius, tile):
    """Closed metal petals with a bevel shoulder, raised fold and flat underside."""
    vertices, faces, uvs, strips = [], [], [], []
    samples = (0., .08, .20, .36, .54, .71, .85, .95, 1.)
    widths = (.16, .49, .80, .98, 1., .93, .74, .44, .12)
    across = (-1., -.84, -.31, 0., .31, .84, 1.)
    # Different slopes make a chased ridge, not an inflated ellipsoid.
    ridge = (.0, .019, .039, .072, .039, .019, .0)
    groove_vertices, groove_faces, groove_uvs = [], [], []
    for petal_index, (angle, inner, outer, width, height, bend) in enumerate(petals):
        ca, sa = math.cos(angle), math.sin(angle)

        def local(s, transverse, lift):
            radial = inner + (outer - inner) * s
            tangent = transverse + bend * math.sin(math.pi * s)
            return (radial * ca - tangent * sa,
                    radial * sa + tangent * ca, lift)

        start = len(vertices)
        for row, s in enumerate(samples):
            for col, t in enumerate(across):
                lift = height + radius * ridge[col] * (0.60 + .40 * math.sin(math.pi * s))
                xyh = local(s, t * width * widths[row], lift)
                vertices.append(_point(frame, *xyh))
                uvs.append((.5 + xyh[0] / (2.1 * radius), .5 + xyh[1] / (2.1 * radius)))
        for row in range(len(samples) - 1):
            for col in range(6):
                a = start + row * 7 + col
                faces.append((a, a + 1, a + 8, a + 7))
                strips.append((petal_index, col))
        perimeter = [start + col for col in range(7)]
        perimeter += [start + row * 7 + 6 for row in range(1, len(samples))]
        perimeter += [start + (len(samples) - 1) * 7 + col for col in range(5, -1, -1)]
        perimeter += [start + row * 7 for row in range(len(samples) - 2, 0, -1)]
        bottom = []
        o, u, v, n = frame
        for top_index in perimeter:
            p = vertices[top_index]
            bottom.append(len(vertices))
            vertices.append(p - n * ((p - o).dot(n) - height + radius * .011))
            uvs.append(uvs[top_index])
        for i in range(len(perimeter)):
            j = (i + 1) % len(perimeter)
            faces.append((perimeter[i], bottom[i], bottom[j], perimeter[j]))
            strips.append(None)
        faces.append(tuple(reversed(bottom)))
        strips.append(None)

        # Two fine tapering incised strokes flank the central hammered fold.
        # Dark strips sit in the low shoulder; the raised center catches light.
        for side in (-1., 1.):
            first = len(groove_vertices)
            for row in range(1, len(samples) - 1):
                s = samples[row]
                center = side * width * widths[row] * .43
                line_width = radius * .008 * math.sin(math.pi * s)
                lift = height + radius * .0345 * (0.60 + .40 * math.sin(math.pi * s))
                for offset in (-line_width, line_width):
                    xyh = local(s, center + offset, lift)
                    groove_vertices.append(_point(frame, *xyh))
                    groove_uvs.append((.4, .4))
            for row in range(len(samples) - 3):
                a = first + row * 2
                groove_faces.append((a, a + 1, a + 3, a + 2))

    ob = g.mesh(name, vertices, faces, tile, uvs)
    # Smooth along a petal while preserving the transverse facets of its fold.
    normals = {}
    for polygon, strip in zip(ob.data.polygons, strips):
        if strip is not None:
            for vi in polygon.vertices:
                key = (vi, strip)
                normals[key] = normals.get(key, Vector()) + polygon.normal
    split = []
    for polygon, strip in zip(ob.data.polygons, strips):
        polygon.use_smooth = strip is not None
        for vi in polygon.vertices:
            split.append(tuple(normals[(vi, strip)].normalized() if strip is not None else polygon.normal))
    ob.data.normals_split_custom_set(split)
    grooves = g.mesh(name + " incised shadow lines", groove_vertices, groove_faces, 0, groove_uvs, False)
    return ob, grooves


def _lathe(g, name, frame, profile, tile=2, sides=48):
    vertices, faces, uvs = [], [], []
    outer = max(r for r, _ in profile)
    for r, height in profile:
        for i in range(sides):
            a = math.tau * i / sides
            vertices.append(_point(frame, r * math.cos(a), r * math.sin(a), height))
            uvs.append((.5 + r * math.cos(a) / (outer * 2.1),
                        .5 + r * math.sin(a) / (outer * 2.1)))
    for row in range(len(profile) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((row * sides + i, row * sides + j,
                          (row + 1) * sides + j, (row + 1) * sides + i))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(profile) - 1) * sides + i for i in range(sides)))
    return g.mesh(name, vertices, faces, tile, uvs)


def flower(g, add, group, origin, axis_u, axis_v, radius=.009):
    """Layered 12+8 petal crest; U × V must point away from the metal surface."""
    frame = _frame(origin, axis_u, axis_v)
    # A thin scalloped black recess separates the flower from brass fittings.
    vertices, faces, uv = [], [], []
    sides = 96
    for height in (-radius * .004, radius * .013):
        for i in range(sides):
            a = math.tau * i / sides
            r = radius * (.85 + .075 * math.cos(12 * a))
            vertices.append(_point(frame, r * math.cos(a), r * math.sin(a), height))
            uv.append((.5 + .43 * math.cos(a), .5 + .43 * math.sin(a)))
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    faces.extend((tuple(reversed(range(sides))), tuple(range(sides, sides * 2))))
    add(group, g.mesh("Chrysanthemum recessed silhouette", vertices, faces, 0, uv, False))

    outer = [(math.tau * i / 12, radius * .21, radius,
              radius * .139, radius * .025, radius * .023) for i in range(12)]
    inner = [(math.tau * (i + .38) / 8, radius * .14, radius * .64,
              radius * .104, radius * .077, -radius * .015) for i in range(8)]
    for name, petals, tile in (("Chased outer chrysanthemum petals", outer, 2),
                               ("Layered inner chrysanthemum petals", inner, 11)):
        metal, shadows = _relief(g, name, frame, petals, radius, tile)
        add(group, metal)
        add(group, shadows)
    profile = [(r * radius, h * radius) for r, h in (
        (.025, .09), (.215, .09), (.229, .104), (.223, .128),
        (.197, .139), (.178, .132), (.163, .113), (.137, .113),
        (.122, .145), (.105, .167), (.079, .178), (.025, .179))]
    add(group, _lathe(g, "Chrysanthemum concentric chased heart", frame, profile, 2, 40))


def vine_frieze(g, add, group, origin, axis_u, axis_v, width, height):
    """Shallow scrolling stem and pointed folded leaves inside a fitting face."""
    frame = _frame(origin, axis_u, axis_v)
    scale = min(width, height)
    wire = scale * .018
    # Asymmetric S-curve avoids a repetitive stamped row of round flowers.
    points = []
    for i in range(49):
        t = i / 48
        points.append(_point(frame, width * (t - .5) * .86,
                             height * .18 * math.sin(math.tau * t), scale * .020))
    add(group, g.tube("Chased vine continuous stem", points, wire, 2, 6))

    for side in (-1., 1.):
        center_x, center_y = side * width * .22, -side * height * .11
        scroll = []
        for i in range(49):
            t = i / 48
            angle = side * (math.pi * .25 + math.tau * 1.14 * t)
            r = scale * (.20 * (1 - t) + .023)
            scroll.append(_point(frame, center_x + r * math.cos(angle),
                                 center_y + r * math.sin(angle), scale * .018))
        add(group, g.tube("Spiral vine tendril", scroll, wire * .70, 2, 6))

    for i, t in enumerate((.13, .29, .44, .60, .76, .88)):
        x = width * (t - .5) * .86
        y = height * .18 * math.sin(math.tau * t)
        tangent = math.atan2(height * .18 * math.tau * math.cos(math.tau * t), width * .86)
        angle = tangent + (-1 if i % 2 else 1) * math.radians(55)
        length = min(width * .185, height * .27)
        origin_leaf = _point(frame, x, y, scale * .014)
        leaf_frame = _frame(origin_leaf, frame[1], frame[2])
        petals = [(angle, 0, length, length * .235, scale * .015, length * .042)]
        metal, shadows = _relief(g, "Pointed folded vine leaf", leaf_frame, petals, length, 11)
        add(group, metal)
        add(group, shadows)
