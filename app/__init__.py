from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import routes
    app.register_blueprint(routes)

    return app
