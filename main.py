"""SOLMARA — a vintage travel poster for a harbour town that does not exist.

Drawn entirely with PIL in flat shapes at twice size (1792x2048) and reduced
with LANCZOS to 896x1024, deterministically, to /output/entry.png.

A colossal natural stone arch strides across the bay of Solmara, a lighthouse
on its crown; on late-summer evenings the setting sun drops exactly through
the archway — the sun coming home through the gate.
"""

import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants
W, H = 896, 1024          # final canvas
SS = 2                    # supersample factor
SW, SH = W * SS, H * SS   # working canvas
SEED = 7

BORDER = 28               # paper-cream border, final px
HORIZON = 640             # sea line, final px
QUAY_TOP = 880            # harbour-quay baseline, final px
SUN_C = (448, 640)        # sun centre, final px
SUN_R = 118               # sun radius, final px

PAPER = (248, 240, 220)
NAVY = (26, 36, 64)
VERMILION = (178, 58, 28)
SUN_RED = (228, 84, 44)
SKY_TOP = (250, 231, 178)
SKY_MID = (246, 183, 107)
SKY_LOW = (240, 138, 90)
MAUVE = (122, 90, 110)
ROCK = (34, 42, 68)
ROCK_DARK = (24, 30, 50)
ROCK_LIGHT = (56, 68, 100)
SEA_TOP = (29, 110, 114)
SEA_LOW = (13, 62, 74)
REFLECT = (242, 165, 65)
SAIL = (247, 238, 216)
TOWER = (245, 238, 222)
BAND = (214, 69, 38)
QUAY = (18, 28, 48)
WINDOW_LIT = (255, 214, 130)
CLOUD = (252, 244, 214)
CLOUD_PEACH = (250, 214, 170)

SERIF_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
SANS_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def X(v):
    """Scale a final-pixel coordinate to the 2x working canvas."""
    return int(v * SS)


def lerp(a, b, t):
    return int(round(a + (b - a) * t))


def lerp_color(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def grad_color(stops, t):
    """Three-stop gradient colour: stops = [(0.0, c0), (0.5, c1), (1.0, c2)]."""
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1 or i == len(stops) - 2:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return lerp_color(c0, c1, max(0.0, min(1.0, f)))
    return stops[-1][1]


def vgrad(draw, x0, y0, x1, y1, stops):
    """Fill a rectangle with a vertical multi-stop gradient."""
    h = y1 - y0
    for yy in range(y0, y1):
        t = (yy - y0) / max(1, h - 1)
        draw.line([(x0, yy), (x1, yy)], fill=grad_color(stops, t))


def load_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def tracked_width(font, text, tracking):
    w = 0
    for ch in text:
        w += font.getlength(ch) + tracking
    return int(w - tracking) if text else 0


def draw_tracked(draw, cx, y, text, font, tracking, fill):
    """Draw tracked text centred on cx, top edge at y."""
    w = tracked_width(font, text, tracking)
    x = cx - w // 2
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += int(font.getlength(ch)) + tracking


# ------------------------------------------------------------------- sky/sun
def draw_sun(img, draw):
    cx, cy = X(SUN_C[0]), X(SUN_C[1])
    r = X(SUN_R)
    # two faint halo rings around the disc
    for rr, alpha in ((r + X(26), 46), (r + X(64), 26)):
        ring = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   outline=SUN_RED + (alpha,), width=X(4))
        img.alpha_composite(ring)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_RED)


