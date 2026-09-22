from pathlib import Path
import os
import uuid

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from scanner.engine import scan_file
from scanner.report import write_json


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_PATH = BASE_DIR / "privacy_findings.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# Maximum upload size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


# ============================================================
# ALLOWED FILE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    # Images
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "tif",
    "tiff",
    "webp",

    # PDF
    "pdf",

    # Excel / spreadsheets
    "csv",
    "xlsx",
    "xlsm",

    # Microsoft Office
    "docx",
    "pptx",

    # Text
    "txt",
    "md",
    "log",

    # Data / markup
    "json",
    "xml",
    "html",
    "htm",
    "yaml",
    "yml",
}


# ============================================================
# CORS
# ============================================================
#
# Allows your Vercel frontend to communicate with this backend.
#
# Current frontend:
# https://pii-detector-xi.vercel.app/
#
# Local development is also allowed.
# ============================================================

ALLOWED_ORIGINS = {
    "https://pii-detector-xi.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename: str) -> bool:
    """
    Check whether the uploaded file has a supported extension.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.get("/")
def index():
    """
    Main backend page / health check.
    """

    return jsonify({
        "status": "online",
        "service": "PII Detector Backend",
        "message": "PII detection API is running.",
        "endpoint": "/api/scan",
        "method": "POST",
        "max_file_size_mb": 10,
        "supported_formats": sorted(ALLOWED_EXTENSIONS)
    })


# ============================================================
# OPTIONAL FRONTEND PAGE
# ============================================================

@app.get("/app")
def app_page():
    """
    If templates/index.html exists, this can display
    the original Flask frontend.
    """

    return render_template("index.html")


# ============================================================
# SCAN API
# ============================================================

@app.route("/api/scan", methods=["POST", "OPTIONS"])
def scan_upload():

    # --------------------------------------------------------
    # Handle browser CORS preflight request
    # --------------------------------------------------------

    if request.method == "OPTIONS":
        return "", 204

    # --------------------------------------------------------
    # Get uploaded file
    # --------------------------------------------------------

    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify({
            "success": False,
            "error": "No file was uploaded.",
            "message": "Please select a file using the 'file' field."
        }), 400

    # --------------------------------------------------------
    # Check filename
    # --------------------------------------------------------

    original_filename = uploaded_file.filename

    if not original_filename:
        return jsonify({
            "success": False,
            "error": "Please select a file."
        }), 400

    # --------------------------------------------------------
    # Check extension
    # --------------------------------------------------------

    if not allowed_file(original_filename):
        extension = (
            original_filename.rsplit(".", 1)[1].lower()
            if "." in original_filename
            else ""
        )

        return jsonify({
            "success": False,
            "error": "Unsupported file type.",
            "extension": extension,
            "supported_formats": sorted(ALLOWED_EXTENSIONS)
        }), 400

    # --------------------------------------------------------
    # Secure filename
    # --------------------------------------------------------

    safe_filename = secure_filename(original_filename)

    if not safe_filename:
        return jsonify({
            "success": False,
            "error": "Invalid filename."
        }), 400

    # --------------------------------------------------------
    # Generate unique filename
    #
    # Prevents two users uploading files with the same name
    # from overwriting each other.
    # --------------------------------------------------------

    unique_id = uuid.uuid4().hex

    extension = safe_filename.rsplit(".", 1)[1].lower()

    stored_filename = f"{unique_id}.{extension}"

    file_path = UPLOAD_DIR / stored_filename

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    try:
        uploaded_file.save(file_path)

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Could not save uploaded file.",
            "detail": str(exc)
        }), 500

    # --------------------------------------------------------
    # Scan file
    # --------------------------------------------------------

    try:

        findings = scan_file(file_path)

        # Save JSON report
        write_json(findings, REPORT_PATH)

        # Convert findings to dictionaries
        finding_data = []

        for finding in findings:
            try:
                finding_data.append(finding.as_dict())
            except AttributeError:
                finding_data.append({
                    "finding": str(finding)
                })

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "filename": original_filename,
            "stored_filename": stored_filename,
            "finding_count": len(findings),
            "findings": finding_data
        }), 200

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": "The file could not be scanned.",
            "detail": str(exc)
        }), 500

    finally:

        # ----------------------------------------------------
        # Delete uploaded temporary file after scanning.
        #
        # This prevents Render storage from filling up.
        # ----------------------------------------------------

        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass


# ============================================================
# FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def too_large(_error):

    return jsonify({
        "success": False,
        "error": "File is too large.",
        "message": "Maximum file size is 10 MB."
    }), 413


# ============================================================
# GENERAL ERROR HANDLER
# ============================================================

@app.errorhandler(500)
def internal_error(_error):

    return jsonify({
        "success": False,
        "error": "Internal server error."
    }), 500


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )