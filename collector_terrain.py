"""
collector_terrain.py — Collecte terrain temps réel (pipeline rapide)
Sources : Telegram, trackers OSINT, comptes partisans via RSSHub.

IMPORTANT : Ces URLs sont DISTINCTES de collector.py.
- collector.py = think tanks, médias (cycle lent ~60 min)
- collector_terrain.py = Telegram, trackers, partisans (cycle rapide ~15 min)
Aucune URL ne doit apparaître dans les deux fichiers.
"""

import feedparser
import os
from datetime import datetime

from database import sauvegarder_signal_terrain, init_db

try:
    from config import RSSHUB_BASE
except ImportError:
    RSSHUB_BASE = "https://rsshub.app"

# ============================================================
# SOURCES TERRAIN — UKRAINE
# Telegram/blogueurs militaires via RSSHub (jamais dans collector.py)
# ============================================================
SOURCES_TERRAIN_UKRAINE = {
    # Canaux Telegram militaires ukrainiens
    "DeepStateUA (TG)":       f"{RSSHUB_BASE}/telegram/channel/deepstatemap",
    "Ukraine Weapons Tracker": f"{RSSHUB_BASE}/telegram/channel/ukraineweaponstracker",
    "Militarnyi (TG)":        f"{RSSHUB_BASE}/telegram/channel/militarnyi",
    "Rezistent UA (TG)":      f"{RSSHUB_BASE}/telegram/channel/rezistentua",

    # Canaux Telegram russes (surveillance)
    "Rybar (TG)":             f"{RSSHUB_BASE}/telegram/channel/rybar",
    "War Gonzo (TG)":         f"{RSSHUB_BASE}/telegram/channel/wargonzo",

    # OSINT trackers
    "LiveUAmap":              "https://liveuamap.com/en/rss",
}

# ============================================================
# SOURCES TERRAIN — MOYEN-ORIENT
# ============================================================
SOURCES_TERRAIN_MOYEN_ORIENT = {
    "Gaza Now (TG)":          f"{RSSHUB_BASE}/telegram/channel/gazanow",
    "Quds News (TG)":         f"{RSSHUB_BASE}/telegram/channel/QudsNEN",
    "Iran International (TG)":f"{RSSHUB_BASE}/telegram/channel/IranIntl_Fa",
    "Osint Gaza (TG)":        f"{RSSHUB_BASE}/telegram/channel/OsintGaza",
}

# ============================================================
# SOURCES TERRAIN — OTAN / EUROPE
# ============================================================
SOURCES_TERRAIN_OTAN = {
    "Intel Slava (TG)":       f"{RSSHUB_BASE}/telegram/channel/intelslava",
    "War Monitor (TG)":       f"{RSSHUB_BASE}/telegram/channel/war_monitor",
    "European Disunion (TG)": f"{RSSHUB_BASE}/telegram/channel/europeandisunion",
}

# ============================================================
# SOURCES TERRAIN GLOBALES (multi-régions, auto-tagging)
# Ces sources ne sont PAS dans collector.py
# ============================================================
SOURCES_TERRAIN_GLOBALES = {
    "OSINTdefender":          f"{RSSHUB_BASE}/telegram/channel/OSINTdefender",
    "GeoConfirmed":           f"{RSSHUB_BASE}/telegram/channel/GeoConfirmed",
    "Intel Crab (TG)":        f"{RSSHUB_BASE}/telegram/channel/IntelCrab",
    "Conflict Monitor (TG)":  f"{RSSHUB_BASE}/telegram/channel/conflictmonitor",
    "ACLED":                  "https://acleddata.com/feed/",
}

SOURCES_TERRAIN = {
    "ukraine":      SOURCES_TERRAIN_UKRAINE,
    "moyen_orient": SOURCES_TERRAIN_MOYEN_ORIENT,
    "otan":         SOURCES_TERRAIN_OTAN,
}

# Fiabilité estimée par type de source
FIABILITE_PAR_TYPE = {
    "tracker":  0.85,
    "telegram": 0.60,
    "partisan": 0.45,
    "osint":    0.75,
}

# Classification des sources
TYPE_SOURCE = {
    "DeepStateUA (TG)":       "tracker",
    "Ukraine Weapons Tracker": "tracker",
    "LiveUAmap":              "tracker",
    "OSINTdefender":          "osint",
    "GeoConfirmed":           "osint",
    "ACLED":                  "osint",
    "Intel Crab (TG)":        "osint",
}

