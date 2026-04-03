# OSINT Veille Géopolitique

Système de veille géopolitique automatisée combinant collecte RSS, analyse Claude AI, renseignement terrain et publication sur X (Twitter).

Suivi en temps réel de **l'Ukraine**, du **Moyen-Orient** et de l'**OTAN** — pour alimenter le compte X [@Rodjayb1](https://x.com/Rodjayb1).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)

---

## 📋 Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Architecture](#architecture)
- [Modèles IA](#modèles-ia)
- [Sources surveillées](#sources-surveillées)
- [Dashboard](#dashboard)
- [Dépannage](#dépannage)
- [Sécurité](#sécurité)
- [Contribuer](#contribuer)
- [Licence](#licence)

---

## Fonctionnalités

### Deux pipelines de collecte

- **Pipeline profond** (~15-20 min) : RSS think tanks + médias → clustering sémantique → analyse Claude Sonnet → mémoire 7 jours
- **Pipeline terrain** (~5 min) : Telegram + trackers OSINT via RSSHub → détection signaux chauds → breaking auto si chaleur ≥ 70

### Rédaction automatisée

- Posts simples, threads narratifs en 4 actes, articles longs (X Premium)
- Deux styles : **Platon Punk** (percutant, décryptage) et **Journaliste** (factuel, sobre)
- Anti-répétition : les posts précédents sont injectés dans le prompt
- Validation éditoriale intégrée avant publication

### Prédictions géopolitiques

- Génération via Sonnet + mémoire + données macro (FRED) + tendances web (Tavily)
- Vérification automatique des prédictions à échéance via Haiku
- Publication manuelle du post de prédiction + bilan depuis le dashboard

### Alertes critiques

- Notifications Discord pour événements breaking (chaleur ≥ 70)
- Détection d'alertes critiques lors de l'analyse profonde
- Webhooks configurables pour intégration externe

### Dashboard Streamlit (9 onglets)

| Onglet | Contenu |
|--------|---------|
| 🔥 Breaking | Signaux terrain en temps réel, validation breaking |
| 📰 Articles | Liste filtrée par région, statut de traitement |
| 🧠 Analyses | Résultats Claude (faits, tendances, alertes) |
| 📊 Régions | Métriques + alertes terrain par zone géographique |
| 🐦 Posts X | Brouillons, validation, publication manuelle |
| 🔮 Prédictions | Actives, vérifiées, publication des bilans |
| 💹 Macro | FRED API — pétrole, taux, VIX, indicateurs US |
| 📈 Engagement | Métriques X par style/région, évolution temporelle |
| 💾 Mémoire | Contexte glissant 7 jours par région |

---

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

### 1. Cloner le dépôt

```bash
git clone https://github.com/Rodjayb1/osint-veille-geopolitique.git
cd osint-veille-geopolitique
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Ou installation manuelle :

```bash
pip install anthropic feedparser tweepy streamlit matplotlib requests tavily-python pandas scrapling
```

### 4. Configurer les clés API

```bash
cp config_example.py config.py
# Ouvrir config.py et remplir toutes les clés
```

---

## Configuration

### Clés API requises

| Clé | Utilité | Gratuit ? | Lien d'inscription |
|-----|---------|-----------|-------------------|
| `ANTHROPIC_API_KEY` | Claude Sonnet + Haiku | Non (~$0.50/jour) | [Anthropic Console](https://console.anthropic.com/) |
| `X_API_KEY` + secrets | Publication X/Twitter | Oui (compte dev) | [Developer Portal](https://developer.twitter.com/) |
| `FRED_API_KEY` | Données macro US | Oui | [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `TAVILY_API_KEY` | Tendances web | Oui (1000 req/mois) | [Tavily](https://tavily.com/) |
| `DISCORD_WEBHOOK_URL` | Alertes breaking | Optionnel | [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668) |
| `RSSHUB_BASE` | Flux Telegram/terrain | Oui (instance publique) | [RSSHub](https://docs.rsshub.app/) |
| `OIL_API_KEY` | Prix du pétrole | Optionnel (FRED en fallback) | - |

### Modèles Claude configurés

```python
CLAUDE_MODEL      = "claude-sonnet-4-20250514"   # analyses, prédictions, rédaction
CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"  # dédup, mémoire, terrain, scoring
```

### Seuil de chaleur breaking

Modifiez `SEUIL_CHALEUR_BREAKING` dans `config.py` (défaut: 70) pour ajuster la sensibilité des alertes terrain.

---

## Utilisation

### Lancer le dashboard

```bash
streamlit run dashboard.py
```

Accédez ensuite à `http://localhost:8501` dans votre navigateur.

### Exécution manuelle des collectes

Le système est conçu pour fonctionner via le dashboard, mais vous pouvez lancer les collectes manuellement :

```bash
# Collecte pipeline profond (toutes régions)
python collector.py --region ukraine
python collector.py --region moyen-orient
python collector.py --region otan

# Collecte terrain rapide
python collector_terrain.py --region ukraine

# Analyse profonde
python analyst.py --region ukraine

# Analyse terrain
python analyst_terrain.py --region ukraine
```

### Planification automatique (cron)

Pour automatiser les collectes, ajoutez des entrées cron :

```bash
# Pipeline profond toutes les 20 minutes
*/20 * * * * cd /path/to/project && ./venv/bin/python collector.py --all-regions

# Pipeline terrain toutes les 5 minutes
*/5 * * * * cd /path/to/project && ./venv/bin/python collector_terrain.py --all-regions
```

---

## Architecture

### Structure du projet

```
osint-veille-geopolitique/
├── config.py              # Clés API + sources RSS (NON commit — dans .gitignore)
├── config_example.py      # Template à copier
├── database.py            # SQLite — 7 tables (articles, analyses, posts, predictions, etc.)
├── collector.py           # Collecte RSS (think tanks, médias)
├── collector_terrain.py   # Collecte terrain (Telegram, trackers via RSSHub)
├── analyst.py             # Analyse profonde Sonnet avec clustering sémantique
├── analyst_terrain.py     # Détection breaking Haiku + scoring chaleur
├── dedup.py               # Clustering sémantique Haiku
├── memory.py              # Mémoire 7 jours glissants Haiku
├── predictions.py         # Génération + vérification prédictions
├── writer.py              # Rédaction posts/threads/articles + validation éditoriale
├── editor.py              # Vérification qualité posts (anti-répétition, cohérence)
├── dashboard.py           # Interface Streamlit (9 onglets)
├── scraper.py             # Tendances web Tavily
├── macro.py               # Données macro FRED + historique pétrole
├── alerts.py              # Notifications Discord + email
├── twitter.py             # Publication X (posts simples + threads)
├── sources.py             # Sources RSS classées par région/perspective
└── requirements.txt       # Dépendances Python
```

### Flux de données

```
Pipeline 1 — Analyse profonde (~15-20 min)
collector.py → articles (DB) → dedup.py → analyst.py → analyses (DB) → memory.py → writer.py

Pipeline 2 — Terrain rapide (~5 min)
collector_terrain.py → signaux_terrain (DB) → analyst_terrain.py → alertes_terrain (DB) → post breaking

Pipeline 3 — Prédictions (manuel via dashboard)
predictions.py → predictions (DB) → writer.py → vérification automatique à échéance
```

### Base de données (SQLite)

Tables principales :
- `articles` : Articles RSS collectés
- `analyses` : Analyses Claude générées
- `signaux_terrain` : Signaux Telegram/trackers
- `alertes_terrain` : Alertes breaking validées
- `posts` : Brouillons et posts publiés
- `predictions` : Prédictions géopolitiques
- `memoire` : Contexte glissant par région
- `engagement` : Métriques X par post

---

## Modèles IA

| Modèle | Usage | Coût relatif | Vitesse |
|--------|-------|--------------|---------|
| `claude-sonnet-4-20250514` | Analyses profondes, prédictions, rédaction | Moyen | ~5-10s |
| `claude-haiku-4-5-20251001` | Déduplication, mémoire, terrain, scoring | Faible | ~1-3s |

**Budget estimé :** ~$0.50/jour pour un cycle complet d'analyse (collecte + analyse + rédaction).

---

## Sources surveillées

### Ukraine (15 sources)

ISW Research, Bellingcat, Kyiv Independent, Ukrinform, Euromaidan Press, Kyiv Post, Meduza (EN), DeepStateUA, Ukraine Weapons Tracker, etc.

### Moyen-Orient (12 sources)

Al-Monitor, Middle East Eye, RFI Moyen-Orient, Times of Israel, Al Jazeera, Rybar, etc.

### OTAN / Europe (10 sources)

ECFR, Atlantic Council, Defense News, IRIS France, Chatham House, RUSI, NATO Review, Carnegie Endowment, etc.

### Terrain (Telegram via RSSHub)

DeepStateUA, Ukraine Weapons Tracker, Rybar, OSINTdefender, GeoConfirmed, Intel Crab, WarMonitors, etc.

### Perspectives couvertes

- Western / NATO
- Russian / Pro-Russia
- Arab / Middle East
- Iranian / Pro-Iran
- Israeli
- Independent / Neutral

---

## Dashboard

### Navigation

Le dashboard est divisé en 9 onglets accessibles via la barre de navigation supérieure :

1. **🔥 Breaking** : Visualisation des signaux terrain chauds, validation manuelle des posts breaking
2. **📰 Articles** : Liste complète des articles collectés, filtrage par région/statut
3. **🧠 Analyses** : Consultation des analyses générées par Claude, export possible
4. **📊 Régions** : Métriques par zone géographique, heatmaps d'activité
5. **🐦 Posts X** : Gestion des brouillons, validation éditoriale, publication
6. **🔮 Prédictions** : Suivi des prédictions actives, bilans vérifiés
7. **💹 Macro** : Indicateurs économiques US (pétrole, taux, VIX)
8. **📈 Engagement** : Statistiques de performance par style de post/région
9. **💾 Mémoire** : Historique contextuel glissant (7 jours) par région

### Thème

Interface sombre inspirée du thème GitHub Dark, optimisée pour une utilisation prolongée.

---

## Dépannage

### Problèmes courants

#### Erreur d'authentification API

```bash
# Vérifiez que config.py existe et contient vos clés
ls -la config.py
cat config.py | grep API_KEY
```

#### Module manquant

```bash
# Réinstallez les dépendances
pip install -r requirements.txt --upgrade
```

#### Base de données corrompue

```bash
# Sauvegardez puis recréez la base
cp veille.db veille.db.backup
rm veille.db
python -c "from database import init_db; init_db()"
```

#### Dashboard ne démarre pas

```bash
# Vérifiez le port
streamlit run dashboard.py --server.port 8502

# Mode debug
streamlit run dashboard.py --server.headless true
```

#### Erreur TLS/SSL lors de la collecte

Le module `scrapling` gère automatiquement les fingerprints TLS. Si problème persiste :

```bash
pip install --upgrade scrapling
```

### Logs et debugging

Activez les logs détaillés en ajoutant dans `config.py` :

```python
DEBUG_MODE = True
```

Consultez les logs Streamlit dans `~/.streamlit/logs/`.

---

## Sécurité

### Bonnes pratiques

**IMPORTANT :** `config.py` contient tes clés API. Il est dans `.gitignore` et ne sera **jamais** poussé sur GitHub.

Vérifiez régulièrement :

```bash
git status  # Assurez-vous que config.py n'apparaît pas
```

### Si vous avez accidentellement commité `config.py`

```bash
git rm --cached config.py
git commit -m "Remove config from tracking"
git push
# Puis régénérez vos clés API compromises
```

### Variables d'environnement (alternative)

Vous pouvez également utiliser des variables d'environnement :

```bash
export ANTHROPIC_API_KEY="your_key_here"
export X_API_KEY="your_key_here"
# etc.
```

---

## Contribuer

Les contributions sont les bienvenues ! Voici comment procéder :

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Guidelines

- Respectez le style de code existant (PEP 8)
- Ajoutez des tests pour les nouvelles fonctionnalités
- Mettez à jour la documentation si nécessaire
- Gardez les commits atomiques et descriptifs

---

## Licence

MIT — Utilisation libre avec attribution.

Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## Roadmap

- [ ] Support multi-comptes X
- [ ] Intégration LinkedIn / Mastodon
- [ ] Export PDF des analyses
- [ ] API REST pour intégration externe
- [ ] Support multilingue (EN/FR/AR)
- [ ] Cartes dynamiques générées
- [ ] Détection de désinformation

---

## Contact

- **Projet** : [OSINT Veille Géopolitique](https://github.com/Rodjayb1/osint-veille-geopolitique)
- **Twitter** : [@Rodjayb1](https://x.com/Rodjayb1)
- **Issues** : [GitHub Issues](https://github.com/Rodjayb1/osint-veille-geopolitique/issues)

---

*Développé pour [@Rodjayb1](https://x.com/Rodjayb1) — Veille géopolitique francophone*

**Dernière mise à jour :** Avril 2026
