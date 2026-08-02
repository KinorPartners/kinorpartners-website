#!/usr/bin/env python3
"""Keep the shared header/footer identical across every page.

The site is plain HTML with no build step, so the nav and footer used to be
copy-pasted into all 50 content pages - changing a link meant a 50-file edit.
This script makes tools/partials/{header,footer}.html the single source of
truth and rewrites every page from them.

The only per-page difference is which nav link carries class="active"; that is
read off the page before rewriting and re-applied, so behaviour never changes.

    python tools/sync_partials.py           # rewrite pages in place
    python tools/sync_partials.py --check   # exit 1 if any page has drifted (CI)
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

HEADER_RE = re.compile(r'<header class="site-header">.*?</header>', re.S)
FOOTER_RE = re.compile(r'<footer class="site-footer">.*?</footer>', re.S)
REFRESH_RE = re.compile(r'http-equiv=["\']refresh', re.I)
ACTIVE_RE = re.compile(r'<a href="([^"]+)"[^>]*\bclass="[^"]*\bactive\b[^"]*"')

header_tpl = io.open('tools/partials/header.html', encoding='utf-8').read()
footer_tpl = io.open('tools/partials/footer.html', encoding='utf-8').read()


def apply_active(header, href):
    """Mark the nav link pointing at `href` as active, matching the old markup."""
    if not href:
        return header
    pat = re.compile(r'(<a href="%s")(?![^>]*\bclass=)' % re.escape(href))
    return pat.sub(r'\1 class="active"', header, count=1)


def main():
    check = '--check' in sys.argv
    drifted, rewritten, skipped = [], 0, 0

    for f in sorted(glob.glob('**/*.html', recursive=True)):
        if f.startswith('tools' + os.sep) or f.startswith('tools/'):
            continue
        t = io.open(f, encoding='utf-8').read()
        if REFRESH_RE.search(t):          # client-side redirect stub, no chrome
            skipped += 1
            continue
        if not HEADER_RE.search(t) or not FOOTER_RE.search(t):
            skipped += 1
            continue

        cur_header = HEADER_RE.search(t).group(0)
        m = ACTIVE_RE.search(cur_header)
        new_header = apply_active(header_tpl, m.group(1) if m else None)

        out = HEADER_RE.sub(lambda _: new_header, t, count=1)
        out = FOOTER_RE.sub(lambda _: footer_tpl, out, count=1)

        if out != t:
            drifted.append(f)
            if not check:
                io.open(f, 'w', encoding='utf-8', newline='').write(out)
                rewritten += 1

    if check:
        if drifted:
            print('Header/footer drift in %d file(s):' % len(drifted))
            for d in drifted[:20]:
                print('  ' + d)
            print('\nRun: python tools/sync_partials.py')
            return 1
        print('OK - header/footer in sync across all pages (%d stubs skipped)' % skipped)
        return 0

    print('rewrote %d page(s); %d already in sync; %d stubs skipped'
          % (rewritten, len(glob.glob("**/*.html", recursive=True)) - rewritten - skipped, skipped))
    return 0


if __name__ == '__main__':
    sys.exit(main())
