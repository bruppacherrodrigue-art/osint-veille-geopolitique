"""
test_editor.py — Tests de qualité de l'agent éditorial

4 scénarios :
  1. POST ANCRÉ  — faits tirés d'une vraie analyse → doit passer fact=verified/uncertain
  2. POST INVENTÉ — faits sans rapport avec les sources → doit déclencher uncertain/contradiction
  3. TON MOU     — post plein de conditionnels → doit déclencher tone=weak/soft
  4. DOUBLON     — post quasi-identique à un publié → doit déclencher doublon=duplicate/similar

Usage :
    python test_editor.py
    python test_editor.py --region ukraine        # teste une seule région
    python test_editor.py --verbose               # affiche les prompts et réponses complètes
"""

import json
import sys
import argparse
from datetime import datetime

# ──────────────────────────────────────────────────────────
# Bootstrap DB + config
# ──────────────────────────────────────────────────────────
from database import init_db, get_connection, sauvegarder_post, get_dernieres_analyses
from editor import verifier_post

init_db()

# ──────────────────────────────────────────────────────────
# Couleurs ANSI (terminal)
# ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"
WARN = f"{YELLOW}⚠️  WARN{RESET}"


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
def _insert_post(region, texte, style="platon_punk", type_post="post"):
    """Insère un post en base et retourne son id."""
    contenu = json.dumps({"type": type_post, "texte": texte}, ensure_ascii=False)
    post_id = sauvegarder_post(region=region, contenu=contenu, style=style)
    return post_id


def _run_review(post_id, verbose=False):
    """Lance la vérification éditoriale et retourne le dict review."""
    review = verifier_post(post_id)
    if verbose and review:
        print(f"\n{CYAN}--- REVIEW COMPLÈTE ---{RESET}")
        print(json.dumps(review, ensure_ascii=False, indent=2))
    return review


def _get_real_facts(region):
    """
    Récupère un fait réel depuis la dernière analyse pour construire un post ancré.
    Retourne un extrait de fait ou un texte générique si aucune analyse dispo.
    """
    analyses = get_dernieres_analyses(region, limit=1)
    if not analyses:
        return None
    try:
        data = json.loads(analyses[0]["contenu"])
        faits = data.get("faits_cles", [])
        if faits:
            return faits[0]  # Premier fait vérifié
        tendances = data.get("tendances", "")
        return tendances[:150] if tendances else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────
# TESTS
# ──────────────────────────────────────────────────────────

def test_post_ancre(region, verbose=False):
    """
    TEST 1 — Post construit à partir d'un fait réel issu d'une analyse.
    Attendu : fact_check != contradiction, verdict != rejeter
    """
    print(f"\n{BOLD}TEST 1 — Post ancré dans les sources [{region}]{RESET}")

    fait_reel = _get_real_facts(region)
    if not fait_reel:
        print(f"  {WARN} Aucune analyse disponible pour {region} — test ignoré")
        return None

    texte = (
        f"{fait_reel[:200]}. "
        f"Cette dynamique reflète les tensions actuelles dans la région. "
        f"À surveiller dans les prochaines 48h.\n"
        f"#Géopolitique #OSINT #AnalyseGéopolitique #RelationsInternationales"
    )
    print(f"  Post : {texte[:120]}...")

    post_id = _insert_post(region, texte)
    review = _run_review(post_id, verbose)

    if not review:
        print(f"  {FAIL} — Review vide (erreur API ?)")
        return False

    fact  = review.get("fact_check", {}).get("score", "?")
    tone  = review.get("tone_check", {}).get("score", "?")
    score = review.get("score_global", 0)
    verdict = review.get("verdict", "?")

    ok = fact != "contradiction" and verdict != "rejeter"
    status = PASS if ok else FAIL
    print(f"  {status} | fact={fact} tone={tone} score={score} verdict={verdict}")
    if not ok:
        print(f"    → fact_details : {review.get('fact_check', {}).get('details', '')}")
    return ok


def test_post_hallucine(region, verbose=False):
    """
    TEST 2 — Post avec des faits inventés sans lien avec les sources.
    Attendu : fact_check = uncertain ou contradiction
    """
    print(f"\n{BOLD}TEST 2 — Post halluciné / hors sources [{region}]{RESET}")

    texte = (
        "L'ambassadeur de Saturne a signé un traité de paix avec les robots de Neptune "
        "lors d'une cérémonie secrète en Antarctique. "
        "Les drones quantiques ont détruit 47 bases spatiales ennemies. "
        "Le PIB de la Lune a chuté de 312% suite à l'invasion des clones. "
        "#Géopolitique #OSINT #AnalyseGéopolitique"
    )
    print(f"  Post : {texte[:120]}...")

    post_id = _insert_post(region, texte)
    review = _run_review(post_id, verbose)

    if not review:
        print(f"  {FAIL} — Review vide (erreur API ?)")
        return False

    fact    = review.get("fact_check", {}).get("score", "?")
    score   = review.get("score_global", 0)
    verdict = review.get("verdict", "?")

    ok = fact in ("uncertain", "contradiction")
    status = PASS if ok else WARN
    print(f"  {status} | fact={fact} score={score} verdict={verdict}")
    if not ok:
        print(f"    → Attendu uncertain/contradiction, obtenu : {fact}")
        print(f"    → details : {review.get('fact_check', {}).get('details', '')}")
    return ok


