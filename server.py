from app import create_app
from app.celery_app import make_celery, celery as celery_global

app = create_app()
celery = make_celery(app)

# Export celery instance globally so tasks can import it
import app.tasks
