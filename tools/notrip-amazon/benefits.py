"""Benefit-led gallery tiles for the Cadenza No-Trip Sleeve (owner ask, 2026-11-05):
"images that talk about the benefits, spelling it out" - no tangled paws, leash off the
ground, easy on, the dog's name, the colour range.

Built only from approved pictures (the OneDrive marketing masters) and the v5.1 CAD
renderer, so no image spend. Writes 2000x2000 drafts to tools/notrip-amazon/benefits/ with
the same Cadenza + MADE IN THE USA band as compose.py; nothing goes to src/ until approved.

    py -3 tools/notrip-amazon/benefits.py          (needs tools/notrip-v51/build/*.npz)
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'notrip-v51'))
import compose as C  # noqa: E402
import render_all as RA  # noqa: E402

S, BAND, NAVY, MUTED, WHITE = C.S, C.BAND, C.NAVY, C.MUTED, C.WHITE
H, B = C.H, C.B
GOOD, BAD = (31, 140, 76), (200, 48, 48)
ACCENT = (26, 115, 232)
OUT = HERE / 'benefits'
IMG = (pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners'
       / 'Clients & Products' / '8. NoTrip Sleeve' / 'marketing' / 'images')


def master(name):
    return Image.open(IMG / name).convert('RGB')


def canvas():
    return Image.new('RGB', (S, S), WHITE)


def title(c, text, sub=None, y=70, size=132):
    d = ImageDraw.Draw(c)
    while d.textlength(text, font=H(size)) > S - 140:   # one row, never wrap
        size -= 4
    d.text((S // 2, y), text, font=H(size), fill=NAVY, anchor='mt')
    if sub:
        d.text((S // 2, y + size + 28), sub, font=B(64), fill=MUTED, anchor='mt')


def rounded(im, r=36):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=r, fill=255)
    out = Image.new('RGBA', im.size)
    out.paste(im, (0, 0), m)
    return out


def fit_cover(im, w, h, fx=0.5, fy=0.5):
    """Scale to cover w x h, then crop about (fx, fy) of the spare room."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = round((im.width - w) * fx), round((im.height - h) * fy)
    return im.crop((l, t, l + w, t + h))


def mark(d, cx, cy, r, ok):
    """A filled tick or cross disc - drawn, since Barlow has neither glyph."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOOD if ok else BAD)
    w = max(6, r // 4)
    if ok:
        d.line([(cx - r * .45, cy + r * .02), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)],
               fill=WHITE, width=w, joint='curve')
    else:
        k = r * .38
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=WHITE, width=w)
        d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=WHITE, width=w)


def pill(c, x, y, text, ok, size=60):
    """Label pill with a tick/cross, anchored at its top-left."""
    d = ImageDraw.Draw(c)
    tw = d.textlength(text, font=H(size))
    r = size // 2 + 8
    h = size + 44
    w = int(tw + 2 * r + 70)
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=WHITE)
    mark(d, x + 22 + r, y + h // 2, r, ok)
    d.text((x + 2 * r + 46, y + h // 2), text, font=H(size), fill=GOOD if ok else BAD, anchor='lm')
    return w


def shadow(c, box, r=36, blur=26, alpha=70):
    sh = Image.new('L', (S, S), 0)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 6, y0 + 14, x1 + 6, y1 + 14], radius=r, fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    c.paste(Image.new('RGB', (S, S), (20, 30, 45)), (0, 0), sh)


# ---------------------------------------------------------------- tiles

# per size (owner 2026-11-05: each size's gallery shows only its own piece): the doodle wears the
# Standard (1 sleeve, 2 clips), the golden the Large (2 sleeves, 3 clips)
SCENES = {
    'S': ('before-slack-panel-small.png', 'lead-slack-small.png'),
    'L': ('before-slack-panel.png', 'lead-slack.png'),
}


def tangle(size):
    """1. No tangled paws: that size's before/after, side by side."""
    c = canvas()
    title(c, 'NO MORE TANGLED PAWS', 'The sleeve holds the slack up, clear of their legs')
    top, h, gap, m = 400, 1310, 24, 60
    w = (S - 2 * m - gap) // 2
    before, after = SCENES[size]
    for i, (f, ok, lab) in enumerate(((before, False, 'BEFORE'), (after, True, 'AFTER'))):
        x = m + i * (w + gap)
        ph = rounded(fit_cover(master(f), w, h, fx=0.42))
        c.paste(ph, (x, top), ph)
        pill(c, x + 30, top + h - 150, lab, ok, 56)
    return C.band(c)


def mess(size):
    """2. Leash off the ground: one big in-use photo, no inset (owner 11-05: the inset confused)."""
    c = canvas()
    title(c, 'NO MORE LEASH IN MUD OR POOP', 'The slack is held up, off the ground')
    top, m = 400, 60
    w, h = S - 2 * m, S - BAND - top - 40
    big = rounded(fit_cover(master(SCENES[size][1]), w, h, fy={'S': 0.55, 'L': 0.62}[size]))
    c.paste(big, (m, top), big)
    return C.band(c)


