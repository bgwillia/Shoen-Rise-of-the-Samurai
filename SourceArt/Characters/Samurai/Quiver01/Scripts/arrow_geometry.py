"""Reusable Quiver01 arrow, metres, steel tip at Z=0 / split nock at Z=.92.

``build_arrow(g)`` needs only the collection in ``g.SOURCE``. The returned
single mesh is ready for linked bundle copies, rig weighting, or static export.
ArrowSurface is a CORNER/FLOAT_COLOR attribute: RGB albedo, A metalness.
The material intentionally does not use the Dō atlas or modify g.MATERIAL.
"""
import math

import bpy


WOOD = (.090, .036, .012, 0.0)
WOOD_LIGHT = (.15, .062, .025, 0.0)
RED = (.12, .008, .004, 0.0)
RED_LIGHT = (.18, .015, .008, 0.0)
CREAM = (.36, .27, .16, 0.0)
CREAM_LIGHT = (.43, .34, .22, 0.0)
FEATHER_BROWN = (.18, .12, .065, 0.0)
RACHIS = (.105, .041, .013, 0.0)
STEEL = (.38, .43, .46, 1.0)


def _scale(color, factor):
    return tuple(min(1., channel * factor) for channel in color[:3]) + (color[3],)


class _Geometry:
    """One indexed mesh; physically separated details retain their own topology."""

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.colors = []
        self.smooth = []

    def vertex(self, co):
        self.vertices.append(tuple(co))
        return len(self.vertices) - 1

    def face(self, indices, color, smooth=False):
        self.faces.append(tuple(indices))
        self.colors.append(color)
        self.smooth.append(smooth)

    def cylinder(self, stations, color, sides=12, phase=0., faceted=False):
        """Tapered Z cylinder from (z, radius) stations, with closed end caps."""
        rings = []
        for z, radius in stations:
            rings.append([self.vertex((radius * math.cos(phase + j * math.tau / sides),
                                       radius * math.sin(phase + j * math.tau / sides), z))
                          for j in range(sides)])
        for k in range(len(rings) - 1):
            for j in range(sides):
                # Restrained lengthwise grain follows the shaft's twelve sectors.
                tint = 1. + .09 * math.sin(j * 2.7) if color == WOOD else 1.
                self.face((rings[k][j], rings[k][(j + 1) % sides],
                           rings[k + 1][(j + 1) % sides], rings[k + 1][j]),
                          _scale(color, tint), not faceted)
        self.face(reversed(rings[0]), color)
        self.face(rings[-1], color)

    def line(self, points, radius, color, sides=5):
        """Small tube around a mostly vertical line, for the feather quill."""
        # Feather rachises run almost parallel to Z. This stable frame avoids
        # dependencies on the atlas helpers and preserves all attribute colors.
        rings = []
        for x, y, z in points:
            rings.append([self.vertex((x + radius * math.cos(j * math.tau / sides),
                                       y + radius * math.sin(j * math.tau / sides), z))
                          for j in range(sides)])
        for k in range(len(rings) - 1):
            for j in range(sides):
                self.face((rings[k][j], rings[k][(j + 1) % sides],
                           rings[k + 1][(j + 1) % sides], rings[k + 1][j]), color, True)
        self.face(reversed(rings[0]), color)
        self.face(rings[-1], color)


def _arrowhead(geo):
    """Closed leaf blade with a raised central ridge and a slender socket."""
    tip = geo.vertex((0., 0., 0.))
    rings = []
    for z, width, depth in ((.010, .0034, .0010), (.020, .0062, .00145),
                            (.027, .0045, .00135), (.035, .0025, .0011)):
        rings.append([geo.vertex((width, 0., z)), geo.vertex((0., depth, z)),
                      geo.vertex((-width, 0., z)), geo.vertex((0., -depth, z))])
    for j in range(4):
        geo.face((tip, rings[0][(j + 1) % 4], rings[0][j]), _scale(STEEL, 1. + .08 * (j % 2)))
    for lower, upper in zip(rings, rings[1:]):
        for j in range(4):
            geo.face((lower[j], lower[(j + 1) % 4], upper[(j + 1) % 4], upper[j]),
                     _scale(STEEL, 1. + .08 * (j % 2)))
    geo.face(rings[-1], STEEL)
    geo.cylinder(((.028, .00235), (.035, .00335), (.047, .00335)), STEEL, sides=10)


