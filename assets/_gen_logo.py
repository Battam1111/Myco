"""Generate Myco logo v2 — Bioluminescent Metabolism, refined."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path

FONTS_DIR = Path(r"C:\Users\10350\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\1fa6c297-5df4-4be7-97fe-2df0766e7550\6ed041c6-b471-4d81-8a07-040da4c12a25\skills\canvas-design\canvas-fonts")
OUT_DIR = Path(__file__).parent

MYCO_GREEN = (0, 229, 176)
MYCO_DARK_GREEN = (0, 135, 94)
WHITE = (255, 255, 255)


def bezier_point(t, p0, p1, p2):
    """Quadratic bezier at parameter t."""
    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
    return x, y


def draw_tapered_curve(img, p0, ctrl, p2, color, max_width, min_width,
                       alpha_start=210, alpha_end=80, steps=80):
    """Draw a smooth tapered bezier curve with opacity gradient."""
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        x0, y0 = bezier_point(t0, p0, ctrl, p2)
        x1, y1 = bezier_point(t1, p0, ctrl, p2)
        # Taper width
        w = max_width + (min_width - max_width) * t0
        # Opacity gradient
        a = int(alpha_start + (alpha_end - alpha_start) * t0)
        # Draw on a temp layer for clean alpha
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer, 'RGBA')
        ld.line([(x0, y0), (x1, y1)], fill=(*color, a), width=max(1, round(w)))
        img.alpha_composite(layer)


def soft_glow(img, cx, cy, radius, color, peak_alpha, blur_factor=0.7):
    """Soft gaussian glow."""
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, 'RGBA')
    d.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
              fill=(*color, peak_alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=int(radius * blur_factor)))
    img.alpha_composite(layer)


def soft_dot(img, cx, cy, radius, color, alpha, blur=0):
    """Crisp or slightly soft terminal dot."""
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, 'RGBA')
    d.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
              fill=(*color, alpha))
    if blur > 0:
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    img.alpha_composite(layer)


def generate_logo(size=512, dark_mode=True):
    """Generate refined Myco logo."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    color = MYCO_GREEN if dark_mode else MYCO_DARK_GREEN
    cx, cy = size / 2, size / 2
    s = size / 100  # scale

    # === Ambient glow (very soft, large) ===
    soft_glow(img, int(cx), int(cy), int(25*s), color, 10, blur_factor=1.0)
    soft_glow(img, int(cx), int(cy), int(16*s), color, 18, blur_factor=0.8)

    # === Filament A: upper-right (longest, with branch) ===
    a_end = (cx + 30*s, cy - 26*s)
    a_ctrl = (cx + 18*s, cy - 18*s + 5*s)  # slight organic bend
    draw_tapered_curve(img, (cx, cy), a_ctrl, a_end, color,
                       max_width=2.8*s, min_width=1.0*s, alpha_start=200, alpha_end=90)
    soft_dot(img, int(a_end[0]), int(a_end[1]), int(3.8*s), color, 190, blur=1)

    # Branch A1
    branch_t = 0.55  # branch starts at 55% along filament A
    bx, by = bezier_point(branch_t, (cx, cy), a_ctrl, a_end)
    b1_end = (cx + 36*s, cy - 38*s)
    b1_ctrl = (bx + 6*s, by - 8*s)
    draw_tapered_curve(img, (bx, by), b1_ctrl, b1_end, color,
                       max_width=1.6*s, min_width=0.6*s, alpha_start=140, alpha_end=50)
    soft_dot(img, int(b1_end[0]), int(b1_end[1]), int(2.5*s), color, 120, blur=1)

    # === Filament B: lower-right ===
    b_end = (cx + 26*s, cy + 28*s)
    b_ctrl = (cx + 16*s, cy + 10*s - 4*s)
    draw_tapered_curve(img, (cx, cy), b_ctrl, b_end, color,
                       max_width=2.4*s, min_width=0.9*s, alpha_start=185, alpha_end=80)
    soft_dot(img, int(b_end[0]), int(b_end[1]), int(3.2*s), color, 170, blur=1)

    # === Filament C: left ===
    c_end = (cx - 32*s, cy - 4*s)
    c_ctrl = (cx - 14*s, cy + 8*s)
    draw_tapered_curve(img, (cx, cy), c_ctrl, c_end, color,
                       max_width=2.4*s, min_width=0.9*s, alpha_start=175, alpha_end=75)
    soft_dot(img, int(c_end[0]), int(c_end[1]), int(3.0*s), color, 160, blur=1)

    # === Central core ===
    # Glow halo
    soft_glow(img, int(cx), int(cy), int(8*s), color, 60, blur_factor=0.5)
    # Teal ring
    soft_dot(img, int(cx), int(cy), int(6.5*s), color, 230)
    # White hot center
    soft_dot(img, int(cx), int(cy), int(3.2*s), WHITE, 245)

    return img


