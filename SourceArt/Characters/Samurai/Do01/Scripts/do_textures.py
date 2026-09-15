"""Dō01 2K atlas, compatible with Kabuto01's linear-color NumPy API.

make_atlas(surfaces=None, detail_sheet=None) returns float32 BaseColor, OpenGL tangent Normal and
ORM RGBA arrays, each (2048, 2048, 4). Surface inputs are the same decoded
LINEAR RGB 512x512 swatches keyed 0 lacquer / 2 brass / 3 cord / 4 leather.
detail_sheet is the complete generated Do01_MaterialSources sheet, decoded to
LINEAR RGB with the first array row at the image bottom, as in Blender pixels.
There is no Blender dependency and no image loading here.

4x4 cells, 512px each; use (.025 + .95*UV) within the selected cell:
  0..7  Kabuto materials; tile 3 uses the new braid when detail_sheet is supplied.
  8, 9, 13, 14 one complete generated lamella each, left to right in the sheet.
  10   upper-front lacquer grain with a restrained gold border, no painted pins.
  11   generated floral engraved brass, reserved for fitting faces.
  12   quilted muted cloth lining.
  15   unchanged Kabuto duplicate padding.

Each plate targets one roughly 20mm-wide strip, not an entire torso row. Its
two cords sit near U=.34/.64, with endpoints at V=.90/.65 and V=.45/.20 (V=1 up).
Thickness and row overlap remain geometry. Image-derived relief and ORM are
restrained artist estimates, not measured PBR or a mesh/sculpt bake.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Kabuto01/Scripts'))
import kabuto_textures as kabuto

SIZE, TILE = kabuto.SIZE, kabuto.TILE


def _tile(array, index):
    return array[(index // 4) * TILE:(index // 4 + 1) * TILE,
                 (index % 4) * TILE:(index % 4 + 1) * TILE]


def _fields(seed, u, v):
    rng = np.random.default_rng(seed)
    broad = kabuto._noise(rng, 4, 5, u, v)
    grain = kabuto._noise(rng, 73, 101, u, v)
    return broad, grain


def _material(base, orm, index):
    color = _tile(base, index)[..., :3].copy()
    channels = _tile(orm, index)
    return color, channels[..., 0].copy(), channels[..., 1].copy(), channels[..., 2].copy()


def _write(base, normal, orm, index, color, height, ao, rough, metal):
    # Heights are texel-relative relief. Material color is never treated as
    # sculpted geometry; the normal field comes from the authored detail.
    gy, gx = np.gradient(height)
    vector = np.stack((-gx, -gy, np.ones_like(gx)), axis=2)
    vector /= np.linalg.norm(vector, axis=2, keepdims=True)
    gutter = np.clip(np.arange(TILE), 13, TILE - 14)
    def extend(field):
        return field[gutter[:, None], gutter[None, :]]
    _tile(base, index)[..., :3] = np.clip(extend(color), 0, 1)
    _tile(normal, index)[..., :3] = extend(vector) * .5 + .5
    target = _tile(orm, index)
    target[..., 0] = np.clip(extend(ao), 0, 1)
    target[..., 1] = np.clip(extend(rough), .08, .98)
    target[..., 2] = np.clip(extend(metal), 0, 1)


def _lamella(base, normal, orm, index, u, v):
    color, ao, rough, metal = _material(base, orm, 0)
    broad, grain = _fields(118000 + index, u, v)
    # Keep variants close in value; broad panels should read as maintained
    # lacquer rather than high-contrast camouflage or an all-over scratch map.
    color *= (1 + broad * .045)[..., None]
    rough = np.clip(rough + broad * .025, .32, .64)
    height = grain * .045
    distance = np.minimum.reduce((u, 1 - u, v * .65))
    wear = (1 - kabuto._smooth(.0015, .012, distance))
    wear *= kabuto._smooth(-.18, .50, broad + grain * .34) * .44
    color = kabuto._mix(color, (.055, .063, .065), wear)
    metal = np.maximum(metal, wear * .85)
    rough = rough * (1 - wear) + .42 * wear
    height -= wear * .20
    # The top is mostly hidden by the preceding physical row. Fasteners remain
    # visible in its upper third; the rest of each strip stays quiet.
    ao *= 1 - (1 - kabuto._smooth(.0, .09, 1 - v)) * .10
    cord_color = _tile(base, 3)[..., :3]
    for pair in (.27, .73):
        for center in (pair - .055, pair + .055):
            for level in (.625, .865):
                radius = np.sqrt(((u - center) / .042) ** 2 + ((v - level) / .028) ** 2)
                lip = (1 - kabuto._smooth(.96, 1.14, radius)) * kabuto._smooth(.77, .93, radius)
                hole = 1 - kabuto._smooth(.74, .95, radius)
                contact = 1 - kabuto._smooth(.92, 1.40, radius)
                color = kabuto._mix(color, (.047, .042, .030), lip * .55)
                color = kabuto._mix(color, (.0025, .0022, .0020), hole)
                height += lip * .30 - hole * 2.2
                rough = rough * (1 - hole) + .82 * hole
                metal *= 1 - hole
                ao *= 1 - contact * .35
            x = (u - center) / .026
            strap = 1 - kabuto._smooth(.84, 1.07, np.abs(x))
            strap *= kabuto._smooth(.620, .646, v) * (1 - kabuto._smooth(.844, .870, v))
            rounded = np.sqrt(np.clip(1 - x * x, 0, 1))
            braid, fibers = kabuto._braid((u - center) / .052, (v - .625) / .24, 2, 25)
            contact = (1 - kabuto._smooth(.96, 1.55, np.abs(x)))
            contact *= kabuto._smooth(.62, .65, v) * (1 - kabuto._smooth(.84, .87, v))
            ao *= 1 - contact * .17
            cord = cord_color * (.87 + rounded * .13 + (braid - .5) * .12)[..., None]
            color = kabuto._mix(color, cord, strap)
            height = height * (1 - strap) + (rounded * 5.0 + braid * .75 + fibers * .12) * strap
            rough = rough * (1 - strap) + (.87 - braid * .018) * strap
            metal *= 1 - strap
            ao = ao * (1 - strap) + (.94 + .06 * braid) * strap
    _write(base, normal, orm, index, color, height, ao, rough, metal)


def _sample(image, u, v):
    """Bilinear sampling of a bottom-up crop of any resolution."""
    h, w = image.shape[:2]
    x, y = np.clip(u, 0, 1) * (w - 1), np.clip(v, 0, 1) * (h - 1)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    tx, ty = (x - x0)[..., None], (y - y0)[..., None]
    return ((image[y0, x0] * (1 - tx) + image[y0, x1] * tx) * (1 - ty)
            + (image[y1, x0] * (1 - tx) + image[y1, x1] * tx) * ty).astype(np.float32)


def _palette(sample, target, region=None):
    pixels = sample.reshape(-1, 3) if region is None else sample[region > .7]
    if len(pixels) == 0:
        pixels = sample.reshape(-1, 3)
    median = np.maximum(np.median(pixels, axis=0), 1e-5)
    # Retain woven/engraved contrast while removing the sheet's broad lightness.
    ratio = np.maximum(sample / median, .01)
    ratio = ratio * 1.125 / (1 + ratio / 8)
    return ratio ** .92 * np.asarray(target, np.float32)


def _detail(sample):
    lum = sample @ np.array((.2126, .7152, .0722), np.float32)
    field = np.log1p(lum / max(float(np.median(lum)), .002))
    return np.clip(field - kabuto._blur(field, 5), -.32, .32)


def _masks(sample):
    r, g, b = np.moveaxis(sample, -1, 0)
    cord = kabuto._smooth(2.5, 4.0, r / (g + .0001))
    cord *= kabuto._smooth(2.5, 4.5, r / (b + .0001))
    gold = kabuto._smooth(1.15, 1.7, r / (g + .0001))
    gold *= kabuto._smooth(1.4, 2.5, g / (b + .0001)) * (1 - cord)
    gold *= kabuto._smooth(.006, .035, r)
    return cord, gold


def _sheet_lamella(base, normal, orm, index, sample, u, v):
    cord, gold = _masks(sample)
    lacquer = np.clip(1 - cord - gold, 0, 1)
    color = _palette(sample, (.008, .010, .012), lacquer)
    color = kabuto._mix(color, _palette(sample, (.080, .010, .007), cord), cord)
    color = kabuto._mix(color, _palette(sample, (.30, .18, .065), gold), gold)
    # Only localized high-frequency texture contributes to relief. Broad source
    # illumination stays out of the normal map; holes are limited to lace ends.
    detail = _detail(sample)
    holes = np.zeros_like(u)
    for x in (.34, .64):
        for y in (.90, .65, .45, .20):
            radius = ((u - x) / .105) ** 2 + ((v - y) / .040) ** 2
            holes = np.maximum(holes, 1 - kabuto._smooth(.65, 1.3, radius))
    lum = sample @ np.array((.2126, .7152, .0722), np.float32)
    holes *= (1 - kabuto._smooth(.002, .012, lum)) * (1 - cord)
    raised = kabuto._blur(cord, 3)
    height = detail * .30 + raised * 2.5 + detail * cord * .55 - holes * 1.2
    rough = .47 + np.clip(-detail * .10, -.04, .04)
    rough = rough * (1 - cord) + (.86 - detail * .035) * cord
    rough = rough * (1 - gold) + (.48 - detail * .05) * gold
    contact = np.clip(kabuto._blur(cord, 6) - cord, 0, 1)
    ao = 1 - holes * .28 - contact * .17
    _write(base, normal, orm, index, color, height, ao, rough, gold * .94)


def _upper_panel(base, normal, orm, u, v, sample=None):
    if sample is None:
        color, ao, rough, metal = _material(base, orm, 0)
        _, grain = _fields(118010, u, v)
        height = grain * .05
    else:
        _, gold = _masks(sample)
        # Keep only clear brass chips conductive. Warm specks in the generated
        # lacquer grain should not turn the whole finish into exposed metal.
        gold *= kabuto._smooth(.22, .65, gold)
        color = _palette(sample, (.0065, .008, .009), 1 - gold)
        color = kabuto._mix(color, _palette(sample, (.22, .14, .055), gold), gold * .6)
        detail = _detail(sample)
        broad, grain = _fields(118010, u, v)
        # A varied satin lacquer avoids the previous broad sheet-like white
        # reflection, retaining subtle polish differences and fine worn grain.
        rough = .565 + broad * .055 + grain * .014 - detail * .08
        rough = rough * (1 - gold) + (.49 - detail * .04) * gold
        height, ao, metal = detail * .26, np.ones_like(u), gold * .90
    distance = np.minimum.reduce((u, 1 - u, v, 1 - v))
    border = (1 - kabuto._smooth(.018, .023, distance)) * kabuto._smooth(.010, .014, distance)
    color = kabuto._mix(color, _tile(base, 2)[..., :3] * .76, border)
    height += border * .45
    rough = rough * (1 - border) + .49 * border
    metal = metal * (1 - border) + .87 * border
    _write(base, normal, orm, 10, color, height, ao, rough, metal)


def _fitting(base, normal, orm, u, v, sample=None):
    if sample is None:
        color, ao, rough, metal = _material(base, orm, 2)
        height = np.zeros_like(u)
    else:
        color = _palette(sample, (.32, .19, .070))
        detail = _detail(sample)
        # Dark, narrow engraved strokes recess slightly; uneven lighting does not.
        recess = kabuto._smooth(.035, .20, -detail)
        height = detail * .45 - recess * .45
        ao, rough, metal = 1 - recess * .16, .46 + recess * .10, np.full_like(u, .94)
    _write(base, normal, orm, 11, color, height, ao, rough, metal)


def _sheet_cord(base, normal, orm, sample, u, v):
    # The complete quadrant is one macro weave. Repeat six times along long
    # bindings, with a narrow crossfade at joins to avoid a hard texture seam.
    grid_v, grid_u = np.mgrid[:TILE, :TILE].astype(np.float32) / (TILE - 1)
    crop = _sample(sample, grid_u, grid_v)
    woven = kabuto._sample_surface(crop, u, v, repeat_v=6)
    color = _palette(woven, (.080, .010, .007))
    detail = _detail(woven)
    _write(base, normal, orm, 3, color, detail * 1.0,
           1 - np.maximum(-detail, 0) * .12, .86 - detail * .035, np.zeros_like(u))


def _lining(base, normal, orm, u, v):
    broad, grain = _fields(118012, u, v)
    color = _tile(base, 4)[..., :3].copy() * np.array((.73, .84, 1.00), np.float32)
    color *= (1 + broad * .035)[..., None]
    cell_u, cell_v = np.mod(u * 6, 1), np.mod(v * 4, 1)
    distance = np.minimum(np.minimum(cell_u, 1 - cell_u) / 6,
                          np.minimum(cell_v, 1 - cell_v) / 4)
    seam = 1 - kabuto._smooth(.0015, .0065, distance)
    puff = kabuto._smooth(.002, .034, distance)
    weave = np.sin(u * np.pi * 320) * np.sin(v * np.pi * 320)
    color *= (1 - seam * .25 + weave * .025)[..., None]
    height = puff * 1.2 - seam * .35 + weave * .12 + grain * .035
    ao = 1 - seam * .26
    rough = .89 + broad * .025 + seam * .025
    _write(base, normal, orm, 12, color, height, ao, rough, np.zeros_like(u))


def make_atlas(surfaces=None, detail_sheet=None):
    """Return compatible opaque 2K atlases without loading/saving any images."""
    base, normal, orm = kabuto.make_atlas(surfaces)
    yy, xx = np.mgrid[:TILE, :TILE].astype(np.float32)
    u = np.clip((xx / (TILE - 1) - .025) / .95, 0, 1)
    v = np.clip((yy / (TILE - 1) - .025) / .95, 0, 1)
    if detail_sheet is None:
        for index in (8, 9, 13, 14):
            _lamella(base, normal, orm, index, u, v)
        _upper_panel(base, normal, orm, u, v)
        _fitting(base, normal, orm, u, v)
    else:
        sheet = np.asarray(detail_sheet, dtype=np.float32)
        if sheet.ndim != 3 or sheet.shape[2] != 3 or min(sheet.shape[:2]) < 32:
            raise ValueError('detail_sheet must be a bottom-up linear RGB image, at least 32px')
        if not np.isfinite(sheet).all() or np.any(sheet < 0):
            raise ValueError('detail_sheet must contain finite non-negative linear RGB values')
        h, w = sheet.shape[0] // 2, sheet.shape[1] // 2
        _sheet_cord(base, normal, orm, sheet[:h, w:], u, v)
        plates = sheet[:h, :w]
        # Tight full-height crops remove the dark gaps between physical plates.
        spans = ((.005, .243), (.256, .495), (.506, .752), (.760, .997))
        for index, (left, right) in zip((8, 9, 13, 14), spans):
            crop = plates[round(h * .004):round(h * .996),
                          round(w * left):round(w * right)]
            _sheet_lamella(base, normal, orm, index, _sample(crop, u, v), u, v)
        _upper_panel(base, normal, orm, u, v, _sample(sheet[h:, :w], u, v))
        _fitting(base, normal, orm, u, v, _sample(sheet[h:, w:], u, v))
    _lining(base, normal, orm, u, v)
    return base, normal, orm
