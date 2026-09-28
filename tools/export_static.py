#!/usr/bin/env python3
"""
export_static.py -- freeze the Flask app into a static site for GitHub Pages.

Runs the real app once through Flask's test client, so the static site is built
by the same code the dev server runs. Writes:

    site/index.html, site/method.html      rendered pages, relative URLs
    site/static/...                        css, js, geo, icons (copied)
    site/api/*.json                        every API response the front end asks for
    site/.nojekyll                         stop Pages from running Jekyll

Family filtering happens in the browser in static mode (see static/js/api.js).

Run:  python tools/export_static.py [--out site]
"""

import argparse
import json
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402


def bar(i, n, label, width=28):
    fill = int(width * i / max(n, 1))
    sys.stdout.write("\r  [%s%s] %3d/%-3d %-28s" % ("#" * fill, "." * (width - fill), i, n, label[:28]))
    sys.stdout.flush()


def relativise(html):
    """Absolute app URLs -> paths relative to the site root, so the site works under
    https://<user>.github.io/<repo>/ as well as from a plain file server."""
    html = html.replace('href="/static/', 'href="static/').replace('src="/static/', 'src="static/')
    html = html.replace('href="/method"', 'href="method.html"').replace('href="/"', 'href="index.html"')
    # Flip the front end into static mode before any app script runs.
    html = html.replace("</head>", "<script>window.GF_STATIC = true;</script>\n</head>", 1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "site"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    t0 = time.time()

    class Frozen(Config):
        DEBUG = False
        HOT_RELOAD_DATA = False

    print("[export] booting app")
    from gradfinder import create_app
    app = create_app(Frozen)
    client = app.test_client()

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "api", "states"))
    os.makedirs(os.path.join(out, "api", "faculty"))

    codes = sorted(app.geo.state_codes)
    jobs = [("/api/v1/meta", "api/meta.json"),
            ("/api/v1/geo", "api/geo.json"),
            ("/api/v1/states", "api/states.json"),
            ("/api/v1/faculty", "api/faculty.json")]
    jobs += [("/api/v1/states/%s" % c, "api/states/%s.json" % c) for c in codes]
    jobs += [("/api/v1/faculty/%s" % c, "api/faculty/%s.json" % c) for c in codes]

    print("[export] writing %d API responses" % len(jobs))
    packs = 0
    for i, (url, rel) in enumerate(jobs, 1):
        r = client.get(url)
        if r.status_code not in (200, 404):
            print("\n[export] FAIL %s -> HTTP %d" % (url, r.status_code))
            return 1
        doc = r.get_json()
        if r.status_code == 404:
            doc["status"] = "empty"          # static mode reads this instead of the 404
        elif rel.startswith("api/states/"):
            packs += 1
        with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
        bar(i, len(jobs), rel)
    print()

    print("[export] rendering pages")
    for url, name in (("/", "index.html"), ("/method", "method.html")):
        r = client.get(url)
        if r.status_code != 200:
            print("[export] FAIL %s -> HTTP %d" % (url, r.status_code))
            return 1
        html = relativise(r.get_data(as_text=True))
        if re.search(r'(href|src)="/(?!/)', html):
            print("[export] FAIL %s still has a root-absolute URL" % name)
            return 1
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            fh.write(html)
        print("  [page] %s" % name)

    print("[export] copying static assets")
    shutil.copytree(os.path.join(ROOT, "gradfinder", "static"), os.path.join(out, "static"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy(os.path.join(ROOT, "gradfinder", "static", "favicon.ico"), os.path.join(out, "favicon.ico"))
    open(os.path.join(out, ".nojekyll"), "w").close()

    print("[export] copying search-material downloads")
    from gradfinder.routes.views import DOWNLOADS
    os.makedirs(os.path.join(out, "downloads"))
    for name in sorted(DOWNLOADS):
        shutil.copy(os.path.join(Config.FACULTY_DIR, name), os.path.join(out, "downloads", name))
        print("  [dl]   %s" % name)

    nfiles = sum(len(f) for _, _, f in os.walk(out))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print("=" * 62)
    print(" static site  %s" % out)
    print(" files        %d  (%.2f MB)" % (nfiles, size / 1e6))
    print(" state packs  %d of %d   faculty lens files %d" % (packs, len(codes), len(codes)))
    print(" built in     %.1f s" % (time.time() - t0))
    print(" preview      python -m http.server 8080 -d site")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
