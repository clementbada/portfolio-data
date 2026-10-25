"""MarketAux — actualités reliées aux tickers. Clé gratuite (variable MARKETAUX_API_KEY),
100 requêtes/jour, 3 articles par requête sur le plan gratuit.
Réponse vue : {"meta": {...}, "data": [{"uuid", "title", "description", "url",
"published_at", "source", "language", "entities": [{"symbol", "name",
"sentiment_score", ...}], ...}]}"""
import os

from ..http import SourceError, get_json

NAME = "MarketAux"
ATTRIBUTION = "Actualités : MarketAux"
URL = "https://api.marketaux.com/v1/news/all"


def news_for_symbol(symbol, key=None):
    key = key or os.environ.get("MARKETAUX_API_KEY")
    if not key:
        raise SourceError("MARKETAUX_API_KEY absente")
    j = get_json(URL, {"symbols": symbol, "filter_entities": "true", "must_have_entities": "true",
                       "language": "en,fr", "api_token": key})
    if "data" not in j:
        raise SourceError(f"champ data absent : {j.get('error')}")
    out = []
    for a in j["data"]:
        ent = next((e for e in a.get("entities") or [] if e.get("symbol") == symbol), {})
        if a.get("title") and a.get("url"):
            out.append({"title": a["title"].strip(), "url": a["url"],
                        "published": (a.get("published_at") or "")[:19] + "Z" if a.get("published_at") else None,
                        "source": a.get("source"), "symbol": symbol,
                        "sentiment": ent.get("sentiment_score")})
    return out


def portfolio_news(symbols_by_envelope):
    """Une requête par ligne ; une ligne en échec n'empêche pas les autres."""
    out, errors, calls = [], [], 0
    for env, symbols in symbols_by_envelope.items():
        for s in symbols:
            calls += 1
            try:
                for a in news_for_symbol(s):
                    out.append({**a, "envelope": env})
            except SourceError as e:
                errors.append(f"{s} : {e}")
    if calls and len(errors) == calls:
        raise SourceError(f"toutes les lignes en échec ({errors[0]})")
    out.sort(key=lambda a: a["published"] or "", reverse=True)
    return out
