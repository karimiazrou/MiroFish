"""
MiroFish Backend development entry point.

For production, serve app:create_app() with a production WSGI server behind
an HTTPS reverse proxy. This module deliberately binds to loopback by default.
"""
import os
import sys

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    errors = Config.validate()
    if errors:
        print("Configuration errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    app = create_app()
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5001))
    app.run(host=host, port=port, debug=Config.DEBUG, threaded=True)


if __name__ == "__main__":
    main()
