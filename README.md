# OSINT Veille Géopolitique

Système de veille géopolitique automatisée combinant collecte RSS, analyse Claude AI, renseignement terrain et publication sur X (Twitter).

Suivi en temps réel de **l'Ukraine**, du **Moyen-Orient** et de l'**OTAN** — pour alimenter le compte X [@Rodjayb1](https://x.com/Rodjayb1).

---

## Fonctionnalités

### Deux pipelines de collecte
- **Pipeline profond** (~15-20 min) : RSS think tanks + médias → clustering sémantique → analyse Claude Sonnet → mémoire 7 jours
- **Pipeline terrain** (~5 min) : Telegram + trackers OSINT via RSSHub → détection signaux chauds → breaking auto si chaleur ≥ 70

### Rédaction automatisée
- Posts simples, threads narratifs en 4 actes, articles longs (X Premium)
- Deux styles : **Platon Punk** (percutant, décryptage) et **Journaliste** (factuel, sobre)
- Anti-répétition : les posts précédents sont injectés dans le prompt

### Prédictions géopolitiques
- Génération via Sonnet + mémoire + données macro (FRED) + tendances web (Tavily)
- Vérification automatique des prédictions à échéance via Haiku
- Publication manuelle du post de prédiction + bilan depuis le dashboard

### Dashboard Streamlit (8 onglets)
| Onglet | Contenu |
|--------|---------|
| 📰 Articles | Liste filtrée par région |
| 🧠 Analyses | Résultats Claude (faits, tendances, alertes) |
| 📊 Régions | Métriques + alertes terrain |
| 🐦 Posts X | Brouillons, validation, publication manuelle |
| 🔮 Prédictions | Actives, vérifiées, publication |
| 💹 Macro | FRED API — pétrole, taux, VIX |
| 📈 Engagement | Métriques X par style/région |
| 🧠 Mémoire | Contexte glissant par région |

---

## Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/Rodjayb1/osint-veille-geopolitique.git
cd osint-veille-geopolitique
```

### 2. Installer les dépendances
```bash
pip install anthropic feedparser tweepy streamlit matplotlib requests tavily-python pandas
```

### 3. Configurer les clés API
```bash
cp config_example.py config.py
# Ouvrir config.py et remplir toutes les clés
```

**Clés requises :**
| Clé | Utilité | Gratuit ? |
|-----|---------|-----------|
| `ANTHROPIC_API_KEY` | Claude Sonnet + Haiku | Non (~$0.50/jour) |
| `X_API_KEY` + secrets | Publication X | Oui (compte dev) |
| `FRED_API_KEY` | Données macro US | Oui |
| `TAVILY_API_KEY` | Tendances web | Oui (1000 req/mois) |
| `DISCORD_WEBHOOK_URL` | Alertes breaking | Optionnel |
| `RSSHUB_BASE` | Flux Telegram/terrain | Oui (instance publique) |

### 4. Lancer le dashboard
```bash
streamlit run dashboard.py
```

---

## Architecture

```
osint-veille-geopolitique/
├── config.py              # Clés API + sources RSS (NON commit — dans .gitignore)
├── config_example.py      # Template à copier
├── database.py            # SQLite — 7 tables
├── collector.py           # Collecte RSS (think tanks, médias)
├── collector_terrain.py   # Collecte terrain (Telegram, trackers)
├── analyst.py             # Analyse Sonnet
├── analyst_terrain.py     # Détection breaking Haiku
├── dedup.py               # Clustering sémantique Haiku
├── memory.py              # Mémoire 7 jours glissants Haiku
├── predictions.py         # Prédictions + vérification
├── writer.py              # Rédaction posts/threads/articles
├── dashboard.py           # Interface Streamlit
├── scraper.py             # Tendances web Tavily
├── macro.py               # Données macro FRED
└── alerts.py              # Notifications Discord
```

### Flux de données

```
Pipeline 1 — Analyse profonde (~15-20 min)
collector.py → articles (DB) → dedup.py → analyst.py → analyses (DB) → memory.py → writer.py

Pipeline 2 — Terrain rapide (~5 min)
collector_terrain.py → signaux_terrain (DB) → analyst_terrain.py → alertes_terrain (DB) → post breaking

Pipeline 3 — Prédictions (manuel)
predictions.py → predictions (DB) → writer.py → vérification automatique
```

---

## Modèles Claude utilisés

| Modèle | Usage | Coût relatif |
|--------|-------|--------------|
| `claude-sonnet-4-20250514` | Analyses, prédictions, rédaction | Moyen |
| `claude-haiku-4-5-20251001` | Dédup, mémoire, terrain, scoring | Faible |

Budget estimé : **~$0.50/jour** pour un cycle complet d'analyse.

---

## Sources surveillées

### Ukraine
ISW Research, Bellingcat, Kyiv Independent, Ukrinform, Euromaidan Press, Kyiv Post, Meduza (EN)

### Moyen-Orient
Al-Monitor, Middle East Eye, RFI Moyen-Orient, Times of Israel, Al Jazeera

### OTAN / Europe
ECFR, Atlantic Council, Defense News, IRIS France, Chatham House, RUSI, NATO Review, Carnegie Endowment

### Terrain (Telegram via RSSHub)
DeepStateUA, Ukraine Weapons Tracker, Rybar, OSINTdefender, GeoConfirmed, Intel Crab...

---

## Sécurité

**IMPORTANT :** `config.py` contient tes clés API. Il est dans `.gitignore` et ne sera **jamais** poussé sur GitHub.

Si tu as accidentellement commité `config.py` :
```bash
git rm --cached config.py
git commit -m "Remove config from tracking"
git push
```

---

## Licence

MIT — Utilisation libre avec attribution.

---

*Développé pour [@Rodjayb1](https://x.com/Rodjayb1) — Veille géopolitique francophone*
