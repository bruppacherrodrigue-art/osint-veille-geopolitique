"""
database.py — Gestion de la base de données SQLite
Crée et gère veille.db avec 7 tables.

Améliorations appliquées :
    - Création automatique d'index pour optimisation des requêtes
    - Logging structuré
    - Gestion robuste des erreurs SQL
"""

import json
import sqlite3
from datetime import datetime, timedelta

# Import des utilitaires
try:
    from utils import create_sql_indexes, logger
except ImportError:
    # Fallback si utils.py n'est pas disponible
    class DummyLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): pass
    logger = DummyLogger()
    
    def create_sql_indexes(*args, **kwargs):
        pass


DB_PATH = "veille.db"


def _dict_factory(cursor, row):
    """Convertit chaque ligne SQLite en dict — permet d'utiliser .get() partout."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection(db_path: str = None):
    """
    Retourne une connexion SQLite avec row_factory dict.
    
    Args:
        db_path: Chemin optionnel vers la base (défaut: DB_PATH global)
    
    Returns:
        Connexion SQLite
    """
    path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = _dict_factory
    return conn


def init_db(db_path: str = None):
    """
    Crée toutes les tables si elles n'existent pas encore et optimise avec des index.
    
    Args:
        db_path: Chemin optionnel vers la base (défaut: veille.db)
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # Utiliser le chemin correct pour les index
    actual_db_path = db_path if db_path else DB_PATH

    try:
        # --- Articles collectés via RSS ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name   TEXT,
                region        TEXT,
                titre         TEXT,
                url           TEXT UNIQUE,
                resume        TEXT,
                date_pub      TEXT,
                date_collecte TEXT,
                lu            INTEGER DEFAULT 0,
                fiabilite     REAL DEFAULT 0.8,
                statut        TEXT DEFAULT 'publie'
            )
        """)

        # --- Analyses Claude (résultat JSON) ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                region        TEXT,
                contenu       TEXT,
                tendances     TEXT,
                niveau_alerte TEXT,
                date_analyse  TEXT
            )
        """)

        # --- Posts rédigés pour X ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS posts_x (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                region           TEXT,
                contenu          TEXT,
                statut           TEXT DEFAULT 'brouillon',
                style            TEXT,
                date_creation    TEXT,
                date_publication TEXT,
                tweet_id         TEXT,
                editorial_review TEXT
            )
        """)

        # --- Métriques d'engagement X ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                post_id          INTEGER PRIMARY KEY,
                tweet_id         TEXT,
                published_at     TEXT,
                hour_published   INTEGER,
                day_of_week      INTEGER,
                region           TEXT,
                style            TEXT,
                has_map          INTEGER DEFAULT 0,
                char_count       INTEGER,
                is_thread        INTEGER DEFAULT 0,
                likes            INTEGER DEFAULT 0,
                retweets         INTEGER DEFAULT 0,
                replies          INTEGER DEFAULT 0,
                impressions      INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0,
                last_checked     TEXT
            )
        """)

        # --- Prédictions géopolitiques ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                region              TEXT,
                prediction          TEXT,
                horizon_jours       INTEGER,
                probabilite         REAL,
                raisonnement        TEXT,
                critere_verification TEXT,
                categorie           TEXT,
                acteurs_cles        TEXT,
                date_creation       TEXT,
                date_echeance       TEXT,
                statut              TEXT DEFAULT 'active',
                resultat            TEXT,
                explication         TEXT,
                precision_score     REAL,
                lecons              TEXT,
                date_verification   TEXT,
                tweet_id_prediction TEXT,
                tweet_id_bilan      TEXT
            )
        """)

        # --- Signaux terrain (Telegram, trackers, partisans) ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS signaux_terrain (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name    TEXT,
                region         TEXT,
                titre          TEXT,
                url            TEXT UNIQUE,
                contenu        TEXT,
                date_pub       TEXT,
                date_collecte  TEXT,
                type_source    TEXT,
                fiabilite      REAL DEFAULT 0.6,
                priorite       INTEGER DEFAULT 0,
                traite         INTEGER DEFAULT 0
            )
        """)

        # --- Alertes terrain générées ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS alertes_terrain (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                region         TEXT,
                chaleur        INTEGER,
                resume         TEXT,
                evenements     TEXT,
                signal_partisan TEXT,
                post_breaking  TEXT,
                date_creation  TEXT
            )
        """)

        # --- Santé des sources RSS ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS sources_health (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name     TEXT UNIQUE,
                region          TEXT,
                url             TEXT,
                statut          TEXT DEFAULT 'inconnu',
                nb_articles     INTEGER DEFAULT 0,
                latence_ms      INTEGER DEFAULT 0,
                derniere_ok     TEXT,
                dernier_test    TEXT,
                url_alternative TEXT
            )
        """)

        conn.commit()
        logger.info("Tables de base de données créées/vérifiées")
        
        # Créer les index pour optimisation (après création des tables)
        create_sql_indexes(actual_db_path)
        
    except sqlite3.Error as e:
        logger.error(f"Erreur SQL lors de l'initialisation: {e}")
        raise
    finally:
        conn.close()
    
    print("✅ Base de données initialisée.")


