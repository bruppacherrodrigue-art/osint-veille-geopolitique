"""
collector.py — Collecte RSS classique (pipeline analyse profonde)
Sources définies dans sources.py (données pures, sans dépendances).
"""

import feedparser
import os
from datetime import datetime

from database import sauvegarder_article, init_db
from sources import (
    SOURCES_UKRAINE, SOURCES_MOYEN_ORIENT, SOURCES_OTAN, SOURCES_GLOBALES,
    RSS_SOURCES, PERSPECTIVES_SOURCES, TAGS_REGIONS
)

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
    
    Améliorations :
        - Rate limiting pour éviter de spammer les flux RSS
        - Logging structuré
        - Validation des URLs
    """
    total = 0
    
    # Import du rate limiter
    try:
        from utils import RATE_LIMITERS, sanitize_url, logger
    except ImportError:
        RATE_LIMITERS = {}
        def sanitize_url(url): return url
        class DummyLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def debug(self, msg): pass
        logger = DummyLogger()
    
    for nom_source, url in sources.items():
        # Valider l'URL
        url_valide = sanitize_url(url)
        if not url_valide:
            logger.warning(f"URL invalide pour {nom_source}, skip")
            continue
        
        try:
            # Appliquer le rate limiter RSS
            if 'rss' in RATE_LIMITERS:
                RATE_LIMITERS['rss'].wait()
            
            feed = feedparser.parse(url_valide)
            if not feed.entries:
                logger.warning(f"{nom_source} : flux vide ou inaccessible ({url_valide})")
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
                logger.info(f"{nom_source} : {nouveaux} article(s)")
        except Exception as e:
            logger.error(f"Erreur {nom_source} : {e}")

    return total


def collecter_sources_globales():
    """
    Collecte les sources globales et auto-tague chaque article par région.
    Retourne le nombre total de nouveaux articles.
    
    Améliorations :
        - Rate limiting pour éviter de spammer les flux RSS
        - Logging structuré
        - Validation des URLs
    """
    # Import du rate limiter
    try:
        from utils import RATE_LIMITERS, sanitize_url, logger
    except ImportError:
        RATE_LIMITERS = {}
        def sanitize_url(url): return url
        class DummyLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def debug(self, msg): pass
        logger = DummyLogger()
    
    total = 0
    for nom_source, url in SOURCES_GLOBALES.items():
        # Valider l'URL
        url_valide = sanitize_url(url)
        if not url_valide:
            logger.warning(f"URL invalide pour {nom_source} (global), skip")
            continue
        
        try:
            # Appliquer le rate limiter RSS
            if 'rss' in RATE_LIMITERS:
                RATE_LIMITERS['rss'].wait()
            
            feed = feedparser.parse(url_valide)
            if not feed.entries:
                logger.warning(f"{nom_source} (global) : flux vide")
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
                logger.info(f"{nom_source} (global) : {nouveaux} article(s)")
        except Exception as e:
            logger.error(f"Erreur {nom_source} (global) : {e}")

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
