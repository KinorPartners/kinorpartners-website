"""Flat colour squares for the Amazon colour picker (owner, 2026-11-02).

Amazon draws each variation's swatch image as its tile in the Color picker. The renders we
sent first made big product tiles, so the swatches are plain colour now. Black - Personalized
carries "ABC" so it never reads as plain Black. White gets a thin border for a white page.

    py -3 tools/notrip-v51/swatch_flat.py   -> src/assets/img/notrip-leash/amazon/KP-NT-*.SWCH.jpg

Bump the swatch ?v= in PatchDesign build-notrip-leash.mjs after changing these, or Amazon
keeps its cached copy.
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'src' / 'assets' / 'img' / 'notrip-leash' / 'amazon'
S = 1000
COLOURS = {
    'BLK': '#2B2E33', 'WHT': '#ECEBE6', 'GRY': '#6E747C', 'RED': '#C13B2E', 'ORG': '#E2652B',
    'YEL': '#EDC220', 'GRN': '#5CBE38', 'TEL': '#159C93', 'BLU': '#2E7FD2', 'PUR': '#9A6FCE',
    'PNK': '#E77CA6', 'BKP': '#2B2E33',
}


def swatch(code):
    im = Image.new('RGB', (S, S), COLOURS[code])
    d = ImageDraw.Draw(im)
    if code == 'WHT':
        d.rectangle((0, 0, S - 1, S - 1), outline='#BDBDBD', width=12)
    if code == 'BKP':
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 300)
        d.text((S / 2, S / 2), 'ABC', font=f, fill='white', anchor='mm')
    return im


def main():
    for size in 'SL':
        for code in COLOURS:
            swatch(code).save(OUT / f'KP-NT-{size}-{code}.SWCH.jpg', quality=95)
    print('wrote', 2 * len(COLOURS), 'swatches to', OUT)


if __name__ == '__main__':
    main()
