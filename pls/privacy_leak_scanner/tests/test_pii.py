from scanner.pii import detect

def test_detects_common_signals():
    hits = detect("Email a.person@example.gov.in and PAN ABCDE1234F")
    assert {h["kind"] for h in hits} >= {"email", "pan_like"}
    assert all("*" in h["masked"] for h in hits)
