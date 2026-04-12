"""Myco logo v3 — Devouring Spiral: spiral growth + open core + asymmetric burst."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path

FONTS_DIR = Path(r"C:\Users\10350\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\1fa6c297-5df4-4be7-97fe-2df0766e7550\6ed041c6-b471-4d81-8a07-040da4c12a25\skills\canvas-design\canvas-fonts")
OUT_DIR = Path(__file__).parent

MYCO_GREEN = (0, 229, 176)
MYCO_DARK_GREEN = (0, 135, 94)
WHITE = (255, 255, 255)


def bezier_cubic(t, p0, p1, p2, p3):
    """Cubic bezier."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1],
    )


def draw_tapered_curve_cubic(img, p0, p1, p2, p3, color, max_w, min_w,
                              a_start=220, a_end=60, steps=100):
    """Smooth tapered cubic bezier with alpha gradient."""
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        x0, y0 = bezier_cubic(t0, p0, p1, p2, p3)
        x1, y1 = bezier_cubic(t1, p0, p1, p2, p3)
        w = max_w + (min_w - max_w) * t0
        a = int(a_start + (a_end - a_start) * t0)
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer, 'RGBA')
        ld.line([(x0, y0), (x1, y1)], fill=(*color, a), width=max(1, round(w)))
        img.alpha_composite(layer)


def soft_glow(img, cx, cy, r, color, alpha, blur=0.7):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, 'RGBA')
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(1, int(r * blur))))
    img.alpha_composite(layer)


def soft_dot(img, cx, cy, r, color, alpha, blur=0):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, 'RGBA')
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*color, alpha))
    if blur > 0:
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    img.alpha_composite(layer)


def draw_arc_segment(img, cx, cy, r, color, start_angle, end_angle, width, alpha):
    """Draw an arc (part of a circle) — for the open core."""
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, 'RGBA')
    bbox = [cx - r, cy - r, cx + r, cy + r]
    d.arc(bbox, start_angle, end_angle, fill=(*color, alpha), width=width)
    img.alpha_composite(layer)


def generate_logo(size=512, dark_mode=True):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    color = MYCO_GREEN if dark_mode else MYCO_DARK_GREEN
    cx, cy = size * 0.48, size * 0.50  # slightly left of center (asymmetric)
    s = size / 100

    # === Ambient glow (bioluminescent aura) ===
    soft_glow(img, int(cx), int(cy), int(28*s), color, 8, blur=1.2)
    soft_glow(img, int(cx), int(cy), int(16*s), color, 16, blur=0.8)

    # === FILAMENT A: The Devouring Spiral (longest, curves upward-right in a spiral arc) ===
    # This is the dominant arm — it's mid-lunge, reaching for the next thing to consume
    a_p0 = (cx, cy)
    a_p1 = (cx + 12*s, cy - 20*s)   # pulls upward
    a_p2 = (cx + 28*s, cy - 28*s)   # continues sweeping
    a_p3 = (cx + 38*s, cy - 18*s)   # curves back inward (spiral motion)
    draw_tapered_curve_cubic(img, a_p0, a_p1, a_p2, a_p3, color,
                              max_w=3.2*s, min_w=0.8*s, a_start=230, a_end=90)
    soft_dot(img, int(a_p3[0]), int(a_p3[1]), int(4.5*s), color, 200, blur=2)
    # Glow at the tip (it just consumed something — brightest point after core)
    soft_glow(img, int(a_p3[0]), int(a_p3[1]), int(6*s), color, 30, blur=0.6)

    # Branch from spiral arm (secondary growth — evolution evidence)
    br_start_t = 0.6
    brx, bry = bezier_cubic(br_start_t, a_p0, a_p1, a_p2, a_p3)
    br_p0 = (brx, bry)
    br_p1 = (brx + 8*s, bry - 12*s)
    br_p2 = (brx + 14*s, bry - 18*s)
    br_p3 = (brx + 16*s, bry - 28*s)
    draw_tapered_curve_cubic(img, br_p0, br_p1, br_p2, br_p3, color,
                              max_w=1.6*s, min_w=0.4*s, a_start=150, a_end=40)
    soft_dot(img, int(br_p3[0]), int(br_p3[1]), int(2.8*s), color, 120, blur=1)

    # === FILAMENT B: Downward reach (shorter, still growing) ===
    b_p0 = (cx, cy)
    b_p1 = (cx + 6*s, cy + 14*s)
    b_p2 = (cx + 16*s, cy + 24*s)
    b_p3 = (cx + 24*s, cy + 30*s)
    draw_tapered_curve_cubic(img, b_p0, b_p1, b_p2, b_p3, color,
                              max_w=2.6*s, min_w=0.7*s, a_start=200, a_end=70)
    soft_dot(img, int(b_p3[0]), int(b_p3[1]), int(3.5*s), color, 170, blur=1)

    # === FILAMENT C: Left tendril (thinnest, youngest — just sprouted) ===
    c_p0 = (cx, cy)
    c_p1 = (cx - 10*s, cy + 4*s)
    c_p2 = (cx - 22*s, cy - 2*s)
    c_p3 = (cx - 30*s, cy - 8*s)
    draw_tapered_curve_cubic(img, c_p0, c_p1, c_p2, c_p3, color,
                              max_w=2.0*s, min_w=0.5*s, a_start=170, a_end=55)
    soft_dot(img, int(c_p3[0]), int(c_p3[1]), int(2.8*s), color, 140, blur=1)

    # === CENTRAL CORE: Open ring (devouring — has a gap/mouth) ===
    # The gap faces upper-right toward the spiral arm (the direction of consumption)
    core_r = int(7*s)

    # Glow behind core
    soft_glow(img, int(cx), int(cy), int(10*s), color, 50, blur=0.5)

    # Draw open ring (arc with gap)
    # Gap from about -30 to 30 degrees (upper-right opening)
    draw_arc_segment(img, int(cx), int(cy), core_r, color,
                     start_angle=40, end_angle=340, width=max(2, int(2.8*s)), alpha=230)

    # Inner bright spot (the digestive fire)
    soft_dot(img, int(cx), int(cy), int(3*s), WHITE, 220)
    # Tiny glow on the inner spot
    soft_glow(img, int(cx), int(cy), int(4*s), WHITE, 40, blur=0.4)

    return img


