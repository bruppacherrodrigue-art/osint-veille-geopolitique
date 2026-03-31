# ============================================================
# config_example.py — EXEMPLE DE CONFIGURATION
# Renomme ce fichier en config.py et remplis tes vraies clés
# NE JAMAIS commit config.py (il est dans .gitignore)
# ============================================================

# --- Claude (Anthropic) ---
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"

# Modèles utilisés
CLAUDE_MODEL      = "claude-sonnet-4-20250514"   # analyses, prédictions, rédaction
CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"  # dédup, mémoire, terrain, scoring

# --- X / Twitter ---
X_API_KEY             = "YOUR_X_API_KEY"
X_API_SECRET          = "YOUR_X_API_SECRET"
X_ACCESS_TOKEN        = "YOUR_X_ACCESS_TOKEN"
X_ACCESS_TOKEN_SECRET = "YOUR_X_ACCESS_TOKEN_SECRET"
X_BEARER_TOKEN        = "YOUR_X_BEARER_TOKEN"

# --- FRED (Federal Reserve — gratuit) ---
# Inscription : https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "YOUR_FRED_API_KEY"

# --- Oil Price API (optionnel, FRED en fallback) ---
OIL_API_KEY = "YOUR_OIL_API_KEY"

# --- Tavily (recherche web — gratuit 1000 req/mois) ---
# Inscription : https://tavily.com
TAVILY_API_KEY = "YOUR_TAVILY_API_KEY"

# --- Discord (optionnel, pour les alertes critiques) ---
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

# --- RSSHub (pour le pipeline terrain) ---
# Par défaut l'instance publique, mais idéalement auto-hébergé
RSSHUB_BASE = "https://rsshub.app"

# ============================================================
# SOURCES RSS — Pipeline analyse profonde
# Structure : { "nom_affiché": "url_rss" }
# ============================================================

# Ukraine — sources actives
RSS_SOURCES_UKRAINE = {
    "ISW Research":       "https://www.iswresearch.org/feeds/posts/default",
    "Kyiv Independent":   "https://kyivindependent.com/feed/",
    "Ukrinform":          "https://www.ukrinform.net/rss/block-lastnews",
    "Euromaidan Press":   "https://euromaidanpress.com/feed/",
    "Ukraine World":      "https://ukraineworld.org/feed/",
    "Kyiv Post":          "https://www.kyivpost.com/feed",
    "Meduza (EN)":        "https://meduza.io/en/rss/all",
    "Bellingcat":         "https://www.bellingcat.com/feed/",
}

# Moyen-Orient — sources actives
RSS_SOURCES_MOYEN_ORIENT = {
    "Al-Monitor":         "https://www.al-monitor.com/rss",
    "Middle East Eye":    "https://www.middleeasteye.net/rss",
    "RFI Moyen-Orient":   "https://www.rfi.fr/fr/moyen-orient/rss",
    "Jerusalem Post":     "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
    "Times of Israel":    "https://www.timesofisrael.com/feed/",
    "Al Jazeera EN":      "https://www.aljazeera.com/xml/rss/all.xml",
}

# OTAN / Europe — sources actives
RSS_SOURCES_OTAN = {
    "ECFR":              "https://ecfr.eu/feed/",
    "Atlantic Council":  "https://www.atlanticcouncil.org/feed/",
    "Defense News":      "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "RFI Europe":        "https://www.rfi.fr/fr/europe/rss",
    "IRIS France":       "https://www.iris-france.org/feed/",
    "Chatham House":     "https://www.chathamhouse.org/rss.xml",
    "IISS":              "https://www.iiss.org/en/research/rss",
    "NATO Review":       "https://www.nato.int/docu/review/rss.xml",
    "RUSI":              "https://rusi.org/rss",
}

# Sources globales (multi-régions, avec auto-tagging)
RSS_SOURCES_GLOBALES = {
    "Le Monde Diplomatique": "https://www.monde-diplomatique.fr/rss",
    "Foreign Affairs":       "https://www.foreignaffairs.com/rss.xml",
    "Foreign Policy":        "https://foreignpolicy.com/feed/",
    "Bellingcat":            "https://www.bellingcat.com/feed/",
    "Reuters World":         "https://feeds.reuters.com/reuters/worldNews",
    "BBC World":             "https://feeds.bbci.co.uk/news/world/rss.xml",
    "RFI International":     "https://www.rfi.fr/fr/rss",
}

# Dictionnaire unifié utilisé par collector.py
RSS_SOURCES = {
    "ukraine":      RSS_SOURCES_UKRAINE,
    "moyen_orient": RSS_SOURCES_MOYEN_ORIENT,
    "otan":         RSS_SOURCES_OTAN,
}

# ============================================================
# PARAMÈTRES GÉNÉRAUX
# ============================================================

# Nombre max d'articles à conserver par région en base
MAX_ARTICLES_PAR_REGION = 200

# Nombre max d'analyses à conserver par région en base
MAX_ANALYSES_PAR_REGION = 50

# Seuil de chaleur terrain pour déclencher un breaking auto
SEUIL_CHALEUR_BREAKING = 70

# Budget API approximatif par cycle d'analyse (en USD)
BUDGET_API_CYCLE = 0.50

# Compte X
X_COMPTE = "@Rodjayb1"

# Longueur max d'un tweet (X Premium)
TWEET_MAX_CHARS = 4000
