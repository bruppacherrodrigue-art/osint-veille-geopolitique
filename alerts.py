"""
alerts.py — Notifications Discord et email sur alertes critiques terrain.
"""

import os
import requests

try:
    from config import DISCORD_WEBHOOK_URL
except ImportError:
    DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

DISCORD_DISPONIBLE = bool(
    DISCORD_WEBHOOK_URL
    and DISCORD_WEBHOOK_URL != "YOUR_DISCORD_WEBHOOK_URL"
)


def envoyer_alerte_discord(titre, message, couleur=0xFF0000):
    """
    Envoie une alerte formatée sur Discord via webhook.
    couleur : 0xFF0000 = rouge (critique), 0xFF8C00 = orange (important)
    """
    if not DISCORD_DISPONIBLE:
        print("  ℹ️  Discord non configuré, alerte non envoyée.")
        return False

    embed = {
        "title": titre,
        "description": message[:4000],
        "color": couleur,
        "footer": {"text": "OSINT Veille Géopolitique"},
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    }

    payload = {"embeds": [embed]}

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        print(f"  ✅ Alerte Discord envoyée : {titre}")
        return True
    except Exception as e:
        print(f"  ⚠️  Erreur envoi Discord : {e}")
        return False


def notifier_breaking(region, chaleur, resume):
    """
    Notifie un événement breaking sur Discord.
    Appelé par analyst_terrain.py quand chaleur >= 70.
    """
    EMOJIS = {"ukraine": "🇺🇦", "moyen_orient": "🌍", "otan": "🛡️"}
    emoji = EMOJIS.get(region, "⚡")

    titre = f"{emoji} BREAKING — {region.upper().replace('_', ' ')} (chaleur {chaleur}/100)"
    message = f"**{resume}**\n\n*Généré automatiquement par le pipeline terrain.*"

    # Couleur selon intensité
    couleur = 0xFF0000 if chaleur >= 85 else 0xFF8C00

    return envoyer_alerte_discord(titre, message, couleur)


def notifier_alerte_critique(region, contenu):
    """
    Notifie une alerte critique (niveau ROUGE) détectée dans l'analyse profonde.
    """
    titre = f"🚨 ALERTE CRITIQUE — {region.upper().replace('_', ' ')}"
    return envoyer_alerte_discord(titre, contenu[:1000], couleur=0xFF0000)
