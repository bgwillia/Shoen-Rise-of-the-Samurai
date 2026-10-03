"""Tachi-specific opaque PBR finish derived from the preserved Dō atlases.

Tile layout follows do_geometry.uvcoord: 0 polished black lacquer, 1 red
pebbled samegawa, 2 aged brass, 3 red cord, 4 charcoal silk, 11 chased brass.
All palette constants are scene-linear. Normal maps are OpenGL tangent space;
their strength is baked into the pixels so the same PNGs work in Unreal.
"""
from pathlib import Path

import bpy
import numpy as np


SIZE = 2048
CELL = SIZE // 4


def _tile(pixels, index):
    return pixels[(index // 4) * CELL:(index // 4 + 1) * CELL,
                  (index % 4) * CELL:(index % 4 + 1) * CELL]


def _read(path, color=False):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    try:
        if tuple(image.size) != (SIZE, SIZE):
            raise ValueError(f'Tachi finish requires a {SIZE}px atlas: {path}')
        pixels = np.empty(SIZE * SIZE * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(SIZE, SIZE, 4)
        if color:
            rgb = pixels[..., :3]
            pixels[..., :3] = np.where(
                rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
        pixels[..., 3] = 1
        return pixels
    finally:
        bpy.data.images.remove(image)


def _palette(source, target, contrast=.82, limits=(.32, 2.8)):
    """Keep source weave/engraving variation without its broad pale lighting."""
    median = np.maximum(np.median(source.reshape(-1, 3), axis=0), 1e-6)
    variation = np.clip(source / median, *limits) ** contrast
    return variation * np.asarray(target, dtype=np.float32)


def _normal_strength(pixels, strength):
    vector = pixels[..., :3] * 2 - 1
    vector[..., :2] *= strength
    vector[..., 2] = np.maximum(vector[..., 2], .01)
    vector /= np.maximum(np.linalg.norm(vector, axis=2, keepdims=True), 1e-6)
    pixels[..., :3] = vector * .5 + .5


def _gutter(pixels):
    # uvcoord keeps all geometry inside the central 95% of each swatch.
    edges = np.clip(np.arange(CELL), 13, CELL - 14)
    pixels[:] = pixels[edges[:, None], edges[None, :]]


def _samegawa(base, normal, orm):
    """Small irregular rounded nodules, with dark pore valleys, beneath ito."""
    yy, xx = np.mgrid[:CELL, :CELL].astype(np.float32)
    x, y = xx / CELL * 34, yy / CELL * 34
    ix, iy = np.floor(x), np.floor(y)
    nearest = np.full_like(x, 100)
    # Jittered bead centers avoid the regular diagonal stripes of cord texture.
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = ix + dx, iy + dy
            jx = np.mod(np.sin(cx * 127.1 + cy * 311.7) * 43758.5453, 1)
            jy = np.mod(np.sin(cx * 269.5 + cy * 183.3) * 27183.1287, 1)
            distance = (x - cx - .5 - (jx - .5) * .48) ** 2
            distance += (y - cy - .5 - (jy - .5) * .48) ** 2
            nearest = np.minimum(nearest, distance)
    bead = np.exp(-nearest * 8.8)
    rng = np.random.default_rng(118001)
    grain = rng.normal(0, .035, (CELL, CELL)).astype(np.float32)
    height = bead * 1.45 + grain * .16
    gy, gx = np.gradient(height)
    vector = np.stack((-gx, -gy, np.ones_like(gx)), axis=2)
    vector /= np.linalg.norm(vector, axis=2, keepdims=True)
    color = np.asarray((.092, .009, .0055), dtype=np.float32)
    _tile(base, 1)[..., :3] = color * (.68 + bead * .48 + grain)[..., None]
    _tile(normal, 1)[..., :3] = vector * .5 + .5
    packed = _tile(orm, 1)
    packed[..., 0] = .87 + bead * .13
    packed[..., 1] = .69 - bead * .055
    packed[..., 2] = 0
    for pixels in (base, normal, orm):
        _gutter(_tile(pixels, 1))


def _save(directory, suffix, pixels):
    encoded = np.clip(pixels, 0, 1).astype(np.float32)
    if suffix == 'BaseColor':
        rgb = encoded[..., :3]
        encoded[..., :3] = np.where(
            rgb <= .0031308, rgb * 12.92,
            1.055 * np.power(rgb, 1 / 2.4) - .055)
    encoded[..., 3] = 1
    name = 'T_Tachi01_' + suffix
    # Save encoded bytes without an additional display/view transform, then
    # reload with the runtime interpretation. This matches the Dō pipeline.
    image = bpy.data.images.new(name + '_write', width=SIZE, height=SIZE, alpha=True)
    image.colorspace_settings.name = 'Non-Color'
    image.pixels.foreach_set(encoded.ravel())
    path = directory / (name + '.png')
    image.filepath_raw = str(path)
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = name
    image.colorspace_settings.name = 'sRGB' if suffix == 'BaseColor' else 'Non-Color'
    image.pack()
    return image


def build_material(ART):
    """Write three Tachi atlases and return M_Tachi01_Fittings; no scene edits."""
    art = Path(ART)
    source = art.parent / 'Do01' / 'Textures'
    directory = art / 'Textures'
    directory.mkdir(parents=True, exist_ok=True)
    base = _read(source / 'T_Do01_BaseColor.png', color=True)
    normal = _read(source / 'T_Do01_Normal.png')
    orm = _read(source / 'T_Do01_ORM.png')

    # Retain the Dō's restrained physical relief on fittings and lacquer.
    cord_color = _tile(base, 3)[..., :3].copy()
    cord_normal = _tile(normal, 3).copy()
    cord_orm = _tile(orm, 3).copy()
    _normal_strength(normal, .65)

    lacquer = _tile(base, 0)
    lacquer[..., :3] = _palette(lacquer[..., :3], (.0045, .0055, .0065),
                                contrast=.66, limits=(.4, 3.0))
    packed = _tile(orm, 0)
    old_rough = packed[..., 1].copy()
    packed[..., 1] = np.clip(.285 + (old_rough - np.median(old_rough)) * .34, .25, .32)
    packed[..., 2] = 0

    for index, color in ((2, (.265, .146, .048)), (11, (.235, .122, .038))):
        metal = _tile(base, index)
        metal[..., :3] = _palette(metal[..., :3], color, contrast=.88,
                                  limits=(.23, 1.9))
        packed = _tile(orm, index)
        old_rough = packed[..., 1].copy()
        packed[..., 1] = np.clip(.35 + (old_rough - np.median(old_rough)) * .6, .31, .43)
        packed[..., 2] = .94

    _tile(base, 3)[..., :3] = _palette(cord_color, (.074, .0065, .0040),
                                      contrast=.87, limits=(.2, 3.1))
    _tile(normal, 3)[:] = cord_normal
    _normal_strength(_tile(normal, 3), .85)
    packed = _tile(orm, 3)
    packed[..., 1] = np.clip(.80 + (cord_orm[..., 1] - .86) * .8, .77, .85)
    packed[..., 2] = 0

    # Tsuka-ito is black woven silk, not the source atlas's brown leather.
    luminance = cord_color @ np.asarray((.2126, .7152, .0722), dtype=np.float32)
    variation = np.clip(luminance / max(float(np.median(luminance)), 1e-6), .24, 3.0) ** .84
    _tile(base, 4)[..., :3] = variation[..., None] * np.asarray((.006, .007, .009), dtype=np.float32)
    _tile(normal, 4)[:] = cord_normal
    _normal_strength(_tile(normal, 4), 1.05)
    _tile(orm, 4)[:] = cord_orm
    packed = _tile(orm, 4)
    packed[..., 1] = np.clip(.90 + (cord_orm[..., 1] - .86) * .9, .87, .94)
    packed[..., 2] = 0
    _samegawa(base, normal, orm)

    images = [_save(directory, suffix, pixels) for suffix, pixels in
              (('BaseColor', base), ('Normal', normal), ('ORM', orm))]
    material = bpy.data.materials.new('M_Tachi01_Fittings')
    material.use_nodes = True
    material.diffuse_color = (.006, .007, .009, 1)
    material['atlas_source'] = 'Do01 preserved BaseColor/Normal/ORM'
    material['normal_convention'] = 'OpenGL; authored strength baked into texture'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Alpha'].default_value = 1
    bsdf.inputs['Coat Weight'].default_value = 0
    bsdf.inputs['Roughness'].default_value = .35
    cloth_response=nodes.new('ShaderNodeVertexColor');cloth_response.layer_name='ArmorTint'
    split=nodes.new('ShaderNodeSeparateColor')
    links.new(cloth_response.outputs['Color'],split.inputs[0])
    links.new(split.outputs['Red'],bsdf.inputs['Specular IOR Level'])
    for index, image in enumerate(images):
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = image
        texture.location = (-600, 250 - index * 250)
        texture.label = image.name
        if index == 0:
            links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
        elif index == 1:
            tangent = nodes.new('ShaderNodeNormalMap')
            tangent.location = (-280, 0)
            tangent.inputs['Strength'].default_value = 1
            links.new(texture.outputs['Color'], tangent.inputs['Color'])
            links.new(tangent.outputs['Normal'], bsdf.inputs['Normal'])
        else:
            channels = nodes.new('ShaderNodeSeparateColor')
            channels.location = (-280, -250)
            links.new(texture.outputs['Color'], channels.inputs['Color'])
            links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
            links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
    return material
