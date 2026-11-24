#!/usr/bin/env python3
"""Build the Resources section of the codi studio site.

Reads every article in content/resources/*.md and writes:
  - site/resources/<slug>.html   one page per article
  - the cards on site/resources.html (all articles, newest first)
  - the cards on site/index.html (latest 3)
  - the article URLs in site/sitemap.xml

Only articles that exist as .md files appear anywhere. Add an article = add a .md file
and run:  python3 tools/build_resources.py
Set `draft: true` in an article's front matter to keep it off the site.
"""
import html, json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
CONTENT = os.path.join(ROOT, 'content', 'resources')
BASE = 'https://codistudio.ai'
SAME_AS = ['https://www.linkedin.com/company/codi-studio', 'https://www.youtube.com/channel/UCgojBGcJphn3vuFl9xBCvhg']  # Codi Studio's own profiles
CALENDLY = 'https://calendly.com/louise-read-codi-marketing/30min'

TOPICS = {  # topic: (colour, tag text colour)
    'Strategy': ('#8DFFBE', '#12032E'),
    'Implementation': ('#8B4BFF', '#FFFFFF'),
    'AI how-to': ('#7CC4FF', '#12032E'),
    'Future of work': ('#E4CCFF', '#12032E'),
}
FILTERS_FROM = 6  # show topic filters once there are this many articles

ICONS = {  # Lucide-style paths, 24x24
    'target': '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>',
    'checklist': '<path d="m3 17 2 2 4-4"></path><path d="m3 7 2 2 4-4"></path><path d="M13 6h8"></path><path d="M13 12h8"></path><path d="M13 18h8"></path></svg>'.replace('</svg>', ''),
    'layers': '<path d="m12 2 10 5-10 5L2 7z"></path><path d="m2 17 10 5 10-5"></path><path d="m2 12 10 5 10-5"></path>',
    'trend': '<path d="m22 7-8.5 8.5-5-5L2 17"></path><path d="M16 7h6v6"></path>',
}

esc = lambda s: html.escape(s, quote=True)


def read_article(path):
    text = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not m:
        sys.exit(f'No front matter in {path}')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    meta['body'] = m.group(2)
    for req in ['title', 'slug', 'topic', 'date', 'excerpt']:
        if not meta.get(req):
            sys.exit(f'{path}: missing {req}')
    if meta['topic'] not in TOPICS:
        sys.exit(f'{path}: topic must be one of {list(TOPICS)}')
    meta['card_title'] = meta.get('card_title') or meta['title']
    meta['order'] = int(meta.get('order') or 0)
    return meta


# ---------- markdown (the subset Google Docs exports) ----------
def clean(s):
    return re.sub(r'\\([&$.\-#*_()\[\]!+])', r'\1', s)


def inline(s):
    s = esc(clean(s))
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: link(m.group(1), m.group(2)), s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    return s


def link(text, url):
    url = html.unescape(url)
    ext = url.startswith('http') and 'codistudio.ai' not in url
    attrs = ' target="_blank" rel="noopener"' if ext else ''
    return f'<a href="{esc(url)}"{attrs}>{text}</a>'


def plain(s):
    return re.sub(r'\*\*|\*', '', re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean(s))).strip()


def md_to_html(md):
    out, faqs, para, lst, ltype = [], [], [], [], None
    section, pending_q = None, None

    def flush_para():
        nonlocal para, pending_q
        if para:
            txt = ' '.join(para).strip()
            if txt.startswith('***') and txt.endswith('***'):
                out.append(f'<blockquote><p>{inline(txt.strip("*"))}</p></blockquote>')
            else:
                out.append(f'<p>{inline(txt)}</p>')
                if section == 'faq' and pending_q:
                    faqs.append((pending_q, plain(txt)))
                    pending_q = None
            para = []

    def flush_list():
        nonlocal lst, ltype
        if lst:
            tag = 'ol' if ltype == 'ol' else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(i)}</li>' for i in lst) + f'</{tag}>')
            lst, ltype = [], None

    for raw in md.splitlines():
        hard_break = raw.endswith('  ')
        line = raw.strip()
        h = re.match(r'(#{2,4})\s+(.*)', line)
        li = re.match(r'[*\-]\s+(.*)', line)
        ol = re.match(r'\d+\\?\.\s+(.*)', line)
        if not line:
            flush_para(); flush_list(); continue
        if h:
            flush_para(); flush_list()
            level = len(h.group(1))
            text = plain(h.group(2))
            if level == 2:
                section = 'faq' if text.lower() in ('faqs', 'faq') else ('sources' if text.lower() == 'sources' else None)
            if level == 3 and section == 'faq':
                pending_q = text
            hid = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            out.append(f'<h{level} id="{hid}">{esc(text)}</h{level}>')
            continue
        if li or ol:
            flush_para()
            t = 'ol' if ol else 'ul'
            if ltype and ltype != t:
                flush_list()
            ltype = t
            lst.append((li or ol).group(1).strip())
            continue
        flush_list()
        para.append(line)
        if hard_break:
            flush_para()
    flush_para(); flush_list()
    body = '\n'.join(out)
    body = body.replace('<h2 id="sources">', '<h2 id="sources" class="sources-h">')
    return body, faqs


