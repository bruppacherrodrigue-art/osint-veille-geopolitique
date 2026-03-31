"""
dedup.py — Déduplication et clustering sémantique des articles
Utilise Claude Haiku pour regrouper les articles qui parlent du même événement.
"""

import json
import anthropic
import os

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"


def prepare_clustered_analysis(articles, region, max_articles=8):
    """
    Regroupe les articles par événement/thème via Haiku, puis retourne
    la liste des clusters à analyser.

    FIX PERFORMANCE : max_articles limité à 8 (au lieu de 15) pour réduire
    le nombre d'appels Sonnet en aval.

    Retourne une liste de clusters, chaque cluster étant une liste d'articles.
    """
    if not articles:
        return []

    # Limiter à max_articles pour contrôler les coûts
    articles_limites = list(articles)[:max_articles]

    # Construire le texte de contexte pour le clustering
    articles_texte = "\n".join([
        f"{i+1}. [{a['source_name']}] {a['titre']}"
        for i, a in enumerate(articles_limites)
    ])

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"""Voici {len(articles_limites)} articles sur la région '{region}' :

{articles_texte}

Regroupe ces articles par événement/thème principal.
Retourne UNIQUEMENT un JSON valide, sans explication :
{{
  "clusters": [
    {{"theme": "...", "indices": [1, 3, 5]}},
    {{"theme": "...", "indices": [2, 4]}}
  ]
}}

Les indices correspondent aux numéros des articles (1-based).
Chaque article doit apparaître dans UN SEUL cluster.
Maximum 5 clusters."""
            }]
        )

        texte = reponse.content[0].text.strip()

        # Nettoyer le JSON si entouré de blocs markdown
        if "```" in texte:
            texte = texte.split("```")[1]
            if texte.startswith("json"):
                texte = texte[4:]

        clusters_data = json.loads(texte)
        clusters = []

        for cluster_info in clusters_data.get("clusters", []):
            indices = cluster_info.get("indices", [])
            articles_cluster = []
            for idx in indices:
                if 1 <= idx <= len(articles_limites):
                    articles_cluster.append(articles_limites[idx - 1])
            if articles_cluster:
                clusters.append({
                    "theme": cluster_info.get("theme", "Thème inconnu"),
                    "articles": articles_cluster
                })

        print(f"  📦 Clustering {region} : {len(articles_limites)} articles → {len(clusters)} clusters")
        return clusters

    except json.JSONDecodeError as e:
        print(f"  ⚠️  Erreur parsing JSON clustering {region} : {e}")
        # Fallback : un cluster par article
        return [{"theme": a["titre"][:50], "articles": [a]} for a in articles_limites]
    except Exception as e:
        print(f"  ⚠️  Erreur clustering {region} : {e}")
        return [{"theme": a["titre"][:50], "articles": [a]} for a in articles_limites]


def deduplifier_articles(articles):
    """
    Filtre les articles en double (même titre, même résumé).
    Retourne la liste dédupliquée.
    """
    vus = set()
    uniques = []
    for a in articles:
        # Clé de déduplication basique : début du titre normalisé
        cle = a.get("titre", "").lower().strip()[:80]
        if cle and cle not in vus:
            vus.add(cle)
            uniques.append(a)
    return uniques
