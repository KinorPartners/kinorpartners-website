"""Write main-in-use-standard-<colour>.jpg: the in-use MAIN scene with its sleeve recoloured.

main-in-use-master.jpg is the purple master (dog, leash and hand already greyed). Run this
before compose.py whenever the master or a hero render changes:

    py -3 -I tools/notrip-amazon/recolour_main.py
Target colour = median Lab of the part in that colour's hero render."""
import sys, pathlib, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import color
HERE = pathlib.Path(__file__).resolve().parent; W = HERE.parents[1]
sys.path.insert(0, str(W / 'tools' / 'notrip-amazon'))
import compose as C
SRC = W / 'src/assets/img/notrip-leash'
base = np.asarray(Image.open(HERE / 'in-use' / 'main-in-use-master.jpg').convert('RGB')).astype(float) / 255

hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV')).astype(int)
m = ndimage.binary_opening((hsv[..., 0] >= 175) & (hsv[..., 0] <= 225) & (hsv[..., 1] >= 60) & (hsv[..., 2] >= 40), iterations=2)
lab_, n = ndimage.label(m); sizes = ndimage.sum(m, lab_, range(1, n + 1))
keep = ndimage.binary_fill_holes(ndimage.binary_closing(lab_ == 1 + sizes.argmax(), iterations=6))
alpha = ndimage.gaussian_filter(keep.astype(float), 1.2)[..., None]
L = color.rgb2lab(base)
src_med = np.median(L[keep], axis=0)

for code, name in C.COLOURS.items():
    hero = C.load(f'hero-standard-{name}.jpg')
    hm = np.asarray(C.cutout(hero)) > 200
    hm = ndimage.binary_erosion(hm, iterations=6)
    tgt = np.median(color.rgb2lab(np.asarray(hero).astype(float) / 255)[hm], axis=0)
    out = L.copy()
    dL = L[..., 0] - src_med[0]
    # keep the moulded lettering legible on very light and very dark parts
    gain = 0.9 if 25 < tgt[0] < 80 else 1.1
    out[..., 0] = np.clip(tgt[0] + dL * gain, 0, 100)
    out[..., 1] = tgt[1] + (L[..., 1] - src_med[1]) * 0.15
    out[..., 2] = tgt[2] + (L[..., 2] - src_med[2]) * 0.15
    rgb = np.clip(color.lab2rgb(out), 0, 1)
    comp = base * (1 - alpha) + rgb * alpha
    im = Image.fromarray((comp * 255).round().astype(np.uint8))
    im.save(HERE / 'in-use' / f'main-in-use-standard-{name}.jpg', quality=92, subsampling=0)
    print(code, name, 'target Lab', np.round(tgt, 1))
