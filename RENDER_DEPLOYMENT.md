# Deploying Sampark Setu on Render

This guide will help you deploy the Sampark Setu chat application on Render.

## Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Render account (sign up at https://render.com)

## Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub**
   - Make sure all files are committed and pushed to your repository

2. **Create a new Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configure Environment Variables**
   - Render will automatically set up:
     - `SECRET_KEY` (auto-generated)
     - `DATABASE_URL` (from the PostgreSQL database)
     - `PYTHON_VERSION` (3.11.0)
     - `RENDER` (set to `true`)
     - `ASYNC_MODE` (set to `eventlet`)
   - You can add additional environment variables if needed:
     - `GIPHY_API_KEY` (if you want to use Giphy for GIFs - get free key from https://developers.giphy.com/)

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - The first deployment may take 5-10 minutes

### Option 2: Manual Configuration

If you prefer to configure manually:

1. **Create a PostgreSQL Database**
   - Go to "New +" → "PostgreSQL"
   - Name it `sampark-setu-db`
   - Note the connection string

2. **Create a Web Service**
   - Go to "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `sampark-setu`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt && python init_db.py`
     - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - run:app`
     
     **Alternative**: You can also use `wsgi:app` if you prefer:
     - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - wsgi:app`
     - **Plan**: Free (or choose a paid plan)

3. **Set Environment Variables**
   - `SECRET_KEY`: Generate a random secret key
   - `DATABASE_URL`: Use the connection string from your PostgreSQL database
   - `PYTHON_VERSION`: `3.11.0`
   - `RENDER`: `true` (to enable production settings)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for the build to complete

## Post-Deployment

### File Storage

**Important**: Render's free tier has ephemeral file storage. Files uploaded to `/uploads` will be lost when the service restarts.

For production, consider:
1. **Upgrading to a paid plan** with persistent storage
2. **Using cloud storage** (AWS S3, Cloudinary, etc.) for file uploads
3. **Using Render Disk** (paid feature) for persistent storage

### GIF Search Feature

If you want to use the GIF search feature:
1. Get a free API key from Giphy: https://developers.giphy.com/
2. Add it as an environment variable: `GIPHY_API_KEY`
3. The app will automatically use it for GIF searches

### Database Initialization

The database is automatically initialized on first deployment. If you need to run migrations manually:
1. Use Render's Shell feature (if available)
2. Or SSH into your service
3. Run: `python init_db.py`

### Database Migrations

The build script automatically runs `init_db.py` which:
- Creates all database tables
- Runs necessary migrations (adds missing columns like `file_name`, `profile_picture`, `display_name`)

**Important**: The app also runs runtime migrations on startup as a safety net. This ensures that even if migrations fail during build, they will be applied when the app starts.

For future migrations:
1. Update your models in `app/models.py`
2. Add migration logic to `init_db.py`
3. The app will automatically apply migrations on startup
4. Or use Flask-Migrate (recommended for complex migrations)

### Custom Domain

1. Go to your service settings
2. Click "Add Custom Domain"
3. Follow the DNS configuration instructions

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | Auto-generated |
| `DATABASE_URL` | PostgreSQL connection string | Yes | Auto-set from database |
| `PYTHON_VERSION` | Python version | No | 3.11.0 |
| `RENDER` | Set to `true` on Render | No | - |
| `GIPHY_API_KEY` | Giphy API key for GIF search | No | - |
| `ASYNC_MODE` | SocketIO async mode | No | eventlet |

## Troubleshooting

### Build Fails

- Check the build logs for errors
- Ensure all dependencies are in `requirements.txt`
- Verify Python version matches `.runtime.txt`

### Database Connection Issues

- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL database is running
- Ensure connection string uses `postgresql://` not `postgres://`

### SocketIO Not Working

- Ensure `eventlet` is installed
- Check that `gunicorn` is using `--worker-class eventlet`
- Verify CORS settings allow your domain

### File Uploads Not Working

- Check `/uploads` directory exists
- Verify file permissions
- Consider using cloud storage for production

### "Failed to Load Messages" Error

If you see "Failed to load messages" on the deployed version:

1. **Check Database Migrations**:
   - The app should automatically run migrations on startup
   - Check the application logs for migration errors
   - Look for messages like "Runtime migration: Added file_name column"

2. **Verify Database Connection**:
   - Ensure `DATABASE_URL` is set correctly
   - Check that PostgreSQL database is running
   - Verify connection string format (`postgresql://` not `postgres://`)

3. **Check Application Logs**:
   - Go to Render dashboard → Your service → Logs
   - Look for database errors or migration failures
   - Common issues:
     - Missing columns (`file_name`, `profile_picture`, `display_name`)
     - Database connection timeouts
     - Permission errors

4. **Manual Migration** (if needed):
   - Use Render's Shell feature to connect to your service
   - Run: `python init_db.py`
   - This will ensure all migrations are applied

5. **Restart the Service**:
   - Sometimes a restart helps apply pending migrations
   - Go to Render dashboard → Your service → Manual Deploy → Clear build cache & deploy

## Support

For issues specific to Render, check:
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com

For application-specific issues, check the application logs in Render dashboard.

