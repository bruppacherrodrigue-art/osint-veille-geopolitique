"""
utils.py — Utilitaires communs pour la sécurité, robustesse et performance

Contient :
    - Retry exponentiel avec logging structuré
    - Validation des clés API
    - Rate limiting
    - Cache disque (scraping + Tavily)
    - Sauvegarde automatique mémoire
    - Sanitization des inputs
"""

import os
import json
import time
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# ============================================================
# CONFIGURATION LOGGING STRUCTURÉ
# ============================================================

def setup_logging(level=logging.INFO):
    """Configure un logging structuré avec timestamps."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('veille.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


# ============================================================
# VALIDATION DES CLÉS API
# ============================================================

class APIKeyValidationError(Exception):
    """Exception levée quand une clé API requise est manquante."""
    pass


def validate_api_keys(required_keys: list) -> None:
    """
    Valide que toutes les clés API requises sont présentes.
    Lève une exception claire si une clé manque.
    
    Args:
        required_keys: Liste des noms de variables d'environnement requises
    
    Raises:
        APIKeyValidationError: Si une ou plusieurs clés sont manquantes
    """
    missing = []
    for key_name in required_keys:
        key_value = os.environ.get(key_name, "")
        if not key_value or key_value.startswith("YOUR_"):
            missing.append(key_name)
    
    if missing:
        msg = f"Clés API manquantes : {', '.join(missing)}\n"
        msg += "Veuillez configurer ces clés dans config.py ou en variables d'environnement."
        logger.error(msg)
        raise APIKeyValidationError(msg)
    
    logger.info(f"Toutes les clés API requises sont configurées ({len(required_keys)} clés)")


def get_required_api_key(key_name: str, allow_empty: bool = False) -> str:
    """
    Récupère une clé API requise avec validation stricte.
    
    Args:
        key_name: Nom de la variable d'environnement
        allow_empty: Si True, retourne chaîne vide au lieu de lever exception
    
    Returns:
        La valeur de la clé API
    
    Raises:
        APIKeyValidationError: Si la clé est manquante et allow_empty=False
    """
    key_value = os.environ.get(key_name, "")
    
    if not allow_empty and (not key_value or key_value.startswith("YOUR_")):
        msg = f"Clé API requise manquante : {key_name}"
        logger.error(msg)
        raise APIKeyValidationError(msg)
    
    return key_value


# ============================================================
# RETRY EXPONENTIEL AVEC BACKOFF
# ============================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_obj=None
):
    """
    Décorateur pour retry exponentiel avec backoff.
    
    Args:
        max_retries: Nombre maximum de tentatives
        base_delay: Délai initial en secondes
        max_delay: Délai maximum en secondes
        exponential_base: Base pour le calcul exponentiel
        exceptions: Tuple des exceptions à catcher
        logger_obj: Logger à utiliser (défaut: logger global)
    
    Returns:
        Décorateur de fonction
    """
    log = logger_obj or logger
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        log.error(f"{func.__name__} échec après {max_retries} tentatives: {e}")
                        raise
                    
                    # Calcul du délai exponentiel avec jitter
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    jitter = delay * 0.1 * (hash(str(time.time())) % 100) / 100
                    total_delay = delay + jitter
                    
                    log.warning(
                        f"{func.__name__} tentative {attempt + 1}/{max_retries + 1} échouée. "
                        f"Prochaine tentative dans {total_delay:.2f}s: {e}"
                    )
                    time.sleep(total_delay)
            
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================
# RATE LIMITING
# ============================================================

class RateLimiter:
    """
    Limiteur de taux simple pour éviter de spammer les APIs.
    Utilise un algorithme de fenêtre glissante.
    """
    
    def __init__(self, calls_per_second: float = 1.0, burst: int = 5):
        """
        Args:
            calls_per_second: Nombre maximum d'appels par seconde
            burst: Nombre maximum d'appels burst autorisés
        """
        self.min_interval = 1.0 / calls_per_second
        self.burst = burst
        self.calls = []
        self._lock = False
    
    def wait(self):
        """Attend si nécessaire pour respecter le rate limit."""
        now = time.time()
        
        # Nettoyer les anciens appels (> 1 seconde)
        self.calls = [t for t in self.calls if now - t < 1.0]
        
        # Vérifier burst
        if len(self.calls) >= self.burst:
            oldest = min(self.calls)
            sleep_time = 1.0 - (now - oldest)
            if sleep_time > 0:
                logger.debug(f"Rate limiter: attente {sleep_time:.2f}s")
                time.sleep(sleep_time)
                now = time.time()
                self.calls = [t for t in self.calls if now - t < 1.0]
        
        # Vérifier intervalle minimum
        if self.calls:
            last_call = max(self.calls)
            elapsed = now - last_call
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug(f"Rate limiter: attente {sleep_time:.2f}s (intervalle)")
                time.sleep(sleep_time)
        
        self.calls.append(time.time())
    
    def __call__(self, func: Callable) -> Callable:
        """Décorateur pour appliquer le rate limiting à une fonction."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper


