"""Every CAD picture of the v5.1 No-Trip Sleeve, from build/*.npz (run geometry.py first).

    hero-<standard|large>-<colour>.jpg   1000 sq, the main image behind the size + colour pickers
    spin/, spin-large/                    36 frames each, the 360 viewer (turns about the long axis)
    mini-standard/, mini-large/           24 frames each, the size-box turntables
    hero.jpg, pair-joined.jpg             the charcoal studio shots in the gallery
    clip-name.jpg, clip-blank.jpg         the connector top, with and without a name
    clip-contrast.jpg                     a body in one colour with the clip in another
    colours.jpg                           the range sheet

The clip is the body's colour unless a picture says otherwise (owner, 2026-10-30): the
name reads by the shadow of its 0.6 mm deboss, so every view keeps the light raking.

    py -3 tools/notrip-v51/render_all.py [only-these-keys...]
"""
import math
import pathlib
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import raster as R  # noqa: E402

REPO = HERE.parents[1]
OUT = REPO / 'src' / 'assets' / 'img' / 'notrip-leash'
FONTS = REPO / 'tools' / 'notrip-amazon' / 'assets'
D = math.radians

COLOURS = [
    ('Black', '#2B2E33'), ('White', '#ECEBE6'), ('Grey', '#6E747C'), ('Red', '#C13B2E'),
    ('Orange', '#E2652B'), ('Yellow', '#EDC220'), ('Green', '#5CBE38'), ('Teal', '#159C93'),
    ('Blue', '#2E7FD2'), ('Purple', '#9A6FCE'), ('Pink', '#E77CA6'),
]
CHARCOAL = (58, 62, 68)
# In pictures the clips are a contrasting colour so they read as separate parts (owner,
# 2026-10-30): orange, or blue where orange would not stand out against the sleeve.
ORANGE, BLUE = '#E2652B', '#2E7FD2'
CLIP_FOR = {n: (BLUE if n in ('Orange', 'Red', 'Yellow', 'Pink') else ORANGE) for n, _ in COLOURS}
BUILD = HERE / 'build'
HERO_CAM = dict(tilt=50, lay=135, roll=25)
JPG = dict(quality=80, optimize=True, progressive=True)   # the page images share a 6 MB budget
WEBP = dict(quality=82, method=6)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


_geo = {}


def geo(name):
    if name not in _geo:
        _geo[name] = R.load(HERE / 'build' / f'{name}.npz')
    return _geo[name]


def shot(asm, body_rgb, clip_rgb=None, W=1000, H=1000, tilt=50, lay=135, roll=25, margin=0.06,
         bg=None, extent=None, noclip=False, **light):
    b, c = geo(asm)
    if noclip:
        c = c[:0]
    tris, cols = R.paint(b, c, body_rgb, clip_rgb or body_rgb)
    tris = R.roll(tris, roll)
    img, _ = R.render(tris, cols, W, H, D(tilt), 0, D(lay), margin=margin, bg=bg, extent=extent, **light)
    return Image.fromarray(img)


# Standard and Large share one scale in the heroes, so the size picker swaps a longer part
# into the same frame rather than rescaling it.
def large_extent():
    b, c = geo('large-name')
    t = R.roll(np.concatenate([b, c]), HERO_CAM['roll'])
    V = t.reshape(-1, 3) @ R.rot(D(HERO_CAM['tilt']), 0, D(HERO_CAM['lay'])).T
    return tuple(np.ptp(V[:, :2], axis=0))


def job_hero(args):
    size, cname, hx = args
    # colour-picker pictures: clips in the sleeve's own colour (owner, 2026-10-30) - a contrasting
    # clip there reads as a two-colour product. Contrast clips stay in the feature pictures.
    # Black is the plain product: blank clip tops. Every other colour is personalised, so
    # its hero shows the example name.
    img = shot(f'{size}-{"blank" if cname == "Black" else "name"}', rgb(hx), extent=EXTENT, **HERO_CAM)
    # the CAD frame feeds photoreal.py; the site copy is replaced by the photo once picked
    (BUILD / 'heroes-cad').mkdir(exist_ok=True)
    img.save(BUILD / 'heroes-cad' / f'hero-{size}-{cname.lower()}.png')
    img.save(OUT / f'hero-{size}-{cname.lower()}.jpg', **JPG)
    return f'hero-{size}-{cname}'


def spin_cam(k, n):
    # about the long axis: the camera sits a little above, the part rolls a full turn
    return dict(tilt=74, lay=135, roll=25 + 360 * k / n)


def job_spin(args):
    size, k, n, folder, px = args
    # plain black, blank clip tops: the page opens on plain black (owner, 2026-10-31)
    img = shot(f'{size}-blank', CHARCOAL, W=px, H=px, extent=SPIN_EXT[size], **spin_cam(k, n))
    if folder.startswith('spin'):
        img.save(OUT / folder / f'spin-{k:02d}.webp', **WEBP)
    else:
        img.save(OUT / folder / f'{k:02d}.webp', **WEBP)
    return f'{folder}/{k}'


