"""The plain-black versions of the key scenes, ready for compose.py.

ai/plain-*.png are the key scenes re-shot with a black sleeve and black clips on a grey leash
(one Gemini 2.1 edit each). Here they are paired into BEFORE/AFTER images exactly like the
colour ones - two 1024 panels, an 8 px white gutter - and labelled with the NoTrip folder's
own label_pairs.label, so both families' pairs look the same.

    py -3 tools/notrip-v51/plain_set.py      -> build/plain/*.png
"""
import pathlib
import shutil
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
AI = HERE / 'ai'
OUT = HERE / 'build' / 'plain'
NOTRIP = pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners' / 'Clients & Products' / '8. NoTrip Sleeve'
IMG = NOTRIP / 'marketing' / 'images'

PAIRS = [
    ('before-after-slack-small-plain.png', 'plain-before-small', 'plain-lead-slack-small',
     'Let the leash go slack and the webbing pools round the front paws.',
     'The Standard single sleeve props the leash clear of the paws.'),
    ('before-after-slack-plain.png', 'plain-before', 'plain-lead-slack',
     'Let the leash go slack and the webbing pools round the front paws.',
     'The stiffened section rests on the grass and props the leash clear.'),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('plain-lead-slack-small', 'plain-lead-slack', 'plain-detail-clip'):
        shutil.copy2(AI / f'{name}-1.png', OUT / f'{name}.png')
    for pair, before, after, left, right in PAIRS:
        a = Image.open(AI / f'{before}-1.png').convert('RGB')
        b = Image.open(AI / f'{after}-1.png').convert('RGB').resize(a.size, Image.LANCZOS)
        o = Image.new('RGB', (a.width + 8 + b.width, a.height), 'white')
        o.paste(a, (0, 0))
        o.paste(b, (a.width + 8, 0))
        o.save(IMG / pair)                       # label_pairs reads from the NoTrip images folder
        code = f'import label_pairs as L; L.label({pair!r}, {left!r}, {right!r})'
        subprocess.run([sys.executable, '-c', code], cwd=NOTRIP / 'scripts', check=True, capture_output=True)
        labelled = pair.replace('.png', '-labelled.png')
        shutil.copy2(IMG / labelled, OUT / labelled)
        print(labelled)


if __name__ == '__main__':
    main()
