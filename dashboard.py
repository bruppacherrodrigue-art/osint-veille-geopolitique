"""
dashboard.py — Interface Streamlit — OSINT Veille Géopolitique
9 onglets : Breaking, Articles, Analyses, Régions, Posts X, Prédictions, Macro, Engagement, Mémoire
"""

import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime

from database import (
    init_db, get_articles_par_region, get_toutes_analyses,
    get_posts_brouillons, get_predictions_actives, get_predictions_verifiees,
    marquer_post_publie, marquer_post_rejete, supprimer_post,
    supprimer_prediction,
    get_stats_engagement, get_dernieres_alertes, compter_articles
)
from writer import (
    parser_contenu_post, extraire_tweets, extraire_texte_post,
    generer_tous_posts, generer_post_pour_region,
    generer_bilan_prediction
)
from twitter import poster_sur_x, poster_thread_sur_x
from memory import afficher_memoire, get_toutes_regions_memoire
from macro import get_donnees_macro, get_historique_petrole

# ============================================================
# CONFIGURATION PAGE
# ============================================================
st.set_page_config(
    page_title="OSINT Veille Géopolitique",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# CSS — THÈME OSINT SOMBRE
# ============================================================
st.markdown("""
<style>
/* Fond général */
.stApp { background-color: #0d1117; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
section[data-testid="stSidebar"] .stButton > button {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    transition: all 0.2s;
    font-size: 0.85rem;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #da3633;
    border-color: #da3633;
    color: white;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #8b949e;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background-color: #21262d !important;
    color: #e6edf3 !important;
    border-bottom: 2px solid #da3633 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    color: #e6edf3 !important;
}
.streamlit-expanderContent {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-top: none !important;
}

/* Métriques */
[data-testid="metric-container"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.8rem; font-weight: 700; }

/* Headers */
h1, h2, h3 { color: #e6edf3 !important; }
h1 { border-bottom: 1px solid #30363d; padding-bottom: 8px; }

/* Boutons principaux */
.stButton > button {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
}
.stButton > button:hover {
    border-color: #da3633;
    color: #da3633;
}

/* Text areas */
.stTextArea textarea {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    font-family: 'SF Mono', monospace;
    font-size: 0.85rem;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
}

/* Info/Success/Warning/Error */
.stAlert { border-radius: 6px !important; }

/* Divider */
hr { border-color: #30363d !important; }

/* Caption / small text */
.stCaption { color: #8b949e !important; }

/* Badges inline */
.badge-rouge  { background:#da3633; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-orange { background:#d97706; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-vert   { background:#1a7f37; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-region { background:#1f6feb; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)

# Init base de données
init_db()

REGIONS = {
    "ukraine":      "🇺🇦 Ukraine",
    "moyen_orient": "🌍 Moyen-Orient",
    "otan":         "🛡️ OTAN",
}

STYLES = {
    "platon_punk": "Platon Punk (percutant)",
    "journaliste": "Journaliste (factuel)",
}

# ============================================================
# SIDEBAR — ACTIONS
# ============================================================
with st.sidebar:
    st.markdown("## 🌍 OSINT Géopolitique")
    st.caption("Veille géopolitique temps réel · @Rodjayb1")
    st.divider()

    # --- Collecte ---
    with st.expander("📡 Collecte", expanded=True):
        if st.button("🔄 Sources RSS", use_container_width=True):
            with st.spinner("Collecte en cours..."):
                from collector import collecter_toutes_sources
                resultats = collecter_toutes_sources()
            total = sum(resultats.values())
            st.success(f"✅ {total} articles")
            st.rerun()

        if st.button("📡 Signaux terrain", use_container_width=True):
            with st.spinner("Collecte terrain..."):
                from collector_terrain import collecter_tous_signaux_terrain
                res = collecter_tous_signaux_terrain()
            st.success(f"✅ {sum(res.values())} signaux")
            st.rerun()

        if st.button("⚡ Terrain complet", use_container_width=True,
                     help="Collecte + analyse terrain en un clic"):
            with st.spinner("Pipeline terrain..."):
                from collector_terrain import collecter_tous_signaux_terrain
                from analyst_terrain import analyser_tous_terrains
                collecter_tous_signaux_terrain()
                analyser_tous_terrains()
            st.success("✅ Pipeline terrain terminé")
            st.rerun()

    # --- Analyse ---
    with st.expander("🤖 Analyse", expanded=True):
        region_analyse = st.selectbox(
            "Région",
            options=["Toutes", "🇺🇦 Ukraine", "🌍 Moyen-Orient", "🛡️ OTAN"],
            index=0,
            key="region_analyse_select"
        )
        MAP_REGION_ANALYSE = {
            "Toutes":          None,
            "🇺🇦 Ukraine":     ["ukraine"],
            "🌍 Moyen-Orient": ["moyen_orient"],
            "🛡️ OTAN":         ["otan"],
        }

        if st.button("🤖 Analyser avec Claude", use_container_width=True):
            regions_cibles = MAP_REGION_ANALYSE[region_analyse]
            label = region_analyse if region_analyse != "Toutes" else "toutes"
            with st.spinner(f"Analyse {label}..."):
                from analyst import analyser_regions
                res = analyser_regions(regions=regions_cibles)
            st.success(f"✅ {sum(res.values())} analyse(s)")
            st.rerun()

        if st.button("🔥 Analyser terrain", use_container_width=True):
            with st.spinner("Analyse terrain..."):
                from analyst_terrain import analyser_tous_terrains
                analyser_tous_terrains()
            st.success("✅ Terrain analysé")
            st.rerun()

    # --- Rédaction ---
    with st.expander("✍️ Rédaction", expanded=True):
        style_post = st.selectbox(
            "Style",
            options=list(STYLES.keys()),
            format_func=lambda x: STYLES[x],
            key="style_select"
        )
        format_post = st.selectbox(
            "Format",
            options=["post", "thread", "article"],
            format_func=lambda x: {"post": "📝 Post", "thread": "🧵 Thread", "article": "📰 Article"}[x],
            key="format_select"
        )
        longueur_post = st.select_slider(
            "Taille",
            options=["court", "moyen", "long"],
            value="moyen",
            key="longueur_select"
        )

        if st.button("✍️ Générer posts X", use_container_width=True):
            with st.spinner("Génération..."):
                resultats = generer_tous_posts(
                    style=style_post, format_type=format_post, longueur=longueur_post
                )
            nb_ok = sum(1 for v in resultats.values() if v) if resultats else 0
            if nb_ok > 0:
                st.success(f"✅ {nb_ok} post(s) générés")
                st.rerun()
            else:
                st.error("❌ Lance d'abord 🤖 Analyser avec Claude")

        region_article = st.selectbox(
            "Région article",
            options=list(REGIONS.keys()),
            format_func=lambda x: REGIONS[x],
            key="region_article"
        )
        if st.button("📰 Écrire un article", use_container_width=True):
            with st.spinner("Rédaction..."):
                generer_post_pour_region(region_article, style=style_post, format_type="article")
            st.success("✅ Article généré")
            st.rerun()

    # --- Prédictions ---
    with st.expander("🔮 Prédictions"):
        if st.button("🔮 Générer prédictions", use_container_width=True):
            with st.spinner("Génération..."):
                from predictions import generer_toutes_predictions
                res = generer_toutes_predictions()
            st.success(f"✅ {sum(res.values())} prédiction(s)")
            st.rerun()

        if st.button("✅ Vérifier échéances", use_container_width=True):
            with st.spinner("Vérification..."):
                from predictions import verifier_predictions_echeance
                nb = verifier_predictions_echeance()
            st.success(f"✅ {nb} vérifiée(s)")
            st.rerun()

# ============================================================
# ONGLETS PRINCIPAUX
# ============================================================
(tab_breaking, tab_articles, tab_analyses, tab_regions,
 tab_posts, tab_pred, tab_macro, tab_engagement, tab_memoire) = st.tabs([
    "🔥 Breaking", "📰 Articles", "🧠 Analyses", "📊 Régions",
    "🐦 Posts X", "🔮 Prédictions", "💹 Macro",
    "📈 Engagement", "💾 Mémoire"
])

# ============================================================
# ONGLET 1 — BREAKING / TERRAIN
# ============================================================
with tab_breaking:
    st.header("🔥 Signaux terrain — Breaking")

    col_filtre, col_nb = st.columns([3, 1])
    with col_filtre:
        region_terrain = st.selectbox(
            "Région",
            options=["Toutes"] + list(REGIONS.keys()),
            format_func=lambda x: "🌐 Toutes" if x == "Toutes" else REGIONS[x],
            key="terrain_region"
        )
    with col_nb:
        nb_alertes = st.number_input("Nombre", min_value=5, max_value=50, value=20, key="nb_alertes")

    region_filtre_terrain = None if region_terrain == "Toutes" else region_terrain
    alertes = get_dernieres_alertes(region=region_filtre_terrain, limit=nb_alertes)

    if not alertes:
        st.info("Aucun signal terrain. Lance **⚡ Terrain complet** dans la sidebar.")
    else:
        st.caption(f"{len(alertes)} signal(s) — triés par date décroissante")

        for alerte in alertes:
            region_label = REGIONS.get(alerte["region"], alerte["region"])
            chaleur = alerte.get("chaleur") or 0
            date_a  = (alerte.get("date_creation") or "")[:16]

            if chaleur >= 70:
                couleur, badge_cls = "🔴", "badge-rouge"
                niveau_txt = "CRITIQUE"
            elif chaleur >= 40:
                couleur, badge_cls = "🟠", "badge-orange"
                niveau_txt = "ÉLEVÉ"
            else:
                couleur, badge_cls = "🟢", "badge-vert"
                niveau_txt = "NORMAL"

            titre_expander = f"{couleur} {region_label} — {niveau_txt} ({chaleur}/100) — {date_a}"

            with st.expander(titre_expander):
                col_left, col_right = st.columns([2, 1])

                with col_left:
                    st.markdown(f"**Résumé :**")
                    st.markdown(alerte.get("resume", ""))

                    try:
                        evts = json.loads(alerte.get("evenements") or "[]")
                        if evts:
                            st.markdown("**Événements clés :**")
                            for e in evts:
                                st.markdown(f"- {e}")
                    except Exception:
                        pass

                with col_right:
                    st.metric("Chaleur", f"{chaleur}/100")
                    st.markdown(
                        f'<span class="{badge_cls}">{niveau_txt}</span>&nbsp;'
                        f'<span class="badge-region">{region_label}</span>',
                        unsafe_allow_html=True
                    )

                if alerte.get("signal_partisan"):
                    st.warning(f"⚠️ Signal partisan : {alerte['signal_partisan']}")

# ============================================================
# ONGLET 2 — ARTICLES
# ============================================================
with tab_articles:
    st.header("📰 Articles collectés")

    col_filtre, col_nb = st.columns([3, 1])
    with col_filtre:
        region_filtre = st.selectbox(
            "Région",
            options=list(REGIONS.keys()),
            format_func=lambda x: REGIONS[x],
            key="articles_region"
        )
    with col_nb:
        nb_articles = st.number_input("Nombre", min_value=10, max_value=200, value=50)

    articles = get_articles_par_region(region_filtre, limit=nb_articles)
    st.caption(f"{len(articles)} articles — {REGIONS[region_filtre]}")

    for art in articles:
        date_art = (art.get("date_pub") or art.get("date_collecte") or "")[:10]
        with st.expander(f"[{art['source_name']}]  {art['titre'][:90]}"):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if art.get("resume"):
                    st.markdown(art["resume"][:400])
            with col_b:
                st.caption(f"**Source** : {art['source_name']}")
                st.caption(f"**Date** : {date_art}")
                if art.get("url"):
                    st.markdown(f"[🔗 Lire l'article]({art['url']})")

# ============================================================
# ONGLET 3 — ANALYSES
# ============================================================
with tab_analyses:
    st.header("🧠 Analyses Claude")

    analyses = get_toutes_analyses(limit=50)
    if not analyses:
        st.info("Aucune analyse. Lance **🤖 Analyser avec Claude** depuis la sidebar.")
    else:
        st.caption(f"{len(analyses)} analyse(s) disponible(s)")
        for analyse in analyses:
            region_label = REGIONS.get(analyse["region"], analyse["region"])
            niveau = analyse.get("niveau_alerte", "VERT")
            date_a = analyse["date_analyse"][:16]

            couleur_map = {"VERT": ("🟢", "badge-vert"), "ORANGE": ("🟠", "badge-orange"), "ROUGE": ("🔴", "badge-rouge")}
            couleur, badge_cls = couleur_map.get(niveau, ("⚪", "badge-vert"))

            with st.expander(f"{couleur} {region_label} — {date_a}"):
                try:
                    data = json.loads(analyse["contenu"])

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        theme = data.get("theme", "")
                        if theme:
                            st.markdown(f"### {theme}")

                        faits = data.get("faits_cles", [])
                        if faits:
                            st.markdown("**📌 Faits clés**")
                            for f in faits:
                                st.markdown(f"- {f}")

                        tendances = data.get("tendances", "")
                        if tendances:
                            st.markdown(f"**📈 Tendances** : {tendances}")

                        implications = data.get("implications", "")
                        if implications:
                            st.markdown(f"**⚡ Implications** : {implications}")

                    with col2:
                        st.markdown(
                            f'<span class="{badge_cls}">{niveau}</span>',
                            unsafe_allow_html=True
                        )
                        acteurs = data.get("acteurs_principaux", [])
                        if acteurs:
                            st.markdown("**Acteurs**")
                            for a in acteurs:
                                st.markdown(f"· {a}")

                    signaux = data.get("signaux_faibles", [])
                    if signaux:
                        st.markdown("**🔍 Signaux faibles**")
                        cols_s = st.columns(min(len(signaux), 3))
                        for i, s in enumerate(signaux):
                            cols_s[i % 3].info(s)

                    surveiller = data.get("a_surveiller", "")
                    if surveiller:
                        st.warning(f"👁️ **À surveiller :** {surveiller}")

                except Exception:
                    st.text(analyse["contenu"][:500])

# ============================================================
# ONGLET 4 — RÉGIONS (vue d'ensemble)
# ============================================================
with tab_regions:
    st.header("📊 Vue d'ensemble par région")

    comptage = compter_articles()
    alertes_recentes = get_dernieres_alertes(limit=3)

    # Métriques
    col1, col2, col3 = st.columns(3)
    for col, (region, label) in zip([col1, col2, col3], REGIONS.items()):
        nb = comptage.get(region, 0)
        # Dernière alerte pour cette région
        alertes_region = get_dernieres_alertes(region=region, limit=1)
        chaleur = alertes_region[0]["chaleur"] if alertes_region else 0
        delta = f"🌡️ Chaleur {chaleur}/100" if alertes_region else "Aucun signal terrain"
        col.metric(label, f"{nb} articles", delta)

    st.divider()

    # Dernières alertes top 3 par région
    st.subheader("🌡️ Derniers signaux par région")
    for region, label in REGIONS.items():
        alertes_r = get_dernieres_alertes(region=region, limit=2)
        if alertes_r:
            derniere = alertes_r[0]
            chaleur = derniere.get("chaleur") or 0
            couleur = "🔴" if chaleur >= 70 else ("🟠" if chaleur >= 40 else "🟢")
            date_d = (derniere.get("date_creation") or "")[:16]
            st.markdown(f"**{label}** {couleur} Chaleur {chaleur}/100 — {date_d}")
            st.markdown(f"> {(derniere.get('resume') or '')[:200]}...")
        else:
            st.markdown(f"**{label}** ⚪ Aucun signal récent")
        st.divider()

# ============================================================
# ONGLET 5 — POSTS X
# ============================================================
with tab_posts:
    st.header("🐦 Posts X — Brouillons")

    region_posts = st.selectbox(
        "Filtrer par région",
        options=["Toutes"] + list(REGIONS.keys()),
        format_func=lambda x: "🌐 Toutes" if x == "Toutes" else REGIONS[x],
        key="posts_region"
    )

    posts = get_posts_brouillons(
        region=None if region_posts == "Toutes" else region_posts
    )

    if not posts:
        st.info("Aucun brouillon. Génère des posts depuis la sidebar.")
    else:
        st.caption(f"{len(posts)} brouillon(s)")

        for post in posts:
            region_label = REGIONS.get(post["region"], post["region"])
            style_label  = STYLES.get(post["style"], post["style"])
            date_c       = post["date_creation"][:16]

            contenu_data = parser_contenu_post(post["contenu"])
            type_post = "post"
            if isinstance(contenu_data, dict):
                type_post = contenu_data.get("type", "post")

            icone = {"thread": "🧵", "article": "📰", "breaking": "🔥",
                     "prediction": "🔮", "bilan": "📋"}.get(type_post, "📝")

            with st.expander(f"{icone} {region_label} · {style_label} · {date_c}"):

                if type_post == "thread":
                    tweets = extraire_tweets(post["contenu"])
                    st.caption(f"{len(tweets)} tweet(s) dans ce thread")
                    for i, tweet in enumerate(tweets):
                        st.text_area(
                            label=f"Tweet {i + 1}",
                            value=tweet,
                            height=90,
                            key=f"tweet_{post['id']}_{i}",
                        )
                        couleur_count = "🔴" if len(tweet) > 280 else "🟢"
                        st.caption(f"{couleur_count} {len(tweet)} / 280 caractères")
                else:
                    texte = extraire_texte_post(post["contenu"])
                    st.text_area(
                        label="Contenu",
                        value=texte,
                        height=130,
                        key=f"post_{post['id']}",
                    )
                    couleur_count = "🔴" if len(texte) > 280 else "🟢"
                    st.caption(f"{couleur_count} {len(texte)} caractères")

                col_x, col_pub, col_rej, col_sup = st.columns(4)
                with col_x:
                    if st.button("🐦 Poster sur X", key=f"x_{post['id']}"):
                        if type_post == "thread":
                            tweets_x = extraire_tweets(post["contenu"])
                            tid, err = poster_thread_sur_x(tweets_x)
                        else:
                            texte_x = extraire_texte_post(post["contenu"])
                            tid, err = poster_sur_x(texte_x)
                        if tid:
                            marquer_post_publie(post["id"])
                            st.success("✅ Publié sur X !")
                            st.rerun()
                        else:
                            st.error(f"❌ {err}")
                with col_pub:
                    if st.button("✅ Publié", key=f"pub_{post['id']}"):
                        marquer_post_publie(post["id"])
                        st.rerun()
                with col_rej:
                    if st.button("❌ Rejeter", key=f"rej_{post['id']}"):
                        marquer_post_rejete(post["id"])
                        st.rerun()
                with col_sup:
                    if st.button("🗑️", key=f"sup_{post['id']}"):
                        supprimer_post(post["id"])
                        st.rerun()

# ============================================================
# ONGLET 6 — PRÉDICTIONS
# ============================================================
with tab_pred:
    st.header("🔮 Prédictions géopolitiques")

    predictions = get_predictions_actives()

    if not predictions:
        st.info("Aucune prédiction active. Génère depuis la sidebar.")
    else:
        st.subheader(f"Actives ({len(predictions)})")
        for pred in predictions:
            region_label = REGIONS.get(pred["region"], pred["region"])
            prob    = pred.get("probabilite") or 0.0
            if prob > 1:
                prob = prob / 100
            horizon  = pred.get("horizon_jours") or 0
            echeance = (pred.get("date_echeance") or "")[:10] or "N/A"
            categorie = pred.get("categorie", "")

            prob_icon = "🟢" if prob >= 0.7 else ("🟠" if prob >= 0.5 else "🔴")

            with st.expander(f"{prob_icon} {region_label} · {prob:.0%} · {horizon}j · {echeance}"):
                col_p, col_m = st.columns([3, 1])
                with col_p:
                    st.markdown(f"**Prédiction :** {pred.get('prediction', '')}")
                    st.markdown(f"**Raisonnement :** {pred.get('raisonnement', '')}")
                    st.markdown(f"**Critère vérif :** {pred.get('critere_verification', '')}")
                with col_m:
                    st.metric("Probabilité", f"{prob:.0%}")
                    st.caption(f"Catégorie : {categorie}")
                    st.caption(f"Acteurs : {pred.get('acteurs_cles', 'N/A')}")

                st.progress(prob)

                col_pp, col_del = st.columns(2)
                with col_pp:
                    if st.button("🔮 Générer post", key=f"postpred_{pred['id']}"):
                        from writer import generer_post_prediction
                        generer_post_prediction(
                            pred_id=pred["id"],
                            region=pred["region"],
                            prediction=pred.get("prediction", ""),
                            probabilite=prob,
                            horizon=horizon,
                            raisonnement=pred.get("raisonnement", ""),
                            critere=pred.get("critere_verification", "")
                        )
                        st.success("Post créé !")
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Supprimer", key=f"delpred_{pred['id']}"):
                        supprimer_prediction(pred["id"])
                        st.rerun()

    st.divider()
    predictions_verifiees = get_predictions_verifiees(limit=10)
    if predictions_verifiees:
        st.subheader(f"✅ Vérifiées ({len(predictions_verifiees)})")
        for pred in predictions_verifiees:
            region_label = REGIONS.get(pred["region"], pred["region"])
            resultat = pred.get("resultat", "indeterminee")
            score    = pred.get("precision_score") or 0.0
            if score > 1:
                score = score / 100
            icone_res = {"realisee": "✅", "partiellement_realisee": "🟡",
                         "non_realisee": "❌", "indeterminee": "❓"}.get(resultat, "❓")
            date_v = (pred.get("date_verification") or "")[:10] or "N/A"

            with st.expander(f"{icone_res} {region_label} · {score:.0%} · {date_v}"):
                st.markdown(f"**Prédiction :** {pred.get('prediction', '')}")
                st.markdown(f"**Résultat :** {resultat.replace('_', ' ')}")
                st.markdown(f"**Explication :** {pred.get('explication', '')}")
                st.progress(score)
                st.caption(f"Leçons : {pred.get('lecons', '')}")

                col_b, col_dv = st.columns(2)
                with col_b:
                    if not pred.get("tweet_id_bilan"):
                        if st.button("📋 Post bilan", key=f"bilan_{pred['id']}"):
                            generer_bilan_prediction(
                                pred_id=pred["id"],
                                region=pred["region"],
                                prediction=pred.get("prediction", ""),
                                resultat=resultat,
                                explication=pred.get("explication", ""),
                                score=score,
                                lecons=pred.get("lecons", "")
                            )
                            st.success("Post bilan créé !")
                            st.rerun()
                with col_dv:
                    if st.button("🗑️ Supprimer", key=f"delpredv_{pred['id']}"):
                        supprimer_prediction(pred["id"])
                        st.rerun()

# ============================================================
# ONGLET 7 — MACRO
# ============================================================
with tab_macro:
    st.header("💹 Données macroéconomiques")

    donnees = get_donnees_macro()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        petrole = donnees.get("petrole")
        val = petrole["valeur"] if petrole and petrole.get("valeur") not in (None, ".") else "N/A"
        st.metric("🛢️ Pétrole ($/baril)", val)
    with col2:
        taux = donnees.get("taux_fed")
        val = f"{taux['valeur']}%" if taux and taux.get("valeur") not in (None, ".") else "N/A"
        st.metric("🏦 Taux Fed Funds", val)
    with col3:
        vix = donnees.get("vix")
        val = vix["valeur"] if vix and vix.get("valeur") not in (None, ".") else "N/A"
        st.metric("📉 VIX (volatilité)", val)
    with col4:
        dollar = donnees.get("dollar")
        val = dollar["valeur"] if dollar and dollar.get("valeur") not in (None, ".") else "N/A"
        st.metric("💵 Indice dollar", val)

    st.divider()
    st.subheader("📈 Historique pétrole (30 derniers points)")

    historique = get_historique_petrole(nb_points=30)
    if historique:
        dates   = [h["date"] for h in reversed(historique)]
        valeurs = [h["valeur"] for h in reversed(historique)]

        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#161b22")
        ax.plot(dates, valeurs, color="#da3633", linewidth=2)
        ax.fill_between(range(len(dates)), valeurs, alpha=0.15, color="#da3633")
        ax.set_xticks(range(0, len(dates), max(1, len(dates) // 5)))
        ax.set_xticklabels(
            [dates[i] for i in range(0, len(dates), max(1, len(dates) // 5))],
            rotation=30, fontsize=8, color="#8b949e"
        )
        ax.set_ylabel("$/baril", color="#8b949e")
        ax.set_title("Prix du pétrole WTI", color="#e6edf3")
        ax.tick_params(colors="#8b949e")
        ax.spines[:].set_color("#30363d")
        ax.grid(True, alpha=0.2, color="#30363d")
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Données historiques non disponibles (configurez FRED_API_KEY).")

# ============================================================
# ONGLET 8 — ENGAGEMENT
# ============================================================
with tab_engagement:
    st.header("📈 Métriques d'engagement X")

    stats = get_stats_engagement()
    if not stats:
        st.info("Aucune donnée d'engagement. Publie des posts et mets à jour les métriques.")
    else:
        import pandas as pd
        rows = []
        for s in stats:
            rows.append({
                "Région":     REGIONS.get(s["region"], s["region"]),
                "Style":      STYLES.get(s["style"], s["style"]),
                "Thread":     "🧵" if s["is_thread"] else "📝",
                "Posts":      s["nb_posts"],
                "Moy. Likes": f"{s['avg_likes'] or 0:.1f}",
                "Moy. RT":    f"{s['avg_retweets'] or 0:.1f}",
                "Score":      f"{s['avg_score'] or 0:.1f}",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df)

        if len(rows) > 1:
            fig, ax = plt.subplots(figsize=(8, 3))
            fig.patch.set_facecolor("#0d1117")
            ax.set_facecolor("#161b22")
            regions_uniq = list({r["Région"] for r in rows})
            scores = [
                sum((s["avg_score"] or 0) for s in stats if REGIONS.get(s["region"]) == r) /
                max(1, sum(1 for s in stats if REGIONS.get(s["region"]) == r))
                for r in regions_uniq
            ]
            ax.barh(regions_uniq, scores, color="#da3633")
            ax.set_xlabel("Score moyen", color="#8b949e")
            ax.set_title("Performance par région", color="#e6edf3")
            ax.tick_params(colors="#8b949e")
            ax.spines[:].set_color("#30363d")
            ax.grid(True, alpha=0.2, color="#30363d", axis="x")
            st.pyplot(fig)
            plt.close(fig)

# ============================================================
# ONGLET 9 — MÉMOIRE
# ============================================================
with tab_memoire:
    st.header("💾 Mémoire contextuelle (7 jours glissants)")

    regions_memoire = get_toutes_regions_memoire()
    if not regions_memoire:
        st.info("Aucune mémoire. Lance une analyse pour alimenter la mémoire.")
    else:
        for region, date_maj in regions_memoire.items():
            region_label = REGIONS.get(region, region)
            with st.expander(f"{region_label} — mis à jour {date_maj[:10]}"):
                st.markdown(afficher_memoire(region))
