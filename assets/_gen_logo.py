"""Myco Logo v9 — Devouring + Evolving Mycelium."""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

OUT_DIR = Path(__file__).parent
random.seed(42)


def generate_mycelium_logo(size=1024, dark_mode=True, pad=0.10):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    color = (0, 229, 176) if dark_mode else (0, 135, 94)
    # Center offset left — the organism is REACHING rightward (evolution direction)
    cx, cy = size * 0.44, size * 0.48
    max_r = size * (0.5 - pad)
    scale = size / 512

    segments = []
    dots = []
    tips = []
    growth_tips = []  # Brightest tips — actively extending

    def grow(x, y, angle, length, width, opacity, depth, max_depth, is_dominant=False):
        if depth > max_depth or length < 1.5 or width < 0.2 or opacity < 8:
            return
        angle += random.gauss(0, 0.16)
        # Spiral bias — slight clockwise twist = perpetual rotation feel
        angle += 0.03
        ex = x + math.cos(angle) * length
        ey = y + math.sin(angle) * length

        dist = math.sqrt((ex - cx)**2 + (ey - cy)**2)
        if dist > max_r * 1.15:
            return
        edge_fade = max(0.08, 1.0 - (dist / max_r) ** 2.0)
        alpha = int(opacity * edge_fade)

        segments.append((x, y, ex, ey, width, alpha, depth))
        tips.append((ex, ey, depth, alpha))

        # Growth tips glow (youngest, most active)
        if depth >= max_depth - 2 and alpha > 30:
            growth_tips.append((ex, ey, width * 2.5, int(alpha * 0.7)))

        if depth >= max_depth - 1 or (random.random() < 0.25 and depth > 3):
            dots.append((ex, ey, width * 1.2, alpha))

        # Dominant arms get deeper branching
        effective_max = max_depth + (1 if is_dominant else 0)

        grow(ex, ey, angle + random.gauss(0, 0.08),
             length * random.uniform(0.72, 0.86),
             width * random.uniform(0.80, 0.90),
             opacity * 0.78, depth + 1, effective_max, is_dominant)

        if random.random() < 0.7 and depth < effective_max - 1:
            side = angle + random.choice([-1, 1]) * random.uniform(0.35, 0.85)
            grow(ex, ey, side,
                 length * random.uniform(0.5, 0.7),
                 width * random.uniform(0.5, 0.7),
                 opacity * 0.50, depth + 1, effective_max, False)

        if random.random() < 0.4 and depth < effective_max - 2:
            side2 = angle + random.choice([-1, 1]) * random.uniform(0.5, 1.1)
            grow(ex, ey, side2,
                 length * random.uniform(0.35, 0.55),
                 width * random.uniform(0.35, 0.55),
                 opacity * 0.35, depth + 1, effective_max, False)

        if random.random() < 0.18 and depth < effective_max - 3:
            side3 = angle + random.choice([-1, 1]) * random.uniform(0.7, 1.4)
            grow(ex, ey, side3,
                 length * random.uniform(0.25, 0.4),
                 width * random.uniform(0.25, 0.4),
                 opacity * 0.22, depth + 1, effective_max, False)

    # === ASYMMETRIC growth: right side is DOMINANT (just evolved) ===
    primary_angles = []
    for i in range(12):
        a = (2 * math.pi * i / 12) + random.gauss(0, 0.22)
        primary_angles.append(a)

    for i, angle in enumerate(primary_angles):
        # Right-side hyphae (angle near 0 or ±pi/4) are dominant — longer, deeper
        is_right = abs(math.cos(angle)) > 0.5 and math.cos(angle) > 0
        is_dominant = is_right or (i == 0)
        base_len = random.uniform(65, 85) if is_dominant else random.uniform(45, 65)
        base_w = random.uniform(4.2, 5.8) if is_dominant else random.uniform(3.0, 4.5)
        max_d = 9 if is_dominant else 7
        grow(cx, cy, angle, base_len * scale, base_w * scale, 240, 0, max_d, is_dominant)

    # === Anastomosis ===
    anastomosis = []
    for i, (x1, y1, d1, a1) in enumerate(tips):
        for j, (x2, y2, d2, a2) in enumerate(tips):
            if i >= j:
                continue
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if 8 * scale < dist < 35 * scale and abs(d1 - d2) <= 2:
                if random.random() < 0.12:
                    a = int(30 * max(0.2, 1.0 - (dist / (35 * scale))))
                    anastomosis.append((x1, y1, x2, y2, 0.7 * scale, a))

    # === DEVOURING: particles converging toward center ===
    spores = []
    for _ in range(35):
        # Particles at various distances, with "absorption trails" toward nearest hypha
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(max_r * 0.6, max_r * 1.1)
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        sr = random.uniform(0.6, 2.0) * scale

        # Opacity: closer = brighter (being consumed)
        rel_dist = dist / max_r
        sa = int(random.uniform(12, 50) * (1.2 - rel_dist))
        sa = max(5, min(60, sa))
        spores.append((sx, sy, sr, sa))

    # Absorption trails: thin lines from spores toward center
    absorption_trails = []
    for (sx, sy, sr, sa) in spores:
        if sa > 20:  # Only visible spores get trails
            # Trail points toward center
            trail_len = random.uniform(8, 20) * scale
            angle_to_center = math.atan2(cy - sy, cx - sx)
            tx = sx + math.cos(angle_to_center) * trail_len
            ty = sy + math.sin(angle_to_center) * trail_len
            absorption_trails.append((sx, sy, tx, ty, 0.5 * scale, int(sa * 0.5)))

    # === DRAW ===
    # Absorption trails first (behind everything)
    draw = ImageDraw.Draw(img, 'RGBA')
    for (x1, y1, x2, y2, w, a) in absorption_trails:
        draw.line([(x1, y1), (x2, y2)], fill=(*color, a), width=max(1, round(w)))

    # Spores
    for (sx, sy, sr, sa) in spores:
        draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=(*color, sa))

    # Branches (deep first)
    segments.sort(key=lambda s: -s[6])
    for (x1, y1, x2, y2, w, a, d) in segments:
        draw.line([(x1, y1), (x2, y2)], fill=(*color, min(255, a)), width=max(1, round(w)))

    # Anastomosis
    for (x1, y1, x2, y2, w, a) in anastomosis:
        draw.line([(x1, y1), (x2, y2)], fill=(*color, min(255, a)), width=max(1, round(w)))

    # Terminal dots
    for (x, y, r, a) in dots:
        r = max(0.8, r)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*color, min(255, a)))

    # Growth tip glows (brightest points — actively extending = EVOLVING)
    for (gx, gy, gr, ga) in growth_tips:
        gl = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl, 'RGBA')
        gr = max(2, gr)
        gd.ellipse([gx-gr, gy-gr, gx+gr, gy+gr], fill=(*color, min(255, ga)))
        gl = gl.filter(ImageFilter.GaussianBlur(radius=max(1, int(gr * 0.5))))
        img.alpha_composite(gl)

    # Central glow
    for gr, ga in [(32*scale, 18), (20*scale, 32), (12*scale, 52)]:
        glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, 'RGBA')
        gd.ellipse([cx-gr, cy-gr, cx+gr, cy+gr], fill=(*color, ga))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=int(gr * 0.6)))
        img.alpha_composite(glow)

    # Open arc core
    draw = ImageDraw.Draw(img, 'RGBA')
    core_r = int(8 * scale)
    arc = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc, 'RGBA')
    ad.arc([int(cx-core_r), int(cy-core_r), int(cx+core_r), int(cy+core_r)],
           start=30, end=340, fill=(*color, 240), width=max(2, int(3.5 * scale)))
    img.alpha_composite(arc)

    # White center
    cl = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cl, 'RGBA')
    cr = int(3.5 * scale)
    cd.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255, 255, 255, 240))
    cl = cl.filter(ImageFilter.GaussianBlur(radius=max(1, int(1.5 * scale))))
    img.alpha_composite(cl)

    return img


if __name__ == "__main__":
    for sz, name in [(1024, "1024"), (512, "512"), (280, "280"), (64, "64"), (32, "32")]:
        logo = generate_mycelium_logo(1024, dark_mode=True)
        if sz != 1024:
            logo = logo.resize((sz, sz), Image.LANCZOS)
        logo.save(OUT_DIR / f"logo_dark_{name}.png")

    generate_mycelium_logo(1024, False).resize((512, 512), Image.LANCZOS).save(OUT_DIR / "logo_light_512.png")

    # Social preview: pure organism, no text
    social = Image.new('RGBA', (1280, 640), (12, 15, 20, 255))
    logo_sp = generate_mycelium_logo(600, dark_mode=True)
    social.paste(logo_sp, (340, 20), logo_sp)
    social.save(OUT_DIR / "social_preview.png")

    print("Generated v9 devouring+evolving mycelium:")
    for f in sorted(OUT_DIR.glob("logo_*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
    print(f"   social_preview.png ({(OUT_DIR / 'social_preview.png').stat().st_size // 1024}KB)")
