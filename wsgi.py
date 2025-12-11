"""
WSGI entry point for production deployment
This file is used by Gunicorn and other WSGI servers

For Gunicorn with eventlet workers, use: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app
"""

from app import create_app

# Create the Flask application
# For Gunicorn with eventlet, we use the Flask app directly
# The eventlet worker will handle SocketIO properly
app = create_app()

# Export as 'application' for some WSGI servers, 'app' for Gunicorn
application = app

