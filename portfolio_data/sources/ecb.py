"""BCE Data Portal — sans clé. Réutilisation libre, source « BCE » à citer.
Doc : https://data.ecb.europa.eu/help/api/overview
Format utilisé : csvdata + detail=dataonly ; colonnes vues :
KEY, FREQ, REF_AREA, ..., TIME_PERIOD, OBS_VALUE."""
import csv
import io

from ..http import SourceError, get
from . import point

NAME = "BCE"
ATTRIBUTION = "Source : BCE"
BASE = "https://data-api.ecb.europa.eu/service/data/"


def _rows(series, last=1):
    text = get(BASE + series, {"lastNObservations": last, "format": "csvdata", "detail": "dataonly"})
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "OBS_VALUE" not in rows[0] or "TIME_PERIOD" not in rows[0]:
        raise SourceError("colonnes TIME_PERIOD/OBS_VALUE absentes")
    return [r for r in rows if r["OBS_VALUE"] not in ("", "NaN")]


def deposit_rate():
    """Taux de la facilité de dépôt (quotidien)."""
    rows = _rows("FM/D.U2.EUR.4F.KR.DFR.LEV")
    if not rows:
        raise SourceError("aucune observation")
    r = rows[-1]
    return {"ECB_DFR": point(r["OBS_VALUE"], "%", r["TIME_PERIOD"], "BCE — taux de dépôt")}


def euro_aaa_10y_daily():
    """Courbe zone euro AAA, maturité 10 ans (quotidien, jours ouvrés)."""
    rows = _rows("YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y")
    if not rows:
        raise SourceError("aucune observation")
    r = rows[-1]
    return {"Y10_EA_AAA": point(round(float(r["OBS_VALUE"]), 3), "%", r["TIME_PERIOD"], "10 ans zone euro AAA (quotidien)")}
