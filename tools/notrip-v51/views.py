"""One colourway, every view: the sheet to agree camera angles on before rendering all colours.

    py -3 tools/notrip-v51/views.py [body_hex] [clip_hex]   -> build/views/*.png + build/views.html
"""
import math
import pathlib
import sys
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_all as A  # noqa: E402

OUT = HERE / 'build' / 'views'
BODY = A.rgb(sys.argv[1] if len(sys.argv) > 1 else '#2B2E33')
CLIP = A.rgb(sys.argv[2] if len(sys.argv) > 2 else '#E2652B')

VIEWS = [
    # name, assembly, size, camera, caption
    ('std-hero', 'standard-name', (1000, 1000), dict(tilt=50, lay=135, roll=25), 'Standard - hero (3/4 from above)'),
    ('lrg-hero', 'large-name', (1000, 1000), dict(tilt=50, lay=135, roll=25), 'Large - hero (3/4 from above)'),
    ('std-side', 'standard-name', (1400, 500), dict(tilt=78, lay=90, roll=30), 'Standard - side, slightly from above'),
    ('lrg-side', 'large-name', (1400, 400), dict(tilt=78, lay=90, roll=30), 'Large - side, slightly from above'),
    ('std-top', 'standard-name', (1400, 400), dict(tilt=90, lay=90, roll=0), 'Standard - straight down (names read)'),
    ('lrg-top', 'large-name', (1400, 300), dict(tilt=90, lay=90, roll=0), 'Large - straight down'),
    ('std-under', 'standard-name', (1000, 1000), dict(tilt=74, lay=135, roll=205), 'Standard - underside (CADENZA / NO-TRIP SLEEVE)'),
    ('std-end', 'standard-name', (1000, 1000), dict(tilt=30, lay=135, roll=25), 'Standard - down the channel'),
    ('clip', 'clip-name', (1200, 800), dict(tilt=62, lay=90, roll=0, light=(-0.85, 0.35, 0.4), ambient=0.30, spec=0.25), 'One clip, close'),
]
VIEWS += [(f'spin-{k:02d}', 'standard-name', (700, 700), A.spin_cam(k, 8), f'360 frame {k + 1}/8') for k in range(8)]


def job(v):
    name, asm, (W, H), cam, _ = v
    cam = dict(cam)
    light = {k: cam.pop(k) for k in ('light', 'ambient', 'spec') if k in cam}
    body = BODY
    A.shot(asm, body, CLIP, W=W, H=H, margin=0.05, **cam, **light).save(OUT / f'{name}.png')
    return name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(17) as pool:
        for n in pool.imap_unordered(job, VIEWS):
            print(n, flush=True)
    rows = ''.join(f'<figure><img src="views/{n}.png"><figcaption>{c}</figcaption></figure>'
                   for n, _, _, _, c in VIEWS)
    (HERE / 'build' / 'views.html').write_text(
        '<!doctype html><meta charset=utf-8><title>No-Trip v5.1 views</title><style>body{font:14px system-ui;'
        'margin:20px;background:#f6f7f9}.g{display:flex;flex-wrap:wrap;gap:12px}figure{margin:0;background:#fff;'
        'border:1px solid #ddd;border-radius:8px;padding:6px;max-width:100%}img{display:block;max-width:100%;'
        'max-height:460px}figcaption{font-size:12px;color:#555;padding-top:4px}</style>'
        '<h1>No-Trip Sleeve v5.1 - views in one colourway</h1><p>Standard: 1 sleeve, 2 clips. '
        'Large: 2 sleeves, 3 clips. Sleeve and clips in contrasting colours.</p><div class=g>' + rows + '</div>',
        encoding='utf-8')


if __name__ == '__main__':
    main()
