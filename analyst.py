"""
analyst.py — Analyse profonde via Claude Sonnet
Pipeline : articles → dedup/clustering → analyse Sonnet → sauvegarde → mémoire

CORRECTIONS PERFORMANCE APPLIQUÉES :
1. Tavily DÉSACTIVÉ dans ce fichier (gardé uniquement dans predictions.py)
2. Limite réduite à 8 articles par région (au lieu de 15)
3. Mémoire mise à jour UNIQUEMENT si nouvelles analyses générées
4. Le sélecteur de région est géré par dashboard.py (paramètre `regions`)
"""

import json
import os
import re
import requests
from datetime import datetime
import anthropic

from database import (
    get_articles_recents, sauvegarder_analyse, get_dernieres_analyses, init_db
)
try:
    from collector import PERSPECTIVES_SOURCES
except ImportError:
    PERSPECTIVES_SOURCES = {}
from dedup import prepare_clustered_analysis, deduplifier_articles
from memory import get_context_for_prompt, update_memory
from analyst_terrain import get_briefing_terrain
from alerts import notifier_alerte_critique

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL      = "claude-sonnet-4-20250514"

def _fetch_article_content(url, timeout=6):
    """
    Récupère le contenu complet d'un article depuis son URL.
    Utilise requests + extraction HTML basique (gratuit, sans API).
    Retourne le texte enrichi (max 1500 chars) ou None si échec.
    """
    if not url or url == "N/A":
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINTBot/1.0)"}
        resp = requests.get(url, timeout=timeout, headers=headers)
        if resp.status_code != 200:
            return None
        # Extraction HTML basique sans dépendances externes
        text = resp.text
        # Supprimer les balises script/style
        text = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        # Supprimer toutes les balises HTML
        text = re.sub(r"<[^>]+>", " ", text)
        # Nettoyer les entités HTML courantes
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ").replace("&quot;", '"')
        # Normaliser les espaces
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1500] if len(text) > 100 else None
    except Exception:
        return None

PROMPT_ANALYSE = """Tu es un analyste géopolitique senior francophone spécialisé en OSINT.

⛔ RÈGLE ABSOLUE — ANTI-HALLUCINATION :
Tu ne peux utiliser QUE les informations présentes dans les articles ci-dessous.
N'utilise PAS ta connaissance générale sur la région, l'histoire ou les acteurs.
Si un fait n'est pas dans les articles fournis, il n'existe pas pour toi.
Si les résumés sont trop courts pour produire une analyse solide, indique-le explicitement.

📌 PERSPECTIVES MULTIPLES :
Chaque article indique sa perspective entre crochets [ex: think-tank occidental, agence d'état russe].
Quand plusieurs sources donnent des versions différentes d'un même fait, présente les deux angles.

CONTEXTE MÉMORISÉ (7 derniers jours — pour orientation uniquement, ne pas citer comme source) :
{contexte_memoire}

BRIEFING TERRAIN RÉCENT (signaux breaking — pour orientation uniquement) :
{briefing_terrain}

ARTICLES À ANALYSER — Région : {region} | Cluster : {theme}
{articles_texte}

Produis une analyse structurée en JSON basée UNIQUEMENT sur les articles ci-dessus.
Pour chaque fait clé, indique la source entre crochets : "[NomSource] fait observé".

{{
  "theme": "{theme}",
  "faits_cles": [
    "[NomSource] fait tiré directement de cet article",
    "[AutreSource] autre fait directement cité ou paraphrasé"
  ],
  "acteurs_principaux": ["acteur mentionné dans les articles"],
  "tendances": "tendances observées EN SE BASANT UNIQUEMENT sur les articles (2-3 phrases)",
  "implications": "implications déduites des faits des articles (2-3 phrases)",
  "niveau_alerte": "VERT|ORANGE|ROUGE",
  "signaux_faibles": ["signal mentionné dans les articles, pas inventé"],
  "a_surveiller": "point de vigilance tiré directement d'un article",
  "sources_utilisees": ["NomSource1", "NomSource2"],
  "qualite_sources": "SUFFISANTE|INSUFFISANTE — indique INSUFFISANTE si les résumés sont trop courts"
}}

Niveau alerte : VERT = stable, ORANGE = à surveiller, ROUGE = critique.
Si qualite_sources = INSUFFISANTE, mets niveau_alerte = VERT et indique-le dans tendances."""


