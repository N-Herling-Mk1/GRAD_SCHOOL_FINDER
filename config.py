"""Configuration. Local development defaults; no secrets live here."""

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


class Config:
    APP_NAME = "GRADFINDER"
    BUILD = "mk3"
    ROOT = ROOT
    DATA_DIR = os.path.join(ROOT, "data")
    INSTITUTIONS_DIR = os.path.join(ROOT, "data", "institutions")
    FACULTY_DIR = os.path.join(ROOT, "data", "faculty")
    DERIVED_DIR = os.path.join(ROOT, "data", "derived")
    GEO_FILE = os.path.join(ROOT, "gradfinder", "static", "geo", "us_states.json")
    PROJECTION_FILE = os.path.join(ROOT, "data", "derived", "projection.json")

    HOST = os.environ.get("GRADFINDER_HOST", "127.0.0.1")
    PORT = int(os.environ.get("GRADFINDER_PORT", "5057"))
    DEBUG = os.environ.get("GRADFINDER_DEBUG", "1") == "1"

    # Reload data packs from disk on every request. Convenient while the packs are
    # being hand-edited; turn off for anything resembling a deploy.
    HOT_RELOAD_DATA = os.environ.get("GRADFINDER_HOT_RELOAD", "1") == "1"

    JSON_SORT_KEYS = False


# Program family labels. The front end renders these; the data packs reference the keys.
FAMILIES = [
    {"key": "physical_sci", "label": "Physical sciences", "cip": "40"},
    {"key": "math_stat", "label": "Mathematics and statistics", "cip": "27"},
    {"key": "comp_info", "label": "Computing and information", "cip": "11"},
    {"key": "engineering", "label": "Engineering", "cip": "14"},
    {"key": "bio_sci", "label": "Biological sciences", "cip": "26"},
    {"key": "geo_env", "label": "Earth and environment", "cip": "40.06 / 03"},
    {"key": "agri", "label": "Agriculture and forestry", "cip": "01"},
    {"key": "biomed_health", "label": "Biomedical and health research", "cip": "26.09 / 51.14"},
    {"key": "psych_research", "label": "Psychology (research)", "cip": "42"},
]
