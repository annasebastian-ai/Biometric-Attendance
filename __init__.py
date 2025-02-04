from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import boto3
import pymysql
import json
import time


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    

    app.config['SECRET_KEY'] = 'your_secret_key'

    # Database connection settings using SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME', 'admin')}:"
        f"{os.getenv('DB_PASSWORD', 'Anna1999*')}@"
        f"{os.getenv('DB_SERVERNAME', 'database-1.cv2ua06cqdq7.ap-south-1.rds.amazonaws.com')}/"
        f"{os.getenv('DB_NAME', 'iot')}"
    )

    db.init_app(app)

    # Import models and blueprints
    from .models import User, Finger
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Set up the login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