# ============================================================
# FONCTIONS ARTICLES
# ============================================================

def sauvegarder_article(source_name, region, titre, url, resume, date_pub):
    """Insère un article (ignore si l'URL existe déjà)."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO articles
            (source_name, region, titre, url, resume, date_pub, date_collecte)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_name, region, titre, url, resume, date_pub,
              datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def get_articles_par_region(region, limit=50):
    """Retourne les derniers articles d'une région."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM articles
        WHERE region = ?
        ORDER BY date_collecte DESC
        LIMIT ?
    """, (region, limit)).fetchall()
    conn.close()
    return rows


def get_articles_recents(region, heures=48):
    """Retourne les articles collectés dans les dernières N heures."""
    from datetime import timedelta
    seuil = (datetime.now() - timedelta(hours=heures)).isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM articles
        WHERE region = ? AND date_collecte >= ?
        ORDER BY date_collecte DESC
    """, (region, seuil)).fetchall()
    conn.close()
    return rows


def compter_articles():
    """Retourne le nombre total d'articles par région."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT region, COUNT(*) as nb
        FROM articles
        GROUP BY region
    """).fetchall()
    conn.close()
    return {r["region"]: r["nb"] for r in rows}


# ============================================================
# FONCTIONS ANALYSES
# ============================================================

def sauvegarder_analyse(region, contenu, tendances, niveau_alerte):
    """Sauvegarde une analyse Claude."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO analyses (region, contenu, tendances, niveau_alerte, date_analyse)
        VALUES (?, ?, ?, ?, ?)
    """, (region, contenu, tendances, niveau_alerte, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_dernieres_analyses(region, limit=5):
    """Retourne les N dernières analyses d'une région."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM analyses
        WHERE region = ?
        ORDER BY date_analyse DESC
        LIMIT ?
    """, (region, limit)).fetchall()
    conn.close()
    return rows


def get_toutes_analyses(limit=100):
    """Retourne toutes les analyses récentes."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM analyses
        ORDER BY date_analyse DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


# ============================================================
# FONCTIONS POSTS X
# ============================================================

def sauvegarder_post(region, contenu, style, statut="brouillon"):
    """Sauvegarde un post rédigé. Retourne l'id du post créé."""
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO posts_x (region, contenu, statut, style, date_creation)
        VALUES (?, ?, ?, ?, ?)
    """, (region, contenu, statut, style, datetime.now().isoformat()))
    post_id = cur.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_posts_brouillons(region=None):
    """Retourne les posts en brouillon (toutes régions ou une seule)."""
    conn = get_connection()
    if region:
        rows = conn.execute("""
            SELECT * FROM posts_x
            WHERE statut = 'brouillon' AND region = ?
            ORDER BY date_creation DESC
        """, (region,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM posts_x
            WHERE statut = 'brouillon'
            ORDER BY date_creation DESC
        """).fetchall()
    conn.close()
    return rows


