import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.feature_extractor import extract_features, indicators


def test_https_url_features():
    values = extract_features("https://example.com")
    assert values["has_https"] == 1
    assert values["has_ip"] == 0


def test_suspicious_url_indicators():
    values = extract_features("http://192.168.0.1/login@verify.xyz")
    assert values["has_ip"] == 1
    assert values["has_at_symbol"] == 1
    assert indicators("http://192.168.0.1/login@verify.xyz")
