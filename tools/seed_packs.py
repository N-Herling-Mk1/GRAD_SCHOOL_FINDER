#!/usr/bin/env python3
"""
seed_packs.py -- emit the CA / CO / NM state packs.

This exists so the three packs share one shape and one set of caveats. It is a
one-shot seeder, not a pipeline stage: everything in here was typed by hand from
institutional graduate catalogues, and stage B replaces all of it from IPEDS.

Run:  python tools/seed_packs.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "institutions")

P = "physical_sci"; M = "math_stat"; C = "comp_info"; E = "engineering"
B = "bio_sci"; G = "geo_env"; A = "agri"; H = "biomed_health"; Y = "psych_research"

NOTE = ("Counts are programs recorded in this pack, not programs offered. Lists are "
        "representative floors typed from graduate catalogues; no IPEDS join has run. "
        "Use the institution count, not the program count, to compare states.")


def inst(id, name, short, city, lat, lon, control, carnegie, domain, website,
         programs, status="in", confidence="medium", complete=False, notes=""):
    return {
        "id": id, "name": name, "short": short, "city": city,
        "lat": lat, "lon": lon, "control": control, "carnegie": carnegie,
        "ipeds_unitid": None, "domain": domain, "website": website,
        "status": status, "confidence": confidence,
        "program_list_complete": complete, "notes": notes,
        "programs": [{"name": n, "family": f, "award": "PhD"} for n, f in programs],
    }


# ------------------------------------------------------------------ NEW MEXICO
NM = [
    inst("nm-unm", "University of New Mexico", "UNM", "Albuquerque", 35.0843, -106.6198,
         "public", "R1", "unm.edu", "https://grad.unm.edu/", [
             ("Physics", P), ("Astronomy", P), ("Chemistry", P), ("Mathematics", M),
             ("Statistics", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical Engineering", E),
             ("Civil Engineering", E), ("Chemical Engineering", E),
             ("Nanoscience and Microsystems Engineering", E),
             ("Optical Science and Engineering", P), ("Biomedical Engineering", E),
             ("Nuclear Engineering", E), ("Biology", B), ("Biomedical Sciences", H),
             ("Earth and Planetary Sciences", G), ("Psychology", Y),
         ], confidence="medium",
         notes="Flagship. Optical Science and Engineering and the Nanoscience program "
               "run alongside Sandia and the Air Force Research Laboratory."),
    inst("nm-nmsu", "New Mexico State University", "NMSU", "Las Cruces", 32.2803, -106.7489,
         "public", "R2", "nmsu.edu", "https://gradschool.nmsu.edu/", [
             ("Physics", P), ("Astronomy", P), ("Chemistry", P), ("Mathematics", M),
             ("Computer Science", C), ("Electrical and Computer Engineering", E),
             ("Mechanical and Aerospace Engineering", E), ("Civil Engineering", E),
             ("Chemical Engineering", E), ("Industrial Engineering", E),
             ("Biology", B), ("Molecular Biology", B),
             ("Plant and Environmental Sciences", A), ("Animal and Range Sciences", A),
             ("Water Science and Management", G), ("Psychology", Y),
         ]),
    inst("nm-nmt", "New Mexico Institute of Mining and Technology", "NM Tech", "Socorro",
         34.0653, -106.9067, "public", "special focus, STEM", "nmt.edu", "https://www.nmt.edu/", [
             ("Earth and Environmental Science", G), ("Hydrology", G),
             ("Materials Engineering", E), ("Mechanical Engineering", E),
             ("Explosives Engineering", E), ("Physics", P), ("Chemistry", P),
         ], confidence="low",
         notes="Small STEM-only institute. The explosives engineering doctorate is "
               "close to unique in the US. Program list is the least verified in this pack."),
]

NM_EXCL = [
    {"name": "New Mexico Highlands University", "city": "Las Vegas", "reason": "master's-level; no research doctorate"},
    {"name": "Eastern New Mexico University", "city": "Portales", "reason": "master's-level; no research doctorate"},
    {"name": "Los Alamos National Laboratory", "city": "Los Alamos", "reason": "not degree-granting; students enrol through partner universities"},
    {"name": "Sandia National Laboratories", "city": "Albuquerque", "reason": "not degree-granting"},
]

# -------------------------------------------------------------------- COLORADO
CO = [
    inst("co-cuboulder", "University of Colorado Boulder", "CU Boulder", "Boulder",
         40.0076, -105.2659, "public", "R1", "colorado.edu", "https://www.colorado.edu/graduateschool/", [
             ("Physics", P), ("Astrophysical and Planetary Sciences", P), ("Chemistry", P),
             ("Biochemistry", P), ("Mathematics", M), ("Applied Mathematics", M),
             ("Computer Science", C), ("Aerospace Engineering Sciences", E),
             ("Electrical Engineering", E), ("Mechanical Engineering", E),
             ("Civil, Environmental and Architectural Engineering", E),
             ("Chemical and Biological Engineering", E), ("Materials Science and Engineering", E),
             ("Molecular, Cellular and Developmental Biology", B),
             ("Ecology and Evolutionary Biology", B), ("Neuroscience", B),
             ("Geological Sciences", G), ("Atmospheric and Oceanic Sciences", G),
             ("Environmental Studies", G), ("Psychology and Neuroscience", Y),
         ], confidence="high",
         notes="JILA and the NIST partnership sit here; the AMO physics group is the "
               "strongest single reason to look at Boulder for condensed matter or quantum."),
    inst("co-csu", "Colorado State University", "CSU", "Fort Collins", 40.5734, -105.0865,
         "public", "R1", "colostate.edu", "https://graduateschool.colostate.edu/", [
             ("Physics", P), ("Chemistry", P), ("Mathematics", M), ("Statistics", M),
             ("Computer Science", C), ("Electrical and Computer Engineering", E),
             ("Mechanical Engineering", E), ("Civil and Environmental Engineering", E),
             ("Chemical and Biological Engineering", E), ("Systems Engineering", E),
             ("Biomedical Engineering", E), ("Cell and Molecular Biology", B),
             ("Ecology", B), ("Microbiology, Immunology and Pathology", H),
             ("Biomedical Sciences", H), ("Atmospheric Science", G),
             ("Soil and Crop Sciences", A), ("Animal Sciences", A),
             ("Forest and Rangeland Stewardship", A),
             ("Fish, Wildlife and Conservation Biology", B), ("Psychology", Y),
         ], confidence="high"),
    inst("co-mines", "Colorado School of Mines", "Mines", "Golden", 39.7510, -105.2220,
         "public", "special focus, engineering", "mines.edu", "https://www.mines.edu/graduate-admissions/", [
             ("Applied Physics", P), ("Chemistry", P), ("Applied Mathematics and Statistics", M),
             ("Computer Science", C), ("Electrical Engineering", E),
             ("Mechanical Engineering", E), ("Civil and Environmental Engineering", E),
             ("Chemical and Biological Engineering", E),
             ("Metallurgical and Materials Engineering", E), ("Materials Science", E),
             ("Mining Engineering", E), ("Petroleum Engineering", E),
             ("Nuclear Science and Engineering", E), ("Quantum Engineering", E),
             ("Geology and Geological Engineering", G), ("Geophysics", G),
             ("Hydrologic Science and Engineering", G),
         ], confidence="high",
         notes="Narrow and deep: earth, energy and materials. Quantum engineering is a "
               "recent addition and worth a direct look given your condensed-matter target."),
    inst("co-anschutz", "University of Colorado Anschutz Medical Campus", "CU Anschutz", "Aurora",
         39.7447, -104.8386, "public", "special focus, health", "cuanschutz.edu",
         "https://graduateschool.cuanschutz.edu/", [
             ("Biomedical Sciences", H), ("Cancer Biology", H), ("Immunology", H),
             ("Microbiology", H), ("Neuroscience", B), ("Pharmacology", H),
             ("Structural Biology and Biochemistry", H),
             ("Human Medical Genetics and Genomics", H), ("Computational Bioscience", C),
             ("Bioengineering", E),
         ]),
    inst("co-cudenver", "University of Colorado Denver", "CU Denver", "Denver",
         39.7452, -105.0021, "public", "R2", "ucdenver.edu", "https://www.ucdenver.edu/graduate-school", [
             ("Computer Science and Information Systems", C), ("Applied Mathematics", M),
             ("Civil Engineering", E), ("Mechanical Engineering", E),
             ("Electrical Engineering", E), ("Bioengineering", E),
             ("Integrative Biology", B), ("Health and Behavioral Sciences", H),
         ]),
    inst("co-uccs", "University of Colorado Colorado Springs", "UCCS", "Colorado Springs",
         38.8930, -104.8003, "public", "R2", "uccs.edu", "https://graduateschool.uccs.edu/", [
             ("Engineering", E), ("Computer Science", C), ("Applied Science", P),
             ("Psychology", Y),
         ], confidence="low",
         notes="Doctoral catalogue is small and several plans are expressed as one "
               "umbrella degree with concentrations. Counts here are soft."),
    inst("co-du", "University of Denver", "DU", "Denver", 39.6766, -104.9619,
         "private nonprofit", "R1", "du.edu", "https://www.du.edu/academics/graduate", [
             ("Physics and Astronomy", P), ("Chemistry and Biochemistry", P),
             ("Mathematics", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical Engineering", E),
             ("Materials Science", E), ("Biological Sciences", B), ("Psychology", Y),
         ]),
    inst("co-unco", "University of Northern Colorado", "UNC", "Greeley", 40.4041, -104.6975,
         "public", "doctoral, professional", "unco.edu", "https://www.unco.edu/graduate-school/", [
             ("Biological Education", B), ("Chemical Education", P),
             ("Educational Mathematics", M), ("School Psychology", Y),
         ], status="boundary", confidence="low",
         notes="Doctorates here are discipline-education plans rather than research "
               "doctorates in the discipline. Boundary by the scope rule."),
]

CO_EXCL = [
    {"name": "Colorado State University Pueblo", "city": "Pueblo", "reason": "master's-level; no research doctorate"},
    {"name": "Regis University", "city": "Denver", "reason": "professional doctorates (DNP, EdD, PsyD) only"},
    {"name": "National Renewable Energy Laboratory", "city": "Golden", "reason": "not degree-granting; students enrol through CU, CSU or Mines"},
    {"name": "United States Air Force Academy", "city": "Colorado Springs", "reason": "undergraduate only"},
]

# ------------------------------------------------------------------ CALIFORNIA
CA = [
    inst("ca-berkeley", "University of California, Berkeley", "UC Berkeley", "Berkeley",
         37.8719, -122.2585, "public", "R1", "berkeley.edu", "https://grad.berkeley.edu/programs/", [
             ("Physics", P), ("Chemistry", P), ("Astrophysics", P), ("Mathematics", M),
             ("Statistics", M), ("Computer Science", C),
             ("Electrical Engineering and Computer Sciences", E), ("Mechanical Engineering", E),
             ("Civil and Environmental Engineering", E), ("Chemical Engineering", E),
             ("Materials Science and Engineering", E), ("Nuclear Engineering", E),
             ("Bioengineering", E), ("Molecular and Cell Biology", B),
             ("Integrative Biology", B), ("Earth and Planetary Science", G),
             ("Environmental Science, Policy and Management", G), ("Plant Biology", A),
         ], confidence="high"),
    inst("ca-ucla", "University of California, Los Angeles", "UCLA", "Los Angeles",
         34.0689, -118.4452, "public", "R1", "ucla.edu", "https://grad.ucla.edu/programs/", [
             ("Physics", P), ("Astronomy and Astrophysics", P), ("Chemistry", P),
             ("Mathematics", M), ("Statistics", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical and Aerospace Engineering", E),
             ("Civil and Environmental Engineering", E),
             ("Chemical and Biomolecular Engineering", E), ("Materials Science and Engineering", E),
             ("Bioengineering", E), ("Molecular Biology", B), ("Neuroscience", B),
             ("Earth, Planetary and Space Sciences", G), ("Atmospheric and Oceanic Sciences", G),
             ("Biomedical Sciences", H), ("Psychology", Y),
         ], confidence="high"),
    inst("ca-ucsd", "University of California, San Diego", "UC San Diego", "La Jolla",
         32.8801, -117.2340, "public", "R1", "ucsd.edu", "https://grad.ucsd.edu/admissions/programs/", [
             ("Physics", P), ("Chemistry and Biochemistry", P), ("Mathematics", M),
             ("Computer Science and Engineering", C), ("Data Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical and Aerospace Engineering", E),
             ("Structural Engineering", E), ("NanoEngineering", E), ("Bioengineering", E),
             ("Materials Science and Engineering", E), ("Biological Sciences", B),
             ("Neurosciences", B), ("Oceanography", G), ("Earth Sciences", G),
             ("Biomedical Sciences", H), ("Cognitive Science", Y),
         ], confidence="high",
         notes="Scripps Institution of Oceanography is part of UCSD; its doctorates are counted here."),
    inst("ca-ucdavis", "University of California, Davis", "UC Davis", "Davis",
         38.5382, -121.7617, "public", "R1", "ucdavis.edu", "https://grad.ucdavis.edu/programs", [
             ("Physics", P), ("Chemistry", P), ("Mathematics", M), ("Statistics", M),
             ("Computer Science", C), ("Electrical and Computer Engineering", E),
             ("Mechanical and Aerospace Engineering", E), ("Civil and Environmental Engineering", E),
             ("Chemical Engineering", E), ("Materials Science and Engineering", E),
             ("Biomedical Engineering", E), ("Biological Systems Engineering", E),
             ("Plant Biology", A), ("Horticulture and Agronomy", A), ("Animal Biology", A),
             ("Soils and Biogeochemistry", A), ("Ecology", B), ("Microbiology", B),
             ("Geology", G), ("Atmospheric Science", G),
         ], confidence="high"),
    inst("ca-uci", "University of California, Irvine", "UC Irvine", "Irvine",
         33.6405, -117.8443, "public", "R1", "uci.edu", "https://grad.uci.edu/programs/", [
             ("Physics", P), ("Chemistry", P), ("Mathematics", M), ("Statistics", M),
             ("Computer Science", C), ("Electrical Engineering and Computer Science", E),
             ("Mechanical and Aerospace Engineering", E), ("Civil and Environmental Engineering", E),
             ("Chemical and Biomolecular Engineering", E), ("Materials Science and Engineering", E),
             ("Biomedical Engineering", E), ("Biological Sciences", B), ("Neurobiology", B),
             ("Earth System Science", G), ("Psychological Science", Y),
         ]),
    inst("ca-ucsb", "University of California, Santa Barbara", "UC Santa Barbara", "Santa Barbara",
         34.4140, -119.8489, "public", "R1", "ucsb.edu", "https://www.graddiv.ucsb.edu/academic-programs", [
             ("Physics", P), ("Chemistry and Biochemistry", P), ("Mathematics", M),
             ("Statistics and Applied Probability", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical Engineering", E),
             ("Chemical Engineering", E), ("Materials", E),
             ("Molecular, Cellular and Developmental Biology", B),
             ("Ecology, Evolution and Marine Biology", B), ("Earth Science", G),
             ("Geography", G),
         ], confidence="high",
         notes="Materials department and the KITP make this a strong condensed-matter target."),
    inst("ca-ucsc", "University of California, Santa Cruz", "UC Santa Cruz", "Santa Cruz",
         36.9914, -122.0609, "public", "R1", "ucsc.edu", "https://graddiv.ucsc.edu/programs/", [
             ("Physics", P), ("Astronomy and Astrophysics", P), ("Chemistry", P),
             ("Mathematics", M), ("Statistics", M), ("Computer Science and Engineering", C),
             ("Electrical and Computer Engineering", E), ("Biomolecular Engineering", E),
             ("Molecular, Cell and Developmental Biology", B),
             ("Ecology and Evolutionary Biology", B), ("Earth and Planetary Sciences", G),
             ("Ocean Sciences", G),
         ]),
    inst("ca-ucr", "University of California, Riverside", "UC Riverside", "Riverside",
         33.9737, -117.3281, "public", "R1", "ucr.edu", "https://graduate.ucr.edu/programs", [
             ("Physics and Astronomy", P), ("Chemistry", P), ("Mathematics", M),
             ("Statistics", M), ("Computer Science", C), ("Electrical Engineering", E),
             ("Mechanical Engineering", E), ("Chemical and Environmental Engineering", E),
             ("Materials Science and Engineering", E), ("Bioengineering", E),
             ("Plant Biology", A), ("Entomology", B), ("Environmental Sciences", G),
             ("Earth and Planetary Sciences", G),
         ]),
    inst("ca-ucmerced", "University of California, Merced", "UC Merced", "Merced",
         37.3661, -120.4237, "public", "R2", "ucmerced.edu", "https://graduatedivision.ucmerced.edu/", [
             ("Physics", P), ("Chemistry and Chemical Biology", P),
             ("Applied Mathematics", M), ("Electrical Engineering and Computer Science", C),
             ("Mechanical Engineering", E), ("Environmental Systems", G),
             ("Quantitative and Systems Biology", B),
         ]),
    inst("ca-ucsf", "University of California, San Francisco", "UCSF", "San Francisco",
         37.7632, -122.4576, "public", "special focus, health", "ucsf.edu",
         "https://graduate.ucsf.edu/phd-programs", [
             ("Biomedical Sciences", H), ("Biophysics", P), ("Bioengineering", E),
             ("Chemistry and Chemical Biology", P), ("Neuroscience", B),
             ("Pharmaceutical Sciences and Pharmacogenomics", H),
             ("Epidemiology and Translational Science", H),
         ], confidence="high",
         notes="Graduate-only health sciences campus. Bioengineering is run jointly with UC Berkeley."),
    inst("ca-stanford", "Stanford University", "Stanford", "Stanford", 37.4275, -122.1697,
         "private nonprofit", "R1", "stanford.edu", "https://gradadmissions.stanford.edu/programs", [
             ("Physics", P), ("Applied Physics", P), ("Chemistry", P), ("Mathematics", M),
             ("Statistics", M), ("Computer Science", C), ("Electrical Engineering", E),
             ("Mechanical Engineering", E), ("Aeronautics and Astronautics", E),
             ("Civil and Environmental Engineering", E), ("Chemical Engineering", E),
             ("Materials Science and Engineering", E), ("Bioengineering", E),
             ("Biology", B), ("Neurosciences", B), ("Earth System Science", G),
             ("Geophysics", G), ("Biomedical Informatics", H),
         ], confidence="high"),
    inst("ca-caltech", "California Institute of Technology", "Caltech", "Pasadena",
         34.1377, -118.1253, "private nonprofit", "R1", "caltech.edu",
         "https://www.gradoffice.caltech.edu/", [
             ("Physics", P), ("Applied Physics", P), ("Chemistry", P),
             ("Astrophysics", P), ("Planetary Science", P), ("Mathematics", M),
             ("Computing and Mathematical Sciences", C), ("Electrical Engineering", E),
             ("Mechanical Engineering", E), ("Aerospace", E),
             ("Materials Science", E), ("Chemical Engineering", E),
             ("Environmental Science and Engineering", G), ("Geology", G),
             ("Biology", B), ("Bioengineering", E), ("Neurobiology", B),
         ], confidence="high",
         notes="Small, entirely STEM, and the highest doctoral density per faculty member "
               "in the state. Program count understates it relative to a large public."),
    inst("ca-usc", "University of Southern California", "USC", "Los Angeles",
         34.0224, -118.2851, "private nonprofit", "R1", "usc.edu", "https://graduateadmission.usc.edu/", [
             ("Physics", P), ("Chemistry", P), ("Mathematics", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Aerospace and Mechanical Engineering", E),
             ("Civil and Environmental Engineering", E), ("Chemical Engineering", E),
             ("Materials Science", E), ("Biomedical Engineering", E),
             ("Astronautical Engineering", E), ("Biological Sciences", B),
             ("Neuroscience", B), ("Earth Sciences", G), ("Ocean Sciences", G),
             ("Biostatistics", H), ("Psychology", Y),
         ], confidence="high"),
    inst("ca-scripps-research", "Scripps Research", "Scripps Research", "La Jolla",
         32.8895, -117.2437, "private nonprofit", "special focus, research institute",
         "scripps.edu", "https://education.scripps.edu/", [
             ("Chemistry", P), ("Biology", B), ("Chemical and Biological Sciences", H),
         ], confidence="medium",
         notes="Independent research institute that grants its own PhD. Distinct from "
               "Scripps Institution of Oceanography (UCSD) and Scripps College (Claremont) "
               "-- three different organisations with the same name."),
    inst("ca-nps", "Naval Postgraduate School", "NPS", "Monterey", 36.5959, -121.8760,
         "federal", "special focus, STEM", "nps.edu", "https://nps.edu/admissions", [
             ("Physics", P), ("Applied Mathematics", M), ("Computer Science", C),
             ("Electrical and Computer Engineering", E), ("Mechanical Engineering", E),
             ("Astronautical Engineering", E), ("Meteorology", G), ("Oceanography", G),
             ("Operations Research", M),
         ], confidence="medium",
         notes="Federal institution. Admission is normally restricted to military officers "
               "and eligible civilians, so its programs are not open on the same terms as the rest."),
    inst("ca-sdsu", "San Diego State University", "SDSU", "San Diego", 32.7757, -117.0719,
         "public", "R2", "sdsu.edu", "https://grad.sdsu.edu/", [
             ("Computational Science", C), ("Engineering Sciences", E), ("Chemistry", P),
             ("Biology", B), ("Ecology", B), ("Mathematics and Science Education", M),
             ("Clinical Psychology", Y), ("Public Health", H),
         ], confidence="medium",
         notes="Most CSU doctorates in STEM are joint with a UC campus. Counting them here "
               "and at the UC partner would double-count; they are counted here only."),
    inst("ca-santaclara", "Santa Clara University", "Santa Clara", "Santa Clara",
         37.3496, -121.9390, "private nonprofit", "doctoral, professional", "scu.edu",
         "https://www.scu.edu/engineering/graduate/", [
             ("Electrical and Computer Engineering", E), ("Computer Science and Engineering", C),
             ("Mechanical Engineering", E),
         ], confidence="low"),
    inst("ca-pacific", "University of the Pacific", "Pacific", "Stockton", 37.9800, -121.3120,
         "private nonprofit", "doctoral, professional", "pacific.edu", "https://www.pacific.edu/academics", [
             ("Pharmaceutical and Chemical Sciences", H), ("Engineering Science", E),
         ], confidence="low"),
    inst("ca-chapman", "Chapman University", "Chapman", "Orange", 33.7935, -117.8534,
         "private nonprofit", "doctoral, professional", "chapman.edu", "https://www.chapman.edu/academics/", [
             ("Computational and Data Sciences", C), ("Pharmaceutical Sciences", H),
             ("Psychology", Y),
         ], confidence="low"),
    inst("ca-lomalinda", "Loma Linda University", "Loma Linda", "Loma Linda", 34.0483, -117.2620,
         "private nonprofit", "special focus, health", "llu.edu", "https://home.llu.edu/academics", [
             ("Biochemistry", H), ("Microbiology and Molecular Genetics", H),
             ("Physiology", H), ("Rehabilitation Science", H),
         ], confidence="low"),
    inst("ca-cgu", "Claremont Graduate University", "CGU", "Claremont", 34.1030, -117.7100,
         "private nonprofit", "R2", "cgu.edu", "https://www.cgu.edu/programs/", [
             ("Computational and Systems Biology", B), ("Mathematics", M),
             ("Information Systems and Technology", C), ("Psychology", Y),
             ("Engineering and Industrial Applied Mathematics", M),
         ], confidence="low",
         notes="Graduate-only institution inside the Claremont Colleges consortium."),
]

CA_EXCL = [
    {"name": "California State University campuses (except SDSU)", "city": "statewide",
     "reason": "CSU independent doctorates are EdD, DNP, DPT and AuD; STEM PhDs run as joint programs with a UC campus"},
    {"name": "Lawrence Berkeley / Livermore National Laboratories", "city": "Berkeley, Livermore",
     "reason": "not degree-granting; students enrol through UC campuses"},
    {"name": "NASA Jet Propulsion Laboratory", "city": "Pasadena",
     "reason": "not degree-granting; operated by Caltech"},
    {"name": "Keck Graduate Institute", "city": "Claremont",
     "reason": "applied life sciences, professional master's and PharmD focus"},
    {"name": "Stanford Research Institute (SRI)", "city": "Menlo Park", "reason": "not degree-granting"},
]

PACKS = {
    "NM": ("New Mexico", NM, NM_EXCL,
           [{"label": "UNM Graduate Studies", "url": "https://grad.unm.edu/", "used_for": "UNM roster", "checked": "2026-09-08"},
            {"label": "NMSU Graduate School", "url": "https://gradschool.nmsu.edu/", "used_for": "NMSU roster", "checked": "2026-09-08"},
            {"label": "New Mexico Tech", "url": "https://www.nmt.edu/", "used_for": "NM Tech roster", "checked": "2026-09-08"}]),
    "CO": ("Colorado", CO, CO_EXCL,
           [{"label": "CU Boulder Graduate School", "url": "https://www.colorado.edu/graduateschool/", "used_for": "CU Boulder roster", "checked": "2026-09-08"},
            {"label": "CSU Graduate School", "url": "https://graduateschool.colostate.edu/", "used_for": "CSU roster", "checked": "2026-09-08"},
            {"label": "Colorado School of Mines", "url": "https://www.mines.edu/graduate-admissions/", "used_for": "Mines roster", "checked": "2026-09-08"}]),
    "CA": ("California", CA, CA_EXCL,
           [{"label": "UC Berkeley Graduate Division", "url": "https://grad.berkeley.edu/programs/", "used_for": "UC Berkeley roster", "checked": "2026-09-08"},
            {"label": "Stanford graduate programs", "url": "https://gradadmissions.stanford.edu/programs", "used_for": "Stanford roster", "checked": "2026-09-08"},
            {"label": "Caltech Graduate Studies Office", "url": "https://www.gradoffice.caltech.edu/", "used_for": "Caltech roster", "checked": "2026-09-08"}]),
}

OPEN = {
    "NM": ["NM Tech's list is the least verified in the pack; treat its count as a rough floor.",
           "The national labs drive much of the state's research but grant no degrees, so the map understates what is actually available there."],
    "CO": ["UCCS expresses several doctorates as one umbrella degree with concentrations; the count depends on which unit you pick.",
           "CU Boulder and CU Anschutz are one university system but separate campuses; they are listed separately and must not be merged without deciding which is which.",
           "UNC is tagged boundary: its doctorates are discipline-education plans."],
    "CA": ["Program lists here are shallower relative to institution size than the Arizona pack, so California's program total is a worse floor than Arizona's.",
           "CSU joint doctorates are counted at the CSU campus only. Flipping that convention moves counts between institutions.",
           "Naval Postgraduate School has restricted admission and is not comparable to the others on access.",
           "Multi-campus systems are one marker each; the UC system's ten doctoral campuses are ten separate records, not one."]
}


def main():
    for code, (name, insts, excl, sources) in PACKS.items():
        doc = {
            "schema": "gradfinder.state_pack/1",
            "state": code,
            "state_name": name,
            "generated": "2026-09-08",
            "stage": "L1-seed",
            "provenance": {
                "method": "hand-seeded from institution graduate-college listings",
                "ipeds_joined": False,
                "roster_complete": "believed complete for research-doctorate institutions; not machine-verified",
                "program_lists_complete": False,
                "note": NOTE,
            },
            "scope": {
                "award": "research doctorate (PhD) and equivalent",
                "stem_definition": "CIP families 01, 03, 11, 14, 26, 27, 40 plus research-track biomedical (51.14 research only). Professional practice doctorates (MD, DO, PharmD, DNP, DPT, OTD, DBA, EdD, PsyD) are excluded.",
                "boundary_families": ["psych_research", "biomed_health"],
            },
            "institutions": insts,
            "excluded": excl,
            "sources": sources,
            "open_questions": OPEN[code],
        }
        path = os.path.join(OUT, "%s.json" % code)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
            fh.write("\n")
        n = sum(len(i["programs"]) for i in insts)
        print("[seed] %s  %2d institutions  %3d programs  ->  %s"
              % (code, len(insts), n, os.path.relpath(path, ROOT)))


if __name__ == "__main__":
    main()
