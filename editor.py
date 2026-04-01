"""
editor.py — Agent éditorial automatique (contrôle qualité post-génération)

S'exécute après chaque génération de post/thread/article par writer.py.
Utilise Claude Haiku (rapide, ~$0.01/jour pour 10 posts).

4 vérifications :
  1. Fact-check       — compare faits du post avec les analyses sources
  2. Tone-check       — détecte les conditionnels et formules molles
  3. Style            — accroche, hashtags, structure
  4. Anti-doublon     — compare avec les 20 derniers posts publiés

Retourne un JSON stocké dans posts_x.editorial_review.
"""

import json
import os
import anthropic

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST
except ImportError:
    ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL_FAST  = "claude-haiku-4-5-20251001"

from database import (
    update_editorial_review, get_editorial_review,
    get_dernieres_analyses, get_posts_publies_recents,
    get_connection
)

# ============================================================
# PROMPT ÉDITEUR
# ============================================================
PROMPT_EDITOR = """Tu es un éditeur géopolitique expert. Tu dois évaluer la qualité d'un post rédigé pour X (Twitter).

## POST À ÉVALUER
Style attendu : {style}
Type : {type_post}

---
{texte_post}
---

## ANALYSES SOURCES (vérité terrain)
{analyses_sources}

## 20 DERNIERS POSTS PUBLIÉS (anti-doublon)
{posts_publies}

## TES 4 VÉRIFICATIONS

### 1. FACT-CHECK
Compare chaque fait/chiffre du post avec les analyses sources.
- verified = tous les faits correspondent aux sources
- uncertain = certains faits ne sont pas dans les sources (non vérifiable)
- contradiction = un fait contredit directement une analyse source

### 2. TONE-CHECK
Vérifie l'absence de :
- Conditionnels : "pourrait", "devrait", "semblerait", "il est possible que"
- Formules molles : "selon certains experts", "on peut penser que", "il semblerait"
- Pour platon_punk : ton doit être tranchant, direct, provocateur
- Pour journaliste : ton doit être factuel, affirmatif, sans fioritures
- ok = aucune faiblesse / weak = 1-2 faiblesses / soft = ton mou à réécrire

### 3. STYLE (score 0-100)
- Force de l'accroche (les 10 premiers mots) : percutante, chiffrée, ou question rhétorique ?
- Hashtags : minimum 3, maximum 5, #Géopolitique obligatoire
- Structure : saut de ligne entre accroche et développement
- Pour les threads : continuité narrative (chaque tweet reprend un élément du précédent)
- Si score < 75 : propose une VERSION AMÉLIORÉE du texte complet

### 4. ANTI-DOUBLON
Compare avec les 20 derniers posts publiés.
- original = sujet non couvert
- similar = sujet similaire mais angle différent (acceptable)
- duplicate = même sujet, même angle, à rejeter

## VERDICT GLOBAL
- publier  : score_global >= 75 ET fact=verified/uncertain ET tone=ok ET doublon=original/similar
- ameliorer: score_global 50-74 OU tone=weak OU doublon=similar
- rejeter  : score_global < 50 OU fact=contradiction OU tone=soft OU doublon=duplicate

## FORMAT DE RÉPONSE
Réponds UNIQUEMENT avec un JSON valide, sans markdown, sans explication :

{{
    "score_global": <int 0-100>,
    "fact_check": {{
        "score": "<verified|uncertain|contradiction>",
        "details": "<explication courte>"
    }},
    "tone_check": {{
        "score": "<ok|weak|soft>",
        "details": "<liste des problèmes ou 'Aucun'>"
    }},
    "style_check": {{
        "score": <int 0-100>,
        "accroche": "<évaluation de l'accroche>",
        "hashtags": "<évaluation des hashtags>"
    }},
    "doublon_check": {{
        "score": "<original|similar|duplicate>",
        "details": "<explication>"
    }},
    "version_amelioree": <"texte amélioré complet" ou null>,
    "verdict": "<publier|ameliorer|rejeter>"
}}
"""


# ============================================================
# HELPER — extraire le texte brut d'un post
# ============================================================
def _extraire_texte(contenu_json, type_post):
    """Extrait le texte d'un post pour le passer à l'éditeur."""
    try:
        data = json.loads(contenu_json)
        if type_post == "thread":
            tweets = data.get("tweets", [])
            return "\n\n---TWEET---\n\n".join(tweets)
        return data.get("texte", str(data))
    except Exception:
        return str(contenu_json)[:2000]


def _get_post_by_id(post_id):
    """Récupère un post depuis la DB."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM posts_x WHERE id = ?", (post_id,)
    ).fetchone()
    conn.close()
    return row


def _formater_analyses(analyses):
    """Formate les analyses pour le prompt éditeur."""
    if not analyses:
        return "Aucune analyse disponible."
    lignes = []
    for a in analyses[:3]:
        try:
            data = json.loads(a.get("contenu", "{}"))
            theme = data.get("theme", "")
            faits = data.get("faits_cles", [])
            tendances = data.get("tendances", "")
            lignes.append(
                f"Thème : {theme}\n"
                f"Faits : {', '.join(faits[:3])}\n"
                f"Tendances : {tendances}"
            )
        except Exception:
            lignes.append(str(a.get("tendances", ""))[:200])
    return "\n\n---\n\n".join(lignes)


def _formater_posts_publies(posts):
    """Formate les posts publiés pour l'anti-doublon."""
    if not posts:
        return "Aucun post publié récemment."
    extraits = []
    for p in posts:
        texte = _extraire_texte(p["contenu"], "post")[:120]
        region = p.get("region", "")
        extraits.append(f"[{region}] {texte}...")
    return "\n".join(extraits)


# ============================================================
# FONCTION PRINCIPALE
# ============================================================
def verifier_post(post_id):
    """
    Vérifie la qualité d'un post et sauvegarde le rapport dans editorial_review.
    Retourne le dict de review ou None en cas d'échec.
    """
    post = _get_post_by_id(post_id)
    if not post:
        print(f"  ⚠️  Editor : post {post_id} introuvable")
        return None

    region  = post.get("region", "")
    style   = post.get("style", "platon_punk")
    contenu = post.get("contenu", "")

    # Détecter le type
    try:
        data = json.loads(contenu)
        type_post = data.get("type", "post")
    except Exception:
        type_post = "post"

    texte_post    = _extraire_texte(contenu, type_post)
    analyses      = get_dernieres_analyses(region, limit=3)
    posts_publies = get_posts_publies_recents(limit=20)

    prompt = PROMPT_EDITOR.format(
        style=style,
        type_post=type_post,
        texte_post=texte_post,
        analyses_sources=_formater_analyses(analyses),
        posts_publies=_formater_posts_publies(posts_publies),
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL_FAST,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        texte_brut = reponse.content[0].text.strip()

        # Nettoyer les backticks markdown si présents
        if texte_brut.startswith("```"):
            texte_brut = texte_brut.split("```")[1]
            if texte_brut.startswith("json"):
                texte_brut = texte_brut[4:]

        review = json.loads(texte_brut)
        update_editorial_review(post_id, json.dumps(review, ensure_ascii=False))

        verdict = review.get("verdict", "?")
        score   = review.get("score_global", "?")
        print(f"  ✏️  Editor post {post_id} : {verdict.upper()} (score {score})")
        return review

    except Exception as e:
        print(f"  ⚠️  Editor erreur post {post_id} : {e}")
        return None
