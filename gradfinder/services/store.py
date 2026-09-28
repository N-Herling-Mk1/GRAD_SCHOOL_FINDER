"""
Data access. Reads the per-state institution packs off disk and answers the
questions the API asks. Nothing here writes; the packs are the source of truth.
"""

import json
import os
import time
from collections import Counter

from config import FAMILIES

FAMILY_KEYS = [f["key"] for f in FAMILIES]
STEM_CORE = {"physical_sci", "math_stat", "comp_info", "engineering",
             "bio_sci", "geo_env", "agri"}


class Store:
    def __init__(self, institutions_dir, geo, hot_reload=True):
        self.dir = institutions_dir
        self.geo = geo
        self.hot_reload = hot_reload
        self._packs = {}
        self._mtimes = {}
        self.load_all(verbose=True)

    # ---------------------------------------------------------------- loading
    def _pack_path(self, code):
        return os.path.join(self.dir, "%s.json" % code.upper())

    def load_all(self, verbose=False):
        t0 = time.time()
        found = sorted(f for f in os.listdir(self.dir) if f.endswith(".json"))
        for i, fname in enumerate(found, 1):
            code = os.path.splitext(fname)[0].upper()
            self._load(code)
            if verbose:
                n = len(self._packs[code]["institutions"])
                print("  [store] %d/%d  %s  %d institutions" % (i, len(found), code, n))
        if verbose:
            print("  [store] %d state pack(s) in %.0f ms" % (len(found), 1000 * (time.time() - t0)))

    def _load(self, code):
        path = self._pack_path(code)
        if not os.path.exists(path):
            return None
        mtime = os.path.getmtime(path)
        if code in self._packs and self._mtimes.get(code) == mtime:
            return self._packs[code]
        with open(path, "r", encoding="utf-8") as fh:
            pack = json.load(fh)
        for inst in pack.get("institutions", []):
            inst["xy"] = self.geo.project(inst["lat"], inst["lon"], code)
            inst["program_count"] = len(inst.get("programs", []))
            inst["families"] = sorted({p["family"] for p in inst.get("programs", [])})
        self._packs[code] = pack
        self._mtimes[code] = mtime
        return pack

    def pack(self, code):
        code = code.upper()
        if self.hot_reload:
            return self._load(code)
        return self._packs.get(code)

    @property
    def loaded_codes(self):
        return sorted(self._packs.keys())

    # --------------------------------------------------------------- rollups
    def rollup(self, code):
        """Per-state summary used by the choropleth and the panel header."""
        pack = self.pack(code)
        if not pack:
            return {
                "state": code,
                "name": self.geo.name_of(code),
                "status": "empty",
                "stage": None,
                "institutions": 0,
                "institutions_in_scope": 0,
                "programs": 0,
                "stem_core_programs": 0,
                "excluded": 0,
                "by_family": {k: 0 for k in FAMILY_KEYS},
                "by_family_institutions": {k: 0 for k in FAMILY_KEYS},
            }
        insts = pack.get("institutions", [])
        fam = Counter()
        fam_inst = Counter()
        for inst in insts:
            here = set()
            for p in inst.get("programs", []):
                fam[p["family"]] += 1
                here.add(p["family"])
            for k in here:
                fam_inst[k] += 1
        return {
            "state": code,
            "name": pack.get("state_name", self.geo.name_of(code)),
            "status": "loaded",
            "stage": pack.get("stage"),
            "generated": pack.get("generated"),
            "institutions": len(insts),
            "institutions_in_scope": sum(1 for i in insts if i.get("status") == "in"),
            "programs": sum(i["program_count"] for i in insts),
            "stem_core_programs": sum(v for k, v in fam.items() if k in STEM_CORE),
            "excluded": len(pack.get("excluded", [])),
            "by_family": {k: fam.get(k, 0) for k in FAMILY_KEYS},
            "by_family_institutions": {k: fam_inst.get(k, 0) for k in FAMILY_KEYS},
        }

    def index(self):
        """Rollup for every jurisdiction on the map, loaded or not."""
        rows = {code: self.rollup(code) for code in self.geo.state_codes}
        counts = [r["programs"] for r in rows.values()]
        return {
            "states": rows,
            "max_programs": max(counts) if counts else 0,
            "loaded": self.loaded_codes,
            "coverage": "%d/%d" % (len(self.loaded_codes), len(self.geo.state_codes)),
        }

    def detail(self, code, family=None, include_boundary=True):
        pack = self.pack(code)
        if not pack:
            return None
        out = dict(pack)
        insts = []
        for inst in pack.get("institutions", []):
            if not include_boundary and inst.get("status") == "boundary":
                continue
            rec = dict(inst)
            if family:
                rec["programs"] = [p for p in inst.get("programs", []) if p["family"] == family]
                rec["program_count"] = len(rec["programs"])
                if not rec["programs"]:
                    continue
            insts.append(rec)
        insts.sort(key=lambda r: (-r["program_count"], r["name"]))
        out["institutions"] = insts
        out["rollup"] = self.rollup(code)
        out["filter"] = {"family": family, "include_boundary": include_boundary}
        return out
