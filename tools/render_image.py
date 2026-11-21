#!/usr/bin/env python3
"""Render an article's blog image as a 1200 x 800 PNG, from the codi studio blog image system.

Usage:  python3 tools/render_image.py <slug> [--out path.png]

Reads the image_* fields from content/resources/<slug>.md (image_kind, image_background,
image_big, image_line1, image_line2, image_icon, topic) and writes
site/images/resources/<slug>.png by default. Needs Google Chrome on the Mac.
"""
import os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_resources as br

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    out = os.path.join(br.SITE, 'images', 'resources', f'{slug}.png')
    if '--out' in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    a = br.read_article(os.path.join(br.CONTENT, f'{slug}.md'))
    a['image_file'] = ''  # always draw from the rules
    css = re.search(r'/\* Blog image system.*?(?=\.blog-card\{)', open(os.path.join(br.SITE, 'resources.html'), encoding='utf-8').read(), re.S)
    css = css.group(0) if css else ''
    page = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@700;800&display=swap" rel="stylesheet">
<style>html,body{{margin:0;width:1200px;height:800px;overflow:hidden;font-family:'Poppins',sans-serif;background:#12032E}}
{css}
.blog-image{{border-radius:0!important;width:1200px;border:0!important}}</style></head>
<body>{br.blog_image(a)}</body></html>'''
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(page)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1200,800',
                    '--virtual-time-budget=4000', f'--screenshot={out}', 'file://' + f.name],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(f.name)
    print(out)


if __name__ == '__main__':
    main()
