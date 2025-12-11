# Quick Start Guide - Sampark Setu

## 🚀 Run the Application (3 Easy Steps)

### Method 1: Using start.bat (Windows - Easiest)

1. Double-click `start.bat`
2. Wait for the server to start
3. Open your browser to `http://localhost:5000`

### Method 2: Using run_local.py (Cross-platform)

1. Open terminal/command prompt
2. Run: `python run_local.py`
3. Follow the prompts
4. Open your browser to `http://localhost:5000`

### Method 3: Manual Start

1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Initialize database (first time only):**
   ```bash
   python init_db.py
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

4. **Open browser:**
   - Go to: `http://localhost:5000`

## ✅ First Time Setup

If you haven't set up the project yet:

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate it:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database:**
   ```bash
   python init_db.py
   ```

5. **Run the app:**
   ```bash
   python run.py
   ```

## 🎯 What to Do Next

1. **Register**: Create a new account
2. **Create Room**: Click "Create Room" to make a chat room
3. **Join Room**: Enter a room ID to join an existing room
4. **Chat**: Start sending messages!

## ⚠️ Troubleshooting

### Port 5000 already in use
- Change port in `run.py` (line 15): `port = int(os.environ.get('PORT', 5001))`

### Database errors
- Run: `python init_db.py`

### Module not found errors
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### Messages stuck loading
- Check browser console (F12) for errors
- Check server terminal for errors
- Try refreshing the page

## 📝 Notes

- The app runs on `http://localhost:5000` by default
- Database file: `instance/sampark_setu.db` (SQLite)
- Uploads are stored in `uploads/` folder
- Press `Ctrl+C` to stop the server

## 🆘 Need Help?

Check the full `README.md` for detailed documentation.