# ---------- image ----------
def blog_image(a, extra_class=''):
    if a.get('image_file'):
        return (f'<div class="blog-image{extra_class}"><img src="{esc(a["image_file"])}" alt="" loading="lazy" '
                f'style="display:block;width:100%;height:100%;object-fit:cover"></div>')
    colour, _ = TOPICS[a['topic']]
    impl = a['topic'] == 'Implementation'
    solid = a.get('image_background', 'solid') != 'indigo'
    if solid:
        bg = f'background: {colour};'
        ink = '#FFFFFF' if impl else '#12032E'
        accent = '#35FF9A' if impl else '#8B4BFF'
        dot1, dot2 = ('#12032E', '#35FF9A; mix-blend-mode: screen') if impl else ('#8B4BFF', '#12032E; opacity: 0.9')
    else:
        bg = 'background: #12032E; border: 1px solid rgba(228,204,255,0.12);'
        ink = '#FFFFFF'
        accent = '#B48CFF' if impl else colour
        dot1, dot2 = '#8B4BFF', f'{accent}; mix-blend-mode: screen'
    kind = a.get('image_kind', 'icon')
    if kind == 'number':
        big = f'<div class="bi-number" style="color: {accent if not solid else ink}">{esc(a.get("image_big", ""))}</div>'
    elif kind == 'hook':
        big = (f'<div class="bi-hook" style="color: {ink}">{esc(a.get("image_line1", ""))}<br>'
               f'<span style="color: {accent}">{esc(a.get("image_line2", ""))}</span></div>')
    else:
        stroke = ink if solid else accent
        big = (f'<svg class="bi-icon" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.3" '
               f'stroke-linecap="round" stroke-linejoin="round">{ICONS.get(a.get("image_icon", "target"), ICONS["target"])}</svg>')
    return (f'<div class="blog-image{extra_class}" aria-hidden="true" style="{bg}">\n'
            f'<span class="bi-wordmark" style="color: {ink}">codi studio</span>\n{big}\n'
            f'<div class="bi-dot bi-dot-1" style="background: {dot1}"></div>\n'
            f'<div class="bi-dot bi-dot-2" style="background: {dot2}"></div>\n</div>')


def nice_date(d):
    y, m, dd = map(int, d.split('-'))
    return date(y, m, dd).strftime('%-d %b %Y')


def card(a, heading='h2'):
    colour, tag_ink = TOPICS[a['topic']]
    url = f'/resources/{a["slug"]}'
    t = esc(a['card_title'])
    return (f'<article class="blog-card" data-topic="{esc(a["topic"])}">\n{blog_image(a)}\n'
            f'<div class="blog-card-body">\n'
            f'<div class="blog-meta"><span class="blog-tag" style="background: {colour}; color: {tag_ink}">{esc(a["topic"])}</span>'
            f'<span>{nice_date(a["date"])}</span></div>\n'
            f'<{heading} class="blog-title"><a href="{url}">{t}</a></{heading}>\n'
            f'<p class="blog-excerpt">{esc(a["excerpt"])}</p>\n'
            f'<a href="{url}" class="blog-read" aria-label="Read {t}">Read now →</a>\n</div>\n</article>')


def replace_between(s, start, end, new):
    i, j = s.index(start) + len(start), s.index(end)
    return s[:i] + '\n' + new + ('\n' if new else '') + s[j:]


ARTICLE_CSS = """
.article-wrap{max-width:760px;margin:0 auto;padding:0 32px;box-sizing:content-box}
.prose{font-size:18px;line-height:1.75;color:#E9E2F7}
.prose p{margin:0 0 22px}
.prose h2{margin:56px 0 18px;font-size:clamp(26px,3vw,34px);font-weight:700;letter-spacing:-0.02em;line-height:1.2;color:#fff}
.prose h3{margin:36px 0 12px;font-size:22px;font-weight:700;letter-spacing:-0.01em;line-height:1.3;color:#fff}
.prose ul,.prose ol{margin:0 0 24px;padding-left:24px}
.prose li{margin:0 0 10px;padding-left:4px}
.prose li::marker{color:#8DFFBE}
.prose strong{color:#fff;font-weight:600}
.prose a{color:#8DFFBE;text-decoration:underline;text-underline-offset:3px}
.prose a:hover{color:#35FF9A}
.prose blockquote{margin:36px 0;padding:4px 0 4px 24px;border-left:3px solid #35FF9A;font-size:clamp(22px,2.6vw,28px);font-weight:600;line-height:1.35;letter-spacing:-0.01em;color:#fff}
.prose blockquote p{margin:0}
.prose .sources-h ~ ul{font-size:14px;line-height:1.6;color:#CFC4E8}
.prose .sources-h{font-size:20px}
.article-image{border-radius:20px;margin:0 0 48px}
"""


