from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Finding:
    source: str
    kind: str
    value_masked: str
    signal: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    classification: str = "CONTEXT_REVIEW"
    context_score: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
