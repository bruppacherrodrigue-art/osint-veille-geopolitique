"""
writer.py — Rédaction des posts X, threads, articles, prédictions, breaking
Styles : platon_punk (percutant, philosophique) | journaliste (factuel, sobre)

CORRECTIONS APPLIQUÉES :
- generer_post_pour_region() utilise les 5 dernières analyses (pas une seule)
- Les posts déjà rédigés sont injectés dans le prompt pour forcer un angle différent
- parser_contenu_post() retourne UNIQUEMENT le contenu (plus de tuple)
- Prompts thread enrichis avec structure narrative en 4 actes
- Chaque tweet reprend un élément du tweet précédent
- Tweet 4 boucle sur le tweet 1 (callback)
"""

import json
import os
from datetime import datetime
import anthropic

from database import (
    get_dernieres_analyses, get_predictions_actives,
    sauvegarder_post, get_posts_recents, init_db
)

try:
    from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, TWEET_MAX_CHARS
except ImportError:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL      = "claude-sonnet-4-20250514"
    TWEET_MAX_CHARS   = 4000

# ============================================================
# BANQUE DE HASHTAGS OPTIMISÉS PAR RÉGION
# Sélection basée sur volume de recherche X, communauté francophone,
# et visibilité cross-langue (FR + EN pour portée maximale).
# ============================================================

HASHTAGS_PAR_REGION = {
    "ukraine": [
        # Identité du conflit
        "#Ukraine", "#Russie", "#Russia", "#UkraineWar", "#GuerreEnUkraine",
        # Géopolitique & analyse
        "#Géopolitique", "#OSINT", "#RelationsInternationales",
        # Acteurs & lieux clés
        "#Zelensky", "#Poutine", "#Kremlin", "#OTAN", "#NATO",
        # Thèmes récurrents
        "#Drone", "#FrontUkrainien", "#AideUkraine", "#DefenseAerienne",
        # Communauté analytique
        "#AnalyseGéopolitique", "#SecuriteInternationale", "#Renseignement",
    ],
    "moyen_orient": [
        # Conflit principal
        "#Gaza", "#Israel", "#Israël", "#Palestine", "#GuerreAGaza",
        # Acteurs régionaux
        "#Iran", "#Hezbollah", "#Hamas", "#Liban", "#Syrie",
        # Géopolitique & analyse
        "#MoyenOrient", "#MiddleEast", "#Géopolitique", "#OSINT",
        # Thèmes récurrents
        "#CriseHumanitaire", "#Diplomatie", "#ConfitRegional",
        # Communauté analytique
        "#AnalyseGéopolitique", "#RelationsInternationales", "#SecuriteInternationale",
    ],
    "otan": [
        # Alliance & défense
        "#OTAN", "#NATO", "#DefenseEuropeenne", "#AllianceAtlantique",
        # Géographie stratégique
        "#Europe", "#Baltique", "#Pologne", "#Scandinavie",
        # Géopolitique & analyse
        "#Géopolitique", "#OSINT", "#SecuriteEuropeenne",
        # Thèmes récurrents
        "#Rearmement", "#BudgetDefense", "#ArticleV", "#Dissuasion",
        # Communauté analytique
        "#AnalyseGéopolitique", "#RelationsInternationales", "#Diplomatie",
    ],
}

HASHTAGS_COMMUNS = ["#Géopolitique", "#OSINT", "#AnalyseGéopolitique",
                    "#RelationsInternationales", "#SecuriteInternationale"]


def _get_hashtags(region):
    """Retourne la liste de hashtags disponibles pour une région."""
    return HASHTAGS_PAR_REGION.get(region, HASHTAGS_COMMUNS)


def _formater_liste_hashtags(region):
    """Retourne la liste de hashtags en texte pour injection dans les prompts."""
    tags = _get_hashtags(region)
    return " ".join(tags)


# ============================================================
# PROMPTS — POSTS SIMPLES
# ============================================================

