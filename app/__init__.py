"""
Sampark Setu - Real-time Chat Application
Flask application initialization
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
import os

# Initialize extensions
socketio = SocketIO(cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))

def create_app():
    """Application factory pattern"""
    # Get the root directory (parent of app directory)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sampark-setu-secret-key-change-in-production')
    
    # Database configuration - use PostgreSQL on Render, SQLite locally
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides PostgreSQL, convert postgres:// to postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local development - use SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sampark_setu.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Only set engine options for PostgreSQL (not SQLite)
    if database_url and 'postgresql' in database_url:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    # Session configuration
    is_production = os.environ.get('RENDER') == 'true' or os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production  # True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize extensions with app
    from app.models import db
    db.init_app(app)
    login_manager.init_app(app)
    # Use eventlet for production, threading for development
    # Default to threading for local development (more reliable)
    async_mode = os.environ.get('ASYNC_MODE', 'threading')
    # Only use eventlet if explicitly set and available
    if async_mode == 'eventlet':
        try:
            import eventlet
            socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")
        except ImportError:
            print("Warning: eventlet not available, falling back to threading")
            socketio.init_app(app, async_mode='threading', cors_allowed_origins="*")
    else:
        socketio.init_app(app, async_mode=async_mode, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.uploads import uploads_bp
    from app.routes.profile import profile_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(profile_bp)
    
    # Register SocketIO events
    from app.socketio_events import register_socketio_events
    register_socketio_events(socketio)
    
    # Create database tables and upload directories
    with app.app_context():
        db.create_all()
        
        # Create upload directories if they don't exist
        uploads_dir = os.path.join(root_dir, 'uploads')
        audio_dir = os.path.join(uploads_dir, 'audio')
        attachments_dir = os.path.join(uploads_dir, 'attachments')
        profiles_dir = os.path.join(uploads_dir, 'profiles')
        
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(attachments_dir, exist_ok=True)
        os.makedirs(profiles_dir, exist_ok=True)
    
    return app

