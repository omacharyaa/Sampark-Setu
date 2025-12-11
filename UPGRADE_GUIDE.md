# Sampark Setu - Upgrade Guide

## 🎉 Major Upgrade Features

### New Features Added:

1. **Full Room Functionality**
   - ✅ Join Room button for each room
   - ✅ Switch between rooms seamlessly
   - ✅ Room-specific chat history loading
   - ✅ Messages broadcast only to joined room
   - ✅ Join/leave notifications

2. **Multiple Message Types**
   - ✅ **Text Messages**: Standard text chat
   - ✅ **GIF Messages**: Search and send GIFs using Giphy API
   - ✅ **Voice Messages**: Record and send audio messages

3. **Voice Recording**
   - ✅ MediaRecorder API integration
   - ✅ Real-time recording visualization
   - ✅ Audio upload to server
   - ✅ Audio player in chat

4. **GIF Search**
   - ✅ Giphy API integration
   - ✅ Search and trending GIFs
   - ✅ Click to send GIFs

5. **Mobile-Responsive Design**
   - ✅ 3-column layout on desktop/tablet
   - ✅ Collapsible sidebars on mobile
   - ✅ Top navigation bar on mobile
   - ✅ Touch-friendly interface
   - ✅ WhatsApp/Discord/Telegram-inspired design

## 🚀 Setup Instructions

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

This will install the `requests` library needed for GIF API integration.

### 2. Run Database Migration

If you have an existing database, run the migration script:

```bash
python migrate_db.py
```

This adds the `message_type` column to the messages table.

**Note**: New installations will automatically create the database with the correct schema.

### 3. Configure GIF API (Optional)

The app uses a public Giphy API key by default. For production, get your own free API key:

1. Go to https://developers.giphy.com/
2. Sign up for a free account
3. Create an app and get your API key
4. Set it as an environment variable:

```bash
# Windows
set GIPHY_API_KEY=your_api_key_here

# Linux/Mac
export GIPHY_API_KEY=your_api_key_here
```

Or update `app/routes/chat.py` line with your API key.

### 4. Start the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 📱 Using New Features

### Joining Rooms

1. **Desktop/Tablet**: Click on any room in the left sidebar, then click "Join"
2. **Mobile**: Tap the rooms icon in the top bar, select a room, tap "Join"

### Sending GIFs

1. Click the GIF button (📷) in the message input or header
2. Browse trending GIFs or search for specific GIFs
3. Click on a GIF to send it

### Recording Voice Messages

1. Click the microphone button (🎤) in the message input
2. Click the red record button to start recording
3. Click "Stop" when done
4. Preview your recording
5. Click "Send" to send the voice message

### Mobile Navigation

- **Rooms Icon**: Opens/closes the rooms sidebar
- **Users Icon**: Opens/closes the online users sidebar
- **GIF Icon**: Opens GIF search modal
- **Menu**: Access all features from the top navigation bar

## 🗂️ Project Structure

```
Sampark Setu/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models (updated with message_type)
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── chat.py          # Chat routes (updated with GIF API)
│   │   └── uploads.py       # NEW: Audio upload routes
│   └── socketio_events.py  # SocketIO events (updated for message types)
├── templates/
│   └── chat.html           # Completely redesigned mobile-responsive UI
├── static/
│   ├── css/
│   │   └── style.css       # Complete CSS overhaul
│   └── js/
│       └── chat.js         # Enhanced JavaScript with all new features
├── uploads/
│   └── audio/              # Audio files storage
├── migrate_db.py           # Database migration script
├── requirements.txt        # Updated dependencies
└── README.md              # Updated documentation
```

## 🔧 Database Schema Changes

### Messages Table
- Added `message_type` column (VARCHAR(20), default: 'text')
- Values: 'text', 'gif', 'audio'

### Migration
- Run `python migrate_db.py` to update existing databases
- New installations automatically include the new column

## 🎨 UI/UX Improvements

### Desktop/Tablet (≥768px)
- 3-column layout: Rooms | Chat | Users
- Full sidebar visibility
- Larger message bubbles
- Better spacing and typography

### Mobile (<768px)
- Top navigation bar
- Collapsible sidebars
- Touch-optimized buttons
- Responsive GIF grid
- Fixed bottom input area

## 🐛 Troubleshooting

### Voice Recording Not Working
- Ensure microphone permissions are granted in browser
- Check browser compatibility (Chrome, Firefox, Edge supported)
- Try using HTTPS (some browsers require secure context)

### GIFs Not Loading
- Check internet connection
- Verify Giphy API key (if using custom key)
- Check browser console for errors

### Database Migration Issues
- Backup your database before migration
- Ensure Flask app is not running during migration
- Check file permissions on database file

### Audio Files Not Playing
- Check browser audio codec support
- Ensure audio files are in supported formats (webm, mp3, wav, ogg, m4a)
- Check server file permissions

## 📝 API Endpoints

### New Endpoints

- `POST /upload_audio` - Upload audio file
- `GET /uploads/audio/<filename>` - Serve audio file
- `GET /api/search-gifs?q=<query>&limit=<limit>` - Search GIFs
- `GET /api/trending-gifs?limit=<limit>` - Get trending GIFs

## 🔒 Security Notes

1. **Audio Uploads**: Files are validated and stored securely
2. **File Size**: Maximum 10MB per audio file
3. **File Types**: Only allowed audio formats accepted
4. **Authentication**: All endpoints require login

## 🚀 Production Deployment

1. Set `GIPHY_API_KEY` environment variable
2. Change `SECRET_KEY` in `app/__init__.py`
3. Use production WSGI server (Gunicorn with eventlet)
4. Configure HTTPS for voice recording
5. Set up proper file storage (consider cloud storage for audio files)

## 📚 Additional Resources

- Giphy API Documentation: https://developers.giphy.com/docs/
- MediaRecorder API: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder
- Flask-SocketIO Documentation: https://flask-socketio.readthedocs.io/

---

**Enjoy your upgraded Sampark Setu chat application!** 🎉

