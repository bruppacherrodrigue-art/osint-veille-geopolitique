"""
predictions.py — Prédictions géopolitiques + vérification automatique
Utilise Sonnet + données macro + Tavily + mémoire pour générer des prédictions.
La vérification automatique score les prédictions échues via Haiku.
"""

import json
import os
from datetime import datetime
import anthropic

from database import (
    sauvegarder_prediction, get_predictions_actives,
    get_predictions_echeance, verifier_prediction, init_db
)
from memory import get_context_for_prompt
from macro import generer_briefing_macro
from scraper import generer_briefing_tendances  # Tavily actif ici

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MODEL_FAST
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL      = "claude-sonnet-4-20250514"
    CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"

PROMPT_PREDICTION = """Tu es un analyste géopolitique senior. Tu dois formuler des prédictions
rigoureuses et vérifiables sur l'évolution de la situation en {region}.

CONTEXTE MÉMORISÉ :
{contexte_memoire}

CONTEXTE MACRO :
{briefing_macro}

TENDANCES WEB RÉCENTES :
{briefing_tendances}

Génère 2-3 prédictions géopolitiques pour cette région.
Retourne UNIQUEMENT un JSON valide :
{{
  "predictions": [
    {{
      "prediction": "<énoncé clair et précis de la prédiction>",
      "horizon_jours": <nombre de jours : 7, 14, 30 ou 60>,
      "probabilite": <float entre 0.0 et 1.0>,
      "raisonnement": "<raisonnement factuel en 3-4 phrases>",
      "critere_verification": "<comment savoir si cette prédiction s'est réalisée>",
      "categorie": "<militaire|diplomatique|économique|politique|humanitaire>",
      "acteurs_cles": "<acteurs principaux impliqués>"
    }}
  ]
}}

Sois spécifique et vérifiable. Évite les prédictions vagues.
Probabilité : 0.7+ = probable, 0.5 = incertain, 0.3- = peu probable."""

PROMPT_VERIFICATION = """Tu es un fact-checker géopolitique. Voici une prédiction faite il y a {jours} jours :

PRÉDICTION : {prediction}
CRITÈRE DE VÉRIFICATION : {critere}
HORIZON PRÉVU : {horizon} jours

Date de création : {date_creation}
Date d'échéance : {date_echeance}
Aujourd'hui : {date_today}

Évalue si cette prédiction s'est réalisée.
Retourne UNIQUEMENT un JSON valide :
{{
  "resultat": "realisee|partiellement_realisee|non_realisee|indeterminee",
  "explication": "<explication factuelle en 2-3 phrases>",
  "precision_score": <float 0.0-1.0 : 1.0=exacte, 0.5=partielle, 0.0=fausse>,
  "lecons": "<leçon à retenir pour les prochaines prédictions>"
}}"""


def generer_predictions_region(region):
    """
    Génère des prédictions pour une région en combinant mémoire + macro + Tavily.
    Retourne le nombre de prédictions sauvegardées.
    """
    print(f"\n  🔮 Prédictions {region.upper().replace('_', ' ')}")

    # Rassembler le contexte
    contexte_memoire   = get_context_for_prompt(region)
    briefing_macro     = generer_briefing_macro()
    briefing_tendances = generer_briefing_tendances(region)  # Tavily actif ici

    prompt = PROMPT_PREDICTION.format(
        region=region.replace("_", " "),
        contexte_memoire=contexte_memoire or "Aucun contexte disponible.",
        briefing_macro=briefing_macro or "Données macro non disponibles.",
        briefing_tendances=briefing_tendances or "Tendances web non disponibles."
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        texte = reponse.content[0].text.strip()
        if "```" in texte:
            texte = texte.split("```")[1]
            if texte.startswith("json"):
                texte = texte[4:]

        data = json.loads(texte)
        predictions = data.get("predictions", [])
        nb = 0

        for pred in predictions:
            sauvegarder_prediction(
                region=region,
                prediction=pred.get("prediction", ""),
                horizon_jours=pred.get("horizon_jours", 30),
                probabilite=pred.get("probabilite", 0.5),
                raisonnement=pred.get("raisonnement", ""),
                critere=pred.get("critere_verification", ""),
                categorie=pred.get("categorie", "politique"),
                acteurs=pred.get("acteurs_cles", "")
            )
            nb += 1
            print(f"    ✅ {pred.get('prediction', '')[:70]}...")

        return nb

    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON invalide prédictions {region} : {e}")
        return 0
    except Exception as e:
        print(f"    ⚠️  Erreur prédictions {region} : {e}")
        return 0


def verifier_predictions_echeance():
    """
    Vérifie automatiquement les prédictions dont l'échéance est passée.
    Utilise Haiku pour scorer les résultats.
    Retourne le nombre de prédictions vérifiées.
    """
    predictions = get_predictions_echeance()
    if not predictions:
        print("  ℹ️  Aucune prédiction échue à vérifier")
        return 0

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    nb_verifie = 0

    for pred in predictions:
        pred = dict(pred)
        date_creation = pred["date_creation"][:10]
        date_echeance = pred["date_echeance"][:10]
        jours_ecoules = (
            datetime.fromisoformat(pred["date_echeance"]) -
            datetime.fromisoformat(pred["date_creation"])
        ).days

        prompt = PROMPT_VERIFICATION.format(
            prediction=pred["prediction"],
            critere=pred["critere_verification"],
            horizon=pred["horizon_jours"],
            date_creation=date_creation,
            date_echeance=date_echeance,
            date_today=datetime.now().strftime("%Y-%m-%d"),
            jours=jours_ecoules
        )

        try:
            reponse = client.messages.create(
                model=CLAUDE_MODEL_FAST,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            texte = reponse.content[0].text.strip()
            if "```" in texte:
                texte = texte.split("```")[1]
                if texte.startswith("json"):
                    texte = texte[4:]

            data = json.loads(texte)
            verifier_prediction(
                pred_id=pred["id"],
                resultat=data.get("resultat", "indeterminee"),
                explication=data.get("explication", ""),
                precision_score=data.get("precision_score", 0.0),
                lecons=data.get("lecons", "")
            )
            nb_verifie += 1
            print(f"    ✅ Prédiction #{pred['id']} vérifiée : {data.get('resultat')}")

        except Exception as e:
            print(f"    ⚠️  Erreur vérification #{pred['id']} : {e}")

    return nb_verifie


def generer_toutes_predictions():
    """
    Génère des prédictions pour les 3 régions.
    Retourne un dict résumant les résultats.
    """
    init_db()
    print(f"\n🔮 Génération prédictions — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    regions = ["ukraine", "moyen_orient", "otan"]
    resultats = {}

    for region in regions:
        nb = generer_predictions_region(region)
        resultats[region] = nb
        print(f"  → {nb} prédiction(s) pour {region}")

    total = sum(resultats.values())
    print(f"\n✅ {total} prédiction(s) générée(s) au total")
    return resultats


if __name__ == "__main__":
    generer_toutes_predictions()
