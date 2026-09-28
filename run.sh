#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
[ -f gradfinder/static/geo/us_states.json ] || python tools/build_geo.py
python tools/check_data.py
python app.py
