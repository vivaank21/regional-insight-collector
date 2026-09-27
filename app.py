"""
app.py
-------
Regional Insight Collector - Flask application entry point.

Flow:
    Visitor submits name (POST /discover)
        -> server resolves visitor IP (server-side only)
        -> server calls geolocation.get_location()
        -> record saved to SQLite + CSV
        -> personalization.get_regional_image() picks regional content
        -> visitor redirected to /experience, which reads only the
           safe, already-computed values out of the session and renders
           them (IP address is never placed in the session or template)
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config, ensure_directories
import database
import csv_logger
import geolocation
import personalization

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------

ensure_directories()

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Only apply ProxyFix (which rewrites request.remote_addr from
# X-Forwarded-For) when the operator has explicitly declared that the
# app sits behind a trusted reverse proxy. This keeps get_client_ip()
# safe from spoofed headers by default.
if Config.TRUST_PROXY_HEADERS:
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=Config.TRUSTED_PROXY_COUNT, x_proto=1, x_host=1
    )

# ---------------------------------------------------------------------
# Logging - technical details go to logs/application.log only, never to
# the visitor's browser.
# ---------------------------------------------------------------------

logger = logging.getLogger("regional_insight")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = RotatingFileHandler(
        Config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

# ---------------------------------------------------------------------
# Database / CSV initialization
# ---------------------------------------------------------------------

database.init_db()
csv_logger.ensure_csv()


# ---------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------

def validate_name(raw_name):
    """
    Validate the visitor-supplied name.

    Returns (cleaned_name, error_message). cleaned_name is None if
    invalid. The value is escaped before it is ever rendered.
    """
    if raw_name is None:
        return None, "Please tell us what to call you."

    name = raw_name.strip()

    if len(name) < Config.MIN_NAME_LENGTH:
        return None, "Please tell us what to call you."

    if len(name) > Config.MAX_NAME_LENGTH:
        return None, f"Names must be {Config.MAX_NAME_LENGTH} characters or fewer."

    # Allow letters (incl. unicode), spaces, apostrophes, hyphens, and periods.
    # This blocks angle brackets, quotes, script fragments, etc. up front,
    # in addition to the output-escaping done at render time.
    cleaned = "".join(
        ch for ch in name if ch.isalpha() or ch.isspace() or ch in "'-."
    ).strip()

    if not cleaned:
        return None, "Please use a name made of letters."

    return cleaned, None


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/discover", methods=["POST"])
def discover():
    raw_name = request.form.get("user_name", "")
    clean_name, error = validate_name(raw_name)

    if error:
        return render_template("index.html", error=error, previous_name=""), 400

    try:
        ip_address = geolocation.get_client_ip()
        location = geolocation.get_location(ip_address)

        record_id, created_at = database.insert_visitor(
            user_name=clean_name, ip_address=ip_address, location=location
        )

        csv_logger.append_visitor_row(
            {
                "id": record_id,
                "user_name": clean_name,
                "ip_address": ip_address,
                "country": location.get("country", "Unknown"),
                "region": location.get("region", "Unknown"),
                "state": location.get("state", "Unknown"),
                "city": location.get("city", "Unknown"),
                "timezone": location.get("timezone", "Unknown"),
                "created_at": created_at,
            }
        )

        content = personalization.get_regional_image(
            country=location.get("country"),
            region=location.get("region"),
            state=location.get("state"),
            city=location.get("city"),
        )

        # Only safe, already-vetted display values go into the session.
        # The IP address, database id, and raw API response are never
        # stored here and never reach the browser.
        session["experience"] = {
            "user_name": clean_name,
            "country": location.get("country", "Unknown"),
            "region": location.get("region", "Unknown"),
            "state": location.get("state", "Unknown"),
            "city": location.get("city", "Unknown"),
            "image_path": content["image_path"],
            "tagline": content["tagline"],
        }

        return redirect(url_for("experience"))

    except Exception:
        logger.exception("Unhandled error while processing /discover request.")
        return render_template(
            "index.html",
            error="Something went wrong on our end. Please try again in a moment.",
            previous_name="",
        ), 500


@app.route("/experience", methods=["GET"])
def experience():
    data = session.get("experience")
    if not data:
        return redirect(url_for("index"))

    # Escaping here is defense-in-depth; validate_name() already
    # constrained the character set. Jinja2 autoescaping in the template
    # also escapes these values automatically.
    safe_data = {key: escape(str(value)) for key, value in data.items()}
    # image_path must remain a plain (unescaped-for-URL-purposes) string
    # for use in an <img src="...">; it is generated internally by
    # personalization.py, never from user input, so it's safe as-is.
    safe_data["image_path"] = data["image_path"]

    return render_template("experience.html", data=safe_data)


# ---------------------------------------------------------------------
# Error handlers - never leak tracebacks or internal details.
# ---------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return render_template("index.html", error=None, previous_name=""), 404


# =====================================================================
# Admin Panel - password-protected visitor data dashboard
# =====================================================================

def is_admin_authenticated():
    """Check if the current session is authenticated as admin."""
    return session.get("admin_authenticated") is True


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """Admin login page - validate password before granting access."""
    if request.method == "POST":
        password = request.form.get("password", "")
        
        if password == Config.ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            logger.info("Admin panel accessed successfully.")
            return redirect(url_for("admin_dashboard"))
        else:
            logger.warning("Failed admin login attempt with incorrect password.")
            return render_template(
                "admin_login.html",
                error="Incorrect password. Try again.",
            ), 401
    
    # GET request - show login form if not already authenticated
    if is_admin_authenticated():
        return redirect(url_for("admin_dashboard"))
    
    return render_template("admin_login.html", error=None)


@app.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard showing visitor analytics and data."""
    if not is_admin_authenticated():
        return redirect(url_for("admin_login"))
    
    try:
        total_visitors = database.get_visitor_count()
        all_visitors = database.get_all_visitors()
        stats = database.get_visitor_stats()
        
        return render_template(
            "admin_dashboard.html",
            total_visitors=total_visitors,
            visitors=all_visitors,
            stats=stats,
        )
    
    except Exception as exc:
        logger.exception("Error loading admin dashboard: %s", exc)
        return render_template(
            "admin_login.html",
            error="Error loading dashboard. Check server logs.",
        ), 500


@app.route("/admin/logout")
def admin_logout():
    """Log out from admin panel."""
    session.pop("admin_authenticated", None)
    logger.info("Admin panel logged out.")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found_handler(_e):
    return render_template("index.html", error=None, previous_name=""), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Internal server error: %s", e)
    return render_template(
        "index.html",
        error="Something went wrong on our end. Please try again in a moment.",
        previous_name="",
    ), 500


# ---------------------------------------------------------------------
# Block direct access to sensitive files even if someone points a
# browser at them (Flask's static handler only ever serves static/, but
# this is an explicit belt-and-braces guard for any misconfiguration).
# ---------------------------------------------------------------------

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
