"""Build the Amazon listing images for the Cadenza No-Trip Leash.

Reads the concept renders and photos in src/assets/img/notrip-leash/ and writes
2000x2000 JPEGs to src/assets/img/notrip-leash/amazon/, named the way the
PatchDesign listing tool (scripts/amazon-listings/create-listings.mjs) builds
image URLs:

    KP-NT-<S|L>-<COLOUR>.MAIN.jpg   one per child SKU, plus KP-NT.MAIN.jpg for the parent
    KP-NT.PT01.jpg .. PT08.jpg      shared by every SKU (sharedImageSlots)

MAIN is the product alone on pure white (255,255,255): Amazon suppresses a
listing whose main image carries text, logos or badges, so the Cadenza wordmark
and the Made in the USA flag go only on PT01-PT08, in a band along the bottom.

    py -3 -I tools/notrip-amazon/compose.py
"""
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SRC = REPO / 'src' / 'assets' / 'img' / 'notrip-leash'
OUT = SRC / 'amazon'
ASSETS = HERE / 'assets'
S = 2000
BAND = 190
NAVY, MUTED, RULE, WHITE = (13, 27, 46), (90, 106, 122), (222, 226, 231), (255, 255, 255)
RED, BLUE = (178, 34, 52), (60, 59, 110)

COLOURS = {
    'BLK': 'black', 'WHT': 'white', 'GRY': 'grey', 'RED': 'red', 'ORG': 'orange', 'YEL': 'yellow',
    'GRN': 'green', 'TEL': 'teal', 'BLU': 'blue', 'PUR': 'purple', 'PNK': 'pink',
}
SIZES = {'S': 'standard', 'L': 'large'}


def font(name, size):
    return ImageFont.truetype(str(ASSETS / name), size)


H = lambda s: font('BarlowCondensed-Black.ttf', s)
B = lambda s: font('BarlowCondensed-SemiBold.ttf', s)


def load(name):
    return Image.open(SRC / name).convert('RGB')


# ---------------------------------------------------------------- MAIN

def cutout(im):
    """Separate the part from the render's smooth light-grey gradient backdrop.

    The backdrop shades across both axes, so fit a quadratic surface per channel
    to a ring of border pixels and call anything well off that surface product.
    """
    a = np.asarray(im).astype(np.float64)
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    basis = np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], axis=-1)
    ring = np.zeros((h, w), bool)
    ring[:24], ring[-24:], ring[:, :24], ring[:, -24:] = True, True, True, True
    bg = np.empty_like(a)
    for ch in range(3):
        coef, *_ = np.linalg.lstsq(basis[ring], a[..., ch][ring], rcond=None)
        bg[..., ch] = basis @ coef
    diff = np.abs(a - bg).max(axis=2)
    mask = Image.fromarray(((diff > 9) * 255).astype(np.uint8))
    # close pin-holes where the shading on a pale part matches the backdrop
    mask = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    mask = fill_holes(mask)
    return mask.filter(ImageFilter.GaussianBlur(1.2))


def fill_holes(mask):
    m = np.asarray(mask) > 127
    # .copy(): floodfill is a silent no-op on the read-only view fromarray returns
    outside = Image.fromarray(((~m) * 255).astype(np.uint8)).copy()
    ImageDraw.floodfill(outside, (0, 0), 128)
    o = np.asarray(outside)
    return Image.fromarray(np.where(o == 128, 0, 255).astype(np.uint8))


