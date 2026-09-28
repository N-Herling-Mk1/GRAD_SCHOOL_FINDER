# Open decisions and the next build

## 1. Scraping, and how the vetting layer should work

Everything in `data/institutions/*.json` today was typed by hand from graduate
catalogues. Four states took one session; fifty will not, and hand-typing has no
audit trail — you cannot tell my typo from a real program.

Scraping is agreed. The design question is not "how do we scrape" but "what makes a
scraped record trustworthy". Proposal, for discussion before any code:

**Two independent sources, then reconcile.**

| layer | source | what it gives | trust |
|---|---|---|---|
| L0 roster | IPEDS HD bulk file | every Title-IV institution, location, control, Carnegie, UNITID | federal, authoritative, no scraping |
| L1 conferred | IPEDS Completions, award level 17 | doctorates **actually conferred** by CIP code, per year | federal, lagging 1-2 years |
| L2 offered | scrape each institution's catalogue | programs **currently advertised**, plus the real program URL | current, unverified |

L1 and L2 answer different questions, which is exactly why both are worth having.
Cross-referencing them gives a per-program verdict rather than a yes/no:

- **confirmed** — catalogue advertises it and the institution has conferred doctorates
  in that CIP in the last three years. Highest confidence.
- **claimed only** — catalogue advertises it, no recent completions. Either new, tiny,
  or dormant. NAU's civil and environmental engineering doctorate, listed but not
  accepting students, is this case; so is any program that quietly stopped admitting.
  This is the single most useful flag in the whole system and neither source produces
  it alone.
- **conferred only** — completions exist, the scraper found no page. Scraper miss, a
  renamed program, or a program that lives under a school-level umbrella. Feeds the
  scraper's own error rate.

**Rules the scraper has to follow to be worth trusting:**

- Store the fetch, not just the parse. Raw HTML, URL, HTTP date, and a content hash
  per page, so any claim can be re-derived and a re-run can diff against it.
- One fetch per page per run, rate limited, honouring robots.txt. Institutional sites
  are not hostile targets and there is no reason to behave like one.
- Never let the parser invent. A field the page did not state is null, not a guess.
- Every disagreement between L1 and L2 goes to a review queue, not to a default. The
  queue is the vetting work; the point of the design is to make that queue small.
- Track the scraper's own accuracy: hand-verify a random sample per run and record the
  hit rate, so "the scrape says 34 programs" carries an error bar.

**Open**: whether to keep CIP as the join key (the honest option, but CIP-to-catalogue
matching is fuzzy) or to match on program title (easy, and wrong in both directions).

## 1b. Scraping minimum GPA

Yes, it is scrapeable, and it is a harder target than program existence. There is no
federal source: IPEDS carries no graduate admission data and the Common Data Set covers
undergraduate admissions only. Every value has to come off an institution's own pages,
which means the vetting rules above matter more here, not less.

The reason a bare number cannot be stored: UArizona currently states all three of these
at once.

| value | scope | type | what it means |
|---|---|---|---|
| 3.00 | institution | floor | Graduate College minimum, waivable by departmental memo |
| 3.50 | program | floor | civil engineering PhD, graduate coursework during the MS |
| 3.70 | program | reported typical | speech and hearing, explicitly stated NOT to be a criterion |

Store a number without its scope and type and you get a tool that tells you the GPA
requirement for a UArizona PhD is 3.7. So the field is a record, not a number:
`{value, scale, basis, scope, type, waiver, source_url, as_of}`. `basis` matters too —
cumulative, last 60 units, major, or graduate coursework are different denominators and
UArizona alone calculates from at least five.

**Where to scrape, in order:**
1. Graduate school admission requirements page -> the institution-wide floor. One page
   per institution, high yield, stable wording, easy to parse.
2. Department or program admissions page -> program floors and reported typicals. Many
   pages, inconsistent wording, and the place where the "typical admit" trap lives.
3. Program handbook PDFs -> often the only place a real floor is written down.

**Parse rules that keep it honest:**
- Capture the sentence the number came from, verbatim, alongside the value. If a human
  ever has to adjudicate, the quote settles it in seconds.
- Classify on the surrounding language, not the number. "must have", "minimum",
  "required" -> floor. "prefer", "competitive applicants" -> recommended. "average
  admitted", "typical", "recent cohorts" -> reported typical. Anything unclassifiable
  goes to review, never to a default.
- No value means empty, never the common 3.0. The packs currently read "not collected"
  for every institution except UArizona, and the panel says so in words.
- Re-read annually with the fetch date stored; a floor from four years ago is a rumour.

**Worth saying plainly:** for your record, the institution-wide floor will almost never
be the binding constraint. Its use is negative screening and spotting the programs that
sit above it, like that 3.5. If the choice is between building GPA collection and
building funding, deadline, or advisor collection, GPA is the least decision-relevant of
the four.

## 2. Still blocking a clean cross-state comparison

- **Award-level codes** (SCOPE.csv SC04) still `<TBD>`. The working rule is research
  doctorates only, professional practice excluded. Write it down.
- **CIP codes** (SC05) still `<TBD>`. The nine families in `config.py` are mine, not CIP.
- **Psychology** is tagged `psych_research` and sits outside the strict rule. Decide once.
- **Joint doctorates.** CSU/UC joint PhDs are counted at the CSU campus only. Flip that
  convention and counts move between institutions.

## 3. Program URLs

The panel links each program name to a site-scoped search on the institution's own
domain, because the packs carry no verified program URLs. That is deliberate —
constructing plausible department URLs would produce links that look authoritative and
404. The L2 scrape above is what fills the real `url` field, and once it does, those
rows become direct links automatically.

## 4. UI, deferred

- Cross-state program search (worth building once packs are machine-generated).
- Compare tray: pin two or three institutions side by side.
- `/institution/<id>` route so a school is linkable.
- Marker labels are suppressed on collision and revealed on hover. Fine at four states;
  revisit if a metro ever holds more than about a dozen institutions.
