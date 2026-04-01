"""
analyst_terrain.py — Analyse des signaux terrain et détection breaking
Utilise Claude Haiku pour scorer la chaleur et détecter les événements chauds.
Auto-génère un post breaking si chaleur >= 70.
"""

import json
import os
from datetime import datetime
import anthropic

from database import (
    get_signaux_non_traites, marquer_signaux_traites,
    sauvegarder_alerte_terrain, get_dernieres_alertes, sauvegarder_post, init_db
)
from alerts import notifier_breaking

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, SEUIL_CHALEUR_BREAKING
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"
    SEUIL_CHALEUR_BREAKING = 70


def analyser_signaux_region(region):
    """
    Analyse les signaux terrain non traités pour une région.
    Retourne un dict avec chaleur, résumé, événements, signal_partisan, post_breaking.
    Retourne None si pas de signaux.
    """
    signaux = get_signaux_non_traites(region)
    if not signaux:
        print(f"  ℹ️  Terrain {region} : aucun signal non traité")
        return None

    # Construire le texte des signaux pour Haiku
    signaux_texte = "\n".join([
        f"[{s['source_name']} | fiabilité {float(s['fiabilite']):.0%}] {s['titre']}\n{s['contenu'][:300]}"
        for s in signaux[:20]  # Max 20 signaux
    ])

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": f"""Tu es un analyste OSINT spécialisé en renseignement terrain pour la région '{region}'.

Voici les signaux terrain récents :

{signaux_texte}

Analyse et retourne UNIQUEMENT un JSON valide :
{{
  "chaleur": <entier 0-100, niveau d'urgence global>,
  "resume": "<résumé factuel en 2-3 phrases>",
  "evenements": ["<événement 1>", "<événement 2>", "<événement 3>"],
  "signal_partisan": "<information contradictoire ou biais détecté, ou null>",
  "post_breaking": "<si chaleur >= 70 : texte d'un post breaking X max 280 caractères, sinon null>"
}}

Critères chaleur :
- 0-30 : situation stable, pas d'urgence
- 30-60 : développements notables, à surveiller
- 60-80 : événement important, alerte modérée
- 80-100 : événement critique, breaking news

Le post_breaking doit être factuel, percutant, sans hashtags excessifs."""
            }]
        )

        texte = reponse.content[0].text.strip()
        if "```" in texte:
            texte = texte.split("```")[1]
            if texte.startswith("json"):
                texte = texte[4:]

        data = json.loads(texte)
        data["region"] = region
        data["nb_signaux"] = len(signaux)
        return data

    except json.JSONDecodeError as e:
        print(f"  ⚠️  Erreur JSON analyse terrain {region} : {e}")
        return None
    except Exception as e:
        print(f"  ⚠️  Erreur analyse terrain {region} : {e}")
        return None


def traiter_resultat_terrain(region, resultat):
    """
    Sauvegarde le résultat d'analyse terrain et déclenche le breaking si besoin.
    """
    if not resultat:
        return

    chaleur        = resultat.get("chaleur", 0)
    resume         = resultat.get("resume", "")
    evenements     = resultat.get("evenements", [])
    signal_partisan = resultat.get("signal_partisan", "")
    post_breaking  = resultat.get("post_breaking", "")

    # Sauvegarder l'alerte terrain
    sauvegarder_alerte_terrain(
        region=region,
        chaleur=chaleur,
        resume=resume,
        evenements=json.dumps(evenements, ensure_ascii=False),
        signal_partisan=signal_partisan or "",
        post_breaking=post_breaking or ""
    )

    # Marquer les signaux comme traités
    marquer_signaux_traites(region)

    print(f"  🌡️  Chaleur {region} : {chaleur}/100")
    if resume:
        print(f"  📋 {resume[:100]}...")

    # Auto-breaking si chaleur >= seuil
    if chaleur >= SEUIL_CHALEUR_BREAKING and post_breaking:
        print(f"  🔥 BREAKING déclenché ! Chaleur = {chaleur}")
        sauvegarder_post(
            region=region,
            contenu=json.dumps({"type": "breaking", "tweets": [post_breaking]},
                               ensure_ascii=False),
            style="breaking",
            statut="brouillon"
        )
        # Notification Discord
        notifier_breaking(region, chaleur, resume)
        print(f"  ✅ Post breaking sauvegardé en brouillon")


def get_briefing_terrain():
    """
    Retourne un texte résumant les dernières alertes terrain pour toutes les régions.
    Utilisé par analyst.py pour enrichir l'analyse profonde.
    """
    alertes = get_dernieres_alertes(limit=6)
    if not alertes:
        return ""

    lignes = ["=== BRIEFING TERRAIN RÉCENT ==="]
    for alerte in alertes:
        region  = alerte["region"].replace("_", " ").upper()
        chaleur = alerte["chaleur"]
        resume  = alerte["resume"]
        date    = alerte["date_creation"][:10]
        lignes.append(f"[{date}] {region} (chaleur {chaleur}/100) : {resume}")

    return "\n".join(lignes)


def analyser_tous_terrains():
    """
    Lance l'analyse terrain pour les 3 régions.
    Retourne un dict résumant les résultats.
    """
    init_db()
    print(f"\n🔥 Analyse terrain — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    regions = ["ukraine", "moyen_orient", "otan"]
    resultats = {}

    for region in regions:
        print(f"\n  📍 {region.upper().replace('_', ' ')}")
        resultat = analyser_signaux_region(region)
        traiter_resultat_terrain(region, resultat)
        resultats[region] = resultat

    print("\n✅ Analyse terrain terminée")
    return resultats


if __name__ == "__main__":
    analyser_tous_terrains()