def get_posts_recents(region, limit=10):
    """Retourne les N derniers posts (tous statuts) pour anti-répétition."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT contenu FROM posts_x
        WHERE region = ?
        ORDER BY date_creation DESC
        LIMIT ?
    """, (region, limit)).fetchall()
    conn.close()
    return [r["contenu"] for r in rows]


def update_editorial_review(post_id, review_json):
    """Sauvegarde le rapport éditorial d'un post."""
    conn = get_connection()
    conn.execute(
        "UPDATE posts_x SET editorial_review = ? WHERE id = ?",
        (review_json, post_id)
    )
    conn.commit()
    conn.close()


def get_editorial_review(post_id):
    """Retourne le rapport éditorial d'un post (dict ou None)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT editorial_review FROM posts_x WHERE id = ?", (post_id,)
    ).fetchone()
    conn.close()
    if row and row["editorial_review"]:
        try:
            return json.loads(row["editorial_review"])
        except Exception:
            return None
    return None


def update_post_contenu(post_id, nouveau_contenu):
    """Remplace le contenu d'un post (pour 'Utiliser la version améliorée')."""
    conn = get_connection()
    conn.execute(
        "UPDATE posts_x SET contenu = ? WHERE id = ?",
        (nouveau_contenu, post_id)
    )
    conn.commit()
    conn.close()


def get_posts_publies_recents(limit=20):
    """Retourne les N derniers posts publiés (pour anti-doublon)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, region, contenu, style FROM posts_x
        WHERE statut = 'publié'
        ORDER BY date_publication DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def marquer_post_publie(post_id, tweet_id=None):
    """Marque un post comme publié et crée automatiquement une entrée engagement."""
    now = datetime.now()
    conn = get_connection()
    conn.execute("""
        UPDATE posts_x
        SET statut = 'publié', tweet_id = ?, date_publication = ?
        WHERE id = ?
    """, (tweet_id, now.isoformat(), post_id))
    # Récupérer les infos du post pour créer l'entrée engagement
    row = conn.execute(
        "SELECT region, style, contenu FROM posts_x WHERE id = ?", (post_id,)
    ).fetchone()
    if row:
        contenu = row["contenu"] if isinstance(row, dict) else row[2]
        region  = row["region"]  if isinstance(row, dict) else row[0]
        style   = row["style"]   if isinstance(row, dict) else row[1]
        is_thread = 1 if '"type": "thread"' in (contenu or "") else 0
        char_count = len(contenu or "")
        conn.execute("""
            INSERT OR IGNORE INTO engagement
            (post_id, tweet_id, published_at, hour_published, day_of_week,
             region, style, char_count, is_thread, last_checked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, tweet_id, now.isoformat(), now.hour, now.weekday(),
              region, style, char_count, is_thread, now.isoformat()))
    conn.commit()
    conn.close()


