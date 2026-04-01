"""
collector.py — Collecte RSS classique (pipeline analyse profonde)
Sources : think tanks, médias, analyses géopolitiques.

CORRECTIONS APPLIQUÉES :
- ISW : nouvelle URL iswresearch.org
- RUSI : URL mise à jour
- Kyiv Independent : URL mise à jour
- RFI Russie (morte) → remplacée par Ukrinform + Euromaidan Press
- Wilson Center (morte) → remplacée par Carnegie Endowment
- Critical Threats (morte) → remplacée par iswresearch.org (déjà présent)
- Haaretz (morte) → remplacée par Times of Israel
- NATO News (pas RSS) → remplacée par NATO Review RSS valide
- IISS (morte) → remplacée par Chatham House
- Jerusalem Post (vide) → remplacée par Jerusalem Post frontpage
- Nouvelles sources Ukraine ajoutées pour équilibrer
- Aucun doublon avec collector_terrain.py
"""

import feedparser
import os
from datetime import datetime

from database import sauvegarder_article, init_db

# ============================================================
# SOURCES RSS — UKRAINE
# ✓ = vérifiée fonctionnelle | ★ = nouvelle source ajoutée
# ============================================================
SOURCES_UKRAINE = {
    # Think tanks & analyses
    "ISW Research":       "https://www.iswresearch.org/feeds/posts/default",   # ★ (ancienne URL morte)
    "Bellingcat":         "https://www.bellingcat.com/feed/",                   # ✓

    # Médias ukrainiens anglophones
    "Kyiv Independent":   "https://kyivindependent.com/feed/",                 # ✓ (URL vérifiée)
    "Ukrinform":          "https://www.ukrinform.net/rss/block-lastnews",      # ★ (nouvelle)
    "Euromaidan Press":   "https://euromaidanpress.com/feed/",                 # ★ (nouvelle)
    "Kyiv Post":          "https://www.kyivpost.com/feed",                     # ★ (nouvelle)
    "Ukraine World":      "https://ukraineworld.org/feed/",                    # ★ (nouvelle)

    # Médias russophones libres
    "Meduza (EN)":        "https://meduza.io/en/rss/all",                      # ✓
}

# ============================================================
# SOURCES RSS — MOYEN-ORIENT
# Note : déjà ~46 articles/cycle, pas d'ajout
# ============================================================
SOURCES_MOYEN_ORIENT = {
    "Al-Monitor":         "https://www.al-monitor.com/rss",                    # ✓
    "Middle East Eye":    "https://www.middleeasteye.net/rss",                 # ✓
    "RFI Moyen-Orient":   "https://www.rfi.fr/fr/moyen-orient/rss",           # ✓
    "Times of Israel":    "https://www.timesofisrael.com/feed/",               # ★ (remplace Haaretz morte)
    "Jerusalem Post":     "https://www.jpost.com/rss/rssfeedsfrontpage.aspx", # ★ (remplace version vide)
    "Al Jazeera EN":      "https://www.aljazeera.com/xml/rss/all.xml",        # ★ (nouvelle)
}

# ============================================================
# SOURCES RSS — OTAN / EUROPE
# ============================================================
SOURCES_OTAN = {
    "ECFR":              "https://ecfr.eu/feed/",                              # ✓
    "Atlantic Council":  "https://www.atlanticcouncil.org/feed/",              # ✓
    "Defense News":      "https://www.defensenews.com/arc/outboundfeeds/rss/", # ✓
    "RFI Europe":        "https://www.rfi.fr/fr/europe/rss",                   # ✓
    "IRIS France":       "https://www.iris-france.org/feed/",                  # ✓
    "Chatham House":     "https://www.chathamhouse.org/rss.xml",               # ★ (remplace IISS morte)
    "RUSI":              "https://rusi.org/rss",                               # ★ (URL mise à jour)
    "NATO Review":       "https://www.nato.int/docu/review/rss.xml",           # ★ (remplace URL non-RSS)
    "Carnegie Endowment":"https://carnegieendowment.org/rss/",                 # ★ (remplace Wilson Center morte)
}

# ============================================================
# SOURCES GLOBALES (multi-régions, auto-tagging par région)
# IMPORTANT : Ces URLs NE DOIVENT PAS apparaître dans collector_terrain.py
# ============================================================
SOURCES_GLOBALES = {
    "Le Monde Diplomatique": "https://www.monde-diplomatique.fr/rss",
    "Foreign Policy":        "https://foreignpolicy.com/feed/",
    "Reuters World":         "https://feeds.reuters.com/reuters/worldNews",
    "BBC World":             "https://feeds.bbci.co.uk/news/world/rss.xml",
}

