"""Application factory."""

import sys
import time

from flask import Flask

from config import Config
from .services.geo import load_geo
from .services.store import Store
from .services.faculty import FacultyLens


def banner(cfg, geo, store, lens):
    line = "=" * 62
    print(line)
    print(" %s %s   graduate program search console" % (cfg.APP_NAME, cfg.BUILD))
    print(line)
    print("  canvas         %dx%d" % (geo.canvas["width"], geo.canvas["height"]))
    print("  jurisdictions  %d" % len(geo.state_codes))
    print("  data packs     %s" % (", ".join(store.loaded_codes) or "none"))
    print("  faculty lens   %d state(s)" % len(lens.rollups()))
    print("  hot reload     %s" % ("on" if cfg.HOT_RELOAD_DATA else "off"))
    print("  serving        http://%s:%d/" % (cfg.HOST, cfg.PORT))
    print(line)
    sys.stdout.flush()


def create_app(config_object=Config):
    t0 = time.time()
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)
    app.json.sort_keys = False

    print("[boot] loading geometry...")
    geo = load_geo(config_object)
    print("[boot] loading data packs...")
    store = Store(config_object.INSTITUTIONS_DIR, geo, hot_reload=config_object.HOT_RELOAD_DATA)

    print("[boot] loading faculty lens...")
    lens = FacultyLens(config_object.FACULTY_DIR, hot_reload=config_object.HOT_RELOAD_DATA)

    app.geo = geo
    app.lens = lens
    app.store = store

    from .routes.views import bp as views_bp
    from .routes.api import bp as api_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    print("[boot] ready in %.0f ms" % (1000 * (time.time() - t0)))
    banner(config_object, geo, store, lens)
    return app
