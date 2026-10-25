"""Orchestrateur : pour chaque jeu de données, essaie la source principale puis
la ou les sources de secours ; si toutes échouent, garde la dernière valeur
connue avec son heure et un message clair. Écrit :

  data/latest.json  — format stable lu par le dashboard / la tâche planifiée
  data/latest.csv   — export tabulaire des séries chiffrées
  data/summary.md   — résumé court en français (notification, réponse d'agent)

Usage : python -m portfolio_data.fetch [--force]
"""
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

from .http import SourceError
from .sources import bls, currencyapi, ecb, eurostat, frankfurter, rss, treasury

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LATEST = DATA / "latest.json"

H = 3600
# nom : (fraîcheur visée en secondes, [(nom de source, mention, fonction), ...] dans l'ordre de préférence)
DATASETS = {
    "fx_eur": (20 * H, [
        (frankfurter.NAME, frankfurter.ATTRIBUTION, frankfurter.fx_eur),
        (currencyapi.NAME, currencyapi.ATTRIBUTION, currencyapi.fx_eur),
    ]),
    "ecb_deposit_rate": (20 * H, [(ecb.NAME, ecb.ATTRIBUTION, ecb.deposit_rate)]),
    "yields_10y_eu_monthly": (20 * H, [(ecb.NAME, ecb.ATTRIBUTION, ecb.yields_10y_monthly)]),
    "yield_10y_ea_aaa_daily": (20 * H, [(ecb.NAME, ecb.ATTRIBUTION, ecb.euro_aaa_10y_daily)]),
    # FRED (principale) sera insérée en tête une fois la clé créée et la réponse vérifiée.
    "yield_10y_us": (20 * H, [(treasury.NAME, treasury.ATTRIBUTION, treasury.us_10y)]),
    "inflation_eu": (20 * H, [(eurostat.NAME, eurostat.ATTRIBUTION, eurostat.hicp_yoy)]),
    "unemployment_eu": (20 * H, [(eurostat.NAME, eurostat.ATTRIBUTION, eurostat.unemployment)]),
    "inflation_us": (20 * H, [(bls.NAME, bls.ATTRIBUTION, bls.us_cpi_yoy)]),
    "unemployment_us": (20 * H, [(bls.NAME, bls.ATTRIBUTION, bls.us_unemployment)]),
    "news_bce": (6 * H, [("RSS BCE", rss.ATTRIBUTION, lambda: rss.central_bank_news("BCE"))]),
    "news_fed": (6 * H, [("RSS Fed", rss.ATTRIBUTION, lambda: rss.central_bank_news("Fed"))]),
    "news_boe": (6 * H, [("RSS BoE", rss.ATTRIBUTION, lambda: rss.central_bank_news("BoE"))]),
}


def _now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def load_previous(path=LATEST):
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("datasets", {})
    except (FileNotFoundError, ValueError):
        return {}


def refresh_dataset(name, ttl, providers, prev, force=False, now=None):
    now = now or _now()
    # 1. Cache : une valeur réussie encore fraîche n'est pas redemandée.
    if (not force and prev and prev.get("status") in ("ok", "secours")
            and prev.get("fetched_at") and (now - _parse(prev["fetched_at"])).total_seconds() < ttl):
        return {**prev, "from_cache": True}
    # 2. Principale, puis secours.
    errors = []
    for i, (src, attribution, fn) in enumerate(providers):
        try:
            data = fn()
            return {"status": "ok" if i == 0 else "secours", "provider": src, "attribution": attribution,
                    "fetched_at": _iso(now), "from_cache": False, "data": data,
                    "message": None if i == 0 else f"Source principale indisponible ({errors[0]}), relais : {src}",
                    "errors": errors}
        except SourceError as e:
            errors.append(f"{src} : {e}")
        except Exception as e:  # format inattendu : on ne casse jamais la sortie
            errors.append(f"{src} : erreur inattendue {type(e).__name__}: {e}")
    # 3. Toutes les sources ont échoué : dernière valeur connue.
    if prev and prev.get("data") is not None:
        since = prev.get("last_success_at") or prev.get("fetched_at")
        return {**prev, "status": "ancienne valeur", "from_cache": False, "last_success_at": since,
                "message": f"Sources indisponibles — dernière valeur connue du {since}", "errors": errors}
    return {"status": "indisponible", "provider": None, "attribution": None, "fetched_at": None,
            "from_cache": False, "data": None, "message": "Aucune source disponible et aucune valeur antérieure",
            "errors": errors}


