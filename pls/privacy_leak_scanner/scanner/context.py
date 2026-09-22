import re

# Positive signals mean "this looks deliberately disclosed".
# Negative signals mean "this looks accidentally exposed/internal".
INTENDED = [
    (r"\bright to information\b|\brti\b", 4.0, "page/document references RTI"),
    (r"\bpublic disclosure\b|\bdisclosure register\b", 4.0, "explicit public-disclosure language"),
    (r"\bstatutory register\b|\bstatutory disclosure\b", 3.5, "statutory publication context"),
    (r"\bbeneficiary list\b|\baward(?:ee)? list\b|\bprocurement result\b", 2.5, "recognized public-list context"),
    (r"\bnotification\b|\bgazette\b|\bpublic notice\b", 2.0, "official notice/publication context"),
    (r"\bproactive disclosure\b|\bsuo moto\b", 3.5, "proactive disclosure language"),
]

ACCIDENTAL = [
    (r"\bconfidential\b|\brestricted\b|\binternal use\b", -5.0, "confidential/internal-use marker"),
    (r"\bdo not publish\b|\bnot for publication\b|\bremove before publication\b", -6.0, "explicit non-publication instruction"),
    (r"\bredact(?:ed|ion)?\b|\bmask(?:ed|ing)?\b", -2.5, "redaction/masking language"),
    (r"\bdraft\b|\bworking copy\b|\btemporary\b", -2.0, "draft/working-copy marker"),
    (r"\bpassword\b|\botp\b|\bsecret\b|\bapi[_ -]?key\b", -6.0, "credential/secret context"),
]

def context_score(text: str) -> tuple[float, list[str]]:
    score = 0.0
    evidence = []
    low = text.lower()
    for pattern, weight, reason in INTENDED + ACCIDENTAL:
        if re.search(pattern, low):
            score += weight
            evidence.append(reason)
    return score, evidence

def classify(pii_confidence: float, score: float, evidence: list[str]) -> str:
    # PII confidence affects whether there is a finding, while context determines intent.
    if "credential/secret context" in evidence or score <= -5:
        return "LIKELY_ACCIDENTAL"
    if score >= 3:
        return "INTENDED_DISCLOSURE"
    return "CONTEXT_REVIEW"
