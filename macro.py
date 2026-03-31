"""
macro.py — Données macroéconomiques via FRED API + Oil Price API
Fournit un briefing macro pour predictions.py et le dashboard.
"""

import os
import requests
from datetime import datetime, timedelta

try:
    from config import FRED_API_KEY, OIL_API_KEY
except ImportError:
    FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
    OIL_API_KEY  = os.environ.get("OIL_API_KEY", "")

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Séries FRED utiles pour la géopolitique
SERIES_FRED = {
    "taux_fed":       "FEDFUNDS",       # Taux Fed Funds
    "inflation_us":   "CPIAUCSL",       # CPI USA
    "dette_us":       "GFDEBTN",        # Dette fédérale USA
    "petrole_wti":    "DCOILWTICO",     # Prix pétrole WTI
    "gaz_us":         "HENRY_HUB_GAS",  # Prix gaz naturel Henry Hub
    "indice_dollar":  "DTWEXBGS",       # Indice dollar DXY
    "vix":            "VIXCLS",         # Volatilité marchés
}


def _get_fred(series_id, nb_obs=1):
    """Récupère les dernières observations d'une série FRED."""
    if not FRED_API_KEY or FRED_API_KEY == "YOUR_FRED_API_KEY":
        return None
    try:
        params = {
            "series_id":        series_id,
            "api_key":          FRED_API_KEY,
            "file_type":        "json",
            "limit":            nb_obs,
            "sort_order":       "desc",
            "observation_start": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        }
        r = requests.get(FRED_BASE, params=params, timeout=10)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        if obs:
            return {"valeur": obs[0]["value"], "date": obs[0]["date"]}
    except Exception as e:
        print(f"  ⚠️  FRED {series_id} : {e}")
    return None


def _get_petrole_oil_api():
    """Récupère le prix du pétrole Brent via Oil Price API (fallback WTI FRED)."""
    if not OIL_API_KEY or OIL_API_KEY == "YOUR_OIL_API_KEY":
        return None
    try:
        r = requests.get(
            "https://api.oilpriceapi.com/v1/prices/latest",
            headers={"Authorization": f"Token {OIL_API_KEY}"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        prix = data.get("data", {}).get("price")
        if prix:
            return {"valeur": str(round(prix, 2)), "date": datetime.now().strftime("%Y-%m-%d")}
    except Exception as e:
        print(f"  ⚠️  Oil Price API : {e}")
    return None


def get_donnees_macro():
    """
    Retourne un dictionnaire avec les principales données macro.
    Utilisé par le dashboard et predictions.py.
    """
    donnees = {}

    # Pétrole : Oil API d'abord, FRED en fallback
    petrole = _get_petrole_oil_api()
    if not petrole:
        petrole = _get_fred("DCOILWTICO")
    donnees["petrole"] = petrole

    # Autres séries FRED
    donnees["taux_fed"]     = _get_fred("FEDFUNDS")
    donnees["inflation_us"] = _get_fred("CPIAUCSL")
    donnees["vix"]          = _get_fred("VIXCLS")
    donnees["dollar"]       = _get_fred("DTWEXBGS")

    return donnees


def generer_briefing_macro():
    """
    Retourne un texte résumant les données macro pour injection dans predictions.py.
    """
    donnees = get_donnees_macro()
    lignes = ["=== CONTEXTE MACRO ==="]

    petrole = donnees.get("petrole")
    if petrole and petrole.get("valeur") not in (None, ".", ""):
        lignes.append(f"Pétrole : {petrole['valeur']} $/baril ({petrole['date']})")

    taux = donnees.get("taux_fed")
    if taux and taux.get("valeur") not in (None, ".", ""):
        lignes.append(f"Taux Fed Funds : {taux['valeur']}% ({taux['date']})")

    inflation = donnees.get("inflation_us")
    if inflation and inflation.get("valeur") not in (None, ".", ""):
        lignes.append(f"Inflation US (CPI) : {inflation['valeur']} ({inflation['date']})")

    vix = donnees.get("vix")
    if vix and vix.get("valeur") not in (None, ".", ""):
        lignes.append(f"VIX (volatilité) : {vix['valeur']} ({vix['date']})")

    dollar = donnees.get("dollar")
    if dollar and dollar.get("valeur") not in (None, ".", ""):
        lignes.append(f"Indice dollar : {dollar['valeur']} ({dollar['date']})")

    if len(lignes) == 1:
        return ""  # Aucune donnée disponible

    return "\n".join(lignes)


def get_historique_petrole(nb_points=30):
    """Retourne l'historique du prix du pétrole pour le graphique dashboard."""
    if not FRED_API_KEY or FRED_API_KEY == "YOUR_FRED_API_KEY":
        return []
    try:
        params = {
            "series_id":        "DCOILWTICO",
            "api_key":          FRED_API_KEY,
            "file_type":        "json",
            "limit":            nb_points,
            "sort_order":       "desc",
            "observation_start": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        }
        r = requests.get(FRED_BASE, params=params, timeout=10)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        return [
            {"date": o["date"], "valeur": float(o["value"])}
            for o in obs
            if o["value"] not in (".", None)
        ]
    except Exception as e:
        print(f"  ⚠️  Historique pétrole : {e}")
        return []
