"""dashboard.py — Interface Streamlit OSINT UX/UI améliorée pour rédaction"""
import streamlit as st
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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

def get_productivite_stats():
    """Récupère les métriques de productivité pour le dashboard"""
    try:
        brouillons = get_posts_brouillons()
        nb_brouillons = len(brouillons) if brouillons else 0
        
        predictions = get_predictions_actives()
        nb_predictions = len(predictions) if predictions else 0
        
        alertes = get_dernieres_alertes(limit=50)
        now = datetime.now()
        alertes_24h = [a for a in (alertes or []) if a.get("timestamp")]
        try:
            alertes_24h = [a for a in (alertes or []) 
                          if a.get("timestamp") and 
                          datetime.fromisoformat(a["timestamp"][:19]) > now - timedelta(hours=24)]
        except:
            pass
        nb_alertes_24h = len(alertes_24h)
        
        analyses = get_dernieres_analyses(limit=100)
        now = datetime.now()
        analyses_24h = []
        for a in (analyses or []):
            try:
                ts = a.get("timestamp") or a.get("created_at")
                if ts and datetime.fromisoformat(ts[:19]) > now - timedelta(hours=24):
                    analyses_24h.append(a)
            except:
                continue
        nb_analyses_24h = len(analyses_24h)
        
        return {
            "brouillons": nb_brouillons,
            "publications_24h": nb_analyses_24h,
            "alertes_breaking": nb_alertes_24h,
            "predictions_actives": nb_predictions
        }
    except Exception as e:
        return {"brouillons": 0, "publications_24h": 0, "alertes_breaking": 0, "predictions_actives": 0}