def write_csv(datasets, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["jeu", "cle", "libelle", "valeur", "unite", "date_donnee", "source", "statut", "recupere_le"])
        for name, d in datasets.items():
            if isinstance(d.get("data"), dict):
                for k, p in d["data"].items():
                    w.writerow([name, k, p["label"], p["value"], p["unit"], p["as_of"], d["provider"], d["status"], d["fetched_at"]])


def summary_md(datasets, generated_at):
    def val(ds, key, fmt="{:.2f}"):
        p = (datasets.get(ds, {}).get("data") or {}).get(key)
        return f"{fmt.format(p['value'])} {p['unit']} ({p['as_of']})" if p else "n.d."
    lines = [f"# Point marchés — {generated_at[:10]}", "",
             f"- EUR/USD : {val('fx_eur', 'EURUSD', '{:.4f}')}",
             f"- Taux de dépôt BCE : {val('ecb_deposit_rate', 'ECB_DFR')}",
             f"- 10 ans US : {val('yield_10y_us', 'Y10_US')} · zone euro AAA : {val('yield_10y_ea_aaa_daily', 'Y10_EA_AAA')}",
             "- 10 ans (moy. mensuelle) : " + " · ".join(f"{c} {val('yields_10y_eu_monthly', 'Y10_' + c)}" for c in ("FR", "DE", "IT", "ES")),
             "- Inflation : " + " · ".join(f"{c} {val('inflation_eu', 'HICP_' + c, '{:.1f}')}" for c in ("EA", "FR")) + f" · US {val('inflation_us', 'CPI_US', '{:.1f}')}",
             ""]
    alerts = [f"- ⚠️ {n} : {d['message']}" for n, d in datasets.items() if d.get("status") not in ("ok",) and d.get("message")]
    if alerts:
        lines += ["## Sources dégradées", *alerts, ""]
    news = sorted((a for n in ("news_bce", "news_fed", "news_boe") for a in (datasets.get(n, {}).get("data") or [])),
                  key=lambda a: a["published"] or "", reverse=True)[:6]
    if news:
        lines += ["## Derniers communiqués", *[f"- [{a['source']}] {a['title']} ({(a['published'] or '')[:10]})" for a in news], ""]
    return "\n".join(lines)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    force = "--force" in argv
    prev = load_previous()
    now = _now()
    out = {}
    for name, (ttl, providers) in DATASETS.items():
        out[name] = refresh_dataset(name, ttl, providers, prev.get(name), force, now)
        d = out[name]
        if d["status"] in ("ok", "secours") and not d.get("from_cache"):
            d["last_success_at"] = d["fetched_at"]
        print(f"{name:26} {d['status']:16} {d.get('provider') or '-':14} {'(cache)' if d.get('from_cache') else ''} "
              f"{'; '.join(d.get('errors') or [])}", file=sys.stderr)
    DATA.mkdir(exist_ok=True)
    doc = {"schema_version": 1, "generated_at": _iso(now), "datasets": out}
    LATEST.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    write_csv(out, DATA / "latest.csv")
    (DATA / "summary.md").write_text(summary_md(out, doc["generated_at"]), encoding="utf-8")
    bad = [n for n, d in out.items() if d["status"] == "indisponible"]
    return 1 if bad and os.environ.get("FAIL_ON_UNAVAILABLE") else 0


if __name__ == "__main__":
    sys.exit(main())