def generate_with_wordmark(size=512, dark_mode=True):
    """Generate logo with 'myco' wordmark below."""
    total_h = int(size * 1.25)
    canvas = Image.new('RGBA', (size, total_h), (0, 0, 0, 0))
    logo = generate_logo(size, dark_mode)
    canvas.paste(logo, (0, 0), logo)

    draw = ImageDraw.Draw(canvas, 'RGBA')
    color = MYCO_GREEN if dark_mode else MYCO_DARK_GREEN

    try:
        font = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), int(size * 0.07))
    except Exception:
        font = ImageFont.load_default()

    text = "m y c o"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (size - tw) // 2
    ty = size + int(size * 0.04)
    draw.text((tx, ty), text, fill=(*color, 180), font=font)
    return canvas


def generate_on_background(size=512, dark_mode=True):
    """Generate logo on solid background for social preview."""
    bg_color = (12, 15, 20, 255) if dark_mode else (250, 251, 252, 255)
    canvas = Image.new('RGBA', (size, size), bg_color)
    logo = generate_logo(int(size * 0.7), dark_mode)
    offset = (size - logo.width) // 2
    canvas.paste(logo, (offset, offset), logo)
    return canvas


if __name__ == "__main__":
    # Icon only (transparent, for README)
    for sz, name in [(512, "512"), (280, "280"), (64, "64"), (32, "32")]:
        logo = generate_logo(512, dark_mode=True)
        if sz != 512:
            logo = logo.resize((sz, sz), Image.LANCZOS)
        logo.save(OUT_DIR / f"logo_dark_{name}.png")

    logo_light = generate_logo(512, dark_mode=False)
    logo_light.save(OUT_DIR / "logo_light_512.png")

    # Transparent background (for general use)
    generate_logo(512, True).save(OUT_DIR / "logo_transparent_512.png")

    # With wordmark
    generate_with_wordmark(512, True).save(OUT_DIR / "myco_full_dark.png")
    generate_with_wordmark(512, False).save(OUT_DIR / "myco_full_light.png")

    # Social preview (on background)
    sp = generate_on_background(1280, True)
    # Make it 1280x640 for GitHub social preview
    social = Image.new('RGBA', (1280, 640), (12, 15, 20, 255))
    logo_for_social = generate_logo(400, True)
    social.paste(logo_for_social, (440, 60), logo_for_social)
    # Add wordmark
    draw = ImageDraw.Draw(social, 'RGBA')
    try:
        font = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), 36)
    except Exception:
        font = ImageFont.load_default()
    text = "m y c o"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((1280 - tw) // 2, 480), text, fill=(0, 229, 176, 180), font=font)

    tagline_font = ImageFont.truetype(str(FONTS_DIR / "GeistMono-Regular.ttf"), 16)
    tag = "devour everything. evolve forever. you just talk."
    bbox2 = draw.textbbox((0, 0), tag, font=tagline_font)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((1280 - tw2) // 2, 530), tag, fill=(0, 229, 176, 100), font=tagline_font)

    social.save(OUT_DIR / "social_preview.png")

    print("Generated all logo variants:")
    for f in sorted(OUT_DIR.glob("*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024}KB)")
