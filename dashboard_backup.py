"""dashboard.py — Interface Streamlit OSINT"""
import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime
from database import (
    init_db, get_articles_par_region, get_toutes_analyses,
    get_posts_brouillons, get_predictions_actives, get_predictions_verifiees,
    marquer_post_publie, marquer_post_rejete, supprimer_post,
    supprimer_prediction, update_post_contenu,
    get_stats_engagement, get_posts_publies_avec_engagement,
    get_engagement_evolution, update_engagement,
    get_dernieres_alertes, get_sources_health_summary, get_sources_mortes,
    get_dernieres_analyses, get_sources_health
)
from writer import extraire_tweets, extraire_texte_post, generer_tous_posts, generer_post_pour_region
from twitter import poster_sur_x, poster_thread_sur_x
from memory import afficher_memoire, get_toutes_regions_memoire
from macro import get_donnees_macro, get_historique_petrole

st.set_page_config(page_title="OSINT Veille Géopolitique", page_icon="🌍", layout="wide")

def get_last_update_info():
    try:
        health = get_sources_health()
        if health:
            dernier_test = max((h.get("dernier_test") or "") for h in health if h.get("dernier_test"))
            if dernier_test:
                dt = datetime.fromisoformat(dernier_test[:19])
                diff = datetime.now() - dt
                minutes = int(diff.total_seconds() / 60)
                if minutes < 1: return "à l'instant"
                elif minutes < 60: return f"il y a {minutes} min"
                else: return f"il y a {int(minutes/60)}h{minutes%60}"
        return "inconnue"
    except: return "inconnue"

st.markdown("""<style>
.stApp { background-color: #0d1117; }
section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
section[data-testid="stSidebar"] .stButton > button { background-color: #21262d; color: #e6edf3; border: 1px solid #30363d; border-radius: 6px; }
section[data-testid="stSidebar"] .stButton > button:hover { background-color: #da3633; border-color: #da3633; color: white; }
[data-testid="metric-container"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; }
[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.8rem; font-weight: 700; }
h1, h2, h3 { color: #e6edf3 !important; }
h1 { border-bottom: 1px solid #30363d; padding-bottom: 8px; }
.stButton > button { background-color: #21262d; color: #e6edf3; border: 1px solid #30363d; border-radius: 6px; }
.stButton > button:hover { border-color: #da3633; color: #da3633; }
.stTextArea textarea { background-color: #161b22 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 6px !important; font-family: 'SF Mono', monospace; font-size: 0.85rem; }
.stSelectbox > div > div { background-color: #161b22 !important; border: 1px solid #30363d !important; color: #e6edf3 !important; }
.stAlert { border-radius: 6px !important; }
hr { border-color: #30363d !important; }
.stCaption { color: #8b949e !important; }
.badge-rouge  { background:#da3633; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-orange { background:#d97706; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-vert   { background:#1a7f37; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
.badge-region { background:#1f6feb; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; }
</style>""", unsafe_allow_html=True)

init_db()
REGIONS = {"ukraine": "🇺🇦 Ukraine", "moyen_orient": "🌍 Moyen-Orient", "otan": "🛡️ OTAN"}
STYLES = {"platon_punk": "Platon Punk (percutant)", "journaliste": "Journaliste (factuel)"}