# Mots-clés pour l'auto-tagging des sources globales terrain
TAGS_TERRAIN = {
    "ukraine":      ["ukraine", "kyiv", "russia", "drone", "shahed", "kherson",
                     "zaporizhzhia", "frontline", "bakhmut", "offensive"],
    "moyen_orient": ["israel", "gaza", "iran", "hamas", "hezbollah", "strike",
                     "missile", "rafah", "west bank", "lebanon"],
    "otan":         ["nato", "otan", "poland", "baltic", "finland", "sweden",
                     "artillery", "f16", "himars", "abrams"],
}


def detecter_region_terrain(titre, contenu):
    """Détecte la région d'un signal terrain selon ses mots-clés."""
    texte = (titre + " " + contenu).lower()
    scores = {region: 0 for region in TAGS_TERRAIN}
    for region, mots in TAGS_TERRAIN.items():
        for mot in mots:
            if mot in texte:
                scores[region] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "ukraine"  # défaut terrain = ukraine


def get_type_source(nom_source):
    """Retourne le type de source (tracker/telegram/partisan/osint)."""
    if nom_source in TYPE_SOURCE:
        return TYPE_SOURCE[nom_source]
    if "(TG)" in nom_source:
        return "telegram"
    return "osint"


def get_fiabilite(nom_source):
    """Retourne la fiabilité estimée d'une source."""
    type_s = get_type_source(nom_source)
    return FIABILITE_PAR_TYPE.get(type_s, 0.60)


def collecter_terrain_region(region, sources):
    """
    Collecte les signaux terrain pour une région.
    Retourne le nombre de nouveaux signaux sauvegardés.
    """
    total = 0
    for nom_source, url in sources.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"    ⚠️  {nom_source} : flux vide ({url[:60]}...)")
                continue

            nouveaux = 0
            for entry in feed.entries[:20]:  # Max 20 entrées terrain (plus court)
                titre   = entry.get("title", "")[:500]
                url_s   = entry.get("link", "")
                contenu = entry.get("summary", entry.get("description", ""))[:2000]
                date_pub = entry.get("published", entry.get("updated", ""))[:50]

                if not titre:
                    continue

                # Priorité : les 5 premières entrées sont les plus récentes
                priorite = max(0, 5 - feed.entries.index(entry)) if entry in feed.entries else 0

                sauvegarder_signal_terrain(
                    source_name=nom_source,
                    region=region,
                    titre=titre,
                    url=url_s or f"terrain_{nom_source}_{hash(titre)}",
                    contenu=contenu,
                    date_pub=date_pub,
                    type_source=get_type_source(nom_source),
                    fiabilite=get_fiabilite(nom_source),
                    priorite=priorite
                )
                nouveaux += 1

            total += nouveaux
            if nouveaux > 0:
                print(f"    ✅ {nom_source} : {nouveaux} signal(aux)")
        except Exception as e:
            print(f"    ❌ Erreur {nom_source} : {e}")

    return total


def collecter_terrain_globales():
    """
    Collecte les sources terrain globales avec auto-tagging.
    """
    total = 0
    for nom_source, url in SOURCES_TERRAIN_GLOBALES.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                continue

            for entry in feed.entries[:15]:
                titre   = entry.get("title", "")[:500]
                url_s   = entry.get("link", "")
                contenu = entry.get("summary", entry.get("description", ""))[:2000]
                date_pub = entry.get("published", entry.get("updated", ""))[:50]

                if not titre:
                    continue

                region = detecter_region_terrain(titre, contenu)
                sauvegarder_signal_terrain(
                    source_name=nom_source,
                    region=region,
                    titre=titre,
                    url=url_s or f"terrain_{nom_source}_{hash(titre)}",
                    contenu=contenu,
                    date_pub=date_pub,
                    type_source=get_type_source(nom_source),
                    fiabilite=get_fiabilite(nom_source),
                    priorite=3
                )
                total += 1

            print(f"    ✅ {nom_source} (global terrain) : ok")
        except Exception as e:
            print(f"    ❌ Erreur {nom_source} : {e}")

    return total


def collecter_tous_signaux_terrain():
    """
    Lance la collecte complète terrain.
    Retourne un dict résumant les résultats.
    """
    init_db()
    print(f"\n📡 Collecte terrain — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    resultats = {}

    for region, sources in SOURCES_TERRAIN.items():
        print(f"\n  📍 {region.upper().replace('_', ' ')} ({len(sources)} sources terrain)")
        nb = collecter_terrain_region(region, sources)
        resultats[region] = nb
        print(f"  → {nb} signal(aux) terrain")

    print("\n  🌐 Sources terrain globales")
    nb_global = collecter_terrain_globales()
    resultats["global"] = nb_global

    total = sum(resultats.values())
    print(f"\n✅ Collecte terrain terminée — {total} signal(aux) au total")
    return resultats


if __name__ == "__main__":
    collecter_tous_signaux_terrain()