CACHE = HERE.parent / 'notrip-v51' / 'build' / 'benefit-parts'


def happy(size):
    """PT07 "happy faces" (owner, 2026-11-05): the dog and its person, both smiling. AI scenes
    (ai_edits.py happy-*), clip names re-lettered locally (fix_clip_names.py)."""
    c = canvas()
    title(c, 'HAPPY DOG. HAPPY YOU.', 'Walks without stopping to untangle the leash')
    # squarer than the other photo tiles so both faces AND the whole sleeve fit
    top = 400
    h = S - BAND - top - 40
    w = 1600
    m = (S - w) // 2
    f = {'S': 'happy-doodle.png', 'L': 'happy-golden.png'}[size]
    ph = rounded(fit_cover(master(f), w, h, fy=0.25))
    c.paste(ph, (m, top), ph)
    return C.band(c)


def render(asm, body, clip=None, **kw):
    """A CAD shot lifted off its backdrop as RGBA, cached (the renderer is slow)."""
    import hashlib
    key = hashlib.md5(repr((asm, body, clip, sorted(kw.items()))).encode()).hexdigest()[:12]
    f = CACHE / f'{asm}-{key}.png'
    if f.exists():
        return Image.open(f)
    im = RA.shot(asm, RA.rgb(body), RA.rgb(clip) if clip else None, **kw).convert('RGB')
    mask = C.cutout(im)
    part = im.convert('RGBA')
    part.putalpha(mask)
    part = part.crop(mask.getbbox())
    CACHE.mkdir(parents=True, exist_ok=True)
    part.save(f)
    return part


def trim(im, box):
    return C.contain(im, box)


def put(c, im, x, y):
    c.paste(im, (x, y), im)


