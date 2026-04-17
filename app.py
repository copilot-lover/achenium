from __future__ import annotations

from flask import Flask, render_template, request

from config import settings
from services.jobs import start_scheduler
from services.research import run_deep_research, suggest_markets
from services.storage import init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/suggestions", methods=["POST"])
def suggestions():
    style = request.form.get("style", "balanced")
    markets = suggest_markets(style)
    return render_template("partials/suggestions.html", markets=markets)


@app.route("/research", methods=["POST"])
def research():
    selected_markets = request.form.getlist("selected_markets")
    risk_profile = request.form.get("risk_profile", "moderate")
    horizon = request.form.get("horizon", "swing")

    if not selected_markets:
        return render_template("partials/error.html", message="Please select at least one market.")

    outputs = run_deep_research(selected_markets, risk_profile, horizon)
    return render_template("partials/reports.html", outputs=outputs)


@app.route("/health")
def health():
    return {"status": "ok"}


def create_app() -> Flask:
    init_db()
    start_scheduler()
    return app


if __name__ == "__main__":
    create_app()
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
