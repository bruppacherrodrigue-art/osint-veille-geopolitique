"""
source_watcher.py — Agent de surveillance et réparation des sources RSS

Fonctions :
  1. Teste chaque source RSS (feedparser + timeout)
  2. Classe chaque source : ok | lent | vide | mort
  3. Pour les sources mortes : tente de découvrir une URL RSS alternative
     depuis la homepage du site (recherche des balises <link rel="alternate">)
  4. Sauvegarde les résultats en DB (sources_health)
  5. Retourne un rapport complet

Usage :
    python source_watcher.py               # teste toutes les sources
    python source_watcher.py --region ukraine
    python source_watcher.py --rapport      # affiche uniquement le rapport DB
"""

import re
import time
import argparse
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse

from database import (
    init_db, upsert_source_health,
    get_sources_health, get_sources_mortes, get_sources_health_summary
)
from sources import SOURCES_UKRAINE, SOURCES_MOYEN_ORIENT, SOURCES_OTAN, SOURCES_GLOBALES

# ──────────────────────────────────────────────────────────
# Couleurs ANSI
# ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

TOUTES_SOURCES = {
    "ukraine":      SOURCES_UKRAINE,
    "moyen_orient": SOURCES_MOYEN_ORIENT,
    "otan":         SOURCES_OTAN,
    "global":       SOURCES_GLOBALES,
}

TIMEOUT_FEED   = 12   # secondes
TIMEOUT_HTTP   = 8    # pour la découverte d'URL alternative
SEUIL_LENT_MS  = 6000 # latence > 6s = "lent"


# ──────────────────────────────────────────────────────────
# TEST D'UNE SOURCE
# ──────────────────────────────────────────────────────────
def tester_source(name, url):
    """
    Teste une source RSS via HTTP direct (sans feedparser).
    Retourne (statut, nb_articles, latence_ms)
    statut : 'ok' | 'lent' | 'vide' | 'mort'
    """
    debut = time.time()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINTBot/1.0)"}
    try:
        resp = requests.get(url, timeout=TIMEOUT_FEED, headers=headers)
        latence_ms = int((time.time() - debut) * 1000)

        if resp.status_code != 200:
            return "mort", 0, latence_ms

        body = resp.text
        # Compter les entrées RSS (<item>) ou Atom (<entry>)
        nb_items = len(re.findall(r"<item[\s>]", body, re.IGNORECASE))
        nb_entries = len(re.findall(r"<entry[\s>]", body, re.IGNORECASE))
        nb = max(nb_items, nb_entries)

        # Vérifier que c'est bien un feed RSS/Atom
        is_feed = any(tag in body[:500].lower() for tag in
                      ["<rss", "<feed", "<channel", "application/rss", "application/atom"])
        if not is_feed:
            return "mort", 0, latence_ms

        if nb == 0:
            return "vide", 0, latence_ms
        if latence_ms > SEUIL_LENT_MS:
            return "lent", nb, latence_ms
        return "ok", nb, latence_ms

    except Exception:
        latence_ms = int((time.time() - debut) * 1000)
        return "mort", 0, latence_ms


