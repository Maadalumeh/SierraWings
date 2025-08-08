import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from mail_service import mail, init_mail

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sierrawings-emergency-medical-delivery-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///sierrawings.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Flask-Mail
init_mail(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register blueprints
def register_blueprints():
    """Register application blueprints"""
    from auth import bp as auth_bp
    from admin import bp as admin_bp
    from hospital import bp as hospital_bp
    from routes_announcement import announcement_bp
    from routes_voice_checklist import voice_checklist
    from routes_feedback import feedback_bp
    # Import update routes  
    import routes_updates
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(hospital_bp, url_prefix='/hospital')
    app.register_blueprint(announcement_bp)
    app.register_blueprint(voice_checklist)
    app.register_blueprint(feedback_bp)

# Function to initialize database structure
def init_database():
    """Initialize database structure for production"""
    import models
    import models_extensions
    
    # Create all tables
    db.create_all()
    
    # Register blueprints
    register_blueprints()
    
    logging.info("SierraWings database initialized for production")
