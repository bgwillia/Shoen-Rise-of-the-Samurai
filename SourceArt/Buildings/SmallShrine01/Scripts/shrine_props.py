"""Authored exterior furnishings for the single SmallShrine01 composition."""
import math


def build_props(env):
    mesh, beam, tube, block = (env[k] for k in ('mesh', 'beam', 'tube', 'block'))
    pivots = {}

    def soften(ob, width=.006, segments=3, smooth=False):
        if smooth:
            for face in ob.data.polygons:
                face.use_smooth = True
        bevel = ob.modifiers.new('Worn restrained arrises', 'BEVEL')
        bevel.width = width
        bevel.segments = segments
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = .38
        bevel.harden_normals = True
        weighted = ob.modifiers.new('Broad weighted surface normals', 'WEIGHTED_NORMAL')
        weighted.keep_sharp = True
        weighted.weight = 40
        return ob

    def profile(name, cx, cy, rings, mat, group, roundness=5.0, sides=32, bevel=.006):
        # Worn rounded-square stone sections. Circular shaft and finial use power 2.
        outline = []
        for i in range(sides):
            angle = i * math.tau / sides
            c, s = math.cos(angle), math.sin(angle)
            wear = 1 + .008 * math.sin(i * 2.39 + cx * 4.1)
            outline.append((math.copysign(abs(c) ** (2 / roundness), c) * wear,
                            math.copysign(abs(s) ** (2 / roundness), s) * wear))
        verts = [(cx + x * r, cy + y * r, z) for z, r in rings for x, y in outline]
        faces = [tuple(reversed(range(sides)))]
        for j in range(len(rings) - 1):
            for i in range(sides):
                faces.append((j * sides + i, j * sides + (i + 1) % sides,
                              (j + 1) * sides + (i + 1) % sides, (j + 1) * sides + i))
        faces.append(tuple(range((len(rings) - 1) * sides, len(rings) * sides)))
        ob = mesh(name, verts, faces, mat, group=group)
        soften(ob, bevel, smooth=True)
        return ob

    def paper(name, x, y, z, scale, group):
        # A thickened, folded zigzag strip reads from either side of the gate.
        shape = [(-.035, 0), (.036, 0), (.010, -.085), (.075, -.128),
                 (.012, -.212), (.065, -.252), (-.012, -.350),
                 (-.059, -.315), (-.015, -.253), (-.063, -.219),
                 (-.004, -.138), (-.053, -.102)]
        n = len(shape)
        verts = []
        for side in (-1, 1):
            for px, pz in shape:
                fold = .018 * math.sin(-pz * math.pi / .090)
                verts.append((x + px * scale, y + fold * scale + side * .0015, z + pz * scale))
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
        return mesh(name, verts, faces, 'Paper', group=group)

    def tassel(name, x, y, z, length, group):
        # Solid low-cost straw pendant, never individual rope fibres.
        tube(name + ' neck', [(x, y, z), (x, y, z - .075)], .034, 'Rope', group, sides=8)
        rings = [(z - .065, .028), (z - length * .40, .045), (z - length, .073)]
        verts = [(x + r * math.cos(i * math.tau / 10),
                  y + r * math.sin(i * math.tau / 10), h)
                 for h, r in rings for i in range(10)]
        faces = [tuple(reversed(range(10))), tuple(range(20, 30))]
        for j in range(2):
            for i in range(10):
                faces.append((j * 10 + i, j * 10 + (i + 1) % 10,
                              (j + 1) * 10 + (i + 1) % 10, (j + 1) * 10 + i))
        mesh(name + ' skirt', verts, faces, 'Rope', group=group)

    # Natural-wood torii: gently canted posts and a restrained curved kasagi.
    gate_y = -3.05
    g = 'Torii_01'
    pivots[g] = (0, gate_y, 0)
    for sign in (-1, 1):
        x = sign * 1.325
        profile('Torii stone shoe', x, gate_y, [(0, .20), (.06, .21), (.13, .165)], 'Stone', g)
        # A tapered trunk section, lightly hewn, has much less furniture-like mass.
        verts, uvs, faces = [], [], []
        sides, levels = 24, 10
        for j in range(levels):
            t = j / (levels - 1)
            z = .065 + 2.75 * t
            cx = sign * (1.325 - .09 * t)
            radius = .139 - .027 * t
            for i in range(sides):
                a = i * math.tau / sides
                r = radius * (1 + .025 * math.sin(i * 2.63 + sign))
                r += .0017 * math.sin(j * 1.5 + i * .72)
                verts.append((cx + math.cos(a) * r,
                              gate_y + math.sin(a) * r * .94, z))
                uvs.append((i / sides * .9, z / 1.10))
        for j in range(levels - 1):
            for i in range(sides):
                faces.append((j * sides + i, j * sides + (i + 1) % sides,
                              (j + 1) * sides + (i + 1) % sides, (j + 1) * sides + i))
        faces.extend([tuple(reversed(range(sides))),
                      tuple(range((levels - 1) * sides, levels * sides))])
        post = mesh('Torii tapered hand hewn upright', verts, faces, 'Timber', uvs, g)
        soften(post, .004, smooth=True)
        block('Torii shoulder block', (sign * 1.238, gate_y, 2.73), (.25, .25, .075),
              'Timber', g, bevel=.010)
    # Crossbeam has visible projecting ends and small pegged joinery.
    beam('Torii penetrating tie', (-1.66, gate_y, 2.29), (1.66, gate_y, 2.29),
         .175, .16, 'Timber', g, rough=.002)
    for sign in (-1, 1):
        beam('Torii shoulder wedge', (sign * 1.14, gate_y - .15, 2.43),
             (sign * 1.40, gate_y - .15, 2.43), .062, .066, 'Timber', g, rough=.001)
        for z in (2.23, 2.36):
            tube('Torii timber peg', [(sign * 1.25, gate_y - .13, z),
                                     (sign * 1.25, gate_y - .165, z)],
                 .020, 'Timber', g, sides=7)
    # Continuous faceted beam, not a row of disconnected block segments.
    for name, half_width, depth, lower, thickness in [
            ('Torii lower crown', 1.73, .265, 2.715, .082),
            ('Torii curved crown', 1.86, .305, 2.796, .145),
            ('Torii crown weathering lip', 1.875, .325, 2.932, .026)]:
        verts, uvs = [], []
        segments = 32
        for i in range(segments + 1):
            x = -half_width + 2 * half_width * i / segments
            lift = .125 * (abs(x) / half_width) ** 2.3
            for y, z in [(-depth / 2, lower), (depth / 2, lower),
                         (depth / 2, lower + thickness), (-depth / 2, lower + thickness)]:
                verts.append((x, gate_y + y, z + lift))
                # SHŌEN timber grain follows V: turn it along this long beam.
                uvs.append(((y / depth + .5) * .28 + (z - lower) * 1.2,
                            (x + half_width) / 1.20))
        faces = [(3, 2, 1, 0), tuple(range(segments * 4, segments * 4 + 4))]
        for i in range(segments):
            faces.extend((i * 4 + j, i * 4 + (j + 1) % 4,
                          (i + 1) * 4 + (j + 1) % 4, (i + 1) * 4 + j) for j in range(4))
        crown = mesh(name, verts, faces, 'Timber', uvs, g)
        soften(crown, .012 if thickness > .1 else .005, smooth=True)
    block('Torii central strut', (0, gate_y, 2.55), (.125, .145, .37), 'Timber', g, bevel=.009)

    # The torii rope remains in its reusable gate group; shrine rope is separate.
    pts = [(-1.15 + 2.30 * i / 24, gate_y - .155,
            2.34 - .29 * math.sin(math.pi * i / 24)) for i in range(25)]
    tube('Torii shimenawa', pts, .038, 'Rope', g, sides=10)
    for x in (-.77, -.26, .26, .77):
        z = 2.34 - .29 * math.sin(math.pi * (x + 1.15) / 2.30)
        paper('Torii folded shide', x, gate_y - .16, z - .015, .84, g)

    g = 'SR01_Shimenawa'
    pivots[g] = (0, -1.27, 2.32)
    pts = [(-1.10 + 2.20 * i / 24, -1.27,
            2.52 - .20 * math.sin(math.pi * i / 24)) for i in range(25)]
    tube('Veranda shimenawa', pts, .047, 'Rope', g, sides=12)
    # Coarse binding collars and three pendants provide recognisable sacred rope.
    for x in (-1.07, 1.07):
        tube('Shimenawa end tie', [(x, -1.27, 2.51), (x, -1.28, 2.43),
                                 (x * .98, -1.29, 2.39)], .026, 'Rope', g, sides=8)
    tassel('Shimenawa centre tassel', 0, -1.30, 2.30, .30, g)
    for x in (-.75, .75):
        tassel('Shimenawa side tassel', x, -1.29, 2.39, .20, g)
    sg = 'SR01_Shimenawa_Shides'
    pivots[sg] = (0, -1.27, 2.32)
    for x in (-.91, -.43, .43, .91):
        z = 2.52 - .20 * math.sin(math.pi * (x + 1.10) / 2.20)
        paper('Veranda folded shide', x, -1.31, z - .025, 1, sg)

    # Compact offering box set on the veranda, with separated top slats.
    g = 'OfferingBox_01'
    pivots[g] = (0, -1.15, .86)
    for x in (-.275, .275):
        block('Offering box foot', (x, -1.15, .90), (.105, .37, .08), 'Timber', g, bevel=.008)
    block('Offering box bottom', (0, -1.15, .975), (.72, .40, .075), 'Timber', g, bevel=.008)
    for x in (-.326, .326):
        block('Offering box side', (x, -1.15, 1.145), (.07, .40, .34), 'Timber', g, bevel=.006)
    for y in (-1.325, -.975):
        for i in range(5):
            block('Offering box face plank', (-.263 + i * .132, y, 1.14),
                  (.127, .050, .30), 'Timber', g, bevel=.003)
        for z in (1.005, 1.277):
            block('Offering box frame rail', (0, y - .014, z), (.72, .045, .065),
                  'Timber', g, bevel=.004)
    block('Offering box dark slot', (0, -1.15, 1.294), (.62, .29, .025), 'Iron', g, bevel=.002)
    for i in range(7):
        slat = block('Offering box rounded top slat', (-.30 + i * .10, -1.15, 1.329),
                     (.067, .42, .053), 'Timber', g, bevel=.009)
        for modifier in slat.modifiers:
            if modifier.type == 'BEVEL':
                modifier.segments = 3
                modifier.harden_normals = True
        for face in slat.data.polygons:
            face.use_smooth = True
        weighted = slat.modifiers.new('Slat weighted normals', 'WEIGHTED_NORMAL')
        weighted.keep_sharp = True
    for x in (-.326, .326):
        for z in (1.025, 1.25):
            tube('Offering box dark nail', [(x, -1.361, z), (x, -1.369, z)],
                 .008, 'Iron', g, sides=6)

    # Small paired stone lanterns. Each keeps its own base-centre pivot.
    for idx, x in enumerate((-2.05, 2.05), 1):
        g = f'StoneLantern_{idx:02d}'
        y = -1.9
        pivots[g] = (x, y, 0)
        profile('Lantern lower plinth', x, y, [(0, .25), (.035, .265), (.083, .265),
                                              (.115, .230)], 'Stone', g, bevel=.012)
        profile('Lantern stepped plinth', x, y, [(.112, .20), (.145, .20), (.175, .177),
                                                (.207, .137), (.224, .126)], 'Stone', g)
        profile('Lantern subtly swelling shaft', x, y,
                [(.217, .102), (.246, .104), (.277, .092), (.365, .081),
                 (.505, .083), (.580, .096), (.607, .127), (.632, .139)],
                'Stone', g, roundness=2.0, bevel=.004)
        profile('Lantern lotus cushion', x, y, [(.62, .135), (.644, .15), (.662, .181),
                                               (.685, .19), (.713, .182)], 'Stone', g)
        block('Lantern chamber floor', (x, y, .718), (.28, .28, .045), 'Stone', g, bevel=.006)
        # A recessed central baffle leaves real depth around the chamber openings.
        block('Lantern recessed chamber back', (x, y + .070, .821),
              (.20, .028, .205), 'Stone', g, bevel=.003)
        for sx in (-1, 1):
            for sy in (-1, 1):
                block('Lantern chamber corner', (x + sx * .139, y + sy * .139, .815),
                      (.066, .066, .205), 'Stone', g, bevel=.010)
        # Top/bottom stone lintels frame shadowed apertures on all four sides.
        profile('Lantern chamber lintel', x, y, [(.903, .180), (.934, .191), (.950, .20)], 'Stone', g)
        # Pagoda cap bends from a shallow tip into a steep central shoulder.
        profile('Lantern curved pagoda cap', x, y,
                [(.945, .190), (.954, .285), (.972, .323), (.989, .337),
                 (1.002, .333), (1.005, .303), (1.018, .255), (1.043, .205),
                 (1.071, .163), (1.102, .119), (1.117, .094)],
                'Stone', g, roundness=7.0, sides=48, bevel=.004)
        profile('Lantern rounded urn finial', x, y,
                [(1.11, .068), (1.128, .070), (1.143, .048), (1.161, .046),
                 (1.178, .064), (1.203, .070), (1.224, .058), (1.244, .029),
                 (1.263, .009)], 'Stone', g, roundness=2.0, sides=32, bevel=.003)

    # Intentionally low, regular boundaries, with a generous approach opening.
    fence_posts = set()
    def fence(name, a, b, group, end_posts=True):
        ax, ay = a
        bx, by = b
        pivots.setdefault(group, (ax, ay, 0))
        for i, (x, y) in enumerate((a, b)):
            if i == 1 and not end_posts:
                continue
            key = (round(x, 4), round(y, 4))
            if key in fence_posts:
                continue
            fence_posts.add(key)
            block(name + ' squared post', (x, y, .325), (.13, .13, .65),
                  'Timber', group, bevel=.009)
            block(name + ' bevel cap', (x, y, .655), (.16, .16, .055),
                  'Timber', group, bevel=.015)
        for z in (.24, .50):
            beam(name + ' horizontal rail', (ax, ay, z), (bx, by, z),
                 .080, .072, 'Timber', group, rough=.002)
        length = math.hypot(bx - ax, by - ay)
        for i in range(1, max(2, round(length / .30))):
            t = i / max(2, round(length / .30))
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            block(name + ' vertical spindle', (x, y, .375), (.052, .052, .40),
                  'Timber', group, bevel=.004)

    fence('Boundary front left', (-2.65, -3.45), (-1.45, -3.45), 'SR01_Fence_End')
    fence('Boundary front right', (1.45, -3.45), (2.65, -3.45), 'SR01_Fence_Boundary')
    for side in (-1, 1):
        for i in range(6):
            y0 = -3.45 + 5.45 * i / 6
            y1 = -3.45 + 5.45 * (i + 1) / 6
            group = 'SR01_Fence_Straight' if side == -1 and i == 0 else 'SR01_Fence_Boundary'
            fence('Boundary side', (side * 2.65, y0), (side * 2.65, y1), group,
                  end_posts=i == 5 or group == 'SR01_Fence_Straight')
    for i in range(6):
        fence('Boundary rear', (-2.65 + 5.30 * i / 6, 2.0),
              (-2.65 + 5.30 * (i + 1) / 6, 2.0), 'SR01_Fence_Boundary', end_posts=False)

    # Two quiet banners; shallow drape and a small, unlettered round flower crest.
    g = 'SR01_Banners'
    pivots[g] = (0, -.60, 0)
    for sign in (-1, 1):
        x, y = sign * 2.28, -.60
        profile('Banner stone socket', x, y, [(0, .16), (.07, .18), (.15, .13)], 'Stone', g)
        beam('Banner timber staff', (x, y, .09), (x, y, 1.93), .052, .05, 'Timber', g, rough=.001)
        beam('Banner top crossarm', (x - .24, y, 1.88), (x + .24, y, 1.88),
             .044, .04, 'Timber', g, rough=.001)
        def cloth_y(u, drop):
            return (y - .040 + .012 * math.sin((u + .19) * 19 + .6 * drop)
                    + .010 * math.sin(drop * 7 + .4) * (u / .19) ** 2 + .014 * drop ** 2)

        verts, uvs = [], []
        nx, nz = 17, 33
        for j in range(nz):
            drop = .97 * j / (nz - 1)
            for i in range(nx):
                u = -.19 + .38 * i / (nx - 1)
                edge = abs(u / .19) ** 8
                px = x + u + edge * .0023 * math.sin(j * 1.7 + i)
                wear = (j / (nz - 1)) ** 15 * (.006 * math.sin(i * 2.8)
                                                       + .005 * math.sin(i * 4.1))
                verts.append((px, cloth_y(u, drop), 1.84 - drop + wear))
                uvs.append((i / (nx - 1), j / (nz - 1)))
        faces = [(j * nx + i, (j + 1) * nx + i, (j + 1) * nx + i + 1, j * nx + i + 1)
                 for j in range(nz - 1) for i in range(nx - 1)]
        banner = mesh('Faded shrine banner with worn hem', verts, faces, 'Paper', uvs, g)
        for face in banner.data.polygons:
            face.use_smooth = True
        thickness = banner.modifiers.new('Cloth edge thickness', 'SOLIDIFY')
        thickness.thickness = .0012
        thickness.offset = 0

        def crest_point(u, z):
            return (x + u, cloth_y(u, 1.84 - z) - .0018, z)

        # The ink is projected onto the same cloth surface, so it follows the folds.
        centre_z = 1.47
        vv, ff = [], []
        for radius in (.098, .112):
            for i in range(64):
                angle = i * math.tau / 64
                vv.append(crest_point(radius * math.cos(angle), centre_z + radius * math.sin(angle)))
        for i in range(64):
            ff.append((i, (i + 1) % 64, (i + 1) % 64 + 64, i + 64))
        ink = mesh('Banner ink circular crest', vv, ff, 'Iron', group=g)
        for face in ink.data.polygons:
            face.use_smooth = True
        for petal in range(4):
            angle = petal * math.pi / 2
            vv = []
            for i in range(24):
                a = i * math.tau / 24
                along = .047 + .027 * math.cos(a)
                across = .020 * math.sin(a)
                u = along * math.cos(angle) - across * math.sin(angle)
                z = centre_z + along * math.sin(angle) + across * math.cos(angle)
                vv.append(crest_point(u, z))
            mesh('Banner ink flower petal', vv, [tuple(range(24))], 'Iron', group=g)
        vv = [crest_point(.017 * math.cos(i * math.tau / 24),
                          centre_z + .017 * math.sin(i * math.tau / 24)) for i in range(24)]
        mesh('Banner ink flower centre', vv, [tuple(range(24))], 'Iron', group=g)
        for dx in (-.14, .14):
            tube('Banner suspension tie', [(x + dx, y, 1.89), (x + dx, y - .018, 1.80)],
                 .012, 'Rope', g, sides=6)

    return pivots
