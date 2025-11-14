Start Multiple Workers (Optional)
To process documents faster, start multiple workers:
Terminal 2:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker1@%h
Terminal 3:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker2@%h
Terminal 4:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker3@%h


docker exec -it docuflow-ai-postgres-1 psql -U docuflow -d docuflow_db