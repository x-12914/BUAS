from app import create_app
from app.celery_app import make_celery

app = create_app()
celery = make_celery(app)

if __name__ == "__main__":
    # Run Flask server on port 5000 for VPS deployment
    app.run(
        host='0.0.0.0',  # Bind to all interfaces for VPS access
        port=5000,       # Flask server port
        debug=True       # Change to False in production
    )
