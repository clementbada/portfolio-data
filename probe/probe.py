"""Sonde de phase 2 : appelle chaque API candidate avec un exemple réaliste
et enregistre code HTTP, temps de réponse, en-têtes de limite et un extrait.

Bibliothèque standard uniquement. Aucune clé : les API à clé sont testées
avec leur clé de démonstration publique (quand elle existe) ou sans clé,
pour vérifier qu'elles répondent et ce qu'elles exigent.

Usage : python probe/probe.py > probe_results.json
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

UA = "portfolio-data-probe/0.1 (+https://github.com/clementbada/portfolio-data)"
TIMEOUT = 8

CANDIDATES = [
    # --- Besoin A : change EUR/USD (secours d'IBKR) ---
    ("fx", "Frankfurter", "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP,JPY,CHF"),
    ("fx", "Frankfurter (ancien domaine)", "https://api.frankfurter.app/latest?from=EUR&to=USD"),
    ("fx", "Currency-api (fawazahmed0)", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.json"),
    ("fx", "Currency-api miroir", "https://latest.currency-api.pages.dev/v1/currencies/eur.json"),
    ("fx", "VATComply", "https://api.vatcomply.com/rates?base=EUR"),
    ("fx", "Exchangerate.dev", "https://api.exchangerate.dev/latest?base=EUR&symbols=USD"),
    ("fx", "FreeForexAPI", "https://www.freeforexapi.com/api/live?pairs=EURUSD"),
    # --- Besoin B : clôture quotidienne indices / actions (secours d'IBKR) ---
    ("eq", "Alpha Vantage (clé demo)", "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo"),
    ("eq", "Twelve Data (clé demo)", "https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&outputsize=2&apikey=demo"),
    ("eq", "EODHD (clé demo)", "https://eodhd.com/api/eod/AAPL.US?api_token=demo&fmt=json&order=d&from=2026-10-15"),
    ("eq", "Financial Modeling Prep (sans clé)", "https://financialmodelingprep.com/stable/quote?symbol=AAPL"),
    ("eq", "Finnhub (sans clé)", "https://finnhub.io/api/v1/quote?symbol=AAPL"),
    ("eq", "Marketstack (sans clé)", "https://api.marketstack.com/v2/eod/latest?symbols=AAPL"),
    # --- Besoin C : taux, obligations, inflation ---
    ("rates", "BCE Data Portal - taux de dépôt (hors annuaire)", "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=1&format=jsondata"),
    ("rates", "BCE Data Portal - 10 ans FR/DE/IT/ES mensuel (hors annuaire)", "https://data-api.ecb.europa.eu/service/data/IRS/M.FR+DE+IT+ES.L.L40.CI.0000.EUR.N.Z?lastNObservations=1&format=csvdata"),
    ("rates", "BCE Data Portal - courbe AAA 10 ans quotidienne (hors annuaire)", "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?lastNObservations=1&format=csvdata"),
    ("rates", "BCE Data Portal - HICP zone euro (hors annuaire)", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR?lastNObservations=1&format=csvdata"),
    ("rates", "US Treasury - courbe des taux (hors annuaire, même éditeur que Fed Treasury)", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&page&_format=csv"),
    ("rates", "Fed Treasury (fiscaldata) - taux moyens", "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?sort=-record_date&page%5Bsize%5D=2"),
    ("rates", "BLS - CPI US (v1 sans clé)", "https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0"),
    ("rates", "Econdb - 10 ans US", "https://www.econdb.com/api/series/Y10YDUS/?format=json"),
    ("rates", "Eurostat - HICP par pays (hors annuaire)", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=FR&geo=DE&geo=IT&geo=ES&coicop=CP00&lastTimePeriod=1"),
    ("rates", "FRED (sans clé)", "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&file_type=json&limit=1&sort_order=desc"),
    # --- Besoin D : actualités ---
    ("news", "GDELT DOC 2.0 (hors annuaire)", "https://api.gdeltproject.org/api/v2/doc/doc?query=%22European%20Central%20Bank%22%20sourcelang:french&mode=artlist&format=json&maxrecords=3&sort=datedesc&timespan=1d"),
    ("news", "Noozra", "https://noozra.com/api"),
    ("news", "BCE - flux RSS communiqués (hors annuaire)", "https://www.ecb.europa.eu/rss/press.html"),
    ("news", "Fed - flux RSS communiqués (hors annuaire)", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("news", "MarketAux (sans clé)", "https://api.marketaux.com/v1/news/all?symbols=AAPL&language=en"),
    ("news", "GNews (sans clé)", "https://gnews.io/api/v4/search?q=ECB&lang=fr"),
    ("news", "NewsData (sans clé)", "https://newsdata.io/api/1/latest?q=ECB&language=fr"),
    ("news", "TheNews (sans clé)", "https://api.thenewsapi.com/v1/news/all?search=ECB&language=fr"),
    ("news", "Currents (sans clé)", "https://api.currentsapi.services/v1/search?keywords=ECB&language=fr"),
]

# Second passage : extraction des valeurs utiles et nouvelles tentatives.
ROUND2 = [
    ("rates", "BCE taux de dépôt (csv)", "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=1&format=csvdata&detail=dataonly"),
    ("rates", "BCE 10 ans FR/DE/IT/ES mensuel (csv)", "https://data-api.ecb.europa.eu/service/data/IRS/M.FR+DE+IT+ES.L.L40.CI.0000.EUR.N.Z?lastNObservations=1&format=csvdata&detail=dataonly"),
    ("rates", "BCE courbe AAA 10 ans quotidienne (csv)", "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?lastNObservations=2&format=csvdata&detail=dataonly"),
    ("rates", "BCE courbe toutes notations 10 ans quotidienne (csv)", "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y?lastNObservations=1&format=csvdata&detail=dataonly"),
    ("rates", "BCE HICP zone euro + pays (csv)", "https://data-api.ecb.europa.eu/service/data/ICP/M.U2+FR+DE+IT+ES.N.000000.4.ANR?lastNObservations=1&format=csvdata&detail=dataonly"),
    ("rates", "Eurostat HICP prc_hicp_manr (2 dernières périodes)", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=FR&geo=EA&coicop=CP00&lastTimePeriod=2"),
    ("rates", "Eurostat HICP prc_hicp_minr (nouveau jeu 2026)", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?geo=FR&geo=EA&coicop18=TOTAL&lastTimePeriod=2"),
    ("rates", "Eurostat chômage une_rt_m", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=FR&geo=ES&geo=IT&geo=EA20&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&lastTimePeriod=1"),
    ("rates", "US Treasury courbe des taux XML (oct. 2026)", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=202610"),
    ("rates", "BLS CPI + chômage US (v1)", "https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000"),
    ("rates", "Alpha Vantage TREASURY_YIELD (clé demo)", "https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey=demo"),
    ("news", "GDELT DOC 2.0 (FR, BCE)", "https://api.gdeltproject.org/api/v2/doc/doc?query=%22BCE%22%20sourcelang:french&mode=artlist&format=json&maxrecords=3&sort=datedesc&timespan=1d"),
    ("news", "GDELT DOC 2.0 (EN, Palantir)", "https://api.gdeltproject.org/api/v2/doc/doc?query=Palantir%20sourcelang:english&mode=artlist&format=json&maxrecords=3&sort=datedesc&timespan=1d"),
    ("news", "Noozra API (feed)", "https://noozra.com/api/headlines?category=business"),
    ("news", "Banque de France RSS", "https://www.banque-france.fr/fr/rss.xml"),
    ("news", "Bank of England RSS", "https://www.bankofengland.co.uk/rss/news"),
    ("news", "SEC EDGAR - dépôts PLTR (User-Agent exigé)", "https://data.sec.gov/submissions/CIK0001321655.json"),
    ("eq", "Twelve Data indice (clé demo, SPX)", "https://api.twelvedata.com/time_series?symbol=SPX&interval=1day&outputsize=1&apikey=demo"),
    ("eq", "EODHD indice CAC 40 (clé demo)", "https://eodhd.com/api/eod/FCHI.INDX?api_token=demo&fmt=json&order=d&from=2026-10-20"),
]

# Troisième passage : réponses complètes (pour écrire les parseurs sur du vu).
ROUND3 = [
    ("fx", "currencyapi_eur", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.min.json"),
    ("rates", "eurostat_hicp_minr", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr?geo=EA&geo=FR&geo=DE&geo=IT&geo=ES&coicop18=TOTAL&lastTimePeriod=1"),
    ("rates", "eurostat_une_EA20", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EA20&geo=FR&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&lastTimePeriod=1"),
    ("rates", "eurostat_une_EA21", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EA21&geo=EA&geo=FR&geo=DE&geo=IT&geo=ES&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT&lastTimePeriod=1"),
    ("rates", "treasury_xml", "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=202610"),
    ("rates", "bls_cpi", "https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0"),
    ("news", "rss_ecb", "https://www.ecb.europa.eu/rss/press.html"),
    ("news", "rss_fed", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("news", "rss_boe", "https://www.bankofengland.co.uk/rss/news"),
    ("news", "gdelt", "https://api.gdeltproject.org/api/v2/doc/doc?query=(%22BCE%22%20OR%20%22ECB%22)&mode=artlist&format=json&maxrecords=5&sort=datedesc&timespan=2d"),
]

# Passage MarketAux : clé lue dans l'environnement, jamais écrite dans les résultats.
def marketaux_batch():
    import os
    key = os.environ.get("MARKETAUX_API_KEY", "")
    if not key:
        return [("news", "marketaux_sans_cle", "https://api.marketaux.com/v1/news/all?symbols=PLTR&language=en")]
    base = "https://api.marketaux.com/v1/news/all?filter_entities=true&must_have_entities=true&language=en,fr&api_token=" + key
    return [
        ("news", "marketaux_portefeuille", base + "&symbols=PLTR,MRNA,OKLO,TSLA,GOOGL"),
        ("news", "marketaux_pea", base.replace("api_token", "countries=fr,de,it&api_token") + "&symbols=AI.PA,PRY.MI,ENR.DE"),
    ]


LIMIT_HEADERS = ("ratelimit", "rate-limit", "x-ratelimit", "retry-after", "x-ratelimit-remaining", "x-ratelimit-limit")


def probe(url, full=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(200_000)
            code, headers = r.status, r.headers
    except urllib.error.HTTPError as e:
        body = e.read(5000) if e.fp else b""
        code, headers = e.code, e.headers
    except Exception as e:  # timeout, DNS, TLS...
        return {"code": None, "ms": round((time.monotonic() - t0) * 1000), "error": f"{type(e).__name__}: {e}"}
    ms = round((time.monotonic() - t0) * 1000)
    text = body.decode("utf-8", "replace")
    limits = {k: v for k, v in (headers.items() if headers else []) if any(h in k.lower() for h in LIMIT_HEADERS)}
    return {
        "code": code,
        "ms": ms,
        "bytes": len(body),
        "content_type": headers.get("Content-Type") if headers else None,
        "limit_headers": limits,
        "excerpt": " ".join(text.split())[:600],
        **({"body": text[:150_000]} if full else {}),
    }


def main():
    global TIMEOUT
    out = []
    batch = CANDIDATES
    if len(sys.argv) > 1 and sys.argv[1] == "round2":
        batch, TIMEOUT = ROUND2, 25  # délai long uniquement pour la sonde, pas pour la prod (8 s)
    full = len(sys.argv) > 1 and sys.argv[1] == "round3"
    if full:
        batch, TIMEOUT = ROUND3, 25
    if len(sys.argv) > 1 and sys.argv[1] == "marketaux":
        batch, TIMEOUT, full = marketaux_batch(), 15, True
    for need, name, url in batch:
        if full and name == "gdelt":
            time.sleep(6)  # GDELT : une requête toutes les 5 s maximum
        res = probe(url, full=full)
        res.update({"need": need, "name": name, "url": re.sub(r"api_token=[^&]+", "api_token=***", url)})
        out.append(res)
        print(f"{need:6} {str(res.get('code')):5} {res['ms']:6} ms  {name}", file=sys.stderr)
    json.dump({"run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": out}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
