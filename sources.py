"""
sources.py — Dictionnaires de sources RSS et métadonnées associées.
Fichier données pur : aucune dépendance externe.
Importé par collector.py, analyst.py, source_watcher.py.
"""

# ============================================================
# SOURCES RSS — UKRAINE / RUSSIE
# ============================================================
SOURCES_UKRAINE = {
    # ── Score 10 — Essentiels ──────────────────────────────────
    "ISW (understandingwar)":  "https://www.understandingwar.org/feeds/posts/default",  # Think-tank US, carte front quotidienne
    "ISW Research Blog":       "https://www.iswresearch.org/feeds/posts/default",       # Miroir Blogger ISW (fallback)
    "War on the Rocks":        "https://warontherocks.com/feed/",                       # Analyse stratégique profonde

    # ── Score 9 — Très pertinents ─────────────────────────────
    "Bellingcat":              "https://www.bellingcat.com/feed/",                       # OSINT/vérification indépendant
    "Kyiv Independent":        "https://kyivindependent.com/feed/",                     # Breaking UA, anglophone
    "Meduza (EN)":             "https://meduza.io/en/rss/all",                          # Russie/perspective interne, indépendant
    "RFE/RL Ukraine":          "https://www.rferl.org/api/zpioqivuiuv/",               # Radio Free Europe, très fiable

    # ── Score 8 — Pertinents ──────────────────────────────────
    "Ukrinform":               "https://www.ukrinform.net/rss/block-lastnews",          # Agence nationale UA
    "Ukrainska Pravda (EN)":   "https://www.pravda.com.ua/eng/rss/",                   # Principal quotidien UA
    "Geopolitical Monitor":    "https://www.geopoliticalmonitor.com/feed/",             # Analyse géostratégique

    # ── Score 7 — Utiles ──────────────────────────────────────
    "Euromaidan Press":        "https://euromaidanpress.com/feed/",                     # Presse civile ukrainienne
    "Kyiv Post":               "https://www.kyivpost.com/feed",                         # Quotidien UA anglophone
    "The Moscow Times":        "https://www.themoscowtimes.com/rss/news",              # Média russe exilé indépendant

    # ── Score 6 ────────────────────────────────────────────────
    "TASS (EN)":               "https://tass.com/rss/v2.xml",                          # Agence d'état russe
}

# ============================================================
# SOURCES RSS — MOYEN-ORIENT
# ============================================================
SOURCES_MOYEN_ORIENT = {
    # ── Score 10 — Essentiels ──────────────────────────────────
    "Al Jazeera (EN)":         "https://www.aljazeera.com/xml/rss/all.xml",            # Référence arabe anglophone, Qatar
    "Al-Monitor":              "https://www.al-monitor.com/rss",                        # Analyse ME indépendante, meilleure source

    # ── Score 9 — Très pertinents ─────────────────────────────
    "Middle East Eye":         "https://www.middleeasteye.net/rss",                    # Breaking + analyse, perspective arabe UK
    "Times of Israel":         "https://www.timesofisrael.com/feed/",                  # Perspective israélienne anglophone
    "INSS Israel":             "https://www.inss.org.il/feed/",                        # Think-tank sécurité israélien

    # ── Score 8 — Pertinents ──────────────────────────────────
    "Middle East Monitor":     "https://www.middleeastmonitor.com/feed/",              # Perspective pro-palestinienne UK
    "Al Arabiya (EN)":         "https://english.alarabiya.net/tools/mrss",             # Chaîne UAE/pan-arabe
    "Jerusalem Post":          "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",    # Quotidien israélien
    "Carnegie ME Program":     "https://carnegieendowment.org/rss/solr/?fa=region:ME", # Think-tank analyse ME
    "RFI Moyen-Orient":        "https://www.rfi.fr/fr/moyen-orient/rss",              # Perspective française

    # ── Score 7 — Utiles ──────────────────────────────────────
    "Arab News":               "https://www.arabnews.com/rss",                         # Perspective saoudienne/Golfe
    "France 24 ME":            "https://www.france24.com/en/middle-east/rss",          # Chaîne française internationale

    # ── Score 6 ────────────────────────────────────────────────
    "IRNA (EN)":               "https://en.irna.ir/rss",                               # Agence d'état iranien
    "PressTV":                 "https://www.presstv.ir/rss",                           # Média iranien
}

