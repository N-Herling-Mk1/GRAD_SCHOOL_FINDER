#!/usr/bin/env python3
"""Local development entry point.  python app.py"""

from config import Config
from gradfinder import create_app

app = create_app(Config)

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
