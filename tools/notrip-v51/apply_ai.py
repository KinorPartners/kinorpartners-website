"""Put the reviewed v5.1 AI edits in place and rebuild everything made from them.

    1. the picked candidate replaces its master in NoTrip marketing/images (the v4
       master is kept beside it as <name>-v4.png, once)
    2. the slack before/afters are re-joined: the untouched BEFORE panel + the new
       lead-slack shot, 8 px white gutter, as before
    3. that folder's label_pairs.py redraws the BEFORE/AFTER headings and captions
    4. each site JPEG is rewritten from its master at the size the page already uses

    py -3 tools/notrip-v51/apply_ai.py
"""
import os
import pathlib
import shutil
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SITE = REPO / 'src' / 'assets' / 'img' / 'notrip-leash'
NOTRIP = pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners' / 'Clients & Products' / '8. NoTrip Sleeve'
IMG = NOTRIP / 'marketing' / 'images'

# reviewed 2026-10-30, second pass: blue sleeve, orange clips, 2 per Standard / 3 per Large.
# lead-slack-small (the key after) and before-slack-panel-small were set by hand from the key pass.
PICKS = {
    'lifestyle-golden': 1, 'lifestyle-doodle': 2, 'before-after': 1, 'before-after-small': 1,
    'lead-slack': 2, 'lifestyle-hand': 2, 'detail-clip': 2,
}
IN_USE_PICK = 2

# site file <- master
SITE_FROM = {
    'lifestyle-golden.jpg': 'lifestyle-golden.png',
    'lifestyle-doodle.jpg': 'lifestyle-doodle.png',
    'before-after-labelled.jpg': 'before-after-labelled.png',
    'before-after-small-labelled.jpg': 'before-after-small-labelled.png',
    'before-after-slack-labelled.jpg': 'before-after-slack-labelled.png',
    'before-after-slack-small-labelled.jpg': 'before-after-slack-small-labelled.png',
    'lead-slack.jpg': 'lead-slack.png',
    'lead-slack-small.jpg': 'lead-slack-small.png',
    'lifestyle-hand-labelled.jpg': 'lifestyle-hand-labelled.png',
    'detail-clip.jpg': 'detail-clip.png',
}


def main():
    for name, n in PICKS.items():
        dst = IMG / f'{name}.png'
        old = IMG / f'{name}-v4.png'
        if not old.exists():
            shutil.copy2(dst, old)
        shutil.copy2(HERE / 'ai' / f'{name}-{n}.png', dst)
        print('master', dst.name)

    for pair, before, after in (('before-after-slack', 'before-slack-panel', 'lead-slack'),
                                ('before-after-slack-small', 'before-slack-panel-small', 'lead-slack-small')):
        a, b = Image.open(IMG / f'{before}.png').convert('RGB'), Image.open(IMG / f'{after}.png').convert('RGB')
        out = Image.new('RGB', (a.width + 8 + b.width, a.height), 'white')
        out.paste(a, (0, 0))
        out.paste(b, (a.width + 8, 0))
        out.save(IMG / f'{pair}.png')
        print('pair', pair)

    subprocess.run([sys.executable, 'label_pairs.py'], cwd=NOTRIP / 'scripts', check=True)

    for site, master in SITE_FROM.items():
        size = Image.open(SITE / site).size
        im = Image.open(IMG / master).convert('RGB')
        if im.size != size:
            im = im.resize(size, Image.LANCZOS)
        im.save(SITE / site, quality=80, optimize=True, progressive=True)
        print('site', site, size)

    inuse = REPO / 'tools' / 'notrip-amazon' / 'in-use' / 'main-in-use-master.jpg'
    pick = HERE / 'ai' / f'main-in-use-master-{IN_USE_PICK}.png'
    if not pick.exists():
        return
    Image.open(HERE / 'ai' / f'main-in-use-master-{IN_USE_PICK}.png').convert('RGB').save(inuse, quality=92, subsampling=0)
    print('in-use master', inuse.name)


if __name__ == '__main__':
    main()
