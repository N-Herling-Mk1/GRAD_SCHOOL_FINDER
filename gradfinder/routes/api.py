"""JSON API. Everything the front end draws comes from here."""

import time

from flask import Blueprint, current_app, jsonify, request

from config import FAMILIES

bp = Blueprint("api", __name__)


@bp.route("/health")
def health():
    return jsonify({
        "ok": True,
        "build": current_app.config["BUILD"],
        "packs": current_app.store.loaded_codes,
        "time": time.time(),
    })


@bp.route("/meta")
def meta():
    return jsonify({
        "build": current_app.config["BUILD"],
        "families": FAMILIES,
        "canvas": current_app.geo.canvas,
    })


@bp.route("/geo")
def geo():
    return jsonify(current_app.geo.geo)


@bp.route("/states")
def states():
    return jsonify(current_app.lens.attach(current_app.store.index()))


@bp.route("/states/<code>")
def state_detail(code):
    family = request.args.get("family") or None
    include_boundary = request.args.get("boundary", "1") != "0"
    detail = current_app.store.detail(code, family=family, include_boundary=include_boundary)
    if detail is None:
        return jsonify({
            "state": code.upper(),
            "name": current_app.geo.name_of(code.upper()),
            "status": "empty",
            "message": "No data pack for this state yet.",
            "next_step": "Add data/institutions/%s.json following the AZ pack schema." % code.upper(),
        }), 404
    return jsonify(detail)


@bp.route("/faculty")
def faculty_index():
    lens = current_app.lens
    return jsonify({"meta": lens.meta, "summary": lens.summary(),
                    "states": lens.rollups(), "sites": lens.sites()})


@bp.route("/faculty/<code>")
def faculty_state(code):
    return jsonify(current_app.lens.state(code))
