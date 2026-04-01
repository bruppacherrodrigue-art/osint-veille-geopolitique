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
#
# Dernière révision : avril 2026
# Sources classées par score de pertinence décroissant (1-10)
# Perspectives : Western / Russian / Arab / Iranian / NATO / Israeli / Independent
# Catégories : breaking / analysis / think-tank / tracker / regional
# ============================================================

# ---------------------------------------------------------------------------
# UKRAINE / RUSSIE
# 15 sources, score 10 → 6, perspectives multiples
# ---------------------------------------------------------------------------
RSS_SOURCES_UKRAINE = {

    # --- Think-tanks / Analyse approfondie ---

    # [10/10] think-tank | Western | EN
    # Mises à jour quotidiennes du champ de bataille, cartes interactives
    "ISW (understandingwar.org)":   "https://www.understandingwar.org/feeds/posts/default",

    # [10/10] think-tank | Western | EN — alt ISW blog Blogger
    "ISW Research Blog":            "https://www.iswresearch.org/feeds/posts/default",

    # [9/10] analysis | Western | EN
    # Analyse stratégique US, dossiers Ukraine / politique russe
    "War on the Rocks":             "https://warontherocks.com/feed/",

    # [9/10] think-tank | Western | EN
    # Analyses OSINT, enquêtes sur crimes de guerre et désinformation
    "Bellingcat":                   "https://www.bellingcat.com/feed/",

    # [8/10] think-tank | Western | EN
    # Publications RAND sur la guerre, sécurité, politique étrangère US
    "RAND Corporation":             "https://www.rand.org/topics/international-affairs.xml",

    # --- Médias ukrainiens indépendants ---

    # [9/10] breaking | Ukrainian/Western | EN
    # Principal quotidien anglophone ukrainien, breaking + investigations
    "Kyiv Independent":             "https://kyivindependent.com/feed/",

    # [8/10] breaking | Ukrainian | EN
    # Agence nationale ukrainienne, dépêches terrain en temps réel
    "Ukrinform":                    "https://www.ukrinform.net/rss/block-lastnews",

    # [8/10] breaking | Ukrainian | EN
    # Journal indépendant fondé en 2000, investigation politique et guerre
    "Ukrainska Pravda (EN)":        "https://www.pravda.com.ua/eng/rss/",

    # [7/10] analysis | Ukrainian/Western | EN
    # Reportages longs, analyses politique intérieure ukrainienne
    "Euromaidan Press":             "https://euromaidanpress.com/feed/",

    # [7/10] breaking | Ukrainian | EN
    # Unes du Kyiv Post, couverture quotidienne
    "Kyiv Post":                    "https://www.kyivpost.com/feed",

    # --- Perspectives russes indépendantes ---

    # [9/10] breaking+analysis | Russian Independent | EN
    # Média russe indépendant en exil (Lettonie), seule voix critique russe crédible en EN
    "Meduza (EN)":                  "https://meduza.io/en/rss/all",

    # [7/10] breaking+analysis | Russian Independent | EN
    # Journal anglophone indépendant relocalisé à Amsterdam depuis 2022
    "The Moscow Times":             "https://www.themoscowtimes.com/rss/news",

    # --- Perspectives russes d'État (à traiter avec recul critique) ---

    # [6/10] breaking | Russian State | EN
    # Agence d'État russe — propagande officielle, utile pour monitorer le narratif Kremlin
    "TASS (EN)":                    "https://tass.com/rss/v2.xml",

    # --- Radio Free Europe / RFE-RL ---

    # [9/10] breaking+analysis | Western/Independent | EN
    # Couverture terrain Ukraine + Russie, journalisme dans pays à presse contrainte
    "RFE/RL Ukraine":               "https://www.rferl.org/api/zpioqivuiuv/",

    # [8/10] analysis | Western | EN+FR
    # Analyses géopolitiques mondiales incluant Ukraine/Russie
    "Geopolitical Monitor":         "https://www.geopoliticalmonitor.com/feed/",
}

