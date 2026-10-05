#!/usr/bin/env python3
"""
Import (repost) Substack posts into this Jekyll site.

Two sources are supported:

  1. Your Substack RSS feed — quickest, covers your ~20 most recent free posts:
       python3 scripts/import_substack.py --feed https://NAME.substack.com/feed

  2. A full Substack export (Settings -> Exports -> "Create new export"), as the
     downloaded .zip or the unzipped folder:
       python3 scripts/import_substack.py --export ~/Downloads/export.zip \
           --substack-url https://NAME.substack.com

Each post is written to _posts/YYYY-MM-DD-slug.html with front matter that
links back to the original (and sets it as the canonical URL, so search engines
don't treat the repost as duplicate content). The HTML is cleaned up:
  * Substack footnotes -> the site's sidenote markup (shown in the margin)
  * Substack LaTeX blocks -> \\[ ... \\] rendered by KaTeX
  * image containers -> plain <figure>/<figcaption>
  * subscribe / share buttons removed

Options:
  --link-only   don't copy the content; create stubs whose blog entry links
                straight to Substack
  --only SLUG   import just one post (repeatable)
  --force       overwrite posts that already exist
  --dry-run     show what would be written

Uses only the Python standard library.
"""

import argparse
import csv
import html
import io
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def find_elements(src, tag, cls):
    """Yield (start, end) spans of <tag class="... cls ..."> elements, balancing nesting."""
    open_re = re.compile(r"<%s\b[^>]*\bclass=\"(?:[^\"]*\s)?%s(?:\s[^\"]*)?\"[^>]*>" % (tag, re.escape(cls)))
    any_re = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    pos = 0
    while True:
        m = open_re.search(src, pos)
        if not m:
            return
        depth, i = 0, m.start()
        for t in any_re.finditer(src, m.start()):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                i = t.end()
                break
        else:
            return
        yield m.start(), i
        pos = i


def replace_elements(src, tag, cls, fn):
    out, last = [], 0
    for start, end in list(find_elements(src, tag, cls)):
        out.append(src[last:start])
        out.append(fn(src[start:end]))
        last = end
    out.append(src[last:])
    return "".join(out)


def inner_html(element):
    return re.sub(r"^<[^>]+>|</[a-z0-9]+>$", "", element.strip(), flags=re.S)


def attr(tag_html, name):
    m = re.search(r'\b%s="([^"]*)"' % name, tag_html)
    return html.unescape(m.group(1)) if m else ""


# ---------------------------------------------------------------------------
# Substack -> site markup
# ---------------------------------------------------------------------------

def convert_latex(el):
    try:
        data = json.loads(attr(el, "data-attrs") or "{}")
        expr = data.get("persistentExpression", "").strip()
    except json.JSONDecodeError:
        expr = ""
    if not expr:
        return el
    return '<div class="math-display">\\[%s\\]</div>' % html.escape(expr, quote=False)


def convert_image(el):
    img = re.search(r"<img\b[^>]*>", el)
    if not img:
        return el
    src, alt = attr(img.group(0), "src"), attr(img.group(0), "alt")
    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", el, re.S)
    out = '<figure><img src="%s" alt="%s" loading="lazy">' % (html.escape(src), html.escape(alt))
    if cap and cap.group(1).strip():
        out += "<figcaption>%s</figcaption>" % cap.group(1).strip()
    return out + "</figure>"


def convert_footnotes(src):
    notes = {}

    def grab(el):
        num = re.search(r'class="footnote-number"[^>]*>\s*([^<\s]+)\s*<', el)
        content = next(find_elements(el, "div", "footnote-content"), None)
        if num and content:
            notes[num.group(1)] = inner_html(el[content[0]:content[1]])
        return ""

    src = replace_elements(src, "div", "footnote", grab)

    def anchor(m):
        n = m.group(2).strip()
        return ('<sup id="fnref:%s" role="doc-noteref"><a href="#fn:%s" class="footnote" '
                'rel="footnote">%s</a></sup>' % (n, n, n))

    src = re.sub(r'<a\b([^>]*class="footnote-anchor"[^>]*)>(.*?)</a>', anchor, src, flags=re.S)

    if notes:
        items = []
        for n, body in notes.items():
            back = '&nbsp;<a href="#fnref:%s" class="reversefootnote" role="doc-backlink">&#8617;&#xFE0E;</a>' % n
            body = re.sub(r"</p>\s*$", back + "</p>", body) if body.rstrip().endswith("</p>") else body + back
            items.append('  <li id="fn:%s" role="doc-endnote">%s</li>' % (n, body))
        src += ('\n<div class="footnotes" role="doc-endnotes">\n<ol>\n%s\n</ol>\n</div>\n'
                % "\n".join(items))
    return src


def clean_html(src):
    src = replace_elements(src, "div", "latex-rendered", convert_latex)
    src = replace_elements(src, "div", "captioned-image-container", convert_image)
    for cls in ("subscription-widget-wrap", "subscription-widget-wrap-editor",
                "subscribe-widget", "share-dialog", "image-link-expand"):
        src = replace_elements(src, "div", cls, lambda _: "")
    src = replace_elements(src, "p", "button-wrapper", lambda _: "")
    src = convert_footnotes(src)
    src = re.sub(r"\n{3,}", "\n\n", src)
    return src.strip() + "\n"


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def slug_from_url(url):
    m = re.search(r"/p/([^/?#]+)", url)
    return m.group(1) if m else re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")


