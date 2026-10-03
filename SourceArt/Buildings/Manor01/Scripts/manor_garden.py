"""Small authored garden module; build_garden receives the manor kit globals."""


def build_garden(g):
    bpy, math, random, Vector = (g[k] for k in ('bpy', 'math', 'random', 'Vector'))
    mesh, tube, fieldstone = (g[k] for k in ('mesh', 'tube', 'fieldstone'))
    src = g['src']
    before = set(src.objects)
    rng = random.Random(118003)
    wood_group, leaf_group = 'GardenTreeTimber', 'GardenTreeNeedles'

    def wood(name, centers, radii, sides=12):
        """Tapered bent rings with longitudinal, uneven bark ridges."""
        pts = [Vector(p) for p in centers]
        verts, uvs, faces = [], [], []
        distance = 0.0
        for j, (p, radius) in enumerate(zip(pts, radii)):
            if j:
                distance += (p - pts[j - 1]).length
            tangent = (pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]).normalized()
            side = tangent.cross(Vector((0, 1, 0))).normalized()
            up = tangent.cross(side).normalized()
            for i in range(sides):
                angle = math.tau * i / sides
                ridge = 1 + .12 * math.sin(i * 2.63) + .055 * math.sin(i * 4.8 + j * .7)
                v = p + radius * ridge * (side * math.cos(angle) + up * math.sin(angle))
                verts.append(v)
                uvs.append((i / sides * 1.3, distance * 1.25))
                if j:
                    a, b = (j - 1) * sides + i, (j - 1) * sides + (i + 1) % sides
                    faces.append((a, b, b + sides, a + sides))
        faces.extend([tuple(reversed(range(sides))),
                      tuple(range((len(pts) - 1) * sides, len(pts) * sides))])
        ob = mesh(name, verts, faces, 'Timber', uvs, wood_group)
        for face in ob.data.polygons:
            face.use_smooth = len(face.vertices) == 4
        return ob

    # Deliberate S-shaped trunk: lean left, recover, then end in a short right leader.
    wood('Manor pine bent bark trunk',
         [(0, 0, -.025), (.015, .01, .12), (-.045, .025, .37),
          (-.18, .015, .73), (-.30, .035, 1.08), (-.26, .06, 1.39),
          (-.07, .105, 1.72), (.12, .13, 2.03), (.13, .15, 2.31),
          (.035, .15, 2.57), (.12, .145, 2.78), (.24, .15, 3.015)],
         [.22, .18, .145, .127, .113, .102, .089, .072, .056, .041, .027, .006], 16)
    for i, angle in enumerate((.3, 1.6, 2.65, 3.8, 5.15)):
        end = Vector((math.cos(angle) * .43, math.sin(angle) * .39, -.012))
        wood('Manor pine spreading surface root %02d' % i,
             [(0, 0, .15), tuple(end * .47 + Vector((0, 0, .038))), end],
             [.087, .060, .008], 8)

    # Centers, spread, and trunk junctions are authored individually, never a sphere crown.
    pads = [
        ((-1.00, -.075, 1.48), (.79, .46, .14), (-.285, .035, 1.12)),
        ((.88, .18, 1.82), (.70, .46, .15), (-.235, .06, 1.44)),
        ((-.60, .47, 2.10), (.74, .42, .14), (-.06, .105, 1.73)),
        ((.025, -.47, 2.31), (.64, .42, .13), (.125, .135, 2.045)),
        ((.62, .275, 2.56), (.56, .38, .12), (.115, .15, 2.29)),
        ((-.27, .15, 2.79), (.52, .36, .12), (.055, .15, 2.55)),
        ((.245, .15, 2.985), (.34, .265, .10), (.15, .145, 2.82)),
    ]
    for index, (center, spread, attachment) in enumerate(pads):
        c, joint = Vector(center), Vector(attachment)
        direction = c - joint
        wood('Manor pine open main bough %02d' % index,
             [joint, joint + direction * .4 + Vector((0, 0, -.055)),
              c + Vector((0, 0, -.07)), c + Vector((.12, 0, -.025))],
             [.066 - index * .006, .045 - index * .004, .022, .005], 9)
        verts, faces, uvs = [], [], []

        def spray(position, angle, length, width, height):
            """Flat serrated needle mass with a peaked spine and ragged needle tips."""
            origin = Vector(position)
            along = Vector((math.cos(angle), math.sin(angle), 0))
            across = Vector((-math.sin(angle), math.cos(angle), 0))
            start = len(verts)
            # Two offset ridge points keep the tuft angular and branch-like, not bulbous.
            verts.extend([origin + Vector((0, 0, height)),
                          origin + Vector((0, 0, -height * .35))])
            uvs.extend([(.5, .5), (.5, .5)])
            edge_count = 18
            for j in range(edge_count):
                a = math.tau * j / edge_count
                tooth = (1.0 if j % 2 else .70) * rng.uniform(.88, 1.10)
                p = origin + along * (math.cos(a) * length * tooth)
                p += across * (math.sin(a) * width * tooth)
                p.z += rng.uniform(-.012, .018)
                verts.append(p)
                uvs.append((.5 + math.cos(a) * .5, .5 + math.sin(a) * .5))
            for j in range(edge_count):
                edge, nxt = start + 2 + j, start + 2 + (j + 1) % edge_count
                faces.extend([(start, edge, nxt), (start + 1, nxt, edge)])
            # A few real tapered blades break the outer contour at ordinary viewing distances.
            for j in range(4):
                a = angle + rng.uniform(-1.3, 1.3)
                axis = Vector((math.cos(a), math.sin(a), rng.uniform(.02, .15)))
                side = Vector((-math.sin(a), math.cos(a), 0)) * .011
                base = origin + along * rng.uniform(.015, length * .7)
                tip = base + axis * rng.uniform(.075, .13)
                q = len(verts)
                verts.extend([base - side, base + side, tip,
                              base + Vector((0, 0, .014))])
                uvs.extend([(0, 0), (1, 0), (.5, 1), (.5, 0)])
                faces.extend([(q, q + 1, q + 2), (q + 1, q + 3, q + 2),
                              (q + 3, q, q + 2)])

        # Low, irregular sprays follow eight twigs and overlap into a broken horizontal pad.
        phase = index * .63
        for arm in range(8):
            angle = arm * math.tau / 8 + phase + rng.uniform(-.15, .15)
            outward = Vector((math.cos(angle) * spread[0], math.sin(angle) * spread[1], 0))
            outward *= rng.uniform(.80, 1.07)
            twig_start = c + Vector((0, 0, -.065))
            twig_end = c + outward * .88 + Vector((0, 0, -.025))
            wood('Manor pine visible twig %02d %02d' % (index, arm),
                 [twig_start, twig_start.lerp(twig_end, .53) + Vector((0, 0, -.012)), twig_end],
                 [.016, .009, .0025], 6)
            for step in range(1, 5):
                t = step / 4
                position = c + outward * (t * .81)
                position.z += spread[2] * (.34 - .42 * t) + rng.uniform(-.018, .018)
                position += Vector((rng.uniform(-.045, .045), rng.uniform(-.035, .035), 0))
                scale = .8 if index == 6 else 1.0
                spray(position, angle + rng.uniform(-.35, .35),
                      rng.uniform(.125, .19) * scale, rng.uniform(.092, .14) * scale,
                      rng.uniform(.025, .055) * scale)
        spray(c + Vector((0, 0, .045)), phase, .19, .145, .055)
        ob = mesh('Manor pine irregular needle pad %02d' % index,
                  verts, faces, 'Leaf', uvs, leaf_group)
        ob['shape'] = 'Flattened pine branch sprays with serrated opaque needle edges'

    # One small exposed spur emphasizes the living branch structure in the canopy gap.
    wood('Manor pine short old branch spur',
         [(-.17, .08, 1.58), (-.38, -.035, 1.80), (-.52, -.055, 1.84)],
         [.034, .022, .009], 8)

    # Reuse the established bedded fieldstone mesh; retain its textured stone shader.
    stones_before = set(src.objects)
    state = random.getstate()
    try:
        random.seed(118003)
        fieldstone('Manor garden broad low rock', (.49, -.53, .12), (.43, .29, .22))
        fieldstone('Manor garden small companion rock', (-.47, .36, .075), (.25, .18, .14))
    finally:
        random.setstate(state)
    stones = [ob for ob in src.objects if ob not in stones_before]
    if 'groups' in g:
        for group in g['groups'].values():
            group[:] = [ob for ob in group if ob not in stones]
        g['groups'].setdefault('GardenRocks', []).extend(stones)

    # Three modest clumps; opaque folded blades reuse the market leaf material.
    verts, faces, uvs = [], [], []
    for x, y in ((.30, -.37), (-.43, .23), (.18, .22)):
        for i in range(7):
            a = rng.uniform(0, math.tau)
            base = Vector((x + rng.uniform(-.055, .055), y + rng.uniform(-.05, .05), .006))
            length = rng.uniform(.10, .20)
            direction = Vector((math.cos(a), math.sin(a), 0))
            side = Vector((-math.sin(a), math.cos(a), 0)) * rng.uniform(.007, .013)
            middle = base + direction * length * .20 + Vector((0, 0, length * .70))
            tip = base + direction * length * .59 + Vector((0, 0, length))
            j = len(verts)
            verts.extend([base - side, base + side, middle - side * .60,
                          middle + side * .60, middle + Vector((0, 0, .005)), tip])
            uvs.extend([(0, 0), (1, 0), (0, .6), (1, .6), (.5, .6), (.5, 1)])
            faces.extend([(j, j + 1, j + 4), (j, j + 4, j + 2),
                          (j + 1, j + 3, j + 4), (j + 2, j + 4, j + 5),
                          (j + 4, j + 3, j + 5)])
    mesh('Manor garden sparse grass blades', verts, faces, 'Leaf', uvs, 'GardenGrass')
    created = [ob for ob in src.objects if ob not in before]
    for ob in created:
        ob['module'] = 'Manor_01 pine garden'
    return created
