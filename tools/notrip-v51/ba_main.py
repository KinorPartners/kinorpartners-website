"""Draft: a before/after Amazon MAIN made locally (no image API).

BEFORE = the key BEFORE doodle (leash pooled round the paws) on white and grey
(ai/main-before-master-1.png, one Gemini 2.1 edit - a rembg cut-out off the grass left a fringe). AFTER = the white-background in-use MAIN for that colour. Both inset on a pure
white 2000 x 2000 canvas, no text: the coloured sleeve is the only colour, so the eye reads
left-to-right as problem -> fix without labels. Same inset-on-white recipe the Shirt Tucker
composite MAIN cleared Amazon with.

Tails and leash (owner, 2026-11-06): the composed picture then gets patches/ba-main-<size>-tails.png
laid over it - the BEFORE dog's tail hangs low (sad), the AFTER dog's is raised mid-wag (happy),
the BEFORE leash is a short slack across the paws instead of the big floor loop, and it is cut at
the centre line rather than running off the top. Each patch is one approved Gemini 2.1 edit
registered onto this script's own output, so it only lines up while compose() stays as it is: if
you change the layout, remake the patch. Its alpha never covers a sleeve pixel, so every colour
keeps the sleeve exactly as recolour_main.py made it.

    py -3 tools/notrip-v51/ba_main.py <standard|large>   -> build/ba-main-<size>-<colour>.png (all 11)
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
NOTRIP = pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners' / 'Clients & Products' / '8. NoTrip Sleeve'
S, M = 2000, 70          # canvas, outer margin


def lift(im):
    """A subject already on pure white, given an alpha from how far each pixel is from white.
    Only the largest connected subject is kept, so a stray (a walker's trouser leg the edit
    left at the frame edge) does not come along."""
    from scipy import ndimage
    im = im.convert('RGB')
    a = np.clip((255 - np.asarray(im.convert('L')).astype(int)) * 6, 0, 255).astype(np.uint8)
    lab_, n = ndimage.label(a > 40)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(a), lab_, range(1, n + 1))
        keep = ndimage.binary_dilation(lab_ == 1 + sizes.argmax(), iterations=3)
        a = np.where(keep, a, 0).astype(np.uint8)
    a = Image.fromarray(a).filter(ImageFilter.GaussianBlur(1))
    im = im.copy()
    im.putalpha(a)
    return im.crop(a.getbbox())


def main():
    size = sys.argv[1] if len(sys.argv) > 1 else 'standard'
    before_master = 'main-before-master-1.png' if size == 'standard' else 'main-before-large-1.png'
    before = lift(Image.open(HERE / 'ai' / before_master))
    for colour in COLOURS:
        after = Image.open(REPO / 'tools' / 'notrip-amazon' / 'in-use' / f'main-in-use-{size}-{colour}.jpg')
        if size == 'standard':
            # its AI shadow sat ~70 px below the tip, so the sleeve hovered (owner, 2026-11-05)
            from tip_contact import ground_tip
            ref = Image.open(REPO / 'tools' / 'notrip-amazon' / 'in-use' / f'main-in-use-{size}-blue.jpg')
            after = ground_tip(after, ref)
        after = lift(after)
        out = HERE / 'build' / f'ba-main-{size}-{colour}.png'
        compose(before, after, out)
        tails(out, size)


def tails(out, size):
    """Lay the sad/happy tail + short-leash patch over a composed MAIN (see the docstring)."""
    patch = Image.open(HERE / 'patches' / f'ba-main-{size}-tails.png').convert('RGBA')
    im = Image.open(out).convert('RGBA')
    assert im.size == patch.size, f'{out.name}: patch is {patch.size}, picture {im.size} - remake the patch'
    Image.alpha_composite(im, patch).convert('RGB').save(out)


COLOURS = 'black white grey red orange yellow green teal blue purple pink'.split()


def dog_rows(part):
    """Top and bottom row of the dog: rows where the subject is wider than a leash strip."""
    a = np.asarray(part.getchannel('A')) > 60
    wide = np.nonzero(a.sum(1) > 0.18 * part.width)[0]
    return wide.min(), wide.max()


def extend_leash(p, up, K=36):
    """Carry the leash strip at the top of p straight on upward by `up` px, so it leaves the
    frame instead of ending in mid-air: repeat its top band of webbing along its own slope."""
    if up <= 0:
        return p
    from scipy import ndimage
    r0 = 10                                          # skip the ragged cut edge
    p = p.crop((0, r0, p.width, p.height))
    up += r0
    A = np.asarray(p.getchannel('A')) > 60
    lab, n = ndimage.label(A[:K])
    # the leash is the right-most shape in the band (the dog's head can reach it on the left)
    lid = max(range(1, n + 1), key=lambda k: np.nonzero(lab == k)[1].mean())
    keep = lab == lid
    cx = lambda r: np.nonzero(keep[r])[0].mean()
    slope = (cx(0) - cx(K - 1)) / (K - 1)            # px right per px up
    band = p.crop((0, 0, p.width, K))
    ba = np.asarray(band).copy()
    ba[..., 3] = np.where(keep, ba[..., 3], 0)
    band = Image.fromarray(ba)
    n = int(np.ceil(up / K)) + 1
    grow = max(0, int(np.ceil(slope * K * n)) + 2)
    out = Image.new('RGBA', (p.width + grow, p.height + up), (0, 0, 0, 0))
    out.paste(p, (0, up), p)
    for i in range(1, n + 1):
        # behind what is already there, so seams fall under the band below
        layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
        layer.paste(band, (round(slope * K * i), up - K * i + 1))
        out = Image.alpha_composite(layer, out)
    return out


def compose(before, after, out):
    """Both dogs at the SAME height, as big as the half-width allows; the leash running up
    past the dog is allowed to leave the top of the frame (owner, 2026-11-05)."""
    canvas = Image.new('RGB', (S, S), (255, 255, 255))
    m, gap, head = 40, 30, 0.14          # side margin, gap, leash kept above the dog (x dog height)
    parts = []
    for part in (before, after):
        t, b = dog_rows(part)
        dh = b - t
        # cut the leash a little above the dog: it then runs off the top of the frame
        part = part.crop((0, max(0, round(t - head * dh)), part.width, part.height))
        part = part.crop(part.getchannel('A').getbbox())     # re-tighten (the leash's far end is gone)
        t2, b2 = dog_rows(part)
        parts.append((part, t2, b2))
    # each panel is as wide as its dog + the low leash (rows below mid-dog); the leash rising
    # above that is free to cross the open sky between the dogs and leave the frame
    def foot(p, t, b):
        a = np.asarray(p.getchannel('A'))[round(t + 0.45 * (b - t)):] > 60
        return np.nonzero(a.any(0))[0].max() + 1
    feet = [foot(*q) for q in parts]
    ratio = sum(f / (b - t) for f, (p, t, b) in zip(feet, parts))
    H = (S - 2 * m - gap) / ratio
    H = min(H, 0.62 * S)
    sc = [H / (b - t) for p, t, b in parts]
    widths = [round(f * s) for f, s in zip(feet, sc)]
    x = (S - sum(widths) - gap) // 2
    # centre the dogs (top of dog to paws) in the frame; the leash is then carried up to the edge
    for (part, t, b), s, w in zip(parts, sc, widths):
        p = part.resize((round(part.width * s), round(part.height * s)), Image.LANCZOS)
        y = round(0.56 * S - H / 2 - t * s)
        p = extend_leash(p, y)
        canvas.paste(p, (x, y - (p.height - round(part.height * s))), p)
        x += w + gap
    A = np.asarray(canvas)
    edge = np.concatenate([A[0], A[-1], A[:, 0], A[:, -1]])
    canvas.save(out)
    print(out.name, 'edge pixels all white:', bool((edge == 255).all()))


if __name__ == '__main__':
    main()
