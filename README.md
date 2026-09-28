# GRADFINDER mk1

Local Flask console for finding graduate programs by state. Stage C front end on a
stage D skeleton: real app factory, blueprints, service layer, JSON API. The map,
the tokens and the click-to-zoom behaviour carry over from `slp_finder_mk1`.

Four states have packs: AZ, CA, CO, NM. Everything else is an outline.

## Run

    python tools/build_geo.py     # only if gradfinder/static/geo/us_states.json is missing
    python tools/check_data.py    # validates every pack; non-zero exit on error
    python app.py                 # http://127.0.0.1:5057/

or `.\run.ps1` on Windows, which does all three. `Unblock-File .\run.ps1` first if it
came out of a zip.

## Layout

    app.py                      dev entry point
    config.py                   paths, port, family taxonomy
    gradfinder/
      __init__.py               create_app factory + boot banner
      routes/views.py           HTML routes
      routes/api.py             /api/v1
      services/albers.py        Albers USA composite, shared by build and runtime
      services/geo.py           geometry + point projection
      services/store.py         pack loading, rollups, filtering
      services/faculty.py       faculty lens loading and rollups
      templates/                base, index, method
      static/css/               tokens (TRON Ares), layout, map, panel
      static/js/                api, map, panel, app
      static/geo/us_states.json built artifact, do not hand-edit
      static/favicon.ico        site icon (16-256 px); img/ holds the logo, PNG favicons, apple-touch icon
    data/
      institutions/*.json       the state packs (AZ, CA, CO, NM)
      faculty/*.json            faculty lens (top-down, paper -> PI -> university)
      derived/projection.json   built artifact
    tools/
      build_geo.py              GeoJSON -> projected SVG paths
      check_data.py             pack validator
      seed_packs.py             one-shot seeder for the CA/CO/NM packs

## API

    GET /api/v1/health
    GET /api/v1/meta
    GET /api/v1/geo
    GET /api/v1/states                       rollup for all 51 jurisdictions
    GET /api/v1/states/AZ                    full pack + projected marker coords
    GET /api/v1/states/AZ?family=engineering filter to one family
    GET /api/v1/states/AZ?boundary=0         drop boundary-status institutions
    GET /api/v1/faculty                      faculty-lens rollup per state
    GET /api/v1/faculty/TN                   faculty lens for one state, grouped by university

## Adding a state

Copy `data/institutions/AZ.json`, change `state`, `state_name` and the contents, run
`python tools/check_data.py`, reload the page. Hot reload is on by default, so no
restart. The validator projects every institution's lat/lon and fails if it lands
outside that state's own bounding box, which catches transposed coordinates.

## Map controls

- wheel zooms at the cursor, drag pans, double click zooms in
- shift+drag draws a box zoom; right click gives the same as a menu item, plus zoom
  in/out at that point, zoom to the state under the cursor, and reset
- Esc resets the view
- neighbouring states keep their outlines while one state is selected; only the fill recedes

## What the numbers are

Two metrics, switched in the filter bar:

- **Institutions** (default) — institutions in scope. Comparable between states,
  because enumerating institutions is a bounded job and the rosters are believed complete.
- **Programs on file** — programs recorded in the pack. **Not** comparable between
  states. It measures how deeply I typed, not how much a state offers. California's
  lists are shallower relative to its size than Arizona's, so California's floor is
  looser than Arizona's.

Nothing here is IPEDS-joined. Program links go to a site-scoped search on the
institution's domain, not to a verified program page — see docs/NEXT.md.

## Admissions / GPA fields

`admissions.gpa_min` is a record, not a number:
`{value, scale, basis, scope, type, waiver, source_url, as_of}`. `type` is one of
`floor`, `recommended`, `reported typical`, and `check_data.py` rejects a value that
arrives without scope, basis, type and a source URL.

Only UArizona is populated, from its Graduate College pages. Every other institution
reads "not collected" — an empty field and a known 3.0 must not look the same.

## Known gaps

- Nothing is scraped. Every record was typed by hand, so there is no audit trail and no
  error rate. docs/NEXT.md has the scrape-and-vet design that replaces it.
- No IPEDS HD / Completions join. UNITIDs are null.
- One marker per institution, at the flagship campus. ASU's four campuses collapse to Tempe.
- No funding, deadline, advisor or admissions fields. Those are L3/L4.
- Cross-state comparison is not defensible until more than one pack exists.

---

## Footnote — the faculty lens (top-down vetting)

<sup>1</sup> Everything above is **bottom-up**: institutions, then programs. The
**Faculty lens** chip adds a second, independent layer built **top-down**: start from the
phonon paper reproduced in FORGE — Chen, Andrejevic, Smidt, …, M. Li, *Direct Prediction
of Phonon Density of States With Euclidean Neural Networks*, Adv. Sci. 8, 2004214 (2021),
https://doi.org/10.1002/advs.202004214 — trace citing and related papers to their senior
authors, then to those authors' current universities. Three sweeps (citation lineage,
Bayesian-UQ + ML-for-CMP, a University of Arizona department sweep) produced
**88 papers → 59 faculty → 25 universities in 18 states**. Each faculty member carries a
hand-assigned fit (1-5) and whether they sit in a Physics department.

The lens shows for every state, including those without a pack, and inside an
institution's card when the faculty member maps to it. **Its counts are not comparable
between states**: Arizona was swept department by department, everywhere else only
through papers. Method, fields and caveats: `docs/TOPDOWN.md`. Data:
`data/faculty/topdown_mk1.json` (validated by `tools/check_data.py`), plus the same data
as `grad_vetting_topdown_mk1.xlsx`.