def marquer_post_rejete(post_id):
    """Marque un post comme rejeté."""
    conn = get_connection()
    conn.execute("UPDATE posts_x SET statut = 'rejeté' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


def supprimer_post(post_id):
    """Supprime un post de la base."""
    conn = get_connection()
    conn.execute("DELETE FROM posts_x WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


# ============================================================
# FONCTIONS ENGAGEMENT
# ============================================================

def sauvegarder_engagement(post_id, tweet_id, region, style, char_count, is_thread):
    """Crée une entrée d'engagement lors de la publication."""
    now = datetime.now()
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO engagement
        (post_id, tweet_id, published_at, hour_published, day_of_week,
         region, style, char_count, is_thread, last_checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (post_id, tweet_id, now.isoformat(), now.hour, now.weekday(),
          region, style, char_count, int(is_thread), now.isoformat()))
    conn.commit()
    conn.close()


def update_engagement(tweet_id, likes, retweets, replies, impressions):
    """Met à jour les métriques d'un tweet."""
    score = likes * 2 + retweets * 3 + replies * 1.5 + impressions * 0.01
    conn = get_connection()
    conn.execute("""
        UPDATE engagement
        SET likes=?, retweets=?, replies=?, impressions=?,
            engagement_score=?, last_checked=?
        WHERE tweet_id=?
    """, (likes, retweets, replies, impressions, score,
          datetime.now().isoformat(), tweet_id))
    conn.commit()
    conn.close()


def get_posts_publies_avec_engagement(limit=50):
    """Retourne tous les posts publiés avec leurs métriques d'engagement."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.region, p.style, p.contenu, p.date_publication, p.tweet_id,
               COALESCE(e.likes, 0)            as likes,
               COALESCE(e.retweets, 0)         as retweets,
               COALESCE(e.replies, 0)          as replies,
               COALESCE(e.impressions, 0)      as impressions,
               COALESCE(e.engagement_score, 0) as engagement_score,
               COALESCE(e.is_thread, 0)        as is_thread,
               e.last_checked
        FROM posts_x p
        LEFT JOIN engagement e ON p.id = e.post_id
        WHERE p.statut = 'publié'
        ORDER BY p.date_publication DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def get_engagement_evolution(region=None, limit=30):
    """Retourne l'évolution du score d'engagement dans le temps (pour graphique)."""
    conn = get_connection()
    if region:
        rows = conn.execute("""
            SELECT DATE(published_at) as jour,
                   AVG(engagement_score) as score_moyen,
                   SUM(likes) as total_likes,
                   SUM(retweets) as total_retweets,
                   COUNT(*) as nb_posts
            FROM engagement
            WHERE region = ?
            GROUP BY DATE(published_at)
            ORDER BY jour DESC LIMIT ?
        """, (region, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT DATE(published_at) as jour,
                   AVG(engagement_score) as score_moyen,
                   SUM(likes) as total_likes,
                   SUM(retweets) as total_retweets,
                   COUNT(*) as nb_posts
            FROM engagement
            GROUP BY DATE(published_at)
            ORDER BY jour DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return rows


def get_stats_engagement():
    """Retourne les stats agrégées pour le dashboard."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT region, style, is_thread,
               AVG(likes) as avg_likes,
               AVG(retweets) as avg_retweets,
               AVG(engagement_score) as avg_score,
               COUNT(*) as nb_posts
        FROM engagement
        GROUP BY region, style, is_thread
    """).fetchall()
    conn.close()
    return rows


# ============================================================
# FONCTIONS PRÉDICTIONS
# ============================================================

def sauvegarder_prediction(region, prediction, horizon_jours, probabilite,
                            raisonnement, critere, categorie, acteurs):
    """Sauvegarde une nouvelle prédiction."""
    from datetime import timedelta
    date_echeance = (datetime.now() + timedelta(days=horizon_jours)).isoformat()
    conn = get_connection()
    conn.execute("""
        INSERT INTO predictions
        (region, prediction, horizon_jours, probabilite, raisonnement,
         critere_verification, categorie, acteurs_cles, date_creation, date_echeance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (region, prediction, horizon_jours, probabilite, raisonnement,
          critere, categorie, acteurs, datetime.now().isoformat(), date_echeance))
    conn.commit()
    conn.close()


def get_predictions_actives():
    """Retourne toutes les prédictions avec statut 'active'."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM predictions WHERE statut = 'active'
        ORDER BY date_echeance ASC
    """).fetchall()
    conn.close()
    return rows


def get_predictions_verifiees(limit=20):
    """Retourne les prédictions déjà vérifiées, les plus récentes en premier."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM predictions
        WHERE statut = 'verifiee'
        ORDER BY date_verification DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def get_predictions_echeance():
    """Retourne les prédictions dont l'échéance est passée et non encore vérifiées."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM predictions
        WHERE statut = 'active' AND date_echeance <= ?
    """, (datetime.now().isoformat(),)).fetchall()
    conn.close()
    return rows


def verifier_prediction(pred_id, resultat, explication, precision_score, lecons):
    """Marque une prédiction comme vérifiée avec son résultat."""
    conn = get_connection()
    conn.execute("""
        UPDATE predictions
        SET statut='verifiee', resultat=?, explication=?,
            precision_score=?, lecons=?, date_verification=?
        WHERE id=?
    """, (resultat, explication, precision_score, lecons,
          datetime.now().isoformat(), pred_id))
    conn.commit()
    conn.close()


def supprimer_prediction(pred_id):
    """Supprime définitivement une prédiction de la base."""
    conn = get_connection()
    conn.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
    conn.commit()
    conn.close()


def update_tweet_id_prediction(pred_id, tweet_id_prediction=None, tweet_id_bilan=None):
    """Met à jour les tweet_ids d'une prédiction."""
    conn = get_connection()
    if tweet_id_prediction:
        conn.execute("UPDATE predictions SET tweet_id_prediction=? WHERE id=?",
                     (tweet_id_prediction, pred_id))
    if tweet_id_bilan:
        conn.execute("UPDATE predictions SET tweet_id_bilan=? WHERE id=?",
                     (tweet_id_bilan, pred_id))
    conn.commit()
    conn.close()


# ============================================================
# FONCTIONS SIGNAUX TERRAIN
# ============================================================

def sauvegarder_signal_terrain(source_name, region, titre, url, contenu,
                                date_pub, type_source, fiabilite, priorite):
    """Insère un signal terrain (ignore si URL existe déjà)."""
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO signaux_terrain
        (source_name, region, titre, url, contenu, date_pub, date_collecte,
         type_source, fiabilite, priorite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (source_name, region, titre, url, contenu, date_pub,
          datetime.now().isoformat(), type_source, fiabilite, priorite))
    conn.commit()
    conn.close()


def get_signaux_non_traites(region=None):
    """Retourne les signaux terrain non encore analysés."""
    conn = get_connection()
    if region:
        rows = conn.execute("""
            SELECT * FROM signaux_terrain
            WHERE traite = 0 AND region = ?
            ORDER BY priorite DESC, date_collecte DESC
        """, (region,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM signaux_terrain
            WHERE traite = 0
            ORDER BY priorite DESC, date_collecte DESC
        """).fetchall()
    conn.close()
    return rows


def marquer_signaux_traites(region):
    """Marque tous les signaux d'une région comme traités."""
    conn = get_connection()
    conn.execute("UPDATE signaux_terrain SET traite=1 WHERE region=?", (region,))
    conn.commit()
    conn.close()


# ============================================================
# FONCTIONS ALERTES TERRAIN
# ============================================================

def sauvegarder_alerte_terrain(region, chaleur, resume, evenements,
                                signal_partisan, post_breaking):
    """Sauvegarde une alerte terrain générée."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO alertes_terrain
        (region, chaleur, resume, evenements, signal_partisan, post_breaking, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (region, chaleur, resume, evenements, signal_partisan,
          post_breaking, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_dernieres_alertes(region=None, limit=10):
    """Retourne les dernières alertes terrain."""
    conn = get_connection()
    if region:
        rows = conn.execute("""
            SELECT * FROM alertes_terrain WHERE region=?
            ORDER BY date_creation DESC LIMIT ?
        """, (region, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM alertes_terrain
            ORDER BY date_creation DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return rows


# ============================================================
# FONCTIONS SANTÉ SOURCES
# ============================================================

def upsert_source_health(source_name, region, url, statut, nb_articles,
                          latence_ms, url_alternative=None):
    """Insère ou met à jour le statut de santé d'une source."""
    now = datetime.now().isoformat()
    conn = get_connection()
    conn.execute("""
        INSERT INTO sources_health
            (source_name, region, url, statut, nb_articles, latence_ms,
             derniere_ok, dernier_test, url_alternative)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_name) DO UPDATE SET
            url            = excluded.url,
            statut         = excluded.statut,
            nb_articles    = excluded.nb_articles,
            latence_ms     = excluded.latence_ms,
            derniere_ok    = CASE WHEN excluded.statut = 'ok' THEN excluded.derniere_ok
                                  ELSE sources_health.derniere_ok END,
            dernier_test   = excluded.dernier_test,
            url_alternative = COALESCE(excluded.url_alternative,
                                       sources_health.url_alternative)
    """, (source_name, region, url, statut, nb_articles, latence_ms,
          now if statut == "ok" else None, now, url_alternative))
    conn.commit()
    conn.close()


def get_sources_health():
    """Retourne toutes les sources avec leur statut."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM sources_health ORDER BY statut DESC, source_name ASC
    """).fetchall()
    conn.close()
    return rows


def get_sources_mortes():
    """Retourne les sources en statut mort ou vide."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM sources_health
        WHERE statut IN ('mort', 'vide')
        ORDER BY source_name ASC
    """).fetchall()
    conn.close()
    return rows


def get_sources_health_summary():
    """Retourne un résumé : {ok, lent, vide, mort, inconnu}."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT statut, COUNT(*) as n FROM sources_health GROUP BY statut
    """).fetchall()
    conn.close()
    return {r["statut"]: r["n"] for r in rows}


