"""Hand-set rubble forge for this Smithy exterior; shared rural materials."""
import math
import random


def build_forge(ns):
    mesh = ns['mesh']
    rng = random.Random(6193)
    fx, fy = 1.35, .43

    def tone(ob, value):
        layer = ob.data.color_attributes.new(name='MasonryTone', type='FLOAT_COLOR', domain='CORNER')
        for polygon in ob.data.polygons:
            face = value * rng.uniform(.965, 1.035)
            for li in polygon.loop_indices:
                layer.data[li].color = (face, face * .99, face * .975, 1)
        return ob

    def rubble(name, center, size, group='Forge', mat='Stone', tint=None):
        # Three chipped cross sections make flat bedded rubble, with broken
        # edges and asymmetric faces rather than a bevel around a perfect box.
        x, y, z = center
        sx, sy, sz = (v / 2 for v in size)
        cuts = [rng.uniform(.16, .34) for _ in range(4)]
        outline = [(-1 + cuts[0], -1), (1 - cuts[1], -1),
                   (1, -1 + cuts[1]), (1, 1 - cuts[2]),
                   (1 - cuts[2], 1), (-1 + cuts[3], 1),
                   (-1, 1 - cuts[3]), (-1, -1 + cuts[0])]
        angle = rng.uniform(-.075, .075)
        ca, sa = math.cos(angle), math.sin(angle)
        vertices = []
        # Broad middle, chipped top and bottom, slightly tilted bedding planes.
        tilt_x, tilt_y = rng.uniform(-.065, .065), rng.uniform(-.055, .055)
        for h, spread in ((-1, rng.uniform(.80, .93)),
                          (rng.uniform(-.3, .25), 1),
                          (1, rng.uniform(.80, .95))):
            for a, b in outline:
                px = sx * (a * spread + rng.uniform(-.055, .055))
                py = sy * (b * spread + rng.uniform(-.07, .07))
                pz = sz * (h + rng.uniform(-.07, .07)) + tilt_x * px + tilt_y * py
                vertices.append((x + px * ca - py * sa, y + px * sa + py * ca, z + pz))
        faces = [tuple(reversed(range(8))), tuple(range(16, 24))]
        for row in range(2):
            for j in range(8):
                k = (j + 1) % 8
                faces.append((row * 8 + j, row * 8 + k, (row + 1) * 8 + k, (row + 1) * 8 + j))
        ob = mesh(name, vertices, faces, mat, group=group)
        tone(ob, tint if tint is not None else rng.uniform(.82, 1.05))
        return ob

    def shell(name, z0, z1, w0, d0, w1=None, d1=None, group='Forge'):
        # Closed wall thickness, with an open bottom and top. The cavity and
        # shaft are actual empty space, not a black polygon over a solid block.
        w1, d1 = w1 or w0, d1 or d0
        t = .065
        verts = []
        for z, w, d in ((z0, w0, d0), (z1, w1, d1)):
            for inset in (0, t):
                for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    verts.append((fx + a * (w / 2 - inset), fy + b * (d / 2 - inset), z))
        faces = []
        for i in range(4):
            j = (i + 1) % 4
            faces.extend(((i, j, j + 8, i + 8),
                          (i + 4, i + 12, j + 12, j + 4),
                          (i, i + 4, j + 4, j),
                          (i + 8, j + 8, j + 12, i + 12)))
        return mesh(name, verts, faces, 'Charcoal', group=group)

    def stone_run(name, center, length, depth, height, count, axis='X', group='Forge'):
        # Unequal spans prevent vertical joints repeating into a brick grid.
        weights = [rng.uniform(.65, 1.5) for _ in range(count)]
        spans = [length * v / sum(weights) for v in weights]
        cursor = -length / 2
        for span in spans:
            along = cursor + span / 2
            x, y, z = center
            if axis == 'X':
                p, size = (x + along, y + rng.uniform(-.014, .014), z), (span + .018, depth, height * rng.uniform(.90, 1.05))
            else:
                p, size = (x + rng.uniform(-.014, .014), y + along, z), (depth, span + .018, height * rng.uniform(.90, 1.05))
            rubble(name, p, size, group)
            cursor += span

    # Low broad fire table, faced in angular local rubble. Recessed dark core
    # seals fine mortar joints without turning their surface into smooth tiles.
    rubble('Recessed hearth bedding', (fx, fy, .325), (1.27, .94, .64), mat='Charcoal', tint=1)
    z = .015
    for row, h in enumerate((.19, .225, .205)):
        zc = z + h / 2
        for side in (-1, 1):
            stone_run('Hearth foundation rubble', (fx, fy + side * .455, zc), 1.30, .22, h, 4 if row != 1 else 5)
            stone_run('Hearth return rubble', (fx + side * .565, fy, zc), .77, .23, h, 3, 'Y')
        z += h - .012
    # A few old hearth slabs, different thicknesses and broken front arrises.
    stone_run('Worn fire-table sill', (fx, fy - .17, .64), 1.33, .81, .12, 3)
    # Dark chamber backing and two narrow side cheeks leave the front clear.
    rubble('Sooted hearth back', (fx, fy + .40, 1.04), (1.03, .14, .80), mat='Charcoal', tint=1)
    for side in (-1, 1):
        rubble('Cheek mortar backing', (fx + side * .535, fy, 1.07), (.20, .85, .77), mat='Charcoal', tint=1)
        z = .70
        for row, h in enumerate((.18, .205, .19, .205)):
            stone_run('Hand-set forge cheek', (fx + side * .535, fy - .01, z + h / 2), .95, .265, h, 3 if row % 2 else 2, 'Y')
            z += h - .013

    # Heavy split lintel gives the opening weight. Its underside stays above
    # the ember bed so the open fire chamber reads in the three-quarter view.
    stone_run('Rough smoke lintel', (fx, fy - .405, 1.49), 1.32, .27, .22, 3)
    shell('Soot-lined taper behind hood stones', 1.46, 2.81, 1.16, .85, .56, .48)
    heights = (.205, .23, .19, .25, .22, .24)
    z = 1.53
    for row, h in enumerate(heights):
        zc = z + h / 2
        blend = min(1, (zc - 1.45) / 1.35)
        w, d = 1.30 - .63 * blend, .99 - .35 * blend
        for side in (-1, 1):
            stone_run('Tapered hood rubble', (fx, fy + side * (d / 2 - .055), zc), w, .205, h, 4 if row < 2 else 3)
            stone_run('Hood return rubble', (fx + side * (w / 2 - .065), fy, zc), d - .23, .20, h, 2, 'Y')
        z += h - .013

    # A restrained crooked stack. Shell and laid stones retain an open dark
    # throat, and every course changes its joint spacing and outer silhouette.
    shell('Black chimney lining', 2.73, 4.48, .54, .49, group='Chimney')
    z = 2.73
    row = 0
    while z < 4.43:
        h = min(rng.uniform(.175, .225), 4.46 - z)
        w = .67 + .025 * math.sin(row * 1.3)
        d = .64 + .022 * math.cos(row * 1.1)
        zc = z + h / 2
        for side in (-1, 1):
            stone_run('Chimney uneven face stone', (fx, fy + side * (d / 2 - .045), zc), w, .18, h, 2 if row % 3 else 3, group='Chimney')
            stone_run('Chimney uneven return stone', (fx + side * (w / 2 - .055), fy, zc), d - .22, .19, h, 2, 'Y', 'Chimney')
        z += h - .009
        row += 1
    # Individually placed projecting crown rubble, not a manufactured frame.
    for side in (-1, 1):
        stone_run('Irregular chimney crown', (fx, fy + side * .278, 4.505), .76, .21, .16, 3, group='Chimney')
        stone_run('Split crown return', (fx + side * .292, fy, 4.50), .38, .205, .15, 2, 'Y', 'Chimney')
    # The low soot floor is far below the opening; the throat has real depth.
    mesh('Deep chimney throat shadow', [(fx - .23, fy - .20, 3.97), (fx + .23, fy - .20, 3.97),
                                      (fx + .23, fy + .20, 3.97), (fx - .23, fy + .20, 3.97)],
         [(0, 1, 2, 3)], 'Charcoal', group='Chimney')

    # Mostly cold black lumps, with tiny amber fracture lines on a few coals.
    # No flame spikes and no fully emissive cubes.
    for index in range(43):
        x = fx + rng.uniform(-.34, .34)
        y = fy + rng.uniform(-.29, .23)
        z = .716 + rng.uniform(0, .024)
        sx, sy, sz = rng.uniform(.048, .108), rng.uniform(.045, .09), rng.uniform(.025, .06)
        rubble('Broken charcoal bed', (x, y, z), (sx, sy, sz), mat='Charcoal', tint=1)
        if index % 4 == 0:
            # A thin crooked crack sits inside the rough top surface.
            zz = z + sz * .43
            verts = [(x - sx * .30, y - .003, zz), (x, y + .006, zz + .003),
                     (x + sx * .29, y - .001, zz), (x + sx * .25, y + .006, zz),
                     (x, y + .012, zz + .003), (x - sx * .27, y + .004, zz)]
            mesh('Dull ember fissure', verts, [(0, 1, 4, 5), (1, 2, 3, 4)], 'Ember', group='Forge')
