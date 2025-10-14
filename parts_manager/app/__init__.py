import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/parts.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = os.urandom(24)
    
    db.init_app(app)
    migrations_dir = os.path.join(os.path.dirname(app.root_path), 'migrations')
    Migrate(app, db, directory=migrations_dir)

    from .models import Part, Tag

    from .routes.main_routes import main_bp
    from .routes.parts_routes import parts_bp
    from .routes.tags_routes import tags_bp
    from .routes.labels_routes import labels_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(parts_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(labels_bp)

    return app
