"""Un module par source. Chaque fonction publique renvoie le même format,
quelle que soit la source :

    {"KEY": {"value": float, "unit": str, "as_of": "YYYY-MM-DD" ou "YYYY-MM",
             "label": str}}

pour les séries chiffrées, ou une liste d'articles
    [{"title", "url", "published", "source"}]
pour les actualités. Toute erreur lève portfolio_data.http.SourceError.
"""


def point(value, unit, as_of, label):
    return {"value": float(value), "unit": unit, "as_of": as_of, "label": label}