def draw_clouds(draw, rng):
    # flat lozenge clouds: rounded bars in pale cream / peach
    clouds = [
        (118, 292, 186, 26, CLOUD),
        (648, 268, 152, 22, CLOUD),
        (688, 428, 172, 24, CLOUD_PEACH),
        (58, 468, 142, 22, CLOUD),
        (560, 336, 118, 18, CLOUD),
        (210, 392, 120, 18, CLOUD_PEACH),
    ]
    for x, y, w, h, col in clouds:
        draw.rounded_rectangle([X(x), X(y), X(x + w), X(y + h)],
                               radius=X(h // 2), fill=col)


def draw_headlands(draw):
    # low mauve headlands closing both sides of the bay at the horizon
    draw.polygon([(X(BORDER), X(HORIZON)), (X(BORDER), X(566)),
                  (X(196), X(584)), (X(318), X(612)), (X(352), X(HORIZON))],
                 fill=MAUVE)
    draw.polygon([(X(W - BORDER), X(HORIZON)), (X(W - BORDER), X(574)),
                  (X(706), X(590)), (X(592), X(616)), (X(556), X(HORIZON))],
                 fill=MAUVE)


def draw_sea(draw, rng):
    vgrad(draw, X(BORDER), X(HORIZON), X(W - BORDER), X(QUAY_TOP),
          [(0.0, SEA_TOP), (1.0, SEA_LOW)])
    # broken warm reflection column under the arch
    cx = X(448)
    for i in range(26):
        y = X(HORIZON) + i * X(9) + rng.randint(0, X(3))
        half = X(34) + rng.randint(-X(14), X(14)) - i * X(1)
        half = max(X(8), half)
        draw.rectangle([cx - half, y, cx + half, y + X(4)], fill=REFLECT)
    # pale flecks scattered on the water
    for _ in range(60):
        fx = rng.randint(X(70), X(W - 70))
        fy = rng.randint(X(HORIZON + 12), X(QUAY_TOP - 16))
        fw = rng.randint(X(8), X(30))
        draw.line([(fx, fy), (fx + fw, fy)], fill=(150, 196, 188), width=X(2))


# ------------------------------------------------------------------ arch
def draw_arch(img, rng):
    arch = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arch)
    # outer mass: crown ellipse + two pillars down into the sea
    ad.ellipse([X(238), X(238), X(658), X(620)], fill=ROCK + (255,))
    ad.rectangle([X(238), X(420), X(362), X(700)], fill=ROCK + (255,))
    ad.rectangle([X(534), X(420), X(658), X(700)], fill=ROCK + (255,))
    # strata: short dashed segments, like bedding planes in the rock face
    for yy in range(272, 700, 46):
        nseg = rng.randint(3, 5)
        for _ in range(nseg):
            sx = rng.randint(X(244), X(600))
            sw = rng.randint(X(18), X(60))
            ad.line([(sx, X(yy)), (sx + sw, X(yy))],
                    fill=ROCK_LIGHT + (30,), width=X(2))
    for _ in range(150):
        sx = rng.randint(X(240), X(656))
        sy = rng.randint(X(240), X(690))
        col = ROCK_LIGHT + (90,) if rng.random() < 0.5 else ROCK_DARK + (110,)
        ad.ellipse([sx, sy, sx + X(3), sy + X(2)], fill=col)
    # lit rim along the crown's outer curve
    ad.arc([X(238), X(238), X(658), X(620)], start=195, end=345,
           fill=ROCK_LIGHT + (255,), width=X(7))
    # punch the archway out of the alpha channel: rectangle + semicircular top
    hole = Image.new("L", (SW, SH), 0)
    hd = ImageDraw.Draw(hole)
    hd.rectangle([X(362), X(450), X(534), X(700)], fill=255)
    hd.ellipse([X(362), X(364), X(534), X(536)], fill=255)
    alpha = ImageChops.subtract(arch.split()[3], hole)
    arch.putalpha(alpha)
    img.paste(arch, (0, 0), arch)
    # inner-edge shading, drawn just inside the rock beside the opening
    d = ImageDraw.Draw(img)
    d.arc([X(368), X(370), X(528), X(530)], start=180, end=360,
          fill=ROCK_DARK, width=X(6))
    d.line([(X(366), X(452)), (X(366), X(696))], fill=ROCK_DARK, width=X(5))
    d.line([(X(530), X(452)), (X(530), X(696))], fill=ROCK_DARK, width=X(5))
    # dark foot of each pillar where it meets the sea
    d.rectangle([X(238), X(668), X(362), X(700)], fill=ROCK_DARK)
    d.rectangle([X(534), X(668), X(658), X(700)], fill=ROCK_DARK)


def draw_lighthouse(img):
    cx = X(448)
    base_y, top_y = X(238), X(238 - 74)
    glow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    # one soft translucent beam, up and to the right from the lamp
    gd.polygon([(cx + X(2), top_y - X(20)), (X(700), X(22)),
                (X(764), X(78)), (cx + X(12), top_y - X(4))],
               fill=(255, 210, 110, 170))
    # glowing lamp halo
    gd.ellipse([cx - X(26), top_y - X(44), cx + X(26), top_y + X(8)],
               fill=(255, 226, 150, 110))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    # tapered white tower
    d.polygon([(cx - X(17), base_y), (cx - X(11), top_y),
               (cx + X(11), top_y), (cx + X(17), base_y)], fill=TOWER)
    # two vermilion bands, widths interpolated along the taper
    for y0, y1 in ((X(190), X(200)), (X(214), X(224))):
        t0 = (base_y - y0) / (base_y - top_y)
        t1 = (base_y - y1) / (base_y - top_y)
        hw0 = X(17) - t0 * X(6)
        hw1 = X(17) - t1 * X(6)
        d.polygon([(cx - hw0, y0), (cx + hw0, y0),
                   (cx + hw1, y1), (cx - hw1, y1)], fill=BAND)
    # gallery, lamp, dark cap
    d.rectangle([cx - X(15), top_y - X(8), cx + X(15), top_y], fill=ROCK_DARK)
    d.ellipse([cx - X(9), top_y - X(26), cx + X(9), top_y - X(8)],
              fill=(255, 236, 170))
    d.polygon([(cx - X(12), top_y - X(26)), (cx + X(12), top_y - X(26)),
               (cx + X(6), top_y - X(40)), (cx - X(6), top_y - X(40))],
              fill=ROCK_DARK)


def draw_boats(draw):
    # two sailboats with cream sails on the bay
    for bx, by, s in ((296, 726, 1.0), (618, 768, 0.8)):
        x, y = X(bx), X(by)
        h = int(X(46) * s)
        w = int(X(30) * s)
        draw.polygon([(x - w, y), (x + w, y), (x + int(w * 0.7), y + X(12)),
                      (x - int(w * 0.7), y + X(12))], fill=ROCK_DARK)
        draw.line([(x, y), (x, y - h)], fill=ROCK_DARK, width=X(3))
        draw.polygon([(x + X(3), y - h), (x + X(3), y - X(6)),
                      (x + int(w * 0.9), y - X(6))], fill=SAIL)
        draw.polygon([(x - X(3), y - h), (x - X(3), y - X(6)),
                      (x - int(w * 0.6), y - X(6))], fill=SAIL)


def draw_quay(draw, rng):
    base = X(QUAY_TOP)
    bottom = X(H - BORDER)
    # quay front wall
    draw.rectangle([X(BORDER), base, X(W - BORDER), bottom], fill=QUAY)
    # harbour rooftops: a run of houses, chimneys and one spire
    buildings = [
        (56, 128, 806), (132, 210, 824), (214, 268, 792), (272, 348, 818),
        (352, 428, 800), (432, 512, 828), (516, 596, 796), (600, 668, 822),
        (672, 742, 808), (746, 824, 830), (828, 868, 812),
    ]
    for x0, x1, top in buildings:
        draw.rectangle([X(x0), X(top), X(x1), base], fill=QUAY)
        draw.polygon([(X(x0 - 4), X(top)), (X((x0 + x1) // 2), X(top - 22)),
                      (X(x1 + 4), X(top))], fill=QUAY)
    # chimneys on a few roofs
    for cx0, cy0 in ((150, 786), (380, 780), (640, 800), (770, 812)):
        draw.rectangle([X(cx0), X(cy0), X(cx0 + 10), X(cy0 + 26)], fill=QUAY)
    # one spire rising above the roofs
    draw.polygon([(X(700), X(822)), (X(712), X(700)), (X(724), X(822))],
                 fill=QUAY)
    draw.line([(X(712), X(688)), (X(712), X(700))], fill=QUAY, width=X(3))
    # ~46 lit windows, seeded
    lit = 0
    tries = 0
    while lit < 46 and tries < 600:
        tries += 1
        x0, x1, top = buildings[rng.randrange(len(buildings))]
        wx = rng.randint(x0 + 10, x1 - 16)
        wy = rng.randint(top + 12, QUAY_TOP - 16)
        draw.rectangle([X(wx), X(wy), X(wx + 7), X(wy + 10)], fill=WINDOW_LIT)
        lit += 1
    # 4 moored masts above the quay line
    for mx in (180, 330, 560, 800):
        draw.line([(X(mx), base), (X(mx), X(QUAY_TOP - 84))],
                  fill=QUAY, width=X(3))
        draw.line([(X(mx - 16), X(QUAY_TOP - 66)), (X(mx + 16), X(QUAY_TOP - 66))],
                  fill=QUAY, width=X(2))


def draw_type(img, draw):
    # SOLMARA, tracked DejaVu Serif Bold caps, ~700px wide, navy.
    # Place by the glyph bbox so the caps sit just inside the border and
    # clear the descriptor line below them.
    font = load_font(SERIF_PATHS, X(110))
    tracking = X(12)
    tw = tracked_width(font, "SOLMARA", tracking)
    size = int(X(110) * X(700) / max(1, tw))
    font = load_font(SERIF_PATHS, size)
    tracking = max(X(4), size // 9)
    bbox = font.getbbox("SOLMARA")
    title_top = X(34) - bbox[1]
    draw_tracked(draw, X(448), title_top, "SOLMARA", font, tracking, NAVY)
    # descriptor in tracked Liberation Sans Bold vermilion, flanking rules
    dfont = load_font(SANS_PATHS, X(20))
    dtracking = X(3)
    text = "WHERE THE SUN COMES HOME THROUGH THE GATE"
    dw = tracked_width(dfont, text, dtracking)
    dy = X(132)
    draw_tracked(draw, X(448), dy, text, dfont, dtracking, VERMILION)
    rule_y = dy + X(10)
    gap = X(16)
    draw.line([(X(BORDER + 6), rule_y), (X(448) - dw // 2 - gap, rule_y)],
              fill=VERMILION, width=X(2))
    draw.line([(X(448) + dw // 2 + gap, rule_y), (X(W - BORDER - 6), rule_y)],
              fill=VERMILION, width=X(2))
    # paper-cream border + thin navy keyline
    draw.rectangle([0, 0, SW - 1, X(BORDER) - 1], fill=PAPER)
    draw.rectangle([0, SH - X(BORDER), SW - 1, SH - 1], fill=PAPER)
    draw.rectangle([0, 0, X(BORDER) - 1, SH - 1], fill=PAPER)
    draw.rectangle([SW - X(BORDER), 0, SW - 1, SH - 1], fill=PAPER)
    draw.rectangle([X(BORDER), X(BORDER), SW - X(BORDER) - 1,
                    SH - X(BORDER) - 1], outline=NAVY, width=X(2))


def add_grain(img, rng):
    # deterministic print grain from a small seeded tile, stretched over the
    # whole poster at low strength, then a gentle vignette
    tile = Image.new("L", (256, 256))
    tile.putdata([128 + rng.randint(-16, 16) for _ in range(256 * 256)])
    noise = tile.resize((SW, SH), Image.NEAREST)
    alpha = noise.point(lambda v: abs(v - 128) * 2)
    overlay = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
    overlay.putalpha(alpha)
    img.alpha_composite(overlay)
    d = ImageDraw.Draw(img)
    for i in range(28):
        inset = i * X(2)
        a = int(2 + i * 0.9)
        d.rectangle([inset, inset, SW - 1 - inset, SH - 1 - inset],
                    outline=(20, 16, 30, a), width=X(2))


# ------------------------------------------------------------------- render
def render():
    rng = random.Random(SEED)
    img = Image.new("RGBA", (SW, SH), PAPER + (255,))
    draw = ImageDraw.Draw(img)
    # sky: cream -> peach -> coral down to the horizon
    vgrad(draw, X(BORDER), X(BORDER), X(W - BORDER), X(HORIZON),
          [(0.0, SKY_TOP), (0.55, SKY_MID), (1.0, SKY_LOW)])
    draw_sun(img, draw)
    draw_clouds(draw, rng)
    draw_headlands(draw)
    draw_sea(draw, rng)
    draw_arch(img, rng)
    draw_lighthouse(img)
    draw_boats(draw)
    draw_quay(draw, rng)
    # three gull strokes, upper right
    for gx, gy, gs in ((688, 246, 10), (732, 276, 8), (664, 302, 7)):
        draw.line([(X(gx - gs), X(gy)), (X(gx), X(gy - 5)),
                   (X(gx + gs), X(gy))], fill=NAVY, width=X(2))
    draw_type(img, draw)
    add_grain(img, rng)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    poster = render()
    path = os.path.join(out_dir, "entry.png")
    poster.save(path, optimize=True)
    print("wrote", path, poster.size)


if __name__ == "__main__":
    main()
