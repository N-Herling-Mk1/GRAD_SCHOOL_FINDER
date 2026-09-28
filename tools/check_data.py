#!/usr/bin/env python3
"""
check_data.py — validate every state pack before the server sees it.

Checks: required keys, family keys against config, marker coordinates landing
inside the state's own bounding box after projection, duplicate program names,
and rollup arithmetic. Exit code 1 on any error.

Run:  python tools/check_data.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FAMILIES, Config  # noqa: E402
from gradfinder.services.geo import load_geo  # noqa: E402

FAMILY_KEYS = {f["key"] for f in FAMILIES}
GPA_TYPES = {"floor", "recommended", "reported typical"}
GPA_SCOPES = {"institution", "program"}
REQUIRED_PACK = ["schema", "state", "state_name", "stage", "institutions"]
REQUIRED_INST = ["id", "name", "city", "lat", "lon", "control", "status", "programs"]

errors = []
warnings = []


def err(msg):
    errors.append(msg)
    print("  FAIL  %s" % msg)


def warn(msg):
    warnings.append(msg)
    print("  warn  %s" % msg)


def check_gpa(where, g):
    """A GPA number with no scope, basis, type or source is not usable evidence."""
    if g is None:
        return
    for k in ("value", "basis", "scope", "type", "source_url", "as_of"):
        if not g.get(k):
            err("%s gpa_min missing '%s'" % (where, k))
    if g.get("type") not in GPA_TYPES:
        err("%s gpa_min type '%s' is not one of %s" % (where, g.get("type"), sorted(GPA_TYPES)))
    if g.get("scope") not in GPA_SCOPES:
        err("%s gpa_min scope '%s' is not one of %s" % (where, g.get("scope"), sorted(GPA_SCOPES)))
    v = g.get("value")
    if isinstance(v, (int, float)) and not (0 < v <= g.get("scale", 4.0)):
        err("%s gpa_min value %s is outside the scale" % (where, v))
    if not str(g.get("source_url", "")).startswith("http"):
        err("%s gpa_min has no usable source_url" % where)


def main():
    geo = load_geo(Config)
    files = sorted(f for f in os.listdir(Config.INSTITUTIONS_DIR) if f.endswith(".json"))
    if not files:
        print("no packs found in %s" % Config.INSTITUTIONS_DIR)
        return 1

    print("[check] %d pack(s)" % len(files))
    for fname in files:
        code = os.path.splitext(fname)[0].upper()
        print("[check] %s" % code)
        with open(os.path.join(Config.INSTITUTIONS_DIR, fname), "r", encoding="utf-8") as fh:
            pack = json.load(fh)

        for k in REQUIRED_PACK:
            if k not in pack:
                err("%s missing top-level key '%s'" % (code, k))
        if pack.get("state") != code:
            err("%s declares state '%s' but the filename says %s" % (code, pack.get("state"), code))
        if code not in geo.geo["states"]:
            err("%s has no geometry" % code)
            continue

        bbox = geo.geo["states"][code]["bbox"]
        seen_ids = set()
        total = 0
        for inst in pack.get("institutions", []):
            for k in REQUIRED_INST:
                if k not in inst:
                    err("%s / %s missing '%s'" % (code, inst.get("name", "?"), k))
            if inst["id"] in seen_ids:
                err("%s duplicate institution id %s" % (code, inst["id"]))
            seen_ids.add(inst["id"])

            x, y = geo.project(inst["lat"], inst["lon"], code)
            pad = 6
            if not (bbox[0] - pad <= x <= bbox[2] + pad and bbox[1] - pad <= y <= bbox[3] + pad):
                err("%s / %s projects to (%.1f, %.1f), outside the state bbox %s"
                    % (code, inst["name"], x, y, bbox))

            adm = inst.get("admissions")
            if adm is None:
                warn("%s / %s has no admissions block" % (code, inst["name"]))
            else:
                check_gpa("%s / %s" % (code, inst["name"]), adm.get("gpa_min"))
            for p in inst["programs"]:
                if p.get("admissions"):
                    check_gpa("%s / %s / %s" % (code, inst["name"], p["name"]),
                              p["admissions"].get("gpa_min"))

            names = [p["name"] for p in inst["programs"]]
            if len(names) != len(set(names)):
                err("%s / %s has duplicate program names" % (code, inst["name"]))
            for p in inst["programs"]:
                if p.get("family") not in FAMILY_KEYS:
                    err("%s / %s / %s has unknown family '%s'"
                        % (code, inst["name"], p["name"], p.get("family")))
            total += len(names)

            if not inst.get("program_list_complete", False):
                warn("%s / %s program list is marked incomplete; its total is a floor"
                     % (code, inst["name"]))

        print("        %d institutions, %d programs" % (len(pack.get("institutions", [])), total))
        if not pack.get("sources"):
            warn("%s has no sources block" % code)

    check_faculty(geo)

    print("[check] %d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


PHYS = {"yes", "joint", "no"}
REQUIRED_FAC = ["name", "university", "state", "department", "physics_dept", "fit", "page", "papers"]


def check_faculty(geo):
    """Faculty lens files: required fields, fit range, state codes, URLs, and that any
    inst_id actually exists in that state's pack."""
    d = Config.FACULTY_DIR
    if not os.path.isdir(d):
        return
    for fname in sorted(f for f in os.listdir(d) if f.endswith(".json")):
        with open(os.path.join(d, fname), encoding="utf-8") as fh:
            doc = json.load(fh)
        print("  lens  %s" % fname)
        if doc.get("schema") != "gradfinder.faculty_lens/1":
            err("%s: unexpected schema %r" % (fname, doc.get("schema")))
        seen = set()
        npapers = 0
        for f in doc.get("faculty", []):
            who = "%s / %s" % (fname, f.get("name"))
            for k in REQUIRED_FAC:
                if k not in f:
                    err("%s missing %s" % (who, k))
            if f.get("name") in seen:
                err("%s duplicated" % who)
            seen.add(f.get("name"))
            if f.get("state") not in geo.state_codes:
                err("%s has unknown state %r" % (who, f.get("state")))
            if f.get("physics_dept") not in PHYS:
                err("%s physics_dept must be one of %s" % (who, sorted(PHYS)))
            if not isinstance(f.get("fit"), int) or not 1 <= f["fit"] <= 5:
                err("%s fit must be an integer 1-5" % who)
            if not str(f.get("page", "")).startswith("http"):
                err("%s page is not a URL" % who)
            iid = f.get("inst_id")
            if iid:
                ppath = os.path.join(Config.INSTITUTIONS_DIR, "%s.json" % f["state"])
                ids = set()
                if os.path.exists(ppath):
                    with open(ppath, encoding="utf-8") as ph:
                        ids = {i["id"] for i in json.load(ph).get("institutions", [])}
                if iid not in ids:
                    err("%s inst_id %r not in %s pack" % (who, iid, f["state"]))
            for p in f.get("papers", []):
                npapers += 1
                if not str(p.get("url", "")).startswith("http"):
                    err("%s paper %r has no URL" % (who, p.get("title")))
            if f.get("note") and "not verified" in f["note"].lower():
                warn("%s affiliation not verified" % who)
        print("        %d faculty, %d papers" % (len(seen), npapers))


if __name__ == "__main__":
    sys.exit(main())