with st.sidebar:
    st.markdown("## 🌍 OSINT Géopolitique")
    st.caption("Veille géopolitique temps réel · @Rodjayb1")
    st.divider()
    page = st.radio("Navigation", ["🏠 Accueil", "🚨 Breaking", "📰 Articles", "🧠 Analyses", "🗺️ Régions", "𝕏 Posts X", "🔮 Prédictions", "📈 Macro", "📊 Engagement", "💾 Mémoire"], label_visibility="collapsed", index=0)
    st.divider()
    with st.expander("📡 Collecte", expanded=True):
        if st.button("🔄 Sources RSS", use_container_width=True):
            with st.spinner("Collecte en cours..."):
                from collector import collecter_toutes_sources
                resultats = collecter_toutes_sources()
            st.success(f"✅ {sum(resultats.values())} articles")
            st.rerun()
        if st.button("📡 Signaux terrain", use_container_width=True):
            with st.spinner("Collecte terrain..."):
                from collector_terrain import collecter_tous_signaux_terrain
                res = collecter_tous_signaux_terrain()
            st.success(f"✅ {sum(res.values())} signaux")
            st.rerun()
        if st.button("⚡ Terrain complet", use_container_width=True):
            with st.spinner("Pipeline terrain..."):
                from collector_terrain import collecter_tous_signaux_terrain
                from analyst_terrain import analyser_tous_terrains
                collecter_tous_signaux_terrain()
                analyser_tous_terrains()
            st.success("✅ Pipeline terrain terminé")
            st.rerun()
    with st.expander("🤖 Analyse", expanded=True):
        region_analyse = st.selectbox("Région", options=["Toutes", "🇺🇦 Ukraine", "🌍 Moyen-Orient", "🛡️ OTAN"], index=0, key="region_analyse_select")
        MAP_REGION_ANALYSE = {"Toutes": None, "🇺🇦 Ukraine": ["ukraine"], "🌍 Moyen-Orient": ["moyen_orient"], "🛡️ OTAN": ["otan"]}
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
    with st.expander("✍️ Rédaction", expanded=True):
        style_post = st.selectbox("Style", options=list(STYLES.keys()), format_func=lambda x: STYLES[x], key="style_select")
        format_post = st.selectbox("Format", options=["post", "thread", "article"], format_func=lambda x: {"post": "📝 Post", "thread": "🧵 Thread", "article": "📰 Article"}[x], key="format_select")
        longueur_post = st.select_slider("Taille", options=["court", "moyen", "long"], value="moyen", key="longueur_select")
        if st.button("✍️ Générer posts X", use_container_width=True):
            with st.spinner("Génération..."):
                resultats = generer_tous_posts(style=style_post, format_type=format_post, longueur=longueur_post)
            nb_ok = sum(1 for v in resultats.values() if v) if resultats else 0
            if nb_ok > 0:
                st.success(f"✅ {nb_ok} post(s) générés")
                st.rerun()
            else:
                st.error("❌ Lance d'abord 🤖 Analyser avec Claude")
        region_article = st.selectbox("Région article", options=list(REGIONS.keys()), format_func=lambda x: REGIONS[x], key="region_article")
        if st.button("📰 Écrire un article", use_container_width=True):
            with st.spinner("Rédaction..."):
                generer_post_pour_region(region_article, style=style_post, format_type="article")
            st.success("✅ Article généré")
            st.rerun()
    with st.expander("🔍 Santé des sources"):
        summary = get_sources_health_summary()
        if summary:
            nb_ok, nb_lent = summary.get("ok", 0), summary.get("lent", 0)
            nb_mort = summary.get("mort", 0) + summary.get("vide", 0)
            st.caption(f"✅ {nb_ok} OK · 🐢 {nb_lent} lentes · 💀 {nb_mort} mortes")
            mortes = get_sources_mortes()
            if mortes:
                with st.expander(f"💀 {nb_mort} source(s) à remplacer", expanded=False):
                    for s in mortes:
                        alt = s["url_alternative"]
                        st.markdown(f"**{s['source_name']}** [{s['region']}]")
                        if alt: st.success(f"Alternative : {alt}")
                        else: st.warning("Aucune alternative détectée")
        else: st.caption("Pas encore de données — lance le test")
        if st.button("🔍 Tester toutes les sources", use_container_width=True):
            with st.spinner("Test des sources en cours..."):
                from source_watcher import tester_toutes_sources
                tester_toutes_sources()
            st.success("✅ Rapport mis à jour")
            st.rerun()
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

derniere_maj = get_last_update_info()
st.caption(f"🕒 Dernière mise à jour : {derniere_maj}")
st.divider()