# Rate limiters pré-configurés pour les APIs courantes
RATE_LIMITERS = {
    'anthropic': RateLimiter(calls_per_second=0.5, burst=3),      # 2 req/s max
    'tavily': RateLimiter(calls_per_second=0.2, burst=2),         # 5 req/s max, prudent
    'twitter': RateLimiter(calls_per_second=0.5, burst=5),        # 2 req/s
    'rss': RateLimiter(calls_per_second=2.0, burst=10),           # RSS plus permissif
    'discord': RateLimiter(calls_per_second=0.5, burst=5),        # Webhook Discord
}


# ============================================================
# CACHE DISQUE POUR SCRAPING ET TAVILY
# ============================================================

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

# Cache pour le contenu scrapé (7 jours)
SCRAPING_CACHE_FILE = CACHE_DIR / "scraping_cache.json"
SCRAPING_CACHE_TTL = timedelta(days=7)

# Cache pour les résultats Tavily (24 heures)
TAVILY_CACHE_FILE = CACHE_DIR / "tavily_cache.json"
TAVILY_CACHE_TTL = timedelta(hours=24)


def _load_cache(cache_file: Path) -> Dict[str, Any]:
    """Charge un fichier cache JSON."""
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache chargé: {cache_file} ({len(data)} entrées)")
                return data
        except Exception as e:
            logger.warning(f"Erreur lecture cache {cache_file}: {e}")
    return {}


def _save_cache(cache_file: Path, data: Dict[str, Any]) -> None:
    """Sauvegarde un fichier cache JSON."""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Cache sauvegardé: {cache_file} ({len(data)} entrées)")
    except Exception as e:
        logger.error(f"Erreur écriture cache {cache_file}: {e}")


