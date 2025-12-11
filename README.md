# Sampark Setu - Real-time Chat Application

A fully functional, production-quality real-time chat application built with Flask, Flask-SocketIO, and SQLite/PostgreSQL.

## Features

- ✅ User registration, login, and authentication
- ✅ Real-time chat with SocketIO
- ✅ Multiple chat rooms
- ✅ Voice messages (Discord-style)
- ✅ GIF search and sharing
- ✅ File attachments (images, videos, documents)
- ✅ Typing indicators
- ✅ Online/offline user status
- ✅ Profile management with pictures
- ✅ Light/Dark mode toggle
- ✅ Mobile-responsive design
- ✅ Message and room deletion
- ✅ Notification sounds

## Quick Start

### Option 1: Using the Setup Script (Recommended)

```bash
python run_local.py
```

This script will:
- Check for virtual environment
- Install dependencies
- Initialize database
- Start the server

### Option 2: Manual Setup

1. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

5. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`
   - Register a new account or login

## Project Structure

```
Sampark Setu/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py             # Database models (User, Room, Message)
│   ├── routes/
│   │   ├── auth.py           # Authentication routes
│   │   ├── chat.py           # Chat routes and API
│   │   ├── uploads.py        # File upload handling
│   │   └── profile.py        # Profile management
│   └── socketio_events.py    # SocketIO event handlers
├── templates/
│   ├── base.html             # Base template
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── chat.html             # Main chat interface
│   └── profile.html          # Profile page
├── static/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/
│       └── chat.js            # Client-side JavaScript
├── uploads/                  # User uploads (audio, attachments, profiles)
├── run.py                    # Application entry point
├── init_db.py               # Database initialization script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `DATABASE_URL`: Database connection string (SQLite used by default)
- `GIPHY_API_KEY`: Giphy API key for GIF search (optional)
- `RENDER`: Set to `true` when deployed on Render
- `ASYNC_MODE`: SocketIO async mode (`eventlet` or `threading`)

### Database

- **Development**: SQLite (`sampark_setu.db`)
- **Production**: PostgreSQL (configured via `DATABASE_URL`)

## Deployment

### Deploy to Render

See `RENDER_DEPLOYMENT.md` for detailed deployment instructions.

Quick steps:
1. Push code to GitHub
2. Connect repository to Render
3. Render will auto-detect `render.yaml` and deploy

## Usage

1. **Register/Login**: Create an account or login
2. **Create Room**: Click "Create Room" to create a new chat room
3. **Join Room**: Enter a room ID to join an existing room
4. **Send Messages**: Type and send text messages
5. **Voice Messages**: Click the microphone icon to record and send voice messages
6. **GIFs**: Click the GIF button to search and send GIFs
7. **Attachments**: Click the paperclip icon to attach files
8. **Profile**: Click your profile picture to edit your profile

## Troubleshooting

### Messages stuck on "Loading messages"
- Check browser console (F12) for errors
- Verify database is initialized
- Check server logs for errors

### Audio not playing
- Ensure audio files are being uploaded correctly
- Check browser console for audio errors
- Verify file permissions

### Database errors
- Run `python init_db.py` to initialize/update database
- Check if database file exists and has correct permissions

### Port already in use
- Change port in `run.py`: `port = int(os.environ.get('PORT', 5001))`
- Or stop the process using port 5000

## Development

### Running in Debug Mode

The application runs in debug mode by default when using `run.py`. For production:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 run:app
```

### Database Migrations

For schema changes, update `init_db.py` or use Flask-Migrate:

```bash
pip install flask-migrate
flask db init
flask db migrate -m "Description"
flask db upgrade
```

## License

This project is for educational purposes.

## Support

For issues or questions, check the logs:
- Server logs: Terminal output
- Client logs: Browser console (F12)
