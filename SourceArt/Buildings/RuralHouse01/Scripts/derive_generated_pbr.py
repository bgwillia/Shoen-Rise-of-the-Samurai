#!/usr/bin/env python3
"""Prepare generated RuralHouse_01 swatches and derive aligned PBR maps.

This is intentionally asset-specific. It resizes and edge-feathers the source
swatch, then treats restrained luminance structure as relief. Output normals
use OpenGL tangent +Y; Unreal imports must flip the green channel.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures"


def periodic_blur(field: np.ndarray, sigma: float) -> np.ndarray:
    h, w = field.shape
    fy = np.fft.fftfreq(h).astype(np.float32)[:, None]
    fx = np.fft.rfftfreq(w).astype(np.float32)[None, :]
    kernel = np.exp(-2.0 * math.pi**2 * sigma**2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(field) * kernel, s=field.shape).real.astype(np.float32)


def match_edges(image: np.ndarray, band: int) -> np.ndarray:
    result = image.astype(np.float32).copy()
    for axis in (1, 0):
        source = result.copy()
        count = source.shape[axis]
        for offset in range(band):
            weight = 0.5 * (1.0 + math.cos(math.pi * offset / (band - 1)))
            lo = [slice(None)] * 3
            hi = [slice(None)] * 3
            lo[axis] = offset
            hi[axis] = count - 1 - offset
            low = source[tuple(lo)]
            high = source[tuple(hi)]
            average = (low + high) * 0.5
            result[tuple(lo)] = low * (1.0 - weight) + average * weight
            result[tuple(hi)] = high * (1.0 - weight) + average * weight
    return result


def derive_height(base: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rgb = np.clip(base / 255.0, 0.0, 1.0)
    luminance = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    # Remove pixel-level image noise while retaining shaft edges, shallow checks,
    # plaster trowel relief, and broader cavities.
    tight = periodic_blur(luminance, 1.25)
    medium = periodic_blur(luminance, 4.0)
    broad = periodic_blur(luminance, 13.0)
    relief = tight * 0.58 + medium * 0.29 + broad * 0.13
    low, high = np.percentile(relief, (1.0, 99.0))
    height = np.clip((relief - low) / max(float(high - low), 1.0e-6), 0.0, 1.0)
    return height.astype(np.float32), luminance.astype(np.float32)


def normal_from_height(height: np.ndarray, strength: float) -> np.ndarray:
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dv_image = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -du * strength
    ny = dv_image * strength
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack((nx / length, ny / length, nz / length), axis=-1) * 0.5 + 0.5


def derive_maps(base: np.ndarray, roughness: float, normal_strength: float):
    height, luminance = derive_height(base)
    normal = normal_from_height(height, normal_strength)
    surrounding = periodic_blur(height, 9.0)
    cavity = np.maximum(surrounding - height, 0.0)
    cavity /= max(float(np.percentile(cavity, 99.0)), 1.0e-6)
    ao = np.clip(0.992 - 0.22 * cavity, 0.74, 1.0)
    micro = periodic_blur(luminance, 1.4) - periodic_blur(luminance, 7.0)
    rough = np.clip(roughness + (0.5 - luminance) * 0.035 + micro * 0.04, roughness - 0.07, roughness + 0.07)
    orm = np.stack((ao, rough, np.zeros_like(ao)), axis=-1)
    return normal, orm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=("Thatch", "Timber", "Plaster"))
    parser.add_argument("source", type=Path)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--roughness", type=float, required=True)
    parser.add_argument("--normal-strength", type=float, required=True)
    args = parser.parse_args()

    source = Image.open(args.source).convert("RGB")
    if source.size != (args.size, args.size):
        source = source.resize((args.size, args.size), Image.Resampling.LANCZOS)
    base = match_edges(np.asarray(source, dtype=np.float32), max(64, args.size * 7 // 100))
    normal, orm = derive_maps(base, args.roughness, args.normal_strength)

    OUT.mkdir(parents=True, exist_ok=True)
    base_u8 = np.clip(base + 0.5, 0, 255).astype(np.uint8)
    normal_u8 = np.clip(normal * 255.0 + 0.5, 0, 255).astype(np.uint8)
    orm_u8 = np.clip(orm * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(base_u8, "RGB").save(OUT / f"RH01_{args.name}_BaseColor.png", compress_level=4)
    Image.fromarray(normal_u8, "RGB").save(OUT / f"RH01_{args.name}_Normal.png", compress_level=4)
    Image.fromarray(orm_u8, "RGB").save(OUT / f"RH01_{args.name}_ORM.png", compress_level=4)
    mean = tuple(int(value) for value in base_u8.reshape(-1, 3).mean(axis=0))
    print(f"{args.name}: {args.size}x{args.size}; mean RGB {mean}; roughness {orm[..., 1].mean():.3f}; AO {orm[..., 0].mean():.3f}")


if __name__ == "__main__":
    main()
