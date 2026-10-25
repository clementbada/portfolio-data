"""Frankfurter — taux de change de référence (BCE), sans clé, sans quota.
Doc : https://frankfurter.dev — Réponse vue : {"amount", "base", "date", "rates": {"USD": ...}}"""
from ..http import SourceError, get_json
from . import point

NAME = "Frankfurter"
ATTRIBUTION = "Données : Frankfurter (taux de référence BCE)"
URL = "https://api.frankfurter.dev/v1/latest"
PAIRS = ("USD", "GBP", "JPY", "CHF")


def fx_eur(pairs=PAIRS):
    j = get_json(URL, {"base": "EUR", "symbols": ",".join(pairs)})
    rates, as_of = j.get("rates"), j.get("date")
    if not isinstance(rates, dict) or not as_of:
        raise SourceError("champs rates/date absents")
    out = {}
    for cur in pairs:
        if cur not in rates:
            raise SourceError(f"devise {cur} absente")
        out[f"EUR{cur}"] = point(rates[cur], cur, as_of, f"1 EUR en {cur}")
    return out
