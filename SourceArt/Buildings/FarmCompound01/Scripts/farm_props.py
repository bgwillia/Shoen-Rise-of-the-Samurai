"""One authored set of reusable agricultural exterior props for FarmCompound01."""


def build_props(ns):
    """Use the rural kit's helpers/materials; each named group starts at ground origin."""
    mesh, beam, tube = (ns[k] for k in ('mesh', 'beam', 'tube'))
    Vector, math = ns['Vector'], ns['math']
    rng = ns['random'].Random(118042)

    def block(name, center, size, material, group):
        x, y, z = center
        a, b, c = (v / 2 for v in size)
        vv = [(x + dx * a, y + dy * b, z + dz * c)
              for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
        return mesh(name, vv, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
                              (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)],
                    material, group=group)

    def binding(name, center, radius, group, turns=3, axis='X', thickness=.008):
        x, y, z = center
        points = []
        for j in range(turns * 16 + 1):
            a = j * math.tau / 16
            along = (j / (turns * 16) - .5) * turns * thickness * 2.2
            offset = ((along, radius * math.cos(a), radius * math.sin(a))
                      if axis == 'X' else
                      (radius * math.cos(a), radius * math.sin(a), along)
                      if axis == 'Z' else
                      (radius * math.cos(a), along, radius * math.sin(a)))
            points.append((x + offset[0], y + offset[1], z + offset[2]))
        return tube(name, points, thickness, 'Rope', group, 5)

    def wheel_ring(name, cx, cy, cz, inside, outside, depth, material, group):
        # Four connected circular rings make a genuinely open wheel, with a flat tread.
        vv, uv, ff = [], [], []
        n = 40
        for yy, rr in [(-depth / 2, inside), (-depth / 2, outside),
                       (depth / 2, outside), (depth / 2, inside)]:
            for i in range(n):
                a = i * math.tau / n
                vv.append((cx + math.cos(a) * rr, cy + yy, cz + math.sin(a) * rr))
                uv.append((i / n * 4, yy + rr))
        for ring in range(4):
            for i in range(n):
                ff.append((ring * n + i, ring * n + (i + 1) % n,
                           ((ring + 1) % 4) * n + (i + 1) % n,
                           ((ring + 1) % 4) * n + i))
        return mesh(name, vv, ff, material, uv, group)

    # A handcart: 1.55 x 1.05 m plank bed, two spoke wheels, and two long pulling shafts.
    # The asymmetric bed and shafts balance around the local ground-center origin.
    g = 'Cart'
    cx, axle = -.49, -.61
    for y in (-.397, .397):
        beam('Cart underbed longitudinal runner', (-1.30, y, .524), (.31, y, .524),
             .095, .120, group=g, rough=.004)
    for x in (-1.12, -.58, .14):
        beam('Cart transverse bed joist', (x, -.55, .568), (x, .55, .568),
             .086, .105, group=g, rough=.003)
    for i in range(7):
        y = -.453 + i * .151
        beam('Cart worn bed plank', (cx - .775, y, .630), (cx + .775, y, .630),
             .146, .057, group=g, rough=.003)
    for y in (-.540, .540):
        for z in (.748, .916):
            beam('Cart side broad plank', (-1.29, y, z), (.29, y, z),
                 .056, .150, group=g, rough=.004)
        for x in (-1.20, -.44, .22):
            beam('Cart side upright stake', (x, y, .55), (x, y, 1.045),
                 .068, .074, group=g, rough=.003)
            for z in (.75, .915):
                tube('Cart small flush joinery peg', [(x, y - .041, z), (x, y + .041, z)],
                     .011, 'Timber', g, 6)
        beam('Cart worn side top rail', (-1.30, y, 1.025), (.31, y, 1.025),
             .070, .062, group=g, rough=.003)
    for x in (-1.245, .247):
        for z in (.748, .916):
            beam('Cart end plank', (x, -.515, z), (x, .515, z),
                 .057, .148, group=g, rough=.003)
    tube('Cart solid wooden axle', [(axle, -.78, .464), (axle, .78, .464)],
         .068, 'Timber', g, 10)
    for side in (-1, 1):
        wy = side * .665
        wheel_ring('Cart jointed timber wheel felloe', axle, wy, .464,
                   .383, .454, .100, 'Timber', g)
        wheel_ring('Cart narrow dark wheel tire', axle, wy, .464,
                   .449, .463, .106, 'Iron', g)
        tube('Cart turned wooden wheel hub', [(axle, wy - .107, .464),
                                             (axle, wy + .107, .464)],
             .102, 'Timber', g, 12)
        for i in range(12):
            a = math.tau * i / 12 + .09
            start = (axle + .080 * math.cos(a), wy, .464 + .080 * math.sin(a))
            end = (axle + .398 * math.cos(a), wy, .464 + .398 * math.sin(a))
            beam('Cart radial hardwood spoke', start, end, .041, .047,
                 group=g, rough=.0015)
        for i in range(8):
            a = math.tau * i / 8
            p = (axle + .421 * math.cos(a), wy + side * .052, .464 + .421 * math.sin(a))
            q = (p[0], p[1] + side * .008, p[2])
            tube('Cart felloe joining peg', [p, q], .010, 'Timber', g, 6)
        tube('Cart axle retaining pin', [(axle, wy + side * .123, .412),
                                        (axle, wy + side * .123, .52)],
             .016, 'Iron', g, 6)
        # Shafts rise gently to hands; no animal or harness is implied.
        tube('Cart long rough pulling shaft', [(-.86, side * .395, .516),
                                               (.25, side * .410, .490),
                                               (1.05, side * .445, .547),
                                               (1.37, side * .452, .585)],
             .040, 'Timber', g, 8)
        binding('Cart shaft lash at bed', (-.07, side * .403, .508), .054, g, 3)
    beam('Cart resting prop leg', (.19, 0, .545), (.33, 0, .050),
         .063, .067, group=g, rough=.002)
    beam('Cart prop foot', (.20, 0, .037), (.41, 0, .037), .073, .055, group=g)

    # Open lapped-plank trough, with visible water set down inside its thick walls.
    g = 'WaterTrough'
    for x in (-.43, .43):
        beam('Trough transverse foot', (x, -.305, .060), (x, .305, .060),
             .110, .110, group=g, rough=.003)
    for i in range(4):
        beam('Trough bottom plank', (-.61, -.185 + i * .123, .136),
             (.61, -.185 + i * .123, .136), .122, .055, group=g, rough=.002)
    for j in range(3):
        z = .214 + .103 * j
        for side in (-1, 1):
            beam('Trough lapped long side', (-.65, side * .247, z),
                 (.65, side * .247, z), .064, .098, group=g, rough=.003)
            beam('Trough end board', (side * .599, -.270, z),
                 (side * .599, .270, z), .067, .099, group=g, rough=.003)
    block('Trough still water surface', (0, 0, .368), (1.122, .414, .007), 'Water', g)
    for x in (-.445, .445):
        for side in (-1, 1):
            beam('Trough exterior retaining cleat', (x, side * .294, .135),
                 (x, side * .294, .466), .040, .050, group=g, rough=.001)
        # Simple hemp loop follows the plank body rather than a modern metal band.
        tube('Trough hemp retaining loop', [(x, -.286, .46), (x, -.291, .139),
                                           (x, .291, .139), (x, .286, .46)],
             .010, 'Rope', g, 6)

    # Four agricultural implements on an independent rail rack, visible from -Y.
    g = 'ToolRack'
    for x in (-.625, .625):
        beam('Farm tool rack splayed foot', (x, -.29, .045), (x, .24, .045),
             .087, .075, group=g, rough=.003)
        beam('Farm tool rack upright', (x, .10, .05), (x, .10, 1.49),
             .069, .075, group=g, rough=.003)
        beam('Farm tool rack small brace', (x, -.23, .085), (x, .10, .57),
             .050, .047, group=g, rough=.002)
    for z in (.27, 1.23):
        beam('Farm tool rack horizontal rail', (-.69, .09, z), (.69, .09, z),
             .063, .086, group=g, rough=.003)
    for x in (-.49, -.16, .18, .49):
        tube('Farm tool rack hanging peg', [(x, .102, 1.23), (x, -.075, 1.23)],
             .012, 'Timber', g, 6)
    # Wood shovel/spade with a narrow iron cutting shoe, distinct from the hoe.
    sx = -.49
    beam('Spade straight ash shaft', (sx, -.09, .36), (sx, -.02, 1.47),
         .034, .035, group=g, rough=.001)
    verts = [(sx + x, -.100 + y, z)
             for y in (-.022, .022)
             for x, z in [(-.083, .36), (.083, .36), (.096, .09),
                           (.055, .026), (-.055, .026), (-.096, .09)]]
    faces = [tuple(reversed(range(6))), tuple(range(6, 12))]
    faces += [(i, (i + 1) % 6, (i + 1) % 6 + 6, i + 6) for i in range(6)]
    mesh('Farm broad wooden spade blade', verts, faces, 'Timber', group=g)
    beam('Spade dark iron lower shoe', (sx - .065, -.104, .047),
         (sx + .065, -.104, .047), .052, .048, 'Iron', g, .001)
    binding('Spade socket hemp binding', (sx, -.070, .392), .030, g, 3, 'Z', .006)
    # The hoe has its blade perpendicular to the handle, projecting toward the viewer.
    hx = -.16
    beam('Hoe long hewn handle', (hx, -.08, .08), (hx + .018, -.025, 1.42),
         .035, .034, group=g, rough=.001)
    beam('Hoe iron socket', (hx, -.055, 1.33), (hx, -.06, 1.445),
         .055, .046, 'Iron', g, .001)
    block('Hoe broad worked iron blade', (hx, -.179, 1.423), (.180, .235, .026), 'Iron', g)
    # A simple six-tooth wooden rake provides the wide comb silhouette.
    rx = .18
    beam('Rake ash handle', (rx - .012, -.10, .046), (rx, -.029, 1.397),
         .030, .034, group=g, rough=.001)
    beam('Rake cross head', (rx - .153, -.045, 1.398), (rx + .153, -.045, 1.398),
         .048, .042, group=g, rough=.001)
    for i in range(6):
        x = rx - .130 + i * .052
        tube('Rake short wooden tooth', [(x, -.048, 1.40), (x, -.174, 1.342)],
             .009, 'Timber', g, 6)
    # A light three-prong wooden fork completes the restrained four-tool selection.
    fx = .49
    tube('Wooden fork shaft', [(fx, -.09, .06), (fx, -.040, 1.17), (fx, -.050, 1.41)],
         .018, 'Timber', g, 7)
    for side in (-1, 1):
        tube('Wooden fork curved outer prong', [(fx, -.04, 1.13),
                                               (fx + side * .068, -.04, 1.26),
                                               (fx + side * .09, -.09, 1.43)],
             .013, 'Timber', g, 6)
    binding('Wooden fork neck binding', (fx, -.04, 1.16), .025, g, 3, 'Z', .006)

    # Reusable open woven basket. Broad woven relief carries the look at practical scale.
    g = 'Baskets'
    n, levels = 32, 8

    def basket_radius(z):
        return .161 + .050 * math.sin(min(1, z / .43) * math.pi * .79)

    vv, uv, ff = [], [], []
    rings = [(z, basket_radius(z)) for z in [i * .43 / levels for i in range(levels + 1)]]
    rings += [(.43 - i * .395 / levels, basket_radius(.43 - i * .395 / levels) - .021)
              for i in range(levels + 1)]
    for j, (z, radius) in enumerate(rings):
        for i in range(n):
            a = math.tau * i / n
            vv.append((radius * math.cos(a), radius * math.sin(a), z + .008))
            uv.append((i / n * 2.1, z * 2.8))
            if j:
                ff.append(((j - 1) * n + i, (j - 1) * n + (i + 1) % n,
                           j * n + (i + 1) % n, j * n + i))
    ff += [tuple(reversed(range(n))), tuple(range((len(rings) - 1) * n, len(rings) * n))]
    basket = mesh('Basket open thick woven shell', vv, ff, 'Rope', uv, g)
    for p in basket.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    for row in range(15):
        z = .025 + row * .0285
        r = basket_radius(z) + .005
        points = [(r * math.cos(math.tau * i / 40), r * math.sin(math.tau * i / 40), z)
                  for i in range(41)]
        tube('Basket horizontal woven course', points, .0065, 'Rope', g, 5)
    for i in range(20):
        a = math.tau * i / 20
        pts = []
        for j in range(16):
            z = .021 + j * .0274
            r = basket_radius(z) + (.011 if (i + j) % 2 else .001)
            pts.append((r * math.cos(a), r * math.sin(a), z))
        tube('Basket alternating upright weave', pts, .0055, 'Rope', g, 5)
    rim = basket_radius(.43)
    tube('Basket thick rolled rim', [(rim * math.cos(i * math.tau / 48),
                                      rim * math.sin(i * math.tau / 48), .437)
                                     for i in range(49)], .014, 'Rope', g, 6)
    for side in (-1, 1):
        tube('Basket small carrying loop', [(side * rim, -.055, .391),
                                            (side * (rim + .034), -.049, .477),
                                            (side * (rim + .040), .035, .477),
                                            (side * rim, .057, .391)],
             .011, 'Rope', g, 6)

    # One tied straw sheaf, about .8 m high, with a full loose crown and broken ends.
    g = 'HayBundles'
    n = 24
    vv, uv, ff = [], [], []
    straw_levels = [(.01, .275), (.14, .309), (.32, .303), (.40, .290),
                    (.50, .307), (.60, .312), (.70, .262), (.757, .143),
                    (.795, .041)]
    for j, (z, rr) in enumerate(straw_levels):
        for i in range(n):
            a = i * math.tau / n
            radius = rr * (1 + .055 * math.sin(i * 3.1) + .033 * math.sin(i * 1.8 + j))
            zz = z + (rng.uniform(-.022, .018) if j in (0, len(straw_levels) - 1)
                      else .014 * math.sin(i * 2.1 + j) if j > 4 else 0)
            vv.append((radius * math.cos(a), radius * .91 * math.sin(a), max(.004, zz)))
            uv.append((i / n * 1.8, z * 2.4))
            if j:
                ff.append(((j - 1) * n + i, (j - 1) * n + (i + 1) % n,
                           j * n + (i + 1) % n, j * n + i))
    ff += [tuple(reversed(range(n))), tuple(range((len(straw_levels) - 1) * n,
                                                  len(straw_levels) * n))]
    hay = mesh('Straw sheaf dense irregular bulk', vv, ff, 'Thatch', uv, g)
    for p in hay.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    # A flattened loose skirt sits beneath the tied sheaf, so instances settle
    # into a harvested-straw pile instead of reading as separate upright drums.
    verts, uvs, faces = [], [], []
    mound_levels = [(.009, .279), (.055, .309), (.133, .294), (.230, .233), (.290, .146)]
    for j, (z, radius) in enumerate(mound_levels):
        for i in range(n):
            a = math.tau * i / n
            rr = radius * (1 + .042 * math.sin(i * 2.73) + .017 * math.sin(i + j))
            verts.append((rr * math.cos(a), rr * .91 * math.sin(a),
                          max(.004, z + .014 * math.sin(i * 1.65 + j))))
            uvs.append((i / n * 1.8, z * 2.4))
            if j:
                faces.append(((j - 1) * n + i, (j - 1) * n + (i + 1) % n,
                              j * n + (i + 1) % n, j * n + i))
    faces += [tuple(reversed(range(n))),
              tuple(range((len(mound_levels) - 1) * n, len(mound_levels) * n))]
    mound = mesh('Straw sheaf loose broad foot mound', verts, faces, 'Thatch', uvs, g)
    for p in mound.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    for i in range(32):
        a = i * math.tau / 32 + rng.uniform(-.023, .023)
        pts = []
        for j, (z, rr) in enumerate(straw_levels):
            r = rr + rng.uniform(.003, .016)
            zz = z + (rng.uniform(-.014, .018) if j in (0, len(straw_levels) - 1)
                      else rng.uniform(-.010, .010))
            pts.append((r * math.cos(a), r * .88 * math.sin(a), max(.004, zz)))
        tube('Straw sheaf surface reed cluster', pts, rng.uniform(.006, .011), 'Thatch', g, 5)
    for z, r in [(.388, .298), (.411, .297)]:
        tube('Straw sheaf hemp binding', [(r * math.cos(i * math.tau / 36),
                                          r * .88 * math.sin(i * math.tau / 36), z)
                                         for i in range(37)], .009, 'Rope', g, 5)
    tube('Straw sheaf visible loose knot', [(0, -.186, .418), (.042, -.224, .41),
                                          (.020, -.242, .376), (-.015, -.210, .416),
                                          (-.05, -.207, .335)], .008, 'Rope', g, 5)
    # Broad tapered reed clumps bend away from the tied center. Their uneven ends
    # make a loose straw silhouette without using a dense strand or hair system.
    for i in range(24):
        a = math.tau * i / 24 + rng.uniform(-.065, .065)
        radial = Vector((math.cos(a), .88 * math.sin(a), 0))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        rise = rng.uniform(-.035, .028)
        tip_radius = rng.uniform(.262, .310)
        profile = [(.247, .495, .038), (.298, .657 + rise, .043),
                   (.279, .743 + rise, .028),
                   (tip_radius, rng.uniform(.65, .782), .004)]
        verts, uvs, faces = [], [], []
        for j, (rr, z, width) in enumerate(profile):
            center = radial * rr + Vector((0, 0, z))
            for k, offset in enumerate((-.5, 0, .5)):
                verts.append(center + tangent * (width * offset)
                             + radial * (.010 if k == 1 else 0))
                uvs.append((k / 2, j / 3))
            if j:
                for k in range(2):
                    q = (j - 1) * 3 + k
                    faces.append((q, q + 1, q + 4, q + 3))
        mesh('Straw sheaf loose bending crown tuft', verts, faces, 'Thatch', uvs, g)
        if i % 2 == 0:
            # Restrained ear-like gathered tips are visibly rough and pointed.
            tip = radial * profile[-1][0] + Vector((0, 0, profile[-1][1]))
            axis = (radial * .6 + Vector((0, 0, .8))).normalized()
            cross = tangent.cross(axis).normalized()
            ev, euv, ef = [], [], []
            for j, (along, radius) in enumerate([(-.037, .008), (-.012, .017),
                                                 (.017, .012), (.037, .0015)]):
                for k in range(5):
                    aa = math.tau * k / 5
                    ev.append(tip + axis * along +
                              (tangent * math.cos(aa) + cross * math.sin(aa)) * radius)
                    euv.append((k / 5, j / 3))
                    if j:
                        ef.append(((j - 1) * 5 + k, (j - 1) * 5 + (k + 1) % 5,
                                   j * 5 + (k + 1) % 5, j * 5 + k))
            ef += [(4, 3, 2, 1, 0), (15, 16, 17, 18, 19)]
            mesh('Straw sheaf gathered rough grain tip', ev, ef, 'Thatch', euv, g)
