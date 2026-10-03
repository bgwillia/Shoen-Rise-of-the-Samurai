#!/usr/bin/env python3
"""Author the reusable RuralHouse_01 exterior PBR texture set.

The maps are deliberately generated from periodic fields and wrapped strokes so
they tile in both axes. Normals use the OpenGL tangent convention (+Y / green
up); invert green when importing into Unreal.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures"
RNG_SEEDS = {
    "Thatch": 11801,
    "Timber": 11802,
    "Plaster": 11803,
    "Stone": 11804,
    "Rope": 11805,
}


def periodic_noise(size: int, sigma: float, rng: np.random.Generator) -> np.ndarray:
    """Return normalized, seamless Gaussian noise using a periodic FFT filter."""
    source = rng.standard_normal((size, size)).astype(np.float32)
    fy = np.fft.fftfreq(size).astype(np.float32)[:, None]
    fx = np.fft.rfftfreq(size).astype(np.float32)[None, :]
    kernel = np.exp(-2.0 * math.pi**2 * sigma**2 * (fx * fx + fy * fy))
    field = np.fft.irfft2(np.fft.rfft2(source) * kernel, s=source.shape).real
    field = field.astype(np.float32)
    field -= field.mean()
    field /= max(float(field.std()), 1.0e-6)
    return field


def multiscale_noise(size: int, rng: np.random.Generator, layers) -> np.ndarray:
    result = np.zeros((size, size), dtype=np.float32)
    weight_sum = 0.0
    for sigma, weight in layers:
        result += periodic_noise(size, sigma, rng) * weight
        weight_sum += weight
    return result / max(weight_sum, 1.0e-6)


def softstep(edge0, edge1, x):
    t = np.clip((x - edge0) / max(edge1 - edge0, 1.0e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def wrapped_polyline(draw: ImageDraw.ImageDraw, points, fill, width, size):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    margin = width + 3
    x_offsets = [0]
    y_offsets = [0]
    if min(xs) < margin:
        x_offsets.append(size)
    if max(xs) > size - margin:
        x_offsets.append(-size)
    if min(ys) < margin:
        y_offsets.append(size)
    if max(ys) > size - margin:
        y_offsets.append(-size)
    for ox in x_offsets:
        for oy in y_offsets:
            draw.line([(x + ox, y + oy) for x, y in points], fill=fill, width=width, joint="curve")


def stroke_mask(size: int):
    image = Image.new("L", (size, size), 0)
    return image, ImageDraw.Draw(image)


def mask_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image, dtype=np.float32) / 255.0


def composite(base: np.ndarray, mask: np.ndarray, color) -> np.ndarray:
    alpha = mask[..., None]
    tint = np.asarray(color, dtype=np.float32)[None, None, :]
    return base * (1.0 - alpha) + tint * alpha


def normal_from_height(height: np.ndarray, strength: float) -> np.ndarray:
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    # Image rows grow downward while texture V grows upward. This produces +Y
    # OpenGL normals; Unreal's DirectX convention should invert green.
    dv_image = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -du * strength
    ny = dv_image * strength
    nz = np.ones_like(height)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack((nx / norm, ny / norm, nz / norm), axis=-1) * 0.5 + 0.5


def ambient_occlusion(height: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    size = height.shape[0]
    # Lower pixels surrounded by higher material receive restrained occlusion.
    broad = periodic_blur(height, 7.0)
    tight = periodic_blur(height, 2.0)
    cavity = np.maximum(tight - height, 0.0) + 0.55 * np.maximum(broad - height, 0.0)
    cavity /= max(float(np.percentile(cavity, 99.5)), 1.0e-5)
    micro = periodic_noise(size, 2.5, rng)
    return np.clip(0.985 - 0.23 * cavity + 0.012 * micro, 0.68, 1.0)


def periodic_blur(field: np.ndarray, sigma: float) -> np.ndarray:
    h, w = field.shape
    fy = np.fft.fftfreq(h).astype(np.float32)[:, None]
    fx = np.fft.rfftfreq(w).astype(np.float32)[None, :]
    kernel = np.exp(-2.0 * math.pi**2 * sigma**2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(field) * kernel, s=field.shape).real.astype(np.float32)


def save_set(name: str, base: np.ndarray, height: np.ndarray, roughness: np.ndarray, normal_strength: float, rng):
    OUT.mkdir(parents=True, exist_ok=True)
    base = np.clip(base, 0.0, 255.0).astype(np.uint8)
    normal = np.clip(normal_from_height(height, normal_strength) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    ao = ambient_occlusion(height, rng)
    orm = np.stack((ao, np.clip(roughness, 0.0, 1.0), np.zeros_like(ao)), axis=-1)
    orm = np.clip(orm * 255.0 + 0.5, 0, 255).astype(np.uint8)

    Image.fromarray(base, "RGB").save(OUT / f"RH01_{name}_BaseColor.png", compress_level=4)
    Image.fromarray(normal, "RGB").save(OUT / f"RH01_{name}_Normal.png", compress_level=4)
    Image.fromarray(orm, "RGB").save(OUT / f"RH01_{name}_ORM.png", compress_level=4)
    mean = tuple(int(v) for v in base.reshape(-1, 3).mean(axis=0))
    print(f"{name:7s} {base.shape[1]}x{base.shape[0]} mean RGB {mean}, mean roughness {roughness.mean():.3f}")


def make_thatch():
    name, size = "Thatch", 2048
    rng = np.random.default_rng(RNG_SEEDS[name])
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    fine = multiscale_noise(size, rng, ((1.1, 0.20), (3.0, 0.28), (11.0, 0.30), (55.0, 0.22)))
    coarse = periodic_noise(size, 95.0, rng)

    base_color = np.array((121.0, 96.0, 62.0), dtype=np.float32)
    warm = np.array((10.0, 6.0, 1.0), dtype=np.float32)
    base = base_color + fine[..., None] * np.array((13.0, 11.0, 8.0)) + coarse[..., None] * warm
    height = 0.47 + fine * 0.045 + coarse * 0.025

    # Overlapping, irregular eave-to-ridge courses. They are broad enough to
    # read at building scale without turning the surface into stripes.
    course_count = 8
    spacing = size / course_count
    edge_warp = 13.0 * np.sin(2.0 * np.pi * x / size * 3.0) + 9.0 * periodic_noise(size, 48.0, rng)
    phase = np.mod(y + edge_warp, spacing)
    shadow_distance = np.abs(phase - 5.0)
    shadow_distance = np.minimum(shadow_distance, spacing - shadow_distance)
    lip_distance = np.abs(phase - 17.0)
    lip_distance = np.minimum(lip_distance, spacing - lip_distance)
    course_shadow = np.exp(-(shadow_distance / 8.0) ** 2)
    course_lip = np.exp(-(lip_distance / 10.0) ** 2)
    base -= course_shadow[..., None] * np.array((28.0, 23.0, 16.0))
    base += course_lip[..., None] * np.array((9.0, 8.0, 5.0))
    height += course_lip * 0.07 - course_shadow * 0.09

    shadow_img, shadow_draw = stroke_mask(size)
    straw_img, straw_draw = stroke_mask(size)
    highlight_img, highlight_draw = stroke_mask(size)
    # Dense, broken vertical fibers. UV +V is the straw length direction.
    for _ in range(11000):
        sx = float(rng.uniform(0, size))
        sy = float(rng.uniform(0, size))
        length = float(rng.uniform(50, 245) * rng.uniform(0.65, 1.15))
        drift = float(rng.normal(0.0, 9.0))
        bow = float(rng.normal(0.0, 5.0))
        points = [
            (sx, sy),
            (sx + bow, sy + length * 0.32),
            (sx + drift * 0.55 - bow * 0.25, sy + length * 0.67),
            (sx + drift, sy + length),
        ]
        width = int(rng.integers(2, 5))
        opacity = int(rng.integers(48, 135))
        wrapped_polyline(shadow_draw, [(px + 2.0, py + 1.5) for px, py in points], opacity, width + 2, size)
        wrapped_polyline(straw_draw, points, int(rng.integers(55, 155)), width, size)
        if rng.random() < 0.48:
            wrapped_polyline(highlight_draw, [(px - 0.8, py) for px, py in points], int(rng.integers(35, 105)), 1, size)

    shadow = mask_array(shadow_img)
    straw = mask_array(straw_img)
    highlight = mask_array(highlight_img)
    base = composite(base, shadow * 0.80, (72, 54, 34))
    base = composite(base, straw * 0.70, (139, 111, 69))
    base = composite(base, highlight * 0.62, (160, 130, 84))
    height += straw * 0.13 + highlight * 0.045 - shadow * 0.09
    roughness = np.clip(0.885 + 0.030 * fine + 0.018 * coarse - 0.018 * straw, 0.82, 0.96)
    save_set(name, base, height, roughness, 8.0, rng)


def make_timber():
    name, size = "Timber", 1024
    rng = np.random.default_rng(RNG_SEEDS[name])
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    u, v = x / size, y / size
    warp = 0.030 * np.sin(2 * np.pi * v * 2.0) + 0.018 * periodic_noise(size, 36.0, rng)
    grain_coord = u + warp
    grain = (
        0.56 * np.sin(2 * np.pi * (grain_coord * 18.0 + 0.35 * np.sin(2 * np.pi * v * 3.0)))
        + 0.29 * np.sin(2 * np.pi * (grain_coord * 43.0 - 0.22 * np.sin(2 * np.pi * v * 5.0)))
        + 0.15 * np.sin(2 * np.pi * (grain_coord * 91.0 + v * 1.0))
    )
    grain = np.tanh(grain * 1.35)
    fine = multiscale_noise(size, rng, ((1.2, 0.20), (4.5, 0.32), (24.0, 0.30), (90.0, 0.18)))
    base = np.array((73.0, 59.0, 44.0)) + grain[..., None] * np.array((9.0, 7.0, 4.5)) + fine[..., None] * np.array((6.0, 5.0, 4.0))
    height = 0.50 + grain * 0.060 + fine * 0.025

    # Wrapped knots create readable timber history without modern sawmill regularity.
    for _ in range(13):
        cx, cy = rng.uniform(0, size, 2)
        rx, ry = rng.uniform(24, 52), rng.uniform(42, 105)
        dx = (x - cx + size * 0.5) % size - size * 0.5
        dy = (y - cy + size * 0.5) % size - size * 0.5
        r = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
        envelope = np.exp(-r * r * 1.3)
        rings = np.sin(r * 30.0 + rng.uniform(0, 6.28)) * envelope
        core = np.exp(-r * r * 8.0)
        base += rings[..., None] * np.array((8.0, 6.0, 4.0))
        base -= core[..., None] * np.array((24.0, 19.0, 13.0))
        height += rings * 0.028 - core * 0.055

    # Broad adze facets catch light subtly and keep the surface hand-hewn.
    cuts_img, cuts_draw = stroke_mask(size)
    cuts_hi_img, cuts_hi_draw = stroke_mask(size)
    for _ in range(150):
        sx, sy = rng.uniform(0, size, 2)
        length = rng.uniform(28, 92)
        angle = rng.choice((-1, 1)) * rng.uniform(0.18, 0.55)
        points = [(sx, sy), (sx + math.sin(angle) * length, sy + math.cos(angle) * length)]
        wrapped_polyline(cuts_draw, points, int(rng.integers(30, 92)), int(rng.integers(2, 5)), size)
        wrapped_polyline(cuts_hi_draw, [(px + 2, py) for px, py in points], int(rng.integers(20, 65)), 1, size)
    cuts, cuts_hi = mask_array(cuts_img), mask_array(cuts_hi_img)
    base = composite(base, cuts * 0.36, (45, 36, 27))
    base = composite(base, cuts_hi * 0.25, (96, 77, 55))
    height += cuts_hi * 0.035 - cuts * 0.040
    roughness = np.clip(0.815 + 0.025 * fine - 0.020 * grain + 0.018 * cuts, 0.74, 0.90)
    save_set(name, base, height, roughness, 7.0, rng)


def make_plaster():
    name, size = "Plaster", 1024
    rng = np.random.default_rng(RNG_SEEDS[name])
    fine = multiscale_noise(size, rng, ((1.2, 0.18), (5.0, 0.30), (22.0, 0.32), (85.0, 0.20)))
    mottling = periodic_noise(size, 95.0, rng)
    base = np.array((168.0, 154.0, 128.0)) + fine[..., None] * np.array((7.0, 6.5, 5.5)) + mottling[..., None] * np.array((7.0, 6.0, 4.0))
    height = 0.52 + fine * 0.040 + mottling * 0.018

    # Soft horizontal/diagonal trowel passes, held well below the crack contrast.
    smear_img, smear_draw = stroke_mask(size)
    for _ in range(95):
        sx, sy = rng.uniform(0, size, 2)
        length = rng.uniform(45, 180)
        angle = rng.uniform(-0.38, 0.38) + math.pi * 0.5
        ex = sx + math.sin(angle) * length
        ey = sy + math.cos(angle) * length
        wrapped_polyline(smear_draw, [(sx, sy), (ex, ey)], int(rng.integers(13, 40)), int(rng.integers(4, 12)), size)
    smear = mask_array(smear_img)
    base = composite(base, smear * 0.18, (185, 172, 146))
    height += smear * 0.022

    cracks_img, cracks_draw = stroke_mask(size)
    crack_hi_img, crack_hi_draw = stroke_mask(size)
    for _ in range(42):
        sx, sy = rng.uniform(0, size, 2)
        angle = rng.uniform(0, 2 * math.pi)
        points = [(sx, sy)]
        x, y = sx, sy
        for _segment in range(int(rng.integers(3, 8))):
            angle += rng.normal(0, 0.42)
            step = rng.uniform(13, 37)
            x += math.cos(angle) * step
            y += math.sin(angle) * step
            points.append((x, y))
        width = int(rng.choice((1, 1, 1, 2)))
        wrapped_polyline(cracks_draw, points, int(rng.integers(100, 190)), width + 1, size)
        wrapped_polyline(crack_hi_draw, [(px + 1.2, py + 0.8) for px, py in points], int(rng.integers(30, 75)), 1, size)
        if rng.random() < 0.5 and len(points) > 3:
            bx, by = points[int(rng.integers(1, len(points) - 1))]
            branch_angle = angle + rng.choice((-1, 1)) * rng.uniform(0.55, 1.15)
            branch = [(bx, by), (bx + math.cos(branch_angle) * rng.uniform(15, 45), by + math.sin(branch_angle) * rng.uniform(15, 45))]
            wrapped_polyline(cracks_draw, branch, int(rng.integers(70, 145)), 1, size)
    cracks, crack_hi = mask_array(cracks_img), mask_array(crack_hi_img)
    base = composite(base, cracks * 0.70, (100, 88, 70))
    base = composite(base, crack_hi * 0.30, (190, 177, 150))
    height += crack_hi * 0.018 - cracks * 0.105
    roughness = np.clip(0.885 + 0.030 * fine + 0.018 * mottling + 0.018 * cracks, 0.82, 0.96)
    save_set(name, base, height, roughness, 6.5, rng)


def periodic_voronoi(size: int, seeds: np.ndarray):
    labels = np.empty((size, size), dtype=np.int16)
    nearest = np.empty((size, size), dtype=np.float32)
    second = np.empty((size, size), dtype=np.float32)
    xs = np.arange(size, dtype=np.float32)[None, :, None]
    for y0 in range(0, size, 32):
        y1 = min(y0 + 32, size)
        ys = np.arange(y0, y1, dtype=np.float32)[:, None, None]
        dx = np.abs(xs - seeds[None, None, :, 0])
        dy = np.abs(ys - seeds[None, None, :, 1])
        dx = np.minimum(dx, size - dx)
        dy = np.minimum(dy, size - dy)
        dist2 = dx * dx + dy * dy
        labels[y0:y1] = np.argmin(dist2, axis=2)
        near2 = np.partition(dist2, 1, axis=2)[..., :2]
        near2.sort(axis=2)
        nearest[y0:y1] = np.sqrt(near2[..., 0])
        second[y0:y1] = np.sqrt(near2[..., 1])
    return labels, nearest, second


def make_stone():
    name, size = "Stone", 2048
    rng = np.random.default_rng(RNG_SEEDS[name])
    grain = periodic_noise(size, 1.15, rng)
    mineral = periodic_noise(size, 8.0, rng)
    mottling = periodic_noise(size, 38.0, rng)
    weathering = periodic_noise(size, 145.0, rng)
    fine = grain * 0.18 + mineral * 0.31 + mottling * 0.32 + weathering * 0.19

    # This is continuous rock surface only. The modeled beveled blocks provide
    # every large boundary, avoiding a second stamped paving pattern in albedo.
    base = (
        np.array((101.0, 98.0, 89.0))
        + grain[..., None] * np.array((2.8, 2.6, 2.3))
        + mineral[..., None] * np.array((4.8, 4.4, 3.8))
        + mottling[..., None] * np.array((6.0, 5.7, 5.0))
        + weathering[..., None] * np.array((6.5, 6.0, 4.8))
    )
    height = 0.50 + grain * 0.014 + mineral * 0.026 + mottling * 0.032 + weathering * 0.018

    # Small wrapped pits and worn inclusions add close-range structure without
    # suggesting joints, flagstones, brickwork, or polygon cells.
    pits_img, pits_draw = stroke_mask(size)
    pale_img, pale_draw = stroke_mask(size)
    for _ in range(920):
        cx, cy = rng.uniform(0, size, 2)
        radius = float(np.clip(rng.lognormal(mean=0.7, sigma=0.55), 0.7, 8.0))
        opacity = int(rng.integers(45, 165))
        offsets_x = (0, size, -size) if cx < radius + 2 or cx > size - radius - 2 else (0,)
        offsets_y = (0, size, -size) if cy < radius + 2 or cy > size - radius - 2 else (0,)
        for ox in offsets_x:
            for oy in offsets_y:
                box = (cx + ox - radius, cy + oy - radius, cx + ox + radius, cy + oy + radius)
                pits_draw.ellipse(box, fill=opacity)
        if rng.random() < 0.28:
            pr = max(0.6, radius * 0.38)
            pale_draw.ellipse((cx - pr, cy - pr, cx + pr, cy + pr), fill=int(rng.integers(35, 95)))
    pits = periodic_blur(mask_array(pits_img), 0.75)
    pale = periodic_blur(mask_array(pale_img), 0.55)
    base = composite(base, pits * 0.48, (72, 70, 65))
    base = composite(base, pale * 0.35, (135, 130, 116))
    height += pale * 0.018 - pits * 0.070

    roughness = np.clip(0.905 + fine * 0.018 + pits * 0.035, 0.86, 0.97)
    save_set(name, base, height, roughness, 5.0, rng)


def make_rope():
    name, size = "Rope", 1024
    rng = np.random.default_rng(RNG_SEEDS[name])
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    u, v = x / size, y / size
    # Integer frequencies preserve exact periodicity. Major diagonal ridges read
    # as the three laid strands; finer parallel ridges read as individual fibers.
    major_phase = 2 * np.pi * (u * 6.0 + v * 12.0)
    opposing_phase = 2 * np.pi * (u * 3.0 - v * 6.0)
    fiber_phase = 2 * np.pi * (u * 31.0 + v * 62.0)
    major = np.maximum(np.sin(major_phase), -0.55)
    opposing = np.maximum(np.sin(opposing_phase), -0.72)
    fibers = np.sin(fiber_phase + 0.26 * np.sin(major_phase))
    fine = multiscale_noise(size, rng, ((1.0, 0.22), (3.5, 0.34), (15.0, 0.28), (58.0, 0.16)))
    base = (
        np.array((128.0, 104.0, 72.0))
        + major[..., None] * np.array((13.0, 10.0, 6.0))
        + opposing[..., None] * np.array((4.5, 3.5, 2.0))
        + fibers[..., None] * np.array((4.0, 3.2, 2.1))
        + fine[..., None] * np.array((7.0, 6.0, 4.5))
    )
    dark_groove = np.clip(-major - 0.18, 0.0, 1.0)
    base -= dark_groove[..., None] * np.array((20.0, 17.0, 12.0))
    height = 0.48 + major * 0.12 + opposing * 0.035 + fibers * 0.025 + fine * 0.018 - dark_groove * 0.05

    fly_img, fly_draw = stroke_mask(size)
    for _ in range(280):
        sx, sy = rng.uniform(0, size, 2)
        length = rng.uniform(12, 65)
        drift = rng.normal(0, 7)
        points = [(sx, sy), (sx + drift * 0.35, sy + length * 0.5), (sx + drift, sy + length)]
        wrapped_polyline(fly_draw, points, int(rng.integers(18, 60)), 1, size)
    fly = mask_array(fly_img)
    base = composite(base, fly * 0.35, (166, 139, 94))
    height += fly * 0.020
    roughness = np.clip(0.88 + 0.030 * fine + 0.025 * dark_groove + 0.014 * fly, 0.82, 0.96)
    save_set(name, base, height, roughness, 7.0, rng)


def main():
    make_thatch()
    make_timber()
    make_plaster()
    make_stone()
    make_rope()
    print(f"Wrote 15 texture maps to {OUT}")


if __name__ == "__main__":
    main()