# Dictionnaire principal utilisé par le dashboard
RSS_SOURCES = {
    "ukraine":      SOURCES_UKRAINE,
    "moyen_orient": SOURCES_MOYEN_ORIENT,
    "otan":         SOURCES_OTAN,
}

# Mots-clés pour l'auto-tagging des sources globales
TAGS_REGIONS = {
    "ukraine":      ["ukraine", "kyiv", "zelensky", "russia", "russie", "donetsk",
                     "zaporizhzhia", "kharkiv", "crimée", "moscow", "kremlin"],
    "moyen_orient": ["israel", "gaza", "iran", "hamas", "hezbollah", "syrie",
                     "liban", "arabie", "qatar", "middle east", "palestine"],
    "otan":         ["nato", "otan", "macron", "europe", "bruxelles", "défense",
                     "trump", "pentagon", "alliance", "berlin", "warsaw"],
}


def detecter_region(titre, resume):
    """Détecte la région d'un article selon ses mots-clés."""
    texte = (titre + " " + resume).lower()
    scores = {region: 0 for region in TAGS_REGIONS}
    for region, mots in TAGS_REGIONS.items():
        for mot in mots:
            if mot in texte:
                scores[region] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None  # None = hors scope, à ignorer


def collecter_region(region, sources):
    """
    Collecte les articles RSS d'une région spécifique.
    Retourne le nombre de nouveaux articles sauvegardés.
    """
    total = 0
    for nom_source, url in sources.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"    ⚠️  {nom_source} : flux vide ou inaccessible ({url})")
                continue

            nouveaux = 0
            for entry in feed.entries[:15]:  # Max 15 entrées par source
                titre  = entry.get("title", "")[:500]
                url_a  = entry.get("link", "")
                resume = entry.get("summary", entry.get("description", ""))[:1000]
                date_pub = entry.get("published", entry.get("updated", ""))[:50]

                if not titre or not url_a:
                    continue

                sauvegarder_article(
                    source_name=nom_source,
                    region=region,
                    titre=titre,
                    url=url_a,
                    resume=resume,
                    date_pub=date_pub
                )
                nouveaux += 1

            total += nouveaux
            if nouveaux > 0:
                print(f"    ✅ {nom_source} : {nouveaux} article(s)")
        except Exception as e:
            print(f"    ❌ Erreur {nom_source} : {e}")

    return total


def collecter_sources_globales():
    """
    Collecte les sources globales et auto-tague chaque article par région.
    Retourne le nombre total de nouveaux articles.
    """
    total = 0
    for nom_source, url in SOURCES_GLOBALES.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"    ⚠️  {nom_source} (global) : flux vide")
                continue

            nouveaux = 0
            for entry in feed.entries[:20]:
                titre   = entry.get("title", "")[:500]
                url_a   = entry.get("link", "")
                resume  = entry.get("summary", entry.get("description", ""))[:1000]
                date_pub = entry.get("published", entry.get("updated", ""))[:50]

                if not titre or not url_a:
                    continue

                region = detecter_region(titre, resume)
                if region is None:
                    continue  # Article hors scope géopolitique, ignoré
                sauvegarder_article(
                    source_name=nom_source,
                    region=region,
                    titre=titre,
                    url=url_a,
                    resume=resume,
                    date_pub=date_pub
                )
                nouveaux += 1

            total += nouveaux
            if nouveaux > 0:
                print(f"    ✅ {nom_source} (global) : {nouveaux} article(s)")
        except Exception as e:
            print(f"    ❌ Erreur {nom_source} (global) : {e}")

    return total


def collecter_toutes_sources():
    """
    Lance la collecte complète : régions + globales.
    Retourne un dict résumant les résultats.
    """
    init_db()
    print(f"\n🔄 Collecte RSS — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    resultats = {}

    for region, sources in RSS_SOURCES.items():
        print(f"\n  📍 {region.upper().replace('_', ' ')} ({len(sources)} sources)")
        nb = collecter_region(region, sources)
        resultats[region] = nb
        print(f"  → {nb} nouveau(x) article(s)")

    print("\n  🌐 Sources globales")
    nb_global = collecter_sources_globales()
    resultats["global"] = nb_global
    print(f"  → {nb_global} nouveau(x) article(s)")

    total = sum(resultats.values())
    print(f"\n✅ Collecte terminée — {total} article(s) au total")
    return resultats


if __name__ == "__main__":
    collecter_toutes_sources()
