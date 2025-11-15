from fastapi import APIRouter
from app.api.v1 import documents, websocket, search, auth, analytics

api_router = APIRouter()

# Include auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include document routes
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# Include WebSocket routes
api_router.include_router(
    websocket.router,
    tags=["websocket"]
)

# Include search routes
api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)

# Include analytics routes
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)