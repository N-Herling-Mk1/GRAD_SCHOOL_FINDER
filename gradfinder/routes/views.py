"""HTML routes."""

from flask import Blueprint, current_app, render_template, send_from_directory

from config import FAMILIES

bp = Blueprint("views", __name__)


@bp.route("/")
def index():
    store = current_app.store
    return render_template(
        "index.html",
        families=FAMILIES,
        canvas=current_app.geo.canvas,
        coverage=store.index()["coverage"],
        lens=current_app.lens.summary(),
        build=current_app.config["BUILD"],
    )


@bp.route("/method")
def method():
    return render_template("method.html", families=FAMILIES, build=current_app.config["BUILD"])


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(current_app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon")


DOWNLOADS = {"grad_vetting_topdown_mk1.xlsx", "gradfinder_universities_mk1.csv", "topdown_mk1.json"}


@bp.route("/downloads/<name>")
def downloads(name):
    """Search-material files from data/faculty. Allow-listed; the static export copies the same set."""
    if name not in DOWNLOADS:
        return ("not found", 404)
    return send_from_directory(current_app.config["FACULTY_DIR"], name, as_attachment=True)