# ============================================================
# SOURCES RSS — OTAN / DÉFENSE EUROPÉENNE
# ============================================================
SOURCES_OTAN = {
    # ── Score 10 — Essentiels ──────────────────────────────────
    "ECFR":                    "https://ecfr.eu/feed/",                                 # Think-tank européen, meilleure analyse EU
    "Atlantic Council":        "https://www.atlanticcouncil.org/feed/",                 # Think-tank transatlantique Washington
    "Breaking Defense":        "https://breakingdefense.com/full-rss-feed/",           # Breaking défense US/NATO

    # ── Score 9 — Très pertinents ─────────────────────────────
    "Chatham House":           "https://www.chathamhouse.org/rss.xml",                 # Think-tank UK référence
    "RUSI":                    "https://rusi.org/rss",                                  # Royal United Services Institute UK
    "IISS":                    "https://www.iiss.org/en/research/rss",                 # International Institute for Strategic Studies
    "Defense One":             "https://www.defenseone.com/rss/all/",                  # Analyse défense US/NATO

    # ── Score 8 — Pertinents ──────────────────────────────────
    "IRIS France":             "https://www.iris-france.org/feed/",                    # Think-tank français
    "SIPRI":                   "https://www.sipri.org/rss",                             # Institut armement/désarmement Stockholm
    "RAND Corporation":        "https://www.rand.org/topics/international-affairs.xml", # Think-tank US politique publique
    "Defense News":            "https://www.defensenews.com/arc/outboundfeeds/rss/",  # Industrie défense

    # ── Score 7 — Utiles ──────────────────────────────────────
    "NATO Newsroom":           "https://www.nato.int/cps/en/natolive/news_rss.xml",   # Communiqués officiels NATO
    "NATO Review":             "https://www.nato.int/docu/review/rss.xml",             # Analyses longues NATO
    "RFI Europe":              "https://www.rfi.fr/fr/europe/rss",                     # Perspective française Europe
    "France 24 Europe":        "https://www.france24.com/en/europe/rss",               # Chaîne française internationale
}

# ============================================================
# SOURCES GLOBALES (multi-régions, auto-tagging)
# ============================================================
SOURCES_GLOBALES = {
    "AP News World":           "https://rsshub.app/apnews/topics/world-news",          # Fil mondial AP
    "Le Monde Diplomatique":   "https://www.monde-diplomatique.fr/rss",                # Analyse profonde française
    "Foreign Policy":          "https://foreignpolicy.com/feed/",                      # Analyse internationale US
    "BBC World":               "https://feeds.bbci.co.uk/news/world/rss.xml",          # Filtrage hors-sujet activé
}

# Dictionnaire principal utilisé par le dashboard
RSS_SOURCES = {
    "ukraine":      SOURCES_UKRAINE,
    "moyen_orient": SOURCES_MOYEN_ORIENT,
    "otan":         SOURCES_OTAN,
}

# Perspective éditoriale par source
PERSPECTIVES_SOURCES = {
    # Ukraine
    "ISW (understandingwar)":  "think-tank occidental",
    "ISW Research Blog":       "think-tank occidental",
    "War on the Rocks":        "analyse stratégique occidentale",
    "Bellingcat":              "OSINT indépendant",
    "Kyiv Independent":        "média ukrainien",
    "Meduza (EN)":             "média russe indépendant (exil)",
    "RFE/RL Ukraine":          "radio occidentale indépendante",
    "Ukrinform":               "agence officielle ukrainienne",
    "Ukrainska Pravda (EN)":   "presse ukrainienne indépendante",
    "Geopolitical Monitor":    "analyse géostratégique occidentale",
    "Euromaidan Press":        "presse civile ukrainienne",
    "Kyiv Post":               "quotidien ukrainien anglophone",
    "The Moscow Times":        "média russe exilé indépendant",
    "TASS (EN)":               "agence d'état russe",
    # Moyen-Orient
    "Al Jazeera (EN)":         "chaîne arabe (Qatar)",
    "Al-Monitor":              "analyse ME indépendante",
    "Middle East Eye":         "presse arabe indépendante (UK)",
    "Times of Israel":         "presse israélienne",
    "INSS Israel":             "think-tank israélien",
    "Middle East Monitor":     "presse pro-palestinienne (UK)",
    "Al Arabiya (EN)":         "chaîne UAE/Golfe",
    "Jerusalem Post":          "quotidien israélien",
    "Carnegie ME Program":     "think-tank occidental",
    "RFI Moyen-Orient":        "radio française internationale",
    "Arab News":               "presse saoudienne",
    "France 24 ME":            "chaîne française internationale",
    "IRNA (EN)":               "agence d'état iranien",
    "PressTV":                 "média iranien",
    # OTAN
    "ECFR":                    "think-tank européen",
    "Atlantic Council":        "think-tank transatlantique",
    "Breaking Defense":        "presse défense US/NATO",
    "Chatham House":           "think-tank britannique",
    "RUSI":                    "think-tank défense UK",
    "IISS":                    "think-tank sécurité international",
    "Defense One":             "analyse défense US",
    "IRIS France":             "think-tank français",
    "SIPRI":                   "institut armement Stockholm",
    "RAND Corporation":        "think-tank politique publique US",
    "Defense News":            "presse industrie défense",
    "NATO Newsroom":           "communication officielle NATO",
    "NATO Review":             "publication officielle NATO",
    "RFI Europe":              "radio française internationale",
    "France 24 Europe":        "chaîne française internationale",
}

# Mots-clés pour l'auto-tagging des sources globales
TAGS_REGIONS = {
    "ukraine":      ["ukraine", "kyiv", "zelensky", "russia", "russie", "donetsk",
                     "zaporizhzhia", "kharkiv", "crimée", "moscow", "kremlin"],
    "moyen_orient": ["israel", "gaza", "iran", "hamas", "hezbollah", "syrie",
                     "liban", "arabie", "qatar", "middle east", "palestine"],
    "otan":         ["nato", "otan", "macron", "europe", "bruxelles", "défense",
                     "trump", "pentagon", "alliance", "berlin", "warsaw"],
}