# ---------------------------------------------------------------------------
# MOYEN-ORIENT (Israël / Gaza / Iran / Liban)
# 15 sources, score 10 → 6, perspectives multiples
# ---------------------------------------------------------------------------
RSS_SOURCES_MOYEN_ORIENT = {

    # --- Agences et médias de référence ---

    # [10/10] breaking | Arab/Qatari | EN
    # Principal média arabe anglophone, couverture Gaza/Iran/Liban en direct
    "Al Jazeera (EN)":              "https://www.aljazeera.com/xml/rss/all.xml",

    # [10/10] analysis+breaking | Western/Independent | EN
    # Think-tank journalistique Middle East, analyses Iran/Israel/Liban les plus fines
    "Al-Monitor":                   "https://www.al-monitor.com/rss",

    # [9/10] breaking | Arab/UK | EN
    # Couverture Palestine/Gaza centrée, angle critique vis-à-vis de l'Occident
    "Middle East Eye":              "https://www.middleeasteye.net/rss",

    # [8/10] breaking | Arab/UK | EN
    # Angle pro-palestinien, dépêches Gaza quotidiennes
    "Middle East Monitor (MEMO)":   "https://www.middleeastmonitor.com/feed/",

    # --- Perspectives israéliennes ---

    # [9/10] breaking | Israeli | EN
    # Référence israélienne anglophone, actualité IDF, diplomatie, Gaza
    "Times of Israel":              "https://www.timesofisrael.com/feed/",

    # [8/10] breaking | Israeli | EN
    # Quotidien israélien historique, dépêches sécurité et diplomatie régionale
    "Jerusalem Post":               "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",

    # --- Perspectives du Golfe ---

    # [7/10] breaking | Saudi/Gulf | EN
    # Angle saoudien/sunnite, couverture Iran, Yémen, diplomatie régionale
    "Arab News":                    "https://www.arabnews.com/rss",

    # [8/10] breaking | UAE/Pan-Arab | EN
    # Al Arabiya en anglais, second grand média panárabe, angle Gulf/UAE
    "Al Arabiya (EN)":              "https://english.alarabiya.net/tools/mrss",

    # --- Perspectives iraniennes (à lire avec recul critique) ---

    # [7/10] breaking | Iranian State | EN
    # Agence d'État iranienne — monitorer le narratif officiel téhéranais
    "IRNA (EN)":                    "https://en.irna.ir/rss",

    # [6/10] breaking | Iranian State | EN
    # Chaîne TV d'État iranienne (ex-.com, domaine .ir après saisie US)
    "PressTV":                      "https://www.presstv.ir/rss",

    # --- Think-tanks et analyses spécialisées ---

    # [9/10] think-tank | Western/Israeli | EN
    # Institut israélien de sécurité nationale, analyses Iran/Hezbollah/Gaza pointues
    "INSS Israel":                  "https://www.inss.org.il/feed/",

    # [8/10] think-tank | Western | EN
    # Analyses Moyen-Orient Carnegie, dossiers Iran nucléaire et politique arabe
    "Carnegie ME Program":          "https://carnegieendowment.org/rss/solr/?fa=region:ME",

    # [8/10] analysis | Western | EN
    # Foreign Policy section Middle East, analyses de fond
    "Foreign Policy – Middle East": "https://foreignpolicy.com/feed/",

    # --- RFI / France 24 francophones ---

    # [7/10] breaking | French/Western | FR
    # Dépêches Moyen-Orient de RFI en français, angle francophone
    "RFI Moyen-Orient":             "https://www.rfi.fr/fr/moyen-orient/rss",

    # [7/10] breaking | French/Western | FR+EN
    # France 24 section Moyen-Orient, breaking bilingue
    "France 24 Middle East":        "https://www.france24.com/en/middle-east/rss",
}

