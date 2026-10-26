from datetime import datetime, timezone
from functools import wraps

from app.config import settings


class LimiteEtapesAtteinte(RuntimeError):
    pass


def etape(nom: str):
    """Journalise chaque étape et applique la limite d'actions par demande."""
    def deco(fn):
        @wraps(fn)
        def wrapper(state):
            n = state.get("nb_etapes", 0) + 1
            if n > settings.max_etapes:
                raise LimiteEtapesAtteinte(f"Limite de {settings.max_etapes} étapes dépassée")
            maj = fn(state) or {}
            raison = maj.pop("_raison", "")
            entree = {"etape": nom, "raison": raison, "ts": datetime.now(timezone.utc).isoformat()}
            return {**maj, "nb_etapes": n, "journal": [*state.get("journal", []), entree]}
        return wrapper
    return deco
