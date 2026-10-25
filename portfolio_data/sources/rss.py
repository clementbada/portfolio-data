"""Flux RSS officiels des banques centrales — sans clé.
Champs vus dans chaque <item> : title, link, pubDate (RFC 822), description (Fed, BoE).
La BCE préfixe ses liens d'un double slash (« europa.eu//press »), corrigé ici."""
import datetime as dt
import email.utils
import xml.etree.ElementTree as ET

from ..http import SourceError, get

FEEDS = {
    "BCE": "https://www.ecb.europa.eu/rss/press.html",
    "Fed": "https://www.federalreserve.gov/feeds/press_all.xml",
    "BoE": "https://www.bankofengland.co.uk/rss/news",
}
ATTRIBUTION = "Communiqués officiels : BCE, Federal Reserve, Bank of England"


def central_bank_news(bank, limit=8):
    if bank not in FEEDS:
        raise SourceError(f"flux inconnu : {bank}")
    text = get(FEEDS[bank]).lstrip("﻿")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise SourceError(f"XML invalide : {e}") from None
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip().replace("europa.eu//", "europa.eu/")
        pub = it.findtext("pubDate")
        try:
            published = (email.utils.parsedate_to_datetime(pub.strip()).astimezone(dt.timezone.utc)
                         .strftime("%Y-%m-%dT%H:%M:%SZ") if pub else None)
        except (TypeError, ValueError):
            published = None
        if title and link:
            items.append({"title": title, "url": link, "published": published, "source": bank})
    if not items:
        raise SourceError("aucun article dans le flux")
    items.sort(key=lambda a: a["published"] or "", reverse=True)
    return items[:limit]
