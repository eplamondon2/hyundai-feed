"""
Cache simple en mémoire avec TTL.
Recharge l'inventaire toutes les 6 heures automatiquement.
"""
import time, logging, threading
from app.scraper import get_all_vehicles

log = logging.getLogger(__name__)

TTL_SECONDS = 6 * 3600  # 6 heures

_cache = {
    "vehicles": [],
    "last_refresh": 0,
    "lock": threading.Lock(),
}


def _needs_refresh() -> bool:
    return time.time() - _cache["last_refresh"] > TTL_SECONDS


def get_vehicles(force: bool = False) -> list:
    """Retourne les véhicules depuis le cache, refresh si expiré."""
    with _cache["lock"]:
        if force or _needs_refresh():
            log.info("Rafraîchissement du cache inventaire...")
            try:
                vehicles = get_all_vehicles()
                if vehicles:
                    _cache["vehicles"] = vehicles
                    _cache["last_refresh"] = time.time()
                    log.info(f"Cache mis à jour: {len(vehicles)} véhicules")
                else:
                    log.warning("Scraper n'a retourné aucun véhicule — cache conservé")
            except Exception as e:
                log.error(f"Erreur lors du refresh: {e}")
        return _cache["vehicles"]


def cache_age_minutes() -> float:
    elapsed = time.time() - _cache["last_refresh"]
    return round(elapsed / 60, 1)

