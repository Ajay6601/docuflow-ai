from fastapi import APIRouter
from app.api.v1 import documents

api_router = APIRouter()

# Include document routes
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)