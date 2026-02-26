from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from color_engine.analyzer import build_color_profile
from color_engine.extractor import extract_skin_lab
from color_engine.groq_generator import generate_palettes

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def _parse_max_file_size_mb() -> int:
    raw = (os.getenv("MAX_FILE_SIZE_MB") or os.getenv("MAX_FILE_SIZE") or "10").strip()
    lowered = raw.lower()
    if lowered.endswith("mb"):
        lowered = lowered[:-2].strip()
    try:
        value = int(float(lowered))
    except ValueError:
        value = 10
    return max(value, 1)


def _parse_allowed_extensions() -> set[str]:
    raw = os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,webp")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


MAX_FILE_SIZE_MB = _parse_max_file_size_mb()
ALLOWED_EXTENSIONS = _parse_allowed_extensions()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_uploaded_image(file_storage: Any) -> Path:
    original = secure_filename(file_storage.filename or "")
    if not original:
        raise ValueError("Missing file name.")
    if not _allowed_file(original):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed: {allowed}")

    suffix = Path(original).suffix.lower()
    unique_name = f"{Path(original).stem}_{uuid.uuid4().hex[:10]}{suffix}"
    output_path = UPLOAD_FOLDER / unique_name
    file_storage.save(output_path)
    return output_path


def _analyze_image(image_path: Path, context: dict[str, Any]) -> dict[str, Any]:
    lab_values = extract_skin_lab(str(image_path))
    profile = build_color_profile(lab_values)
    palettes = generate_palettes(profile, context=context)
    return {
        "profile": profile,
        "palettes": palettes,
        "image_path": str(image_path),
    }


def _request_context() -> dict[str, str]:
    return {
        "user_segment": "college_student",
        "mood": (request.form.get("mood") or "").strip(),
        "occasion": (request.form.get("occasion") or "").strip(),
        "gender": (request.form.get("gender") or "").strip(),
        "campus_style": (request.form.get("campus_style") or "").strip(),
        "budget_tier": (request.form.get("budget_tier") or "").strip(),
        "student_year": (request.form.get("student_year") or "").strip(),
        "season": (request.form.get("season") or "").strip(),
    }


@app.errorhandler(413)
def file_too_large(_error: Exception):
    return (
        render_template(
            "index.html",
            error=f"File too large. Max allowed size is {MAX_FILE_SIZE_MB} MB.",
        ),
        413,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    file = request.files.get("image")
    if file is None or not file.filename:
        return render_template("index.html", error="Please select an image file."), 400

    try:
        image_path = _save_uploaded_image(file)
        context = _request_context()
        result = _analyze_image(image_path=image_path, context=context)
    except Exception as exc:
        return render_template("index.html", error=f"Analysis failed: {exc}"), 400

    return render_template(
        "result.html",
        profile=result["profile"],
        palettes=result["palettes"],
        context=context,
    )


@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    file = request.files.get("image")
    if file is None or not file.filename:
        return jsonify({"error": "Please include an image file in field 'image'."}), 400

    try:
        image_path = _save_uploaded_image(file)
        context = _request_context()
        result = _analyze_image(image_path=image_path, context=context)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "status": "ok",
            "profile": result["profile"],
            "palette_recommendations": result["palettes"],
            "input_context": context,
        }
    )


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
