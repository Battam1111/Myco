"""Myco Logo v8 — Dense Microscopic Mycelium with anastomosis."""
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
    cx, cy = size * 0.48, size * 0.50
    max_r = size * (0.5 - pad)
    scale = size / 512

    segments = []  # (x1, y1, x2, y2, width, alpha, depth)
    dots = []      # (x, y, radius, alpha)
    tips = []      # Track all tip positions for anastomosis

    def grow(x, y, angle, length, width, opacity, depth, max_depth):
        if depth > max_depth or length < 1.5 or width < 0.2 or opacity < 8:
            return

        # Organic bend
        angle += random.gauss(0, 0.18)
        ex = x + math.cos(angle) * length
        ey = y + math.sin(angle) * length

        # Boundary fade
        dist = math.sqrt((ex - cx)**2 + (ey - cy)**2)
        if dist > max_r * 1.15:
            return
        edge_fade = max(0.15, 1.0 - (dist / max_r) ** 1.3)
        alpha = int(opacity * edge_fade)

        segments.append((x, y, ex, ey, width, alpha, depth))
        tips.append((ex, ey, depth))

        # Terminal dot
        if depth >= max_depth - 1 or (random.random() < 0.25 and depth > 3):
            dots.append((ex, ey, width * 1.3, alpha))

        # Main continuation
        grow(ex, ey, angle + random.gauss(0, 0.08),
             length * random.uniform(0.72, 0.86),
             width * random.uniform(0.80, 0.90),
             opacity * 0.87, depth + 1, max_depth)

        # Primary branch (high probability)
        if random.random() < 0.6 and depth < max_depth - 1:
            side = angle + random.choice([-1, 1]) * random.uniform(0.35, 0.85)
            grow(ex, ey, side,
                 length * random.uniform(0.5, 0.7),
                 width * random.uniform(0.5, 0.7),
                 opacity * 0.65, depth + 1, max_depth)

        # Secondary branch (medium probability — adds density)
        if random.random() < 0.3 and depth < max_depth - 2:
            side2 = angle + random.choice([-1, 1]) * random.uniform(0.5, 1.1)
            grow(ex, ey, side2,
                 length * random.uniform(0.35, 0.55),
                 width * random.uniform(0.35, 0.55),
                 opacity * 0.45, depth + 1, max_depth)

        # Rare tertiary (creates fine detail)
        if random.random() < 0.12 and depth < max_depth - 3:
            side3 = angle + random.choice([-1, 1]) * random.uniform(0.7, 1.4)
            grow(ex, ey, side3,
                 length * random.uniform(0.25, 0.4),
                 width * random.uniform(0.25, 0.4),
                 opacity * 0.3, depth + 1, max_depth)

    # === Generate from center — 8 primary hyphae ===
    for i in range(8):
        base_angle = (2 * math.pi * i / 8) + random.gauss(0, 0.3)
        grow(cx, cy, base_angle,
             random.uniform(58, 78) * scale,
             random.uniform(3.8, 5.5) * scale,
             235, 0, 9)

    # === Anastomosis: connect nearby tips ===
    anastomosis = []
    for i, (x1, y1, d1) in enumerate(tips):
        for j, (x2, y2, d2) in enumerate(tips):
            if i >= j:
                continue
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            # Connect tips that are close but from different primary hyphae
            if 10 * scale < dist < 40 * scale and abs(d1 - d2) <= 2:
                if random.random() < 0.15:  # Sparse connections
                    alpha = int(40 * max(0.2, 1.0 - (dist / (40 * scale))))
                    w = 0.8 * scale
                    anastomosis.append((x1, y1, x2, y2, w, alpha))

    # === Draw everything ===
    # Layer 1: deep branches (behind)
    segments.sort(key=lambda s: -s[6])
    for (x1, y1, x2, y2, w, a, d) in segments:
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.line([(x1, y1), (x2, y2)], fill=(*color, min(255, a)), width=max(1, round(w)))

    # Layer 2: anastomosis connections (network feel)
    for (x1, y1, x2, y2, w, a) in anastomosis:
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.line([(x1, y1), (x2, y2)], fill=(*color, min(255, a)), width=max(1, round(w)))

    # Layer 3: terminal dots
    draw = ImageDraw.Draw(img, 'RGBA')
    for (x, y, r, a) in dots:
        r = max(0.8, r)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*color, min(255, a)))

    # === Floating spores (being consumed — approaching the organism) ===
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(max_r * 0.85, max_r * 1.05)
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        sr = random.uniform(0.8, 1.8) * scale
        sa = random.randint(15, 40)
        draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=(*color, sa))

    # === Central glow ===
    for gr, ga in [(30*scale, 20), (20*scale, 35), (12*scale, 55)]:
        glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, 'RGBA')
        gd.ellipse([cx-gr, cy-gr, cx+gr, cy+gr], fill=(*color, ga))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=int(gr * 0.6)))
        img.alpha_composite(glow)

    # Open arc core
    draw = ImageDraw.Draw(img, 'RGBA')
    core_r = int(8 * scale)
    arc_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc_img, 'RGBA')
    ad.arc([int(cx-core_r), int(cy-core_r), int(cx+core_r), int(cy+core_r)],
           start=35, end=335, fill=(*color, 240), width=max(2, int(3.5 * scale)))
    img.alpha_composite(arc_img)

    # White hot center
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

    # Social preview
    social = Image.new('RGBA', (1280, 640), (12, 15, 20, 255))
    logo_sp = generate_mycelium_logo(520, dark_mode=True)
    social.paste(logo_sp, (380, 10), logo_sp)
    try:
        from PIL import ImageFont
        fd = os.environ.get("MYCO_FONTS_DIR", "./fonts")
        font = ImageFont.truetype(os.path.join(fd, "GeistMono-Regular.ttf"), 38)
        small = ImageFont.truetype(os.path.join(fd, "GeistMono-Regular.ttf"), 15)
    except Exception:
        from PIL import ImageFont
        font = ImageFont.load_default()
        small = font
    sd = ImageDraw.Draw(social, 'RGBA')
    t = "m y c o"
    bb = sd.textbbox((0, 0), t, font=font)
    sd.text(((1280-(bb[2]-bb[0]))//2, 540), t, fill=(0, 229, 176, 180), font=font)
    tg = "devour everything. evolve forever. you just talk."
    bb2 = sd.textbbox((0, 0), tg, font=small)
    sd.text(((1280-(bb2[2]-bb2[0]))//2, 590), tg, fill=(0, 229, 176, 90), font=small)
    social.save(OUT_DIR / "social_preview.png")

    print("Generated v8 mycelium logo:")
    for f in sorted(OUT_DIR.glob("logo_*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
    print(f"   social_preview.png ({(OUT_DIR / 'social_preview.png').stat().st_size // 1024}KB)")
