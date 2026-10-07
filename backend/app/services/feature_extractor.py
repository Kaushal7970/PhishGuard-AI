import ipaddress
import math
import re
from collections import Counter
from urllib.parse import urlparse

FEATURE_NAMES = [
    "url_length", "hostname_length", "path_length", "query_length",
    "dot_count", "hyphen_count", "underscore_count", "slash_count",
    "digit_count", "special_char_count", "subdomain_count", "has_https",
    "has_ip", "has_at_symbol", "has_encoded_char", "has_suspicious_port",
    "suspicious_keyword_count", "domain_entropy", "has_suspicious_tld",
]
SUSPICIOUS_KEYWORDS = {"login", "verify", "verification", "secure", "account", "update", "password", "bank", "paypal", "signin", "confirm", "billing", "wallet", "security"}
SUSPICIOUS_TLDS = {"zip", "top", "xyz", "click", "work", "gq", "tk", "ml", "cf"}


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def extract_features(url: str) -> dict[str, float]:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    labels = [part for part in hostname.split(".") if part]
    try:
        ipaddress.ip_address(hostname)
        has_ip = 1.0
    except ValueError:
        has_ip = 0.0
    tld = labels[-1].lower() if labels else ""
    keyword_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in url.lower())
    special_count = sum(1 for char in url if not char.isalnum() and char not in "._-")
    return {
        "url_length": float(len(url)),
        "hostname_length": float(len(hostname)),
        "path_length": float(len(parsed.path)),
        "query_length": float(len(parsed.query)),
        "dot_count": float(url.count(".")),
        "hyphen_count": float(url.count("-")),
        "underscore_count": float(url.count("_")),
        "slash_count": float(url.count("/")),
        "digit_count": float(sum(char.isdigit() for char in url)),
        "special_char_count": float(special_count),
        "subdomain_count": float(max(0, len(labels) - 2)),
        "has_https": float(parsed.scheme.lower() == "https"),
        "has_ip": has_ip,
        "has_at_symbol": float("@" in url),
        "has_encoded_char": float(bool(re.search(r"%[0-9a-fA-F]{2}", url))),
        "has_suspicious_port": float(parsed.port is not None and parsed.port not in {80, 443}),
        "suspicious_keyword_count": float(keyword_count),
        "domain_entropy": _entropy(hostname),
        "has_suspicious_tld": float(tld in SUSPICIOUS_TLDS),
    }


def vectorize(url: str):
    import numpy as np
    features = extract_features(url)
    return np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float32)


def indicators(url: str) -> list[str]:
    values = extract_features(url)
    result: list[str] = []
    if not values["has_https"]:
        result.append("Uses HTTP instead of HTTPS")
    if values["has_ip"]:
        result.append("Uses an IP address instead of a domain")
    if values["has_at_symbol"]:
        result.append("Contains an @ symbol")
    if values["has_encoded_char"]:
        result.append("Contains encoded characters")
    if values["has_suspicious_port"]:
        result.append("Uses a non-standard port")
    if values["suspicious_keyword_count"]:
        result.append("Contains a suspicious security-related keyword")
    if values["subdomain_count"] >= 3:
        result.append("Contains multiple subdomains")
    if values["url_length"] >= 100:
        result.append("Unusually long URL")
    if values["has_suspicious_tld"]:
        result.append("Uses a TLD commonly seen in suspicious URLs")
    return result
