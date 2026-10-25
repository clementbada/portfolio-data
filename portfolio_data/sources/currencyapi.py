"""Currency-api (fawazahmed0/exchange-api) — sans clé, sans quota, licence CC0.
Adresse principale jsDelivr, miroir Cloudflare Pages.
Réponse vue : {"date": "YYYY-MM-DD", "eur": {"usd": 1.12, ...}} (codes en minuscules)."""
from ..http import SourceError, get_json
from . import point

NAME = "Currency-api"
ATTRIBUTION = "Données : Currency-api (fawazahmed0)"
URLS = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.min.json",
    "https://latest.currency-api.pages.dev/v1/currencies/eur.min.json",
)
PAIRS = ("USD", "GBP", "JPY", "CHF")


def fx_eur(pairs=PAIRS):
    last_err = None
    for url in URLS:
        try:
            j = get_json(url)
            break
        except SourceError as e:
            last_err = e
    else:
        raise last_err
    rates, as_of = j.get("eur"), j.get("date")
    if not isinstance(rates, dict) or not as_of:
        raise SourceError("champs eur/date absents")
    out = {}
    for cur in pairs:
        v = rates.get(cur.lower())
        if v is None:
            raise SourceError(f"devise {cur} absente")
        out[f"EUR{cur}"] = point(v, cur, as_of, f"1 EUR en {cur}")
    return out
