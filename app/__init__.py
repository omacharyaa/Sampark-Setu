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
    
    # Database configuration - use PostgreSQL on Render/Railway, SQLite locally
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
    # Detect production environment (Render, Railway, or explicit FLASK_ENV)
    is_production = (
        os.environ.get('RENDER') == 'true' or 
        os.environ.get('RAILWAY_ENVIRONMENT') is not None or
        os.environ.get('RAILWAY') == 'true' or
        os.environ.get('FLASK_ENV') == 'production'
    )
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
        
        # Run runtime migrations to ensure all columns exist
        # This is a safety net in case migrations didn't run during build
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            database_url = os.environ.get('DATABASE_URL', '')
            
            def column_exists_safe(table_name, column_name):
                """Safely check if column exists"""
                try:
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    return column_name in columns
                except:
                    return False
            
            # Check and add missing columns
            with db.engine.connect() as conn:
                # Check file_name in messages
                if not column_exists_safe('messages', 'file_name'):
                    try:
                        conn.execute(text("ALTER TABLE messages ADD COLUMN file_name VARCHAR(255)"))
                        conn.commit()
                        print("✓ Runtime migration: Added file_name column to messages")
                    except Exception as e:
                        conn.rollback()
                        print(f"⚠ Runtime migration: file_name may already exist: {e}")
                
                # Check profile_picture and display_name in users
                if not column_exists_safe('users', 'profile_picture'):
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)"))
                        conn.commit()
                        print("✓ Runtime migration: Added profile_picture column to users")
                    except Exception as e:
                        conn.rollback()
                        print(f"⚠ Runtime migration: profile_picture may already exist: {e}")
                
                if not column_exists_safe('users', 'display_name'):
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
                        conn.commit()
                        print("✓ Runtime migration: Added display_name column to users")
                    except Exception as e:
                        conn.rollback()
                        print(f"⚠ Runtime migration: display_name may already exist: {e}")
        except Exception as e:
            # Don't fail app startup if migrations fail - log and continue
            print(f"⚠ Runtime migration check failed (non-critical): {e}")
        
        # Create upload directories if they don't exist
        uploads_dir = os.path.join(root_dir, 'uploads')
        audio_dir = os.path.join(uploads_dir, 'audio')
        attachments_dir = os.path.join(uploads_dir, 'attachments')
        profiles_dir = os.path.join(uploads_dir, 'profiles')
        
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(attachments_dir, exist_ok=True)
        os.makedirs(profiles_dir, exist_ok=True)
    
    return app

# Provide default WSGI application for servers expecting `app:app`
# This mirrors `wsgi.py` but keeps compatibility if start command is misconfigured
app = create_app()
application = app

