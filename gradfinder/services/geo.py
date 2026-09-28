"""Geometry and point projection, loaded once at start-up."""

import json
import os

from .albers import project as albers_project


class Geo:
    def __init__(self, geo_file, projection_file):
        with open(geo_file, "r", encoding="utf-8") as fh:
            self.geo = json.load(fh)
        with open(projection_file, "r", encoding="utf-8") as fh:
            self.projection = json.load(fh)
        self.canvas = self.geo["canvas"]

    @property
    def state_codes(self):
        return sorted(self.geo["states"].keys())

    def name_of(self, code):
        rec = self.geo["states"].get(code)
        return rec["name"] if rec else code

    def project(self, lat, lon, state_code):
        x, y = albers_project(lon, lat, state_code, self.projection)
        return [round(x, 2), round(y, 2)]

    def in_canvas(self, xy):
        x, y = xy
        return 0 <= x <= self.canvas["width"] and 0 <= y <= self.canvas["height"]


def load_geo(app_config):
    for path in (app_config.GEO_FILE, app_config.PROJECTION_FILE):
        if not os.path.exists(path):
            raise SystemExit(
                "missing %s\nRun:  python tools/build_geo.py" % os.path.basename(path)
            )
    return Geo(app_config.GEO_FILE, app_config.PROJECTION_FILE)