def _nock(geo):
    """Two rounded wooden ears and a genuine open slot, without a boolean."""
    radius, slot_halfwidth = .0032, .00080
    start = math.asin(slot_halfwidth / radius)
    for sign in (-1, 1):
        ring = []
        # Each prong is a clipped half-disc, bounded by a flat inner slot wall.
        for j in range(9):
            a = start + (math.pi - 2 * start) * j / 8
            ring.append((radius * math.cos(a), sign * radius * math.sin(a)))
        if sign < 0:
            ring.reverse()
        lower = [geo.vertex((x, y, .917)) for x, y in ring]
        upper = [geo.vertex((x * .96, y, .920)) for x, y in ring]
        for j in range(len(ring)):
            geo.face((lower[j], lower[(j + 1) % len(ring)],
                      upper[(j + 1) % len(ring)], upper[j]), WOOD_LIGHT, j != len(ring) - 1)
        geo.face(reversed(lower), WOOD)
        geo.face(upper, WOOD_LIGHT)
    # Dark wood floor below the slot makes the nock readable at moderate range.
    x = math.sqrt(radius * radius - slot_halfwidth * slot_halfwidth)
    floor = [geo.vertex(p) for p in ((-x, -.0008, .91702), (x, -.0008, .91702),
                                      (x, .0008, .91702), (-x, .0008, .91702))]
    geo.face(floor, RACHIS)


def _feather(geo, phase, vane_index):
    """Three closed, thin vane shells; broad patterned faces carry the detail."""
    c, s = math.cos(phase), math.sin(phase)
    # Irregular broad silhouette, rather than an expensive comb of tiny barbs.
    profile = ((0., .0036), (.055, .0060), (.16, .0113), (.29, .0147),
               (.43, .0155), (.61, .0151), (.76, .0137), (.90, .0097),
               (.975, .0058), (1., .0036))

    def outer_radius(t):
        for (a, ra), (b, rb) in zip(profile, profile[1:]):
            if t <= b:
                u = (t - a) / (b - a)
                return ra + (rb - ra) * u
        return profile[-1][1]

    count = 56
    transverse = (0., .48, 1.)
    surfaces = []
    for side in (-1., 1.):
        rows = []
        for k in range(count + 1):
            t = k / count
            row = []
            for u in transverse:
                radial = .00345 + (outer_radius(t) - .00345) * u
                # Barred colors and topology lean slightly toward the nock at
                # the outer edge. Endpoints remain exactly .710 and .885.
                z = .710 + .175 * t + .008 * math.sin(math.pi * t) * u
                # Maximum bulge is restrained; closed shell thickness .30 mm.
                thickness = side * .00015 + .00030 * math.sin(math.pi * u)
                row.append(geo.vertex((radial * c - thickness * s,
                                       radial * s + thickness * c, z)))
            rows.append(row)
        surfaces.append(rows)
        for k in range(count):
            t = (k + .5) / count
            stripe_phase = (k + vane_index) % 13
            base = FEATHER_BROWN if stripe_phase in (1, 2, 3, 4) else CREAM
            for j in range(len(transverse) - 1):
                indices = (rows[k][j], rows[k + 1][j], rows[k + 1][j + 1], rows[k][j + 1])
                if side < 0:
                    indices = tuple(reversed(indices))
                # Lighter perimeter and small segment variation suggest feather
                # fibers while keeping the primary silhouette quiet and clean.
                tint = .89 + .10 * math.sin(k * 2.1 + vane_index) + .07 * j
                if k in (0, count - 1):
                    base = CREAM_LIGHT
                geo.face(indices, _scale(base, tint))
    back, front = surfaces
    for k in range(count):
        geo.face((back[k][0], back[k + 1][0], front[k + 1][0], front[k][0]), RACHIS)
        geo.face((back[k][-1], front[k][-1], front[k + 1][-1], back[k + 1][-1]), CREAM)
    for k in (0, count):
        for j in range(len(transverse) - 1):
            indices = (back[k][j], front[k][j], front[k][j + 1], back[k][j + 1])
            geo.face(indices if k == 0 else tuple(reversed(indices)), CREAM)
    geo.line([(.00362 * c, .00362 * s, z) for z in (.708, .740, .800, .850, .887)],
             .00042, RACHIS)


