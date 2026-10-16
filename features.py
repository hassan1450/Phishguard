import math
import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update", "bank", "signin",
                    "confirm", "password", "paypal", "webscr", "ebay", "wallet", "support",
                    "bonus", "free"]
SHORTENERS = ("bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
              "buff.ly", "rebrand.ly", "cutt.ly")
IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def normalize_url(url):
    url = str(url).strip()
    return url if SCHEME_RE.match(url) else "http://" + url


def _entropy(text):
    if not text:
        return 0.0
    return -sum((text.count(c) / len(text)) * math.log2(text.count(c) / len(text))
                for c in set(text))


def parse_parts(url):
    full = normalize_url(url)
    host = path = query = scheme = ""
    has_port = 0
    try:
        p = urlparse(full)
        host = (p.hostname or "").lower()
        path = p.path or ""
        query = p.query or ""
        scheme = (p.scheme or "http").lower()

        netloc = p.netloc or ""
        if "@" in netloc:
            netloc = netloc.rsplit("@", 1)[1]
        if "[" in netloc and "]" in netloc:
            port_part = netloc[netloc.rfind("]") + 1:]
        else:
            port_part = netloc

        try:
            p.port
        except ValueError:
            has_port = 1 if ":" in port_part else 0
        else:
            has_port = 1 if p.port is not None else 0
    except ValueError:
        # Preserve the host when there is a malformed port; avoid treating the whole
        # URL as empty because the host is still useful for detection.
        try:
            fallback = urlparse(full)
            host = (fallback.hostname or "").lower()
            path = fallback.path or ""
            query = fallback.query or ""
            scheme = (fallback.scheme or "http").lower()
        except ValueError:
            host, path, query, scheme = "", "", "", "http"
    return host, path, query, scheme, has_port


def get_host(url):
    return parse_parts(url)[0]


def extract_features(url):
    raw = str(url).strip()
    host, path, query, scheme, has_port = parse_parts(raw)
    low = raw.lower()
    parts = [x for x in host.split(".") if x]
    tld = parts[-1] if len(parts) > 1 else ""
    digits = sum(c.isdigit() for c in raw)
    letters = sum(c.isalpha() for c in raw)
    return {
        "url_length": len(raw),
        "host_length": len(host),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": raw.count("."),
        "num_hyphens": raw.count("-"),
        "num_underscores": raw.count("_"),
        "num_slashes": raw.count("/"),
        "num_digits": digits,
        "num_letters": letters,
        "digit_ratio": digits / max(len(raw), 1),
        "num_at": raw.count("@"),
        "num_question": raw.count("?"),
        "num_equals": raw.count("="),
        "num_ampersand": raw.count("&"),
        "num_percent": raw.count("%"),
        "special_chars": sum(not c.isalnum() for c in raw),
        "has_ip": 1 if IP_RE.match(host) else 0,
        "is_https": 1 if scheme == "https" else 0,
        "has_port": has_port,
        "num_subdomains": max(len(parts) - 2, 0),
        "tld_length": len(tld),
        "host_hyphens": host.count("-"),
        "host_digits": sum(c.isdigit() for c in host),
        "suspicious_words": sum(low.count(w) for w in SUSPICIOUS_WORDS),
        "is_shortener": 1 if host in SHORTENERS else 0,
        "has_punycode": 1 if "xn--" in host else 0,
        "double_slash_in_path": path.count("//"),
        "url_entropy": _entropy(raw),
        "host_entropy": _entropy(host),
    }


FEATURE_NAMES = list(extract_features("http://example.com/").keys())


def explain(f):
    """Human-readable red flags shown in the UI."""
    s = []
    if f["has_ip"]:
        s.append(("Uses a raw IP address instead of a domain name", "danger"))
    if f["num_at"]:
        s.append(("Contains '@', which can hide the real destination", "danger"))
    if f["has_punycode"]:
        s.append(("Domain uses punycode (possible look-alike characters)", "danger"))
    if f["is_shortener"]:
        s.append(("Link shortener hides the final destination", "warn"))
    if not f["is_https"]:
        s.append(("Not using HTTPS (note: HTTPS alone does not prove safety)", "warn"))
    if f["url_length"] > 75:
        s.append((f"Unusually long URL ({f['url_length']} characters)", "warn"))
    if f["num_subdomains"] >= 3:
        s.append((f"Many subdomains ({f['num_subdomains']})", "warn"))
    if f["host_hyphens"] >= 2:
        s.append(("Several hyphens in the domain name", "warn"))
    if f["suspicious_words"] >= 2:
        s.append((f"{f['suspicious_words']} suspicious keywords (login, verify, secure...)", "warn"))
    if f["digit_ratio"] > 0.25:
        s.append(("High proportion of digits in the URL", "warn"))
    if not s:
        s.append(("No strong red flags in the URL structure", "ok"))
    return [{"text": t, "level": l} for t, l in s]