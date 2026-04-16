# extensions.py — single source of truth for all Flask extensions
# Import from here everywhere to guarantee only ONE instance exists.
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
