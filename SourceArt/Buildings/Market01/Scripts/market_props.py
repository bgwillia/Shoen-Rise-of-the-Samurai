"""A small reusable vocabulary of rural market goods, authored in metres."""


def build_props(ns):
    """Return local modules; only HangingGoods has a raised attachment pivot."""
    from pathlib import Path

    bpy, math, Vector = (ns[k] for k in ('bpy', 'math', 'Vector'))
    mesh, beam, tube = (ns[k] for k in ('mesh', 'beam', 'tube'))
    groups, src, mats = (ns[k] for k in ('groups', 'src', 'mats'))
    rng = ns['random'].Random(1180319)
    modules = {}
    buildings = Path(__file__).resolve().parents[2]

    def begin(key):
        groups[key] = []
        modules[key] = groups[key]
        return key

    def turned(name, center, profile, material, group, squash=1, n=24):
        """A continuous pot/sack profile; profiles include the inside of mouths."""
        pottery_surface = material == 'Pottery'
        if pottery_surface:
            # Subdivide the wheel profile, retaining the actual hollow rolled lip.
            # Gentle radial curves avoid the stacked-cone look of sparse lathe rings.
            dense = []
            for j in range(len(profile) - 1):
                p0, p1 = profile[max(0, j - 1)], profile[j]
                p2, p3 = profile[j + 1], profile[min(len(profile) - 1, j + 2)]
                steps = max(2, int(abs(p2[0] - p1[0]) / .007))
                for step in range(steps):
                    t = step / steps
                    z = p1[0] + (p2[0] - p1[0]) * t
                    r = .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                              + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t*t
                              + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t*t*t)
                    dense.append((z, max(.001, r)))
            profile = dense + [profile[-1]]
            n = 48
        verts, uvs, faces = [], [], []
        height = max(z for z, radius in profile)
        phase = center[0] * 7.3 + center[1] * 8.1 + height * 3.4
        for j, (z, radius) in enumerate(profile):
            for i in range(n):
                a = math.tau * i / n
                if pottery_surface:
                    r = radius * (1 + .022 * math.sin(2*a + phase)
                                  + .010 * math.sin(3*a - z * 8 + phase))
                    # Small thrown rings are relief in the ceramic, not added bands.
                    r += .00085 * math.sin(z * 390 + .5 * math.sin(a * 3))
                    rim = max(0, (z / height - .94) / .06)
                    angle = (a - 1.3 - phase + math.pi) % math.tau - math.pi
                    chip = .004 * max(0, 1 - abs(angle) / .16) * rim
                    zz = z + .0016 * rim * math.sin(3*a + phase) - chip
                    dx = .006 * math.sin(z / height * 2.4) * math.sin(phase)
                    dy = .004 * z / height
                else:
                    r = radius * (1 + .033 * math.sin(3*a + phase + z*3)
                                  + .012 * math.sin(7*a - z*8))
                    zz, dx, dy = z, .007 * math.sin(z * 12), 0
                verts.append((center[0] + dx + r * math.cos(a),
                              center[1] + dy + r * squash * math.sin(a), center[2] + zz))
                uvs.append((i / n * 1.5, z * 2))
                if j:
                    faces.append(((j - 1) * n + i, (j - 1) * n + (i + 1) % n,
                                  j * n + (i + 1) % n, j * n + i))
        faces += [tuple(reversed(range(n))),
                  tuple(range((len(profile) - 1) * n, len(profile) * n))]
        ob = mesh(name, verts, faces, material, uvs, group)
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices) == 4
        return ob

    def ring(name, center, radii, group, material='Rope', thickness=.008):
        return tube(name, [(center[0] + radii[0] * math.cos(i * math.tau / 32),
                            center[1] + radii[1] * math.sin(i * math.tau / 32),
                            center[2]) for i in range(33)],
                    thickness, material, group, 6)

    def leaf(name, base, tip, width, group):
        a, b = Vector(base), Vector(tip)
        axis = b - a
        side = axis.cross(Vector((0, 0, 1)))
        if side.length < .0001:
            side = Vector((1, 0, 0))
        side.normalize()
        vv, uv, ff = [], [], []
        curl = rng.uniform(-.035, .035)
        for j in range(7):
            t = j / 6
            middle = a + axis * t + Vector((0, 0, .024 * math.sin(t * math.pi)))
            middle += side * (curl * t*t)
            span = width * math.sin(t * math.pi) ** .7 * (.44 + .09 * math.sin(t*11))
            for k, s in enumerate((-1, 0, 1)):
                p = middle + side * span * s
                p.z += (.006 * math.sin(t*22 + s) - .012 * math.sin(t*math.pi)) * abs(s)
                vv.append(p);uv.append((k/2, t))
            if j:
                q = (j - 1)*3
                ff.extend([(q, q+3, q+4, q+1), (q+1, q+4, q+5, q+2)])
        ob = mesh(name, vv, ff, 'Leaf', uv, group)
        for polygon in ob.data.polygons:
            polygon.use_smooth = True
        # Opaque folded leaves remain visible from either side without masked foliage.
        solid = ob.modifiers.new('Leaf thickness', 'SOLIDIFY')
        solid.thickness = .002
        return ob

    # Reuse the actual finished FarmCompound01 woven basket mesh datablocks.
    # Its first basket collection has placed transforms but local-origin vertex data.
    empty = begin('MK01_BasketEmpty')
    basket_path = buildings / 'FarmCompound01/FarmCompound01.blend'
    with bpy.data.libraries.load(str(basket_path), link=False) as (available, loaded):
        if 'FC01_Baskets' not in available.collections:
            raise RuntimeError('FarmCompound01 source is missing FC01_Baskets')
        loaded.collections = ['FC01_Baskets']
    source_collection = loaded.collections[0]
    for ob in list(source_collection.all_objects):
        if ob.type != 'MESH':
            continue
        for col in list(ob.users_collection):
            col.objects.unlink(ob)
        src.objects.link(ob)
        ob.matrix_world.identity()
        ob.name = 'Market reused ' + ob.name
        ob['reused_from'] = 'FarmCompound01.blend / FC01_Baskets'
        for slot in ob.material_slots:
            if slot.material:
                family = slot.material.name.split('_', 1)[-1].split('.')[0]
                if family in mats:
                    slot.material = mats[family]
        colors = ob.data.color_attributes.get('Color')
        if not colors:
            colors = ob.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
            for value in colors.data:
                value.color = (1, 1, 1, 1)
        ob.data.color_attributes.active_color = colors
        groups[empty].append(ob)
    bpy.data.collections.remove(source_collection)

    produce = begin('MK01_BasketProduce')
    for original in modules[empty]:
        ob = original.copy()
        ob.data = original.data.copy()
        src.objects.link(ob)
        ob.name = original.name + ' broad produce basket'
        for v in ob.data.vertices:
            v.co.x *= 1.35
            v.co.y *= 1.35
            v.co.z *= .78
        groups[produce].append(ob)
    # Three leafy heads and three pale roots give only two produce silhouettes.
    for j, (x, y, z, radius) in enumerate([(-.13, .085, .275, .092),
                                           (.047, .12, .30, .11), (-.10, -.11, .29, .087)]):
        turned('Market rounded green vegetable', (x, y, z),
               [(0, .035), (.025, radius * .8), (.09, radius),
                (.145, radius * .68), (.16, .022)], 'Leaf', produce, n=16)
        for i in range(7):
            a = i * math.tau / 7 + j * .7 + rng.uniform(-.21, .21)
            leaf('Market folded outer vegetable leaf', (x, y, z + rng.uniform(.015, .045)),
                 (x + radius * rng.uniform(.8, 1.24) * math.cos(a),
                  y + radius * rng.uniform(.75, 1.2) * math.sin(a), z + rng.uniform(.10, .18)),
                 radius * rng.uniform(.67, 1.17), produce)
    for i in range(3):
        x, y = [.038, .145, .082][i], [-.15, -.055, -.004][i]
        size = [.83, .72, .91][i]
        ob = turned('Market ivory tapering root', (0, 0, 0),
                    [(z * size, r * size) for z, r in
                     [(0, .002), (.05, .010), (.14, .028), (.23, .032), (.27, .020)]],
                    'Root', produce, n=12)
        direction = Vector([(-.31, .36, .16), (.19, .28, .27), (-.28, .15, .32)][i]).normalized()
        quat = Vector((0, 0, 1)).rotation_difference(direction)
        for v in ob.data.vertices:
            v.co = quat @ v.co + Vector((x, y, .35))
        top = quat @ Vector((0, 0, .27 * size)) + Vector((x, y, .35))
        for k in range(3):
            tip = top + Vector((.04 * (k - 1), .08 + k * .025, .055 - .035 * k))
            leaf('Market root green tops', top, tip, .035, produce)

    pottery = begin('MK01_Pottery')
    for x, y, scale in [(-.17, 0, 1), (.17, .02, .73)]:
        profile = [(0, .10), (.025, .13), (.11, .175), (.25, .17),
                   (.34, .11), (.385, .083), (.397, .095), (.410, .095),
                   (.410, .072), (.378, .067), (.30, .096), (.12, .14), (.04, .083)]
        turned('Market open earthenware jar', (x, y, 0),
               [(z * scale, r * scale) for z, r in profile], 'Pottery', pottery)
    tall = begin('MK01_PotteryTall')
    turned('Market tall storage jar', (0, 0, 0),
           [(0, .13), (.05, .17), (.23, .23), (.43, .215), (.54, .12),
            (.58, .115), (.60, .13), (.62, .13), (.62, .104), (.56, .095),
            (.42, .181), (.12, .173), (.05, .105)], 'Pottery', tall)
    ring('Market tall jar hemp neck', (0, 0, .566), (.121, .121), tall, thickness=.011)

    crate = begin('MK01_Crate')
    for y in (-.22, .22):
        beam('Market crate bottom runner', (-.34, y, .035), (.34, y, .035),
             .065, .065, group=crate, rough=.003)
    for i in range(5):
        y = -.23 + i * .115
        beam('Market crate worn base slat', (-.35, y, .091), (.35, y, .091),
             .11, .042, group=crate, rough=.002)
    for x in (-.323, .323):
        for y in (-.257, .257):
            beam('Market crate upright corner', (x, y, .10), (x, y, .455),
                 .047, .047, group=crate, rough=.001)
    for z in (.16, .295, .43):
        for y in (-.279, .279):
            beam('Market crate long slat', (-.35, y, z), (.35, y, z),
                 .031, .105, group=crate, rough=.002)
        for x in (-.35, .35):
            beam('Market crate end slat', (x, -.274, z), (x, .274, z),
                 .031, .105, group=crate, rough=.002)

    sacks = begin('MK01_Sacks')
    for index, (x, y, scale) in enumerate([(-.16, .025, 1), (.20, -.025, .75)]):
        outline = [(0, .12), (.018, .175), (.065, .205), (.15, .219),
                   (.24, .204), (.31, .176), (.37, .127), (.42, .075),
                   (.452, .043), (.476, .047), (.50, .070), (.53, .060)]
        vv, uv, ff = [], [], []
        n, levels = 40, 44
        def sack_surface(z, angle):
            for k in range(len(outline)-1):
                if outline[k][0] <= z <= outline[k+1][0]:
                    f = (z-outline[k][0])/(outline[k+1][0]-outline[k][0])
                    # Cubic radius interpolation gives soft packed grain bulk.
                    r0 = outline[max(0, k-1)][1];r1 = outline[k][1]
                    r2 = outline[k+1][1];r3 = outline[min(len(outline)-1, k+2)][1]
                    r = .5*(2*r1+(-r0+r2)*f+(2*r0-5*r1+4*r2-r3)*f*f
                            +(-r0+3*r1-3*r2+r3)*f*f*f)
                    break
            t = z/.53
            phase = angle + index*.8
            shoulder = math.exp(-((z-.39)/.095)**2)
            opening = max(0, (z-.467)/.063)
            # Unequal broad lobes and slanting gathered creases, strongest at the neck.
            r *= 1 + .074*math.sin(2*phase+.6) + .040*math.sin(3*phase-z*5)
            r += (.0025+.009*shoulder+.011*opening)*math.sin(9*phase+z*4)
            r += .0035*math.sin(15*phase-z*9)*shoulder
            zz = z + opening*(.012*math.sin(5*phase)+.007*math.sin(9*phase))
            zz += .006*math.sin(phase*3+z*7)*math.sin(math.pi*t)
            dx = -.037*t*t + .017*math.sin(t*math.pi)
            dy = .026*t*t
            return Vector((x+(dx+r*math.cos(angle))*scale,
                           y+(dy+r*.79*math.sin(angle))*scale, max(.003, zz)*scale))
        for j in range(levels+1):
            z = .53*j/levels
            for i in range(n):
                vv.append(sack_surface(z, math.tau*i/n));uv.append((i/n*1.8, z*3))
                if j:
                    ff.append(((j-1)*n+i, (j-1)*n+(i+1)%n, j*n+(i+1)%n, j*n+i))
        ff.append(tuple(reversed(range(n))))
        # Visible cloth folds turn inward at the ragged mouth, rather than a flat cap.
        inner_start = len(vv)
        for i in range(n):
            p = sack_surface(.53, math.tau*i/n)
            neck = sack_surface(.47, math.tau*i/n)
            vv.append(p.lerp(neck, .82));uv.append((i/n*1.8, 1.6))
            ff.append((levels*n+i, levels*n+(i+1)%n,
                       inner_start+(i+1)%n, inner_start+i))
        ff.append(tuple(range(inner_start, inner_start+n)))
        ob = mesh('Market slumped gathered grain sack', vv, ff, 'Cloth', uv, sacks)
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices) == 4
        for z in (.449, .461):
            points = [sack_surface(z, math.tau*i/40) for i in range(41)]
            tube('Market sack tight hemp collar', points, .007*scale, 'Rope', sacks, 6)
        neck = sack_surface(.453, -math.pi/2)
        tube('Market sack uneven loose knot', [neck, neck+Vector((.029,-.021,-.013))*scale,
                                              neck+Vector((-.024,-.026,-.004))*scale,
                                              neck+Vector((.010,-.018,-.030))*scale,
                                              neck+Vector((-.035,-.028,-.092))*scale],
             .006*scale, 'Rope', sacks, 5)
        # One hem along the sack's side adds a readable cloth construction cue.
        seam = [sack_surface(.027+j*.019, -1.97) for j in range(21)]
        tube('Market sack sewn side seam', seam, .0028*scale, 'Cloth', sacks, 5)

    hanging = begin('MK01_HangingGoods')
    beam('Market hanging goods support rail', (-.5, 0, 0), (.5, 0, 0),
         .048, .053, group=hanging, rough=.003)
    for i, x in enumerate((-.35, -.09, .16)):
        length = [.31, .265, .34][i]
        drop = [.145, .205, .12][i]
        lean = [-.042, .03, -.021][i]
        yaw = [-.22, .34, -.45][i]
        def fish_point(xx, yy, t):
            return Vector((x+xx*math.cos(yaw)-yy*math.sin(yaw)+lean*t,
                           xx*math.sin(yaw)+yy*math.cos(yaw)+.013*math.sin(t*5+i),
                           -drop-t*length))
        neck = fish_point(0, 0, 0)
        tube('Market fish hanging cord', [(x, 0, -.025), (x+.008, -.008, -.075), neck],
             .005, 'Rope', hanging, 5)
        verts, uv, faces = [], [], []
        profile = [(0,.009),(.12,.018),(.27,.037),(.47,.049),(.64,.047),
                   (.79,.035),(.91,.024),(1,.007)]
        for j,(t,width) in enumerate(profile):
            for k in range(12):
                a = k*math.tau/12
                verts.append(fish_point(width*math.cos(a), width*.38*math.sin(a), t))
                uv.append((k/12,t))
                if j:
                    faces.append(((j-1)*12+k,(j-1)*12+(k+1)%12,j*12+(k+1)%12,j*12+k))
        faces += [tuple(reversed(range(12))),tuple(range(84,96))]
        ob = mesh('Market curved dried fish body',verts,faces,'Fish',uv,hanging)
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices)==4
        tail = [fish_point(xx,0,t) for xx,t in [(-.009,.01),(-.037,-.20),(0,-.13),(.035,-.19),(.009,.01)]]
        ob = mesh('Market forked dried fish tail',tail,[(0,1,2),(0,2,4),(2,3,4)],'Fish',group=hanging)
        mod=ob.modifiers.new('Thin dried tail','SOLIDIFY');mod.thickness=.003
        tube('Market dried fish gill crease',[fish_point(-.026,-.012,.76),
                                             fish_point(0,-.019,.79),
                                             fish_point(.026,-.012,.76)],.002,'Ink',hanging,4)
        # Small dorsal edge and split tail break the repeated paddle silhouette.
        fin=[fish_point(xx,0,t) for xx,t in [(-.032,.27),(-.063,.43),(-.047,.61),(-.039,.69)]]
        mesh('Market dry fish folded dorsal fin',fin,[(0,1,2,3)],'Fish',group=hanging)
    tube('Market herb hanging cord', [(.39, 0, -.02), (.37, -.01, -.15)],
         .005, 'Rope', hanging, 5)
    for i in range(9):
        a = i * 2.399 + .3
        stem = Vector((.37, -.01, -.14))
        tip = Vector((.37 + rng.uniform(.026,.081)*math.cos(a),
                      rng.uniform(.025,.062)*math.sin(a), rng.uniform(-.34,-.46)))
        mid = stem.lerp(tip,.56)+Vector((.014*math.sin(a),-.012,0))
        tube('Market drooping herb stem', [stem, mid, tip], .0025, 'Leaf', hanging, 4)
        for j in range(3):
            base=stem.lerp(tip,.36+j*.17)
            end=base+Vector((.036*math.cos(a+j),.026*math.sin(a+j),-.075+j*.010))
            leaf('Market irregular dried herb leaf',base,end,rng.uniform(.025,.047),hanging)

    cloth = begin('MK01_ClothBundle')
    for i, (z, width, depth) in enumerate([(.07, .56, .35), (.175, .51, .33), (.265, .48, .31)]):
        # Broad softened folds remain distinct even in a small market overview.
        verts, faces, uv = [], [], []
        for j, (zz, ratio) in enumerate([(-.045, .92), (-.027, 1), (.027, 1), (.045, .92)]):
            for k in range(16):
                a = k * math.tau / 16
                c, s = math.cos(a), math.sin(a)
                verts.append((width * .5 * ratio * math.copysign(abs(c) ** .30, c),
                              depth * .5 * ratio * math.copysign(abs(s) ** .30, s),
                              z + zz + .004 * math.sin(k * 2 + i)))
                uv.append((k / 16, j / 3))
                if j:
                    faces.append(((j - 1) * 16 + k, (j - 1) * 16 + (k + 1) % 16,
                                  j * 16 + (k + 1) % 16, j * 16 + k))
        faces += [tuple(reversed(range(16))), tuple(range(48, 64))]
        mesh('Market folded cloth bale', verts, faces, 'Cloth', uv, cloth)
    for x in (-.14, .14):
        tube('Market cloth bundle hemp strap', [(x, -.166, .30), (x, -.181, .09),
                                               (x, -.16, .022), (x, .16, .022),
                                               (x, .181, .09), (x, .166, .30),
                                               (x, -.166, .30)], .008, 'Rope', cloth, 6)
    return modules