PROMPT_POST_PLATON_PUNK = """Tu es Platon Punk, analyste géopolitique francophone radical et lucide.
Tu publies sur X (@Rodjayb1) pour un public cultivé qui veut de la profondeur, pas de la superficialité.

ANALYSES RÉCENTES ({region}) :
{analyses_texte}

POSTS DÉJÀ RÉDIGÉS (à NE PAS répéter, prendre un angle DIFFÉRENT) :
{posts_existants}

HASHTAGS DISPONIBLES (choisir 6 à 8 parmi ceux-ci) :
{hashtags_disponibles}

Rédige UN post X (max {max_chars} caractères) sur l'actualité {region} en style "platon_punk" :
- Commence par un fait brut ou une question déstabilisante
- Décrypte ce que les médias mainstream ne disent pas
- Termine par une conséquence concrète ou une question ouverte
- Ton : direct, sans condescendance, jamais vague
- Hashtags : place 6 à 8 hashtags à la FIN du post, sur une ligne séparée
  → Choisis les plus pertinents selon l'angle exact du post (pas tous les mêmes à chaque fois)
  → Mélange hashtags spécifiques (ex: #Gaza) et communautaires (ex: #OSINT #Géopolitique)
- Pas d'emojis sauf si vraiment utiles (max 2)

Retourne UNIQUEMENT le texte du post, sans guillemets ni explication."""

PROMPT_POST_JOURNALISTE = """Tu es un journaliste géopolitique francophone rigoureux.
Tu publies sur X (@Rodjayb1) pour informer clairement sur l'actualité internationale.

ANALYSES RÉCENTES ({region}) :
{analyses_texte}

POSTS DÉJÀ RÉDIGÉS (à NE PAS répéter, prendre un angle DIFFÉRENT) :
{posts_existants}

HASHTAGS DISPONIBLES (choisir 6 à 8 parmi ceux-ci) :
{hashtags_disponibles}

Rédige UN post X (max {max_chars} caractères) sur l'actualité {region} en style journalistique :
- Commence par le fait le plus important (règle de la pyramide inversée)
- Contextualise avec 1-2 éléments de fond
- Termine par l'enjeu ou la prochaine étape à surveiller
- Ton : neutre, factuel, sans jargon inutile
- Hashtags : place 6 à 8 hashtags à la FIN du post, sur une ligne séparée
  → Choisis les plus pertinents selon le sujet précis traité dans le post
  → Mélange hashtags géographiques/thématiques + hashtags communautaires (#OSINT #Géopolitique)
- Émojis autorisés mais sobres (max 3)

Retourne UNIQUEMENT le texte du post, sans guillemets ni explication."""

# ============================================================
# PROMPTS — THREADS (FIX QUALITÉ NARRATIVE)
# ============================================================

PROMPT_THREAD_BASE = """Tu es {style_label} publiant un thread X (@Rodjayb1) sur {region}.

ANALYSES RÉCENTES :
{analyses_texte}

POSTS DÉJÀ RÉDIGÉS (prendre un angle DIFFÉRENT) :
{posts_existants}

HASHTAGS DISPONIBLES (choisir 6 à 8 pour le tweet final uniquement) :
{hashtags_disponibles}

⚠️ RÈGLES ABSOLUES DU THREAD — LIS ATTENTIVEMENT :

Le thread doit se lire comme un RÉCIT en 4 actes, PAS comme 4 posts indépendants.

STRUCTURE NARRATIVE OBLIGATOIRE :
- Tweet 0 (accroche) : UNE question ou UN fait choc. Court. Donne envie de lire la suite.
  Format : "🧵 THREAD | [fait précis]. Mais personne ne pose la vraie question. ⬇️"

- Tweet 1 (acte 1 — "1/") : Développe LE MÊME fait du tweet 0. Commence par reprendre
  un mot-clé ou chiffre du tweet 0. Explique POURQUOI ce fait existe maintenant.

- Tweet 2 (acte 2 — "2/") : Commence par un connecteur lié au tweet 1 ("Et ce que les
  médias taisent :", "Ce que ça change concrètement :", "La vraie conséquence :").
  Apporte l'élément que le grand public ne sait pas.

- Tweet 3 (acte 3 — "3/") : Boucle sur le tweet 0 (callback). Reformule la question
  initiale avec les éléments révélés. Termine par une question ouverte ou un fait
  à surveiller dans les 48h.
  Hashtags ICI UNIQUEMENT (pas dans les autres tweets) : 6 à 8 hashtags sur une ligne
  séparée à la fin. Choisis dans la liste fournie les plus pertinents pour ce thread.

EXEMPLE DE BON THREAD (modèle à suivre) :
---
Tweet 0 : "🧵 THREAD | 47 drones Shahed abattus en 24h sur Zaporizhzhia. Mais personne ne pose la vraie question. ⬇️"
Tweet 1 : "1/ 47 drones, c'est 3x la moyenne hebdomadaire. Pourquoi cette saturation soudaine ? Moscou teste une nouvelle vague avant l'offensive de printemps. Les patterns de ciblage ont changé."
Tweet 2 : "2/ Ce que les médias ne disent pas : le taux d'interception ukrainien est passé de 80% à 62% en 2 semaines. La défense aérienne s'épuise. Les stocks de missiles Patriot s'amenuisent."
Tweet 3 : "3/ 47 drones abattus aujourd'hui. Combien demain si les livraisons de missiles sol-air n'arrivent pas avant le printemps ? C'est LA question des prochaines 48h.
#Ukraine #UkraineWar #GuerreEnUkraine #DefenseAerienne #OTAN #OSINT #Géopolitique #AnalyseGéopolitique"
---

EXEMPLE DE MAUVAIS THREAD (à éviter absolument) :
---
Tweet 0 : "🧵 THREAD | Situation Ukraine ⬇️"           ← trop vague
Tweet 1 : "1/ L'OTAN renforce sa présence en Baltique" ← aucun lien avec tweet 0
Tweet 2 : "2/ Le pétrole dépasse les 95$"              ← sujet différent
Tweet 3 : "3/ À surveiller. #Géopolitique"             ← sans substance
---

Chaque tweet MAX {max_chars_tweet} caractères.
Retourne UNIQUEMENT un JSON :
{{
  "tweets": ["tweet0", "tweet1", "tweet2", "tweet3"]
}}"""

