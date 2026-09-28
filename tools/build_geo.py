#!/usr/bin/env python3
"""
build_geo.py — US states GeoJSON -> projected SVG path data.

Inputs
    tools/us-states.raw.json        source GeoJSON (WGS84, 52 features incl. DC + PR)

Outputs
    gradfinder/static/geo/us_states.json    path d strings, bbox, centroid per state
    data/derived/projection.json            solved affine fits for the three regions

Run:  python tools/build_geo.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gradfinder.services.albers import CONES, albers_raw, apply_fit, region_for, solve_fit  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "us-states.raw.json")
OUT_GEO = os.path.join(ROOT, "gradfinder", "static", "geo", "us_states.json")
OUT_PROJ = os.path.join(ROOT, "data", "derived", "projection.json")

CANVAS = (975, 610)
BOX_L48 = (14, 8, 961, 500)
BOX_AK = (18, 396, 214, 586)
BOX_HI = (232, 500, 344, 584)

DROP = {"Puerto Rico"}
SIMPLIFY_EPS = 0.35       # pixels
MIN_RING_AREA = 1.2       # square pixels; drops slivers, keeps the Hawaiian chain

USPS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


# ---------------------------------------------------------------- progress UI
class Progress:
    """Single-line progress bar with a final elapsed-time report."""

    def __init__(self, label, total, width=34):
        self.label = label
        self.total = max(total, 1)
        self.width = width
        self.t0 = time.time()
        self.n = 0
        self.draw()

    def step(self, n=1):
        self.n += n
        self.draw()

    def draw(self):
        frac = min(self.n / self.total, 1.0)
        filled = int(round(frac * self.width))
        bar = "#" * filled + "-" * (self.width - filled)
        sys.stdout.write("\r  [%s] %3d%%  %s" % (bar, round(frac * 100), self.label))
        sys.stdout.flush()

    def done(self, note=""):
        self.n = self.total
        self.draw()
        sys.stdout.write("  %.2fs %s\n" % (time.time() - self.t0, note))
        sys.stdout.flush()


def status(msg):
    print("[build_geo] %s" % msg)


# ------------------------------------------------------------------ geometry
def rings_of(geometry):
    """Flatten Polygon / MultiPolygon into a list of coordinate rings."""
    if geometry["type"] == "Polygon":
        return list(geometry["coordinates"])
    out = []
    for poly in geometry["coordinates"]:
        out.extend(poly)
    return out


def perp_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return ((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2) ** 0.5


def douglas_peucker(pts, eps):
    if len(pts) < 3:
        return pts
    stack = [(0, len(pts) - 1)]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        worst, wi = -1.0, i
        for k in range(i + 1, j):
            d = perp_dist(pts[k], pts[i], pts[j])
            if d > worst:
                worst, wi = d, k
        if worst > eps:
            keep[wi] = True
            stack.append((i, wi))
            stack.append((wi, j))
    return [p for p, k in zip(pts, keep) if k]


def ring_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def ring_centroid(pts):
    a = ring_area(pts)
    if abs(a) < 1e-9:
        n = len(pts)
        return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    cx = cy = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        cross = x0 * y1 - x1 * y0
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    return (cx / (6 * a), cy / (6 * a))


def path_d(rings, prec=1):
    parts = []
    for r in rings:
        if len(r) < 3:
            continue
        seg = ["M%s,%s" % (round(r[0][0], prec), round(r[0][1], prec))]
        for x, y in r[1:]:
            seg.append("L%s,%s" % (round(x, prec), round(y, prec)))
        seg.append("Z")
        parts.append("".join(seg))
    return "".join(parts)


# ----------------------------------------------------------------------- main
def main():
    t0 = time.time()
    status("canvas %dx%d, source %s" % (CANVAS[0], CANVAS[1], os.path.relpath(SRC, ROOT)))

    with open(SRC, "r", encoding="utf-8") as fh:
        gj = json.load(fh)

    feats = []
    for f in gj["features"]:
        name = f["properties"]["name"]
        if name in DROP:
            status("dropped %s (outside canvas scope)" % name)
            continue
        if name not in USPS:
            status("dropped %s (no USPS code)" % name)
            continue
        feats.append((USPS[name], name, f["geometry"]))
    status("%d jurisdictions in scope" % len(feats))

    # Pass 1 -- raw cone projection, grouped by region, so the fits can be solved.
    raw = {}
    by_region = {"l48": [], "ak": [], "hi": []}
    bar = Progress("projecting", len(feats))
    for code, name, geom in feats:
        region = region_for(code)
        cone = CONES[region]
        rings = []
        for ring in rings_of(geom):
            pts = [albers_raw(lon, lat, cone) for lon, lat in ring]
            rings.append(pts)
            by_region[region].extend(pts)
        raw[code] = {"name": name, "region": region, "rings": rings}
        bar.step()
    bar.done("%d vertices" % sum(len(v) for v in by_region.values()))

    fits = {
        "l48": solve_fit(by_region["l48"], BOX_L48),
        "ak": solve_fit(by_region["ak"], BOX_AK),
        "hi": solve_fit(by_region["hi"], BOX_HI),
    }
    for rid, fit in fits.items():
        status("fit %-4s scale %.1f  translate (%.1f, %.1f)" % (rid, fit["sx"], fit["tx"], fit["ty"]))

    # Pass 2 -- affine into canvas space, simplify, emit paths.
    states = {}
    kept = dropped = 0
    bar = Progress("simplifying", len(raw))
    for code, rec in sorted(raw.items()):
        fit = fits[rec["region"]]
        out_rings = []
        for pts in rec["rings"]:
            px = [apply_fit(p, fit) for p in pts]
            px = douglas_peucker(px, SIMPLIFY_EPS)
            if len(px) < 3 or abs(ring_area(px)) < MIN_RING_AREA:
                dropped += 1
                continue
            out_rings.append(px)
            kept += len(px)
        if not out_rings:
            status("WARNING %s produced no rings" % code)
            continue
        biggest = max(out_rings, key=lambda r: abs(ring_area(r)))
        xs = [p[0] for r in out_rings for p in r]
        ys = [p[1] for r in out_rings for p in r]
        cx, cy = ring_centroid(biggest)
        states[code] = {
            "name": rec["name"],
            "region": rec["region"],
            "d": path_d(out_rings),
            "bbox": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
            "centroid": [round(cx, 1), round(cy, 1)],
        }
        bar.step()
    bar.done("%d vertices kept, %d slivers dropped" % (kept, dropped))

    geo = {
        "schema": "gradfinder.geo/1",
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "source": "us-states.raw.json (public-domain state outlines, coarse)",
        "states": states,
    }
    proj = {
        "schema": "gradfinder.projection/1",
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "cones": CONES,
        "fits": fits,
        "boxes": {"l48": BOX_L48, "ak": BOX_AK, "hi": BOX_HI},
    }

    for path, doc in ((OUT_GEO, geo), (OUT_PROJ, proj)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))
        status("wrote %s (%.1f KB)" % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024))

    status("done in %.2fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