# ============================================================
# ARCHIVAGE DES DONNÉES ANCIENNES
# ============================================================

def archive_old_data(db_path: str = "veille.db", days_threshold: int = 90) -> int:
    """
    Archive les données plus anciennes que N jours pour éviter la croissance infinie.
    
    Args:
        db_path: Chemin de la base de données
        days_threshold: Nombre de jours avant archivage
    
    Returns:
        Nombre d'articles archivés
    """
    import logging
    logger = logging.getLogger(__name__)
    
    conn = get_connection(db_path) if 'db_path' in locals() else get_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Archiver les anciens articles
    cursor.execute("""
        UPDATE articles 
        SET statut = 'archive' 
        WHERE date_collecte < ? AND statut != 'archive'
    """, (cutoff_date,))
    articles_archived = cursor.rowcount
    
    # Archiver les anciens posts publiés
    cursor.execute("""
        UPDATE posts_x 
        SET statut = 'archive' 
        WHERE date_creation < ? AND statut = 'publie'
    """, (cutoff_date,))
    posts_archived = cursor.rowcount
    
    # Archiver les prédictions vérifiées anciennes
    cursor.execute("""
        UPDATE predictions 
        SET statut = 'archive' 
        WHERE date_echeance < ? AND statut = 'verifiee'
    """, (cutoff_date,))
    predictions_archived = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    total_archived = articles_archived + posts_archived + predictions_archived
    logger.info(f"Archivage: {total_archived} éléments archivés (>{days_threshold} jours)")
    logger.info(f"  - Articles: {articles_archived}")
    logger.info(f"  - Posts X: {posts_archived}")
    logger.info(f"  - Prédictions: {predictions_archived}")
    
    return total_archived


def get_db_connection(db_path: str = None):
    """
    Retourne une connexion à la base de données.
    
    Args:
        db_path: Chemin optionnel vers la base (défaut: veille.db)
    
    Returns:
        Connexion SQLite
    """
    path = db_path if db_path else "veille.db"
    conn = sqlite3.connect(path)
    conn.row_factory = _dict_factory
    return conn


# Point d'entrée
if __name__ == "__main__":
    init_db()
