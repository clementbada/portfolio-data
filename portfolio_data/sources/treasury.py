"""US Treasury — courbe des taux quotidienne (flux XML), sans clé, domaine public.
Champs vus dans chaque <entry> : d:NEW_DATE (2026-10-23T00:00:00), d:BC_10YEAR (5.00), etc.
⚠️ Mesuré à ~20 s lors des tests : avec le plafond de 8 s, ce secours échoue souvent."""
import datetime as dt
import re

from ..http import SourceError, get
from . import point

NAME = "US Treasury"
ATTRIBUTION = "Source : US Department of the Treasury"
URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"


def us_10y(today=None):
    today = today or dt.date.today()
    month = today.strftime("%Y%m")
    text = get(URL, {"data": "daily_treasury_yield_curve", "field_tdr_date_value_month": month})
    pairs = re.findall(r"<d:NEW_DATE[^>]*>([\d-]+)T[^<]*</d:NEW_DATE>.*?<d:BC_10YEAR[^>]*>([\d.]+)</d:BC_10YEAR>", text, re.S)
    if not pairs:
        raise SourceError("aucune entrée NEW_DATE/BC_10YEAR ce mois-ci")
    date, val = max(pairs)
    return {"Y10_US": point(val, "%", date, "10 ans US (Treasury)")}
