"""
Albers USA composite projection.

Three conic equal-area sub-projections (lower 48, Alaska, Hawaii), each with its
own affine fit into a region of the canvas. Parameters are solved once by
tools/build_geo.py and written to data/derived/projection.json so that the geometry
build and the runtime point projection can never drift apart.

No dependencies outside the standard library.
"""

from math import asin, cos, radians, sin, sqrt

# Sub-projection cone definitions. Keyed by region id.
CONES = {
    "l48": {"lon0": -96.0, "lat0": 37.5, "phi1": 29.5, "phi2": 45.5},
    "ak": {"lon0": -152.0, "lat0": 60.0, "phi1": 55.0, "phi2": 65.0},
    "hi": {"lon0": -157.0, "lat0": 20.0, "phi1": 8.0, "phi2": 18.0},
}

# Which region each jurisdiction is drawn in.
REGION_OF_STATE = {"AK": "ak", "HI": "hi"}


def region_for(state_code):
    """Region id for a USPS state code."""
    return REGION_OF_STATE.get(state_code.upper(), "l48")


def albers_raw(lon, lat, cone):
    """Albers conic equal-area, unit sphere, y increasing north."""
    lam = radians(lon - cone["lon0"])
    phi = radians(lat)
    p1 = radians(cone["phi1"])
    p2 = radians(cone["phi2"])
    p0 = radians(cone["lat0"])

    n = 0.5 * (sin(p1) + sin(p2))
    if abs(n) < 1e-12:  # degenerate cone; fall back to a cylindrical case
        n = 1e-12
    c = cos(p1) ** 2 + 2.0 * n * sin(p1)
    rho0 = sqrt(max(c - 2.0 * n * sin(p0), 0.0)) / n
    rho = sqrt(max(c - 2.0 * n * sin(phi), 0.0)) / n
    theta = n * lam
    return rho * sin(theta), rho0 - rho * cos(theta)


def albers_inverse(x, y, cone):
    """Inverse of albers_raw. Used only by tools/check_data.py as a round-trip test."""
    p1 = radians(cone["phi1"])
    p2 = radians(cone["phi2"])
    p0 = radians(cone["lat0"])
    n = 0.5 * (sin(p1) + sin(p2))
    c = cos(p1) ** 2 + 2.0 * n * sin(p1)
    rho0 = sqrt(max(c - 2.0 * n * sin(p0), 0.0)) / n
    ry = rho0 - y
    rho = sqrt(x * x + ry * ry)
    if n < 0:
        rho = -rho
    theta = 0.0 if rho == 0 else asin(max(-1.0, min(1.0, x / rho)))
    from math import atan2, degrees

    theta = atan2(x, ry)
    phi = asin(max(-1.0, min(1.0, (c - rho * rho * n * n) / (2.0 * n))))
    return degrees(theta / n) + cone["lon0"], degrees(phi)


def apply_fit(xy, fit):
    """Apply a solved affine fit (scale + translate, y flipped) to raw projected xy."""
    x, y = xy
    return x * fit["sx"] + fit["tx"], y * fit["sy"] + fit["ty"]


def project(lon, lat, state_code, projection):
    """
    Geographic coordinate -> canvas pixel, using the fits in projection.json.

    projection: the parsed data/derived/projection.json document.
    """
    region = region_for(state_code)
    cone = CONES[region]
    fit = projection["fits"][region]
    return apply_fit(albers_raw(lon, lat, cone), fit)


def solve_fit(points, box, pad=6.0):
    """
    Solve scale/translate placing projected `points` inside `box` = (x0, y0, x1, y1).

    Equal aspect, y flipped for screen coordinates, centred in the box.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, y0, x1, y1 = box
    bw = (x1 - x0) - 2 * pad
    bh = (y1 - y0) - 2 * pad
    dx = max(max(xs) - min(xs), 1e-9)
    dy = max(max(ys) - min(ys), 1e-9)
    s = min(bw / dx, bh / dy)
    cx = 0.5 * (max(xs) + min(xs))
    cy = 0.5 * (max(ys) + min(ys))
    return {
        "sx": s,
        "sy": -s,
        "tx": 0.5 * (x0 + x1) - s * cx,
        "ty": 0.5 * (y0 + y1) + s * cy,
    }
