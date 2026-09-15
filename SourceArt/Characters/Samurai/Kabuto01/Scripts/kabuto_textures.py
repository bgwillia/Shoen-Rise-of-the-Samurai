"""Kabuto01 atlas with analytic details and optional generated material swatches.

NumPy only, no Blender side effects. Optional surfaces maps material IDs
0/2/3/4 to caller-decoded LINEAR RGB 512x512 arrays (ImageGen source quadrants).
Their color texture is normalized to the authored material palette. Only fine
local contrast contributes to normal detail; source lighting is not geometry.

make_atlas() returns BaseColor, OpenGL tangent Normal and ORM float32 RGBA arrays
of shape (2048, 2048, 4). BaseColor is LINEAR: Blender encodes its sRGB PNG.
Normals are authored for the material's 0.65 strength. ORM is occlusion,
roughness, metallic. Occlusion describes procedural pores/strap contact only;
it is not mesh-baked ambient occlusion or a sculpt bake.

4x4 atlas, 512px cells, with IDs 8..15 repeating 0..7. Existing UV padding is
preserved: the useful domain is .025..975 inside each cell.
0 lacquer; 1 three paired lacing columns; 2 aged brass; 3 braided red cord;
4 leather; 5 bound lacquer side panel; 6 brass for modeled rosette; 7 padding.
Tile 1 repeats six times around a shikoro row: eighteen PAIRS, not 108 pairs.
"""
import numpy as np


SIZE = 2048
TILE = 512


def _smooth(low, high, value):
    t = np.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _noise(rng, cells_x, cells_y, u, v):
    """Periodic bicubic-smoothed value noise without a trigonometric pattern."""
    grid = rng.uniform(-1.0, 1.0, (cells_y, cells_x)).astype(np.float32)
    x, y = u * cells_x, v * cells_y
    ix, iy = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    tx, ty = x - ix, y - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = grid[iy % cells_y, ix % cells_x], grid[iy % cells_y, (ix + 1) % cells_x]
    c, d = grid[(iy + 1) % cells_y, ix % cells_x], grid[(iy + 1) % cells_y, (ix + 1) % cells_x]
    return ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty).astype(np.float32)


def _mix(color, target, mask):
    mask = np.clip(mask, 0.0, 1.0)[..., None]
    return color * (1.0 - mask) + np.asarray(target, dtype=np.float32) * mask


def _sample_surface(image, u, v, repeat_v=1):
    """Bilinear sampling; repeated cord ends crossfade over a narrow seam."""
    def sample(y):
        x = np.clip(u, 0, 1) * (TILE - 1)
        y = np.clip(y, 0, 1) * (TILE - 1)
        x0, y0 = x.astype(np.int32), y.astype(np.int32)
        x1, y1 = np.minimum(x0 + 1, TILE - 1), np.minimum(y0 + 1, TILE - 1)
        tx, ty = (x - x0)[..., None], (y - y0)[..., None]
        return ((image[y0, x0] * (1 - tx) + image[y0, x1] * tx) * (1 - ty)
                + (image[y1, x0] * (1 - tx) + image[y1, x1] * tx) * ty)
    phase = v if repeat_v == 1 else np.mod(v * repeat_v, 1)
    result = sample(phase)
    if repeat_v != 1:
        blend = .5 * (1 - _smooth(0, .045, np.minimum(phase, 1 - phase)))
        result = result * (1 - blend[..., None]) + sample(1 - phase) * blend[..., None]
    return result.astype(np.float32)


