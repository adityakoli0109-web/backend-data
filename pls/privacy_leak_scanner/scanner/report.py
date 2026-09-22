import json
from pathlib import Path

def write_json(findings, path: Path):
    path.write_text(
        json.dumps([f.as_dict() for f in findings], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