# ---------------------------------------------------------------------------
# OTAN / DÉFENSE EUROPÉENNE
# 15 sources, score 10 → 6, couverture think-tanks + médias spécialisés
# ---------------------------------------------------------------------------
RSS_SOURCES_OTAN = {

    # --- Think-tanks européens ---

    # [10/10] think-tank | European/Western | EN
    # Principale source sur politique étrangère et sécurité européenne, très suivi à Bruxelles
    "ECFR":                         "https://ecfr.eu/feed/",

    # [10/10] think-tank | Western/Transatlantic | EN
    # Atlantic Council, think-tank transatlantique, dossiers OTAN/Ukraine/Europe
    "Atlantic Council":             "https://www.atlanticcouncil.org/feed/",

    # [9/10] think-tank | UK/Western | EN
    # Chatham House, analyses stratégiques britanniques et sécurité européenne
    "Chatham House":                "https://www.chathamhouse.org/rss.xml",

    # [9/10] think-tank | UK/Western | EN
    # RUSI, Royal United Services Institute, analyses défense UK+OTAN les plus pointues
    "RUSI":                         "https://www.rusi.org/rss",

    # [9/10] think-tank | International | EN
    # IISS, autorité mondiale sur dépenses militaires (Military Balance), stratégie OTAN
    "IISS":                         "https://www.iiss.org/en/research/rss",

    # [8/10] think-tank | French | FR
    # IRIS, premier think-tank français relations internationales / défense
    "IRIS France":                  "https://www.iris-france.org/feed/",

    # [8/10] think-tank | Western | EN
    # SIPRI, données de référence armements, dépenses militaires, commerce d'armes
    "SIPRI":                        "https://www.sipri.org/rss",

    # [8/10] think-tank | US/Western | EN
    # RAND, études sécurité, politique défense US/OTAN
    "RAND Corporation":             "https://www.rand.org/topics/international-affairs.xml",

    # --- Médias spécialisés défense ---

    # [10/10] breaking+analysis | US/Western | EN
    # Breaking Defense, référence pour l'actualité industrie et politique de défense
    "Breaking Defense":             "https://breakingdefense.com/full-rss-feed/",

    # [9/10] breaking+analysis | US/Western | EN
    # Defense One, analyses politiques, budgets, technologies de défense US+OTAN
    "Defense One":                  "https://www.defenseone.com/rss/all/",

    # [8/10] breaking | US/Western | EN
    # Defense News, actualités industrie et forces armées mondiales
    "Defense News":                 "https://www.defensenews.com/arc/outboundfeeds/rss/",

    # --- Sources institutionnelles OTAN / EU ---

    # [7/10] breaking | NATO/Official | EN+FR
    # Communiqués officiels OTAN — essentiel pour les déclarations d'Alliance
    "NATO Newsroom":                "https://www.nato.int/cps/en/natolive/news_rss.xml",

    # [7/10] analysis | NATO/Official | EN+FR
    # NATO Review, articles de fond publiés par l'OTAN
    "NATO Review":                  "https://www.nato.int/docu/review/rss.xml",

    # --- RFI / France 24 ---

    # [7/10] breaking | French/Western | FR
    # RFI Europe, dépêches défense et politique européenne en français
    "RFI Europe":                   "https://www.rfi.fr/fr/europe/rss",

    # [7/10] breaking+analysis | French/Western | FR+EN
    # France 24 Europe, couverture OTAN et défense européenne
    "France 24 Europe":             "https://www.france24.com/en/europe/rss",
}

# ---------------------------------------------------------------------------
# SOURCES GLOBALES (multi-régions, auto-tagging par collector.py)
# Sources fil d'actu, wire services, think-tanks transversaux
# ---------------------------------------------------------------------------
RSS_SOURCES_GLOBALES = {

    # [10/10] breaking | Global Wire | EN — Agence de presse internationale indépendante
    "AP World News":                "https://apnews.com/world-news.rss",

    # [9/10] breaking | Western/French | FR+EN — 1re chaîne d'info internationale française
    "France 24 (EN)":               "https://www.france24.com/en/rss",

    # [9/10] breaking | British/Western | EN
    "BBC World News":               "https://feeds.bbci.co.uk/news/world/rss.xml",

    # [9/10] analysis | Western | EN — Revue de référence politique étrangère US
    "Foreign Affairs":              "https://foreignaffairs.com/rss.xml",

    # [9/10] analysis | Western | EN — Magazine géopolitique, dossiers de fond
    "Foreign Policy":               "https://foreignpolicy.com/feed/",

    # [9/10] analysis | Western | EN — Analyses guerre, stratégie, sécurité nationale US
    "War on the Rocks":             "https://warontherocks.com/feed/",

    # [8/10] analysis | Western | EN — OSINT, investigations terrain, crimes de guerre
    "Bellingcat":                   "https://www.bellingcat.com/feed/",

    # [8/10] breaking+analysis | French/Western | FR — Mensuel références, géopolitique critique
    "Le Monde Diplomatique":        "https://www.monde-diplomatique.fr/rss",

    # [8/10] breaking | French/Western | FR — Fil monde RFI
    "RFI International":            "https://www.rfi.fr/fr/rss",

    # [8/10] analysis | Western | EN — Publications RAND toutes thématiques
    "RAND Corporation":             "https://www.rand.org/topics/international-affairs.xml",

    # [7/10] breaking | Russian State | EN — Agence d'État russe (suivi narratif Kremlin)
    "TASS (EN)":                    "https://tass.com/rss/v2.xml",

    # [7/10] breaking+analysis | Global | EN — Géopolitique monitor, analyses indépendantes
    "Geopolitical Monitor":         "https://www.geopoliticalmonitor.com/feed/",
}

# ---------------------------------------------------------------------------
# Dictionnaire unifié utilisé par collector.py
# ---------------------------------------------------------------------------
RSS_SOURCES = {
    "ukraine":      RSS_SOURCES_UKRAINE,
    "moyen_orient": RSS_SOURCES_MOYEN_ORIENT,
    "otan":         RSS_SOURCES_OTAN,
}

