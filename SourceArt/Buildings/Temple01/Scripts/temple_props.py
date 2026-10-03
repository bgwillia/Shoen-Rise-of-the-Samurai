"""Authored exterior accessories for Temple_01; dimensions are in metres."""


def build_props(env):
    """Build four editable, locally centered modules with the existing art kit.

    Gate faces -Y. The pavilion and gate have ground-center origins. Bell geometry
    starts at its open mouth at Z=0; place at (0, 0, 1.3) in the pavilion. Fence
    runs along X, with its origin at the ground-level center, ends at X=+/-1.
    """
    import math

    mesh, beam, tube, block = (env[k] for k in ('mesh', 'beam', 'tube', 'block'))
    before, collect = (env[k] for k in ('before', 'collect'))

    def tint(ob, color):
        # The assembling script can preserve this explicit authored tint while
        # building its shared export Color layer. No new material is introduced.
        ob['temple_tint'] = color
        colors = ob.data.color_attributes.get('Color')
        if colors is None:
            colors = ob.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
        for value in colors.data:
            value.color = (*color, 1)
        ob.data.color_attributes.active_color = colors
        return ob

    def plate(name, corners, thickness, group, color):
        """One closed hand-laid roofing piece; corners follow its roof surface."""
        n = len(corners)
        vertices = list(corners) + [(x, y, z - thickness) for x, y, z in corners]
        faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
        faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
        uv = [(x * .75, y * .75) for x, y, z in vertices]
        return tint(mesh(name, vertices, faces, 'Cedar', uv, group), color)

    def fascia(name, points, width, height, group, color=(.90, .85, .75)):
        """Chamfered, square-section joinery following an authored eave curve."""
        outline = [(-.44, -.50), (.44, -.50), (.50, -.40), (.50, .40),
                   (.44, .50), (-.44, .50), (-.50, .40), (-.50, -.40)]
        vertices, faces, uv = [], [], []
        distance = 0
        for j, point in enumerate(points):
            prev, nxt = points[max(0, j - 1)], points[min(len(points) - 1, j + 1)]
            dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
            length = max(.00001, math.hypot(dx, dy))
            if j:
                distance += math.dist(points[j - 1], point)
            for i, (across, vertical) in enumerate(outline):
                vertices.append((point[0] - dy / length * across * width,
                                 point[1] + dx / length * across * width,
                                 point[2] + vertical * height))
                uv.append((distance * .60, i / 8))
                if j:
                    a, b = (j - 1) * 8 + i, (j - 1) * 8 + (i + 1) % 8
                    faces.append((a, b, b + 8, a + 8))
        faces.extend([tuple(reversed(range(8))), tuple(range(len(vertices) - 8, len(vertices)))])
        return tint(mesh(name, vertices, faces, 'Cedar', uv, group), color)

    def carved_arm(name, center, along, span, depth, group, height=1):
        """A broad bracket shoulder with paired cloud-shaped underside lobes."""
        profile = [(-.50, .055), (.50, .055), (.50, -.015), (.45, -.090),
                   (.38, -.115), (.31, -.063), (.255, -.080), (.185, -.185),
                   (.10, -.245), (-.10, -.245), (-.185, -.185), (-.255, -.080),
                   (-.31, -.063), (-.38, -.115), (-.45, -.090), (-.50, -.015)]
        ax, ay = along
        vertices = []
        for side in (-1, 1):
            vertices.extend((center[0] + ax * u * span - ay * side * depth / 2,
                             center[1] + ay * u * span + ax * side * depth / 2,
                             center[2] + z * height) for u, z in profile)
        n = len(profile)
        faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
        faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
        ob = tint(mesh(name, vertices, faces, 'Cedar',
                       [(v[0] * .6 + v[1] * .3, v[2]) for v in vertices], group), (.93, .86, .73))
        bevel = ob.modifiers.new('Carved shoulder softened arrises', 'BEVEL')
        bevel.width, bevel.segments = .008, 2
        return ob

    def post_shoe(name, x, y, z, post_width, group):
        """Four short iron heel plates, with two restrained peened fasteners."""
        half = post_width / 2 + .006
        for axis in (0, 1):
            for side in (-1, 1):
                center = (x, y + side * half, z) if axis == 0 else (x + side * half, y, z)
                size = (post_width * .80, .018, .20) if axis == 0 else (.018, post_width * .80, .20)
                tint(block(name + ' iron heel plate', center, size, 'Iron', group, .005), (.57, .58, .53))
                for dz in (-.058, .058):
                    start = (center[0], center[1], z + dz)
                    end = (start[0], start[1] + side * .015, start[2]) if axis == 0 else (start[0] + side * .015, start[1], start[2])
                    tint(tube(name + ' iron peened shoe rivet', [start, end], .013,
                              'Iron', group, sides=8), (.64, .65, .59))

    def ring(name, radius, z, wire, group, color=(.68, .57, .38)):
        ob = tube(name, [(radius * math.cos(i * math.tau / 48),
                          radius * math.sin(i * math.tau / 48), z) for i in range(49)],
                  wire, 'Iron', group, sides=8)
        return tint(ob, color)

    # Formal open gate: a shallow gabled roof, actual bracket work and four
    # restrained uprights. It deliberately has neither torii bars nor chigi.
    old = before()
    g = 'TP01_Gate'
    for x in (-2.15, 2.15):
        for y in (-.39, .39):
            block('Gate dressed stone post spreading foot', (x, y, .045), (.55, .55, .09), 'Stone', g, .018)
            block('Gate dressed stone post raised die', (x, y, .14), (.43, .43, .11), 'Stone', g, .014)
            block('Gate dressed stone post chamfered cap', (x, y, .225), (.49, .49, .07), 'Stone', g, .022)
            beam('Gate square structural post', (x, y, .26), (x, y, 2.65), .30, .30,
                 mat='Cedar', group=g, rough=.0015)
            post_shoe('Gate column', x, y, .385, .30, g)
            block('Gate column foot collar', (x, y, .285), (.325, .325, .055), 'Cedar', g, .009)
            block('Gate square capital', (x, y, 2.55), (.48, .48, .18), 'Cedar', g, .014)
            for direction in (-1, 1):
                # Broad angled knees are visible beneath the eaves.
                beam('Gate column corner knee', (x, y, 2.18),
                     (x + direction * .40, y, 2.55), .14, .16, mat='Cedar', group=g, rough=.001)
            carved_arm('Gate paired carved capital shoulders', (x, y, 2.49), (1, 0), .98, .20, g)
            carved_arm('Gate outboard carved roof bracket', (x, y, 2.70), (0, 1), 1.06, .20, g, .8)
            for offset in (-.32, .32):
                block('Gate bracket upper bearing block', (x, y + offset, 2.75), (.25, .22, .12), 'Cedar', g, .01)
        beam('Gate short depth tie', (x, -.68, 2.61), (x, .68, 2.61), .22, .24, mat='Cedar', group=g)
        beam('Gate side lower tie', (x, -.39, .61), (x, .39, .61), .13, .12, mat='Cedar', group=g)
    for y in (-.39, .39):
        beam('Gate broad head beam', (-2.40, y, 2.57), (2.40, y, 2.57), .23, .28, mat='Cedar', group=g, rough=.001)
        beam('Gate upper architrave', (-2.44, y, 2.77), (2.44, y, 2.77), .19, .18, mat='Cedar', group=g, rough=.001)
        for x in (-1.80, -1.20, -.60, 0, .60, 1.20, 1.80):
            block('Gate lintel spaced timber dentil', (x, y, 2.69), (.12, .21, .16), 'Cedar', g, .005)
    # A quiet timber plaque gives a focal point without invented writing.
    block('Gate central framed dedication plaque', (0, -.548, 2.56), (.53, .075, .35), 'Timber', g, .013)
    tint(block('Gate plaque inset face', (0, -.591, 2.56), (.42, .018, .25), 'Timber', g, .003), (.39, .31, .22))

    def gate_surface(x, t, side, lift=0):
        return (x, side * 1.02 * t,
                2.70 + .77 * max(0, 1 - t) ** 1.80 + .13 * t ** 8
                + .095 * (abs(x) / 2.73) ** 7 * t ** 3 + lift)

    for side in (-1, 1):
        # Substantial sheathing and two fascia courses carry the shingle roof.
        for j in range(12):
            t0, t1 = j / 12, (j + 1) / 12
            for i in range(12):
                x0, x1 = -2.73 + 5.46 * i / 12, -2.73 + 5.46 * (i + 1) / 12
                plate('Gate roof continuous sheathing',
                      [gate_surface(x0, t0, side), gate_surface(x1, t0, side),
                       gate_surface(x1, t1, side), gate_surface(x0, t1, side)],
                      .115, g, (.77, .72, .63))
        # Tightly laid overlapping shingles make the broad roof read as wood.
        for row in range(7):
            t0, t1 = max(0, row / 7 - .025), min(1.008, (row + 1) / 7 + .019)
            for col in range(23):
                x0 = -2.73 + col * 5.46 / 23 + (row % 2) * .055
                x1 = min(2.73, x0 + 5.46 / 23 - .006)
                x0 = max(-2.73, x0)
                if x0 >= x1:
                    continue
                value = .90 + .035 * math.sin(col * 2.4 + row * 1.7)
                plate('Gate staggered cedar roof shingle',
                      [gate_surface(x0, t0, side, .023), gate_surface(x1, t0, side, .023),
                       gate_surface(x1, t1, side, .038), gate_surface(x0, t1, side, .038)],
                      .030, g, (value, value * .944, value * .833))
        for x in (-2.65, -2.15, -1.62, -1.08, -.54, 0, .54, 1.08, 1.62, 2.15, 2.65):
            points = [gate_surface(x, i / 10, side, -.15) for i in range(11)]
            fascia('Gate visible curved square common rafter', points, .080, .085, g, (.79, .73, .62))
        fascia('Gate sweeping broad eave fascia',
               [gate_surface(-2.78 + i * 5.56 / 24, 1, side, -.079) for i in range(25)],
               .15, .17, g)
        fascia('Gate lower stepped eave moulding',
               [gate_surface(-2.78 + i * 5.56 / 24, .963, side, -.185) for i in range(25)],
               .19, .085, g, (.82, .77, .67))
        fascia('Gate thin proud eave drip edge',
               [gate_surface(-2.80 + i * 5.60 / 24, 1.018, side, .012) for i in range(25)],
               .145, .052, g, (.94, .88, .77))
    for x in (-2.73, 2.73):
        for side in (-1, 1):
            fascia('Gate broad shaped gable bargeboard',
                   [gate_surface(x, i / 14, side, -.045) for i in range(15)], .16, .18, g)
            fascia('Gate raised gable finishing moulding',
                   [gate_surface(x, i / 14, side, .067) for i in range(15)], .105, .050, g, (.94, .88, .78))
        beam('Gate gable king post', (x, 0, 2.76), (x, 0, 3.42), .12, .12, mat='Cedar', group=g)
        beam('Gate gable short collar tie', (x, -.49, 2.97), (x, .49, 2.97), .10, .12, mat='Cedar', group=g)
    beam('Gate layered timber ridge bed', (-2.77, 0, 3.48), (2.77, 0, 3.48), .28, .10, mat='Cedar', group=g, rough=.001)
    beam('Gate narrow ridge crown', (-2.82, 0, 3.57), (2.82, 0, 3.57), .18, .09, mat='Cedar', group=g, rough=.001)
    collect(old, 'TempleGate_01')

    # A square open pavilion with a low stone pad and a compact curved roof.
    old = before()
    g = 'TP01_BellPavilion'
    for x in (-.9375, -.3125, .3125, .9375):
        for y in (-.9375, -.3125, .3125, .9375):
            block('Bell pavilion low stone paving slab', (x, y, .08), (.616, .616, .16), 'Stone', g, .015)
    for x in (-1.02, 1.02):
        for y in (-1.02, 1.02):
            block('Pavilion dressed stone spreading foot', (x, y, .195), (.43, .43, .085), 'Stone', g, .018)
            block('Pavilion dressed stone raised die', (x, y, .275), (.32, .32, .075), 'Stone', g, .012)
            block('Pavilion dressed stone chamfered cap', (x, y, .335), (.39, .39, .060), 'Stone', g, .017)
            beam('Pavilion four timber columns', (x, y, .365), (x, y, 2.63), .22, .22, mat='Cedar', group=g, rough=.0015)
            post_shoe('Pavilion column', x, y, .478, .22, g)
            block('Pavilion timber capital block', (x, y, 2.48), (.39, .39, .17), 'Cedar', g, .012)
            for axis in (0, 1):
                delta = -.39 if (x if axis == 0 else y) > 0 else .39
                end = (x + delta, y, 2.55) if axis == 0 else (x, y + delta, 2.55)
                beam('Pavilion open knee brace', (x, y, 2.15), end, .135, .135, mat='Cedar', group=g, rough=.001)
            carved_arm('Pavilion lower carved capital arm', (x, y, 2.59), (1, 0), .85, .17, g, .80)
            carved_arm('Pavilion upper carved capital arm', (x, y, 2.69), (0, 1), .90, .17, g, .70)
            for offset in (-.28, .28):
                block('Pavilion stepped roof bearing block', (x + offset, y, 2.68), (.20, .23, .12), 'Cedar', g, .01)
    for side in (-1, 1):
        beam('Pavilion front rear head tie', (-1.29, side * 1.02, 2.51), (1.29, side * 1.02, 2.51), .20, .24, mat='Cedar', group=g)
        beam('Pavilion side head tie', (side * 1.02, -1.29, 2.64), (side * 1.02, 1.29, 2.64), .21, .21, mat='Cedar', group=g)
    beam('Pavilion bell suspension crossbeam', (-1.14, 0, 2.79), (1.14, 0, 2.79), .20, .23, mat='Cedar', group=g)
    tube('Pavilion short bell iron suspension', [(0, 0, 2.76), (0, 0, 2.53)], .025, 'Iron', g, sides=10)

    def pavilion_surface(side, across, t, lift=0):
        r = 1.72 * t
        x, y = across * r, -r
        angle = side * math.pi / 2
        z = 2.53 + .89 * max(0, 1 - t) ** 1.7 + .115 * t ** 8
        z += .155 * abs(across) ** 6 * t ** 5
        return (x * math.cos(angle) - y * math.sin(angle),
                x * math.sin(angle) + y * math.cos(angle), z + lift)

    for side in range(4):
        for row in range(10):
            t0, t1 = .035 + row * .965 / 10, .035 + (row + 1) * .965 / 10
            for col in range(10):
                u0, u1 = -1 + col * .2, -1 + (col + 1) * .2
                plate('Pavilion curved roof timber substrate',
                      [pavilion_surface(side, u0, t0), pavilion_surface(side, u1, t0),
                       pavilion_surface(side, u1, t1), pavilion_surface(side, u0, t1)],
                      .105, g, (.77, .72, .63))
        for row in range(9):
            t0, t1 = max(.028, .035 + row * .965 / 9 - .021), min(1.006, .035 + (row + 1) * .965 / 9 + .010)
            # The taper is cut into each shingle instead of a rectangular roof.
            count = max(2, round(3.44 * t1 / .21))
            for col in range(count):
                u0, u1 = -1 + col * 2 / count + .002, -1 + (col + 1) * 2 / count - .002
                value = .90 + .035 * math.sin(col * 1.8 + row * 2.37 + side)
                plate('Pavilion radial hand laid cedar shingles',
                      [pavilion_surface(side, u0, t0, .023), pavilion_surface(side, u1, t0, .023),
                       pavilion_surface(side, u1, t1, .039), pavilion_surface(side, u0, t1, .039)],
                      .027, g, (value, value * .944, value * .833))
        fascia('Pavilion sweeping broad eave fascia',
               [pavilion_surface(side, -1 + i / 12, 1, -.072) for i in range(25)],
               .14, .155, g)
        fascia('Pavilion lower stepped eave moulding',
               [pavilion_surface(side, -1 + i / 12, .971, -.168) for i in range(25)],
               .17, .077, g, (.82, .77, .67))
        fascia('Pavilion projecting upper drip moulding',
               [pavilion_surface(side, -1 + i / 12, 1.013, .011) for i in range(25)],
               .13, .048, g, (.94, .88, .77))
        for u in (-.90, -.60, -.30, 0, .30, .60, .90):
            fascia('Pavilion exposed square roof underside rafter',
                   [pavilion_surface(side, u, .15 + .85 * i / 9, -.139) for i in range(10)],
                   .065, .075, g, (.79, .73, .62))
        fascia('Pavilion raised curved hip cap',
               [pavilion_surface(side, 1, .04 + .96 * i / 16, .061) for i in range(17)],
               .15, .11, g, (.93, .87, .76))
    block('Pavilion compact layered apex base', (0, 0, 3.43), (.31, .31, .075), 'Cedar', g, .018)
    block('Pavilion compact layered apex cap', (0, 0, 3.51), (.22, .22, .065), 'Cedar', g, .016)
    block('Pavilion simple timber crown', (0, 0, 3.57), (.12, .12, .075), 'Cedar', g, .024)
    # A static horizontal striker hangs beside the bell; no dynamic rig is used.
    beam('Bell suspended timber striker', (0, -1.56, 1.65), (0, -.40, 1.65), .16, .17, group=g, rough=.003)
    for y in (-1.27, -.64):
        tube('Bell striker hanging hemp rope', [(0, y, 2.59), (.01, y + .015, 2.12), (0, y, 1.72)],
             .014, 'Rope', g, sides=6)
        for shift in (-.027, 0, .027):
            tube('Bell striker rope binding',
                 [(.099 * math.cos(i * math.tau / 16), y + shift,
                   1.65 + .105 * math.sin(i * math.tau / 16)) for i in range(17)],
                 .009, 'Rope', g, sides=6)
    collect(old, 'TempleBellPavilion_01')

    # Hollow cast bell. Lip starts at local ground; the module is then lifted
    # 1.30 m into the pavilion. A closed radial wall retains its open mouth.
    old = before()
    g = 'TP01_Bell'
    profile = [(0, .426), (.025, .449), (.090, .448), (.145, .416),
               (.25, .392), (.55, .357), (.84, .329), (.935, .296),
               (.995, .218), (1.045, .116), (1.061, .035),
               (1.005, .031), (.981, .103), (.938, .194), (.883, .262),
               (.81, .285), (.54, .314), (.22, .354), (.068, .385), (0, .386)]
    vertices, faces, uv = [], [], []
    sides = 64
    for j, (z, radius) in enumerate(profile):
        for i in range(sides):
            angle = i * math.tau / sides
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
            uv.append((i / sides, z))
    for j in range(len(profile)):
        next_ring = (j + 1) % len(profile)
        for i in range(sides):
            faces.append((j * sides + i, j * sides + (i + 1) % sides,
                          next_ring * sides + (i + 1) % sides, next_ring * sides + i))
    bell = tint(mesh('Temple bell hollow cast bronze body', vertices, faces, 'Iron', uv, g), (.72, .60, .40))
    for poly in bell.data.polygons:
        poly.use_smooth = True
    for radius, z, wire in ((.442, .029, .015), (.440, .092, .012),
                            (.406, .180, .009), (.361, .525, .009),
                            (.327, .844, .010), (.295, .938, .010)):
        ring('Bell raised cast horizontal band', radius, z, wire, g)
    # Four generous panels and shallow nipple bosses give the distant bell its
    # cast-temple identity; no tiny lettering or elaborate dragon ornament.
    for quarter in range(4):
        center_angle = quarter * math.pi / 2
        for edge_angle in (center_angle - .60, center_angle + .60):
            tube('Bell shallow cast vertical panel edge',
                 [(.365 * math.cos(edge_angle), .365 * math.sin(edge_angle), .53),
                  (.339 * math.cos(edge_angle), .339 * math.sin(edge_angle), .78),
                  (.331 * math.cos(edge_angle), .331 * math.sin(edge_angle), .837)],
                 .008, 'Iron', g, sides=6)
        for row in range(3):
            z = .622 + row * .083
            radius = .357 - (z - .55) * .097
            for col in range(4):
                angle = center_angle + (col - 1.5) * .235
                tube('Bell restrained cast boss cluster',
                     [(radius * math.cos(angle), radius * math.sin(angle), z),
                      ((radius + .018) * math.cos(angle), (radius + .018) * math.sin(angle), z)],
                     .018, 'Iron', g, sides=8)
        # One low, broad striking disk per side, flush enough to remain modest.
        angle = center_angle
        tube('Bell round cast striking panel',
             [(.376 * math.cos(angle), .376 * math.sin(angle), .354),
              (.385 * math.cos(angle), .385 * math.sin(angle), .354)],
             .062, 'Iron', g, sides=20)
    tint(tube('Bell stout crown suspension loop',
              [(.073 * math.cos(i * math.tau / 24), 0,
                1.146 + .083 * math.sin(i * math.tau / 24)) for i in range(25)],
              .020, 'Iron', g, sides=10), (.71, .60, .41))
    for ob in env['src'].objects:
        if ob not in old and ob.type == 'MESH' and not ob.get('temple_tint'):
            tint(ob, (.68, .57, .38))
    collect(old, 'TempleBell_01')

    # Low maintained boundary: an open railing, with a repeat length of 2 m.
    old = before()
    g = 'TP01_Fence'
    for x in (-1, 1):
        block('Temple boundary stone foot', (x, 0, .065), (.23, .24, .13), 'Stone', g, .02)
        beam('Temple boundary square timber post', (x, 0, .12), (x, 0, .94), .12, .12, group=g, rough=.001)
        block('Temple boundary post small cap', (x, 0, .945), (.16, .16, .065), 'Timber', g, .012)
    for z, width, depth in ((.29, .095, .11), (.83, .12, .12)):
        beam('Temple low continuous boundary rail', (-1.015, 0, z), (1.015, 0, z), width, depth, group=g, rough=.001)
    for x in (-.75, -.50, -.25, 0, .25, .50, .75):
        beam('Temple boundary open vertical baluster', (x, 0, .33), (x, 0, .78), .045, .045, group=g, rough=.0008)
    collect(old, 'Temple_Fence_01')

    return {
        'bell_placement': (0, 0, 1.3),
        'fence_origin': 'ground-center; repeat axis X; post centers at X=-1 and X=+1',
        'fence_repeat_length': 2.0,
        'gate_front': '-Y',
        'gate_clear_opening': 4.0,
    }
