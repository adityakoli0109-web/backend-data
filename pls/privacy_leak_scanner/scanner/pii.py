import re
from dataclasses import dataclass

@dataclass(frozen=True)
class PIISignal:
    kind: str
    pattern: re.Pattern
    confidence: float

PATTERNS = [
    PIISignal("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), .92),
    PIISignal("phone", re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"), .78),
    PIISignal("aadhaar_like", re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"), .72),
    PIISignal("pan_like", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I), .88),
    PIISignal("date_of_birth", re.compile(
        r"\b(?:0?[1-9]|[12]\d|3[01])[-/](?:0?[1-9]|1[0-2])[-/](?:19|20)\d{2}\b"
    ), .62),
]

def mask(value: str) -> str:
    value = value.strip()
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * max(1, len(value) - 4) + value[-2:]

def detect(text: str):
    hits = []
    for sig in PATTERNS:
        for m in sig.pattern.finditer(text):
            hits.append({
                "kind": sig.kind,
                "value": m.group(0),
                "masked": mask(m.group(0)),
                "confidence": sig.confidence,
                "start": m.start(),
                "end": m.end(),
            })
    return hits