# ============================================================
# PROMPTS — ARTICLES LONGS
# ============================================================

PROMPT_ARTICLE = """Tu es un rédacteur géopolitique francophone expert.
Tu rédiges un article de fond pour X (@Rodjayb1) — format long (X Premium).

ANALYSES RÉCENTES ({region}) :
{analyses_texte}

Rédige un article structuré (max {max_chars} caractères) sur la situation {region} :

HASHTAGS DISPONIBLES (choisir 6 à 8 parmi ceux-ci) :
{hashtags_disponibles}

Structure obligatoire :
📌 TITRE — accroche en gras
📍 Contexte (2-3 phrases)
⚡ Développements récents (3-4 points clés)
🔍 Analyse & implications (2-3 phrases)
🔮 À surveiller (1-2 points)
[ligne vide]
[6 à 8 hashtags sur une seule ligne — choisis dans la liste ci-dessus, les plus pertinents]

Ton : sérieux, pédagogique, jamais condescendant.
Retourne UNIQUEMENT le texte de l'article.

# ============================================================
# PROMPTS — PRÉDICTIONS
# ============================================================

PROMPT_POST_PREDICTION = """Tu es un analyste géopolitique publiant une prédiction sur X (@Rodjayb1).

PRÉDICTION :
Région : {region}
Prédiction : {prediction}
Probabilité : {probabilite:.0%}
Horizon : {horizon} jours
Raisonnement : {raisonnement}

HASHTAGS DISPONIBLES (choisir 6 à 8 parmi ceux-ci) :
{hashtags_disponibles}

Rédige un post X (max {max_chars} caractères) présentant cette prédiction :
- Formule la prédiction clairement
- Donne le raisonnement en 1-2 phrases
- Indique la probabilité et l'horizon
- Termine par le critère de vérification
- Utilise 🔮 comme emoji signature
- Place 6 à 8 hashtags sur une ligne séparée à la fin

Retourne UNIQUEMENT le texte du post.