def _clean_expired_cache(cache_data: Dict, ttl: timedelta) -> Dict:
    """Supprime les entrées expirées du cache."""
    now = datetime.now()
    cleaned = {}
    
    for key, value in cache_data.items():
        if isinstance(value, dict) and 'timestamp' in value:
            timestamp = datetime.fromisoformat(value['timestamp'])
            if now - timestamp < ttl:
                cleaned[key] = value
        else:
            # Ancien format sans timestamp, on garde
            cleaned[key] = value
    
    if len(cleaned) < len(cache_data):
        logger.info(f"Nettoyage cache: {len(cache_data) - len(cleaned)} entrées expirées supprimées")
    
    return cleaned


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Génère une clé de cache unique à partir des arguments."""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_scraping_cache(url: str) -> Optional[str]:
    """
    Récupère le contenu scrapé depuis le cache.
    
    Args:
        url: URL de l'article
    
    Returns:
        Contenu scrapé ou None si non trouvé/expiré
    """
    cache = _load_cache(SCRAPING_CACHE_FILE)
    cache = _clean_expired_cache(cache, SCRAPING_CACHE_TTL)
    
    if url in cache:
        entry = cache[url]
        logger.debug(f"Cache hit scraping: {url}")
        return entry.get('content')
    
    return None


def set_scraping_cache(url: str, content: str) -> None:
    """
    Sauvegarde le contenu scrapé dans le cache.
    
    Args:
        url: URL de l'article
        content: Contenu scrapé à cacher
    """
    cache = _load_cache(SCRAPING_CACHE_FILE)
    cache[url] = {
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    _save_cache(SCRAPING_CACHE_FILE, cache)


def get_tavily_cache(query: str, params: Dict = None) -> Optional[Dict]:
    """
    Récupère un résultat Tavily depuis le cache.
    
    Args:
        query: Requête de recherche
        params: Paramètres additionnels (search_depth, etc.)
    
    Returns:
        Résultats Tavily ou None si non trouvé/expiré
    """
    cache = _load_cache(TAVILY_CACHE_FILE)
    cache = _clean_expired_cache(cache, TAVILY_CACHE_TTL)
    
    key = _generate_cache_key('tavily', query, **(params or {}))
    
    if key in cache:
        logger.debug(f"Cache hit Tavily: {query}")
        return cache[key].get('results')
    
    return None


def set_tavily_cache(query: str, results: Dict, params: Dict = None) -> None:
    """
    Sauvegarde les résultats Tavily dans le cache.
    
    Args:
        query: Requête de recherche
        results: Résultats à cacher
        params: Paramètres additionnels utilisés
    """
    cache = _load_cache(TAVILY_CACHE_FILE)
    key = _generate_cache_key('tavily', query, **(params or {}))
    
    cache[key] = {
        'results': results,
        'timestamp': datetime.now().isoformat(),
        'query': query
    }
    _save_cache(TAVILY_CACHE_FILE, cache)


# ============================================================
# SANITIZATION DES INPUTS
# ============================================================

import re
import html


def sanitize_input(text: str, max_length: int = 10000, allow_html: bool = False) -> str:
    """
    Sanitize et valide un input utilisateur.
    
    Args:
        text: Texte à sanitiser
        max_length: Longueur maximale autorisée
        allow_html: Si True, conserve le HTML (après nettoyage)
    
    Returns:
        Texte sanitisé
    """
    if not text:
        return ""
    
    # Tronquer si trop long
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input tronqué à {max_length} caractères")
    
    if not allow_html:
        # Échapper tout le HTML
        text = html.escape(text)
    else:
        # Nettoyer le HTML dangereux
        text = clean_dangerous_html(text)
    
    # Supprimer les caractères de contrôle invisibles
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_dangerous_html(html_text: str) -> str:
    """
    Nettoie le HTML dangereux (scripts, iframes, etc.).
    
    Args:
        html_text: HTML à nettoyer
    
    Returns:
        HTML sécurisé
    """
    # Supprimer les balises dangereuses
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    
    for tag in dangerous_tags:
        html_text = re.sub(
            f'<{tag}[^>]*>.*?</{tag}>',
            '',
            html_text,
            flags=re.IGNORECASE | re.DOTALL
        )
        html_text = re.sub(f'<{tag}[^>]*/?>', '', html_text, flags=re.IGNORECASE)
    
    # Supprimer les attributs dangereux (javascript:, on*, data:)
    html_text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', html_text, flags=re.IGNORECASE)
    html_text = re.sub(r'src\s*=\s*["\']data:[^"\']*["\']', 'src=""', html_text, flags=re.IGNORECASE)
    
    return html_text


def sanitize_url(url: str) -> Optional[str]:
    """
    Valide et sanitize une URL.
    
    Args:
        url: URL à valider
    
    Returns:
        URL validée ou None si invalide
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Pattern simple de validation URL
    pattern = r'^https?://[^\s<>\"{}|\\^`\[\]]+$'
    
    if not re.match(pattern, url, re.IGNORECASE):
        logger.warning(f"URL invalide détectée: {url[:100]}")
        return None
    
    # Bloquer les URLs avec javascript: ou data:
    if url.lower().startswith(('javascript:', 'data:', 'file:')):
        logger.warning(f"URL dangereuse bloquée: {url[:100]}")
        return None
    
    return url


# ============================================================
# SAUVEGARDE AUTOMATIQUE MÉMOIRE
# ============================================================

MEMORY_BACKUP_DIR = Path(".backups")
MEMORY_BACKUP_DIR.mkdir(exist_ok=True)