# CSS amélioré pour UX/UI human-friendly et professionnelle
st.markdown("""<style>
/* Global Dark Theme - Professional */
.stApp { background-color: #0d1117; }
section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }

/* Navigation Tabs - Style professionnel */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { 
    background-color: #21262d; 
    border-radius: 6px; 
    padding: 8px 16px; 
    border: 1px solid #30363d;
    font-weight: 500;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] { 
    background-color: #1f6feb; 
    border-color: #1f6feb; 
    color: white; 
}
.stTabs [data-baseweb="tab"]:hover { 
    background-color: #30363d; 
    border-color: #8b949e; 
}

/* Sidebar Buttons */
section[data-testid="stSidebar"] .stButton > button { 
    background-color: #21262d; 
    color: #e6edf3; 
    border: 1px solid #30363d; 
    border-radius: 6px; 
    transition: all 0.2s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover { 
    background-color: #da3633; 
    border-color: #da3633; 
    color: white; 
    transform: translateY(-1px);
}

/* Metrics Cards - Enhanced visibility */
[data-testid="metric-container"] { 
    background-color: #161b22; 
    border: 1px solid #30363d; 
    border-radius: 8px; 
    padding: 12px 16px; 
    transition: all 0.2s ease;
}
[data-testid="metric-container"]:hover {
    border-color: #1f6feb;
    box-shadow: 0 2px 8px rgba(31, 111, 235, 0.2);
}
[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.8rem; font-weight: 700; }

/* Typography */
h1, h2, h3 { color: #e6edf3 !important; }
h1 { border-bottom: 1px solid #30363d; padding-bottom: 8px; margin-bottom: 16px; }
.stCaption { color: #8b949e !important; font-size: 0.85rem; }

/* Buttons - Primary actions */
.stButton > button { 
    background-color: #21262d; 
    color: #e6edf3; 
    border: 1px solid #30363d; 
    border-radius: 6px; 
    padding: 8px 16px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:hover { 
    border-color: #1f6feb; 
    color: #1f6feb; 
    transform: translateY(-1px);
}
.stButton > button[disabled] { 
    opacity: 0.5; 
    cursor: not-allowed; 
    transform: none;
}

/* Text Areas - Editor friendly */
.stTextArea textarea { 
    background-color: #161b22 !important; 
    color: #e6edf3 !important; 
    border: 1px solid #30363d !important; 
    border-radius: 6px !important; 
    font-family: 'SF Mono', 'Monaco', monospace; 
    font-size: 0.9rem; 
    line-height: 1.6;
    padding: 12px;
}
.stTextArea textarea:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.2);
    outline: none;
}

/* Select boxes */
.stSelectbox > div > div { 
    background-color: #161b22 !important; 
    border: 1px solid #30363d !important; 
    color: #e6edf3 !important; 
    border-radius: 6px;
}

/* Alerts - Actionable messages */
.stAlert { 
    border-radius: 6px !important; 
    border-left: 4px solid;
    margin: 8px 0;
}
.stAlert-success { border-left-color: #1a7f37; background-color: rgba(26, 127, 55, 0.1); }
.stAlert-error { border-left-color: #da3633; background-color: rgba(218, 54, 51, 0.1); }
.stAlert-warning { border-left-color: #d97706; background-color: rgba(217, 119, 6, 0.1); }
.stAlert-info { border-left-color: #1f6feb; background-color: rgba(31, 111, 235, 0.1); }

/* Dividers */
hr { border-color: #30363d !important; margin: 16px 0; }

/* Badges - Status indicators */
.badge-rouge  { background:#da3633; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; }
.badge-orange { background:#d97706; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; }
.badge-vert   { background:#1a7f37; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; }
.badge-region { background:#1f6feb; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; display:inline-block; }
.badge-blue   { background:#1f6feb; color:white; padding:4px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; }

/* Workflow Progress Bar */
.workflow-step { 
    display: inline-flex; 
    align-items: center; 
    padding: 8px 16px; 
    border-radius: 20px; 
    margin-right: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
}
.workflow-step-active { background-color: #1f6feb; color: white; }
.workflow-step-completed { background-color: #1a7f37; color: white; }
.workflow-step-pending { background-color: #21262d; color: #8b949e; border: 1px solid #30363d; }

/* Validation Cards */
.validation-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    transition: all 0.2s ease;
}
.validation-card:hover {
    border-color: #1f6feb;
    box-shadow: 0 2px 8px rgba(31, 111, 235, 0.15);
}
.validation-score {
    font-size: 1.5rem;
    font-weight: 700;
    display: inline-block;
    width: 50px;
    text-align: center;
}
.score-excellent { color: #1a7f37; }
.score-good { color: #3fb950; }
.score-average { color: #d97706; }
.score-poor { color: #da3633; }

/* Accessibility - Focus states */
*:focus-visible {
    outline: 2px solid #1f6feb;
    outline-offset: 2px;
}

/* Loading states */
.stSpinner > div { border-top-color: #1f6feb !important; }

/* Expander styling */
.stExpander { 
    background-color: #161b22; 
    border: 1px solid #30363d; 
    border-radius: 6px; 
    margin: 8px 0;
}
.stExpander summary { 
    font-weight: 500; 
    color: #e6edf3;
}

/* Container spacing */
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>""", unsafe_allow_html=True)

init_db()
REGIONS = {"ukraine": "🇺🇦 Ukraine", "moyen_orient": "🌍 Moyen-Orient", "otan": "🛡️ OTAN"}
STYLES = {"platon_punk": "Platon Punk (percutant)", "journaliste": "Journaliste (factuel)"}

# Initialize session state for workflow
if "workflow_mode" not in st.session_state:
    st.session_state.workflow_mode = "veille"  # veille, redaction, analyse
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Accueil"

