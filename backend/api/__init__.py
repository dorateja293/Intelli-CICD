from backend.api.routes.auth import router as auth_router
from backend.api.routes.predict import router as predict_router
from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.webhook import router as webhook_router
from backend.api.routes.logs import router as logs_router
from backend.api.routes.system import router as system_router
from backend.api.routes.profile import router as profile_router

__all__ = [
    "auth_router", "predict_router", "analytics_router", "webhook_router",
    "logs_router", "system_router", "profile_router",
]
