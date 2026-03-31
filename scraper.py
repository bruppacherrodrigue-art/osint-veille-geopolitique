"""
scraper.py — Tendances web via Tavily
Utilisé UNIQUEMENT par predictions.py (pas par analyst.py).
"""

import os

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


def generer_briefing_tendances(region):
    """
    Retourne un briefing textuel des tendances web pour une région.
    Appelé UNIQUEMENT depuis predictions.py.
    Retourne une chaîne vide si Tavily n'est pas disponible.
    """
    if not SCRAPER_DISPONIBLE:
        return ""

    requetes = REQUETES_PAR_REGION.get(region, [f"{region} geopolitics news"])

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        resultats = []

        for requete in requetes[:2]:  # Max 2 requêtes par région pour économiser
            try:
                reponse = client.search(
                    query=requete,
                    search_depth="basic",
                    max_results=3,
                    include_raw_content=False
                )
                for r in reponse.get("results", []):
                    resultats.append(f"- {r.get('title', '')} : {r.get('content', '')[:200]}")
            except Exception as e:
                print(f"  ⚠️  Tavily requête '{requete}' : {e}")
                continue

        if not resultats:
            return ""

        return "=== TENDANCES WEB (Tavily) ===\n" + "\n".join(resultats[:6])

    except ImportError:
        print("  ⚠️  Package tavily-python non installé.")
        return ""
    except Exception as e:
        print(f"  ⚠️  Erreur Tavily : {e}")
        return ""