def generate_with_wordmark(size=512, dark_mode=True):
    total_h = int(size * 1.22)
    canvas = Image.new('RGBA', (size, total_h), (0, 0, 0, 0))
    logo = generate_logo(size, dark_mode)
    canvas.paste(logo, (0, 0), logo)

    draw = ImageDraw.Draw(canvas, 'RGBA')
    color = MYCO_GREEN if dark_mode else MYCO_DARK_GREEN
    try:
        font = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), int(size * 0.065))
    except Exception:
        font = ImageFont.load_default()

    text = "m y c o"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (size - tw) // 2
    ty = size + int(size * 0.03)
    draw.text((tx, ty), text, fill=(*color, 170), font=font)
    return canvas


if __name__ == "__main__":
    # Icon variants
    for sz, name in [(512, "512"), (280, "280"), (64, "64"), (32, "32")]:
        logo = generate_logo(512, dark_mode=True)
        if sz != 512:
            logo = logo.resize((sz, sz), Image.LANCZOS)
        logo.save(OUT_DIR / f"logo_dark_{name}.png")

    generate_logo(512, False).save(OUT_DIR / "logo_light_512.png")
    generate_logo(512, True).save(OUT_DIR / "logo_transparent_512.png")

    # Wordmark
    generate_with_wordmark(512, True).save(OUT_DIR / "myco_full_dark.png")
    generate_with_wordmark(512, False).save(OUT_DIR / "myco_full_light.png")

    # Social preview 1280x640
    social = Image.new('RGBA', (1280, 640), (12, 15, 20, 255))
    logo_sp = generate_logo(420, True)
    social.paste(logo_sp, (430, 40), logo_sp)
    draw = ImageDraw.Draw(social, 'RGBA')
    try:
        font = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), 38)
        small = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), 15)
    except Exception:
        font = small = ImageFont.load_default()

    text = "m y c o"
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((1280 - (bbox[2]-bbox[0])) // 2, 485), text, fill=(0, 229, 176, 180), font=font)

    tag = "devour everything. evolve forever. you just talk."
    bbox2 = draw.textbbox((0, 0), tag, font=small)
    draw.text(((1280 - (bbox2[2]-bbox2[0])) // 2, 540), tag, fill=(0, 229, 176, 90), font=small)

    social.save(OUT_DIR / "social_preview.png")

    print("Generated all logo v3 variants:")
    for f in sorted(OUT_DIR.glob("logo_*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
    for f in sorted(OUT_DIR.glob("myco_*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
    print(f"   social_preview.png ({(OUT_DIR / 'social_preview.png').stat().st_size // 1024}KB)")
