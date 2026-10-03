"""Dense, trained evergreen garden for the refined Manor_01 source."""


def build_garden(g):
    bpy, math, random, Vector = (g[k] for k in ('bpy', 'math', 'random', 'Vector'))
    mesh, src = g['mesh'], g['src']
    before = set(src.objects)
    rng = random.Random(118009)

    def tint(ob, colors):
        attr = ob.data.color_attributes.get('Color')
        if attr is None:
            attr = ob.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
        for face, color in zip(ob.data.polygons, colors):
            for loop in face.loop_indices:
                attr.data[loop].color = (*color, 1)
        ob.data.color_attributes.active_color = attr

    def wood(name, controls, radii, sides=12, detail=3):
        # Interpolated crooked limbs have taper and persistent longitudinal bark ridges.
        centers, sizes = [], []
        for j in range(len(controls) - 1):
            a, b = Vector(controls[j]), Vector(controls[j + 1])
            for k in range(detail):
                t = k / detail
                centers.append(a.lerp(b, t))
                sizes.append(radii[j] * (1 - t) + radii[j + 1] * t)
        centers.append(Vector(controls[-1])); sizes.append(radii[-1])
        vv, ff, uv, colors = [], [], [], []
        distance = 0.0
        for j, (center, radius) in enumerate(zip(centers, sizes)):
            if j:
                distance += (center - centers[j - 1]).length
            axis = (centers[min(j + 1, len(centers) - 1)] - centers[max(0, j - 1)]).normalized()
            side = axis.cross(Vector((0, 1, 0))).normalized()
            cross = axis.cross(side).normalized()
            for k in range(sides):
                a = math.tau * k / sides + .075 * math.sin(j * .42)
                bark = 1 + .13 * math.sin(k * 2.79) + .06 * math.sin(k * 4.31 + j * .63)
                vv.append(center + radius * bark * (side * math.cos(a) + cross * math.sin(a)))
                uv.append((k / sides * 1.7, distance * 1.8))
                if j:
                    p, q = (j - 1) * sides + k, (j - 1) * sides + (k + 1) % sides
                    ff.append((p, q, q + sides, p + sides))
                    shade = .65 + .19 * math.sin(k * 2.79) + rng.uniform(-.055, .055)
                    colors.append((shade, shade * .93, shade * .80))
        ff += [tuple(reversed(range(sides))), tuple(range(len(vv) - sides, len(vv)))]
        colors += [(.72, .65, .53), (.58, .50, .39)]
        ob = mesh(name, vv, ff, 'Timber', uv, 'GardenTreeTimber')
        for face in ob.data.polygons:
            face.use_smooth = len(face.vertices) == 4
        tint(ob, colors)
        return ob

    trunk = [(0, 0, -.015), (.025, .015, .13), (-.015, .025, .36),
             (-.17, .02, .69), (-.295, .03, 1.02), (-.29, .06, 1.29),
             (-.125, .105, 1.60), (.09, .135, 1.93), (.125, .16, 2.22),
             (.025, .145, 2.49), (.12, .13, 2.75), (.265, .145, 2.99)]
    wood('Manor refined pine deeply ridged bent trunk', trunk,
         [.24, .185, .155, .132, .118, .105, .090, .074, .058, .043, .027, .008], 24, 4)
    for i, a in enumerate((.16, 1.33, 2.48, 3.54, 4.85, 5.70)):
        direction = Vector((math.cos(a), math.sin(a), 0))
        wood('Manor refined pine tapering root %02d' % i,
             [(0, 0, .17), direction * .22 + Vector((0, 0, .065)),
              direction * rng.uniform(.42, .56) + Vector((0, 0, -.018))],
             [.09, .053, .006], 10, 2)

    # The asymmetric, overlapping crowns retain clear air below their long lateral limbs.
    pads = [
        ((-1.035, -.04, 1.44), (.79, .46, .18), (-.285, .04, 1.035)),
        ((.84, .18, 1.79), (.75, .47, .20), (-.265, .065, 1.34)),
        ((-.60, .43, 2.055), (.77, .47, .20), (-.09, .11, 1.655)),
        ((.025, -.405, 2.27), (.67, .46, .18), (.10, .14, 1.985)),
        ((.625, .285, 2.52), (.61, .43, .19), (.11, .155, 2.235)),
        ((-.24, .18, 2.76), (.56, .39, .19), (.03, .145, 2.49)),
        ((.285, .14, 2.945), (.39, .31, .17), (.15, .135, 2.80)),
    ]
    # Icosahedral micro-clumps supply broken internal mass, never a broad polygon leaf.
    phi = (1 + math.sqrt(5)) / 2
    ico = [Vector(v).normalized() for v in
           [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
            (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
            (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]]
    ico_faces = [(0,11,5), (0,5,1), (0,1,7), (0,7,10), (0,10,11),
                 (1,5,9), (5,11,4), (11,10,2), (10,7,6), (7,1,8),
                 (3,9,4), (3,4,2), (3,2,6), (3,6,8), (3,8,9),
                 (4,9,5), (2,4,11), (6,2,10), (8,6,7), (9,8,1)]

    for pad, (center, spread, joint) in enumerate(pads):
        c, origin = Vector(center), Vector(joint)
        limb = c - origin
        wood('Manor refined pine long trained bough %02d' % pad,
             [origin, origin + limb * .36 + Vector((0, 0, -.065)),
              c + Vector((0, 0, -.125)), c + Vector((.14, .015, -.045))],
             [.068 - pad * .006, .046 - pad * .004, .024, .006], 12, 3)
        vv, ff, uv, colors = [], [], [], []

        def face(indices, color):
            ff.append(tuple(indices)); colors.append(color)

        def cluster(position, direction, size, brightness):
            # Every cluster is a small irregular 3D growth tuft with eight tapered needles.
            p = Vector(position)
            along = Vector(direction).normalized()
            side = along.cross(Vector((0, 0, 1))).normalized()
            up = side.cross(along).normalized()
            hue = rng.uniform(-.025, .025)
            col = (.27 * brightness + hue, .40 * brightness + hue, .16 * brightness)
            start = len(vv)
            for vertex in ico:
                jitter = rng.uniform(.79, 1.18)
                point = p + (along * vertex.x * .092 + side * vertex.y * .058
                             + up * vertex.z * .050) * size * jitter
                vv.append(point); uv.append((vertex.x * .5 + .5, vertex.z * .5 + .5))
            for indices in ico_faces:
                shade = rng.uniform(.86, 1.075)
                face([start + v for v in indices], tuple(v * shade for v in col))
            for n in range(8):
                angle = math.tau * (n + rng.uniform(-.22, .22)) / 8
                radial = side * math.cos(angle) + up * math.sin(angle)
                base = p + along * rng.uniform(-.052, .065) * size + radial * .022 * size
                needle_axis = (along * rng.uniform(.45, .95) + radial * rng.uniform(.65, 1.1)
                               + Vector((0, 0, .19))).normalized()
                length = rng.uniform(.065, .135) * size
                radius = rng.uniform(.0033, .0058) * size
                cross = needle_axis.cross(Vector((0, 0, 1)))
                if cross.length < .01:
                    cross = needle_axis.cross(Vector((0, 1, 0)))
                cross.normalize()
                second = needle_axis.cross(cross).normalized()
                needle_start = len(vv)
                for t, width in ((0, .72), (.59, 1)):
                    bend = Vector((0, 0, -.014 * t * t * size))
                    middle = base + needle_axis * length * t + bend
                    for k in range(3):
                        a = math.tau * k / 3
                        vv.append(middle + radius * width * (cross * math.cos(a) + second * math.sin(a)))
                        uv.append((k / 3, t))
                vv.append(base + needle_axis * length + Vector((0, 0, -.018 * size)))
                uv.append((.5, 1))
                needle_col = tuple(v * rng.uniform(.94, 1.28) for v in col)
                for k in range(3):
                    nxt = (k + 1) % 3
                    face((needle_start + k, needle_start + nxt,
                          needle_start + 3 + nxt, needle_start + 3 + k), needle_col)
                    face((needle_start + 3 + k, needle_start + 3 + nxt, needle_start + 6),
                         tuple(v * 1.055 for v in needle_col))
                face((needle_start + 2, needle_start + 1, needle_start), col)

        phase = pad * .71
        for arm in range(10):
            a = arm * math.tau / 10 + phase + rng.uniform(-.13, .13)
            reach = Vector((math.cos(a) * spread[0], math.sin(a) * spread[1], 0))
            reach *= rng.uniform(.79, 1.06)
            tip = c + reach * .86 + Vector((0, 0, -.055))
            wood('Manor refined pine branching spray %02d %02d' % (pad, arm),
                 [c + Vector((0, 0, -.135)), c + reach * .48 + Vector((0, 0, -.095)), tip],
                 [.018, .009, .0025], 6, 2)
            lateral = Vector((-math.sin(a), math.cos(a), 0))
            for step in range(5):
                t = .17 + step * .175
                for flank in (-1, 1):
                    p = c + reach * t + lateral * flank * rng.uniform(.030, .090)
                    # A changing vertical band gives a deep uneven underside and a soft crown.
                    p.z += spread[2] * (.35 * math.sin(t * math.pi) - .24)
                    p.z += rng.uniform(-.070, .070)
                    p += Vector((rng.uniform(-.025, .025), rng.uniform(-.025, .025), 0))
                    direction = (reach.normalized() + lateral * flank * .40
                                 + Vector((0, 0, rng.uniform(-.04, .22)))).normalized()
                    size = rng.uniform(.81, 1.20) * (.76 if pad == 6 else .90 if pad == 5 else 1)
                    # Low sprays remain cooler and darker; scattered fresh tips catch the light.
                    brightness = rng.uniform(.74, 1.23) * (1.06 if p.z > c.z else .87)
                    cluster(p, direction, size, brightness)
        ob = mesh('Manor refined pine dense needle crown %02d' % pad,
                  vv, ff, 'Leaf', uv, 'GardenTreeNeedles')
        for polygon in ob.data.polygons:
            polygon.use_smooth = True
        tint(ob, colors)
        ob['foliage'] = 'Opaque volumetric micro-clumps and individual bent tapered needle geometry'

    wood('Manor refined pine weathered short bare spur',
         [(-.155, .09, 1.565), (-.36, -.055, 1.78), (-.50, -.10, 1.82)],
         [.036, .022, .007], 10, 3)

    def boulder(name, center, radii, seed):
        vv, ff, uv, cols = [], [], [], []
        n, rings = 24, 11
        for j in range(rings + 1):
            latitude = -math.pi / 2 + math.pi * (j + .06) / (rings + .12)
            for k in range(n):
                a = k * math.tau / n
                rough = 1 + .09 * math.sin(a * 3 + seed) + .045 * math.sin(a * 7 - latitude * 4)
                rough += .035 * math.sin(a * 11 + latitude * 7 + seed)
                x = math.cos(latitude) * math.cos(a) * radii[0] * rough
                y = math.cos(latitude) * math.sin(a) * radii[1] * rough
                z = math.sin(latitude) * radii[2]
                z += .030 * math.sin(a * 3 + latitude * 4) * math.cos(latitude)
                z = max(-radii[2] * .62, z)
                vv.append(Vector(center) + Vector((x + .055 * z, y - .1 * z, z)))
                uv.append((x * 2.2 + y * .3, z * 2.2 + y * .7))
                if j:
                    q, r = (j - 1) * n + k, (j - 1) * n + (k + 1) % n
                    ff.append((q, r, r + n, q + n))
                    shade = .62 + .15 * rng.random() + .07 * math.sin(a * 3 + latitude * 2)
                    cols.append((shade * .94, shade, shade * .89))
        ff += [tuple(reversed(range(n))), tuple(range(len(vv) - n, len(vv)))]
        cols += [(.62, .65, .55), (.73, .76, .68)]
        ob = mesh(name, vv, ff, 'Stone', uv, 'GardenRocks')
        for polygon in ob.data.polygons:
            polygon.use_smooth = True
        tint(ob, cols)

    boulder('Manor refined broad naturally worn garden boulder', (.49, -.54, .155), (.50, .34, .25), 1.4)
    boulder('Manor refined companion garden stone', (-.49, .33, .08), (.30, .22, .14), 3.7)

    # Sparse fine, folded grass adds scale without turning the compound into a garden display.
    vv, ff, uv, colors = [], [], [], []
    for x, y in ((.25, -.38), (-.49, .15), (.20, .28), (.67, -.39)):
        for k in range(15):
            a = rng.uniform(0, math.tau)
            direction = Vector((math.cos(a), math.sin(a), 0))
            cross = Vector((-math.sin(a), math.cos(a), 0))
            p = Vector((x + rng.uniform(-.045, .045), y + rng.uniform(-.045, .045), .008))
            height, width = rng.uniform(.11, .235), rng.uniform(.003, .006)
            start = len(vv)
            for j in range(5):
                t = j / 4
                middle = p + direction * height * t * t * .70 + Vector((0, 0, height * t))
                for s in (-1, 0, 1):
                    vv.append(middle + cross * width * (1 - t) * s
                              + Vector((0, 0, .002 * (1 - abs(s)) * math.sin(t * math.pi))))
                    uv.append(((s + 1) / 2, t))
                if j:
                    q = start + (j - 1) * 3
                    ff.extend([(q, q + 1, q + 4, q + 3), (q + 1, q + 2, q + 5, q + 4)])
                    color = (.30 + .12 * t, .43 + .10 * t, .15 + .06 * t)
                    colors.extend([color, color])
        ob_name = 'Manor refined fine garden grass'
    ob = mesh(ob_name, vv, ff, 'Leaf', uv, 'GardenGrass')
    tint(ob, colors)
    created = [ob for ob in src.objects if ob not in before]
    for ob in created:
        ob['module'] = 'Manor_01 refined pine garden'
    return created
