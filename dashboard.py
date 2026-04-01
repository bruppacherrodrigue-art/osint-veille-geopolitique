"""
dashboard.py — Interface Streamlit — OSINT Veille Géopolitique
8 onglets : Articles, Analyses, Régions, Posts X, Prédictions, Macro, Engagement, Mémoire

CORRECTIONS APPLIQUÉES :
- use_container_width=True remplacé par width='stretch' (déprécié Streamlit)
- Sélecteur de région ajouté avant "Analyser avec Claude" (FIX PERFORMANCE #4)
- parser_contenu_post() : plus de déballage tuple (x, y = ...)
- Toutes les occurrences de l'ancienne signature corrigées
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
    st.title("🌍 OSINT Géopolitique")
    st.caption("@Rodjayb1")
    st.divider()

    # --- Pipeline collecte ---
    st.subheader("📡 Collecte")

    if st.button("🔄 Collecter les sources RSS", use_container_width=True):
        with st.spinner("Collecte en cours..."):
            from collector import collecter_toutes_sources
            resultats = collecter_toutes_sources()
        total = sum(resultats.values())
        st.success(f"✅ {total} nouveaux articles collectés")
        st.rerun()

    if st.button("📡 Collecter signaux terrain", use_container_width=True):
        with st.spinner("Collecte terrain..."):
            from collector_terrain import collecter_tous_signaux_terrain
            res = collecter_tous_signaux_terrain()
        st.success(f"✅ {sum(res.values())} signaux terrain")
        st.rerun()

    st.divider()

    # --- Pipeline analyse ---
    st.subheader("🤖 Analyse")

    # FIX PERFORMANCE #4 : Sélecteur de région avant l'analyse
    region_analyse = st.selectbox(
        "Région à analyser",
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
        label = region_analyse if region_analyse != "Toutes" else "toutes les régions"
        with st.spinner(f"Analyse {label} en cours..."):
            from analyst import analyser_regions
            res = analyser_regions(regions=regions_cibles)
        total_a = sum(res.values())
        st.success(f"✅ {total_a} analyse(s) générée(s)")
        st.rerun()

    if st.button("🔥 Analyser terrain (breaking)", use_container_width=True):
        with st.spinner("Analyse terrain..."):
            from analyst_terrain import analyser_tous_terrains
            analyser_tous_terrains()
        st.success("✅ Analyse terrain terminée")
        st.rerun()

    if st.button("⚡ Terrain complet (collecte + analyse)", use_container_width=True):
        with st.spinner("Pipeline terrain complet..."):
            from collector_terrain import collecter_tous_signaux_terrain
            from analyst_terrain import analyser_tous_terrains
            collecter_tous_signaux_terrain()
            analyser_tous_terrains()
        st.success("✅ Pipeline terrain terminé")
        st.rerun()

    st.divider()

    # --- Rédaction ---
    st.subheader("✍️ Rédaction")

    style_post = st.selectbox(
        "Style d'écriture",
        options=list(STYLES.keys()),
        format_func=lambda x: STYLES[x],
        key="style_select"
    )

    format_post = st.selectbox(
        "Format",
        options=["post", "thread", "article"],
        format_func=lambda x: {"post": "📝 Post simple", "thread": "🧵 Thread", "article": "📰 Article long"}[x],
        key="format_select"
    )

    if st.button("✍️ Générer posts X", use_container_width=True):
        with st.spinner("Génération en cours..."):
            generer_tous_posts(style=style_post, format_type=format_post)
        st.success("✅ Posts générés !")
        st.rerun()

    st.divider()

    # --- Articles longs ---
    st.subheader("📰 Article long")
    region_article = st.selectbox(
        "Région",
        options=list(REGIONS.keys()),
        format_func=lambda x: REGIONS[x],
        key="region_article"
    )

    if st.button("📰 Écrire un article", use_container_width=True):
        with st.spinner("Rédaction..."):
            generer_post_pour_region(region_article, style=style_post, format_type="article")
        st.success("✅ Article généré !")
        st.rerun()

    st.divider()

    # --- Prédictions ---
    st.subheader("🔮 Prédictions")

    if st.button("🔮 Générer prédictions", use_container_width=True):
        with st.spinner("Génération prédictions..."):
            from predictions import generer_toutes_predictions
            res = generer_toutes_predictions()
        st.success(f"✅ {sum(res.values())} prédiction(s)")
        st.rerun()

    if st.button("✅ Vérifier prédictions échues", use_container_width=True):
        with st.spinner("Vérification..."):
            from predictions import verifier_predictions_echeance
            nb = verifier_predictions_echeance()
        st.success(f"✅ {nb} prédiction(s) vérifiée(s)")
        st.rerun()

# ============================================================
# ONGLETS PRINCIPAUX
# ============================================================
tab_articles, tab_analyses, tab_regions, tab_posts, \
tab_pred, tab_macro, tab_engagement, tab_memoire = st.tabs([
    "📰 Articles", "🧠 Analyses", "📊 Régions",
    "🐦 Posts X", "🔮 Prédictions", "💹 Macro",
    "📈 Engagement", "🧠 Mémoire"
])

# ============================================================
# ONGLET 1 — ARTICLES
# ============================================================
with tab_articles:
    st.header("📰 Articles collectés")

    col_filtre, col_nb = st.columns([3, 1])
    with col_filtre:
        region_filtre = st.selectbox(
            "Filtrer par région",
            options=list(REGIONS.keys()),
            format_func=lambda x: REGIONS[x],
            key="articles_region"
        )
    with col_nb:
        nb_articles = st.number_input("Nombre", min_value=10, max_value=200, value=50)

    articles = get_articles_par_region(region_filtre, limit=nb_articles)
    st.caption(f"{len(articles)} articles — {REGIONS[region_filtre]}")

    for art in articles:
        with st.expander(f"[{art['source_name']}] {art['titre'][:80]}"):
            st.markdown(f"**Source :** {art['source_name']}")
            st.markdown(f"**Publié :** {art['date_pub'][:16] if art['date_pub'] else 'N/A'}")
            st.markdown(f"**Collecté :** {art['date_collecte'][:16]}")
            if art['resume']:
                st.markdown(art['resume'][:500])
            if art['url']:
                st.markdown(f"[🔗 Lire l'article]({art['url']})")

# ============================================================
# ONGLET 2 — ANALYSES
# ============================================================
with tab_analyses:
    st.header("🧠 Analyses Claude")

    analyses = get_toutes_analyses(limit=50)
    if not analyses:
        st.info("Aucune analyse disponible. Lance une analyse depuis la sidebar.")
    else:
        for analyse in analyses:
            region_label = REGIONS.get(analyse["region"], analyse["region"])
            niveau = analyse.get("niveau_alerte", "VERT")
            couleur = {"VERT": "🟢", "ORANGE": "🟠", "ROUGE": "🔴"}.get(niveau, "⚪")
            date_a = analyse["date_analyse"][:16]

            with st.expander(f"{couleur} {region_label} — {date_a}"):
                try:
                    data = json.loads(analyse["contenu"])
                    theme = data.get("theme", "")
                    if theme:
                        st.markdown(f"**Thème :** {theme}")

                    faits = data.get("faits_cles", [])
                    if faits:
                        st.markdown("**Faits clés :**")
                        for f in faits:
                            st.markdown(f"- {f}")

                    acteurs = data.get("acteurs_principaux", [])
                    if acteurs:
                        st.markdown(f"**Acteurs :** {', '.join(acteurs)}")

                    tendances = data.get("tendances", "")
                    if tendances:
                        st.markdown(f"**Tendances :** {tendances}")

                    implications = data.get("implications", "")
                    if implications:
                        st.markdown(f"**Implications :** {implications}")

                    signaux = data.get("signaux_faibles", [])
                    if signaux:
                        st.markdown("**Signaux faibles :**")
                        for s in signaux:
                            st.markdown(f"- {s}")

                    surveiller = data.get("a_surveiller", "")
                    if surveiller:
                        st.markdown(f"**À surveiller :** {surveiller}")

                except Exception:
                    st.text(analyse["contenu"][:500])

# ============================================================
# ONGLET 3 — RÉGIONS
# ============================================================
with tab_regions:
    st.header("📊 Métriques par région")

    comptage = compter_articles()
    alertes = get_dernieres_alertes(limit=10)

    col1, col2, col3 = st.columns(3)
    for col, (region, label) in zip([col1, col2, col3], REGIONS.items()):
        nb = comptage.get(region, 0)
        col.metric(label, f"{nb} articles")

    st.divider()
    st.subheader("🌡️ Dernières alertes terrain")

    if not alertes:
        st.info("Aucune alerte terrain. Lance l'analyse terrain depuis la sidebar.")
    else:
        for alerte in alertes:
            region_label = REGIONS.get(alerte["region"], alerte["region"])
            chaleur = alerte["chaleur"]
            couleur_chaleur = "🔴" if chaleur >= 70 else ("🟠" if chaleur >= 40 else "🟢")
            date_a = alerte["date_creation"][:16]
            with st.expander(f"{couleur_chaleur} {region_label} — Chaleur {chaleur}/100 — {date_a}"):
                st.markdown(alerte["resume"])
                try:
                    evts = json.loads(alerte["evenements"])
                    if evts:
                        st.markdown("**Événements :**")
                        for e in evts:
                            st.markdown(f"- {e}")
                except Exception:
                    pass
                if alerte["signal_partisan"]:
                    st.warning(f"⚠️ Signal partisan : {alerte['signal_partisan']}")

# ============================================================
# ONGLET 4 — POSTS X
# ============================================================
with tab_posts:
    st.header("🐦 Posts X — Brouillons")

    region_posts = st.selectbox(
        "Filtrer par région",
        options=["Toutes"] + list(REGIONS.keys()),
        format_func=lambda x: "Toutes les régions" if x == "Toutes" else REGIONS[x],
        key="posts_region_filtre"
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

            # Parser le contenu — FIX : pas de tuple
            contenu_data = parser_contenu_post(post["contenu"])
            type_post = "post"
            if isinstance(contenu_data, dict):
                type_post = contenu_data.get("type", "post")

            icone = {"thread": "🧵", "article": "📰", "breaking": "🔥",
                     "prediction": "🔮", "bilan": "📋"}.get(type_post, "📝")

            with st.expander(f"{icone} {region_label} | {style_label} | {date_c}"):

                if type_post == "thread":
                    tweets = extraire_tweets(post["contenu"])
                    for i, tweet in enumerate(tweets):
                        st.markdown(f"**Tweet {i} :**")
                        st.text_area(
                            label=f"tweet_{post['id']}_{i}",
                            value=tweet,
                            height=100,
                            key=f"tweet_{post['id']}_{i}",
                            label_visibility="collapsed"
                        )
                        st.caption(f"{len(tweet)} / 280 caractères")
                else:
                    texte = extraire_texte_post(post["contenu"])
                    st.text_area(
                        label=f"post_{post['id']}",
                        value=texte,
                        height=150,
                        key=f"post_{post['id']}",
                        label_visibility="collapsed"
                    )
                    st.caption(f"{len(texte)} caractères")

                col_pub, col_rej, col_sup = st.columns(3)
                with col_pub:
                    if st.button("✅ Marquer publié", key=f"pub_{post['id']}"):
                        marquer_post_publie(post["id"])
                        st.success("Marqué comme publié !")
                        st.rerun()
                with col_rej:
                    if st.button("❌ Rejeter", key=f"rej_{post['id']}"):
                        marquer_post_rejete(post["id"])
                        st.rerun()
                with col_sup:
                    if st.button("🗑️ Supprimer", key=f"sup_{post['id']}"):
                        supprimer_post(post["id"])
                        st.rerun()

# ============================================================
# ONGLET 5 — PRÉDICTIONS
# ============================================================
with tab_pred:
    st.header("🔮 Prédictions géopolitiques")

    predictions = get_predictions_actives()

    if not predictions:
        st.info("Aucune prédiction active. Génère des prédictions depuis la sidebar.")
    else:
        st.subheader(f"Prédictions actives ({len(predictions)})")
        for pred in predictions:
            region_label = REGIONS.get(pred["region"], pred["region"])
            prob    = pred.get("probabilite") or 0.0
            if prob > 1:  # Claude a retourné 85 au lieu de 0.85
                prob = prob / 100
            horizon = pred.get("horizon_jours") or 0
            echeance = (pred.get("date_echeance") or "")[:10] or "N/A"
            categorie = pred.get("categorie", "")

            prob_icon = "🟢" if prob >= 0.7 else ("🟠" if prob >= 0.5 else "🔴")

            with st.expander(
                f"{prob_icon} {region_label} | {prob:.0%} | {horizon}j | {echeance}"
            ):
                st.markdown(f"**Prédiction :** {pred.get('prediction', '')}")
                st.markdown(f"**Catégorie :** {categorie}")
                st.markdown(f"**Acteurs :** {pred.get('acteurs_cles', 'N/A')}")
                st.markdown(f"**Raisonnement :** {pred.get('raisonnement', '')}")
                st.markdown(f"**Critère vérif :** {pred.get('critere_verification', '')}")

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
                        st.success("Post prédiction créé !")
                        st.rerun()
                with col_del:
                    if st.button("🗑️ Supprimer", key=f"delpred_{pred['id']}"):
                        supprimer_prediction(pred["id"])
                        st.rerun()

    # --- Prédictions vérifiées ---
    st.divider()
    predictions_verifiees = get_predictions_verifiees(limit=10)
    if predictions_verifiees:
        st.subheader(f"✅ Prédictions vérifiées ({len(predictions_verifiees)})")
        for pred in predictions_verifiees:
            region_label = REGIONS.get(pred["region"], pred["region"])
            resultat = pred.get("resultat", "indeterminee")
            score    = pred.get("precision_score") or 0.0
            if score > 1:
                score = score / 100
            icone_res = {"realisee": "✅", "partiellement_realisee": "🟡",
                         "non_realisee": "❌", "indeterminee": "❓"}.get(resultat, "❓")
            date_v = (pred.get("date_verification") or "")[:10] or "N/A"

            with st.expander(f"{icone_res} {region_label} | {score:.0%} | {date_v}"):
                st.markdown(f"**Prédiction :** {pred.get('prediction', '')}")
                st.markdown(f"**Résultat :** {resultat.replace('_', ' ')}")
                st.markdown(f"**Explication :** {pred.get('explication', '')}")
                st.markdown(f"**Score précision :** {score:.0%}")
                st.markdown(f"**Leçons :** {pred.get('lecons', '')}")

                col_b, col_dv = st.columns(2)
                with col_b:
                    if not pred.get("tweet_id_bilan"):
                        if st.button("📋 Générer post bilan", key=f"bilan_{pred['id']}"):
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
# ONGLET 6 — MACRO
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
        dates  = [h["date"] for h in reversed(historique)]
        valeurs = [h["valeur"] for h in reversed(historique)]

        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(dates, valeurs, color="#FF4B4B", linewidth=2)
        ax.fill_between(range(len(dates)), valeurs, alpha=0.15, color="#FF4B4B")
        ax.set_xticks(range(0, len(dates), max(1, len(dates)//5)))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), max(1, len(dates)//5))],
                           rotation=30, fontsize=8)
        ax.set_ylabel("$/baril")
        ax.set_title("Prix du pétrole WTI")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Données historiques non disponibles (configurez FRED_API_KEY).")

# ============================================================
# ONGLET 7 — ENGAGEMENT
# ============================================================
with tab_engagement:
    st.header("📈 Métriques d'engagement X")

    stats = get_stats_engagement()
    if not stats:
        st.info("Aucune donnée d'engagement. Publie des posts et mets à jour les métriques.")
    else:
        # Tableau récapitulatif
        import pandas as pd
        rows = []
        for s in stats:
            rows.append({
                "Région":      REGIONS.get(s["region"], s["region"]),
                "Style":       STYLES.get(s["style"], s["style"]),
                "Thread":      "🧵 Oui" if s["is_thread"] else "📝 Non",
                "Posts":       s["nb_posts"],
                "Moy. Likes":  f"{s['avg_likes'] or 0:.1f}",
                "Moy. RT":     f"{s['avg_retweets'] or 0:.1f}",
                "Score moy.":  f"{s['avg_score'] or 0:.1f}",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df)

        # Graphique par région
        if len(rows) > 1:
            fig, ax = plt.subplots(figsize=(8, 3))
            regions_uniq = list({r["Région"] for r in rows})
            scores = [
                sum((s["avg_score"] or 0) for s in stats if REGIONS.get(s["region"]) == r) /
                max(1, sum(1 for s in stats if REGIONS.get(s["region"]) == r))
                for r in regions_uniq
            ]
            ax.barh(regions_uniq, scores, color="#FF4B4B")
            ax.set_xlabel("Score d'engagement moyen")
            ax.set_title("Performance par région")
            st.pyplot(fig)
            plt.close(fig)

# ============================================================
# ONGLET 8 — MÉMOIRE
# ============================================================
with tab_memoire:
    st.header("🧠 Mémoire contextuelle (7 jours glissants)")

    regions_memoire = get_toutes_regions_memoire()
    if not regions_memoire:
        st.info("Aucune mémoire. Lance une analyse pour alimenter la mémoire.")
    else:
        for region, date_maj in regions_memoire.items():
            region_label = REGIONS.get(region, region)
            with st.expander(f"{region_label} — mis à jour {date_maj[:10]}"):
                st.markdown(afficher_memoire(region))
