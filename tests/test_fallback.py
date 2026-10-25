"""Tests hors ligne de la logique cache / secours / dernière valeur connue."""
import datetime as dt
import unittest

from portfolio_data.fetch import refresh_dataset
from portfolio_data.http import SourceError

NOW = dt.datetime(2026, 10, 26, 20, 0, tzinfo=dt.timezone.utc)
POINT = {"X": {"value": 1.0, "unit": "%", "as_of": "2026-10-26", "label": "x"}}


def ok(data=POINT):
    return lambda: data


def ko(msg="HTTP 500"):
    def f():
        raise SourceError(msg)
    return f


class FallbackTests(unittest.TestCase):
    def test_principale(self):
        r = refresh_dataset("t", 3600, [("A", "a", ok()), ("B", "b", ko())], None, now=NOW)
        self.assertEqual((r["status"], r["provider"]), ("ok", "A"))

    def test_secours(self):
        r = refresh_dataset("t", 3600, [("A", "a", ko()), ("B", "b", ok())], None, now=NOW)
        self.assertEqual((r["status"], r["provider"]), ("secours", "B"))
        self.assertIn("A : HTTP 500", r["message"])

    def test_derniere_valeur_connue(self):
        prev = {"status": "ok", "provider": "A", "fetched_at": "2026-10-20T20:00:00Z",
                "last_success_at": "2026-10-20T20:00:00Z", "data": POINT}
        r = refresh_dataset("t", 3600, [("A", "a", ko()), ("B", "b", ko("timeout"))], prev, now=NOW)
        self.assertEqual(r["status"], "ancienne valeur")
        self.assertEqual(r["data"], POINT)
        self.assertIn("2026-10-20T20:00:00Z", r["message"])
        self.assertEqual(len(r["errors"]), 2)

    def test_rien_du_tout(self):
        r = refresh_dataset("t", 3600, [("A", "a", ko())], None, now=NOW)
        self.assertEqual(r["status"], "indisponible")
        self.assertIsNone(r["data"])

    def test_cache_frais(self):
        prev = {"status": "ok", "provider": "A", "fetched_at": "2026-10-26T19:30:00Z", "data": POINT}
        r = refresh_dataset("t", 3600, [("A", "a", ko())], prev, now=NOW)
        self.assertTrue(r["from_cache"])
        self.assertEqual(r["status"], "ok")

    def test_cache_force(self):
        prev = {"status": "ok", "provider": "A", "fetched_at": "2026-10-26T19:30:00Z", "data": POINT}
        r = refresh_dataset("t", 3600, [("A", "a", ok({"Y": POINT["X"]}))], prev, force=True, now=NOW)
        self.assertFalse(r["from_cache"])
        self.assertIn("Y", r["data"])

    def test_erreur_inattendue_ne_casse_pas(self):
        def boom():
            raise KeyError("champ")
        r = refresh_dataset("t", 3600, [("A", "a", boom), ("B", "b", ok())], None, now=NOW)
        self.assertEqual(r["status"], "secours")


if __name__ == "__main__":
    unittest.main()
