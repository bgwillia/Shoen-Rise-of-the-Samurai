"""Small exterior retainer props, with existing SHŌEN weapons and armor."""


def build_props(env):
    """Return editable modules in metres with local ground-centre origins."""
    from pathlib import Path

    bpy, math, Vector, Matrix = (env[k] for k in ('bpy', 'math', 'Vector', 'Matrix'))
    mesh, beam, tube = (env[k] for k in ('mesh', 'beam', 'tube'))
    src, mats, groups = (env[k] for k in ('src', 'mats', 'groups'))
    rng = env['random'].Random(1180419)
    samurai = Path(env['ROOT']) / 'SourceArt/Characters/Samurai'
    modules = {}

    def begin(name):
        groups[name] = []
        modules[name] = groups[name]
        return name

    def turned(name, center, profile, material, group, squash=1, sides=20):
        verts, uvs, faces = [], [], []
        for j, (z, radius) in enumerate(profile):
            for i in range(sides):
                angle = math.tau * i / sides
                r = radius * (1 + .015 * math.sin(i * 2.39 + z * 11))
                verts.append((center[0] + r * math.cos(angle),
                              center[1] + squash * r * math.sin(angle), center[2] + z))
                uvs.append((i / sides, z * 1.5))
                if j:
                    faces.append(((j - 1) * sides + i, (j - 1) * sides + (i + 1) % sides,
                                  j * sides + (i + 1) % sides, j * sides + i))
        faces += [tuple(reversed(range(sides))),
                  tuple(range((len(profile) - 1) * sides, len(profile) * sides))]
        ob = mesh(name, verts, faces, material, uvs, group)
        for poly in ob.data.polygons:
            poly.use_smooth = len(poly.vertices) == 4
        return ob

    def ring(name, center, radius_x, radius_y, group, material='Rope', wire=.009):
        return tube(name, [(center[0] + radius_x * math.cos(i * math.tau / 32),
                            center[1] + radius_y * math.sin(i * math.tau / 32), center[2])
                           for i in range(33)], wire, material, group, sides=6)

    def stalks(name, paths, group, material='Thatch'):
        """A few combined meshes of actual stalk relief, with tapered cut ends."""
        vv, ff, uv = [], [], []
        for points, radius in paths:
            start = len(vv)
            points = [Vector(p) for p in points]
            for j, p in enumerate(points):
                tangent = points[min(j + 1, len(points) - 1)] - points[max(j - 1, 0)]
                tangent.normalize()
                ref = Vector((1, 0, 0)) if abs(tangent.x) < .85 else Vector((0, 1, 0))
                across = tangent.cross(ref).normalized()
                other = tangent.cross(across).normalized()
                r = radius * (.70 if j in (0, len(points) - 1) else 1)
                for i in range(4):
                    angle = math.tau * i / 4
                    vv.append(p + r * (across * math.cos(angle) + other * math.sin(angle)))
                    uv.append((i / 4, j / max(1, len(points) - 1)))
                    if j:
                        q = start + (j - 1) * 4
                        ff.append((q + i, q + (i + 1) % 4, q + 4 + (i + 1) % 4, q + 4 + i))
            ff.extend([tuple(reversed(range(start, start + 4))),
                       tuple(range(len(vv) - 4, len(vv)))])
        return mesh(name, vv, ff, material, uv, group)

    def straw_bundle(name, a, b, profile, group, squash=.75, count=80):
        """Pressed sheaves: irregular longitudinal lobes, tied waists, raw ends."""
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        ref = Vector((1, 0, 0)) if abs(axis.z) > .8 else Vector((0, 1, 0))
        across = (ref - axis * ref.dot(axis)).normalized()
        other = axis.cross(across).normalized()
        phase = rng.uniform(0, math.tau)

        def surface(t, angle, relief=0):
            radius = profile[-1][1]
            for (t0, r0), (t1, r1) in zip(profile, profile[1:]):
                if t <= t1:
                    f = max(0, (t - t0) / (t1 - t0))
                    radius = r0 * (1 - f) + r1 * f
                    break
            radius *= (1 + .065 * math.sin(angle * 7 + phase)
                       + .034 * math.sin(angle * 15 + phase + .6 * t))
            radius += relief
            p = a + (b - a) * t
            p += across * (.012 * math.sin(t * math.pi) + .006 * t)
            p += other * (.008 * math.sin(t * 4 + phase))
            p += radius * (across * math.cos(angle) + other * squash * math.sin(angle))
            if t < .001 or t > .999:
                p += axis * (.014 * math.sin(angle * 17 + phase) + .008 * math.cos(angle * 9))
            return p

        vv, ff, uv = [], [], []
        sides = 56
        for j, (t, radius) in enumerate(profile):
            for i in range(sides):
                vv.append(surface(t, math.tau * i / sides))
                uv.append((i / sides, t * 1.7))
                if j:
                    q = (j - 1) * sides
                    ff.append((q + i, q + (i + 1) % sides,
                               q + sides + (i + 1) % sides, q + sides + i))
        ff += [tuple(reversed(range(sides))), tuple(range(len(vv) - sides, len(vv)))]
        ob = mesh(name, vv, ff, 'Thatch', uv, group)
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices) == 4
        paths = []
        for i in range(count):
            angle = math.tau * (i + rng.uniform(-.3, .3)) / count
            t0, t1 = rng.uniform(0, .08), rng.uniform(.93, 1)
            points = []
            for j in range(8):
                t = t0 + (t1 - t0) * j / 7
                points.append(surface(t, angle + .015 * math.sin(t * 9 + i), rng.uniform(.001, .003)))
            paths.append((points, rng.uniform(.0016, .0030)))
        # Short split stalks project from cut bundle ends; the silhouette is not
        # a smooth capped tube and each tuft has a slightly different length.
        for end in (0, 1):
            for i in range(count // 3):
                angle = math.tau * (i + rng.random()) / (count // 3)
                p = surface(end, angle)
                direction = -1 if end == 0 else 1
                length = rng.uniform(.020, .055)
                fan = (p - (a if end == 0 else b)) * .12
                paths.append(([p - axis * direction * .035,
                               p + axis * direction * length * .4,
                               p + axis * direction * length + fan], rng.uniform(.0017, .0027)))
        stalks(name + ' uneven individual stalk relief', paths, group)
        return surface, axis

    def white_colors(ob):
        # Copy the authored armor mask into the building export's active layer.
        # The unchanged Blender materials continue to read ArmorTint by name.
        colors = ob.data.color_attributes.get('Color')
        if colors is None:
            colors = ob.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
        authored = ob.data.color_attributes.get('ArmorTint')
        for i, value in enumerate(colors.data):
            value.color = authored.data[i].color if authored and authored.domain == 'CORNER' else (1, 1, 1, 1)
        ob.data.color_attributes.active_color = colors

    def append_parts(asset, names, group, transform=None, light_prop=False):
        path = samurai / asset / (asset + '.blend')
        with bpy.data.libraries.load(str(path), link=False) as (available, loaded):
            loaded.objects = [name for name in names if name in available.objects]
        appended = []
        for ob in loaded.objects:
            if ob is None or ob.type != 'MESH':
                continue
            old_name = ob.name
            matrix = ob.matrix_world.copy()
            ob.data = ob.data.copy()
            ob.parent = None
            ob.modifiers.clear()
            ob.constraints.clear()
            ob.animation_data_clear()
            ob.data.transform(matrix)
            if transform is not None:
                ob.data.transform(transform)
            ob.matrix_world = Matrix.Identity(4)
            for col in list(ob.users_collection):
                col.objects.unlink(ob)
            src.objects.link(ob)
            ob.hide_set(False)
            ob.hide_render = False
            ob.hide_viewport = False
            ob.name = 'RC01 reused ' + old_name
            ob['reused_from'] = asset + '.blend / ' + old_name
            if asset in ('Do01', 'Kabuto01', 'Sode01', 'Kusazuri01'):
                ob['reused_armor'] = True
            ob['module'] = group
            # Only the display copies of dense weapon furniture are simplified.
            # Armor uses its already-existing static LOD2 with no new reduction.
            if light_prop and len(ob.data.polygons) > 8000:
                reduction = ob.modifiers.new('Prop scale furniture detail', 'DECIMATE')
                reduction.ratio = .12
            white_colors(ob)
            groups[group].append(ob)
            appended.append(ob)
        return appended

    # A bundled straw human silhouette, with a visible hewn post and rope ties.
    g = begin('TrainingDummy_01')
    beam('Dummy planted timber post', (0, 0, .005), (0, 0, 1.45),
         .092, .080, 'Timber', g, rough=.003)
    for a in (-2.45, -.30, 1.50):
        tube('Dummy foot wedge', [(math.cos(a) * .22, math.sin(a) * .16, .02),
                                  (math.cos(a) * .09, math.sin(a) * .06, .11)],
             .043, 'Timber', g, sides=7)
    torso, torso_axis = straw_bundle('Dummy tightly pressed straw torso', (.005, -.01, .585), (-.015, -.015, 1.27),
                                     [(0, .175), (.08, .196), (.24, .205), (.30, .174),
                                      (.49, .193), (.68, .207), (.79, .179), (.93, .196), (1, .159)],
                                     g, squash=.73, count=112)
    tube('Dummy shoulder crossbar', [(-.61, 0, 1.18), (.61, 0, 1.18)],
         .039, 'Timber', g, sides=8)
    for sign in (-1, 1):
        arm, arm_axis = straw_bundle('Dummy cut bound straw arm', (sign * .14, -.015, 1.19),
                                     (sign * .555, -.012, 1.16 + sign * .008),
                                     [(0, .082), (.13, .095), (.34, .080), (.59, .090),
                                      (.78, .071), (1, .081)], g, squash=.97, count=48)
        for t in (.34, .78):
            for j in range(3):
                tube('Dummy arm rope binding',
                     [arm(t + (j - 1) * .024, i * math.tau / 40, .006) for i in range(41)],
                     .006, 'Rope', g, sides=6)
    head, head_axis = straw_bundle('Dummy raw cut straw head', (.018, -.01, 1.305), (-.007, -.014, 1.602),
                                   [(0, .073), (.17, .098), (.39, .115), (.67, .120), (1, .116)],
                                   g, squash=.83, count=64)
    for t in (.11, .19):
        tube('Dummy neck gathered tie', [head(t, i * math.tau / 36, .007) for i in range(37)],
             .007, 'Rope', g, sides=6)
    for t in (.30, .79):
        for j in range(3):
            points = [torso(t + (j - 1) * .022, i * math.tau / 56, .008) for i in range(57)]
            tube('Dummy closely wrapped torso binding', points, .0075, 'Rope', g, sides=7)
    tube('Dummy diagonal lashing', [(-.145, -.142, 1.195), (-.089, -.16, 1.09),
                                    (.008, -.168, .945), (.119, -.15, .80)],
         .009, 'Rope', g, sides=7)
    # A knot and hanging rope ends connect the tied sheaf to the hidden frame.
    tube('Dummy front binding knot', [(.13, -.15, .815), (.163, -.158, .785), (.139, -.171, .762),
                                      (.115, -.174, .79), (.154, -.179, .81), (.17, -.169, .78)],
         .009, 'Rope', g, sides=7)
    tube('Dummy loose rope end', [(.148, -.175, .784), (.157, -.19, .705),
                                 (.139, -.20, .624), (.15, -.19, .588)], .0065, 'Rope', g, sides=6)
    tube('Dummy short rope end', [(.16, -.172, .787), (.19, -.20, .73),
                                  (.186, -.209, .669)], .006, 'Rope', g, sides=6)

    # Open rack: wide feet and crossbars keep the slender stored weapons legible.
    g = begin('WeaponRack_01')
    for x in (-.80, .80):
        beam('Weapon rack foot', (x, -.34, .075), (x, .34, .075),
             .13, .12, 'Timber', g, rough=.003)
        beam('Weapon rack upright', (x, .065, .10), (x, .065, 1.52),
             .105, .095, 'Timber', g, rough=.003)
        beam('Weapon rack rear brace', (x, .29, .14), (x, .08, .77),
             .066, .067, 'Timber', g, rough=.002)
    for z in (.23, 1.31):
        beam('Weapon rack crossbar', (-.91, .065, z), (.91, .065, z),
             .095, .095, 'Timber', g, rough=.002)
    for x in (-.67, -.36, -.04, .28, .59):
        tube('Weapon rack timber cradle peg', [(x, .075, 1.34), (x, -.11, 1.34)],
             .023, 'Timber', g, sides=7)
    yumi_names = ['Yumi_01_UpperLimb', 'Yumi_01_LowerLimb', 'Yumi_01_UpperNock',
                  'Yumi_01_LowerNock', 'Yumi_01_Grip', 'Yumi_01_Fittings', 'Yumi_01_String']
    for x, angle in [(-.62, -3), (-.22, 4)]:
        transform = Matrix.Translation((x, -.055, .845)) @ Matrix.Rotation(math.radians(angle), 4, 'Y')
        append_parts('Yumi01', yumi_names, g, transform, light_prop=True)
    # The existing sheathed sword keeps its lacquer saya and fittings. Hidden
    # steel and minute wrap sculpture are unnecessary for this stored prop.
    sword_names = ['Tachi_01_Tsuka', 'Tachi_01_Tsuba', 'Tachi_01_Saya',
                   'Tachi_01_Kojiri', 'Tachi_01_Kashira', 'Tachi_01_Fuchi', 'Tachi_01_Habaki']
    transform = Matrix.Translation((.49, -.16, 1.07)) @ Matrix.Rotation(math.radians(87), 4, 'Y')
    append_parts('Tachi01', sword_names, g, transform, light_prop=True)
    for x, top in [(.10, 1.83), (.28, 1.92), (.68, 1.79)]:
        tube('Rack plain wooden training staff', [(x - .07, -.12, .20), (x, -.04, top)],
             .019, 'Timber', g, sides=8)
    # Existing rope around the outer joints makes this a rural carpentry prop.
    for x in (-.80, .80):
        for z in (.24, 1.31):
            for j in range(2):
                ring('Rack joint rope binding', (x, .065, z + (j - .5) * .02), .076, .079, g, wire=.009)

    # The original armor meshes, hung on a plain removable timber display stand.
    g = begin('ArmorStand_01')
    for x in (-.27, .27):
        beam('Armor stand splayed foot', (x, -.27, .045), (x, .27, .045),
             .08, .09, 'Timber', g, rough=.002)
    beam('Armor stand base tie', (-.34, 0, .115), (.34, 0, .115),
         .10, .09, 'Timber', g, rough=.002)
    beam('Armor stand central spine', (0, .035, .12), (0, .035, 1.59),
         .077, .078, 'Timber', g, rough=.0015)
    beam('Armor stand shoulders', (-.29, .02, 1.39), (.29, .02, 1.39),
         .073, .075, 'Timber', g, rough=.0015)
    for x in (-.27, .27):
        beam('Armor stand lower brace', (x, 0, .15), (0, .035, .49),
             .043, .044, 'Timber', g, rough=.001)
    lower = Matrix.Translation((0, 0, -.10))
    append_parts('Do01', ['SM_Do01_LOD2'], g, lower)
    append_parts('Kusazuri01', ['SM_Kusazuri01_LOD2'], g, lower)
    append_parts('Kabuto01', ['SM_Kabuto01_LOD2'], g, Matrix.Translation((0, -.025, 1.498)))
    for side, sign in [('L', 1), ('R', -1)]:
        pivot = Vector((sign * .18, .015, 1.49))
        hanging = (lower @ Matrix.Translation(pivot)
                   @ Matrix.Rotation(math.radians(sign * 28), 4, 'Y')
                   @ Matrix.Translation(-pivot))
        append_parts('Sode01', ['SM_Sode_' + side + '_01_LOD2'], g, hanging)

    # Same temporary four-petal flower clan mark used by SmallShrine01.
    # Black crest on a single calm off-white hanging; both faces carry the mark.
    g = begin('RetainerBanner_01')
    turned('Retainer banner stone socket', (0, .04, 0),
           [(0, .16), (.06, .18), (.14, .14), (.20, .095)], 'Stone', g, sides=12)
    tube('Retainer banner pole', [(0, .04, .12), (0, .04, 2.90)],
         .036, 'Timber', g, sides=10)
    tube('Retainer banner hanging crossarm', [(-.40, .04, 2.80), (.40, .04, 2.80)],
         .026, 'Timber', g, sides=8)
    top = 2.735

    def cloth_y(u, drop):
        v = drop / 1.90
        # The four restrained folds originate at the suspension tabs and relax
        # downwards. A slight lower billow preserves the weight of heavy linen.
        folds = .030 * math.sin((u + .325) * 27 + .42 * v)
        folds += .014 * math.sin((u + .325) * 54 + .75 * v) * (1 - .55 * v)
        return -.031 + folds * (.72 + .28 * v) + .070 * v * v + .009 * math.sin(drop * 6 + u * 4) * v

    def cloth_point(u, drop, offset=0):
        v = drop / 1.90
        sag = .010 * (1 - math.cos((u + .245) * math.tau / .245)) * math.exp(-drop * 6)
        bottom = v ** 12 * (.014 * math.sin(u * 13 + .4) + .006 * math.sin(u * 31 + 2))
        return (u, cloth_y(u, drop) + offset, top - drop - sag + bottom)

    verts, uvs, faces = [], [], []
    nx, nz = 41, 81
    for j in range(nz):
        drop = 1.90 * j / (nz - 1)
        for i in range(nx):
            u = -.325 + .65 * i / (nx - 1)
            verts.append(cloth_point(u, drop))
            uvs.append((i / (nx - 1), j / (nz - 1)))
    for j in range(nz - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + nx, a + nx + 1, a + 1))
    cloth = mesh('Retainer unbleached cloth banner', verts, faces, 'Cloth', uvs, g)
    for poly in cloth.data.polygons:
        poly.use_smooth = True
    thick = cloth.modifiers.new('Banner cloth thickness', 'SOLIDIFY')
    thick.thickness = .002
    thick.offset = 0
    # Folded hems have their own narrow surface rather than thick rope edges.
    for side in (-1, 1):
        vv, ff, uv = [], [], []
        for j in range(nz):
            drop = 1.90 * j / (nz - 1)
            for i, width in enumerate((0, .006, .014)):
                u = side * (.325 - width)
                vv.append(cloth_point(u, drop, -.0018 - .0014 * math.sin(math.pi * i / 2)))
                uv.append((width * 8, drop * 2))
            if j:
                q = (j - 1) * 3
                ff.extend([(q, q + 3, q + 4, q + 1), (q + 1, q + 4, q + 5, q + 2)])
        hem = mesh('Retainer folded linen side hem', vv, ff, 'Cloth', uv, g)
        for p in hem.data.polygons:
            p.use_smooth = True
    for drop in (.010, 1.885):
        vv, ff, uv = [], [], []
        for i in range(nx):
            u = -.325 + .65 * i / (nx - 1)
            for j, d in enumerate((drop - .008, drop, drop + .008)):
                vv.append(cloth_point(u, d, -.0025 - .0015 * math.sin(j * math.pi / 2)))
                uv.append((i / (nx - 1), j / 2))
            if i:
                q = (i - 1) * 3
                ff.extend([(q, q + 3, q + 4, q + 1), (q + 1, q + 4, q + 5, q + 2)])
        mesh('Retainer folded linen end hem', vv, ff, 'Cloth', uv, g)
    for x in (-.245, 0, .245):
        # Broad doubled fabric loops carry the load; small ties secure them.
        loop = [(x, cloth_y(x, .015), 2.705), (x, -.004, 2.790),
                (x, .019, 2.828), (x, .064, 2.822), (x, .082, 2.786),
                (x, .024, 2.720)]
        vv = [(p[0] + sign * .015, p[1], p[2]) for p in loop for sign in (-1, 1)]
        ff = [(i * 2, i * 2 + 2, i * 2 + 3, i * 2 + 1) for i in range(len(loop) - 1)]
        tab = mesh('Retainer doubled cloth suspension tab', vv, ff, 'Cloth', group=g)
        so = tab.modifiers.new('Suspension tab double cloth thickness', 'SOLIDIFY')
        so.thickness = .003
        tube('Retainer top fastening knot', [(x - .021, -.01, 2.80), (x, -.023, 2.773),
                                             (x + .019, -.014, 2.795), (x, -.021, 2.807),
                                             (x - .014, -.037, 2.757), (x - .009, -.035, 2.724)],
             .0045, 'Rope', g, sides=6)
    centre_z, scale = 2.205, 1.68
    for side in (-1, 1):
        def crest_point(u, z):
            return (u, cloth_y(u, top - z) + side * .0026, z)
        vv, ff = [], []
        for radius in (.098, .105, .112):
            for i in range(96):
                angle = i * math.tau / 96
                vv.append(crest_point(radius * scale * math.cos(angle),
                                      centre_z + radius * scale * math.sin(angle)))
        for j in range(2):
            for i in range(96):
                q = j * 96
                ff.append((q + i, q + (i + 1) % 96, q + (i + 1) % 96 + 96, q + i + 96))
        if side > 0:
            ff = [tuple(reversed(face)) for face in ff]
        mesh('Retainer existing clan crest circle', vv, ff, 'Ink', group=g)
        def printed_disc(name, cx, cz, radius_x, radius_z, angle=0):
            vv, ff = [crest_point(cx, cz)], []
            for j in range(1, 9):
                r = j / 8
                for i in range(40):
                    a = i * math.tau / 40
                    x, z = r * radius_x * math.cos(a), r * radius_z * math.sin(a)
                    vv.append(crest_point(cx + x * math.cos(angle) - z * math.sin(angle),
                                          cz + x * math.sin(angle) + z * math.cos(angle)))
                    if j == 1:
                        ff.append((0, 1 + i, 1 + (i + 1) % 40))
                    else:
                        q = 1 + (j - 2) * 40
                        ff.append((q + i, q + (i + 1) % 40, q + (i + 1) % 40 + 40, q + i + 40))
            if side > 0:
                ff = [tuple(reversed(face)) for face in ff]
            printed = mesh(name, vv, ff, 'Ink', group=g)
            for p in printed.data.polygons:
                p.use_smooth = True
        for petal in range(4):
            angle = petal * math.pi / 2
            printed_disc('Retainer existing clan flower petal', .047 * scale * math.cos(angle),
                         centre_z + .047 * scale * math.sin(angle), .027 * scale, .020 * scale, angle)
        printed_disc('Retainer existing clan flower centre', 0, centre_z, .017 * scale, .017 * scale)

    # Tall, narrow tripod braziers follow the entrance reference. Their warm
    # coal/flame geometry reuses Smithy01's existing ember material; no effects.
    g = begin('Brazier_01')
    for i in range(3):
        a = i * math.tau / 3 + .25
        tube('Brazier tall crossed tripod support', [(math.cos(a) * .30, math.sin(a) * .30, .015),
                                                    (math.cos(a) * .18, math.sin(a) * .18, .44),
                                                    (math.cos(a) * .095, math.sin(a) * .095, .76),
                                                    (math.cos(a) * .20, math.sin(a) * .20, 1.00)],
             .027, 'Timber', g, sides=8)
        tube('Brazier forged bowl cradle', [(math.cos(a) * .090, math.sin(a) * .090, .78),
                                            (math.cos(a) * .16, math.sin(a) * .16, .91),
                                            (math.cos(a) * .265, math.sin(a) * .265, 1.065)],
             .016, 'Iron', g, sides=6)
    ring('Brazier iron tripod binding collar', (0, 0, .76), .104, .104, g, material='Iron', wire=.016)
    ring('Brazier iron tripod lower tie', (0, 0, .28), .232, .232, g, material='Iron', wire=.009)
    turned('Brazier open iron fire bowl', (0, 0, 0),
           [(.875, .105), (.905, .16), (.960, .232), (1.035, .279),
            (1.062, .284), (1.068, .270), (1.037, .263), (.973, .214),
            (.927, .147), (.920, .102)], 'Iron', g, sides=40)
    ring('Brazier hammered rolled rim', (0, 0, 1.062), .279, .279, g, material='Iron', wire=.010)
    # Slightly proud peened fasteners at the three bowl cradles.
    for i in range(9):
        a = i * math.tau / 9
        tube('Brazier bowl peened rivet', [(.277 * math.cos(a), .277 * math.sin(a), 1.035),
                                          (.286 * math.cos(a), .286 * math.sin(a), 1.035)],
             .007, 'Iron', g, sides=8)
    turned('Brazier charcoal bed', (0, 0, 0), [(.925, .11), (.970, .202), (.982, .196)], 'Charcoal', g, sides=24)
    # Split charred wood lies below the lip, with sparse hot fracture lines.
    for i in range(4):
        a = i * 1.37 + .3
        length = .30 + .041 * math.sin(i * 2.5)
        x, y = .045 * math.sin(i * 3.1), .04 * math.cos(i * 1.5)
        z = .985 + .015 * i
        end_a = Vector((x - math.cos(a) * length / 2, y - math.sin(a) * length / 2, z))
        end_b = Vector((x + math.cos(a) * length / 2, y + math.sin(a) * length / 2, z + .013))
        tube('Brazier charred split fuel', [end_a, (end_a + end_b) * .5 + Vector((0, .005, .003)), end_b],
             .024, 'Charcoal', g, sides=6)
        glow = [end_a.lerp(end_b, .15) + Vector((0, 0, .019)),
                end_a.lerp(end_b, .39) + Vector((.003, 0, .020)),
                end_a.lerp(end_b, .62) + Vector((-.002, 0, .020)),
                end_a.lerp(end_b, .81) + Vector((0, 0, .019))]
        tube('Brazier thin glowing split', glow, .003, 'Ember', g, sides=4)
    for i in range(14):
        a, r = i * 2.40, .16 * math.sqrt((i + .5) / 14)
        cx, cy = r * math.cos(a), r * math.sin(a)
        z, radius = .981 + .014 * math.sin(i * 2.9), .018 + .005 * math.sin(i * 5)
        vv = [(cx + math.cos(j * math.tau / 7) * radius,
               cy + math.sin(j * math.tau / 7) * radius, z + .005 * math.sin(j * 3 + i)) for j in range(7)]
        vv.append((cx + radius * .2, cy - radius * .15, z + radius * .70))
        ff = [(j, (j + 1) % 7, 7) for j in range(7)]
        mesh('Brazier small live coal', vv, ff, 'Ember' if i % 3 == 0 else 'Charcoal', group=g)
    # Three slender irregular tongues: low continuous fire, no opaque fireball.
    for index, (x, y, height, lean) in enumerate([(-.053, -.01, .25, -.045), (.034, .018, .34, .043), (.095, -.025, .19, -.032)]):
        vv, ff = [], []
        profile = [(0, .019), (.12, .036), (.36, .028), (.62, .021), (.83, .009), (1, .001)]
        for j, (t, radius) in enumerate(profile):
            cx = x + lean * t + .012 * math.sin(t * 6 + index) * t
            cy = y + .019 * math.sin(t * 5 + index) * t
            for k in range(7):
                a = k * math.tau / 7
                vv.append((cx + radius * math.cos(a), cy + radius * .52 * math.sin(a), 1.01 + height * t))
                if j:
                    q = (j - 1) * 7
                    ff.append((q + k, q + (k + 1) % 7, q + (k + 1) % 7 + 7, q + k + 7))
        ff.extend([tuple(reversed(range(7))), tuple(range(len(vv) - 7, len(vv)))])
        mesh('Brazier restrained ember flame', vv, ff, 'Ember', group=g)
    return modules
