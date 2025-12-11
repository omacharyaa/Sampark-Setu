"""
Sampark Setu - Real-time Chat Application
Main application entry point
"""

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Run the application
    # In production, use a production WSGI server like Gunicorn with eventlet workers
    # For Render deployment, use: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=debug
    )