# ──────────────────────────────────────────────────────────
# DÉCOUVERTE D'URL RSS ALTERNATIVE
# ──────────────────────────────────────────────────────────
def _base_url(url):
    """Extrait l'URL de base (schéma + domaine) depuis une URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _normaliser_url(url, base):
    """Convertit une URL relative en URL absolue."""
    if url.startswith("http"):
        return url
    return urljoin(base, url)


def decouvrir_url_alternative(url_morte):
    """
    Tente de trouver une URL RSS valide depuis la homepage du domaine.
    Stratégie :
      1. Cherche les balises <link rel="alternate" type="application/rss+xml">
      2. Cherche les balises <link ... type="application/atom+xml">
      3. Essaie des chemins RSS courants (/feed, /rss, /feed.xml, /rss.xml)
    Retourne la première URL valide trouvée, ou None.
    """
    base = _base_url(url_morte)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINTBot/1.0)"}

    # Étape 1 & 2 — scraper la homepage
    try:
        resp = requests.get(base, timeout=TIMEOUT_HTTP, headers=headers)
        if resp.status_code == 200:
            html = resp.text

            # RSS + Atom
            patterns = [
                r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
                r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/atom\+xml["\']',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for candidate in matches:
                    candidate = _normaliser_url(candidate, base)
                    statut, nb, _ = tester_source("?", candidate)
                    if statut in ("ok", "lent") and nb > 0:
                        return candidate
    except Exception:
        pass

    # Étape 3 — chemins RSS communs
    chemins_courants = [
        "/feed", "/feed/", "/rss", "/rss/", "/rss.xml", "/feed.xml",
        "/feeds/posts/default", "/atom.xml", "/news/rss.xml",
    ]
    for chemin in chemins_courants:
        candidate = base + chemin
        if candidate == url_morte:
            continue
        statut, nb, _ = tester_source("?", candidate)
        if statut in ("ok", "lent") and nb > 0:
            return candidate

    return None


# ──────────────────────────────────────────────────────────
# AGENT PRINCIPAL
# ──────────────────────────────────────────────────────────
def tester_toutes_sources(region_filtre=None):
    """
    Teste toutes les sources RSS et met à jour la DB.
    Tente une réparation auto pour les sources mortes.
    Retourne un dict de résultats.
    """
    init_db()
    resultats = {}
    total = ok = lent = vide = mort = 0

    for region, sources in TOUTES_SOURCES.items():
        if region_filtre and region != region_filtre:
            continue

        print(f"\n{BOLD}{CYAN}── {region.upper().replace('_', ' ')} ──{RESET}")

        for name, url in sources.items():
            statut, nb, latence = tester_source(name, url)
            total += 1
            url_alternative = None

            if statut == "ok":
                ok += 1
                icone = f"{GREEN}✅{RESET}"
            elif statut == "lent":
                lent += 1
                icone = f"{YELLOW}🐢{RESET}"
            elif statut == "vide":
                vide += 1
                icone = f"{YELLOW}📭{RESET}"
            else:  # mort
                mort += 1
                icone = f"{RED}💀{RESET}"
                # Tenter de trouver une alternative
                print(f"  {icone} {name:30} → mort — recherche alternative...")
                url_alternative = decouvrir_url_alternative(url)
                if url_alternative:
                    print(f"      {GREEN}🔗 Alternative trouvée : {url_alternative}{RESET}")
                else:
                    print(f"      {RED}   Aucune alternative trouvée{RESET}")

            if statut != "mort":
                print(f"  {icone} {name:30} {latence:5}ms  {nb} articles")

            upsert_source_health(
                source_name=name,
                region=region,
                url=url,
                statut=statut,
                nb_articles=nb,
                latence_ms=latence,
                url_alternative=url_alternative,
            )
            resultats[name] = {
                "region": region, "statut": statut,
                "nb": nb, "latence": latence,
                "url_alternative": url_alternative,
            }

    print(f"\n{BOLD}── RÉSUMÉ ────────────────────────────────────{RESET}")
    print(f"  Total    : {total}")
    print(f"  {GREEN}✅ OK     : {ok}{RESET}")
    print(f"  {YELLOW}🐢 Lent   : {lent}{RESET}")
    print(f"  {YELLOW}📭 Vide   : {vide}{RESET}")
    print(f"  {RED}💀 Mort   : {mort}{RESET}")

    if mort > 0:
        mortes = [n for n, r in resultats.items() if r["statut"] == "mort"]
        alternatives = [n for n in mortes if resultats[n]["url_alternative"]]
        print(f"\n  Sources mortes avec alternative : {len(alternatives)}/{mort}")
        if alternatives:
            print(f"  {YELLOW}→ Mets à jour collector.py avec les URLs alternatives ci-dessus.{RESET}")

    return resultats


def afficher_rapport():
    """Affiche le rapport de santé depuis la DB."""
    sources = get_sources_health()
    if not sources:
        print("Aucune donnée — lance d'abord : python source_watcher.py")
        return

    summary = get_sources_health_summary()
    print(f"\n{BOLD}{CYAN}══ RAPPORT SANTÉ SOURCES ══{RESET}")
    for statut, n in summary.items():
        icone = {"ok": "✅", "lent": "🐢", "vide": "📭", "mort": "💀"}.get(statut, "❓")
        print(f"  {icone} {statut.upper():8} : {n}")

    mortes = get_sources_mortes()
    if mortes:
        print(f"\n{RED}{BOLD}── SOURCES MORTES / VIDES ──{RESET}")
        for s in mortes:
            alt = s["url_alternative"] or "—"
            print(f"  💀 [{s['region']:12}] {s['source_name']}")
            print(f"     URL     : {s['url']}")
            print(f"     Alt     : {alt}")
            dernier = s["dernier_test"][:16] if s["dernier_test"] else "jamais"
            print(f"     Testé   : {dernier}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Surveillance santé sources RSS")
    parser.add_argument("--region",
                        choices=["ukraine", "moyen_orient", "otan", "global"],
                        help="Tester une seule région")
    parser.add_argument("--rapport", action="store_true",
                        help="Afficher uniquement le rapport DB sans tester")
    args = parser.parse_args()

    if args.rapport:
        afficher_rapport()
    else:
        tester_toutes_sources(region_filtre=args.region)
        afficher_rapport()
