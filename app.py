"""Flask application entrypoint and route registration."""

from __future__ import annotations

import logging

from flask import Flask, render_template, request

from config import settings
from services.jobs import scheduler, start_scheduler
from services.research import run_deep_research, suggest_markets, validate_selected_markets
from services.storage import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/suggestions", methods=["POST"])
def suggestions():
    try:
        style = request.form.get("style", "balanced").strip().lower()
        markets = suggest_markets(style)
        return render_template("partials/suggestions.html", markets=markets)
    except Exception as exc:
        logger.exception("Failed to generate suggestions: %s", exc)
        return render_template(
            "partials/error.html",
            message="Could not generate market suggestions right now. Please retry.",
        ), 500


@app.route("/research", methods=["POST"])
def research():
    try:
        selected_markets = validate_selected_markets(request.form.getlist("selected_markets"))
        risk_profile = request.form.get("risk_profile", "moderate").strip().lower()
        horizon = request.form.get("horizon", "swing").strip().lower()

        if not selected_markets:
            return render_template("partials/error.html", message="Select at least one valid market."), 400

        outputs = run_deep_research(selected_markets, risk_profile, horizon)
        if not outputs:
            return render_template(
                "partials/error.html",
                message="No valid markets were processed. Please adjust your selections.",
            ), 400

        return render_template("partials/reports.html", outputs=outputs)
    except Exception as exc:
        logger.exception("Research generation failed: %s", exc)
        return render_template(
            "partials/error.html",
            message=(
                "Deep research is temporarily unavailable. "
                "The app switched to a safe fallback; try again shortly."
            ),
        ), 500


@app.route("/health")
def health():
    return {
        "status": "ok",
        "scheduler_running": bool(scheduler and scheduler.running),
        "scheduler_type": "APScheduler BackgroundScheduler (in-process)",
    }


def create_app() -> Flask:
    init_db()
    start_scheduler()
    return app


if __name__ == "__main__":
    create_app()
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
