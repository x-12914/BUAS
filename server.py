from app import create_app, db
from app.celery_app import make_celery

app = create_app()
celery = make_celery(app)

# Optional: Create DB tables on startup
with app.app_context():
    db.create_all()
