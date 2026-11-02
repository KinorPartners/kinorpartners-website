"""Write main-in-use-<standard|large>-<colour>.jpg: the in-use scenes recoloured for every colour.

main-in-use-master.jpg (Standard) and main-in-use-large-master.jpg (golden, 2 sleeves, 3 clips)
are the masters. Standard: the key AFTER doodle on white, sleeve and both clips
purple, everything else greyed (an older master had orange clips; both work). Sleeve and clips both take each colour: these are the per-colour MAIN pictures, and a
contrasting clip there reads as a two-colour product (owner, 2026-10-30). Run this before compose.py
whenever the master or the swatch renders change:

    py -3 -I tools/notrip-amazon/recolour_main.py

Target colour = median Lab of the part in tools/notrip-v51/build/swatch/<colour>.png, the
sleeve rendered without its clips (the heroes carry clips, which would skew the median)."""
import sys, pathlib, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import color
HERE = pathlib.Path(__file__).resolve().parent; W = HERE.parents[1]
sys.path.insert(0, str(W / 'tools' / 'notrip-amazon'))
import compose as C
SWATCH = W / 'tools' / 'notrip-v51' / 'build' / 'swatch'

def part_mask(hsv, hue_lo, hue_hi):
    """The coloured part in a hue band. v5.1 is an open channel: the grey leash shows through
    and must stay grey (not included), so no hole filling - a small closing only, enough to
    take in the clip lettering."""
    m = ndimage.binary_opening((hsv[..., 0] >= hue_lo) & (hsv[..., 0] <= hue_hi)
                               & (hsv[..., 1] >= 60) & (hsv[..., 2] >= 40), iterations=2)
    lab_, n = ndimage.label(m)
    if n == 0:
        return m, np.zeros(m.shape + (1,))
    sizes = ndimage.sum(m, lab_, range(1, n + 1))
    keep = ndimage.binary_closing(np.isin(lab_, 1 + np.flatnonzero(sizes > 0.02 * sizes.max())), iterations=3)
    return keep, ndimage.gaussian_filter(keep.astype(float), 1.2)[..., None]




def target(name):
    sw = Image.open(SWATCH / f'{name}.png').convert('RGB')
    m = ndimage.binary_erosion(np.asarray(C.cutout(sw)) > 200, iterations=6)
    return np.median(color.rgb2lab(np.asarray(sw).astype(float) / 255)[m], axis=0)


def recolour(L, mask, tgt):
    src = np.median(L[mask], axis=0)
    out = L.copy()
    # keep the moulded lettering legible on very light and very dark parts
    gain = 0.9 if 25 < tgt[0] < 80 else 1.1
    out[..., 0] = np.clip(tgt[0] + (L[..., 0] - src[0]) * gain, 0, 100)
    out[..., 1] = tgt[1] + (L[..., 1] - src[1]) * 0.15
    out[..., 2] = tgt[2] + (L[..., 2] - src[2]) * 0.15
    return np.clip(color.lab2rgb(out), 0, 1)


for size, master in (('standard', 'main-in-use-master.jpg'), ('large', 'main-in-use-large-master.jpg')):
    base = np.asarray(Image.open(HERE / 'in-use' / master).convert('RGB')).astype(float) / 255
    hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV')).astype(int)
    sleeve, a_sleeve = part_mask(hsv, 175, 225)   # purple
    clips, a_clips = part_mask(hsv, 5, 28)        # orange (older masters only)
    L = color.rgb2lab(base)
    for code, name in C.COLOURS.items():
        tgt = target(name)
        comp = base * (1 - a_sleeve) + recolour(L, sleeve, tgt) * a_sleeve
        if clips.any():
            comp = comp * (1 - a_clips) + recolour(L, clips, tgt) * a_clips
        Image.fromarray((comp * 255).round().astype(np.uint8)).save(
            HERE / 'in-use' / f'main-in-use-{size}-{name}.jpg', quality=92, subsampling=0)
        print(size, code, name, 'target Lab', np.round(tgt, 1))