def _blur(field, radius=4):
    width = radius * 2 + 1
    padded = np.pad(field, radius, mode="reflect")
    integral = np.pad(padded, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    return (integral[width:, width:] - integral[:-width, width:]
            - integral[width:, :-width] + integral[:-width, :-width]) / (width * width)


def _swatch_material(sample, target_color):
    # Per-channel medians preserve the authored palette instead of carrying
    # baked swatch illumination or a pale source white balance into the atlas.
    median = np.maximum(np.median(sample.reshape(-1, 3), axis=0), 1e-6)
    ratio = np.clip(sample / median, .18, 3.8) ** .78
    color = ratio * target_color
    luminance = ratio @ np.array((.2126, .7152, .0722), dtype=np.float32)
    local = np.log1p(luminance)
    detail = np.clip(local - _blur(local), -.30, .30)
    roughness = np.clip(1 - luminance, -1, 1) * .026 - detail * .035
    return color.astype(np.float32), detail.astype(np.float32), roughness.astype(np.float32)


def _scratches(rng, u, v, count):
    """Sparse tapered, gently curved abrasions of varied length and direction."""
    result = np.zeros_like(u)
    for _ in range(count):
        cx, cy = rng.uniform(.025, .975, 2)
        angle = rng.uniform(-np.pi, np.pi)
        length = rng.uniform(.025, .16)
        width = rng.uniform(.00065, .00165)
        dx, dy = u - cx, v - cy
        along = dx * np.cos(angle) + dy * np.sin(angle)
        across = -dx * np.sin(angle) + dy * np.cos(angle)
        across -= rng.uniform(-.20, .20) * along * along / length
        taper = 1.0 - _smooth(length * .25, length * .5, np.abs(along))
        line = (1.0 - _smooth(width * .25, width, np.abs(across))) * taper
        result = np.maximum(result, line * rng.uniform(.25, .9))
    return result


def _braid(u, v, around=18.0, along=72.0):
    """Alternating diagonal bundles, with fine parallel silk fibers inside."""
    forward = u * around + v * along
    backward = u * around - v * along
    fa, fb = np.mod(forward, 1.0), np.mod(backward, 1.0)
    ra = 1.0 - _smooth(.22, .50, np.abs(fa - .5))
    rb = 1.0 - _smooth(.22, .50, np.abs(fb - .5))
    over = np.mod(np.floor(forward) + np.floor(backward), 2.0)
    bundles = np.maximum(ra * (.70 + .30 * over), rb * (1.0 - .30 * over))
    fiber_a = 1.0 - _smooth(.08, .43, np.abs(np.mod(forward * 5.0, 1.0) - .5))
    fiber_b = 1.0 - _smooth(.08, .43, np.abs(np.mod(backward * 5.0, 1.0) - .5))
    return bundles, (fiber_a * ra + fiber_b * rb) * .5


def _surface(kind, seed, u, v):
    rng = np.random.default_rng(seed)
    broad = _noise(rng, 5, 4, u, v)
    medium = _noise(rng, 19, 17, u, v)
    grain = _noise(rng, 83, 97, u, v)
    micro = rng.normal(0, 1, u.shape).astype(np.float32)
    h = grain * .07 + micro * .015
    ao = np.ones_like(u)

    if kind in (0, 1, 5):
        # A clear lacquer coat is dielectric. Exposed abrasion alone is metal.
        rgb = np.zeros((*u.shape, 3), np.float32) + (.0075, .010, .012)
        rgb *= (1 + broad * .12 + medium * .035)[..., None]
        rough = .43 + broad * .09 + medium * .025 + grain * .016
        metal = np.zeros_like(u)
        h = grain * .12 + micro * .014
        scratches = _scratches(rng, u, v, 62 if kind == 0 else 29)
        # Broken edge wear remains narrow and follows a slightly irregular edge.
        waviness = .003 * _noise(rng, 11, 2, u, v)
        distance = np.minimum(v, 1 - v) + waviness
        chips = (1 - _smooth(.002, .011, distance)) * _smooth(-.10, .45, medium + grain * .35)
        # A few small, irregular nicks accompany the long fine scratches.
        # Their clustered distribution keeps the broad panels maintained.
        nicks = _smooth(.68, .92, grain) * _smooth(.10, .52, medium)
        exposure = np.maximum.reduce((scratches * .58, chips * .78, nicks * .68))
        rgb = _mix(rgb, (.118, .126, .123), exposure)
        metal = np.maximum(metal, exposure * .88)
        rough = rough * (1 - exposure) + (.44 + grain * .03) * exposure
        h -= scratches * .18 + chips * .13 + nicks * .22
        # Barely visible handling patches; no uniform grime/noise blanket.
        rub = _smooth(.20, .55, broad) * _smooth(-.2, .35, medium)
        rough -= rub * .035
        return rgb, h, ao, rough, metal, (broad, medium, grain)

    if kind in (2, 6):
        rgb = np.zeros((*u.shape, 3), np.float32) + (.32, .195, .074)
        rgb *= (1 + broad * .020 + medium * .025 + grain * .012)[..., None]
        # Aging is irregular at a fine scale. Broad masks used at high
        # contrast turn a brass sheet into camouflage under a large light.
        patina = _smooth(.16, .76, broad * .10 + medium * .35 + grain * .55) * .38
        rgb = _mix(rgb, (.090, .078, .046), patina)
        rough = .45 + patina * .13 + medium * .028 + grain * .018
        metal = .94 - patina * .20
        # Sparse microscopic pits, concentrated in the aged patches.
        pits = _smooth(.57, .88, grain + medium * .19) * (.26 + .45 * patina)
        rgb = _mix(rgb, (.052, .045, .030), pits * .35)
        h -= pits * .24
        ao -= pits * .15
        scratches = _scratches(rng, u, v, 46)
        rgb = _mix(rgb, (.46, .355, .188), scratches * .32)
        rough -= scratches * .055
        h -= scratches * .12
        # Smooth polishing patches produce broad metal reflections. The actual
        # modeled bevel supplies the crest/rivet rim; no painted flower/ring.
        polish = _smooth(.08, .55, -broad) * .30
        rgb = _mix(rgb, (.42, .325, .17), polish * .25)
        rough -= polish * .060
        return rgb, h, ao, rough, metal, (broad, medium, grain)

    if kind == 3:
        braid, fibers = _braid(u, v, 22, 96)
        rgb = np.zeros((*u.shape, 3), np.float32) + (.072, .009, .0045)
        rgb *= (1 + broad * .05 + (braid - .5) * .38 + grain * .022)[..., None]
        h = braid * 2.8 + fibers * .32 + micro * .008
        ao = .93 + .07 * braid
        rough = .86 + broad * .025 - braid * .018
        return rgb, h, ao, rough, np.zeros_like(u), (broad, medium, grain)

    rgb = np.zeros((*u.shape, 3), np.float32) + ((.043, .026, .014) if kind == 4 else (.047, .034, .022))
    rgb *= (1 + broad * .12 + medium * .035 + grain * .012)[..., None]
    pores = _smooth(.4, .78, grain + medium * .14)
    h = grain * .12 - pores * .15
    rough = .77 + broad * .045 + medium * .018
    ao -= pores * .06
    return rgb, h, ao, rough, np.zeros_like(u), (broad, medium, grain)


def make_atlas(surfaces=None):
    """Build padded 2K atlases; optional swatches are 512² linear RGB arrays."""
    yy, xx = np.mgrid[:TILE, :TILE].astype(np.float32)
    # Match the mesh's existing .025 + .95*UV contract. Border texels extend
    # the nearest useful texel, providing a real gutter at every tile edge.
    u = np.clip((xx / (TILE - 1) - .025) / .95, 0, 1)
    v = np.clip((yy / (TILE - 1) - .025) / .95, 0, 1)
    base = np.ones((SIZE, SIZE, 4), np.float32)
    normal = np.ones_like(base)
    orm = np.ones_like(base)
    swatches = {}
    for key, source in (surfaces or {}).items():
        if key not in (0, 2, 3, 4):
            raise ValueError("Surface IDs must be 0 (lacquer), 2 (brass), 3 (cord), or 4 (leather)")
        source = np.asarray(source, dtype=np.float32)
        if source.shape != (TILE, TILE, 3) or not np.isfinite(source).all() or (source < 0).any():
            raise ValueError("Each surface must be a finite nonnegative 512x512x3 linear RGB array")
        swatches[key] = _sample_surface(source, np.mod(u*3,1) if key==2 else u, v,
                                        repeat_v=7 if key==3 else 3 if key==2 else 1)
    cord_pattern = None
    if 3 in swatches:
        cord_pattern = _swatch_material(swatches[3], np.array((.069, .0085, .0043), np.float32))[0]

    for kind in range(8):
        rgb, height, ao, rough, metal, fields = _surface(kind, 73019 + kind * 773, u, v)
        broad, medium, grain = fields
        material_key = {1: 0, 5: 0, 6: 2, 7: 4}.get(kind, kind)
        if material_key in swatches:
            target = np.median(rgb.reshape(-1, 3), axis=0)
            swatch_color, detail, rough_detail = _swatch_material(swatches[material_key], target)
            influence=.45 if material_key==2 else .83
            rgb = rgb * (1-influence) + swatch_color * influence
            height = height * .40 + detail * (.15 if material_key == 2 else .32)
            rough += rough_detail

        if kind == 1:
            # Three pairs per texture repeat. The six repeats around one lame
            # make 18 readable pairs, with negative space between each pair.
            for pair_center in (1 / 6, 1 / 2, 5 / 6):
                for center in (pair_center - .043, pair_center + .043):
                    for row in (.25, .73):
                        radius = np.sqrt(((u - center) / .030) ** 2 + ((v - row) / .064) ** 2)
                        lip = (1 - _smooth(.93, 1.15, radius)) * _smooth(.69, .88, radius)
                        hole = 1 - _smooth(.71, .94, radius)
                        contact = 1 - _smooth(.93, 1.35, radius)
                        rgb = _mix(rgb, (.080, .075, .055), lip * .65)
                        rgb = _mix(rgb, (.0035, .003, .0025), hole)
                        height += lip * .20 - hole * .85
                        rough = rough * (1 - hole) + .78 * hole
                        metal = metal * (1 - hole) + lip * .55
                        ao *= 1 - contact * .28
                    x = (u - center) / .017
                    strap = (1 - _smooth(.82, 1.08, np.abs(x)))
                    strap *= _smooth(.241, .27, v) * (1 - _smooth(.714, .742, v))
                    rounded = np.sqrt(np.clip(1 - x * x, 0, 1))
                    braid, fibers = _braid((u - center) / .034, (v - .25) / .48, 2.5, 42)
                    contact = (1 - _smooth(1.02, 1.7, np.abs(x))) * _smooth(.24, .28, v) * (1 - _smooth(.71, .75, v))
                    ao *= 1 - contact * .13
                    cord_color = np.zeros_like(rgb) + (.069, .0085, .0043)
                    cord_color *= (.90 + rounded * .10 + (braid - .5) * .30 + broad * .025)[..., None]
                    if cord_pattern is not None:
                        cord_color = cord_color * .25 + cord_pattern * (.90 + rounded * .10)[..., None] * .75
                    rgb = _mix(rgb, cord_color, strap)
                    # Relief is smooth across the strap, with small diagonal
                    # braid ridges, and sinks into its two actual dark holes.
                    height = height * (1 - strap) + (rounded * .65 + braid * .85 + fibers * .12) * strap
                    rough = rough * (1 - strap) + (.87 - braid * .018) * strap
                    metal *= 1 - strap
                    ao = ao * (1 - strap) + (.92 + braid * .08) * strap

        elif kind == 5:
            # Bound leather/metal border on four edges. Knots and rosettes are
            # modeled by the builder, so there are no painted red rectangles.
            distance = np.minimum.reduce((u, 1 - u, v, 1 - v))
            binding = 1 - _smooth(.041, .050, distance)
            brass, _, _, brass_rough, brass_metal, _ = _surface(2, 33491, u, v)
            if 2 in swatches:
                source_brass, _, brass_rough_detail = _swatch_material(
                    swatches[2], np.median(brass.reshape(-1, 3), axis=0))
                brass = brass * .17 + source_brass * .83
                brass_rough += brass_rough_detail
            rgb = _mix(rgb, brass, binding)
            rough = rough * (1 - binding) + brass_rough * binding
            metal = metal * (1 - binding) + brass_metal * binding
            height += binding * .65
            seam = np.exp(-((distance - .050) / .0035) ** 2)
            ao *= 1 - seam * .15
            height -= seam * .18

        elif kind == 7:
            # Soft, rectangular quilt cushions with restrained recessed seams.
            cu, cv = np.mod(u * 8, 1), np.mod(v * 3, 1)
            du, dv = np.minimum(cu, 1 - cu) / 8, np.minimum(cv, 1 - cv) / 3
            distance = np.minimum(du, dv)
            seam = 1 - _smooth(.0015, .007, distance)
            puff = _smooth(.001, .024, distance)
            rgb *= (1 - seam * .27 + puff * .035)[..., None]
            height += puff * .70 - seam * .28
            ao *= 1 - seam * .24
            rough += seam * .045

        # Height is in texel-relative units; broad color/roughness variation
        # never becomes a lumpy normal field. Positive green means +tangent Y.
        gy, gx = np.gradient(height)
        vectors = np.stack((-gx, -gy, np.ones_like(gx)), axis=2)
        vectors /= np.linalg.norm(vectors, axis=2, keepdims=True)
        # Extend finished texels, including stochastic microdetail, into the
        # gutter. Evaluating clamped UVs alone would leave random border noise.
        sample = np.clip(np.arange(TILE), 13, TILE - 14)
        rgb = rgb[sample[:, None], sample[None, :]]
        vectors = vectors[sample[:, None], sample[None, :]]
        ao = ao[sample[:, None], sample[None, :]]
        rough = rough[sample[:, None], sample[None, :]]
        metal = metal[sample[:, None], sample[None, :]]
        for tile in (kind, kind + 8):
            region = (slice((tile // 4) * TILE, (tile // 4 + 1) * TILE),
                      slice((tile % 4) * TILE, (tile % 4 + 1) * TILE))
            base[region][..., :3] = np.clip(rgb, 0, 1)
            normal[region][..., :3] = vectors * .5 + .5
            orm[region][..., 0] = np.clip(ao, 0, 1)
            orm[region][..., 1] = np.clip(rough, .08, .98)
            orm[region][..., 2] = np.clip(metal, 0, 1)
    return base, normal, orm
