# Academic website

A minimal Jekyll site for GitHub Pages: home/about, publications, CV, and a blog
with **margin sidenotes**, **LaTeX math (KaTeX)**, and **Substack reposting**.
No theme dependency; everything is in this repo.

## Where to edit things

| What                              | File                                   |
|-----------------------------------|----------------------------------------|
| Name, position, links, nav, CV PDF| `_config.yml`                          |
| Introduction / bio                | `index.md`                             |
| Profile photo                     | put it in `assets/img/`, set `author.avatar` |
| News                              | `_data/news.yml`                       |
| Publications                      | `_data/publications.yml`               |
| CV sections (education, awards…)  | `_data/cv.yml`                         |
| CV PDF                            | `assets/files/cv.pdf` + `cv_pdf:` in `_config.yml` |
| Blog posts                        | `_posts/YYYY-MM-DD-title.md`           |
| Colours / fonts                   | tokens at the top of `assets/css/main.css` |

Publications marked `selected: true` also appear on the home page. Your name is
bolded in author lists wherever it matches `author.pub_names`.

## Writing a post

Create `_posts/2026-10-01-my-post.md`:

```markdown
---
title: "My Post"
description: "One-line summary shown under the title and in previews."
tags: [ml, theory]
---

Text with a citation.[^vaswani] Inline math $$\alpha_t$$, and display math:

$$
\mathcal{L}(\theta) = -\sum_t \log p_\theta(x_t \mid x_{<t})
$$

[^vaswani]: A. Vaswani et al., "Attention Is All You Need," NeurIPS 2017.
```

- **Footnotes → sidenotes.** Ordinary Markdown footnotes appear in the right
  margin on wide screens; on phones, tapping the number opens the note inline.
- **Math.** Use `$$...$$` for both inline and display math (display = on its own
  lines). Single `$` is *not* math. Add `math: false` to skip loading KaTeX.
- **Unnumbered margin notes:** `{% include marginnote.html text="..." %}`.
- See `_posts/2026-09-29-writing-guide.md` for a demo of every feature
  (delete it when you're done with it).

## Reposting from Substack

```bash
# Latest posts, via your RSS feed:
python3 scripts/import_substack.py --feed https://NAME.substack.com/feed

# Everything, via Substack Settings → Exports:
python3 scripts/import_substack.py --export ~/Downloads/export.zip --substack-url https://NAME.substack.com
```

Posts land in `_posts/` as `.html` files. Footnotes become sidenotes, LaTeX
blocks render with KaTeX, and each post shows "Originally published on Substack"
with a canonical link back (good for SEO). Already-imported posts are skipped,
so re-running is safe; `--force` re-imports. Use `--link-only` to just list a
Substack post on your blog and link out to it; `--only SLUG` imports one post.
You can edit imported files afterwards (e.g. add `tags`).

To link to any external post without copying it, make a post whose front matter
has `external_url: https://...` (and optionally `original_source: Medium`).

## Preview locally

Requires Ruby ≥ 3.0. On Ubuntu, `apt install ruby-full` does not include
Bundler, so install it once into your home folder (no sudo needed):

```bash
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
gem install bundler
```

Then, in this folder:

```bash
bundle install
bundle exec jekyll serve --livereload   # http://localhost:4000
```

## Deploy on GitHub Pages

1. Create a repository named **`<username>.github.io`** and push this folder.
2. In `_config.yml`, set `url: "https://<username>.github.io"`
   (for a repo with another name, also set `baseurl: "/<repo-name>"`).
3. Repository **Settings → Pages → Build and deployment**: Source
   “Deploy from a branch”, branch `main`, folder `/ (root)`.

The site uses only plugins GitHub Pages supports (feed, SEO tags, sitemap),
so no build workflow is needed. Every push rebuilds the site in about a minute.