def analyser_cluster(region, theme, articles, contexte_memoire, briefing_terrain):
    """
    Analyse un cluster d'articles avec Claude Sonnet.
    Retourne le JSON d'analyse ou None en cas d'échec.
    """
    lignes = []
    for a in articles:
        resume = a.get("resume", "") or ""
        url    = a.get("url", "N/A") or "N/A"
        # Enrichissement : fetch contenu complet si résumé court (< 300 chars)
        contenu_enrichi = None
        if len(resume) < 300 and url != "N/A":
            contenu_enrichi = _fetch_article_content(url)
        if contenu_enrichi:
            contenu_final = f"RÉSUMÉ RSS : {resume}\nCONTENU COMPLET : {contenu_enrichi}"
        else:
            contenu_final = resume or "(résumé absent — analyser uniquement le titre)"
        lignes.append(
            "SOURCE : {src} [{perspective}]\nDATE : {date}\nTITRE : {titre}\n{contenu}\nURL : {url}".format(
                src=a.get("source_name", "Inconnu"),
                perspective=PERSPECTIVES_SOURCES.get(a.get("source_name", ""), "perspective inconnue"),
                date=(a.get("date_pub") or a.get("date_collecte") or "N/A")[:10],
                titre=a.get("titre", ""),
                contenu=contenu_final,
                url=url,
            )
        )
    articles_texte = "\n\n".join(lignes)

    prompt = PROMPT_ANALYSE.format(
        contexte_memoire=contexte_memoire or "Aucun contexte mémorisé.",
        briefing_terrain=briefing_terrain or "Aucun signal terrain récent.",
        region=region.replace("_", " ").upper(),
        theme=theme,
        articles_texte=articles_texte
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        texte = reponse.content[0].text.strip()
        if "```" in texte:
            texte = texte.split("```")[1]
            if texte.startswith("json"):
                texte = texte[4:]

        data = json.loads(texte)
        data["theme"] = theme
        data["nb_articles"] = len(articles)

        qualite = data.get("qualite_sources", "SUFFISANTE")
        if qualite == "INSUFFISANTE":
            print(f"    ⚠️  Sources insuffisantes pour '{theme}' — analyse ignorée")
            return None

        return data

    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON invalide pour cluster '{theme}' : {e}")
        return None
    except Exception as e:
        print(f"    ⚠️  Erreur analyse cluster '{theme}' : {e}")
        return None


def analyser_region(region):
    """
    Analyse complète d'une région :
    1. Récupère les articles récents (48h)
    2. Déduplique
    3. Cluster (max 8 articles — FIX PERFORMANCE #2)
    4. Analyse chaque cluster avec Sonnet
    5. Sauvegarde les résultats
    6. Met à jour la mémoire SEULEMENT si de nouveaux résultats (FIX PERFORMANCE #3)

    Retourne la liste des analyses générées.
    """
    print(f"\n  📍 Analyse {region.upper().replace('_', ' ')}")

    # Récupérer les articles des 48 dernières heures
    articles_bruts = get_articles_recents(region, heures=48)
    if not articles_bruts:
        print(f"    ℹ️  Aucun article récent pour {region}")
        return []

    # Convertir en dict pour traitement
    articles = [dict(a) for a in articles_bruts]

    # Déduplication basique
    articles = deduplifier_articles(articles)
    print(f"    📰 {len(articles)} article(s) après déduplication")

    clusters = prepare_clustered_analysis(articles, region, max_articles=20)
    if not clusters:
        print(f"    ℹ️  Aucun cluster généré pour {region}")
        return []

    # Récupérer contexte mémorisé et briefing terrain
    contexte_memoire  = get_context_for_prompt(region)
    briefing_terrain  = get_briefing_terrain()

    # Analyser chaque cluster
    nouvelles_analyses = []
    for i, cluster in enumerate(clusters):
        theme    = cluster.get("theme", f"Cluster {i+1}")
        articles_c = cluster.get("articles", [])
        print(f"    🔍 Cluster {i+1}/{len(clusters)} : {theme[:50]}")

        resultat = analyser_cluster(
            region=region,
            theme=theme,
            articles=articles_c,
            contexte_memoire=contexte_memoire,
            briefing_terrain=briefing_terrain
        )

        if resultat:
            # Déterminer le niveau d'alerte global
            niveau = resultat.get("niveau_alerte", "VERT")
            tendances = resultat.get("tendances", "")

            sauvegarder_analyse(
                region=region,
                contenu=json.dumps(resultat, ensure_ascii=False),
                tendances=tendances,
                niveau_alerte=niveau
            )

            nouvelles_analyses.append(resultat)

            # Notification Discord si alerte critique
            if niveau == "ROUGE":
                contenu_alerte = f"{theme}\n{tendances}"
                notifier_alerte_critique(region, contenu_alerte)

            print(f"    ✅ Cluster analysé — Alerte : {niveau}")

    # FIX PERFORMANCE #3 : mise à jour mémoire UNIQUEMENT si nouvelles analyses
    if nouvelles_analyses:
        update_memory(region, nouvelles_analyses)
    else:
        print(f"    ℹ️  Pas de nouvelles analyses — mémoire non mise à jour")

    return nouvelles_analyses


def analyser_regions(regions=None):
    """
    Lance l'analyse pour une liste de régions.
    Si regions=None, analyse les 3 régions.

    FIX PERFORMANCE #4 : le paramètre `regions` permet d'analyser une seule région
    depuis le dashboard (ex. analyser_regions(["ukraine"])).

    Retourne un dict résumant les résultats.
    """
    init_db()
    toutes_regions = ["ukraine", "moyen_orient", "otan"]

    if regions is None:
        regions = toutes_regions
    elif isinstance(regions, str):
        regions = [regions]

    print(f"\n🤖 Analyse Claude — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"   Régions : {', '.join(regions)}")
    resultats = {}

    for region in regions:
        if region not in toutes_regions:
            print(f"  ⚠️  Région inconnue : {region}")
            continue
        analyses = analyser_region(region)
        resultats[region] = len(analyses)
        print(f"  → {len(analyses)} analyse(s) générée(s) pour {region}")

    total = sum(resultats.values())
    print(f"\n✅ Analyse terminée — {total} analyse(s) au total")
    return resultats


if __name__ == "__main__":
    # Exemple : analyser une seule région
    # analyser_regions(["ukraine"])
    analyser_regions()
