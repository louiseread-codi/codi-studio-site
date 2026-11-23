#!/usr/bin/env python3
"""Draw an article's blog image (1200 x 800 PNG) from the codi studio blog image system.

No browser needed: pure Python (Pillow) with the Poppins fonts in tools/fonts.

Usage:  python3 tools/render_image.py <slug> [--out path.png]

Reads from content/resources/<slug>.md:
  topic             Strategy | Implementation | AI how-to | Future of work
  image_kind        hook (word image) | icon
  image_background  solid | indigo
  image_line1, image_line2   for hook (line 2 in the accent colour)
  image_icon        bars | target | checklist | layers | trend | bulb
Writes site/images/resources/<slug>.png (also the LinkedIn / social preview image).

Brand rules (Louise, 22 Nov 2026): word or icon only, never a number, never the
article title; alternate word / icon by publish order; wordmark top left; two dots
cropped bottom right with nothing over them.
"""
import os, sys
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('Pillow missing: run  pip install pillow')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_resources as br

W, H, S = 1200, 800, 2          # draw at 2x, then downscale for smooth edges
FONT_BOLD = os.path.join(HERE, 'fonts', 'Poppins-Bold.ttf')
FONT_XBOLD = os.path.join(HERE, 'fonts', 'Poppins-ExtraBold.ttf')
INDIGO, PURPLE, MINT, WHITE = '#12032E', '#8B4BFF', '#35FF9A', '#FFFFFF'


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette(topic, background):
    colour = br.TOPICS[topic][0]
    impl = topic == 'Implementation'
    if background != 'indigo':
        return dict(bg=colour, ink=WHITE if impl else INDIGO, accent=MINT if impl else PURPLE,
                    dot1=INDIGO if impl else PURPLE, dot2=MINT if impl else INDIGO,
                    blend='screen' if impl else 'over90')
    accent = '#B48CFF' if impl else colour
    return dict(bg=INDIGO, ink=WHITE, accent=accent, dot1=PURPLE, dot2=accent, blend='screen')


def tracked_text(d, xy, text, font, fill, tracking):
    """Draw text with letter-spacing (tracking in px, negative = tighter)."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking
    return x


def draw_dots(img, p):
    r = 150 * S
    c1 = ((1200 - 20 - 150) * S, (800 - 300 + 120 + 150) * S)     # matches the CSS: 25cqw dots, bottom -10cqw
    c2 = ((1200 + 140 - 150) * S, c1[1])
    d = ImageDraw.Draw(img)
    d.ellipse([c1[0] - r, c1[1] - r, c1[0] + r, c1[1] + r], fill=rgb(p['dot1']))
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).ellipse([c2[0] - r, c2[1] - r, c2[0] + r, c2[1] + r], fill=255)
    if p['blend'] == 'screen':
        top = Image.new('RGB', img.size, rgb(p['dot2']))
        from PIL import ImageChops
        mixed = ImageChops.screen(img, top)
    else:   # dot at 90% opacity over whatever is beneath
        top = Image.new('RGB', img.size, rgb(p['dot2']))
        mixed = Image.blend(img, top, 0.9)
    img.paste(mixed, (0, 0), mask)
    return img


def draw_icon(d, name, colour):
    """Simple line icons on a 24-unit grid, Lucide style, 1.3 stroke."""
    x0, y0, size = 312 * S, 136 * S, 432 * S
    u = size / 24
    w = max(2, int(1.3 * u))
    P = lambda x, y: (x0 + x * u, y0 + y * u)
    col = rgb(colour)
    def line(*pts): d.line([P(*p) for p in pts], fill=col, width=w, joint='curve')
    def rrect(x, y, x2, y2, rad=1.2): d.rounded_rectangle([P(x, y), P(x2, y2)], radius=rad * u, outline=col, width=w)
    def circle(cx, cy, r): d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], outline=col, width=w)
    if name == 'bars':
        rrect(3, 14, 6.5, 21); rrect(8.5, 10, 12, 21); rrect(14, 6.5, 17.5, 21); rrect(19.5, 3, 23, 21)
    elif name == 'target':
        circle(12, 12, 10); circle(12, 12, 6); circle(12, 12, 2)
    elif name == 'checklist':
        line((3, 17), (5, 19), (9, 15)); line((3, 7), (5, 9), (9, 5))
        line((13, 6), (21, 6)); line((13, 12), (21, 12)); line((13, 18), (21, 18))
    elif name == 'layers':
        line((12, 2), (22, 7), (12, 12), (2, 7), (12, 2)); line((2, 12), (12, 17), (22, 12)); line((2, 17), (12, 22), (22, 17))
    elif name == 'trend':
        line((2, 17), (8.5, 10.5), (13.5, 15.5), (22, 7)); line((16, 7), (22, 7), (22, 13))
    elif name == 'bulb':
        d.arc([P(5, 2), P(19, 16)], start=140, end=40, fill=col, width=w)
        line((7.6, 13.5), (9, 16), (9, 18)); line((16.4, 13.5), (15, 16), (15, 18)); line((9, 18), (15, 18)); line((10, 21.5), (14, 21.5))
    else:
        sys.exit(f'Unknown image_icon "{name}". Use: bars, target, checklist, layers, trend, bulb')


def render(a, out):
    kind = a.get('image_kind', 'icon')
    if kind not in ('hook', 'icon'):
        sys.exit('image_kind must be "hook" (word image) or "icon". Number images are not used.')
    p = palette(a['topic'], a.get('image_background', 'solid'))
    img = Image.new('RGB', (W * S, H * S), rgb(p['bg']))
    d = ImageDraw.Draw(img)
    wm = ImageFont.truetype(FONT_BOLD, 38 * S)
    tracked_text(d, (72 * S, 56 * S), 'codi studio', wm, rgb(p['ink']), -0.03 * 38 * S)
    if kind == 'hook':
        size = 138 * S
        f = ImageFont.truetype(FONT_XBOLD, size)
        line_h = 0.95 * size
        bottom = (800 - 224) * S                     # text block sits 28% up from the bottom
        asc, desc = f.getmetrics()
        y2 = bottom - asc - desc * 0.3
        y1 = y2 - line_h
        tracked_text(d, (72 * S, y1), a.get('image_line1', ''), f, rgb(p['ink']), -0.05 * size)
        tracked_text(d, (72 * S, y2), a.get('image_line2', ''), f, rgb(p['accent']), -0.05 * size)
    else:
        solid = a.get('image_background', 'solid') != 'indigo'
        draw_icon(d, a.get('image_icon', 'target'), p['ink'] if solid else p['accent'])
    img = draw_dots(img, p)
    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, 'PNG', optimize=True)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    out = os.path.join(br.SITE, 'images', 'resources', f'{slug}.png')
    if '--out' in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    a = br.read_article(os.path.join(br.CONTENT, f'{slug}.md'))
    print(render(a, out))


if __name__ == '__main__':
    main()