def _material():
    material = bpy.data.materials.get('M_Arrow01') or bpy.data.materials.new('M_Arrow01')
    material.use_nodes = True
    material.diffuse_color = WOOD[:3] + (1.,)
    material.node_tree.nodes.clear()
    output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 40)
    principled = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (70, 40)
    principled.inputs['Roughness'].default_value = .55
    principled.inputs['Alpha'].default_value = 1.
    colors = material.node_tree.nodes.new('ShaderNodeVertexColor')
    colors.layer_name = 'ArrowSurface'
    colors.location = (-240, 40)
    material.node_tree.links.new(colors.outputs['Color'], principled.inputs['Base Color'])
    material.node_tree.links.new(colors.outputs['Alpha'], principled.inputs['Metallic'])
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    material['surface_contract'] = 'ArrowSurface RGB = linear albedo; alpha = metallic; opaque'
    return material


def build_arrow(g):
    """Return one Arrow_01 mesh linked to g.SOURCE, with all detail joined."""
    geo = _Geometry()
    _arrowhead(geo)
    geo.cylinder(((.030, .0032), (.320, .0032), (.600, .0032),
                  (.710, .0032), (.890, .0032), (.917, .0032)), WOOD)
    # Modest bindings: red collars and raised fine cord ridges at feather roots.
    for lo, hi in ((.047, .056), (.378, .382), (.681, .685),
                   (.704, .714), (.882, .894), (.905, .911)):
        geo.cylinder(((lo, .00335), (lo + .0008, .0037),
                      (hi - .0008, .0037), (hi, .00335)), RED)
    for z in (.7055, .7085, .7115, .8840, .8870, .8900, .907):
        geo.cylinder(((z - .00035, .0036), (z, .00394),
                      (z + .00035, .0036)), RED_LIGHT, sides=10)
    for vane in range(3):
        _feather(geo, vane * math.tau / 3, vane)
    _nock(geo)

    data = bpy.data.meshes.new('Arrow_01_Geometry')
    data.from_pydata(geo.vertices, [], geo.faces)
    data.update()
    ob = bpy.data.objects.new('Arrow_01', data)
    g.SOURCE.objects.link(ob)
    data.materials.append(_material())
    colors = data.color_attributes.new(name='ArrowSurface', type='FLOAT_COLOR', domain='CORNER')
    data.color_attributes.active_color_index = data.color_attributes.find('ArrowSurface')
    data.color_attributes.render_color_index = data.color_attributes.active_color_index
    uv = data.uv_layers.new(name='UV0_Arrow')
    for polygon, color, smooth in zip(data.polygons, geo.colors, geo.smooth):
        polygon.use_smooth = smooth
        for loop_index in polygon.loop_indices:
            colors.data[loop_index].color = color
            co = data.vertices[data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = ((math.atan2(co.y, co.x) / math.tau) % 1., co.z / .92)
    ob['asset'] = 'Arrow01'
    ob['length_m'] = .92
    ob['shaft_radius_m'] = .0032
    ob['fletching_vanes'] = 3
    ob['construction'] = 'Reusable joined arrow; tip Z0, split nock Z0.920; three thick feather vanes'
    return ob