def test_ton_mou(region, verbose=False):
    """
    TEST 3 — Post avec ton mou (conditionnels, formules vagues).
    Attendu : tone_check = weak ou soft
    """
    print(f"\n{BOLD}TEST 3 — Post au ton mou [{region}]{RESET}")

    texte = (
        "Il semblerait que certains experts pensent que la situation pourrait évoluer. "
        "Selon certaines sources, il est possible que des développements aient lieu. "
        "On peut penser que les acteurs régionaux devrait peut-être réagir d'une certaine façon. "
        "La situation pourrait potentiellement changer dans les prochains jours. "
        "#Géopolitique #OSINT"
    )
    print(f"  Post : {texte[:120]}...")

    post_id = _insert_post(region, texte)
    review = _run_review(post_id, verbose)

    if not review:
        print(f"  {FAIL} — Review vide (erreur API ?)")
        return False

    tone    = review.get("tone_check", {}).get("score", "?")
    score   = review.get("score_global", 0)
    verdict = review.get("verdict", "?")

    ok = tone in ("weak", "soft")
    status = PASS if ok else WARN
    print(f"  {status} | tone={tone} score={score} verdict={verdict}")
    if not ok:
        print(f"    → Attendu weak/soft, obtenu : {tone}")
        print(f"    → details : {review.get('tone_check', {}).get('details', '')}")
    return ok


def test_doublon(region, verbose=False):
    """
    TEST 4 — Deux posts quasi-identiques publiés sur la même région.
    Le second doit être détecté comme duplicate/similar.
    """
    print(f"\n{BOLD}TEST 4 — Doublon [{region}]{RESET}")

    texte_base = (
        f"SITUATION {region.upper().replace('_', ' ')} : "
        "Les frappes de missiles se sont intensifiées ce matin sur la zone industrielle. "
        "Bilan provisoire : 3 sites détruits, défense anti-aérienne débordée. "
        "Les alliés occidentaux réunis en urgence à Bruxelles. "
        "#Géopolitique #OSINT #AnalyseGéopolitique"
    )

    # Post 1 — simuler "publié" (statut publie)
    contenu1 = json.dumps({"type": "post", "texte": texte_base}, ensure_ascii=False)
    conn = get_connection()
    conn.execute(
        "INSERT INTO posts_x (region, contenu, style, statut, date_creation) VALUES (?, ?, ?, ?, ?)",
        (region, contenu1, "platon_punk", "publie", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    # Post 2 — quasi-identique → doit être marqué doublon
    texte_doublon = (
        f"FLASH {region.upper().replace('_', ' ')} : "
        "Les frappes de missiles se sont intensifiées ce matin sur la zone industrielle. "
        "Bilan : 3 sites détruits, défense anti-aérienne débordée. "
        "Les alliés occidentaux réunis en urgence à Bruxelles. "
        "#Géopolitique #OSINT #AnalyseGéopolitique"
    )
    post_id2 = _insert_post(region, texte_doublon)
    review = _run_review(post_id2, verbose)

    if not review:
        print(f"  {FAIL} — Review vide (erreur API ?)")
        return False

    doublon = review.get("doublon_check", {}).get("score", "?")
    score   = review.get("score_global", 0)
    verdict = review.get("verdict", "?")

    ok = doublon in ("duplicate", "similar")
    status = PASS if ok else WARN
    print(f"  {status} | doublon={doublon} score={score} verdict={verdict}")
    if not ok:
        print(f"    → Attendu duplicate/similar, obtenu : {doublon}")
        print(f"    → details : {review.get('doublon_check', {}).get('details', '')}")
    return ok


# ──────────────────────────────────────────────────────────
# RUNNER
# ──────────────────────────────────────────────────────────

def run_all(region="ukraine", verbose=False):
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}  TEST ÉDITEUR — région : {region.upper()}{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════{RESET}")

    resultats = {
        "ancré":     test_post_ancre(region, verbose),
        "halluciné": test_post_hallucine(region, verbose),
        "ton mou":   test_ton_mou(region, verbose),
        "doublon":   test_doublon(region, verbose),
    }

    print(f"\n{BOLD}── RÉCAPITULATIF ──────────────────────────────{RESET}")
    passes = 0
    warns  = 0
    skips  = 0
    for nom, ok in resultats.items():
        if ok is None:
            print(f"  {YELLOW}⏭  {nom.upper():12}{RESET} — ignoré (pas de données)")
            skips += 1
        elif ok:
            print(f"  {GREEN}✅ {nom.upper():12}{RESET}")
            passes += 1
        else:
            print(f"  {RED}❌ {nom.upper():12}{RESET}")
            warns += 1

    total = len([r for r in resultats.values() if r is not None])
    print(f"\n  {passes}/{total} tests passés", end="")
    if skips:
        print(f" ({skips} ignorés)", end="")
    print()

    if warns == 0 and skips == 0:
        print(f"  {GREEN}{BOLD}Éditeur opérationnel ✓{RESET}")
    elif warns == 0:
        print(f"  {YELLOW}{BOLD}Éditeur opérationnel (données insuffisantes pour certains tests){RESET}")
    else:
        print(f"  {RED}{BOLD}Éditeur à revoir — {warns} test(s) échoué(s){RESET}")

    return warns == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tests de l'agent éditorial")
    parser.add_argument("--region", default="ukraine",
                        choices=["ukraine", "moyen_orient", "otan"],
                        help="Région à tester (défaut: ukraine)")
    parser.add_argument("--verbose", action="store_true",
                        help="Affiche les reviews complètes")
    parser.add_argument("--all-regions", action="store_true",
                        help="Teste les 3 régions")
    args = parser.parse_args()

    if args.all_regions:
        overall = True
        for r in ["ukraine", "moyen_orient", "otan"]:
            ok = run_all(r, args.verbose)
            overall = overall and ok
        sys.exit(0 if overall else 1)
    else:
        ok = run_all(args.region, args.verbose)
        sys.exit(0 if ok else 1)
