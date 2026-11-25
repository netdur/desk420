#!/usr/bin/env python3
"""Generate Desk420's macOS AppIcon.icns into assets/AppIcon.icns.

Uses only Python stdlib + macOS sips/iconutil so the icon builds identically
on any Mac with no external dependencies.
"""
import math
import os
import shutil
import struct
import subprocess
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ICNS = os.path.join(ROOT, "assets", "AppIcon.icns")


def write_png(path: str, width: int, height: int, rgba: bytes) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)  # filter type 0
        raw.extend(rgba[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)


def sd_rounded_box(px: float, py: float, bx: float, by: float, r: float) -> float:
    qx = abs(px) - bx + r
    qy = abs(py) - by + r
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def point_in_poly(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def dist_seg(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    c1 = vx * wx + vy * wy
    if c1 <= 0.0:
        return math.hypot(px - ax, py - ay)
    c2 = vx * vx + vy * vy
    if c2 <= c1:
        return math.hypot(px - bx, py - by)
    t = c1 / c2
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def sd_poly(px: float, py: float, poly: list[tuple[float, float]]) -> float:
    d = min(
        dist_seg(px, py, poly[i][0], poly[i][1], poly[(i + 1) % len(poly)][0], poly[(i + 1) % len(poly)][1])
        for i in range(len(poly))
    )
    return -d if point_in_poly(px, py, poly) else d


def clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = clamp01((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def render_icon(size: int = 1024) -> bytes:
    # Apple macOS icon grid: outer ~80% squircle with subtle top highlight + Desk420 lime bolt mark
    buf = bytearray(size * size * 4)
    # Crisp geometric lightning/spark polygon in normalized [-1, 1] coords
    bolt = [
        (0.06, -0.52),
        (-0.34, 0.06),
        (-0.02, 0.06),
        (-0.10, 0.52),
        (0.34, -0.08),
        (0.02, -0.08),
    ]
    aa = 2.5 / size

    idx = 0
    for py in range(size):
        ny = (py + 0.5) / size * 2.0 - 1.0
        for px in range(size):
            nx = (px + 0.5) / size * 2.0 - 1.0

            # Outer rounded macOS squircle (margin ~9.5% on each side, radius ~22% of box)
            d_box = sd_rounded_box(nx, ny, 0.81, 0.81, 0.36)
            alpha_box = 1.0 - smoothstep(-aa, aa, d_box)
            if alpha_box <= 0.001:
                idx += 4
                continue

            # Subtle dark obsidian vertical gradient + soft lime radial glow behind the bolt
            grad = clamp01((ny + 0.85) / 1.7)
            bg_r = 26.0 - 10.0 * grad
            bg_g = 28.0 - 11.0 * grad
            bg_b = 31.0 - 11.0 * grad

            r_glow = math.hypot(nx, ny * 0.9)
            glow = math.exp(-r_glow * r_glow * 3.4) * 0.14
            bg_r += 198.0 * glow
            bg_g += 241.0 * glow
            bg_b += 53.0 * glow

            # Subtle hairline inner rim
            rim = smoothstep(-0.032, -0.014, d_box) * (1.0 - smoothstep(-0.008, 0.0, d_box))
            rim_k = rim * (0.16 if ny < 0.0 else 0.07)
            bg_r = bg_r * (1.0 - rim_k) + 255.0 * rim_k
            bg_g = bg_g * (1.0 - rim_k) + 255.0 * rim_k
            bg_b = bg_b * (1.0 - rim_k) + 255.0 * rim_k

            # Lime bolt mark (#C6F135 -> #B4E522 vertical sheen)
            d_bolt = sd_poly(nx, ny, bolt)
            alpha_bolt = 1.0 - smoothstep(-aa, aa, d_bolt)
            if alpha_bolt > 0.0:
                b_grad = clamp01((ny + 0.52) / 1.04)
                fg_r = 208.0 - 24.0 * b_grad
                fg_g = 247.0 - 18.0 * b_grad
                fg_b = 64.0 - 24.0 * b_grad
                r = bg_r * (1.0 - alpha_bolt) + fg_r * alpha_bolt
                g = bg_g * (1.0 - alpha_bolt) + fg_g * alpha_bolt
                b = bg_b * (1.0 - alpha_bolt) + fg_b * alpha_bolt
            else:
                r, g, b = bg_r, bg_g, bg_b

            buf[idx] = int(min(255, max(0, r)))
            buf[idx + 1] = int(min(255, max(0, g)))
            buf[idx + 2] = int(min(255, max(0, b)))
            buf[idx + 3] = int(min(255, max(0, alpha_box * 255.0)))
            idx += 4

    return bytes(buf)


def main() -> None:
    os.makedirs(os.path.dirname(OUT_ICNS), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        master = os.path.join(td, "icon_1024.png")
        iconset = os.path.join(td, "AppIcon.iconset")
        os.makedirs(iconset)

        rgba = render_icon(1024)
        write_png(master, 1024, 1024, rgba)

        specs = [
            ("icon_16x16.png", 16),
            ("icon_16x16@2x.png", 32),
            ("icon_32x32.png", 32),
            ("icon_32x32@2x.png", 64),
            ("icon_128x128.png", 128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png", 256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png", 512),
            ("icon_512x512@2x.png", 1024),
        ]
        for fname, dim in specs:
            dst = os.path.join(iconset, fname)
            if dim == 1024:
                shutil.copyfile(master, dst)
            else:
                subprocess.run(
                    ["sips", "-z", str(dim), str(dim), master, "--out", dst],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", OUT_ICNS], check=True)
        print(f"wrote {OUT_ICNS} ({os.path.getsize(OUT_ICNS)} bytes)")


if __name__ == "__main__":
    main()