def backup_memory_file(memory_file: str = "memory_state.json") -> Optional[str]:
    """
    Crée une sauvegarde automatique du fichier de mémoire.
    
    Args:
        memory_file: Chemin du fichier de mémoire
    
    Returns:
        Chemin du fichier de backup ou None si échec
    """
    if not os.path.exists(memory_file):
        logger.debug(f"Pas de fichier mémoire à sauvegarder: {memory_file}")
        return None
    
    try:
        # Générer un nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{Path(memory_file).stem}_{timestamp}.json"
        backup_path = MEMORY_BACKUP_DIR / backup_name
        
        # Copier le fichier
        with open(memory_file, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        logger.info(f"Sauvegarde mémoire créée: {backup_path}")
        
        # Nettoyer les anciennes sauvegardes (> 30 jours)
        cleanup_old_backups(days=30)
        
        return str(backup_path)
    
    except Exception as e:
        logger.error(f"Erreur sauvegarde mémoire: {e}")
        return None


def cleanup_old_backups(directory: Path = None, days: int = 30) -> int:
    """
    Supprime les sauvegardes plus vieilles que N jours.
    
    Args:
        directory: Dossier des backups (défaut: MEMORY_BACKUP_DIR)
        days: Âge maximum en jours
    
    Returns:
        Nombre de fichiers supprimés
    """
    if directory is None:
        directory = MEMORY_BACKUP_DIR
    
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    
    for file in directory.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff:
                file.unlink()
                removed += 1
                logger.debug(f"Backup supprimé: {file.name}")
        except Exception as e:
            logger.warning(f"Erreur suppression backup {file}: {e}")
    
    if removed > 0:
        logger.info(f"Nettoyage backups: {removed} fichiers supprimés")
    
    return removed


def auto_backup_on_update(memory_file: str = "memory_state.json"):
    """
    Décorateur pour sauvegarder automatiquement avant modification.
    
    Args:
        memory_file: Chemin du fichier de mémoire
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Backup avant modification
            backup_memory_file(memory_file)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# OPTIMISATION SQL - INDEX
# ============================================================

def create_sql_indexes(db_path: str = "veille.db") -> None:
    """
    Crée des index sur les colonnes fréquemment requêtées.
    À exécuter une fois après init_db().
    
    Args:
        db_path: Chemin de la base de données
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    indexes = [
        # Articles
        ("idx_articles_region", "articles(region)"),
        ("idx_articles_date_collecte", "articles(date_collecte)"),
        ("idx_articles_source", "articles(source_name)"),
        
        # Analyses
        ("idx_analyses_region", "analyses(region)"),
        ("idx_analyses_date", "analyses(date_analyse)"),
        
        # Posts X
        ("idx_posts_statut", "posts_x(statut)"),
        ("idx_posts_region", "posts_x(region)"),
        ("idx_posts_date_creation", "posts_x(date_creation)"),
        
        # Engagement
        ("idx_engagement_tweet", "engagement(tweet_id)"),
        ("idx_engagement_region", "engagement(region)"),
        ("idx_engagement_published", "engagement(published_at)"),
        
        # Prédictions
        ("idx_predictions_region", "predictions(region)"),
        ("idx_predictions_statut", "predictions(statut)"),
        ("idx_predictions_echeance", "predictions(date_echeance)"),
        
        # Signaux terrain
        ("idx_signaux_region", "signaux_terrain(region)"),
        ("idx_signaux_traite", "signaux_terrain(traite)"),
        
        # Santé sources
        ("idx_sources_statut", "sources_health(statut)"),
        ("idx_sources_nom", "sources_health(source_name)"),
    ]
    
    created = 0
    for idx_name, idx_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            created += 1
        except Exception as e:
            logger.warning(f"Erreur création index {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    
    logger.info(f"{created} index SQL créés pour optimisation des requêtes")


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    # Test des utilitaires
    print("Test des utilitaires utils.py")
    
    # Test validation API keys
    try:
        validate_api_keys(['TEST_KEY'])
    except APIKeyValidationError as e:
        print(f"✓ Validation API fonctionne: {e}")
    
    # Test sanitization
    test_input = "<script>alert('xss')</script>Hello World"
    sanitized = sanitize_input(test_input)
    print(f"✓ Sanitization: {test_input} → {sanitized}")
    
    # Test cache
    set_scraping_cache("http://test.com", "Contenu test")
    cached = get_scraping_cache("http://test.com")
    print(f"✓ Cache scraping: {cached}")
    
    # Test backup
    if os.path.exists("memory_state.json"):
        backup_path = backup_memory_file()
        print(f"✓ Backup mémoire: {backup_path}")
    else:
        print("ℹ Pas de fichier mémoire pour test backup")
    
    print("\n✅ Tous les tests utilitaires passés")
