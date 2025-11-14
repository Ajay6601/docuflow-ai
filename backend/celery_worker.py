"""
Celery worker entry point.
Run with: celery -A celery_worker worker --loglevel=info --pool=solo
"""
from app.celery_app import celery_app
from app.tasks import extraction_tasks

# This ensures tasks are registered when worker starts
__all__ = ['celery_app']