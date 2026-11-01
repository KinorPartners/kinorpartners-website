"""Turn the one-colourway CAD views into studio product photographs, geometry untouched.

Each CAD view (views.py) is the exact part; the image model only re-photographs it: real
moulded-plastic surface, soft studio light, a contact shadow. Framed as a restoration, not
a generation, or it redesigns the part (see the Gemini upscale notes in memory).

    py -3 tools/notrip-v51/photoreal.py [names...] [--n 2]   -> build/real/<name>-<n>.png
"""
import base64
import concurrent.futures as cf
import io
import json
import pathlib
import sys
import urllib.request

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ai_edits import key, part, ratio, MODEL  # noqa: E402

VIEWS = HERE / 'build' / 'views'
OUT = HERE / 'build' / 'real'
NAMES = ['std-hero', 'lrg-hero', 'std-side', 'lrg-side', 'std-top', 'lrg-top', 'std-under', 'std-end', 'clip']

PROMPT = (
    "This is a CAD render of a real product. Re-photograph it as a high-end studio product "
    "PHOTOGRAPH of the physical injection-moulded part, as if shot with a 100mm macro lens on a "
    "seamless light-grey sweep. Reproduce the object EXACTLY: same outline, same proportions, same "
    "camera angle and framing, same position in the frame, every edge, window, slot, tab and gap "
    "where it is, and the same number of clips in the same places. Do not add, remove, move "
    "or redesign anything, and add no other object, logo or leash. "
    "What to change: make the materials real - the blue sleeve is matte satin moulded plastic with "
    "a very faint fine texture and slightly softened edges, the orange clips the same material; "
    "COLOURS. Replace the flat CG shading with "
    "soft diffused studio light from the upper left, gentle falloff and realistic soft reflections "
    "on curved surfaces, subtle ambient occlusion in corners and inside the channel, and a soft "
    "natural contact shadow under the part. The letters read by real shadow inside the deboss. "
    "Photographic, sharp focus across the part, no vignette, no watermark.")


# Lettering is where the models go wrong: told about the underside wordmark, they print it on
# every visible face. So each view says exactly what text it may show, and nothing else.
PLAIN = ("LETTERING: the ONLY text in the picture is the name BUDDY sunk into the flat top of each "
         "clip, exactly where the render shows it (where the render shows it faintly, make it "
         "a crisp real deboss in the same place). The inside of the blue channel, the channel floor, "
         "the sleeve walls and the clip side arms are completely PLAIN - no words, no logo, no icon. ")
NOTES = {
    'std-under': ("LETTERING: this view shows the UNDERSIDE. Its only text is what the render shows sunk "
                  "into the blue underside: the CADENZA wordmark with TM, a small dog-on-a-leash icon, and "
                  "NO-TRIP SLEEVE - same letters, size and place, spelled exactly. The orange clip arms "
                  "seen here carry NO text at all. "),
    'clip': ("This is ONE orange clip on its own (no blue sleeve in the picture): the whole object stays "
             "ORANGE. " + PLAIN.replace('each orange clip', 'the clip')),
}


HEROES = HERE / 'build' / 'heroes-cad'


def colours_line(name):
    """The colour sentence: blue/orange for the views, each variant's own pair for the heroes."""
    if not name.startswith('hero-'):
        return 'colours stay the same blue (#2E7FD2) and orange (#E2652B). '
    import render_all as A
    cname = name.split('-')[-1].capitalize()
    body = dict(A.COLOURS)[cname]
    # colour-picker heroes: clips match the sleeve
    return (f'colours stay EXACTLY as rendered: the sleeve AND every clip are the same {cname.lower()} '
            f'({body}); the clips are separate parts, so keep the thin seam where each clip meets the sleeve. ')


def real(name, n):
    src = Image.open((HEROES if name.startswith('hero-') else VIEWS) / f'{name}.png').convert('RGB')
    text = PROMPT.replace('COLOURS. ', colours_line(name)).replace('the orange clips', 'the clips').replace('the blue sleeve', 'the sleeve')
    plain = PLAIN.replace('the blue channel', 'the channel')
    body = {'contents': [{'parts': [{'text': text + NOTES.get(name, plain)}, part(src, 2048)]}],
            'generationConfig': {'responseModalities': ['IMAGE'],
                                 'imageConfig': {'aspectRatio': ratio(*src.size), 'imageSize': '2K'}}}
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key()}'
    req = urllib.request.Request(url, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.load(r)
    for p in res['candidates'][0]['content']['parts']:
        d = p.get('inline_data') or p.get('inlineData')
        if d:
            im = Image.open(io.BytesIO(base64.b64decode(d['data']))).convert('RGB')
            # back to the render's exact frame; the aspect presets are close, not exact
            w = max(src.width, 1600)
            im = im.resize((w, round(w * src.height / src.width)), Image.LANCZOS)
            f = OUT / f'{name}-{n}.png'
            im.save(f)
            return f.name
    raise RuntimeError(f'{name}: no image: {json.dumps(res)[:300]}')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--') and not a.isdigit()]
    if args == ['heroes']:
        args = sorted(f.stem for f in HEROES.glob('hero-*.png'))
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 2
    OUT.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(9) as ex:
        futs = {ex.submit(real, nm, i): (nm, i) for nm in (args or NAMES) for i in range(1, n + 1)}
        for f in cf.as_completed(futs):
            try:
                print('ok', f.result(), flush=True)
            except Exception as e:
                print('FAIL', futs[f], e, flush=True)


if __name__ == '__main__':
    main()
