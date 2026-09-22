from scanner.context import context_score, classify

def test_rti_is_not_automatically_a_leak():
    score, evidence = context_score("RTI proactive disclosure register")
    assert score >= 3
    assert classify(.9, score, evidence) == "INTENDED_DISCLOSURE"

def test_internal_pii_is_flagged():
    score, evidence = context_score("CONFIDENTIAL - internal use only")
    assert score < 0
    assert classify(.9, score, evidence) == "LIKELY_ACCIDENTAL"
