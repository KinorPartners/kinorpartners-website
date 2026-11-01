"""Swap the v4 sleeve for the v5.1 one in the AI lifestyle shots, keeping each scene.

The scenes (dog, leash, ground, hands, light) were approved as they are; only the
product in them is out of date. So each call is an EDIT of the existing picture, with
the v5.1 CAD renders (render_all.py) as references for what the part now looks like,
rather than a fresh generation that would re-roll the dog too.

Sources are the unlabelled masters in the NoTrip OneDrive marketing/images folder;
outputs land in tools/notrip-v51/ai/<name>-<n>.png for review, then get copied
over the masters and relabelled with that folder's label_pairs.py.

    py -3 tools/notrip-v51/ai_edits.py [names...] [--n 2]
Key: C:\\GitHub\\Shirt-Tucker\\gemini_api_key.txt (or GOOGLE_GEMINI_API_KEY).
Model: gemini-3.1-flash-image (Nano Banana 2.1, the house default).
"""
import base64
import concurrent.futures as cf
import io
import json
import os
import pathlib
import sys
import urllib.request

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
IMG = REPO / 'src' / 'assets' / 'img' / 'notrip-leash'
NOTRIP = pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents' / '1. Kinor Partners' / 'Clients & Products' / '8. NoTrip Sleeve'
SRC = NOTRIP / 'marketing' / 'images'
OUT = HERE / 'ai'
MODEL = os.environ.get('EVAL_MODEL', 'gemini-3.1-flash-image')

PART = (
    "THE PRODUCT (v5.1, shown in the reference renders - copy it exactly, do not redesign it): "
    "a slim rigid sleeve that the leash webbing lies inside. Its cross-section is a rounded U, "
    "about 1 in wide and 3/4 in deep, OPEN along the whole top so the leash is visible lying in "
    "the channel - it is NOT a closed tube and has no narrow slot. Each side wall has just two "
    "small rounded-oblong windows near EACH end of a piece (none along the middle). A short "
    "snap-on CLIP, about 1.6 in long, is a squared-off cap "
    "that WRAPS the sleeve: it bridges over the open top and its side arms come down over both "
    "side walls, so it is slightly wider than the sleeve, like a ring around it - it is NOT a "
    "flat plate or a badge sitting on top. Each clip's side arms cover BOTH windows at its end, on "
    "BOTH sides, so where a clip sits no window shows; a Standard piece with its two clips on shows "
    "no open windows at all. The clip's flat top has the dog's name BUDDY debossed "
    "in plain capital letters (sunk in, not printed, not raised), reading along the leash. "
    "Matte injection-moulded plastic, no shine, no stitching, no foam. Nothing else anywhere "
    "carries the name or any lettering - the metal snap hook and the collar stay plain. ")
STD = ("Here the sleeve is ONE 6 in piece with TWO clips, one at EACH end of the piece "
       "(each clip covers about the last quarter of the piece at its end). ")
LRG = ("Here the sleeve is TWO 6 in pieces butted end to end (12 in in all) with THREE clips: "
       "one at each far end and one bridging the joint in the middle. ")
KEEP = (
    "EDIT the first image. Change ONLY the black sleeve on the leash, replacing it with the "
    "product described. Keep everything else exactly as it is: the dog (breed, pose, fur, face, "
    "collar), the leash webbing and its colour, the clip hardware, the person, the ground, the "
    "background, the lighting, the camera angle and the framing. Same position and same length "
    "along the leash as the sleeve being replaced. No text, no logos, no watermark anywhere "
    "except the name moulded on the clip. ")

