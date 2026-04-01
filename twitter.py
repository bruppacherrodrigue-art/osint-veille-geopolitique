"""
twitter.py — Intégration X (Twitter) via tweepy
Poste des tweets simples et des threads directement depuis l'app.

Config requise dans config.py :
    TWITTER_API_KEY        = "..."
    TWITTER_API_SECRET     = "..."
    TWITTER_ACCESS_TOKEN   = "..."
    TWITTER_ACCESS_SECRET  = "..."
"""

import os

try:
    from config import (
        X_API_KEY, X_API_SECRET,
        X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
    )
except ImportError:
    X_API_KEY             = os.environ.get("X_API_KEY", "")
    X_API_SECRET          = os.environ.get("X_API_SECRET", "")
    X_ACCESS_TOKEN        = os.environ.get("X_ACCESS_TOKEN", "")
    X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")


def _get_client():
    """Crée un client tweepy v2. Retourne None si tweepy absent ou clés manquantes."""
    if not all([X_API_KEY, X_API_SECRET,
                X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        return None, "Clés Twitter manquantes dans config.py"
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        return client, None
    except ImportError:
        return None, "tweepy non installé — pip install tweepy"
    except Exception as e:
        return None, str(e)


def poster_sur_x(texte):
    """
    Poste un tweet simple sur X.
    Retourne (tweet_id, None) en succès ou (None, message_erreur).
    """
    client, err = _get_client()
    if not client:
        return None, err
    try:
        response = client.create_tweet(text=texte[:280])
        return response.data["id"], None
    except Exception as e:
        return None, str(e)


def poster_thread_sur_x(tweets):
    """
    Poste un thread sur X.
    Retourne (id_premier_tweet, None) en succès ou (None, message_erreur).
    """
    client, err = _get_client()
    if not client:
        return None, err
    try:
        premier_id = None
        reply_to = None
        for tweet in tweets:
            if not tweet.strip():
                continue
            if reply_to:
                response = client.create_tweet(
                    text=tweet[:280],
                    in_reply_to_tweet_id=reply_to
                )
            else:
                response = client.create_tweet(text=tweet[:280])
            reply_to = response.data["id"]
            if premier_id is None:
                premier_id = reply_to
        return premier_id, None
    except Exception as e:
        return None, str(e)
