"""
scraper.py — Tendances web via Tavily
Utilisé UNIQUEMENT par predictions.py (pas par analyst.py).

Améliorations appliquées :
    - Retry exponentiel pour les appels API
    - Rate limiting pour éviter le spam
    - Cache des résultats (24h)
    - Logging structuré
"""

import os
from typing import Dict, Optional

# Import des utilitaires
try:
    from utils import (
        retry_with_backoff,
        RATE_LIMITERS,
        get_tavily_cache,
        set_tavily_cache,
        logger
    )
except ImportError:
    # Fallback si utils.py n'est pas disponible
    class DummyLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): pass
    logger = DummyLogger()
    
    def retry_with_backoff(**kwargs):
        def decorator(func):
            return func
        return decorator
    
    RATE_LIMITERS = {}
    
    def get_tavily_cache(*args, **kwargs):
        return None
    
    def set_tavily_cache(*args, **kwargs):
        pass

try:
    from config import TAVILY_API_KEY
except ImportError:
    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

SCRAPER_DISPONIBLE = bool(TAVILY_API_KEY and TAVILY_API_KEY != "YOUR_TAVILY_API_KEY")

REQUETES_PAR_REGION = {
    "ukraine": [
        "Ukraine Russia war latest news",
        "front ukrainien situation militaire",
        "Ukraine OTAN aide militaire",
    ],
    "moyen_orient": [
        "Middle East conflict latest",
        "Gaza Israël situation humanitaire",
        "Iran tensions régionales",
    ],
    "otan": [
        "NATO latest news",
        "défense européenne actualité",
        "OTAN Russie tensions",
    ],
}


@retry_with_backoff(max_retries=3, base_delay=2.0, max_delay=30.0, logger_obj=logger)
def _tavily_search(client, query: str, search_depth: str, max_results: int):
    """Appel API Tavily avec retry exponentiel."""
    return client.search(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
        include_raw_content=False
    )


def generer_briefing_tendances(region: str) -> str:
    """
    Retourne un briefing textuel des tendances web pour une région.
    Appelé UNIQUEMENT depuis predictions.py.
    Retourne une chaîne vide si Tavily n'est pas disponible.
    
    Améliorations :
        - Utilisation du cache 24h pour éviter les appels redondants
        - Rate limiting pour respecter les quotas API
        - Retry exponentiel en cas d'échec temporaire
    """
    if not SCRAPER_DISPONIBLE:
        logger.debug("Tavily non configuré, skipping tendances web")
        return ""

    requetes = REQUETES_PAR_REGION.get(region, [f"{region} geopolitics news"])

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        resultats = []

        for requete in requetes[:2]:  # Max 2 requêtes par région pour économiser
            
            # Vérifier le cache d'abord
            cached_results = get_tavily_cache(requete, {'search_depth': 'basic', 'max_results': 3})
            if cached_results:
                logger.debug(f"Tavily cache hit: {requete}")
                for r in cached_results:
                    resultats.append(f"- {r.get('title', '')} : {r.get('content', '')[:200]}")
                continue
            
            # Appliquer le rate limiter
            if 'tavily' in RATE_LIMITERS:
                RATE_LIMITERS['tavily'].wait()
            
            try:
                # Appel API avec retry
                reponse = _tavily_search(
                    client, 
                    query=requete,
                    search_depth="basic",
                    max_results=3
                )
                
                # Sauvegarder dans le cache
                results_data = reponse.get("results", [])
                set_tavily_cache(requete, results_data, {'search_depth': 'basic', 'max_results': 3})
                
                for r in results_data:
                    resultats.append(f"- {r.get('title', '')} : {r.get('content', '')[:200]}")
                    
            except Exception as e:
                logger.warning(f"Tavily requête '{requete}' échouée : {e}")
                continue

        if not resultats:
            logger.info(f"Aucun résultat Tavily pour {region}")
            return ""

        briefing = "=== TENDANCES WEB (Tavily) ===\n" + "\n".join(resultats[:6])
        logger.info(f"Briefing tendances généré pour {region} ({len(resultats)} résultats)")
        return briefing

    except ImportError:
        logger.error("Package tavily-python non installé.")
        return ""
    except Exception as e:
        logger.error(f"Erreur générale Tavily : {e}")
        return ""
