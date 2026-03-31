"""
memory.py — Mémoire contextuelle glissante 7 jours
Utilise Claude Haiku pour synthétiser et mettre à jour le contexte par région.
"""

import json
import os
from datetime import datetime, timedelta
import anthropic

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"

MEMORY_FILE = "memory_state.json"
FENETRE_JOURS = 7


def _charger_memoire():
    """Charge le fichier de mémoire JSON, retourne un dict vide si absent."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _sauvegarder_memoire(data):
    """Sauvegarde le fichier de mémoire JSON."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _nettoyer_entrees_anciennes(data):
    """Supprime les entrées de mémoire plus vieilles que FENETRE_JOURS."""
    seuil = (datetime.now() - timedelta(days=FENETRE_JOURS)).isoformat()
    for region in data:
        if "historique" in data[region]:
            data[region]["historique"] = [
                e for e in data[region]["historique"]
                if e.get("date", "") >= seuil
            ]
    return data


def get_context_for_prompt(region):
    """
    Retourne le contexte mémorisé d'une région sous forme de texte
    à injecter dans les prompts d'analyse.
    """
    data = _charger_memoire()
    if region not in data or not data[region].get("synthese"):
        return f"Aucun contexte mémorisé pour {region}."
    synthese = data[region].get("synthese", "")
    date_maj = data[region].get("date_mise_a_jour", "inconnue")
    return f"[MÉMOIRE — {region} — mise à jour {date_maj[:10]}]\n{synthese}"


def update_memory(region, nouvelles_analyses):
    """
    Met à jour la mémoire pour une région à partir des nouvelles analyses.
    Utilise Haiku pour synthétiser.

    FIX PERFORMANCE : n'est appelé que si nouvelles_analyses n'est pas vide.
    """
    if not nouvelles_analyses:
        print(f"  ℹ️  Mémoire {region} : pas de nouvelles analyses, mise à jour ignorée.")
        return

    data = _charger_memoire()
    data = _nettoyer_entrees_anciennes(data)

    if region not in data:
        data[region] = {"historique": [], "synthese": ""}

    # Ajouter les nouvelles analyses à l'historique
    for analyse in nouvelles_analyses:
        data[region]["historique"].append({
            "date": datetime.now().isoformat(),
            "contenu": str(analyse)[:500]  # résumé court pour limiter la taille
        })

    # Synthétiser via Haiku
    historique_texte = "\n---\n".join([
        f"[{e['date'][:10]}] {e['contenu']}"
        for e in data[region]["historique"][-10:]  # max 10 entrées
    ])

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"""Tu es un analyste géopolitique. Voici les dernières analyses pour la région '{region}' :

{historique_texte}

Synthétise en 5-8 phrases clés :
1. Les tendances persistantes observées
2. Les acteurs principaux en jeu
3. Les événements récents à retenir
4. Les signaux à surveiller

Sois factuel et concis. Ne répète pas les dates en détail."""
            }]
        )
        synthese = reponse.content[0].text
        data[region]["synthese"] = synthese
        data[region]["date_mise_a_jour"] = datetime.now().isoformat()
        _sauvegarder_memoire(data)
        print(f"  ✅ Mémoire mise à jour pour {region}")
    except Exception as e:
        print(f"  ⚠️  Erreur mise à jour mémoire {region} : {e}")


def afficher_memoire(region):
    """Affiche le contenu mémorisé pour une région (usage debug/dashboard)."""
    data = _charger_memoire()
    if region not in data:
        return f"Aucune mémoire pour {region}."
    return (
        f"**Synthèse ({region})**\n"
        f"{data[region].get('synthese', 'Vide')}\n\n"
        f"*Dernière mise à jour : {data[region].get('date_mise_a_jour', 'inconnue')[:16]}*\n"
        f"*Entrées historiques : {len(data[region].get('historique', []))}*"
    )


def get_toutes_regions_memoire():
    """Retourne les régions présentes en mémoire avec leur date de mise à jour."""
    data = _charger_memoire()
    return {
        region: data[region].get("date_mise_a_jour", "inconnue")
        for region in data
    }
