from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app import routes, models, auth

