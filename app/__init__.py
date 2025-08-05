import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # CORS configuration for dashboard integration
    CORS(app,
         origins=[
             "http://localhost:3000",        # React development
             "http://127.0.0.1:3000",        # Alternative localhost
             "https://your-dashboard-domain.com",  # Production dashboard
             "*"  # Allow all origins (be more restrictive in production)
         ],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    base_dir = os.path.abspath(os.path.dirname(__file__))
    upload_folder = os.path.join(base_dir, 'uploads')

    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import routes
    app.register_blueprint(routes)

    return app