def read_url_or_file(loc):
    if re.match(r"https?://", loc):
        req = urllib.request.Request(loc, headers={"User-Agent": "Mozilla/5.0 (jekyll importer)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                sys.exit(
                    "Substack refused the download (HTTP %d). Its bot protection often blocks\n"
                    "servers and cloud machines. Instead:\n"
                    "  1. Open %s in your browser, save the page as feed.xml, then run\n"
                    "       python3 scripts/import_substack.py --feed feed.xml\n"
                    "  2. Or download a full export (Substack Settings -> Exports) and use --export.\n"
                    "  3. Or run this script on your own laptop." % (e.code, loc))
            raise
    return Path(loc).expanduser().read_bytes()


def from_feed(loc):
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    root = ET.fromstring(read_url_or_file(loc))
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        yield {
            "title": (item.findtext("title") or "").strip(),
            "subtitle": (item.findtext("description") or "").strip(),
            "date": parsedate_to_datetime(item.findtext("pubDate")),
            "url": link,
            "slug": slug_from_url(link),
            "html": item.findtext("content:encoded", namespaces=ns) or "",
        }


def from_export(loc, base_url):
    path = Path(loc).expanduser()
    if path.suffix == ".zip":
        z = zipfile.ZipFile(path)
        names = z.namelist()
        read = lambda n: z.read(n).decode("utf-8")
    else:
        names = [str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()]
        read = lambda n: (path / n).read_text(encoding="utf-8")

    csv_name = next((n for n in names if n.endswith("posts.csv")), None)
    if not csv_name:
        sys.exit("posts.csv not found in the export")
    for row in csv.DictReader(io.StringIO(read(csv_name))):
        if row.get("is_published", "").lower() != "true" or not row.get("post_date"):
            continue
        post_id = row["post_id"]
        slug = post_id.split(".", 1)[1] if "." in post_id else post_id
        html_name = next((n for n in names if n.endswith("posts/%s.html" % post_id)), None)
        yield {
            "title": row.get("title", "").strip(),
            "subtitle": row.get("subtitle", "").strip(),
            "date": datetime.fromisoformat(row["post_date"].replace("Z", "+00:00")),
            "url": "%s/p/%s" % (base_url.rstrip("/"), slug) if base_url else "",
            "slug": slug,
            "html": read(html_name) if html_name else "",
        }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def write_post(post, link_only, force, dry_run):
    day = post["date"].strftime("%Y-%m-%d")
    existing = list(POSTS_DIR.glob("*-%s.*" % post["slug"]))
    target = POSTS_DIR / ("%s-%s.html" % (day, post["slug"]))
    if existing and not force:
        print("skip   %s (already imported: %s)" % (post["slug"], existing[0].name))
        return
    fm = ["---", "title: " + yaml_str(post["title"])]
    if post["subtitle"]:
        fm.append("description: " + yaml_str(post["subtitle"]))
    fm.append("date: " + post["date"].strftime("%Y-%m-%d %H:%M:%S %z"))
    fm.append("original_source: Substack")
    if post["url"]:
        key = "external_url" if link_only else "original_url"
        fm.append("%s: %s" % (key, yaml_str(post["url"])))
        if not link_only:
            fm.append("canonical_url: " + yaml_str(post["url"]))
    fm += ["tags: []", "---", ""]

    if link_only:
        body = "<p>This post lives on Substack: <a href=\"%s\">read it there</a>.</p>\n" % post["url"]
    else:
        # Escape "{{" / "{%" as an HTML entity so Jekyll's Liquid engine leaves
        # them alone (e.g. in code or LaTeX); browsers render them unchanged.
        body = re.sub(r"\{(?=[{%])", "&#123;", clean_html(post["html"]))

    if dry_run:
        print("would write %s" % target.relative_to(ROOT))
        return
    for old in existing:
        old.unlink()
    target.write_text("\n".join(fm) + body, encoding="utf-8")
    print("wrote  %s" % target.relative_to(ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--feed", help="Substack RSS feed URL (https://NAME.substack.com/feed) or a saved feed file")
    src.add_argument("--export", help="Substack export .zip or unzipped folder")
    ap.add_argument("--substack-url", help="e.g. https://NAME.substack.com (needed with --export for backlinks)")
    ap.add_argument("--only", action="append", metavar="SLUG", help="import only this post slug (repeatable)")
    ap.add_argument("--link-only", action="store_true", help="create link-out stubs instead of copying content")
    ap.add_argument("--force", action="store_true", help="overwrite already-imported posts")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    posts = from_feed(args.feed) if args.feed else from_export(args.export, args.substack_url)
    POSTS_DIR.mkdir(exist_ok=True)
    n = 0
    for post in posts:
        if args.only and post["slug"] not in args.only:
            continue
        write_post(post, args.link_only, args.force, args.dry_run)
        n += 1
    if n == 0:
        print("No matching posts found.")


if __name__ == "__main__":
    main()