def easy_on(size='S'):
    """3. Easy on: three steps, CAD for the parts, the detail photo for the result."""
    c = canvas()
    title(c, 'ON IN SECONDS. NO TOOLS.', 'Clips onto the leash you already own')
    d = ImageDraw.Draw(c)
    steps = [
        ('LAY THE LEASH IN', 'Into the open channel'),
        ('SNAP THE CLIPS ON', 'They lock it in place'),
        ('GO FOR A WALK', 'Slack stays off the paws'),
    ]
    asm = {'S': 'standard-name', 'L': 'large-name'}[size]
    sleeve = trim(render(asm, RA.BLUE, noclip=True, W=1400, H=1400, **RA.HERO_CAM), (520, 520))
    clip = trim(render('clip-blank', RA.ORANGE, W=1200, H=800, tilt=62, lay=90, roll=0, margin=0.1,
                       light=(-0.85, 0.35, 0.4), ambient=0.30, spec=0.25), (440, 300))
    done = fit_cover(master('detail-clip.png'), 560, 560, fx=0.45)
    top, cw, gap = 420, 600, 40
    x0 = (S - 3 * cw - 2 * gap) // 2
    for i, (head, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        d.rounded_rectangle([x, top, x + cw, top + 1300], radius=40, fill=(243, 246, 249))
        cx = x + cw // 2
        d.ellipse([cx - 60, top + 40, cx + 60, top + 160], fill=NAVY)
        d.text((cx, top + 100), str(i + 1), font=H(96), fill=WHITE, anchor='mm')
        area_t, area_h = top + 200, 640
        if i == 0:
            put(c, sleeve, cx - sleeve.width // 2, area_t + (area_h - sleeve.height) // 2)
        elif i == 1:
            # clip above, arrow down, sleeve below
            cl = trim(clip, (330, 200))
            sm = trim(sleeve, (300, 300))
            put(c, cl, cx - cl.width // 2, area_t)
            # a bold down arrow in the gap, in the brand accent so it reads against both parts
            ay = area_t + cl.height + 24
            d.rectangle([cx - 16, ay, cx + 16, ay + 70], fill=ACCENT)
            d.polygon([(cx - 56, ay + 62), (cx + 56, ay + 62), (cx, ay + 130)], fill=ACCENT)
            put(c, sm, cx - sm.width // 2, ay + 150)
        else:
            ph = rounded(done, 30)
            c.paste(ph, (cx - ph.width // 2, area_t + (area_h - ph.height) // 2), ph)
        d.text((cx, top + 900), head, font=H(70), fill=NAVY, anchor='mt')
        y = top + 1000
        for line in wrap(d, sub, B(54), cw - 80):
            d.text((cx, y), line, font=B(54), fill=MUTED, anchor='mt')
            y += 66
    return C.band(c)


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def name():
    """4. Their name on it: the real-looking clip photo, plus what it buys you."""
    c = canvas()
    title(c, 'THEIR NAME ON IT', 'Personalized clips - no more mixed-up leashes')
    m, top = 60, 400
    ph = rounded(fit_cover(master('detail-clip.png'), S - 2 * m, 860, fx=0.5, fy=0.5))
    c.paste(ph, (m, top), ph)
    d = ImageDraw.Draw(c)
    points = [
        ('UP TO 10 LETTERS', 'On every clip'),
        ('MOLDED IN', 'Sunk in, so it never wears off'),
        ('ANY CLIP COLOR', 'Match the sleeve or mix it up'),
    ]
    y0, cw = top + 860 + 70, (S - 2 * m) // 3
    for i, (h, s) in enumerate(points):
        cx = m + i * cw + cw // 2
        mark(d, cx, y0 + 50, 46, True)
        d.text((cx, y0 + 130), h, font=H(70), fill=NAVY, anchor='mt')
        y = y0 + 220
        for line in wrap(d, s, B(52), cw - 70):
            d.text((cx, y), line, font=B(52), fill=MUTED, anchor='mt')
            y += 62
    return C.band(c)


# sleeve / clip pairs for the range tile: every sleeve colour shown, clips mixed
COMBOS = [
    ('Black', 'Orange'), ('Blue', 'Orange'), ('Pink', 'Purple'), ('Teal', 'Yellow'),
    ('Red', 'White'), ('Purple', 'Pink'), ('Green', 'Black'), ('Orange', 'Blue'),
    ('Yellow', 'Teal'), ('Grey', 'Red'), ('White', 'Green'), ('Black', 'Black'),
]


def designs(size='S'):
    """5. The range: 11 sleeve colours x 11 clip colours, mixed clips, any name."""
    c = canvas()
    title(c, '1,000+ COLOR COMBOS', 'Pick the sleeve. Pick each clip. Add a name.')
    hx = dict(RA.COLOURS)
    d = ImageDraw.Draw(c)
    cols, cw, ch, gx, gy = 4, 440, 300, 30, 26
    x0 = (S - cols * cw - (cols - 1) * gx) // 2
    top = 400
    for k, (body, clip) in enumerate(COMBOS):
        x, y = x0 + (k % cols) * (cw + gx), top + (k // cols) * (ch + gy)
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=28, fill=(243, 246, 249))
        asm = {'S': 'standard-name', 'L': 'large-name'}[size]
        im = trim(render(asm, hx[body], hx[clip], W=900, H=900, **RA.HERO_CAM), (cw - 60, ch - 50))
        put(c, im, x + (cw - im.width) // 2, y + (ch - im.height) // 2)
    y = top + 3 * (ch + gy) + 40
    # the arithmetic behind the headline, so it adds up on the tile: 11 x 11 x 11 = 1,331
    # (Large: 3 clips, 11^4 = 14,641)
    if size == 'S':
        parts = [('11', 'SLEEVE'), ('x', None), ('11', 'CLIP 1'), ('x', None), ('11', 'CLIP 2'),
                 ('=', None), ('1,331', 'COMBOS')]
        xs = [390, 560, 730, 900, 1070, 1250, 1610]
    else:
        parts = [('11', 'SLEEVES'), ('x', None), ('11', 'CLIP 1'), ('x', None), ('11', 'CLIP 2'),
                 ('x', None), ('11', 'CLIP 3'), ('=', None), ('14,641', 'COMBOS')]
        xs = [250, 410, 570, 730, 890, 1050, 1210, 1370, 1680]
    for (big, small), x in zip(parts, xs):
        if small is None:
            d.text((x, y + 70), big, font=H(100), fill=MUTED, anchor='mm')
        else:
            d.text((x, y), big, font=H(130), fill=NAVY, anchor='mt')
            d.text((x, y + 150), small, font=B(50), fill=MUTED, anchor='mt')
    # no prices in gallery images (Amazon image rules)
    d.text((S // 2, S - BAND - 50), {'S': 'Then add their name. Or keep both clips the same color.', 'L': 'Then add their name. Or keep all three clips the same color.'}[size],
           font=B(50), fill=MUTED, anchor='mb')
    return C.band(c)


TILES = {
    'B1-tangle-S': lambda: tangle('S'), 'B1-tangle-L': lambda: tangle('L'),
    'B2-mess-S': lambda: mess('S'), 'B2-mess-L': lambda: mess('L'),
    'B3-easy-on-S': lambda: easy_on('S'), 'B3-easy-on-L': lambda: easy_on('L'),
    'B4-name': name,
    'B7-happy-S': lambda: happy('S'), 'B7-happy-L': lambda: happy('L'),
    'B5-designs-S': lambda: designs('S'), 'B5-designs-L': lambda: designs('L'),
}


def main():
    OUT.mkdir(exist_ok=True)
    want = set(sys.argv[1:])
    for key, fn in TILES.items():
        if want and key not in want:
            continue
        fn().save(OUT / f'{key}.jpg', quality=90, optimize=True, progressive=True)
        print('wrote', key)


if __name__ == '__main__':
    main()