# name: (source file, size, colour words, extra instruction, refs)
COL = 'sleeve BRIGHT BLUE (#2E7FD2), every clip ORANGE (#E2652B)'
RS = ['real/std-hero.pick.png', 'real/std-side.pick.png', 'real/clip.pick.png']
RL = ['real/lrg-hero.pick.png', 'real/lrg-side.pick.png', 'real/clip.pick.png']
TWO = 'This is a two-panel image. The LEFT panel shows no sleeve and must not change at all; edit only the sleeve in the RIGHT panel. '
# Second pass (2026-10-30): two clips per sleeve, contrasting clip colour. Sources are the
# first-pass v5.1 masters, whose composition was already approved.
JOBS = {
    'lifestyle-golden': ('lifestyle-golden.png', LRG, COL, '', RL),
    'lifestyle-doodle': ('lifestyle-doodle.png', STD, COL, '', RS),
    'before-after': ('before-after.png', LRG, COL, TWO, RL),
    'before-after-small': ('before-after-small.png', STD, COL, TWO, RS),
    'lead-slack': ('lead-slack.png', LRG, COL, '', RL),
    'lifestyle-hand': ('lifestyle-hand.png', STD, COL,
                       'The name BUDDY on the clips should be legible in this shot. ', RS),
    'detail-clip': ('detail-clip.png', STD, COL,
                    'This is a close-up of one end: make that orange clip the hero of the shot, its debossed '
                    'name BUDDY crisp and readable, the leash webbing visible lying in the open blue channel '
                    'beside it. ', RS),
    # the key before/after (owner, 2026-10-30): sleeve, clips and leash each a different colour
    # so every component reads; same black leash in both panels
    'key-after': ('lead-slack-small.png', STD,
                  'sleeve BRIGHT BLUE (#2E7FD2), both clips ORANGE (#E2652B)',
                  'EXCEPTION: recolour the leash webbing to plain matte BLACK along its whole length. '
                  'The blue sleeve, the two orange clips and the black leash must each be clearly '
                  'distinguishable. COMPOSITION MUST NOT CHANGE: no hand and no person in frame; the sleeve '
                  'runs from the collar snap at the chest of the dog DOWN to the grass, its lower end resting on the '
                  'grass beside the front paws, and from that point the leash rises steeply to the top-right '
                  'corner and out of frame. No leash lies on the ground. ',
                  ['views/std-hero.png', 'views/std-side.png', 'views/clip.png']),
    'key-before': ('before-slack-panel-small.png', '', '',
                   'This panel has NO sleeve and must not get one. The ONLY change: recolour the leash '
                   'webbing to plain matte BLACK along its whole length, keeping every fold and loop exactly. ',
                   []),
    # Amazon Standard MAIN, v2 (owner, 2026-10-30): the key AFTER doodle on pure white, dog and
    # leash grey, sleeve and both clips one colour (purple master; recolour_main.py does the rest)
    'main-doodle-master': ('lead-slack-small.png', STD, 'sleeve AND both clips the same saturated PURPLE (#9A6FCE)',
                           'EXCEPTIONS, this is a catalogue main image: (1) replace the whole background - grass, '
                           'trees, sky - with PURE WHITE (#FFFFFF), the dog standing on white with only a faint soft '
                           'shadow under its paws and under the sleeve tip; (2) make the dog, its collar, the metal '
                           'snap and the whole leash fully GREYSCALE (neutral greys, no colour cast); (3) the sleeve '
                           'and its two clips are the ONLY coloured things, all one purple. Keep the dog, its pose, '
                           'the head down sniffing, the sleeve running from the collar snap down to the ground by '
                           'the front paws, the leash rising to the top-right corner and out of frame, and the framing '
                           'exactly as they are. No grass anywhere. ', RS),
    # BEFORE half of a before/after MAIN: same doodle, leash pooled, on white, all grey, no sleeve
    'main-before-master': ('before-slack-panel-small.png', '', '',
                           'This is a catalogue image. (1) Replace the whole background - grass, trees, sky - with '
                           'PURE WHITE (#FFFFFF): the dog stands on white with only a faint soft shadow under its paws '
                           'and under the leash loops; (2) make the dog, collar, metal snap and the whole leash fully '
                           'GREYSCALE, the leash a mid neutral grey like webbing photographed in black and white; '
                           '(3) keep everything else exactly: the dog, its pose with the head down sniffing, the leash '
                           'running from the collar down to the ground and lying pooled in loops round the front '
                           'paws, then rising to the top-right corner and out of frame, and the framing. There is NO '
                           'sleeve and nothing coloured anywhere. No grass. ', []),
    # Large before/after MAIN: the golden retriever pair, same treatment as the doodle
    'main-before-large': ('before-slack-panel.png', '', '',
                          'This is a catalogue image. (1) Replace the whole background - grass, trees, sky - with '
                          'PURE WHITE (#FFFFFF): the dog stands on white with only a faint soft shadow under its paws '
                          'and under the leash loops; (2) make the dog, collar, metal snap and the whole leash fully '
                          'GREYSCALE, the leash a mid neutral grey; (3) keep everything else exactly: the dog, its pose, '
                          'the leash pooled round the front paws and rising out of frame, and the framing. There is NO '
                          'sleeve and nothing coloured anywhere. No grass. ', []),
    'main-after-large': ('lead-slack.png', LRG, 'the sleeves AND all three clips the same saturated PURPLE (#9A6FCE)',
                         'EXCEPTIONS, this is a catalogue main image: (1) replace the whole background - grass, '
                         'trees, sky - with PURE WHITE (#FFFFFF), the dog standing on white with only a faint soft '
                         'shadow under its paws and under the sleeve tip; (2) make the dog, its collar, the metal '
                         'snap and the whole leash fully GREYSCALE (a mid neutral grey leash); (3) the two sleeves and '
                         'three clips are the ONLY coloured things, all one purple. Keep the dog, its pose, the sleeve '
                         'running from the collar snap down to the ground, the leash rising out of frame, and the '
                         'framing exactly. No grass. ', RL),
    # Plain-black listing (owner, 2026-10-31): the key scenes with a black sleeve and black clips,
    # and the leash turned mid grey so the black part stays visible. Outputs land as <name>-1.png
    # and are installed under KINOR-PLAIN names by plain_set.py, not over the colour masters.
    'plain-lead-slack-small': ('lead-slack-small.png', STD, 'sleeve AND both clips matte BLACK (#2B2E33)',
                               'EXCEPTION: recolour the leash webbing to a plain mid neutral GREY along its whole '
                               'length so the black sleeve stands out against it. Composition unchanged: no hand, the '
                               'sleeve from the collar snap down to the grass, the leash rising out of frame. ', RS),
    'plain-lead-slack': ('lead-slack.png', LRG, 'both sleeves AND all three clips matte BLACK (#2B2E33)',
                         'EXCEPTION: recolour the leash webbing to a plain mid neutral GREY along its whole length so '
                         'the black sleeve stands out against it. Composition unchanged. ', RL),
    'plain-before-small': ('before-slack-panel-small.png', '', '',
                           'This panel has NO sleeve and must not get one. The ONLY change: recolour the leash webbing '
                           'to a plain mid neutral GREY along its whole length, keeping every fold and loop exactly. ', []),
    'plain-before': ('before-slack-panel.png', '', '',
                     'This panel has NO sleeve and must not get one. The ONLY change: recolour the leash webbing to a '
                     'plain mid neutral GREY along its whole length, keeping every fold and loop exactly. ', []),
    'plain-detail-clip': ('detail-clip.png', STD, 'sleeve AND both clips matte BLACK (#2B2E33)',
                          'This is a close-up of one end: the black clip is the hero, its debossed name BUDDY crisp and '
                          'readable by its shadow. EXCEPTION: recolour the leash webbing in the channel to a plain mid '
                          'neutral GREY so the black parts stand out. ', RS),
    'main-in-use-master': (str(REPO / 'tools' / 'notrip-amazon' / 'in-use' / 'main-in-use-master.jpg'), STD,
                           'sleeve saturated PURPLE (#9A6FCE), both clips ORANGE (#E2652B)',
                           'The sleeve hangs straight down from the collar snap exactly where it is now, same '
                           'length; give it TWO orange clips, one at its top end just under the snap and one at '
                           'its bottom end. There is ONE sleeve. Everything except the sleeve and its clips is '
                           'deliberately GREYSCALE and must stay greyscale (dog, collar, snap, leash, hand). Pure '
                           'white background stays pure white. ', RS),
}
REFS = ['hero.jpg', 'clip-name.jpg', 'hero-large-black.jpg']