def main_image(src_name):
    im = load(src_name)
    mask = cutout(im)
    box = mask.getbbox()
    part, m = im.crop(box), mask.crop(box)
    scale = (S * 0.86) / max(part.size)
    size = (round(part.width * scale), round(part.height * scale))
    part, m = part.resize(size, Image.LANCZOS), m.resize(size, Image.LANCZOS)
    canvas = Image.new('RGB', (S, S), WHITE)
    canvas.paste(part, ((S - size[0]) // 2, (S - size[1]) // 2), m)
    return canvas


# ---------------------------------------------------------------- band

def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -np.pi / 2 + i * np.pi / 5
        rr = r if i % 2 == 0 else r * 0.4
        pts.append((cx + rr * np.cos(ang), cy + rr * np.sin(ang)))
    d.polygon(pts, fill=fill)


def flag(w):
    """US flag at 10:19, drawn so it is crisp at any size."""
    h = round(w * 10 / 19)
    f = Image.new('RGB', (w * 4, h * 4), WHITE)
    d = ImageDraw.Draw(f)
    W, Hh = f.size
    sh = Hh / 13
    for i in range(0, 13, 2):
        d.rectangle([0, round(i * sh), W, round((i + 1) * sh)], fill=RED)
    cw, ch = W * 0.4, sh * 7
    d.rectangle([0, 0, cw, ch], fill=BLUE)
    for row in range(9):
        n = 6 if row % 2 == 0 else 5
        for col in range(n):
            x = cw / 12 * (2 * col + (1 if row % 2 == 0 else 2))
            y = ch / 10 * (row + 1)
            star(d, x, y, sh * 0.31, WHITE)
    return f.resize((w, h), Image.LANCZOS)


WORDMARK = Image.open(ASSETS / 'cadenza-wordmark-color-light-1024.png').convert('RGBA')


def band(canvas):
    d = ImageDraw.Draw(canvas)
    top = S - BAND
    d.rectangle([0, top, S, S], fill=WHITE)
    d.line([(60, top), (S - 60, top)], fill=RULE, width=3)
    mid = top + BAND // 2
    wm_h = 72
    wm = WORDMARK.resize((round(WORDMARK.width * wm_h / WORDMARK.height), wm_h), Image.LANCZOS)
    canvas.paste(wm, (70, mid - wm_h // 2), wm)
    text, tf = 'MADE IN THE USA', H(72)
    tw = d.textlength(text, font=tf)
    fl = flag(150)
    x = S - 70 - tw
    d.text((x, mid), text, font=tf, fill=NAVY, anchor='lm')
    fx = round(x - 30 - fl.width)
    canvas.paste(fl, (fx, mid - fl.height // 2))
    d.rectangle([fx, mid - fl.height // 2, fx + fl.width - 1, mid + (fl.height + 1) // 2 - 1], outline=RULE, width=2)
    return canvas


# ---------------------------------------------------------------- slots

AREA = (S, S - BAND)


def cover(im, area=AREA):
    w, h = area
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def contain(im, area=AREA, pad=0):
    w, h = area[0] - 2 * pad, area[1] - 2 * pad
    scale = min(w / im.width, h / im.height)
    return im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)


def on_white(im, top=0, pad=60):
    c = Image.new('RGB', (S, S), WHITE)
    im = contain(im, (S, S - BAND - top), pad)
    c.paste(im, ((S - im.width) // 2, top + (S - BAND - top - im.height) // 2))
    return c


def headline(c, title, sub=None, y=90):
    d = ImageDraw.Draw(c)
    d.text((S // 2, y), title, font=H(120), fill=NAVY, anchor='mt')
    if sub:
        d.text((S // 2, y + 150), sub, font=B(62), fill=MUTED, anchor='mt')
    return c


def photo(name):
    c = Image.new('RGB', (S, S), WHITE)
    c.paste(cover(load(name)), (0, 0))
    return band(c)


def sizing():
    c = Image.new('RGB', (S, S), WHITE)
    headline(c, 'WHICH SIZE?', 'Measure from the floor to the top of the shoulder')
    d = ImageDraw.Draw(c)
    cols = [
        ('STANDARD', '1 piece  ·  6.0 in', 'Up to 20 in at the shoulder',
         ['Dachshund  9 in', 'French Bulldog  12 in', 'Cavalier  13 in', 'Mini Schnauzer  13 in',
          'Beagle  14 in', 'Cocker Spaniel  16 in'], 'hero-standard-black.jpg'),
        ('LARGE', '2 pieces  ·  11.4 in', '20 to 30 in at the shoulder',
         ['Australian Shepherd  21 in', 'Standard Poodle  21 in', 'Labrador  23 in',
          'Golden Retriever  23 in', 'German Shepherd  24 in', 'Rottweiler / Boxer  24 in'], 'hero-large-black.jpg'),
    ]
    for i, (name, spec, rng, breeds, img) in enumerate(cols):
        x0 = 90 + i * 930
        d.rounded_rectangle([x0, 330, x0 + 890, 1700], radius=36, outline=RULE, width=4)
        part = main_image(img)
        part = part.crop(part.convert('L').point(lambda v: 255 if v < 250 else 0).getbbox())
        part = contain(part, (520, 360))
        c.paste(part, (x0 + (890 - part.width) // 2, 380))
        cx = x0 + 445
        d.text((cx, 790), name, font=H(110), fill=NAVY, anchor='mt')
        d.text((cx, 920), spec, font=B(60), fill=NAVY, anchor='mt')
        d.text((cx, 1000), rng, font=B(56), fill=MUTED, anchor='mt')
        for j, b in enumerate(breeds):
            d.text((cx, 1110 + j * 88), b, font=B(56), fill=NAVY, anchor='mt')
    d.text((S // 2, 1740), 'Between the two? Take Large: it is two of the same piece.', font=B(56), fill=MUTED, anchor='mt')
    return band(c)


def pair():
    c = Image.new('RGB', (S, S), WHITE)
    headline(c, 'TWO CLICK TOGETHER', 'Slots face opposite ways, so the leash is held captive')
    im = main_image('pair-joined.jpg')
    im = im.crop(im.convert('L').point(lambda v: 255 if v < 250 else 0).getbbox())
    im = contain(im, (S - 160, S - BAND - 400))
    c.paste(im, ((S - im.width) // 2, 360 + (S - BAND - 360 - im.height) // 2))
    return band(c)


def colours():
    c = Image.new('RGB', (S, S), WHITE)
    headline(c, '11 COLORS', 'The same part in every color')
    im = load('colours.jpg')
    im = im.crop((0, 24, im.width, im.height))   # drop the page's small caption
    im = contain(im, (S - 120, S - BAND - 420))
    c.paste(im, ((S - im.width) // 2, 380 + (S - BAND - 380 - im.height) // 2))
    return band(c)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = dict(quality=90, optimize=True, progressive=True)
    for code, colour in COLOURS.items():
        for sz, size in SIZES.items():
            main_image(f'hero-{size}-{colour}.jpg').save(OUT / f'KP-NT-{sz}-{code}.MAIN.jpg', **q)
    main_image('hero-large-black.jpg').save(OUT / 'KP-NT.MAIN.jpg', **q)

    slots = {
        'PT01': band(on_white(load('before-after-labelled.jpg'), pad=40)),
        'PT02': photo('lifestyle-hand-labelled.jpg'),
        'PT03': photo('lifestyle-golden.jpg'),
        'PT04': pair(),
        'PT05': sizing(),
        'PT06': photo('detail-clip.jpg'),
        'PT07': band(on_white(load('before-after-small-labelled.jpg'), pad=40)),
        'PT08': colours(),
    }
    for slot, im in slots.items():
        im.save(OUT / f'KP-NT.{slot}.jpg', **q)
    print(f'wrote {len(list(OUT.glob("*.jpg")))} images to {OUT}')


if __name__ == '__main__':
    main()
