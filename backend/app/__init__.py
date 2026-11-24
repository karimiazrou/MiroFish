"""
MiroFish Backend - Flask application factory.
"""
import os
import warnings

warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from .utils.logger import setup_logger, get_logger
from .utils.security import register_security


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(app, "json") and hasattr(app.json, "ensure_ascii"):
        app.json.ensure_ascii = False

    logger = setup_logger("mirofish")
    is_reloader_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    debug_mode = app.config.get("DEBUG", False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend starting...")
        logger.info("=" * 50)

    # Trust forwarded client/protocol headers only when the deployment is
    # behind the private Nginx service defined in docker-compose.yml.
    if app.config.get("TRUST_PROXY_HEADERS", False):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # No wildcard CORS. Cross-origin access is disabled unless explicitly
    # allow-listed with CORS_ALLOWED_ORIGINS.
    register_security(app)

    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation process cleanup registered")

    @app.before_request
    def log_request():
        # Never log JSON bodies: they may contain prompts, customer data or
        # credentials. Do not log query strings, which may contain tokens.
        get_logger("mirofish.request").debug(
            "Request: %s %s", request.method, request.path
        )

    @app.after_request
    def log_response(response):
        get_logger("mirofish.request").debug("Response: %s", response.status_code)
        return response

    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix="/api/graph")
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(report_bp, url_prefix="/api/report")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "MiroFish Backend"}

    if should_log_startup:
        logger.info("MiroFish Backend startup complete")
    return app
