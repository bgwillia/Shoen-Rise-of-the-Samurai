"""Authored exterior smithing equipment; called by the Smithy01 scene builder."""


def build_props(ns):
    """Build in meters using the parent scene's mesh, beam, tube and materials."""
    mesh, beam, tube = (ns[k] for k in ('mesh', 'beam', 'tube'))
    Vector, math = ns['Vector'], ns['math']
    bpy = ns['bpy']
    rng = ns['random'].Random(118001)

    def block(name, center, size, material, group):
        x, y, z = center
        a, b, c = (v / 2 for v in size)
        verts = [(x + dx * a, y + dy * b, z + dz * c)
                 for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
        return mesh(name, verts, [(0, 2, 3, 1), (4, 5, 7, 6),
                                 (0, 1, 5, 4), (1, 3, 7, 5),
                                 (3, 2, 6, 7), (2, 0, 4, 6)], material, group=group)

    def rings(name, levels, material, group, sides=16):
        # Each level: x, y, z, x radius, y radius. Shared phase preserves grain.
        verts, faces = [], []
        phase = [rng.uniform(-.16, .16) if material == 'Charcoal'
                 else rng.uniform(-.020, .020) for _ in range(sides)]
        for j, (x, y, z, rx, ry) in enumerate(levels):
            for i in range(sides):
                angle = math.tau * i / sides + .012 * math.sin(i * 2.7 + j * .65)
                relief = 1 + phase[i] + .008 * math.sin(i * 1.7 + j * 1.3)
                zz = z
                if material == 'Charcoal':
                    relief += rng.uniform(-.16, .16)
                    zz += rng.uniform(-.022, .022)
                verts.append((x + rx * relief * math.cos(angle),
                              y + ry * relief * math.sin(angle), zz))
                if j:
                    a, b = (j - 1) * sides + i, (j - 1) * sides + (i + 1) % sides
                    faces.append((a, b, b + sides, a + sides))
        faces += [tuple(reversed(range(sides))),
                  tuple(range((len(levels) - 1) * sides, len(levels) * sides))]
        return mesh(name, verts, faces, material, group=group)

    def nail(name, point, group, radius=.013):
        p = Vector(point)
        tube(name, [p, p + Vector((0, -.010, 0))], radius, 'Iron', group, 6)

    def hammer(name, center, group, hanging=False, length=.39):
        x, y, z = center
        if hanging:
            beam(name + ' ash handle', (x, y, z - length), (x, y, z),
                 .027, .031, group=group, rough=.001)
            beam(name + ' forged head', (x - .097, y, z), (x + .090, y, z),
                 .065, .073, 'Iron', group, .001)
            beam(name + ' peen', (x + .08, y, z), (x + .137, y, z),
                 .048, .035, 'Iron', group, .001)
        else:
            beam(name + ' ash handle', (x, y - length, z), (x, y + .018, z),
                 .027, .033, group=group, rough=.001)
            beam(name + ' forged head', (x - .094, y, z), (x + .088, y, z),
                 .066, .069, 'Iron', group, .001)

    # The freestanding anvil has a flared base, narrow waist, flat face and horn.
    g = 'Anvil'
    ax, ay = .55, -1.95
    stump = rings('Anvil stump bark body', [(ax, ay, .018, .256, .250),
                                          (ax - .005, ay, .09, .251, .238),
                                          (ax - .007, ay + .006, .24, .242, .229),
                                          (ax + .003, ay, .43, .235, .225),
                                          (ax, ay, .585, .238, .229)], 'Timber', g, 48)
    for p in stump.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    for i in range(11):
        angle = math.tau * (i + rng.uniform(-.20, .20)) / 11
        points = []
        start, end = rng.uniform(.035, .20), rng.uniform(.36, .565)
        for j in range(5):
            z = start + (end - start) * j / 4
            a = angle + .018 * math.sin(j * 2.1 + i)
            rx = .254 - .033 * z
            ry = .241 - .022 * z
            points.append((ax + math.cos(a) * rx, ay + math.sin(a) * ry, z))
        tube('Interrupted shallow bark fissure', points, rng.uniform(.002, .004),
             'Timber', g, 5)
    # Warm end-grain rings on the exposed shoulder of the stump use the same wood.
    for r in (.169, .200):
        tube('Stump exposed growth ring', [(ax + r * math.cos(i * math.tau / 40),
                                          ay + r * .95 * math.sin(i * math.tau / 40), .586)
                                         for i in range(41)], .0018, 'Timber', g, 4)
    for angle in (.3, 2.25, 3.7, 5.1):
        tube('Stump short radial end grain split',
             [(ax + r * math.cos(angle + .02 * j),
               ay + r * .95 * math.sin(angle + .02 * j), .5865)
              for j, r in enumerate((.18, .20, .227))], .0018, 'Charcoal', g, 4)
    # Cross-sections form an integrated forging, with the top broader than waist.
    verts, faces = [], []
    for z, halfx, halfy in [(.585, .214, .134), (.626, .211, .126),
                           (.700, .116, .075), (.793, .103, .074),
                           (.867, .188, .110), (.935, .232, .115),
                           (.960, .227, .109)]:
        for x, y in [(-halfx, -halfy), (halfx, -halfy), (halfx, halfy), (-halfx, halfy)]:
            verts.append((ax + x, ay + y, z))
    for j in range(6):
        for i in range(4):
            faces.append((j * 4 + i, j * 4 + (i + 1) % 4,
                          (j + 1) * 4 + (i + 1) % 4, (j + 1) * 4 + i))
    faces += [(3, 2, 1, 0), (24, 25, 26, 27)]
    mesh('Forged anvil flared feet waist and face', verts, faces, 'Iron', group=g)
    verts, faces = [], []
    for j, (x, ry, rz, z) in enumerate([(-.208, .105, .055, .899),
                                      (-.30, .082, .043, .912),
                                      (-.41, .049, .026, .925),
                                      (-.53, .009, .009, .934)]):
        for i in range(12):
            t = i * math.tau / 12
            verts.append((ax + x, ay + ry * math.cos(t), z + rz * math.sin(t)))
            if j:
                a, b = (j - 1) * 12 + i, (j - 1) * 12 + (i + 1) % 12
                faces.append((a, b, b + 12, a + 12))
    faces += [tuple(reversed(range(12))), tuple(range(36, 48))]
    mesh('Anvil tapered round horn', verts, [tuple(reversed(f)) for f in faces], 'Iron', group=g)
    for dx in (-.16, .16):
        tube('Forged anvil holdfast', [(ax + dx, ay - .165, .53),
                                     (ax + dx, ay - .16, .616),
                                     (ax + dx, ay - .092, .62)], .011, 'Iron', g, 6)
    hammer('Anvil resting hammer', (ax + .082, ay + .017, .995), g, length=.27)

    # Heavy plank bench with real open space beneath it and visible joinery.
    g = 'Workbench'
    for x in (-1.93, -.57):
        for y in (.48, 1.01):
            beam('Bench splayed square leg', (x + (-.035 if x < -1 else .035), y, .025),
                 (x, y, .802), .105, .112, group=g, rough=.004)
        beam('Bench end lower tie', (x, .42, .255), (x, 1.07, .255), .073, group=g)
    for y in (.485, 1.005):
        beam('Bench mortised apron', (-2.065, y, .692), (-.425, y, .692),
             .084, .147, group=g, rough=.003)
        for x in (-1.93, -.57):
            nail('Bench square joinery peg', (x, y - .043, .714), g, .011)
    for i in range(4):
        beam('Bench broad worn top board', (-2.09, .464 + i * .190, .817),
             (-.415, .464 + i * .190, .817), .186, .066, group=g, rough=.003)
    beam('Bench longitudinal lower stretcher', (-1.96, .75, .285), (-.54, .75, .285),
         .079, .090, group=g, rough=.003)
    hammer('Bench cross peen hammer', (-1.49, .88, .883), g, length=.34)
    for i in range(3):
        beam('Short unfinished iron stock', (-1.03 + i * .055, .70, .872),
             (-.88 + i * .050, .99, .872), .025, .020, 'Iron', g, .001)
    rings('Bench small grinding stone', [(-1.89, .66, .86, .065, .057),
                                        (-1.89, .66, .922, .065, .057)], 'Stone', g, 12)

    # The dark tools stand away from the rear wall to retain their silhouettes.
    g = 'ToolRack'
    beam('Rear tool hanging rail', (-2.11, 1.285, 1.66), (-.39, 1.285, 1.66),
         .070, .098, group=g, rough=.003)
    for x in (-2.00, -.50):
        beam('Tool rail bench anchored upright', (x, 1.27, .75), (x, 1.27, 1.78),
             .061, .076, group=g, rough=.003)
        beam('Tool rail bench mortise foot', (x, 1.15, .86), (x, 1.37, .86),
             .077, .054, group=g, rough=.002)
        nail('Tool support iron fixing', (x, 1.225, .91), g)
    for i in range(7):
        x = -2.03 + i * .257
        beam('Tool rail rough backing plank', (x, 1.335, 1.04 + rng.uniform(-.016, .015)),
             (x, 1.335, 1.734 + rng.uniform(-.021, .02)), .253, .027,
             group=g, rough=.003)
    for x in (-1.93, -1.61, -1.29, -.96, -.60):
        tube('Tool rack iron hook', [(x, 1.28, 1.68), (x, 1.155, 1.66),
                                    (x, 1.145, 1.71)], .008, 'Iron', g, 6)
    hammer('Rack broad forging hammer', (-1.93, 1.153, 1.645), g, True, .405)
    hammer('Rack small finishing hammer', (-.96, 1.153, 1.645), g, True, .34)
    for x, length in [(-1.61, .52), (-1.29, .44)]:
        # Tongs have two curved arms, a pivot and deliberately separated jaws.
        for side in (-1, 1):
            tube('Hanging tongs articulated arm',
                 [(x + side * .058, 1.143, 1.67 - length),
                  (x + side * .035, 1.146, 1.48), (x, 1.139, 1.58),
                  (x - side * .039, 1.146, 1.69),
                  (x - side * .015, 1.146, 1.715)], .011, 'Iron', g, 6)
        nail('Tongs proud pivot pin', (x, 1.123, 1.58), g, .018)
    beam('Hanging cold chisel wooden grip', (-.60, 1.15, 1.69), (-.60, 1.15, 1.49),
         .036, .035, group=g, rough=.001)
    beam('Hanging cold chisel steel blade', (-.60, 1.15, 1.50), (-.60, 1.15, 1.30),
         .031, .017, 'Iron', g, .001)

    # Open quenching trough: thick interlocked boards, internal water and hoops.
    g = 'WaterTrough'
    tx, ty = -2.20, -2.00
    for x in (tx - .46, tx + .46):
        beam('Trough transverse foot', (x, ty - .355, .071), (x, ty + .355, .071),
             .130, .12, group=g, rough=.004)
    for i in range(4):
        beam('Trough bottom plank', (tx - .60, ty - .207 + i * .138, .15),
             (tx + .60, ty - .207 + i * .138, .15), .14, .075, group=g, rough=.002)
    for j in range(3):
        z = .222 + j * .106
        for s in (-1, 1):
            beam('Trough long lapped board', (tx - .64 + rng.uniform(-.01, .008), ty + s * .273, z),
                 (tx + .64 + rng.uniform(-.012, .012), ty + s * .273, z + rng.uniform(-.006, .006)),
                 .071, .102, group=g, rough=.005)
            beam('Trough end lapped board', (tx + s * .593, ty - .313, z),
                 (tx + s * .593, ty + .314, z), .070, .102, group=g, rough=.004)
    # Sparse longitudinal checks follow the worn face; they are shallow, not grooves.
    for i in range(7):
        x = tx + rng.uniform(-.56, .33)
        z = .21 + (i % 3) * .105 + rng.uniform(-.018, .018)
        tube('Trough weathered face check', [(x, ty - .310, z),
                                            (x + .085, ty - .312, z + .003),
                                            (x + rng.uniform(.12, .19), ty - .310, z + .001)],
             .0016, 'Charcoal', g, 4)
    block('Trough still dark water', (tx, ty, .391), (1.110, .464, .009), 'Water', g)
    for dx in (-.46, .46):
        for s in (-1, 1):
            block('Trough forged retaining strap', (tx + dx, ty + s * .313, .323),
                  (.037, .010, .320), 'Iron', g)
            for z in (.224, .425):
                nail('Trough strap rivet', (tx + dx, ty + s * .320, z), g, .012)
        block('Trough strap under base', (tx + dx, ty, .116), (.037, .622, .014), 'Iron', g)
    beam('Trough resting stirring stick', (tx - .32, ty - .34, .51),
         (tx + .25, ty + .35, .535), .025, .025, group=g, rough=.001)

    # A compact three-sided charcoal bin with large, readable individual lumps.
    g = 'CharcoalBin'
    cx, cy = 2.85, .25
    for x in (cx - .34, cx + .34):
        for y in (cy - .53, cy + .53):
            beam('Charcoal bin corner stake', (x, y, .015), (x, y, .445),
                 .058, group=g, rough=.002)
    for i in range(5):
        beam('Charcoal bin base plank', (cx - .32, cy - .43 + i * .21, .075),
             (cx + .32, cy - .43 + i * .21, .075), .200, .045, group=g, rough=.003)
    for j in range(3):
        z = .14 + j * .104
        for s in (-1, 1):
            beam('Charcoal bin side slat', (cx + s * .325, cy - .54, z),
                 (cx + s * .325, cy + .54, z), .037, .093, group=g, rough=.002)
        beam('Charcoal bin back slat', (cx - .32, cy + .50, z),
             (cx + .32, cy + .50, z), .038, .093, group=g, rough=.002)
    beam('Charcoal bin low front lip', (cx - .35, cy - .50, .140),
         (cx + .35, cy - .50, .140), .047, .139, group=g, rough=.003)
    for j in range(5):
        for i in range(5):
            x = cx - .25 + i * .122 + rng.uniform(-.025, .025)
            y = cy - .39 + j * .181 + rng.uniform(-.025, .025)
            z = .18 + .11 * (1 - abs(i - 2) / 3) + rng.uniform(-.03, .05)
            rx, ry = rng.uniform(.073, .113), rng.uniform(.094, .139)
            rings('Faceted charcoal lump', [(x, y, z - .085, rx * .66, ry * .65),
                                           (x + .008, y, z, rx, ry),
                                           (x - .020, y + .014, z + .080, rx * .49, ry * .54)],
                  'Charcoal', g, 7)

    # Four work-in-progress poles / bars are intentionally modest in number.
    g = 'WeaponRack'
    wx, wy = 2.65, -1.12
    for x in (wx - .36, wx + .36):
        beam('Stock rack foot', (x, wy - .34, .07), (x, wy + .25, .07), .095, group=g)
        beam('Stock rack upright', (x, wy + .15, .07), (x, wy + .15, 1.35),
             .069, group=g, rough=.003)
    for z in (.30, 1.18):
        beam('Stock rack horizontal rail', (wx - .425, wy + .15, z),
             (wx + .425, wy + .15, z), .065, group=g, rough=.002)
    for i in range(4):
        x = wx - .255 + i * .170
        ztop = (1.61, 1.72, 1.65, 1.52)[i]
        lower, upper = (x - .042, wy - .19, .07), (x + .022, wy + .112, ztop - .22)
        if i < 3:
            tube('Unfinished spear ash shaft', [lower, upper], .018, 'Timber', g, 8)
            a = Vector(upper)
            t = (a - Vector(lower)).normalized()
            tube('Plain unfinished spear socket', [a - t * .065, a + t * .066], .025, 'Iron', g, 8)
            # A ridged leaf-shaped head, without ornament or decorative fantasy scale.
            right, front = Vector((1, 0, 0)), Vector((0, -.012, 0))
            blade = [a, a + t * .105 - right * .048, a + t * .25,
                     a + t * .105 + right * .048, a + t * .103 + front,
                     a + t * .103 - front]
            mesh('Unfinished leaf spearhead', blade,
                 [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4),
                  (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)], 'Iron', group=g)
        else:
            beam('Long unworked iron billet', lower, (x + .022, wy + .12, ztop),
                 .029, .023, 'Iron', g, .001)
        tube('Stock rack individual peg', [(x, wy + .17, 1.18), (x, wy + .045, 1.18)],
             .010, 'Timber', g, 6)

    g = 'GroundDress'
    for i in range(3):
        x, y = 1.22 + .072 * i, -1.19 + .09 * i
        beam('Discarded short iron offcut', (x, y, .027), (x + .16, y + .26, .027),
             .024, .028, 'Iron', g, .002)
    for i in range(4):
        x, y = 2.72 + rng.uniform(-.23, .20), -.47 + rng.uniform(-.15, .08)
        rings('Spilled charcoal chunk', [(x, y, .006, .035, .041),
                                        (x + .007, y, .034, .046, .050),
                                        (x - .008, y, .069, .024, .030)], 'Charcoal', g, 6)

    # A small work supply, with split wedge ends and staggered lengths.
    for row, count in enumerate((5, 4, 3)):
        for i in range(count):
            x = -3.25 + (i - (count - 1) / 2) * .145
            y = .7 + rng.uniform(-.06, .06)
            z = .105 + row * .131 + rng.uniform(-.008, .008)
            length = rng.uniform(.51, .74)
            radius = rng.uniform(.077, .095)
            profile = [(-.9, -.50), (.80, -.40), (.65, .60), (-.45, .95)]
            verts = []
            for end in (-1, 1):
                for px, pz in profile:
                    verts.append((x + px * radius, y + end * length / 2 + rng.uniform(-.008, .008),
                                  z + pz * radius))
            log = mesh('Split stacked firewood billet', verts,
                       [(0, 1, 2, 3), (7, 6, 5, 4), (4, 5, 1, 0),
                        (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)], 'Timber', group=g)
            bevel = log.modifiers.new('Chipped firewood corners', 'BEVEL')
            bevel.width = .003
            bevel.segments = 1

    # Broken clusters of scale/charcoal flakes leave soil visible between pieces.
    for center, spread in [((.62, -2.04), (.39, .35)), ((1.35, -.87), (.36, .29)),
                           ((2.82, -.39), (.34, .19))]:
        for i in range(9):
            x = center[0] + rng.uniform(-spread[0], spread[0])
            y = center[1] + rng.uniform(-spread[1], spread[1])
            radius = rng.uniform(.009, .033)
            verts = []
            for k in range(6):
                angle = math.tau * k / 6
                r = radius * rng.uniform(.55, 1.3)
                verts.append((x + math.cos(angle) * r, y + math.sin(angle) * r * .6,
                              rng.uniform(.002, .005)))
            mesh('Scattered broken forge scale', verts, [(0, 1, 2, 3, 4, 5)], 'Charcoal', group=g)

    # Keep the work visible through the open bay. The rack stands on the bench.
    for ob in ns['groups'].get('Workbench', []):
        ob.location.y -= 1.05
    for ob in ns['groups'].get('ToolRack', []):
        ob.location.y -= 1.30

    # Small rounded arrises catch light on the forge tools without softening mass.
    for group in ('Anvil', 'Workbench', 'ToolRack', 'WaterTrough', 'WeaponRack', 'GroundDress'):
        for ob in ns['groups'].get(group, []):
            if not ob.data.materials or ob.data.materials[0] != ns['mats']['Iron']:
                continue
            for p in ob.data.polygons:
                p.use_smooth = True
            bevel = ob.modifiers.new('Worn forged iron arrises', 'BEVEL')
            bevel.width = .005 if 'anvil' in ob.name.lower() else .002
            bevel.segments = 3
            bevel.limit_method = 'ANGLE'
            bevel.angle_limit = .30
            bevel.harden_normals = True
            normal = ob.modifiers.new('Forged broad face normals', 'WEIGHTED_NORMAL')
            normal.keep_sharp = True
            normal.weight = 60
