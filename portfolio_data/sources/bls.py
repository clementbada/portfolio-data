"""Bureau of Labor Statistics, API v1 — sans clé (25 requêtes/jour), domaine public.
Réponse vue : Results.series[0].data = [{"year", "period": "M09", "value": "336.940"}, ...]
Certaines valeurs valent "-" (mois non publiés, ex. octobre 2025)."""
from ..http import SourceError, get_json
from . import point

NAME = "BLS"
ATTRIBUTION = "Source : U.S. Bureau of Labor Statistics"
URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"


def _series(series_id):
    j = get_json(URL + series_id)
    if j.get("status") != "REQUEST_SUCCEEDED":
        raise SourceError(f"statut BLS : {j.get('status')} {j.get('message')}")
    data = j["Results"]["series"][0]["data"]
    out = {}
    for d in data:
        if d.get("period", "").startswith("M") and d.get("value") not in (None, "-"):
            out[(int(d["year"]), int(d["period"][1:]))] = float(d["value"])
    if not out:
        raise SourceError("aucune observation")
    return out


def us_cpi_yoy():
    """Inflation CPI-U (non CVS) sur un an, calculée depuis l'indice."""
    s = _series("CUUR0000SA0")
    (y, m) = max(s)
    prev = s.get((y - 1, m))
    if prev is None:
        raise SourceError(f"indice de {m:02d}/{y - 1} absent, glissement annuel impossible")
    return {"CPI_US": point(round((s[(y, m)] / prev - 1) * 100, 1), "% a/a", f"{y}-{m:02d}", "Inflation CPI US")}


def us_unemployment():
    s = _series("LNS14000000")
    (y, m) = max(s)
    return {"UNEMP_US": point(s[(y, m)], "%", f"{y}-{m:02d}", "Chômage US")}