with st.sidebar:
    st.markdown("## 🌍 OSINT Géopolitique")
    st.caption("Veille géopolitique temps réel · @Rodjayb1")
    st.divider()
    
    # Mode de travail - Navigation contextuelle
    st.markdown("### 🎯 Mode de travail")
    
    # Get current mode from session state and map to display value
    current_mode = st.session_state.get("workflow_mode", "veille")
    REVERSE_MODE_MAP = {"veille": "👁️ Veille", "redaction": "✍️ Rédaction", "analyse": "📊 Analyse"}
    default_display = REVERSE_MODE_MAP.get(current_mode, "👁️ Veille")
    
    workflow_mode = st.segmented_control(
        "Mode",
        ["👁️ Veille", "✍️ Rédaction", "📊 Analyse"],
        key="workflow_mode_selector",
        default=default_display
    )
    
    # Map mode to internal state
    MODE_MAP = {"👁️ Veille": "veille", "✍️ Rédaction": "redaction", "📊 Analyse": "analyse"}
    st.session_state.workflow_mode = MODE_MAP.get(workflow_mode, "veille")
    
    st.divider()
    
    # Navigation principale simplifiée
    page = st.radio(
        "Navigation", 
        ["🏠 Accueil", "🚨 Breaking", "📰 Articles", "🧠 Analyses", "🗺️ Régions", "𝕏 Posts X", "🔮 Prédictions", "📈 Macro", "📊 Engagement", "💾 Mémoire"], 
        label_visibility="collapsed", 
        index=0,
        key="main_navigation"
    )
    
    st.divider()
    
    # Actions contextuelles selon le mode
    if st.session_state.workflow_mode == "veille":
        with st.expander("📡 Collecte", expanded=True):
            if st.button("🔄 Sources RSS", use_container_width=True, help="Collecter les articles des sources RSS"):
                with st.spinner("Collecte en cours..."):
                    from collector import collecter_toutes_sources
                    resultats = collecter_toutes_sources()
                st.success(f"✅ {sum(resultats.values())} articles collectés")
                st.rerun()
            if st.button("📡 Signaux terrain", use_container_width=True, help="Collecter les signaux depuis le terrain"):
                with st.spinner("Collecte terrain..."):
                    from collector_terrain import collecter_tous_signaux_terrain
                    res = collecter_tous_signaux_terrain()
                st.success(f"✅ {sum(res.values())} signaux collectés")
                st.rerun()
            if st.button("⚡ Terrain complet", use_container_width=True, help="Pipeline complet de collecte et analyse terrain"):
                with st.spinner("Pipeline terrain..."):
                    from collector_terrain import collecter_tous_signaux_terrain
                    from analyst_terrain import analyser_tous_terrains
                    collecter_tous_signaux_terrain()
                    analyser_tous_terrains()
                st.success("✅ Pipeline terrain terminé")
                st.rerun()
    
    elif st.session_state.workflow_mode == "redaction":
        with st.expander("✍️ Rédaction", expanded=True):
            style_post = st.selectbox("Style", options=list(STYLES.keys()), format_func=lambda x: STYLES[x], key="style_select")
            format_post = st.selectbox("Format", options=["post", "thread", "article"], format_func=lambda x: {"post": "📝 Post", "thread": "🧵 Thread", "article": "📰 Article"}[x], key="format_select")
            longueur_post = st.select_slider("Taille", options=["court", "moyen", "long"], value="moyen", key="longueur_select")
            if st.button("✍️ Générer posts X", use_container_width=True, help="Générer des posts pour toutes les régions"):
                with st.spinner("Génération en cours..."):
                    resultats = generer_tous_posts(style=style_post, format_type=format_post, longueur=longueur_post)
                nb_ok = sum(1 for v in resultats.values() if v) if resultats else 0
                if nb_ok > 0:
                    st.success(f"✅ {nb_ok} post(s) générés avec succès")
                    st.rerun()
                else:
                    st.error("❌ Lance d'abord l'analyse avec Claude")
            region_article = st.selectbox("Région article", options=list(REGIONS.keys()), format_func=lambda x: REGIONS[x], key="region_article")
            if st.button("📰 Écrire un article", use_container_width=True, help=f"Rédiger un article sur {REGIONS.get(region_article, region_article)}"):
                with st.spinner("Rédaction en cours..."):
                    generer_post_pour_region(region_article, style=style_post, format_type="article")
                st.success("✅ Article généré avec succès")
                st.rerun()
    
    elif st.session_state.workflow_mode == "analyse":
        with st.expander("🤖 Analyse IA", expanded=True):
            region_analyse = st.selectbox("Région", options=["Toutes", "🇺🇦 Ukraine", "🌍 Moyen-Orient", "🛡️ OTAN"], index=0, key="region_analyse_select")
            MAP_REGION_ANALYSE = {"Toutes": None, "🇺🇦 Ukraine": ["ukraine"], "🌍 Moyen-Orient": ["moyen_orient"], "🛡️ OTAN": ["otan"]}
            if st.button("🤖 Analyser avec Claude", use_container_width=True, help="Lancer l'analyse IA avec Claude"):
                regions_cibles = MAP_REGION_ANALYSE[region_analyse]
                label = region_analyse if region_analyse != "Toutes" else "toutes"
                with st.spinner(f"Analyse de {label} en cours..."):
                    from analyst import analyser_regions
                    res = analyser_regions(regions=regions_cibles)
                st.success(f"✅ {sum(res.values())} analyse(s) générée(s)")
                st.rerun()
            if st.button("🔥 Analyser terrain", use_container_width=True, help="Analyser les signaux terrain"):
                with st.spinner("Analyse terrain en cours..."):
                    from analyst_terrain import analyser_tous_terrains
                    analyser_tous_terrains()
                st.success("✅ Terrain analysé avec succès")
                st.rerun()
    
    # Santé des sources (toujours visible)
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
        if st.button("🔍 Tester toutes les sources", use_container_width=True, help="Tester la disponibilité de toutes les sources"):
            with st.spinner("Test des sources en cours..."):
                from source_watcher import tester_toutes_sources
                tester_toutes_sources()
            st.success("✅ Rapport de santé mis à jour")
            st.rerun()
    
    # Prédictions (toujours visible)
    with st.expander("🔮 Prédictions"):
        if st.button("🔮 Générer prédictions", use_container_width=True, help="Générer des prédictions géopolitiques"):
            with st.spinner("Génération en cours..."):
                from predictions import generer_toutes_predictions
                res = generer_toutes_predictions()
            st.success(f"✅ {sum(res.values())} prédiction(s) générée(s)")
            st.rerun()
        if st.button("✅ Vérifier échéances", use_container_width=True, help="Vérifier les prédictions arrivées à échéance"):
            with st.spinner("Vérification des échéances..."):
                from predictions import verifier_predictions_echeance
                nb = verifier_predictions_echeance()
            st.success(f"✅ {nb} prédiction(s) vérifiée(s)")
            st.rerun()

