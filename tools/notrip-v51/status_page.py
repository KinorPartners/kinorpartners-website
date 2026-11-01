"""Write _site/notrip-status.html: the current No-Trip v5.1 draft set on one page, local only.

    py -3 tools/notrip-v51/status_page.py      (then open http://localhost:8089/notrip-status.html)
"""
import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMG = '/assets/img/notrip-leash'
C = 'black white grey red orange yellow green teal blue purple pink'.split()
K = 'BLK WHT GRY RED ORG YEL GRN TEL BLU PUR PNK'.split()

SECTIONS = [
    ('1. Key before / after (colour)', 'Black leash, blue sleeve, two orange BUDDY clips. Personalised gallery PT01.',
     [f'{IMG}/before-after-slack-small-labelled.jpg'], 900),
    ('2. Amazon - PLAIN BLACK listings (KP-NT, FBA candidate)', 'Main images: Standard, Large, parent. Then the six-slide gallery (black sleeve on a grey leash) and the swatch.',
     [f'{IMG}/amazon/{f}' for f in ['KP-NT-S-BLK.MAIN.jpg', 'KP-NT-L-BLK.MAIN.jpg', 'KP-NT.MAIN.jpg']]
     + [f'{IMG}/amazon/KP-NT.PT0{i}.jpg' for i in range(1, 7)] + [f'{IMG}/amazon/KP-NT-S-BLK.SWCH.jpg'], 260),
    ('3. Amazon - PERSONALISED listings (KP-NTP, Amazon Custom, FBM)', 'Main images (shown in blue): Standard, Large, parent. Then the eight-slide colour gallery.',
     [f'{IMG}/amazon/{f}' for f in ['KP-NTP-S.MAIN.jpg', 'KP-NTP-L.MAIN.jpg', 'KP-NTP.MAIN.jpg']]
     + [f'{IMG}/amazon/KP-NTP.PT0{i}.jpg' for i in range(1, 9)], 260),
    ('4. Page colour heroes (CAD, clips match the sleeve)', 'Standard, then Large. Plain mode shows black; Personalised follows the sleeve colour.',
     [f'{IMG}/hero-standard-{c}.jpg' for c in C] + [f'{IMG}/hero-large-{c}.jpg' for c in C], 170),
    ('5. Page gallery - Plain mode', 'Black sleeve, grey leash.',
     [f'{IMG}/{f}' for f in ['plain-before-after-small.jpg', 'plain-before-after.jpg', 'plain-detail-clip.jpg']], 380),
    ('6. Page gallery - Personalised mode', 'The colour key scenes: slack-leash before/afters, AFTER shots and the clip close-up.',
     [f'{IMG}/{f}' for f in ['before-after-slack-small-labelled.jpg', 'before-after-slack-labelled.jpg',
                             'lead-slack-small.jpg', 'lead-slack.jpg', 'detail-clip.jpg']], 300),
    ('7. Photo-real product views (blue / orange)', 'AI re-shoots of the CAD views. Not yet used on the page.',
     [f'/notrip-views/real/{n}.jpg' for n in ['std-hero', 'lrg-hero', 'std-under', 'std-end', 'clip', 'std-side', 'lrg-side', 'std-top', 'lrg-top']], 300),
    ('8. Clip close-ups and pair (CAD)', 'Used in Amazon PT04 and the page gallery.',
     [f'{IMG}/{f}' for f in ['clip-name.jpg', 'clip-blank.jpg', 'clip-match.jpg', 'pair-joined.jpg', 'hero.jpg', 'colours.jpg']], 280),
    ('9. 360 spin (CAD, charcoal + orange clips, every 3rd frame)', 'Standard, then Large.',
     [f'{IMG}/spin/spin-{i:02d}.webp' for i in range(0, 36, 3)] + [f'{IMG}/spin-large/spin-{i:02d}.webp' for i in range(0, 36, 3)], 150),
    ('10. Live name-preview clip tops (page overlays the typed name)', '',
     [f'{IMG}/clip-top/{c}.webp' for c in C], 160),
]


def main():
    o = ['<!doctype html><meta charset=utf-8><title>No-Trip v5.1 - current drafts</title><style>'
         'body{font:14px system-ui;margin:20px;background:#f6f7f9;color:#111}h2{margin:30px 0 4px;font-size:18px}'
         'p.s{margin:0 0 10px;color:#555}.g{display:flex;flex-wrap:wrap;gap:10px}figure{margin:0;background:#fff;'
         'border:1px solid #ddd;border-radius:8px;padding:5px}img{display:block;max-width:100%}'
         'figcaption{font-size:10.5px;color:#777;padding-top:3px}</style>'
         '<h1>No-Trip Sleeve v5.1 - what we have (drafts)</h1>'
         '<p>Everything here is a draft. Nothing is committed or live. Final high-resolution, colour-true images '
         'get made once the set is approved.</p>']
    for title, sub, files, w in SECTIONS:
        if title:
            o.append(f'<h2>{html.escape(title)}</h2>')
        if sub:
            o.append(f'<p class=s>{html.escape(sub)}</p>')
        o.append('<div class=g>')
        for f in files:
            name = f.rsplit('/', 1)[1]
            o.append(f'<figure><a href="{f}" target=_blank><img src="{f}" width={w}></a><figcaption>{html.escape(name)}</figcaption></figure>')
        o.append('</div>')
    (REPO / '_site' / 'notrip-status.html').write_text(''.join(o), encoding='utf-8')


if __name__ == '__main__':
    main()
