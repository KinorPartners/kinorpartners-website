"""Draft: a before/after Amazon MAIN made locally (no image API).

BEFORE = the key BEFORE doodle (leash pooled round the paws) on white and grey
(ai/main-before-master-1.png, one Gemini 2.1 edit - a rembg cut-out off the grass left a fringe). AFTER = the white-background in-use MAIN for that colour. Both inset on a pure
white 2000 x 2000 canvas, no text: the coloured sleeve is the only colour, so the eye reads
left-to-right as problem -> fix without labels. Same inset-on-white recipe the Shirt Tucker
composite MAIN cleared Amazon with.

    py -3 tools/notrip-v51/ba_main.py <standard|large>   -> build/ba-main-<size>-<colour>.png (all 11)
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
NOTRIP = pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners' / 'Clients' / '8. NoTrip Sleeve'
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
        after = lift(Image.open(REPO / 'tools' / 'notrip-amazon' / 'in-use' / f'main-in-use-{size}-{colour}.jpg'))
        compose(before, after, HERE / 'build' / f'ba-main-{size}-{colour}.png')


COLOURS = 'black white grey red orange yellow green teal blue purple pink'.split()


def compose(before, after, out):

    canvas = Image.new('RGB', (S, S), (255, 255, 255))
    half = (S - 2 * M - 40) // 2
    for i, part in enumerate((before, after)):
        sc = min(half / part.width, (S - 2 * M) / part.height)
        p = part.resize((round(part.width * sc), round(part.height * sc)), Image.LANCZOS)
        x = M + i * (half + 40) + (half - p.width) // 2
        y = (S + round(min(before.height * half / before.width, after.height * half / after.width))) // 2 - p.height
        canvas.paste(p, (x, y), p)
    A = np.asarray(canvas)
    edge = np.concatenate([A[0], A[-1], A[:, 0], A[:, -1]])
    canvas.save(out)
    print(out.name, 'edge pixels all white:', bool((edge == 255).all()))


if __name__ == '__main__':
    main()
