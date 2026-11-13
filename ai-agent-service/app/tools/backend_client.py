import logging
import httpx
from app.config import settings

logger = logging.getLogger("ai_agent_service.backend_client")

_token: str | None = None

def _get_auth_headers(force_refresh: bool = False) -> dict[str, str]:
    global _token
    if not _token or force_refresh:
        try:
            with httpx.Client(base_url=settings.BACKEND_API_URL, timeout=5.0) as client:
                resp = client.post("/auth/login", json={
                    "username": settings.ADMIN_USERNAME,
                    "password": settings.ADMIN_PASSWORD
                })
                if resp.status_code == 200:
                    _token = resp.json().get("token")
                    logger.info("Token de service backend obtenu avec succès.")
                else:
                    logger.warning(f"Échec d'authentification auprès du backend: status={resp.status_code}")
        except Exception as ex:
            logger.warning(f"Impossible d'obtenir un token d'authentification pour le backend: {ex}")
    return {"Authorization": f"Bearer {_token}"} if _token else {}

def fetch_players() -> list[dict]:
    """
    Récupère la liste des joueurs enregistrés dans la ligue via l'API Spring Boot.
    """
    try:
        with httpx.Client(base_url=settings.BACKEND_API_URL, timeout=10.0) as client:
            headers = _get_auth_headers()
            resp = client.get("/players", headers=headers)
            if resp.status_code == 401:
                # Token expiré, retry avec refresh
                headers = _get_auth_headers(force_refresh=True)
                resp = client.get("/players", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Réponse inattendue de /players: status={resp.status_code}")
            return []
    except Exception as ex:
        logger.error(f"Échec de connexion au backend Spring pour /players: {ex}")
        return []

def fetch_matches() -> list[dict]:
    """
    Récupère la liste des matchs de la ligue via l'API Spring Boot.
    """
    try:
        with httpx.Client(base_url=settings.BACKEND_API_URL, timeout=10.0) as client:
            headers = _get_auth_headers()
            resp = client.get("/matches", headers=headers)
            if resp.status_code == 401:
                headers = _get_auth_headers(force_refresh=True)
                resp = client.get("/matches", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Réponse inattendue de /matches: status={resp.status_code}")
            return []
    except Exception as ex:
        logger.error(f"Échec de connexion au backend Spring pour /matches: {ex}")
        return []

def predict_match(player1_id: int, player2_id: int) -> dict | None:
    """
    Calcule la prédiction probabiliste Elo entre deux joueurs via l'API Spring Boot.
    """
    try:
        with httpx.Client(base_url=settings.BACKEND_API_URL, timeout=10.0) as client:
            headers = _get_auth_headers()
            resp = client.get(f"/matches/predict?player1Id={player1_id}&player2Id={player2_id}", headers=headers)
            if resp.status_code == 401:
                headers = _get_auth_headers(force_refresh=True)
                resp = client.get(f"/matches/predict?player1Id={player1_id}&player2Id={player2_id}", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Réponse inattendue de /matches/predict: status={resp.status_code}")
            return None
    except Exception as ex:
        logger.error(f"Échec de connexion au backend Spring pour /matches/predict: {ex}")
        return None
