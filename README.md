# codi studio website (codistudio.ai)

Static site, hosted on Netlify. Netlify publishes the `site/` folder (base directory `site`).

## Publish an article (Walt)
1. Add `content/resources/<slug>.md` with front matter (copy an existing article).
2. Run `python3 tools/build_resources.py`. It builds the article page, the Resources cards, the homepage's latest 3 and the sitemap.
3. Open a pull request. Netlify posts a preview link. Louise merges = live.

Only articles that exist as .md files appear on the site. `draft: true` keeps one off.

## Front matter
- `title`, `slug`, `topic` (Strategy, Implementation, AI how-to, Future of work), `date` (YYYY-MM-DD), `excerpt` are required.
- `card_title` (shorter title for cards), `description` (meta description), `author`, `order` (tie-break on the same date) are optional.
- Image rules (Louise, 22 Nov 2026): only a word image (`image_kind: hook`, two lines) or an icon image (`image_kind: icon`). No number images. Alternate word, icon, word by publish order.
- Image: `image_file: /images/resources/<file>` uses a supplied image. Leave it empty and the build draws one automatically (tools/render_image.py, no browser needed) from `image_kind` (hook or icon), `image_background` (solid or indigo), `image_big`, `image_line1`, `image_line2`, `image_icon` (bars, target, checklist, layers, trend, bulb). The PNG is also the LinkedIn / social preview picture. Never put the article title on the image.

## Rules
- Edit only through this repo. No drag-and-drop deploys or Netlify AI edits once Git is linked.
- Never hand-edit between the `CARDS` / `FILTERS` markers in `site/index.html` and `site/resources.html`. The build script owns them.