# ---------------------------------------------------------------------------
# MÉTADONNÉES DES SOURCES (pour scoring et filtrage dans analyst.py)
# Format : { "nom_affiché": {"category": ..., "perspective": ..., "score": ...} }
# ---------------------------------------------------------------------------
RSS_SOURCES_META = {
    # Ukraine / Russie
    "ISW (understandingwar.org)":   {"category": "think-tank",  "perspective": "Western",             "score": 10},
    "ISW Research Blog":            {"category": "think-tank",  "perspective": "Western",             "score": 10},
    "War on the Rocks":             {"category": "analysis",    "perspective": "Western",             "score": 9},
    "Bellingcat":                   {"category": "tracker",     "perspective": "Independent",         "score": 9},
    "RAND Corporation":             {"category": "think-tank",  "perspective": "Western",             "score": 8},
    "Kyiv Independent":             {"category": "breaking",    "perspective": "Ukrainian/Western",   "score": 9},
    "Ukrinform":                    {"category": "breaking",    "perspective": "Ukrainian",           "score": 8},
    "Ukrainska Pravda (EN)":        {"category": "breaking",    "perspective": "Ukrainian",           "score": 8},
    "Euromaidan Press":             {"category": "analysis",    "perspective": "Ukrainian/Western",   "score": 7},
    "Kyiv Post":                    {"category": "breaking",    "perspective": "Ukrainian",           "score": 7},
    "Meduza (EN)":                  {"category": "breaking",    "perspective": "Russian Independent", "score": 9},
    "The Moscow Times":             {"category": "breaking",    "perspective": "Russian Independent", "score": 7},
    "TASS (EN)":                    {"category": "breaking",    "perspective": "Russian State",       "score": 6},
    "RFE/RL Ukraine":               {"category": "breaking",    "perspective": "Western/Independent", "score": 9},
    "Geopolitical Monitor":         {"category": "analysis",    "perspective": "Western",             "score": 8},
    # Moyen-Orient
    "Al Jazeera (EN)":              {"category": "breaking",    "perspective": "Arab/Qatari",         "score": 10},
    "Al-Monitor":                   {"category": "analysis",    "perspective": "Western/Independent", "score": 10},
    "Middle East Eye":              {"category": "breaking",    "perspective": "Arab/UK",             "score": 9},
    "Middle East Monitor (MEMO)":   {"category": "breaking",    "perspective": "Arab/UK",             "score": 8},
    "Times of Israel":              {"category": "breaking",    "perspective": "Israeli",             "score": 9},
    "Jerusalem Post":               {"category": "breaking",    "perspective": "Israeli",             "score": 8},
    "Arab News":                    {"category": "breaking",    "perspective": "Saudi/Gulf",          "score": 7},
    "Al Arabiya (EN)":              {"category": "breaking",    "perspective": "UAE/Pan-Arab",        "score": 8},
    "IRNA (EN)":                    {"category": "breaking",    "perspective": "Iranian State",       "score": 7},
    "PressTV":                      {"category": "breaking",    "perspective": "Iranian State",       "score": 6},
    "INSS Israel":                  {"category": "think-tank",  "perspective": "Western/Israeli",     "score": 9},
    "Carnegie ME Program":          {"category": "think-tank",  "perspective": "Western",             "score": 8},
    "Foreign Policy – Middle East": {"category": "analysis",    "perspective": "Western",             "score": 8},
    "RFI Moyen-Orient":             {"category": "breaking",    "perspective": "French/Western",      "score": 7},
    "France 24 Middle East":        {"category": "breaking",    "perspective": "French/Western",      "score": 7},
    # OTAN / Europe
    "ECFR":                         {"category": "think-tank",  "perspective": "European/Western",    "score": 10},
    "Atlantic Council":             {"category": "think-tank",  "perspective": "Western/Transatlantic","score": 10},
    "Chatham House":                {"category": "think-tank",  "perspective": "UK/Western",          "score": 9},
    "RUSI":                         {"category": "think-tank",  "perspective": "UK/Western",          "score": 9},
    "IISS":                         {"category": "think-tank",  "perspective": "International",       "score": 9},
    "IRIS France":                  {"category": "think-tank",  "perspective": "French",              "score": 8},
    "SIPRI":                        {"category": "think-tank",  "perspective": "International",       "score": 8},
    "Breaking Defense":             {"category": "breaking",    "perspective": "US/Western",          "score": 10},
    "Defense One":                  {"category": "analysis",    "perspective": "US/Western",          "score": 9},
    "Defense News":                 {"category": "breaking",    "perspective": "US/Western",          "score": 8},
    "NATO Newsroom":                {"category": "breaking",    "perspective": "NATO/Official",       "score": 7},
    "NATO Review":                  {"category": "analysis",    "perspective": "NATO/Official",       "score": 7},
    "RFI Europe":                   {"category": "breaking",    "perspective": "French/Western",      "score": 7},
    "France 24 Europe":             {"category": "breaking",    "perspective": "French/Western",      "score": 7},
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