def article_page(a, template):
    body, faqs = md_to_html(a['body'])
    url = f'{BASE}/resources/{a["slug"]}'
    title = a['title']
    desc = a.get('description') or a['excerpt']
    head_end = template.index('<!-- /seo -->')
    head = template[:head_end]
    old_title = re.search(r'<title>(.*?)</title>', head).group(1)
    old_desc = re.search(r'<meta name="description" content="(.*?)">', head).group(1)
    page_title = f'{title} | codi studio'
    head = head.replace(f'<title>{old_title}</title>', f'<title>{esc(page_title)}</title>')
    head = head.replace(f'content="{old_title}"', f'content="{esc(page_title)}"')
    head = head.replace(old_desc, esc(desc))
    head = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\g<1>' + url, head)
    head = re.sub(r'(<meta property="og:url" content=")[^"]*', r'\g<1>' + url, head)
    head = head.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="article">')
    head = head.replace('</style>', '/* article */' + ARTICLE_CSS + '</style>', 1)
    share_img = BASE + (a['image_file'] if a.get('image_file') else '/images/codi-studio-share.jpg')
    head = head.replace('<meta name="twitter:card"',
                        f'<meta property="og:image" content="{share_img}">\n<meta name="twitter:image" content="{share_img}">\n<meta name="twitter:card"', 1)
    author = a.get('author', 'Louise Read')
    graph = [{
        '@type': 'Article', 'headline': title, 'description': desc, 'datePublished': a['date'],
        'dateModified': a.get('updated', a['date']), 'mainEntityOfPage': url,
        'author': ({'@type': 'Organization', 'name': 'Codi Studio', '@id': f'{BASE}/#org'} if author.lower().startswith('codi')
                   else {'@type': 'Person', 'name': 'Louise Read', '@id': f'{BASE}/speaking#louise'}),
        'publisher': {'@id': f'{BASE}/#org'},
        'image': share_img,
    }]
    # Publisher: the full Codi Studio entity, so Google ties every article to the brand
    graph.append({'@type': 'ProfessionalService', '@id': f'{BASE}/#org', 'name': 'Codi Studio',
                  'alternateName': ['codi studio', 'Codi Studio AI', 'codistudio.ai'], 'url': f'{BASE}/',
                  'logo': {'@type': 'ImageObject', 'url': f'{BASE}/apple-touch-icon.png', 'width': 180, 'height': 180},
                  'sameAs': SAME_AS})
    if faqs:
        graph.append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': ans}} for q, ans in faqs]})
    graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Resources', 'item': f'{BASE}/resources'},
        {'@type': 'ListItem', 'position': 2, 'name': title, 'item': url}]})
    ld = '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False) + '</script>\n'
    # header + footer straight from the resources page (Resources link is current)
    header = template[template.index('<header class="site-header"'):template.index('</header>') + 9]
    footer = template[template.index('<footer'):template.index('</footer>') + 9]
    scripts = template[template.rindex('<script>'):template.rindex('</script>') + 9]
    close = template[template.rindex('<section style="border-top: 1px solid rgba(228,204,255,0.18); position: relative'):template.index('<footer')]
    colour, tag_ink = TOPICS[a['topic']]
    byline = esc(author if author.lower().startswith('codi') else author)
    hero = f'''
<div style="padding:72px 0 40px">
<div class="article-wrap" style="display:flex;flex-direction:column;gap:22px">
<a href="/resources" class="hv1" style="color:#CFC4E8;text-decoration:none;font-size:15px;font-weight:500">← All resources</a>
<div class="blog-meta"><span class="blog-tag" style="background: {colour}; color: {tag_ink}">{esc(a["topic"])}</span><span>{nice_date(a["date"])}</span></div>
<h1 style="margin:0;font-size:clamp(34px,4.4vw,52px);font-weight:700;letter-spacing:-0.03em;line-height:1.08;text-wrap:balance">{esc(title)}</h1>
<p style="margin:0;font-size:15px;color:#CFC4E8">By {byline}</p>
</div>
</div>
<main>
<article class="article-wrap" style="padding-bottom:96px">
{blog_image(a, ' article-image')}
<div class="prose">
{body}
</div>
</article>
</main>
'''
    return (head + ld + '<!-- /seo -->\n</head>\n<body>\n<div style="background:#12032E;color:#fff;font-family:\'Poppins\',sans-serif;min-height:100vh">\n\n'
            + header + '\n' + hero + close + footer + '\n</div>\n' + scripts + '\n</body>\n</html>\n')


