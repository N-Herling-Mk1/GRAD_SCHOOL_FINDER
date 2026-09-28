# GRADFINDER mk3

Live site: https://n-herling-mk1.github.io/GRAD_SCHOOL_FINDER/

Console for finding graduate programs by state. Developed as a Flask app, published as a
**static site** on GitHub Pages (see *Publish*). Stage C front end on a
stage D skeleton: real app factory, blueprints, service layer, JSON API. The map,
the tokens and the click-to-zoom behaviour carry over from `slp_finder_mk1`.

Four states have packs: AZ, CA, CO, NM. Everything else is an outline.

## Run

    python tools/build_geo.py     # only if gradfinder/static/geo/us_states.json is missing
    python tools/check_data.py    # validates every pack; non-zero exit on error
    python app.py                 # http://127.0.0.1:5057/

or `.\run.ps1` on Windows, which does all three. `Unblock-File .\run.ps1` first if it
came out of a zip.

## Publish (static site, no backend)

The Flask server only reads JSON files, so the whole site can be frozen:

    python tools/export_static.py        # writes site/ (gitignored)
    python -m http.server 8080 -d site   # preview exactly what Pages serves

or `.\export.ps1`, which validates, exports and previews in one go.

`export_static.py` runs the real app through Flask's test client, writes every API
response to `site/api/*.json`, renders `index.html` / `method.html` with relative URLs,
and sets `window.GF_STATIC = true` so `static/js/api.js` reads the JSON files instead
of `/api/v1`. Family filtering moves to the browser in static mode (`filterFamily` in
`api.js` mirrors `Store.detail` — keep the two in step).

Deploy is automatic: `.github/workflows/pages.yml` validates, exports and publishes on
every push to `main`. One-time setup: **Settings → Pages → Source: GitHub Actions**.

Workflow: edit data or code → `python app.py` to develop → `.\export.ps1` to check the
static build → commit and push → Pages updates in about a minute.

## Layout

    app.py                      dev entry point
    export.ps1                  validate + export + local preview
    .github/workflows/pages.yml build and deploy to Pages on push
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
      export_static.py          freeze the app into site/ for GitHub Pages
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
    GET /api/v1/faculty                      faculty-lens rollup per state + map sites + totals
    GET /downloads/<file>                    search-material files (xlsx, csv, json)
    GET /api/v1/faculty/TN                   faculty lens for one state, grouped by university

## Adding a state

Copy `data/institutions/AZ.json`, change `state`, `state_name` and the contents, run
`python tools/check_data.py`, reload the page. Hot reload is on by default, so no
restart. The validator projects every institution's lat/lon and fails if it lands
outside that state's own bounding box, which catches transposed coordinates.

## Layout of the page

Left rail: brand, Map / Method links, pack coverage, map metric, program family, layers,
and the **search material** block (seed paper, totals, the 28 universities ranked by best
fit, downloads). Centre: the map. Right: the state panel.

## Faculty sites on the map

Every university the paper trace reached is a **lime diamond** (the logo's centre dot).
Size = faculty found there, brightness = best fit (1-5). Hover for the top three names;
click — or click it in the left-rail list — to open that state and jump to the
university's block in the faculty lens. The *Faculty sites on map* layer chip toggles
them. Coordinates live in the `universities` block of `data/faculty/topdown_mk1.json`
and `check_data.py` fails any that project outside their state.

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
**88 papers → 59 faculty → 28 universities in 18 states**. Each faculty member carries a
hand-assigned fit (1-5) and whether they sit in a Physics department.

The lens shows for every state, including those without a pack, and inside an
institution's card when the faculty member maps to it. **Its counts are not comparable
between states**: Arizona was swept department by department, everywhere else only
through papers. Method, fields and caveats: `docs/TOPDOWN.md`. Data:
`data/faculty/topdown_mk1.json` (validated by `tools/check_data.py`), plus the same data
as `grad_vetting_topdown_mk1.xlsx`.
