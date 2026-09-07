"""Herdwise Flask application backed by Supabase."""

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from supabase import Client, create_client


load_dotenv()
app = Flask(__name__)
# Vue and Jinja both use {{ ... }} by default. Give Jinja its own delimiters so
# Vue expressions can be sent to the browser untouched.
app.jinja_env.variable_start_string = "[["
app.jinja_env.variable_end_string = "]]"


class SupabaseConfigurationError(RuntimeError):
    """Raised when the server does not have the required Supabase settings."""


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Create one server-side Supabase client from Render environment variables."""
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_KEY")  # Legacy key name, kept for compatibility.
    )
    if not url or not key:
        raise SupabaseConfigurationError(
            "Set SUPABASE_URL and SUPABASE_SECRET_KEY (or SUPABASE_PUBLISHABLE_KEY)."
        )
    return create_client(url, key)


def formatted_value(value: Any, unit: str = "") -> str:
    """Render a Supabase value consistently while allowing null sensor readings."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        value = f"{value:g}"
    value = str(value)
    if unit and not value.lower().endswith(unit.lower()):
        return f"{value} {unit}"
    return value


def coordinates_from(row: dict[str, Any], parameters: dict[str, Any]) -> str:
    """Support a text coordinate column or separate latitude/longitude columns."""
    coordinates = parameters.get("gps_coordinates") or row.get("gps_coordinates")
    if coordinates:
        return str(coordinates)

    latitude = row.get("gps_latitude", row.get("latitude"))
    longitude = row.get("gps_longitude", row.get("longitude"))
    if latitude is None or longitude is None:
        return "—"

    latitude, longitude = float(latitude), float(longitude)
    lat_direction = "N" if latitude >= 0 else "S"
    lng_direction = "E" if longitude >= 0 else "W"
    return f"{abs(latitude):.4f}° {lat_direction}, {abs(longitude):.4f}° {lng_direction}"


def cow_from_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map a cows-table row into the API shape used by the Vue interface.

    The supplied schema stores readings as regular columns. A JSONB `parameters`
    column is also supported, so existing installations can migrate gradually.
    """
    raw_parameters = row.get("parameters")
    parameters = raw_parameters if isinstance(raw_parameters, dict) else {}

    def reading(key: str, unit: str = "") -> str:
        return formatted_value(parameters.get(key, row.get(key)), unit)

    return {
        "id": str(row.get("cow_id", row.get("id", "Unknown"))),
        "name": row.get("name", "Unnamed cow"),
        "tag": row.get("tag", row.get("ear_tag", "No tag")),
        "breed": row.get("breed", "Unspecified breed"),
        "health": row.get("health", row.get("health_status", "Observation")),
        "last_checked": row.get("last_checked", row.get("updated_at", "not yet")),
        "image": row.get("image_url", row.get("image", "/static/images/cow-portrait.svg")),
        "parameters": {
            "activity_level": reading("activity_level"),
            "body_temp": reading("body_temp", "°C"),
            "udder_temp": reading("udder_temp", "°C"),
            "teat1_tds": reading("teat1_tds", "ppm"),
            "teat2_tds": reading("teat2_tds", "ppm"),
            "teat3_tds": reading("teat3_tds", "ppm"),
            "teat4_tds": reading("teat4_tds", "ppm"),
            "gps_coordinates": coordinates_from(row, parameters),
        },
    }


def load_cows() -> list[dict[str, Any]]:
    table_name = os.getenv("SUPABASE_COWS_TABLE", "cows")
    response = get_supabase_client().table(table_name).select("*").execute()
    return [cow_from_row(row) for row in response.data]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    """Lightweight liveness check for Render health checks or an external cron."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/api/cows")
def cows():
    try:
        return jsonify(load_cows())
    except SupabaseConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except Exception:
        app.logger.exception("Unable to load cows from Supabase")
        return jsonify({"error": "Unable to load herd data from Supabase."}), 503


@app.get("/api/cows/<cow_id>")
def cow(cow_id: str):
    try:
        found = next((entry for entry in load_cows() if entry["id"] == cow_id), None)
        return jsonify(found or {"error": "Cow not found"}), 200 if found else 404
    except SupabaseConfigurationError as error:
        return jsonify({"error": str(error)}), 503
    except Exception:
        app.logger.exception("Unable to load cow %s from Supabase", cow_id)
        return jsonify({"error": "Unable to load herd data from Supabase."}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
