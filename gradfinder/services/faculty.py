"""
Faculty lens. A second, independent layer on top of the state packs: faculty found
top-down (paper -> senior author -> current university), not by enumerating programs.
Read-only; data/faculty/*.json is the source of truth.
"""

import json
import os
from collections import defaultdict

STRONG_FIT = 4


class FacultyLens:
    def __init__(self, faculty_dir, hot_reload=True):
        self.dir = faculty_dir
        self.hot_reload = hot_reload
        self._docs = {}
        self._mtimes = {}
        self._reload(verbose=True)

    def _reload(self, verbose=False):
        if not os.path.isdir(self.dir):
            return
        for fname in sorted(os.listdir(self.dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self.dir, fname)
            mtime = os.path.getmtime(path)
            if self._mtimes.get(fname) == mtime:
                continue
            with open(path, "r", encoding="utf-8") as fh:
                self._docs[fname] = json.load(fh)
            self._mtimes[fname] = mtime
            if verbose:
                d = self._docs[fname]
                print("  [lens]  %s  %d faculty" % (d.get("name", fname), len(d.get("faculty", []))))

    def _all(self):
        if self.hot_reload:
            self._reload()
        out = []
        for d in self._docs.values():
            for f in d.get("faculty", []):
                rec = dict(f)
                rec["lens"] = d.get("name")
                out.append(rec)
        return out

    @property
    def meta(self):
        if self.hot_reload:
            self._reload()
        return [{k: d.get(k) for k in ("name", "generated", "seed", "provenance")} for d in self._docs.values()]

    def rollups(self):
        by = defaultdict(list)
        for f in self._all():
            by[f["state"]].append(f)
        out = {}
        for st, fl in by.items():
            out[st] = {
                "faculty": len(fl),
                "physics": sum(1 for f in fl if f["physics_dept"] == "yes"),
                "joint": sum(1 for f in fl if f["physics_dept"] == "joint"),
                "strong": sum(1 for f in fl if f["fit"] >= STRONG_FIT),
                "best_fit": max(f["fit"] for f in fl),
                "universities": len({f["university"] for f in fl}),
                "papers": sum(len(f.get("papers", [])) for f in fl),
            }
        return out

    def attach(self, index_doc):
        """Merge per-state lens rollups into the /states index."""
        roll = self.rollups()
        for code, row in index_doc["states"].items():
            row["lens"] = roll.get(code)
        index_doc["lens_max_strong"] = max([r["strong"] for r in roll.values()] or [0])
        return index_doc

    def state(self, code):
        code = code.upper()
        fl = [f for f in self._all() if f["state"] == code]
        unis = defaultdict(list)
        for f in fl:
            unis[f["university"]].append(f)
        rows = []
        for name, members in unis.items():
            members.sort(key=lambda f: (-f["fit"], f["name"]))
            rows.append({
                "university": name,
                "inst_id": members[0].get("inst_id"),
                "best_fit": members[0]["fit"],
                "physics": sum(1 for f in members if f["physics_dept"] == "yes"),
                "faculty": members,
            })
        rows.sort(key=lambda r: (-r["best_fit"], -r["physics"], r["university"]))
        return {"state": code, "universities": rows, "rollup": self.rollups().get(code), "meta": self.meta}
