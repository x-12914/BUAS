# server.py
from app import create_app
from app.celery_app import celery

app = create_app()

# Tie Flask app context to Celery
celery.conf.update(app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask
