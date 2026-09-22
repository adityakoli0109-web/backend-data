from pathlib import Path
from .crawl import local_discover
from .extract import extract
from .pii import detect
from .context import context_score, classify
from .models import Finding


def _windows(text, start, end, radius=180):
    return text[max(0, start-radius):min(len(text), end+radius)].replace("\n", " ")


def scan_text(text: str, source: str):
    """Scan already-extracted text and return privacy findings."""
    findings = []
    if not text:
        return findings

    score, evidence = context_score(text)
    for hit in detect(text):
        window = _windows(text, hit["start"], hit["end"])
        ev = evidence + [f"nearby text: {window[:360]}"]
        classification = classify(hit["confidence"], score, evidence)
        findings.append(Finding(
            source=source,
            kind=hit["kind"],
            value_masked=hit["masked"],
            signal=hit["kind"],
            confidence=hit["confidence"],
            evidence=ev,
            classification=classification,
            context_score=score,
        ))
    return findings


def scan_local(root: Path):
    findings = []
    for path in local_discover(root):
        findings.extend(scan_text(extract(path), str(path)))
    return findings


def scan_file(path: Path):
    """Scan one supported local file, including images through OCR."""
    return scan_text(extract(path), str(path))
