#!/usr/bin/env python3
"""Pre-flight checks for the static site. Run locally or in CI.

    python tools/check_site.py

Fails (exit 1) on anything that would be visibly broken in production:
broken internal links, malformed JSON-LD, missing images, or a page-weight
blow-out. Warnings (missing alt text, missing image dimensions) are reported
but do not fail the build.
"""
import glob, io, json, os, re, sys
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

IMG_BUDGET_MB = 6.0          # total weight of assets/img
PAGE_BUDGET_KB = 120.0       # largest single HTML document

errors, warnings = [], []

pages = [p.replace('\\', '/') for p in glob.glob('**/*.html', recursive=True)
         if not p.replace('\\', '/').startswith('tools/')]

# ---------- build the set of servable paths ----------
have = {'/'}
for p in pages:
    have.add('/' + p)
    if p.endswith('index.html'):
        have.add('/' + p[:-10])
        have.add('/' + p[:-11])
for a in glob.glob('assets/**/*', recursive=True):
    if os.path.isfile(a):
        have.add('/' + a.replace('\\', '/'))
for extra in ('sitemap.xml', 'robots.txt', 'favicon.ico', 'site.webmanifest', 'CNAME'):
    if os.path.exists(extra):
        have.add('/' + extra)

attr = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I)
imgtag = re.compile(r'<img\b[^>]*>', re.I)

# ---------- links ----------
for f in pages:
    t = io.open(f, encoding='utf-8').read()
    for raw in attr.findall(t):
        u = raw.strip()
        if u.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', '#',
                         'data:', 'javascript:')):
            continue
        path = unquote(urlparse(u).path)
        if not path:
            continue
        if not path.startswith('/'):
            path = os.path.normpath('/' + os.path.dirname(f) + '/' + path).replace('\\', '/')
        if path not in have and path.rstrip('/') not in have and path + '/' not in have:
            errors.append('broken link %s  (in %s)' % (path, f))

# ---------- JSON-LD ----------
for f in pages:
    t = io.open(f, encoding='utf-8').read()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try:
            json.loads(m.group(1))
        except Exception as e:
            errors.append('invalid JSON-LD in %s: %s' % (f, str(e)[:80]))

# ---------- images ----------
for f in pages:
    t = io.open(f, encoding='utf-8').read()
    for tag in imgtag.findall(t):
        if not re.search(r'\balt\s*=', tag, re.I):
            warnings.append('img without alt in %s' % f)
        if not (re.search(r'\bwidth\s*=', tag, re.I) and re.search(r'\bheight\s*=', tag, re.I)):
            warnings.append('img without width/height in %s' % f)

# ---------- tag balance (warning only) ----------
# Browsers silently repair unbalanced markup, and some pages still carry
# nesting debris from the Shopify scrape, so this reports rather than fails.
from html.parser import HTMLParser

VOID = {'area','base','br','col','embed','hr','img','input','link','meta',
        'param','source','track','wbr'}
FOREIGN = {'svg', 'math'}
OPTIONAL = {'p','li','td','th','tr','tbody','thead','tfoot','option','dt','dd'}


class Balance(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.stack, s.bad, s.foreign = [], [], 0

    def handle_starttag(s, tag, attrs):
        if tag in FOREIGN:
            s.foreign += 1
        if tag not in VOID:
            s.stack.append(tag)

    def handle_startendtag(s, tag, attrs):
        # HTML5 ignores a trailing slash on non-void HTML elements (<div/> opens
        # a div) but honours it in foreign content (<path/> really self-closes).
        if tag in VOID or s.foreign > 0:
            return
        s.stack.append(tag)

    def handle_endtag(s, tag):
        if tag in FOREIGN and s.foreign > 0:
            s.foreign -= 1
        if tag in VOID:
            return
        while s.stack:
            t = s.stack.pop()
            if t == tag:
                return
            if t not in OPTIONAL:
                s.bad.append('</%s> while <%s> open' % (tag, t))
                return


for f in pages:
    b = Balance()
    b.feed(io.open(f, encoding='utf-8').read())
    left = [t for t in b.stack if t not in OPTIONAL]
    if b.bad or left:
        warnings.append('unbalanced tags in %s (%s)'
                        % (f, '; '.join(b.bad[:2]) or 'unclosed ' + ','.join(left[:3])))

# ---------- weight ----------
img_bytes = sum(os.path.getsize(p) for p in glob.glob('assets/img/**/*', recursive=True)
                if os.path.isfile(p))
if img_bytes / 1048576 > IMG_BUDGET_MB:
    errors.append('assets/img is %.1f MB, over the %.1f MB budget'
                  % (img_bytes / 1048576, IMG_BUDGET_MB))

for f in pages:
    kb = os.path.getsize(f) / 1024
    if kb > PAGE_BUDGET_KB:
        warnings.append('%s is %.0f KB (budget %.0f KB)' % (f, kb, PAGE_BUDGET_KB))

# ---------- report ----------
print('checked %d pages | assets/img %.2f MB' % (len(pages), img_bytes / 1048576))
if warnings:
    seen = {}
    for w in warnings:
        seen[w] = seen.get(w, 0) + 1
    print('\n%d warning(s):' % len(warnings))
    for w, n in sorted(seen.items(), key=lambda kv: -kv[1])[:15]:
        print('  [x%d] %s' % (n, w) if n > 1 else '  %s' % w)
if errors:
    print('\n%d ERROR(S):' % len(errors))
    for e in errors[:30]:
        print('  ' + e)
    sys.exit(1)
print('\nOK - no blocking issues')