def key():
    k = os.environ.get('GOOGLE_GEMINI_API_KEY')
    if not k:
        k = pathlib.Path(r'C:\GitHub\Shirt-Tucker\gemini_api_key.txt').read_text().strip()
    return k


def part(im, maxpx=1536):
    im = im.convert('RGB')
    im.thumbnail((maxpx, maxpx))
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=92)
    return {'inline_data': {'mime_type': 'image/jpeg', 'data': base64.b64encode(b.getvalue()).decode()}}


def ratio(w, h):
    opts = {'1:1': 1, '4:3': 4 / 3, '3:4': 3 / 4, '3:2': 1.5, '2:3': 2 / 3, '16:9': 16 / 9, '4:5': 0.8, '5:4': 1.25, '21:9': 21 / 9}
    return min(opts, key=lambda k: abs(opts[k] - w / h))


def edit(name, n):
    src, size, colour, extra, *refs = JOBS[name]
    refs = refs[0] if refs else REFS
    srcp = pathlib.Path(src) if os.path.isabs(src) else SRC / src
    im = Image.open(srcp)
    if size:
        prompt = (KEEP + PART + size + f"Colour of the sleeve and clips: {colour}. " + extra +
                  "Reference images after the first one are CAD renders of the product (match their shape "
                  "and the number and position of the clips).")
    else:
        prompt = "EDIT the first image. Keep everything exactly as it is. " + extra
    ref_im = [Image.open(HERE / 'build' / r) if r.startswith(('views/', 'real/')) else Image.open(IMG / r) for r in refs]
    body = {'contents': [{'parts': [{'text': prompt}, part(im)] + [part(r, 1024) for r in ref_im]}],
            'generationConfig': {'responseModalities': ['IMAGE'],
                                 'imageConfig': {'aspectRatio': ratio(*im.size), 'imageSize': os.environ.get('IMAGE_SIZE', '1K')}}}
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key()}'
    req = urllib.request.Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.load(r)
    for p in res['candidates'][0]['content']['parts']:
        d = p.get('inline_data') or p.get('inlineData')
        if d:
            out = Image.open(io.BytesIO(base64.b64decode(d['data']))).convert('RGB')
            out = out.resize(im.size, Image.LANCZOS)   # back to the master's exact size
            f = OUT / f'{name}-{n}.png'
            out.save(f)
            return str(f)
    raise RuntimeError(f'{name}: no image in response: {json.dumps(res)[:400]}')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 2
    args = [a for a in args if not a.isdigit()]
    OUT.mkdir(exist_ok=True)
    names = args or list(JOBS)
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(edit, nm, i): (nm, i) for nm in names for i in range(1, n + 1)}
        for f in cf.as_completed(futs):
            try:
                print('ok', f.result(), flush=True)
            except Exception as e:  # keep the batch going; report what failed
                print('FAIL', futs[f], e, flush=True)


if __name__ == '__main__':
    main()