def main():
    arts = []
    for f in sorted(os.listdir(CONTENT)):
        if f.endswith('.md'):
            a = read_article(os.path.join(CONTENT, f))
            if a.get('draft', '').lower() != 'true':
                arts.append(a)
    arts.sort(key=lambda a: (a['date'], -a['order']), reverse=True)
    res_path = os.path.join(SITE, 'resources.html')
    template = open(res_path, encoding='utf-8').read()

    # article pages
    out_dir = os.path.join(SITE, 'resources')
    os.makedirs(out_dir, exist_ok=True)
    live = set()
    for a in arts:
        if not a.get('image_file'):
            # every article gets a real PNG: card, article header and LinkedIn preview
            png = os.path.join(SITE, 'images', 'resources', a['slug'] + '.png')
            if not os.path.exists(png):
                import render_image
                render_image.render(a, png)
            a['image_file'] = f'/images/resources/{a["slug"]}.png'
        open(os.path.join(out_dir, a['slug'] + '.html'), 'w', encoding='utf-8').write(article_page(a, template))
        live.add(a['slug'] + '.html')
    for f in os.listdir(out_dir):  # remove pages whose article was deleted or set to draft
        if f.endswith('.html') and f not in live:
            os.remove(os.path.join(out_dir, f))

    # resources hub
    s = replace_between(template, '<!-- CARDS:START -->', '<!-- CARDS:END -->', '\n'.join(card(a) for a in arts))
    filters = ''
    if len(arts) >= FILTERS_FROM:
        used = [t for t in TOPICS if any(a['topic'] == t for a in arts)]
        btns = ['<button type="button" class="filter-btn" data-filter="All" aria-pressed="true">All</button>'] + [
            f'<button type="button" class="filter-btn hvpill" data-filter="{esc(t)}" aria-pressed="false">{esc(t)}</button>' for t in used]
        filters = '<div role="group" aria-label="Filter articles by topic" style="display: flex; flex-wrap: wrap; gap: 12px">\n' + '\n'.join(btns) + '\n</div>'
    s = replace_between(s, '<!-- FILTERS:START -->', '<!-- FILTERS:END -->', filters)
    # hub article list: sits after <!-- /seo --> so article pages don't inherit it (brand node is already in the page)
    hub = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': f'{BASE}/resources#page', 'url': f'{BASE}/resources', 'name': 'Resources',
         'description': re.search(r'<meta name="description" content="(.*?)">', s).group(1),
         'isPartOf': {'@id': f'{BASE}/#website'}, 'publisher': {'@id': f'{BASE}/#org'},
         'mainEntity': {'@type': 'ItemList', 'itemListElement': [
             {'@type': 'ListItem', 'position': i + 1, 'url': f'{BASE}/resources/{a["slug"]}', 'name': a['title']}
             for i, a in enumerate(arts)]}}]}
    hub_ld = '<script type="application/ld+json">' + json.dumps(hub, ensure_ascii=False) + '</script>'
    if '<!-- HUB-LD:START -->' not in s:
        s = s.replace('</head>', '<!-- HUB-LD:START -->\n<!-- HUB-LD:END -->\n</head>', 1)
    s = replace_between(s, '<!-- HUB-LD:START -->', '<!-- HUB-LD:END -->', hub_ld)
    open(res_path, 'w', encoding='utf-8').write(s)

    # homepage: latest 3
    idx_path = os.path.join(SITE, 'index.html')
    idx = open(idx_path, encoding='utf-8').read()
    idx = replace_between(idx, '<!-- CARDS:START -->', '<!-- CARDS:END -->', '\n'.join(card(a, 'h3') for a in arts[:3]))
    open(idx_path, 'w', encoding='utf-8').write(idx)

    # sitemap
    sm_path = os.path.join(SITE, 'sitemap.xml')
    sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'  <url><loc>https://codistudio.ai/resources/[^<]+</loc>.*?</url>\n', '', sm)
    extra = ''.join(f'  <url><loc>{BASE}/resources/{a["slug"]}</loc><lastmod>{a.get("updated", a["date"])}</lastmod></url>\n' for a in arts)
    sm = sm.replace('</urlset>', extra + '</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)
    print(f'Built {len(arts)} article(s): ' + ', '.join(a['slug'] for a in arts))


if __name__ == '__main__':
    main()
