"""Write build/review.html: every v5.1 picture on one local page, for eyeballing a batch.

    py -3 tools/notrip-v51/review_page.py
"""
import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
R = HERE.parents[1] / 'src' / 'assets' / 'img' / 'notrip-leash'
C = 'black white grey red orange yellow green teal blue purple pink'.split()
K = 'BLK WHT GRY RED ORG YEL GRN TEL BLU PUR PNK'.split()
SECTIONS = [
    ('Dog scenes (AI, v5.1 sleeve swapped in)', [R / f for f in [
        'lifestyle-golden.jpg', 'lifestyle-doodle.jpg', 'before-after-labelled.jpg',
        'before-after-small-labelled.jpg', 'before-after-slack-labelled.jpg',
        'before-after-slack-small-labelled.jpg', 'lead-slack.jpg', 'lead-slack-small.jpg',
        'lifestyle-hand-labelled.jpg', 'detail-clip.jpg']], 300),
    ('Name clip (CAD)', [R / f for f in ['clip-name.jpg', 'clip-blank.jpg', 'clip-match.jpg',
                                         'hero.jpg', 'pair-joined.jpg', 'colours.jpg']], 300),
    ('Live-preview clip tops (the page lays the typed name over these)', [R / 'clip-top' / f'{c}.webp' for c in C], 200),
    ('Amazon: parent MAIN + gallery PT01-PT08', [R / 'amazon' / f'KP-NT.{s}.jpg' for s in ['MAIN'] + [f'PT0{i}' for i in range(1, 9)]], 260),
    ('Amazon MAIN - Standard (in-use scene, recoloured)', [R / 'amazon' / f'KP-NT-S-{k}.MAIN.jpg' for k in K], 200),
    ('Amazon MAIN - Large', [R / 'amazon' / f'KP-NT-L-{k}.MAIN.jpg' for k in K], 200),
    ('Amazon colour-picker swatches', [R / 'amazon' / f'KP-NT-S-{k}.SWCH.jpg' for k in K], 120),
    ('PDP heroes - Standard', [R / f'hero-standard-{c}.jpg' for c in C], 200),
    ('PDP heroes - Large', [R / f'hero-large-{c}.jpg' for c in C], 200),
    ('360 spin - Standard (every 3rd frame)', [R / 'spin' / f'spin-{i:02d}.webp' for i in range(0, 36, 3)], 160),
    ('360 spin - Large (every 3rd frame)', [R / 'spin-large' / f'spin-{i:02d}.webp' for i in range(0, 36, 3)], 160),
]


def main():
    o = ['<!doctype html><meta charset=utf-8><title>No-Trip v5.1 images</title><style>'
         'body{font:14px system-ui;margin:20px;background:#f6f7f9;color:#111}h2{margin:28px 0 8px;font-size:17px}'
         '.g{display:flex;flex-wrap:wrap;gap:10px}figure{margin:0;background:#fff;border:1px solid #ddd;'
         'border-radius:8px;padding:6px}figcaption{font-size:11px;color:#666}a img{display:block}</style>'
         '<h1>No-Trip Sleeve v5.1 - image review</h1><p>Click any image for full size.</p>']
    for title, files, w in SECTIONS:
        o.append(f'<h2>{html.escape(title)}</h2><div class=g>')
        for f in files:
            if f.exists():
                u = f.as_uri()
                o.append(f'<figure><a href="{u}" target=_blank><img src="{u}" width={w}></a>'
                         f'<figcaption>{html.escape(f.name)}</figcaption></figure>')
        o.append('</div>')
    out = HERE / 'build' / 'review.html'
    out.write_text(''.join(o), encoding='utf-8')
    print(out.as_uri())


if __name__ == '__main__':
    main()
