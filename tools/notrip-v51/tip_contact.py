"""Ground the sleeve tip in the in-use MAIN (owner 2026-11-05: "a version of the tip touching
the ground"). The AI scene drew the sleeve's drop shadow ~70 px below the tip, so the tip
reads as hovering. Locally, no image API: lift that stray shadow off the white floor, then
paint a tight contact shadow right under the tip so it reads as resting on the ground.

Neutral sleeves (black/white/grey) take their mask from a coloured recolour via ref=.

    py -3 tools/notrip-v51/tip_contact.py <in.jpg> <out.png>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def sleeve_mask(im):
    """The sleeve: the only saturated thing in a coloured scene (dog, leash, floor are grey)."""
    a = np.asarray(im.convert('RGB')).astype(np.float64)
    return (a.max(2) - a.min(2)) > 45


def ground_tip(im, ref=None):
    """ref: a saturated recolour of the same scene (black/white/grey sleeves have no colour
    to find them by; every recolour shares one geometry, so its mask fits them all)."""
    a = np.asarray(im.convert('RGB')).astype(np.float64)
    h, w, _ = a.shape
    L = a.mean(2)
    sleeve = sleeve_mask(ref if ref is not None else im)
    ys, xs = np.nonzero(sleeve[h // 2:])
    ys = ys + h // 2
    ty = ys.max()
    tx = int(xs[ys >= ty - 4].mean())

    # 1. lift the stray shadow: in a box below/right of the tip, any light-grey floor pixel
    #    (not sleeve, not fur) goes back to white, feathered at the box edge
    box = np.zeros((h, w))
    x0, x1, y0, y1 = tx - 120, tx + 280, ty + 8, ty + 200
    box[y0:y1, x0:x1] = 1
    box = np.asarray(Image.fromarray((box * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))) / 255
    floor = (L > 120) & ~sleeve
    k = (box * floor)[..., None]
    a = a * (1 - k) + 255 * k

    # 2. contact shadow: a soft halo and a dark core, hugging the tip, on the floor only
    sh = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(sh)
    d.ellipse([tx - 95, ty - 14, tx + 95, ty + 22], fill=70)
    soft = np.asarray(sh.filter(ImageFilter.GaussianBlur(16))) / 255
    core = Image.new('L', (w, h), 0)
    ImageDraw.Draw(core).ellipse([tx - 42, ty - 6, tx + 42, ty + 9], fill=150)
    core = np.asarray(core.filter(ImageFilter.GaussianBlur(5))) / 255
    dark = 1 - (1 - soft) * (1 - core)
    onfloor = np.clip((L - 170) / 60, 0, 1) * ~sleeve
    a = a * (1 - (dark * onfloor)[..., None] * 0.85)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    ground_tip(Image.open(sys.argv[1])).save(sys.argv[2])
