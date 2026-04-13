"""Myco Logo v11 — Vivid Mycelium: sharp lines, dense network, strong colors."""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

OUT_DIR = Path(__file__).parent
random.seed(42)


def lerp_color(c1, c2, t):
    """Interpolate between two RGB tuples."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def generate_mycelium_logo(size=1024, dark_mode=True, pad=0.08):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Color gradient: vivid core → mid → edge
    if dark_mode:
        core_color = (220, 255, 245)    # Near-white (hottest, like a star core)
        mid_color = (0, 220, 170)       # Vibrant Myco green
        edge_color = (0, 80, 80)        # Deep dark teal (cool)
        opacity_init = 240
        opacity_decay = 0.84
        branch_opacity_mult = 0.6
        sub_opacity_mult = 0.4
        fine_opacity_mult = 0.25
        alpha_floor = 6
    else:
        # Strong dark colors for white backgrounds
        core_color = (0, 60, 50)        # Very dark green-black (core is densest)
        mid_color = (0, 140, 100)       # Mid green
        edge_color = (80, 190, 160)     # Lighter teal-cyan (edges fade lighter)
        opacity_init = 255              # Full opacity start
        opacity_decay = 0.92            # Very slow decay
        branch_opacity_mult = 0.80      # Branches highly visible
        sub_opacity_mult = 0.60
        fine_opacity_mult = 0.40
        alpha_floor = 50                # Minimum alpha — nothing invisible

    cx, cy = size * 0.5, size * 0.5
    max_r = size * (0.5 - pad)
    scale = size / 512

    segments = []
    dots = []
    growth_tips = []

    def get_color(dist_ratio):
        """Color based on distance from center."""
        if dist_ratio < 0.3:
            return lerp_color(core_color, mid_color, dist_ratio / 0.3)
        else:
            t = min(1.0, (dist_ratio - 0.3) / 0.7)
            return lerp_color(mid_color, edge_color, t)

    def grow(x, y, angle, length, width, opacity, depth, max_depth):
        if depth > max_depth or length < 1.0 or width < 0.15 or opacity < 5:
            return

        angle += random.gauss(0, 0.12)
        ex = x + math.cos(angle) * length
        ey = y + math.sin(angle) * length

        dist = math.sqrt((ex - cx)**2 + (ey - cy)**2)
        if dist > max_r * 1.05:
            return

        dist_ratio = dist / max_r
        # Sharper edge fade — maintains density longer, then cuts hard
        edge_fade = max(0.08, 1.0 - dist_ratio ** 2.5)
        alpha = max(alpha_floor, int(opacity * edge_fade))

        color = get_color(dist_ratio)
        segments.append((x, y, ex, ey, width, alpha, depth, color))

        # Growth glow at active tips (smaller, sharper)
        if depth >= max_depth - 2 and alpha > 30:
            growth_tips.append((ex, ey, width * 1.5, int(alpha * 0.5), color))

        if depth >= max_depth - 1 or (random.random() < 0.35 and depth > 2):
            dots.append((ex, ey, width * 1.0, alpha, color))

        # Main continuation
        grow(ex, ey, angle + random.gauss(0, 0.07),
             length * random.uniform(0.76, 0.89),
             width * random.uniform(0.84, 0.93),
             opacity * opacity_decay, depth + 1, max_depth)

        # Primary branch
        if random.random() < 0.65 and depth < max_depth - 1:
            side = angle + random.choice([-1, 1]) * random.uniform(0.3, 0.75)
            grow(ex, ey, side,
                 length * random.uniform(0.5, 0.7),
                 width * random.uniform(0.5, 0.7),
                 opacity * branch_opacity_mult, depth + 1, max_depth)

        # Secondary branch
        if random.random() < 0.35 and depth < max_depth - 2:
            side2 = angle + random.choice([-1, 1]) * random.uniform(0.45, 0.95)
            grow(ex, ey, side2,
                 length * random.uniform(0.35, 0.55),
                 width * random.uniform(0.35, 0.55),
                 opacity * sub_opacity_mult, depth + 1, max_depth)

        # Fine detail
        if random.random() < 0.18 and depth < max_depth - 3:
            side3 = angle + random.choice([-1, 1]) * random.uniform(0.5, 1.2)
            grow(ex, ey, side3,
                 length * random.uniform(0.2, 0.4),
                 width * random.uniform(0.2, 0.4),
                 opacity * fine_opacity_mult, depth + 1, max_depth)

    # === 12 primary hyphae — evenly spaced, slight organic jitter ===
    for i in range(12):
        base_angle = (2 * math.pi * i / 12) + random.gauss(0, 0.1)
        init_len = random.uniform(45, 60) * scale
        init_w = random.uniform(3.8, 5.5) * scale
        grow(cx, cy, base_angle, init_len, init_w, opacity_init, 0, 9)

    # === Anastomosis (cross-connections for network feel) ===
    tips_list = [(s[2], s[3], s[6], s[5]) for s in segments if s[6] >= 3]
    anastomosis = []
    for i in range(len(tips_list)):
        x1, y1, d1, a1 = tips_list[i]
        for j in range(i+1, min(i+60, len(tips_list))):
            x2, y2, d2, a2 = tips_list[j]
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            if 5*scale < dist < 28*scale and abs(d1-d2) <= 2 and random.random() < 0.10:
                a = max(alpha_floor, int(25 * max(0.2, 1.0 - dist/(28*scale))))
                dr = math.sqrt(((x1+x2)/2-cx)**2 + ((y1+y2)/2-cy)**2) / max_r
                c = get_color(dr)
                anastomosis.append((x1, y1, x2, y2, 0.7*scale, a, c))

    # === Converging spores (being devoured) ===
    spores = []
    for _ in range(25):
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(max_r*0.65, max_r*1.0)
        sx = cx + math.cos(angle)*dist
        sy = cy + math.sin(angle)*dist
        sr = random.uniform(0.5, 1.8)*scale
        sa = max(alpha_floor, int(random.uniform(15, 45)*(1.1 - dist/max_r)))
        dr = dist/max_r
        sc = get_color(dr)
        spores.append((sx, sy, sr, sa, sc))
        # Absorption trail
        if sa > 18:
            tl = random.uniform(6, 18)*scale
            atc = math.atan2(cy-sy, cx-sx)
            tx = sx + math.cos(atc)*tl
            ty = sy + math.sin(atc)*tl
            spores.append(('trail', sx, sy, tx, ty, 0.5*scale, int(sa*0.45), sc))

    # === DRAW ===
    draw = ImageDraw.Draw(img, 'RGBA')

    # Spore trails
    for s in spores:
        if s[0] == 'trail':
            _, x1, y1, x2, y2, w, a, c = s
            draw.line([(x1,y1),(x2,y2)], fill=(*c, a), width=max(1, round(w)))

    # Spore dots
    for s in spores:
        if s[0] != 'trail':
            sx, sy, sr, sa, sc = s
            draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=(*sc, sa))

    # Branches (deep first for proper layering)
    segments.sort(key=lambda s: -s[6])
    for (x1, y1, x2, y2, w, a, d, c) in segments:
        draw.line([(x1,y1),(x2,y2)], fill=(*c, min(255, a)), width=max(1, round(w)))

    # Anastomosis
    for (x1, y1, x2, y2, w, a, c) in anastomosis:
        draw.line([(x1,y1),(x2,y2)], fill=(*c, min(255, a)), width=max(1, round(w)))

    # Terminal dots
    for (x, y, r, a, c) in dots:
        r = max(0.6, r)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*c, min(255, a)))

    # Growth tip glows — MUCH smaller blur for sharpness
    for (gx, gy, gr, ga, gc) in growth_tips:
        gl = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl, 'RGBA')
        gr = max(1.5, gr)
        gd.ellipse([gx-gr, gy-gr, gx+gr, gy+gr], fill=(*gc, min(255, ga)))
        gl = gl.filter(ImageFilter.GaussianBlur(radius=max(1, int(gr*0.25))))
        img.alpha_composite(gl)

    # === Central glow — tighter, less blur ===
    if dark_mode:
        glow_layers = [(25*scale, core_color, 10), (15*scale, mid_color, 22), (8*scale, core_color, 40)]
    else:
        glow_layers = [(20*scale, mid_color, 15), (12*scale, core_color, 30), (6*scale, core_color, 55)]
    for gr, c, ga in glow_layers:
        glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, 'RGBA')
        gd.ellipse([cx-gr, cy-gr, cx+gr, cy+gr], fill=(*c, ga))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=int(gr*0.4)))
        img.alpha_composite(glow)

    # Open arc core
    draw = ImageDraw.Draw(img, 'RGBA')
    cr = int(6*scale)
    arc = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc, 'RGBA')
    arc_color = core_color if dark_mode else (0, 70, 50)
    ad.arc([int(cx-cr), int(cy-cr), int(cx+cr), int(cy+cr)],
           start=30, end=345, fill=(*arc_color, 240), width=max(2, int(2.5*scale)))
    img.alpha_composite(arc)

    # Center dot — white for dark mode, dark for light mode
    cl = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cl, 'RGBA')
    wr = int(2.5*scale)
    dot_color = (255, 255, 255, 240) if dark_mode else (0, 80, 60, 240)
    cd.ellipse([cx-wr, cy-wr, cx+wr, cy+wr], fill=dot_color)
    cl = cl.filter(ImageFilter.GaussianBlur(radius=max(1, int(0.8*scale))))
    img.alpha_composite(cl)

    return img


if __name__ == "__main__":
    # Render natively at each size for maximum sharpness
    for sz in [1024, 512, 280, 64, 32]:
        logo = generate_mycelium_logo(sz, dark_mode=True)
        logo.save(OUT_DIR / f"logo_dark_{sz}.png")

    for sz in [1024, 512, 280, 64]:
        logo = generate_mycelium_logo(sz, dark_mode=False)
        logo.save(OUT_DIR / f"logo_light_{sz}.png")

    # Social preview — white background with project name for GitHub OG
    from PIL import ImageFont
    social = Image.new('RGBA', (1280, 640), (255, 255, 255, 255))
    logo_sp = generate_mycelium_logo(420, dark_mode=False)
    social.paste(logo_sp, (430, 30), logo_sp)
    sd = ImageDraw.Draw(social, 'RGBA')
    # Project name below logo
    try:
        font_large = ImageFont.truetype("arial.ttf", 64)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    title_color = (0, 80, 60, 230)
    sub_color = (0, 120, 90, 180)
    # "Myco" centered
    bbox = sd.textbbox((0, 0), "Myco", font=font_large)
    tw = bbox[2] - bbox[0]
    sd.text(((1280 - tw) // 2, 470), "Myco", fill=title_color, font=font_large)
    # Tagline
    tagline = "Eternal Devouring. Eternal Evolution."
    bbox2 = sd.textbbox((0, 0), tagline, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    sd.text(((1280 - tw2) // 2, 550), tagline, fill=sub_color, font=font_small)
    social.save(OUT_DIR / "social_preview.png")

    print("Generated v11 vivid mycelium (native resolution):")
    for f in sorted(OUT_DIR.glob("logo_*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
    print(f"   social_preview.png ({(OUT_DIR / 'social_preview.png').stat().st_size // 1024}KB)")
