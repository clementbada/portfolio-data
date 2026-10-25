"""Eurostat (API de diffusion, JSON-stat 2.0) — sans clé. Source « Eurostat » à citer.
Structure vue : "id" (ordre des dimensions), "size", "dimension"[dim]["category"]["index"],
"value" = dict {position aplatie: valeur}, positions absentes = pas de donnée."""
from ..http import SourceError, get_json
from . import point

NAME = "Eurostat"
ATTRIBUTION = "Source : Eurostat"
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
# EA = zone euro dans sa composition courante (EA21 depuis 2026, vu dans le libellé).
GEOS = ("EA", "FR", "DE", "IT", "ES")


def _cells(j):
    """Itère sur (coordonnées {dim: code}, valeur) d'un jeu JSON-stat."""
    dims, sizes, values = j.get("id"), j.get("size"), j.get("value")
    if not dims or not sizes or values is None:
        raise SourceError("structure JSON-stat inattendue")
    codes = []
    for d in dims:
        idx = j["dimension"][d]["category"]["index"]
        codes.append(sorted(idx, key=idx.get))
    for pos_str, v in values.items():
        pos, coords = int(pos_str), {}
        for d, size, cl in zip(reversed(dims), reversed(sizes), reversed(codes)):
            coords[d] = cl[pos % size]
            pos //= size
        yield coords, v


def hicp_yoy(geos=GEOS):
    """Inflation IPCH sur un an (jeu prc_hicp_minr, ECOICOP v2, depuis 2026)."""
    j = get_json(BASE + "prc_hicp_minr", {"geo": list(geos), "coicop18": "TOTAL", "unit": "RCH_A", "lastTimePeriod": 1})
    out = {}
    for c, v in _cells(j):
        out[f"HICP_{c['geo']}"] = point(v, "% a/a", c["time"], f"Inflation IPCH {c['geo']}")
    if not out:
        raise SourceError("aucune valeur")
    return out


def unemployment(geos=("EA21", "FR", "DE", "IT", "ES")):
    """Taux de chômage CVS : dernier mois renseigné par pays (le mois le plus
    récent peut être listé sans valeur)."""
    j = get_json(BASE + "une_rt_m", {"geo": list(geos), "s_adj": "SA", "age": "TOTAL", "sex": "T",
                                     "unit": "PC_ACT", "lastTimePeriod": 4})
    best = {}
    for c, v in _cells(j):
        if v is None:
            continue
        g = "EA" if c["geo"].startswith("EA") else c["geo"]
        if g not in best or c["time"] > best[g]["as_of"]:
            best[g] = point(v, "%", c["time"], f"Chômage {g}")
    if not best:
        raise SourceError("aucune valeur sur les 4 derniers mois")
    return {f"UNEMP_{g}": p for g, p in best.items()}