PROMPT_BILAN_PREDICTION = """Tu es un analyste géopolitique publiant le bilan d'une prédiction sur X (@Rodjayb1).

PRÉDICTION INITIALE : {prediction}
RÉSULTAT : {resultat}
EXPLICATION : {explication}
SCORE PRÉCISION : {score:.0%}
LEÇONS : {lecons}

HASHTAGS DISPONIBLES (choisir 6 à 8 parmi ceux-ci) :
{hashtags_disponibles}

Rédige un post X (max {max_chars} caractères) faisant le bilan honnête de cette prédiction :
- Rappelle brièvement la prédiction
- Annonce le résultat clairement (réalisée / partielle / ratée)
- Explique pourquoi en 1-2 phrases
- Tire la leçon pour la suite
- Ton : honnête, sans excuses ni auto-congratulation
- Place 6 à 8 hashtags sur une ligne séparée à la fin

Retourne UNIQUEMENT le texte du post.


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def parser_contenu_post(contenu_json):
    """
    Parse le contenu JSON d'un post stocké en base.
    RETOURNE uniquement le contenu (string ou dict) — PAS de tuple.

    FIX : l'ancienne version retournait (contenu, carte).
    Plus aucun endroit du code ne doit faire : x, y = parser_contenu_post(...)
    """
    try:
        data = json.loads(contenu_json)
        return data
    except (json.JSONDecodeError, TypeError):
        return contenu_json  # Retourne tel quel si pas du JSON


def extraire_tweets(contenu_json):
    """
    Extrait la liste de tweets d'un post thread.
    Retourne une liste de strings.
    """
    data = parser_contenu_post(contenu_json)
    if isinstance(data, dict):
        return data.get("tweets", [])
    return []


def extraire_texte_post(contenu_json):
    """
    Extrait le texte principal d'un post simple.
    Retourne une string.
    """
    data = parser_contenu_post(contenu_json)
    if isinstance(data, dict):
        if "tweets" in data:
            # C'est un thread — retourner les tweets joints
            return "\n\n".join(data["tweets"])
        return data.get("texte", str(data))
    return str(data)


def _formater_analyses(analyses):
    """Formate les analyses pour injection dans les prompts."""
    if not analyses:
        return "Aucune analyse récente disponible."

    lignes = []
    for a in analyses:
        try:
            contenu = json.loads(a["contenu"])
            faits = contenu.get("faits_cles", [])
            tendances = contenu.get("tendances", "")
            niveau = contenu.get("niveau_alerte", "VERT")
            date = a["date_analyse"][:10]
            lignes.append(
                f"[{date} | Alerte {niveau}]\n"
                f"Faits clés : {'; '.join(faits[:3])}\n"
                f"Tendances : {tendances}"
            )
        except Exception:
            lignes.append(a.get("tendances", "")[:200])

    return "\n\n---\n\n".join(lignes)


def _formater_posts_existants(posts):
    """Formate les posts récents pour le prompt anti-répétition."""
    if not posts:
        return "Aucun post précédent."
    extraits = []
    for p in posts[:5]:
        texte = extraire_texte_post(p)
        extraits.append(f"• {texte[:150]}...")
    return "\n".join(extraits)


# ============================================================
# GÉNÉRATEURS PRINCIPAUX
# ============================================================

def generer_post_pour_region(region, style="platon_punk", format_type="post"):
    """
    Génère un post/thread/article pour une région.

    FIX RÉPÉTITION :
    - Utilise les 5 dernières analyses (pas une seule)
    - Injecte les posts déjà rédigés dans le prompt

    Paramètres :
    - region : "ukraine" | "moyen_orient" | "otan"
    - style : "platon_punk" | "journaliste"
    - format_type : "post" | "thread" | "article"

    Retourne l'id du post sauvegardé ou None en cas d'échec.
    """
    # Récupérer les 5 dernières analyses
    analyses = get_dernieres_analyses(region, limit=5)
    if not analyses:
        print(f"  ⚠️  Aucune analyse disponible pour {region}")
        return None

    analyses_texte = _formater_analyses(analyses)

    # Récupérer les posts récents pour éviter les répétitions
    posts_recents = get_posts_recents(region, limit=5)
    posts_existants = _formater_posts_existants(posts_recents)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        hashtags = _formater_liste_hashtags(region)

        if format_type == "thread":
            style_label = (
                "Platon Punk, analyste radical et lucide,"
                if style == "platon_punk"
                else "un journaliste géopolitique rigoureux,"
            )
            prompt = PROMPT_THREAD_BASE.format(
                style_label=style_label,
                region=region.replace("_", " "),
                analyses_texte=analyses_texte,
                posts_existants=posts_existants,
                hashtags_disponibles=hashtags,
                max_chars_tweet=280
            )
            max_tokens = 800

        elif format_type == "article":
            prompt = PROMPT_ARTICLE.format(
                region=region.replace("_", " "),
                analyses_texte=analyses_texte,
                hashtags_disponibles=hashtags,
                max_chars=TWEET_MAX_CHARS
            )
            max_tokens = 1500

        else:  # post simple
            if style == "journaliste":
                prompt = PROMPT_POST_JOURNALISTE.format(
                    region=region.replace("_", " "),
                    analyses_texte=analyses_texte,
                    posts_existants=posts_existants,
                    hashtags_disponibles=hashtags,
                    max_chars=TWEET_MAX_CHARS
                )
            else:
                prompt = PROMPT_POST_PLATON_PUNK.format(
                    region=region.replace("_", " "),
                    analyses_texte=analyses_texte,
                    posts_existants=posts_existants,
                    hashtags_disponibles=hashtags,
                    max_chars=TWEET_MAX_CHARS
                )
            max_tokens = 600

        reponse = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        texte_brut = reponse.content[0].text.strip()

        # Pour les threads, parser le JSON
        if format_type == "thread":
            try:
                clean = texte_brut
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                data = json.loads(clean)
                contenu_final = json.dumps(
                    {"type": "thread", "tweets": data.get("tweets", [])},
                    ensure_ascii=False
                )
            except Exception:
                # Fallback : sauvegarder le texte brut
                contenu_final = json.dumps(
                    {"type": "thread", "tweets": [texte_brut]},
                    ensure_ascii=False
                )
        elif format_type == "article":
            contenu_final = json.dumps(
                {"type": "article", "texte": texte_brut},
                ensure_ascii=False
            )
        else:
            contenu_final = json.dumps(
                {"type": "post", "texte": texte_brut},
                ensure_ascii=False
            )

        sauvegarder_post(region=region, contenu=contenu_final, style=style)
        print(f"  ✅ Post {format_type} ({style}) généré pour {region}")
        return contenu_final

    except Exception as e:
        print(f"  ⚠️  Erreur génération post {region} : {e}")
        return None


def generer_post_prediction(pred_id, region, prediction, probabilite,
                             horizon, raisonnement, critere):
    """Génère et sauvegarde un post annonçant une prédiction."""
    prompt = PROMPT_POST_PREDICTION.format(
        region=region.replace("_", " "),
        prediction=prediction,
        probabilite=probabilite,
        horizon=horizon,
        raisonnement=raisonnement,
        hashtags_disponibles=_formater_liste_hashtags(region),
        max_chars=TWEET_MAX_CHARS
    )
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        texte = reponse.content[0].text.strip()
        contenu = json.dumps({"type": "prediction", "texte": texte,
                              "pred_id": pred_id}, ensure_ascii=False)
        sauvegarder_post(region=region, contenu=contenu, style="prediction")
        print(f"  ✅ Post prédiction généré")
        return contenu
    except Exception as e:
        print(f"  ⚠️  Erreur post prédiction : {e}")
        return None


def generer_bilan_prediction(pred_id, region, prediction, resultat,
                              explication, score, lecons):
    """Génère et sauvegarde un post bilan d'une prédiction vérifiée."""
    prompt = PROMPT_BILAN_PREDICTION.format(
        prediction=prediction,
        resultat=resultat,
        explication=explication,
        score=score,
        lecons=lecons,
        hashtags_disponibles=_formater_liste_hashtags(region),
        max_chars=TWEET_MAX_CHARS
    )
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        reponse = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        texte = reponse.content[0].text.strip()
        contenu = json.dumps({"type": "bilan", "texte": texte,
                              "pred_id": pred_id}, ensure_ascii=False)
        sauvegarder_post(region=region, contenu=contenu, style="bilan")
        print(f"  ✅ Post bilan prédiction généré")
        return contenu
    except Exception as e:
        print(f"  ⚠️  Erreur post bilan : {e}")
        return None


def generer_tous_posts(style="platon_punk", format_type="post", regions=None):
    """
    Génère des posts pour toutes les régions (ou une liste spécifique).
    Retourne un dict résumant les résultats.
    """
    init_db()
    if regions is None:
        regions = ["ukraine", "moyen_orient", "otan"]

    print(f"\n✍️  Génération posts — style={style} format={format_type}")
    resultats = {}

    for region in regions:
        print(f"\n  📍 {region.upper().replace('_', ' ')}")
        post = generer_post_pour_region(region, style=style, format_type=format_type)
        resultats[region] = post is not None

    return resultats


if __name__ == "__main__":
    generer_tous_posts(style="platon_punk", format_type="thread")
