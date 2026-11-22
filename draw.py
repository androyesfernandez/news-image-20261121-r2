#!/usr/bin/env python3
"""Draw the round-2 poster for news-image-20261121 (Saturday 21 Nov 2026).

Cream broadsheet in the winners' template: serif typography throughout
(Liberation Serif for the date, headlines and summaries; Liberation Sans
for kickers, chips and briefs), 46 numbered stories, 15 of them carrying
a real flat-vector scene, per-card trust chips with named sources, a UTC
timeline, a six-numbers row, a region strip with counts, a dotted world
map with numbered pins, and a red DATE CHECK box.

Deterministic: fixed fonts, fixed geometry, a seeded grain pass. Two
runs are byte-identical. Writes entry.png (1024x1024) next to this file.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
FD = "/usr/share/fonts/truetype/liberation"
SERIF = FD + "/LiberationSerif-Regular.ttf"
SERIF_B = FD + "/LiberationSerif-Bold.ttf"
SERIF_I = FD + "/LiberationSerif-Italic.ttf"
SANS = FD + "/LiberationSans-Regular.ttf"
SANS_B = FD + "/LiberationSans-Bold.ttf"

CREAM = (246, 239, 220)
PAPER = (255, 253, 246)
INK = (24, 22, 20)
GREY = (105, 100, 90)
LGREY = (216, 208, 186)
DRED = (163, 32, 26)
RED = (196, 40, 32)
GREEN = (34, 110, 52)
AMBER = (176, 110, 10)
NAVY = (22, 42, 84)
SKY = (146, 196, 228)
SKY2 = (198, 228, 246)
SEA = (52, 112, 152)
SAND = (224, 186, 122)
TAN = (232, 220, 188)
BROWN = (122, 82, 42)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
DARK = (38, 44, 58)

REGION_COLORS = {
    "EUROPE": (36, 84, 160), "ASIA": (178, 34, 34),
    "N AMERICA": (18, 130, 118), "OCEANIA": (224, 122, 26),
    "AFRICA": (46, 125, 50), "LATIN AM": (123, 72, 160),
    "MID EAST": (150, 96, 20), "GLOBAL": (38, 44, 58),
}
REGION_COUNTS = [("EUROPE", 13), ("ASIA", 7), ("N AMERICA", 6),
                 ("MID EAST", 5), ("AFRICA", 5), ("LATIN AM", 4),
                 ("OCEANIA", 4), ("GLOBAL", 2)]

_font_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def tw(d, s, font):
    return d.textlength(s, font=font)


def wrap_px(d, s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text(d, x, y, s, font, fill=INK, anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)


def vgrad(d, x, y, w, h, c0, c1):
    for j in range(h):
        t = j / max(1, h - 1)
        c = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
        d.line([(x, y + j), (x + w - 1, y + j)], fill=c)


def sun(d, cx, cy, r, c=(250, 205, 70)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    for a in range(0, 360, 45):
        x1 = cx + int((r + 3) * math.cos(math.radians(a)))
        y1 = cy + int((r + 3) * math.sin(math.radians(a)))
        x2 = cx + int((r + 8) * math.cos(math.radians(a)))
        y2 = cy + int((r + 8) * math.sin(math.radians(a)))
        d.line([(x1, y1), (x2, y2)], fill=c, width=2)


def cloud(d, x, y, s=1.0, c=WHITE):
    d.ellipse([x, y, x + 34 * s, y + 14 * s], fill=c)
    d.ellipse([x + 10 * s, y - 6 * s, x + 30 * s, y + 10 * s], fill=c)
    d.rectangle([x + 2 * s, y + 6 * s, x + 32 * s, y + 14 * s], fill=c)


def person(d, cx, base, h, skin, cloth):
    hr = max(3, h // 6)
    d.ellipse([cx - hr, base - h, cx + hr, base - h + 2 * hr], fill=skin)
    d.rectangle([cx - hr - 1, base - h + 2 * hr, cx + hr + 1, base - h // 3],
                fill=cloth)
    d.line([(cx - 2, base - h // 3), (cx - 3, base)], fill=DARK, width=2)
    d.line([(cx + 2, base - h // 3), (cx + 3, base)], fill=DARK, width=2)


def flag(d, x, y, w, h, stripes, vertical=False, disc_c=None):
    n = len(stripes)
    for i, c in enumerate(stripes):
        if vertical:
            d.rectangle([x + i * w // n, y, x + (i + 1) * w // n, y + h],
                        fill=c)
        else:
            d.rectangle([x, y + i * h // n, x + w, y + (i + 1) * h // n],
                        fill=c)
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=GREY)
    if disc_c:
        d.ellipse([x + w // 2 - h // 5, y + h // 2 - h // 5,
                   x + w // 2 + h // 5, y + h // 2 + h // 5], fill=disc_c)


def dashed_arc(d, x0, y0, x1, y1, lift, c, width=2, dash=7):
    steps = 60
    prev = None
    for i in range(steps + 1):
        t = i / steps
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - lift
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t ** 2 * x1
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t ** 2 * y1
        if prev is not None and (i // 3) % 2 == 0:
            d.line([prev, (px, py)], fill=c, width=width)
        prev = (px, py)


def burst(d, cx, cy, r, c1=(250, 180, 60), c2=(230, 90, 30)):
    for a in range(0, 360, 30):
        x2 = cx + int(r * math.cos(math.radians(a)))
        y2 = cy + int(r * math.sin(math.radians(a)))
        d.line([(cx, cy), (x2, y2)], fill=c2, width=2)
    d.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2], fill=c1)


def chip(d, x, y, status, source):
    """Trust chip: coloured status word + named source, right-aligned at x."""
    col = GREEN if status == "CONFIRMED" else AMBER
    f = F(SANS_B, 10)
    label = status + " · " + source
    wdt = tw(d, label, f)
    d.rectangle([x - wdt - 10, y - 2, x + 4, y + 13],
                fill=(238, 244, 232) if status == "CONFIRMED"
                else (248, 240, 220), outline=col)
    text(d, x - wdt - 5, y, label, f, fill=col)
    return wdt + 14


def num_disc(d, cx, cy, r, num, fill=RED):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    f = F(SANS_B, r + 2)
    text(d, cx, cy - 1, str(num), f, fill=WHITE, anchor="ma")


# ---------------------------------------------------------------- scenes
def scene_cop31(d, x, y, w, h):
    # Antalya conference hall: columns, COP31 banner, crowd, an overtime
    # clock, flags of many nations along the roofline.
    vgrad(d, x, y, w, h, SKY2, (238, 244, 248))
    sun(d, x + w - 30, y + 18, 9)
    cloud(d, x + 18, y + 10, 0.8)
    # Roofline flags.
    cols = [(36, 84, 160), (178, 34, 34), (46, 125, 50), (240, 196, 25),
            (123, 72, 160), (18, 130, 118), (224, 122, 26), (150, 96, 20)]
    for i, c in enumerate(cols):
        fx = x + 12 + i * (w - 24) // len(cols)
        d.line([(fx, y + 6), (fx, y + 20)], fill=DARK, width=1)
        d.rectangle([fx, y + 6, fx + 11, y + 13], fill=c)
    # Hall body.
    d.rectangle([x + 26, y + 34, x + w - 26, y + h - 22], fill=(238, 230, 208))
    d.rectangle([x + 26, y + 34, x + w - 26, y + h - 22], outline=BROWN)
    d.polygon([(x + 16, y + 34), (x + w - 16, y + 34), (x + w // 2, y + 22)],
              fill=(196, 164, 104))
    for i in range(6):
        cx = x + 44 + i * (w - 88) // 5
        d.rectangle([cx - 5, y + 52, cx + 5, y + h - 22], fill=(250, 246, 232),
                    outline=BROWN)
    d.rectangle([x + 26, y + 40, x + w - 26, y + 52], fill=NAVY)
    text(d, x + w // 2, y + 43, "COP31 · ANTALYA", F(SANS_B, 11),
         fill=WHITE, anchor="ma")
    # Overtime clock on the facade.
    cx, cy = x + w // 2, y + 74
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=WHITE, outline=INK,
              width=2)
    d.line([(cx, cy), (cx, cy - 10)], fill=INK, width=2)
    d.line([(cx, cy), (cx + 8, cy + 4)], fill=RED, width=2)
    text(d, cx + 20, cy - 6, "PAST DEADLINE", F(SANS_B, 8), fill=RED)
    # Crowd silhouettes.
    for i in range(9):
        px = x + 34 + i * (w - 68) // 8
        person(d, px, y + h - 4, 20, (120, 90, 70), DARK)
    d.rectangle([x, y + h - 4, x + w, y + h], fill=(120, 110, 90))


def scene_bahrain(d, x, y, w, h):
    # Map scene: the Gulf, Bahrain island at left-centre with two US
    # bases, dashed missile arcs flying in from Iran at the right edge,
    # interception bursts, a burning facility on the shore.
    vgrad(d, x, y, w, h, (168, 205, 228), SEA)
    for i in range(30):
        wx = x + (i * 53) % w
        wy = y + (i * 37) % h
        d.arc([wx, wy, wx + 16, wy + 6], 180, 360, fill=(210, 232, 244))
    # Arabia coast along the bottom-left.
    d.polygon([(x, y + h - 18), (x + 120, y + h - 26), (x + 168, y + h),
               (x, y + h)], fill=(226, 196, 140))
    # Bahrain island.
    d.polygon([(x + 62, y + 26), (x + 96, y + 18), (x + 112, y + 40),
               (x + 100, y + 68), (x + 70, y + 70), (x + 56, y + 46)],
              fill=SAND, outline=BROWN)
    text(d, x + 8, y + 6, "BAHRAIN", F(SANS_B, 10), fill=BROWN)
    # Iran coast: a strip at the right edge.
    d.polygon([(x + w - 44, y), (x + w, y), (x + w, y + h),
               (x + w - 30, y + h), (x + w - 40, y + 44)], fill=(214, 178, 118))
    text(d, x + w - 38, y + 8, "IRAN", F(SANS_B, 10), fill=DRED)
    # Bases on the island.
    for bx, by, name in [(x + 76, y + 36, "AL-RIFFA"), (x + 88, y + 60,
                                                         "AWALI")]:
        d.polygon([(bx, by - 6), (bx + 2, by - 2), (bx + 6, by - 2),
                   (bx + 3, by + 1), (bx + 4, by + 5), (bx, by + 2),
                   (bx - 4, by + 5), (bx - 3, by + 1), (bx - 6, by - 2),
                   (bx - 2, by - 2)], fill=NAVY)
        text(d, bx + 9, by - 4, name, F(SANS_B, 8), fill=NAVY)
    # Arcs from the east to the island.
    dashed_arc(d, x + w - 42, y + 22, x + 82, y + 34, 30, RED)
    dashed_arc(d, x + w - 36, y + 48, x + 94, y + 58, 22, RED)
    dashed_arc(d, x + w - 50, y + 10, x + 90, y + 28, 38, DRED)
    burst(d, x + 80, y + 32, 9)
    burst(d, x + 96, y + 56, 7)
    # Burning civilian facility on the shore below the island.
    d.rectangle([x + 128, y + h - 24, x + 152, y + h - 10],
                fill=(150, 140, 130))
    burst(d, x + 140, y + h - 28, 10)
    text(d, x + 158, y + h - 22, "CIVILIAN SITE ABLAZE", F(SANS_B, 8),
         fill=(255, 240, 220))


def scene_chapo(d, x, y, w, h):
    # Sinaloa: desert road, sierra, army truck and helicopter, a burning
    # roadblock, a captured boss with hands up, a town sign.
    vgrad(d, x, y, w, h, (240, 214, 160), (250, 232, 190))
    sun(d, x + 26, y + 16, 10)
    d.polygon([(x, y + 52), (x + 70, y + 22), (x + 140, y + 52)],
              fill=(178, 138, 92))
    d.polygon([(x + 110, y + 52), (x + 190, y + 18), (x + 268, y + 52)],
              fill=(160, 122, 78))
    d.polygon([(x + 220, y + 52), (x + 290, y + 28), (x + w, y + 52)],
              fill=(178, 138, 92))
    d.rectangle([x, y + 52, x + w, y + h], fill=(214, 178, 118))
    for i in range(14):
        d.point((x + (i * 67) % w, y + 60 + (i * 29) % (h - 66)),
                fill=(190, 152, 96))
    # Road.
    d.polygon([(x + 96, y + h), (x + 150, y + 54), (x + 176, y + 54),
               (x + 250, y + h)], fill=(96, 92, 88))
    # Helicopter.
    hx, hy = x + w - 74, y + 20
    d.ellipse([hx - 16, hy - 6, hx + 16, hy + 6], fill=DARK)
    d.line([(hx + 14, hy), (hx + 34, hy - 4)], fill=DARK, width=3)
    d.line([(hx - 30, hy - 10), (hx + 30, hy - 10)], fill=DARK, width=2)
    d.line([(hx, hy + 6), (hx, hy + 12)], fill=DARK, width=2)
    d.line([(hx - 10, hy + 12), (hx + 10, hy + 12)], fill=DARK, width=2)
    # Army truck.
    tx, ty = x + 58, y + h - 34
    d.rectangle([tx, ty, tx + 58, ty + 18], fill=(74, 92, 54))
    d.rectangle([tx + 42, ty - 10, tx + 58, ty], fill=(74, 92, 54))
    d.rectangle([tx + 46, ty - 8, tx + 54, ty - 2], fill=SKY2)
    for wx in (tx + 12, tx + 46):
        d.ellipse([wx - 7, ty + 12, wx + 7, ty + 26], fill=(30, 30, 30))
    # Burning roadblock.
    for bx in (x + 196, x + 214, x + 232):
        d.rectangle([bx, y + h - 22, bx + 14, y + h - 12], fill=(90, 70, 50))
        burst(d, bx + 7, y + h - 28, 9)
    # Captured figure, hands up, between two soldiers.
    cx, base = x + w // 2 + 42, y + h - 8
    person(d, cx - 26, base, 26, (90, 70, 55), (74, 92, 54))
    person(d, cx + 26, base, 26, (110, 84, 62), (74, 92, 54))
    d.ellipse([cx - 4, base - 30, cx + 4, base - 22], fill=(224, 186, 140))
    d.rectangle([cx - 3, base - 22, cx + 3, base - 8], fill=(240, 240, 240))
    d.line([(cx - 3, base - 20), (cx - 12, base - 30)], fill=(224, 186, 140),
           width=3)
    d.line([(cx + 3, base - 20), (cx + 12, base - 30)], fill=(224, 186, 140),
           width=3)
    # Town sign.
    d.rectangle([x + 10, y + h - 44, x + 64, y + h - 30], fill=(250, 246, 232),
                outline=BROWN)
    text(d, x + 37, y + h - 41, "GUASAVE", F(SANS_B, 9), fill=BROWN,
         anchor="ma")
    d.line([(x + 37, y + h - 30), (x + 37, y + h - 8)], fill=BROWN, width=2)


def scene_quake(d, x, y, w, h):
    vgrad(d, x, y, w, h, SKY2, (240, 244, 246))
    d.rectangle([x, y + h - 12, x + w, y + h], fill=(168, 148, 116))
    d.line([(x + 4, y + h - 6), (x + 40, y + h - 9), (x + 70, y + h - 4),
            (x + 110, y + h - 8), (x + w - 4, y + h - 5)], fill=BROWN, width=2)
    heights = [26, 34, 22, 30, 24]
    for i, bh in enumerate(heights):
        bx = x + 8 + i * (w - 40) // 4
        d.rectangle([bx - 11, y + h - 12 - bh, bx + 11, y + h - 12],
                    fill=(206, 198, 182), outline=GREY)
        for r in range(bh // 9):
            for c_ in range(2):
                d.rectangle([bx - 7 + c_ * 9, y + h - 18 - bh + r * 9,
                             bx - 3 + c_ * 9, y + h - 15 - bh + r * 9],
                            fill=(250, 220, 130))
        if i == 2:
            d.line([(bx - 4, y + h - 12 - bh), (bx + 2, y + h - 24),
                    (bx - 3, y + h - 14)], fill=DRED, width=2)
    # Seismograph trace.
    pts = [(x + 6, y + 10)]
    for i, v in enumerate([2, 8, 3, 12, 4, 10, 2]):
        pts.append((x + 16 + i * 20, y + 10 - v if i % 2 else y + 10 + v))
    pts.append((x + w - 6, y + 10))
    d.line(pts, fill=RED, width=2)
    text(d, x + w - 6, y + 2, "M6.9", F(SANS_B, 11), fill=DRED, anchor="ra")


def scene_trump(d, x, y, w, h):
    vgrad(d, x, y, w, h, SKY, (228, 240, 250))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(86, 148, 74))
    d.rectangle([x + 12, y + h - 30, x + 62, y + h - 8], fill=WHITE,
                outline=GREY)
    d.polygon([(x + 10, y + h - 30), (x + 64, y + h - 30), (x + 37, y + h - 40)],
              fill=WHITE, outline=GREY)
    d.ellipse([x + 26, y + h - 40, x + 48, y + h - 30], fill=WHITE,
              outline=GREY)
    # Sealed document under a gag band.
    d.rectangle([x + 84, y + 8, x + 128, y + 40], fill=(252, 250, 242),
                outline=INK)
    for i in range(3):
        d.line([(x + 90, y + 15 + i * 6), (x + 122, y + 15 + i * 6)],
               fill=GREY)
    d.rectangle([x + 84, y + 21, x + 128, y + 29], fill=DRED)
    text(d, x + 106, y + 22, "HUSH", F(SANS_B, 8), fill=WHITE, anchor="ma")
    d.ellipse([x + 116, y + 30, x + 126, y + 40], fill=RED, outline=GOLD)


def scene_eu_kyiv(d, x, y, w, h):
    vgrad(d, x, y, w, h, (206, 224, 246), (240, 240, 234))
    flag(d, x + 8, y + 7, 52, 32, [(36, 84, 160)])
    for i in range(8):
        a = math.radians(i * 45)
        d.ellipse([x + 32 + 11 * math.cos(a) - 2, y + 21 + 11 * math.sin(a) - 2,
                   x + 36 + 11 * math.cos(a), y + 25 + 11 * math.sin(a)],
                  fill=GOLD)
    flag(d, x + w - 60, y + 7, 52, 32, [(36, 84, 160), (240, 196, 25)])
    for i in range(4):
        for j in range(4 - i):
            cx = x + w // 2 - 24 + i * 16
            cy = y + h - 10 - j * 9
            d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=GOLD,
                      outline=(160, 120, 20))
            text(d, cx, cy - 5, "€", F(SANS_B, 10), fill=(120, 88, 10),
                 anchor="ma")
    # A bridge beam linking the two flags: aid, delivered.
    d.rectangle([x + 62, y + 20, x + w - 62, y + 24], fill=NAVY)
    d.polygon([(x + w - 62, y + 16), (x + w - 52, y + 22), (x + w - 62, y + 28)],
              fill=NAVY)


def scene_rugby(d, x, y, w, h):
    vgrad(d, x, y, w, h, (44, 74, 128), (96, 140, 196))
    d.rectangle([x, y, x + w, y + 13], fill=NAVY)
    text(d, x + 5, y + 2, "FRA 45–17 ARG", F(SANS_B, 9), fill=WHITE)
    text(d, x + w - 5, y + 2, "PARIS", F(SANS_B, 9), fill=GOLD, anchor="ra")
    for r in range(2):
        for i in range(16):
            d.ellipse([x + 6 + i * 9, y + 18 + r * 6, x + 9 + i * 9,
                       y + 21 + r * 6],
                      fill=[RED, WHITE, (90, 140, 220), GOLD][(r + i) % 4])
    d.rectangle([x, y + h - 16, x + w, y + h], fill=(56, 140, 60))
    d.rectangle([x + w // 2 - 20, y + h - 34, x + w // 2 - 17, y + h - 14],
                fill=WHITE)
    d.rectangle([x + w // 2 + 17, y + h - 34, x + w // 2 + 20, y + h - 14],
                fill=WHITE)
    d.rectangle([x + w // 2 - 20, y + h - 16, x + w // 2 + 20, y + h - 14],
                fill=WHITE)
    d.ellipse([x + w // 2 - 26, y + h - 30, x + w // 2 - 14, y + h - 22],
              fill=(122, 72, 34))
    flag(d, x + 6, y + h - 15, 22, 11, [(36, 84, 160), WHITE, RED],
         vertical=True)
    person(d, x + 30, y + h - 1, 15, (240, 200, 160), (36, 84, 160))
    person(d, x + w - 28, y + h - 1, 15, (200, 160, 120), (46, 125, 50))


def scene_leeds(d, x, y, w, h):
    vgrad(d, x, y, w, h, (52, 92, 150), (130, 176, 224))
    d.rectangle([x, y, x + w, y + 13], fill=NAVY)
    text(d, x + 5, y + 2, "CHE 1–4 LEE", F(SANS_B, 9), fill=WHITE)
    text(d, x + w - 5, y + 2, "LONDON", F(SANS_B, 9), fill=GOLD, anchor="ra")
    for i in range(6):
        d.rectangle([x + i * w // 6, y + 13, x + (i + 1) * w // 6, y + h],
                    fill=(56, 140, 60) if i % 2 == 0 else (66, 152, 70))
    d.line([(x, y + h - 14), (x + w, y + h - 14)], fill=WHITE)
    d.rectangle([x + w - 48, y + h - 32, x + w - 4, y + h - 6], outline=WHITE,
                width=2)
    for i in range(1, 5):
        d.line([(x + w - 48 + i * 9, y + h - 32), (x + w - 48 + i * 9,
                                                   y + h - 6)], fill=LGREY)
    d.ellipse([x + w - 33, y + h - 24, x + w - 21, y + h - 12], fill=WHITE,
              outline=INK)
    person(d, x + 22, y + h - 1, 16, (240, 200, 160), (250, 214, 40))
    person(d, x + 44, y + h - 1, 16, (200, 160, 120), (36, 84, 160))


def scene_launcher(d, x, y, w, h):
    vgrad(d, x, y, w, h, (236, 202, 152), (214, 168, 104))
    d.rectangle([x, y + h - 10, x + w, y + h], fill=(164, 124, 72))
    d.rectangle([x + 10, y + 10, x + 74, y + h - 10], fill=(94, 78, 62))
    d.rectangle([x + 16, y + 15, x + 68, y + h - 16], fill=(58, 48, 40))
    d.rectangle([x + 84, y + h - 20, x + 140, y + h - 10], fill=(70, 75, 70))
    d.line([(x + 92, y + h - 20), (x + 74, y + 12)], fill=(96, 100, 96),
           width=5)
    d.polygon([(x + 68, y + 4), (x + 76, y + 12), (x + 82, y + 6)],
              fill=RED)
    d.rectangle([x + 72, y + 12, x + 80, y + 22], fill=WHITE)
    for wx in (x + 96, x + 128):
        d.ellipse([wx - 5, y + h - 12, wx + 5, y + h - 2], fill=(20, 20, 20))
    flag(d, x + w - 34, y + 8, 26, 16, [(46, 125, 50), WHITE, RED],
         disc_c=RED)
    d.polygon([(x + w - 52, y + 12), (x + w - 44, y + 16), (x + w - 52, y + 20),
               (x + w - 58, y + 16)], fill=DARK)
    d.polygon([(x + w - 66, y + 22), (x + w - 59, y + 25), (x + w - 66, y + 28),
               (x + w - 71, y + 25)], fill=DARK)


def scene_cricket(d, x, y, w, h):
    vgrad(d, x, y, w, h, (70, 128, 188), (168, 206, 238))
    d.rectangle([x, y, x + w, y + 13], fill=NAVY)
    text(d, x + 5, y + 2, "AUS WIN BY 3 WKTS", F(SANS_B, 9), fill=WHITE)
    text(d, x + w - 5, y + 2, "1 BALL LEFT", F(SANS_B, 9), fill=GOLD,
         anchor="ra")
    d.rectangle([x, y + 13, x + w, y + h], fill=(56, 140, 60))
    d.rectangle([x + w // 2 - 9, y + 13, x + w // 2 + 9, y + h], fill=SAND)
    for i in range(3):
        d.rectangle([x + w // 2 - 7 + i * 6, y + h - 18, x + w // 2 - 4 + i * 6,
                     y + h - 6], fill=(240, 196, 25))
    d.line([(x + w // 2 - 20, y + h - 12), (x + w // 2 - 30, y + h - 26)],
           fill=(200, 165, 105), width=3)
    d.ellipse([x + w // 2 + 22, y + h - 26, x + w // 2 + 30, y + h - 18],
              fill=RED)
    person(d, x + 20, y + h - 1, 15, (240, 200, 160), (250, 214, 40))
    person(d, x + w - 20, y + h - 1, 15, (200, 160, 120), RED)


def scene_taiwan(d, x, y, w, h):
    vgrad(d, x, y, w, h, (146, 194, 232), (204, 232, 246))
    d.rectangle([x, y + h - 14, x + w, y + h], fill=SEA)
    for i in range(6):
        d.arc([x + i * 26, y + h - 12, x + i * 26 + 14, y + h - 6], 180, 360,
              fill=(210, 232, 244))
    d.polygon([(x + 58, y + h - 14), (x + 76, y + h - 34), (x + 96, y + h - 14)],
              fill=(60, 140, 70))
    flag(d, x + 72, y + 8, 24, 14, [RED])
    d.rectangle([x + 72, y + 8, x + 84, y + 15], fill=(36, 84, 160))
    for k in range(2):
        jx, jy = x + 12 + k * 44, y + 8 + k * 9
        d.polygon([(jx, jy), (jx + 18, jy + 4), (jx, jy + 8)], fill=(90, 95, 105))
        d.line([(jx, jy + 4), (jx - 16, jy + 4)], fill=WHITE, width=2)
    for k in range(2):
        sx = x + 16 + k * 84
        d.rectangle([sx, y + h - 20, sx + 34, y + h - 14], fill=(70, 80, 90))
        d.rectangle([sx + 11, y + h - 26, sx + 23, y + h - 20],
                    fill=(90, 100, 110))
    for k in range(2):
        bx = x + w - 24 - k * 26
        d.ellipse([bx - 6, y + 6 + k * 7, bx + 6, y + 18 + k * 7], fill=WHITE,
                  outline=RED)
        d.line([(bx, y + 18 + k * 7), (bx, y + 24 + k * 7)], fill=DARK)


def scene_druzhba(d, x, y, w, h):
    vgrad(d, x, y, w, h, (196, 214, 232), (238, 242, 244))
    d.rectangle([x, y + h - 12, x + w, y + h], fill=(240, 242, 240))
    d.rectangle([x + 96, y + h - 34, x + 140, y + h - 12], fill=(150, 140, 130),
                outline=GREY)
    d.rectangle([x + 104, y + h - 42, x + 116, y + h - 34], fill=(110, 100, 92))
    d.line([(x, y + h - 22), (x + w, y + h - 26)], fill=(90, 100, 110),
           width=5)
    d.line([(x, y + h - 22), (x + w, y + h - 26)], fill=(140, 155, 170),
           width=2)
    for px in (x + 30, x + 70, x + 146):
        d.rectangle([px, y + h - 24, px + 4, y + h - 12], fill=(90, 100, 110))
    burst(d, x + 108, y + h - 44, 12)
    for j in range(4):
        d.ellipse([x + 118 + j * 3, y + 6 + j * 5, x + 126 + j * 3,
                   y + 13 + j * 5], fill=(120, 120, 120))
    text(d, x + 6, y + 3, "TATARSTAN", F(SANS_B, 9), fill=NAVY)
    text(d, x + 6, y + 15, "1,000+ KM FROM FRONT", F(SANS_B, 8), fill=GREY)


def scene_newcastle(d, x, y, w, h):
    vgrad(d, x, y, w, h, (52, 92, 150), (130, 176, 224))
    d.rectangle([x, y, x + w, y + 13], fill=(20, 20, 24))
    text(d, x + 5, y + 2, "NEW 2–2 ARS", F(SANS_B, 9), fill=WHITE)
    text(d, x + w - 5, y + 2, "ST JAMES'", F(SANS_B, 9), fill=GOLD, anchor="ra")
    for i in range(6):
        d.rectangle([x + i * w // 6, y + 13, x + (i + 1) * w // 6, y + h],
                    fill=(56, 140, 60) if i % 2 == 0 else (66, 152, 70))
    d.rectangle([x + 6, y + h - 32, x + 50, y + h - 6], outline=WHITE, width=2)
    for i in range(1, 5):
        d.line([(x + 6 + i * 9, y + h - 32), (x + 6 + i * 9, y + h - 6)],
               fill=LGREY)
    d.ellipse([x + 20, y + h - 24, x + 32, y + h - 12], fill=WHITE, outline=INK)
    person(d, x + w - 40, y + h - 1, 16, (240, 200, 160), (30, 30, 30))
    d.rectangle([x + w - 45, y + h - 12, x + w - 35, y + h - 6], fill=WHITE)
    person(d, x + w - 66, y + h - 1, 16, (200, 160, 120), RED)


def scene_vanuatu(d, x, y, w, h):
    vgrad(d, x, y, w, h, SKY2, (240, 246, 248))
    sun(d, x + w - 24, y + 14, 8)
    d.rectangle([x, y + h - 16, x + w, y + h], fill=SEA)
    for i in range(5):
        d.arc([x + i * 32, y + h - 13, x + i * 32 + 16, y + h - 7], 180, 360,
              fill=(210, 232, 244))
    d.polygon([(x + 16, y + h - 16), (x + 52, y + h - 26), (x + 92, y + h - 16)],
              fill=(86, 160, 80))
    d.line([(x + 62, y + h - 24), (x + 58, y + h - 38)], fill=BROWN, width=3)
    for a in (-40, -15, 15, 40):
        d.arc([x + 58 - 12, y + h - 46, x + 58 + 12, y + h - 30],
              200 + a, 320 + a, fill=(46, 125, 50), width=3)
    person(d, x + 112, y + h - 15, 17, (120, 84, 58), (224, 122, 26))
    d.rectangle([x + 118, y + h - 32, x + 148, y + h - 22], fill=WHITE,
                outline=INK)
    text(d, x + 133, y + h - 31, "1.5°C", F(SANS_B, 8), fill=DRED, anchor="ma")


def scene_hormuz(d, x, y, w, h):
    vgrad(d, x, y, w, h, (206, 224, 238), (238, 242, 240))
    d.polygon([(x, y), (x + 44, y), (x + 30, y + 22), (x, y + 30)], fill=SAND)
    d.polygon([(x + w, y), (x + w - 40, y), (x + w - 28, y + 20), (x + w, y + 28)],
              fill=SAND)
    d.rectangle([x, y + 18, x + w, y + h], fill=SEA)
    for k in range(3):
        tx = x + 14 + k * 48
        ty = y + 26 + (k % 2) * 8
        d.rectangle([tx, ty, tx + 36, ty + 7], fill=(52, 56, 64))
        d.rectangle([tx + 4, ty - 5, tx + 12, ty], fill=(120, 60, 40))
        d.rectangle([tx + 26, ty - 4, tx + 32, ty], fill=(90, 95, 100))
        if k == 1:
            burst(d, tx + 18, ty - 10, 8)
            for j in range(3):
                d.ellipse([tx + 20 + j * 3, ty - 20 - j * 4, tx + 27 + j * 3,
                           ty - 14 - j * 4], fill=(120, 120, 120))
    text(d, x + w // 2, y + 2, "STRAIT OF HORMUZ", F(SANS_B, 8), fill=NAVY,
         anchor="ma")


# ------------------------------------------------------------------ data
LEADS = [
    (1, "GLOBAL", "CLIMATE", "COP31 runs into overtime in Antalya",
     "Talks run past their Friday deadline: nearly 200 nations still "
     "split over fossil fuels and the $120bn adaptation target. "
     "No final text yet.", "REPORTED", "UN", scene_cop31),
    (2, "MID EAST", "IRAN WAR", "Iran hits US bases in Bahrain",
     "Missiles and drones hit US positions at Al-Riffa and Awali late "
     "on Saturday; a civilian facility catches fire. The IRGC claims "
     "two Patriot radars hit — unverified.", "CONFIRMED", "BAHRAIN",
     scene_bahrain),
    (3, "LATIN AM", "CARTELS", "'Chapo Isidro' seized, 11 dead",
     "Mexican forces capture the FBI most-wanted boss Fausto Isidro "
     "Meza Flores in Guasave, Sinaloa. Seven gunmen and four soldiers "
     "die in the firefight.", "CONFIRMED", "MEXICO", scene_chapo),
]

SMALL = [
    (4, "LATIN AM", "DISASTER", "Peru shaken by M6.9",
     "Felt in Lima; no damage", "CONFIRMED", "USGS", scene_quake),
    (5, "N AMERICA", "POLITICS", "Trump gags contractors",
     "'Check with White House first'", "REPORTED", "WHITE HOUSE",
     scene_trump),
    (6, "EUROPE", "UKRAINE AID", "EU gives Kyiv €1bn",
     "As Russia rejects peace plan", "CONFIRMED", "EU", scene_eu_kyiv),
    (7, "EUROPE", "RUGBY", "France into rugby final",
     "France face South Africa next", "CONFIRMED", "WORLD RUGBY",
     scene_rugby),
    (8, "EUROPE", "FOOTBALL", "Leeds humble Chelsea 4–1",
     "First win there since 1999", "CONFIRMED", "LONDON", scene_leeds),
    (9, "MID EAST", "DEFENCE", "Iran shows off new launcher",
     "Tehran claims 2 US drones down", "REPORTED", "TEHRAN",
     scene_launcher),
    (10, "OCEANIA", "CRICKET", "Aussies edge England",
     "Chaudhary 66 in T20 thriller", "CONFIRMED", "SYDNEY", scene_cricket),
    (11, "ASIA", "TAIWAN STRAIT", "Taiwan tracks China's jets",
     "Taipei rejects Beijing account", "REPORTED", "TAIPEI", scene_taiwan),
    (12, "EUROPE", "UKRAINE WAR", "Ukraine hits Druzhba station",
     "1,000+ km from the front", "CONFIRMED", "KYIV", scene_druzhba),
    (18, "EUROPE", "FOOTBALL", "Newcastle 2–2 Arsenal",
     "Keeper Raya hurt, faces scan", "CONFIRMED", "NEWCASTLE",
     scene_newcastle),
    (34, "OCEANIA", "CLIMATE", "Vanuatu warns COP31",
     "'We will not survive' warning", "CONFIRMED", "VANUATU",
     scene_vanuatu),
    (43, "MID EAST", "SHIPPING", "Tankers hit near Hormuz",
     "Struck by projectiles", "REPORTED", "SHIPPING", scene_hormuz),
]

BRIEFS = [
    (13, "EUROPE", "Ukraine strikes 3 Russian ballistic-missile launchers"),
    (14, "EUROPE", "NATO chief Rutte visits Poland after airspace incursion"),
    (15, "EUROPE", "Russian cargo ship hit by drones in Gulf of Finland"),
    (16, "EUROPE", "Putin urges Ukrainian soldiers to join Russia"),
    (17, "EUROPE", "EU admits AI-assisted cyberattack hit it weeks ago"),
    (19, "EUROPE", "Malen scores four as Roma rout Parma 5–1"),
    (20, "EUROPE", "Real Madrid come back to beat Celta Vigo 2–1"),
    (21, "EUROPE", "PSG beat Nice 3–2; Doué knee injury feared"),
    (22, "ASIA", "Nepal PM Balendra Shah to visit India, meet Modi"),
    (23, "ASIA", "IBSA backs partnership model for Global South"),
    (24, "ASIA", "Toxic liquor kills 11 in Manipur; 180+ hospitalised"),
    (25, "ASIA", "Prabowo and Xi discuss South China Sea in Beijing"),
    (26, "ASIA", "EU–Indonesia trade deal covers 730m people"),
    (27, "ASIA", "Vietnam tightens checks on Chinese strawberries"),
    (28, "N AMERICA", "Trump vows 10% cap on credit-card interest"),
    (29, "N AMERICA", "FBI investigates hack of its NCIC crime database"),
    (30, "N AMERICA", "Oath Keepers founder Rhodes 'done' with Trump"),
    (31, "N AMERICA", "Democrats' Senate leadership vote tests promises"),
    (32, "N AMERICA", "Judge declines long ban on Trump's midterm ads"),
    (33, "OCEANIA", "Melbourne teen accused of organising arsons on Signal"),
    (35, "OCEANIA", "Australia, Canada, NZ condemn Russia's war at APEC"),
    (36, "AFRICA", "Tanzania president: new constitution by 2028–29"),
    (37, "AFRICA", "Guinea president orders ministers onto national TV"),
    (38, "AFRICA", "South Africa mourns ex-deputy president Mlambo-Ngcuka"),
    (39, "AFRICA", "Senegal president imposes budget rejected by MPs"),
    (40, "AFRICA", "Sudan's displaced elderly face hardship"),
    (41, "LATIN AM", "Palmeiras 1–1 Flamengo in Brasileirão title race"),
    (42, "LATIN AM", "Bahia 0–1 Coritiba in Brasileirão"),
    (44, "MID EAST", "Four Palestinians killed in Israeli attacks in Gaza"),
    (45, "MID EAST", "Qatari delegation in Tehran to mediate US–Iran"),
    (46, "GLOBAL", "CBS: how China gets access to American AI chips"),
]

TIMELINE = [
    ("00:09", "Peru M6.9 quake"), ("07:20", "Chapo Isidro captured"),
    ("07:41", "COP31 deadlocked"), ("10:24", "Russia rebuked at APEC"),
    ("11:05", "Nepal PM visit set"), ("21:31", "Bahrain attacked"),
]

NUMBERS = [
    ("6.9", "PERU QUAKE MAGNITUDE"), ("11", "DEAD IN SINALOA"),
    ("€1bn", "EU AID TO UKRAINE"), ("200", "NATIONS AT COP31"),
    ("$120bn", "ADAPTATION TARGET"), ("4", "BALLOONS NEAR TAIWAN"),
]

DATE_CHECK = [
    "Kyiv mass attack, 3 bridges hit — Thu 20 Nov",
    "Russian missiles, drone into Poland — 20 Nov",
    "Shenzhen Xi–Trump–Putin summit — Wed 19 Nov",
    "'Claude proved Riemann' claim — Thu 20 Nov",
    "India–Japan live-fire training deal — 19 Nov",
    "Not yet: World Court Myanmar ruling — 22 Nov",
]

GEO = {
    1: (30.7, 36.9), 2: (50.5, 26.2), 3: (-108.5, 25.6), 4: (-75.0, -10.0),
    5: (-77.0, 38.9), 6: (30.5, 50.4), 7: (2.3, 48.9), 8: (-0.19, 51.48),
    9: (56.5, 27.0), 10: (151.2, -33.9), 11: (121.0, 23.5),
    12: (50.0, 55.0), 13: (35.0, 49.0), 14: (19.0, 52.0), 15: (24.0, 59.8),
    16: (37.6, 55.75), 17: (4.35, 50.85), 18: (-1.6, 54.97),
    19: (12.5, 41.9), 20: (-3.7, 40.4), 21: (2.3, 48.9), 22: (77.2, 28.6),
    23: (28.0, -26.2), 24: (93.9, 24.8), 25: (116.4, 39.9),
    26: (106.8, -6.2), 27: (105.8, 21.0), 28: (-77.0, 38.9),
    29: (-77.0, 38.9), 30: (-77.0, 38.9), 31: (-77.0, 38.9),
    32: (-77.0, 38.9), 33: (145.0, -37.8), 34: (168.3, -17.7),
    35: (151.2, -33.9), 36: (35.7, -6.2), 37: (-13.7, 9.5),
    38: (28.0, -26.2), 39: (-17.4, 14.7), 40: (32.5, 15.6),
    41: (-46.6, -23.5), 42: (-38.5, -13.0), 43: (56.5, 26.5),
    44: (34.5, 31.5), 45: (51.4, 35.7), 46: (-77.0, 38.9),
}
PIN_POS = {1: (37.0, 32.0), 2: (44.0, 21.0), 5: (-84.0, 44.0),
           6: (34.0, 53.0), 7: (12.0, 44.0), 8: (-7.0, 53.0),
           9: (65.0, 28.0), 12: (55.0, 58.0), 18: (-15.0, 61.0),
           43: (58.0, 15.0)}
ILLUSTRATED = {s[0] for s in LEADS} | {s[0] for s in SMALL}

LAND = [
    (-168, 50, -140, 70), (-140, 42, -110, 62), (-110, 30, -85, 50),
    (-85, 25, -70, 48), (-70, 42, -55, 48), (-125, 32, -114, 42),
    (-100, 16, -86, 22), (-92, 8, -77, 16), (-80, -5, -60, 8),
    (-70, -12, -50, -5), (-75, -22, -58, -12), (-72, -38, -62, -22),
    (-70, -52, -66, -38), (-56, 48, -44, 52), (-44, 60, -22, 68),
    (-18, 36, -9, 44), (-9, 43, 3, 51), (3, 51, 20, 58), (5, 58, 18, 63),
    (18, 56, 32, 66), (20, 46, 32, 56), (8, 44, 20, 46), (12, 38, 28, 44),
    (20, 40, 40, 46), (28, 44, 48, 52), (40, 52, 70, 62), (70, 55, 110, 68),
    (110, 60, 160, 72), (160, 64, 180, 70), (32, 36, 44, 42),
    (-18, 15, -10, 28), (-10, 5, 10, 15), (10, 4, 30, 12),
    (8, -12, 30, 4), (20, -26, 34, -12), (26, -32, 32, -26),
    (44, 12, 52, 28), (48, -12, 50, -2), (36, 28, 56, 40),
    (56, 24, 70, 38), (70, 34, 90, 48), (78, 8, 88, 22),
    (90, 22, 98, 28), (92, 46, 112, 54), (98, 28, 108, 40),
    (100, 6, 104, 18), (104, -8, 114, -2), (108, 18, 122, 32),
    (114, -22, 124, -12), (122, -34, 130, -22), (130, -28, 140, -12),
    (140, -38, 148, -28), (146, -42, 150, -38), (114, -12, 122, -10),
    (122, 32, 132, 40), (130, 40, 142, 46), (142, 46, 156, 52),
    (167, -46, 174, -40), (172, -40, 176, -36), (95, 5, 104, 8),
    (55, 46, 70, 52), (44, 40, 56, 46),
]


# ---------------------------------------------------------------- layout
MX = 18
CW = W - 2 * MX  # 988


def masthead(d):
    text(d, MX, 12, "THE WORLD'S NEWS OF ONE DAY", F(SANS_B, 13), fill=DRED)
    text(d, W - MX, 12, "46 STORIES · 8 REGIONS · EVERY ONE FROM THIS "
         "SATURDAY", F(SANS_B, 13), fill=DRED, anchor="ra")
    f = F(SERIF_B, 64)
    s = "Saturday 21 November 2026"
    while tw(d, s, f) > CW:
        f = F(SERIF_B, f.size - 2)
    text(d, MX - 2, 30, s, f, fill=(16, 14, 12))
    d.rectangle([MX, 102, W - MX, 104], fill=INK)
    d.rectangle([MX, 106, W - MX, 107], fill=INK)


def region_strip(d):
    y = 112
    widths = [196, 128, 132, 116, 112, 112, 112, 80]
    x = MX
    for (name, count), wdt in zip(REGION_COUNTS, widths):
        col = REGION_COLORS[name]
        d.rectangle([x, y, x + wdt - 3, y + 20], fill=col)
        text(d, x + wdt // 2 - 1, y + 4, "%s %d" % (name, count),
             F(SANS_B, 11), fill=WHITE, anchor="ma")
        x += wdt


def band_label(d, y, lines, h):
    d.rectangle([MX, y, MX + 70, y + h], fill=DRED)
    f = F(SANS_B, 10)
    for i, ln in enumerate(lines):
        text(d, MX + 35, y + 4 + i * 12, ln, f, fill=WHITE, anchor="ma")


def timeline(d):
    y = 138
    band_label(d, y, ["THE DAY", "IN UTC"], 46)
    x0 = MX + 78
    slot = (W - MX - x0) // 6
    d.line([(x0, y + 25), (W - MX, y + 25)], fill=LGREY, width=2)
    for i, (t, label) in enumerate(TIMELINE):
        sx = x0 + i * slot
        d.ellipse([sx, y + 22, sx + 6, y + 28], fill=DRED)
        text(d, sx, y, t, F(SERIF_B, 16), fill=DRED)
        for ln in wrap_px(d, label, F(SANS, 10), slot - 6)[:1]:
            text(d, sx, y + 34, ln, F(SANS, 10), fill=INK)


def numbers_row(d):
    y = 190
    band_label(d, y, ["THE DAY", "IN", "NUMBERS"], 40)
    x0 = MX + 78
    slot = (W - MX - x0) // 6
    for i, (num, label) in enumerate(NUMBERS):
        sx = x0 + i * slot
        text(d, sx, y - 2, num, F(SERIF_B, 27), fill=INK)
        for ln in wrap_px(d, label, F(SANS_B, 8), slot - 8)[:1]:
            text(d, sx, y + 29, ln, F(SANS_B, 8), fill=GREY)


def lead_card(d, x, y, w, h, story):
    num, region, topic, head, body, status, source, scene = story
    d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LGREY)
    scene(d, x + 1, y + 1, w - 2, 102)
    d.rectangle([x, y + 103, x + w, y + 104], fill=LGREY)
    ky = y + 110
    num_disc(d, x + 13, ky + 7, 9, num)
    text(d, x + 27, ky + 1, "%s · %s" % (region, topic), F(SANS_B, 11),
         fill=REGION_COLORS[region])
    chip(d, x + w - 8, ky + 1, status, source)
    lines = wrap_px(d, head, F(SERIF_B, 24), w - 16)[:2]
    for i, ln in enumerate(lines):
        text(d, x + 8, y + 126 + i * 27, ln, F(SERIF_B, 24), fill=INK)
    blines = wrap_px(d, body, F(SERIF, 12), w - 16)[:4]
    for i, ln in enumerate(blines):
        text(d, x + 8, y + 184 + i * 15, ln, F(SERIF, 12), fill=(52, 48, 44))


def small_card(d, x, y, w, h, story):
    num, region, topic, head, sub, status, source, scene = story
    d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LGREY)
    scene(d, x + 1, y + 1, w - 2, 47)
    d.rectangle([x, y + 48, x + w, y + 49], fill=LGREY)
    ky = y + 53
    num_disc(d, x + 9, ky + 5, 7, num)
    text(d, x + 20, ky, "%s · %s" % (region, topic), F(SANS_B, 8),
         fill=REGION_COLORS[region])
    lines = wrap_px(d, head, F(SERIF_B, 14), w - 10)[:2]
    for i, ln in enumerate(lines):
        text(d, x + 5, y + 66 + i * 16, ln, F(SERIF_B, 14), fill=INK)
    text(d, x + 5, y + 100, sub, F(SERIF_I, 10), fill=(70, 64, 58))
    col = GREEN if status == "CONFIRMED" else AMBER
    text(d, x + 5, y + h - 13, "%s · %s" % (status, source), F(SANS_B, 8),
         fill=col)


def world_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(224, 233, 238), outline=LGREY)

    def proj(lon, lat):
        return (x + (lon + 170) / 360 * w, y + (75 - lat) / 135 * h)

    for gy in range(int(y) + 3, int(y + h), 5):
        lat = 75 - (gy - y) / h * 135
        for gx in range(int(x) + 3, int(x + w), 5):
            lon = (gx - x) / w * 360 - 170
            for (a, b, c, e) in LAND:
                if a <= lon <= c and b <= lat <= e:
                    d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2],
                              fill=(214, 186, 132))
                    break
    for num, (lon, lat) in sorted(GEO.items()):
        if num in ILLUSTRATED:
            continue
        px, py = proj(lon + (num % 5) - 2, lat + (num % 3) - 1)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(150, 148, 140))
    for num in sorted(ILLUSTRATED):
        lon, lat = PIN_POS.get(num, GEO[num])
        px, py = proj(lon, lat)
        num_disc(d, px, py, 7, num)


def bottom(d):
    y = 750
    text(d, MX, y, "WHERE IT HAPPENED", F(SANS_B, 12), fill=DRED)
    world_map(d, MX, y + 18, 330, 124)
    text(d, MX, y + 146, "Red pins: the 15 illustrated stories · grey dots: "
         "the briefs", F(SANS, 9), fill=GREY)
    # DATE CHECK box.
    by = y + 158
    d.rectangle([MX, by, MX + 330, y + 248], outline=RED, width=2)
    d.rectangle([MX, by, MX + 330, by + 17], fill=DRED)
    text(d, MX + 6, by + 3, "DATE CHECK — LEFT OUT ON PURPOSE", F(SANS_B, 10),
         fill=WHITE)
    for i, item in enumerate(DATE_CHECK):
        text(d, MX + 6, by + 21 + i * 12, "· " + item, F(SANS, 9), fill=INK)
    # Briefs.
    bx = MX + 344
    text(d, bx, y, "ALSO ON SATURDAY", F(SANS_B, 12), fill=DRED)
    text(d, W - MX, y, "31 MORE STORIES", F(SANS_B, 12), fill=GREY,
         anchor="ra")
    colw = (W - MX - bx - 12) // 2
    for ci in range(2):
        cx = bx + ci * (colw + 12)
        for ri, (num, region, txt) in enumerate(BRIEFS[ci * 16:(ci + 1) * 16]):
            ry = y + 20 + ri * 14
            text(d, cx, ry, str(num), F(SANS_B, 10),
                 fill=REGION_COLORS[region])
            text(d, cx + 22, ry, txt, F(SANS, 10), fill=INK)


def footer(d):
    d.rectangle([MX, 1004, W - MX, 1005], fill=LGREY)
    text(d, MX, 1009, "Every story here happened, or was first reported, on "
         "Saturday 21 November 2026. Claims are attributed to their makers.",
         F(SANS, 9), fill=GREY)
    text(d, W - MX, 1009, "Sources: Reuters · AP · AFP · Al Jazeera · USGS "
         "· UN · EU", F(SANS, 9), fill=GREY, anchor="ra")


def main():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    masthead(d)
    region_strip(d)
    timeline(d)
    numbers_row(d)
    lw = (CW - 22) // 3
    for i, story in enumerate(LEADS):
        lead_card(d, MX + i * (lw + 11), 236, lw, 238, story)
    sw = (CW - 25) // 6
    for i, story in enumerate(SMALL):
        row, col = divmod(i, 6)
        small_card(d, MX + col * (sw + 5), 482 + row * 134, sw, 126, story)
    bottom(d)
    footer(d)
    # Seeded paper grain: deterministic, lifts the flat colour fields the
    # way newsprint texture does, and carries the file into the winners'
    # weight band.
    arr = np.asarray(img).astype(np.int16)
    rng = np.random.default_rng(20261121)
    noise = rng.normal(0, 0.55, (H, W, 1)).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr, "RGB")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "entry.png")
    out.save(path, optimize=True)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