def spin_extent(size):
    """Largest projected span over a full roll, so the frames do not breathe."""
    b, c = geo(f'{size}-name')
    t0 = np.concatenate([b, c])
    span = np.zeros(2)
    for k in range(0, 360, 10):
        cam = spin_cam(k, 360)
        V = R.roll(t0, cam['roll']).reshape(-1, 3) @ R.rot(D(cam['tilt']), 0, D(cam['lay'])).T
        span = np.maximum(span, np.ptp(V[:, :2], axis=0))
    return tuple(span)


def job_misc(key):
    if key == 'hero':
        shot('standard-name', CHARCOAL, W=1200, H=900, **HERO_CAM).save(OUT / 'hero.jpg', **JPG)
    elif key == 'pair':
        # side-on, both clips up: one bridging the joint, one locking the far end
        shot('large-name', CHARCOAL, W=1200, H=448, tilt=30, lay=90, roll=0, margin=0.04
             ).save(OUT / 'pair-joined.jpg', **JPG)
    elif key in ('clip-name', 'clip-blank'):
        # the connector seen from above and a little in front, name reading left to right
        # low raking light from the side, so the 0.6 mm deboss throws a shadow worth reading
        shot(key, rgb('#E2652B'), W=1200, H=800, tilt=62, lay=90, roll=0, margin=0.10,
             light=(-0.85, 0.35, 0.4), ambient=0.30, spec=0.25).save(OUT / f'{key}.jpg', **JPG)
    elif key.startswith('clip-top/'):
        # the PDP's live name preview: blank clip straight down, framed on exactly its
        # 40 x 23.64 mm footprint plus the 6% margin, so 1 mm = 1/44.8 of the width
        # (the page lays the typed name over the flat top in those units)
        n = key.split('/')[1]
        hx = dict((c.lower(), h) for c, h in COLOURS)[n]
        (OUT / 'clip-top').mkdir(exist_ok=True)
        shot('clip-blank', rgb(hx), W=800, H=473, tilt=90, lay=90, roll=0, margin=0.06,
             extent=(40.0, 23.64)).save(OUT / 'clip-top' / f'{n}.webp', **WEBP)
    elif key == 'clip-match':
        # the other option: clips in the sleeve's own colour
        shot('standard-name', rgb(BLUE), rgb(BLUE), W=1200, H=900, **HERO_CAM).save(OUT / 'clip-match.jpg', **JPG)
    elif key.startswith('swatch/'):
        # Amazon's colour picker: the sleeve alone, so the swatch is one colour
        n = key.split('/')[1]
        hx = dict((c.lower(), h) for c, h in COLOURS)[n]
        (BUILD / 'swatch').mkdir(exist_ok=True)
        shot('standard-name', rgb(hx), noclip=True, **HERO_CAM).save(BUILD / 'swatch' / f'{n}.png')
    return key


def colours_sheet():
    tw, th, cols, pad, lab = 300, 300, 4, 12, 26
    rows = math.ceil(len(COLOURS) / cols)
    W = cols * tw + (cols + 1) * pad
    H = rows * (th + lab) + (rows + 1) * pad
    sheet = Image.new('RGB', (W, H), (250, 250, 249))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(str(FONTS / 'BarlowCondensed-SemiBold.ttf'), 20)
    for i, (n, _) in enumerate(COLOURS):
        im = Image.open(OUT / f'hero-standard-{n.lower()}.jpg').resize((tw, th), Image.LANCZOS)
        x, y = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + lab + pad)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + th + 2), n.upper(), fill=(24, 27, 32), font=f)
    sheet.save(OUT / 'colours.jpg', **JPG)


EXTENT = None
SPIN_EXT = {}


def init():
    global EXTENT, SPIN_EXT
    EXTENT = large_extent()
    SPIN_EXT = {s: spin_extent(s) for s in ('standard', 'large')}


def main():
    want = set(sys.argv[1:])
    on = lambda k: not want or k in want  # noqa: E731
    jobs = []
    if on('heroes'):
        jobs += [(job_hero, (s, n, hx)) for s in ('standard', 'large') for n, hx in COLOURS]
    if on('black-heroes'):
        jobs += [(job_hero, (s, 'Black', dict(COLOURS)['Black'])) for s in ('standard', 'large')]
    for size, folder, n, px in (('standard', 'spin', 36, 1000), ('large', 'spin-large', 36, 1000),
                                ('standard', 'mini-standard', 24, 300), ('large', 'mini-large', 24, 300)):
        if on('spins' if px == 1000 else 'minis'):
            (OUT / folder).mkdir(exist_ok=True)
            jobs += [(job_spin, (size, k, n, folder, px)) for k in range(n)]
    for k in ('hero', 'pair', 'clip-name', 'clip-blank', 'clip-match'):
        if on(k) or on('misc'):
            jobs.append((job_misc, k))
    if on('swatches'):
        jobs += [(job_misc, f'swatch/{n.lower()}') for n, _ in COLOURS]
    if on('cliptops'):
        jobs += [(job_misc, f'clip-top/{n.lower()}') for n, _ in COLOURS]
    with Pool(20, initializer=init) as pool:
        for i, r in enumerate(pool.imap_unordered(_run, jobs), 1):
            print(f'{i}/{len(jobs)} {r}', flush=True)
    if on('heroes') or on('colours'):
        colours_sheet()
        print('colours.jpg')


def _run(j):
    return j[0](j[1])


if __name__ == '__main__':
    main()
