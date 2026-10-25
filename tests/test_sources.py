"""Un test par source : appelle la VRAIE API et vérifie que les champs utilisés
existent toujours. Lancé par GitHub Actions (le réseau de l'espace de travail
de Claude ne joint pas ces sites).

    python -m unittest tests.test_sources -v
"""
import re
import time
import unittest

import os

from portfolio_data.config import NEWS_SYMBOLS
from portfolio_data.sources import bls, currencyapi, ecb, eurostat, frankfurter, marketaux, rss
from portfolio_data.http import SourceError

DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


class Shape:
    def check_points(self, out, keys, lo, hi):
        for k in keys:
            self.assertIn(k, out)
            p = out[k]
            self.assertEqual(set(p), {"value", "unit", "as_of", "label"})
            self.assertRegex(p["as_of"], DATE)
            self.assertTrue(lo <= p["value"] <= hi, f"{k} = {p['value']} hors de [{lo}, {hi}]")


class FX(unittest.TestCase, Shape):
    def test_frankfurter(self):
        self.check_points(frankfurter.fx_eur(), ["EURUSD", "EURGBP", "EURJPY", "EURCHF"], 0.3, 400)

    def test_currencyapi(self):
        self.check_points(currencyapi.fx_eur(), ["EURUSD", "EURGBP", "EURJPY", "EURCHF"], 0.3, 400)


class Rates(unittest.TestCase, Shape):
    def test_ecb_deposit(self):
        self.check_points(ecb.deposit_rate(), ["ECB_DFR"], -1, 10)

    def test_ecb_aaa_daily(self):
        self.check_points(ecb.euro_aaa_10y_daily(), ["Y10_EA_AAA"], -1, 15)


class Inflation(unittest.TestCase, Shape):
    def test_eurostat_hicp(self):
        self.check_points(eurostat.hicp_yoy(), ["HICP_EA", "HICP_FR", "HICP_DE", "HICP_IT", "HICP_ES"], -5, 30)

    def test_eurostat_unemployment(self):
        out = eurostat.unemployment()
        self.check_points(out, ["UNEMP_FR"], 0, 40)

    def test_bls_cpi(self):
        self.check_points(bls.us_cpi_yoy(), ["CPI_US"], -5, 30)

    def test_bls_unemployment(self):
        time.sleep(1)
        self.check_points(bls.us_unemployment(), ["UNEMP_US"], 0, 40)


class News(unittest.TestCase):
    def _check(self, bank):
        items = rss.central_bank_news(bank)
        self.assertGreater(len(items), 0)
        for a in items:
            self.assertEqual(set(a), {"title", "url", "published", "source"})
            self.assertTrue(a["url"].startswith("https://"))
            self.assertNotIn("europa.eu//", a["url"])

    def test_rss_bce(self):
        self._check("BCE")

    def test_rss_fed(self):
        self._check("Fed")

    def test_rss_boe(self):
        self._check("BoE")


class PortfolioNews(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("MARKETAUX_API_KEY"), "MARKETAUX_API_KEY absente")
    def test_marketaux_une_ligne(self):
        items = marketaux.news_for_symbol("PLTR")
        self.assertIsInstance(items, list)
        for a in items:
            self.assertTrue({"title", "url", "published", "source", "symbol", "sentiment"} <= set(a))
            self.assertEqual(a["symbol"], "PLTR")

    def test_config(self):
        self.assertEqual(sum(len(v) for v in NEWS_SYMBOLS.values()), 16)


if __name__ == "__main__":
    unittest.main()