# Header avec dernière mise à jour et stats productivité
derniere_maj = get_last_update_info()
stats = get_productivite_stats()

# Affichage des métriques de productivité
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="📝 Brouillons",
        value=stats["brouillons"],
        help="Posts en attente de validation"
    )
with col2:
    st.metric(
        label="📰 Publications 24h",
        value=stats["publications_24h"],
        help="Analyses publiées dans les dernières 24 heures"
    )
with col3:
    st.metric(
        label="🚨 Alertes breaking",
        value=stats["alertes_breaking"],
        help="Alertes critiques détectées en 24h"
    )
with col4:
    st.metric(
        label="🔮 Prédictions actives",
        value=stats["predictions_actives"],
        help="Prédictions en cours de suivi"
    )

st.divider()

# Workflow visuel - Barre de progression
if st.session_state.workflow_mode == "redaction":
    st.markdown("### 🔄 Workflow de rédaction")
    workflow_cols = st.columns(5)
    workflow_steps = [
        ("📥 Collecte", "collecte"),
        ("🤖 Analyse", "analyse"),
        ("✍️ Rédaction", "redaction"),
        ("✅ Validation", "validation"),
        ("📤 Publication", "publication")
    ]
    
    current_step_idx = {"veille": 0, "redaction": 2, "analyse": 1}.get(st.session_state.workflow_mode, 0)
    
    for i, (label, step_id) in enumerate(workflow_steps):
        with workflow_cols[i]:
            if i < current_step_idx:
                st.markdown(f'<div class="workflow-step workflow-step-completed">✓ {label}</div>', unsafe_allow_html=True)
            elif i == current_step_idx:
                st.markdown(f'<div class="workflow-step workflow-step-active">● {label}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="workflow-step workflow-step-pending">○ {label}</div>', unsafe_allow_html=True)
    
    st.divider()
