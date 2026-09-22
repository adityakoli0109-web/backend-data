from pathlib import Path
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from scanner.engine import scan_file
from scanner.report import write_json

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_PATH = BASE_DIR / "privacy_findings.json"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "bmp", "tif", "tiff", "webp", "pdf", "csv", "xlsx", "xlsm", "docx", "pptx", "txt", "md", "log", "json", "xml", "html", "htm", "yaml", "yml"}
MAX_FILE_SIZE = 10 * 1024 * 1024

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/scan")
def scan_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Please select a file."}), 400
    if not allowed(file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    safe_name = secure_filename(file.filename)
    if not safe_name:
        return jsonify({"error": "Invalid filename."}), 400

    path = UPLOAD_DIR / safe_name
    file.save(path)

    try:
        findings = scan_file(path)
        write_json(findings, REPORT_PATH)
        return jsonify({
            "filename": safe_name,
            "finding_count": len(findings),
            "findings": [finding.as_dict() for finding in findings],
        })
    except Exception as exc:
        return jsonify({
            "error": "The file could not be scanned.",
            "detail": str(exc),
        }), 500


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File is too large. Maximum size is 10 MB."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
