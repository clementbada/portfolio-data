"""Appels HTTP communs : délai maximum de 8 secondes, User-Agent explicite,
erreurs normalisées. Bibliothèque standard uniquement."""
import json
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_S = 8
USER_AGENT = "portfolio-data/1.0 (+https://github.com/clementbada/portfolio-data)"


class SourceError(Exception):
    """Une source n'a pas répondu correctement (réseau, code HTTP, format)."""


def get(url, params=None, timeout=TIMEOUT_S, headers=None):
    """Renvoie le corps de la réponse en texte, ou lève SourceError."""
    if params:
        url = f"{url}{'&' if '?' in url else '?'}{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise SourceError(f"HTTP {e.code}") from None
    except Exception as e:  # délai dépassé, DNS, TLS...
        raise SourceError(f"{type(e).__name__}: {e}") from None


def get_json(url, params=None, timeout=TIMEOUT_S, headers=None):
    text = get(url, params, timeout, headers)
    try:
        return json.loads(text)
    except ValueError:
        raise SourceError("réponse non JSON") from None


def redact(url):
    """Retire les clés d'une URL avant de la journaliser."""
    parts = urllib.parse.urlsplit(url)
    q = [(k, "***" if "key" in k.lower() or "token" in k.lower() else v)
         for k, v in urllib.parse.parse_qsl(parts.query)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))
