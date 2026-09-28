# Faculty lens — top-down vetting (topdown_mk1, 2026-09-27)

The state packs work bottom-up: enumerate institutions, then their programs. This layer
runs the other direction: **start from papers, trace each to its senior author, then to
that author's current university.** It answers "who is doing work I'd actually join?",
which a program list can't.

## Seed

Z. Chen, N. Andrejevic, T. Smidt, Z. Ding, Q. Xu, Y.-T. Chi, Q. T. Nguyen, A. Alatas,
J. Kong, M. Li, *Direct Prediction of Phonon Density of States With Euclidean Neural
Networks*, Advanced Science 8, 2004214 (2021) — https://doi.org/10.1002/advs.202004214

Reproduced as the phonon DOS experiment in FORGE (INFO 698). Target: a condensed-matter
physics PhD, with strength in ML and Bayesian uncertainty.

## Sweeps

| sweep key | what it covered | result |
|---|---|---|
| `phonon-lineage` | papers citing the seed + sideways (phonon ML, equivariant NNs, scattering ML, thermal transport) | 36 papers, 21 PIs |
| `bayes-cmp` | Bayesian UQ / GP / Bayesian optimisation in CMP and materials; ML-for-CMP out of physics departments | 25 papers, 21 PIs |
| `ua` | University of Arizona, department by department | 24 papers, 13 PIs |

Rules: US university faculty only (national-lab and foreign senior authors dropped);
2025-26 affiliation checked on a faculty page; no paper kept without a real DOI/arXiv link.

## Fields

- **fit (1-5)** — hand-assigned. 5 = direct overlap with phonon ML or Bayesian UQ *and*
  can advise a condensed-matter Physics PhD. Edit freely; the map and panel follow.
- **physics_dept** — `yes` primary Physics/Applied Physics; `joint` joint appointment or
  listed in a physics grad program (confirm sole advising); `no` other department.
- **inst_id** — links the faculty member to a state-pack institution when one exists
  (AZ, CA today); drives the "Faculty lens" line inside that institution's card.

## Read with care

- **Not comparable between states.** Arizona got a full department sweep; every other state
  entered only through papers. Map colour = count of fit >= 4 faculty; compare on best fit.
  Averaged per faculty, AZ (2.9) sits below FL (3.7), TN (3.6), NY (3.5), MIT (3.3).
- Not exhaustive: each sweep stopped at ~25-36 papers.
- Open flags: Gull (Michigan) lab relocating to Warsaw; Gomez-Bombarelli possible leave;
  Transtrum left BYU; Shuiwang Ji unverified; Biswas partial.
- Recruiting status is only what a faculty page says.

## Files

    data/faculty/topdown_mk1.json               source of truth (schema gradfinder.faculty_lens/1)
    data/faculty/grad_vetting_topdown_mk1.xlsx  same data as a workbook (papers / faculty / universities)
    data/faculty/gradfinder_universities_mk1.csv university roll-up

## Next

Give the top schools (UTK, MIT, Cornell, UF, UIUC) the same full Physics-department
sweep Arizona got, so the counts become comparable. Add a second seed (FORGE's Bayesian
last-layer Laplace / HMC work) to widen the paper trace.
