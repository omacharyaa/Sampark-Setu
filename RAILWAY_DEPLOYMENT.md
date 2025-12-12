# Deploying Sampark Setu on Railway

This guide will help you deploy the Sampark Setu chat application on Railway.

## Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Railway account (sign up at https://railway.app)

## Deployment Steps

### Option 1: Quick Deploy (Recommended)

1. **Push your code to GitHub**
   - Make sure all files are committed and pushed to your repository

2. **Create a new project on Railway**
   - Go to https://railway.app
   - Sign up or log in
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add a PostgreSQL Database**
   - In your Railway project, click "New"
   - Select "Database" → "Add PostgreSQL"
   - Railway will automatically create a PostgreSQL database
   - The `DATABASE_URL` environment variable will be automatically set

4. **Configure Environment Variables**
   - Go to your service settings → Variables
   - Add the following environment variables:
     - `SECRET_KEY`: Generate a random secret key (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)
     - `RAILWAY`: `true` (to enable production settings)
     - `ASYNC_MODE`: `eventlet` (for SocketIO support)
     - `PYTHON_VERSION`: `3.11.0` (optional, Railway auto-detects)

5. **Deploy**
   - Railway will automatically detect your `Procfile` or `railway.json`
   - The first deployment may take 5-10 minutes
   - Railway will automatically build and deploy your application

### Option 2: Using Railway CLI

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize and deploy**
   ```bash
   railway init
   railway up
   ```

4. **Add PostgreSQL database**
   ```bash
   railway add postgresql
   ```

5. **Set environment variables**
   ```bash
   railway variables set SECRET_KEY=your-secret-key-here
   railway variables set RAILWAY=true
   railway variables set ASYNC_MODE=eventlet
   ```

## Configuration Files

### Procfile
Railway automatically detects and uses the `Procfile`:
```
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - wsgi:app
```

### railway.json (Optional)
If you prefer explicit configuration, Railway will use `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python init_db.py"
  },
  "deploy": {
    "startCommand": "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - wsgi:app"
  }
}
```

## Post-Deployment

### File Storage

**Important**: Railway's free tier has ephemeral file storage. Files uploaded to `/uploads` will be lost when the service restarts.

For production, consider:
1. **Using Railway Volumes** (paid feature) for persistent storage
2. **Using cloud storage** (AWS S3, Cloudinary, etc.) for file uploads
3. **Upgrading to a paid plan** with persistent storage

### Database Initialization

The database is automatically initialized on first deployment via the build command. If you need to run migrations manually:
1. Use Railway's CLI: `railway run python init_db.py`
2. Or use Railway's web console → Service → Deployments → Run Command

### Custom Domain

1. Go to your service settings
2. Click "Generate Domain" or "Custom Domain"
3. Follow the DNS configuration instructions

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | Must be set |
| `DATABASE_URL` | PostgreSQL connection string | Yes | Auto-set from Railway PostgreSQL |
| `RAILWAY` | Set to `true` on Railway | No | - |
| `RAILWAY_ENVIRONMENT` | Railway environment name | No | Auto-set by Railway |
| `PYTHON_VERSION` | Python version | No | Auto-detected |
| `GIPHY_API_KEY` | Giphy API key for GIF search | No | - |
| `ASYNC_MODE` | SocketIO async mode | No | eventlet |
| `PORT` | Port to bind to | No | Auto-set by Railway |

## Troubleshooting

### Build Fails

- Check the build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version matches `.runtime.txt` (3.11.0)

### Database Connection Issues

- Verify `DATABASE_URL` is set correctly (Railway sets this automatically)
- Check PostgreSQL database is running
- Ensure connection string uses `postgresql://` not `postgres://`
- The app automatically converts `postgres://` to `postgresql://`

### SocketIO Not Working

- Ensure `eventlet` is installed (it's in requirements.txt)
- Check that `gunicorn` is using `--worker-class eventlet`
- Verify `ASYNC_MODE` is set to `eventlet`
- Check CORS settings allow your domain

### Application Not Accessible

- Ensure your app binds to `0.0.0.0:$PORT` (Railway provides PORT)
- Check Railway service logs for errors
- Verify the service is deployed and running (green status)

### File Uploads Not Working

- Check `/uploads` directory exists (created automatically)
- Verify file permissions
- Consider using cloud storage for production (files are ephemeral on free tier)

### Port Binding Issues

- Railway automatically sets the `$PORT` environment variable
- Make sure your Gunicorn command uses `$PORT` not a hardcoded port
- The Procfile already uses `$PORT` correctly

## Railway vs Render Differences

| Feature | Railway | Render |
|---------|---------|--------|
| Configuration | `Procfile` or `railway.json` | `render.yaml` or `Procfile` |
| Database | Auto-creates PostgreSQL | Auto-creates PostgreSQL |
| Environment Detection | `RAILWAY_ENVIRONMENT` or `RAILWAY` | `RENDER` |
| Build Command | In `railway.json` or auto-detected | In `render.yaml` |
| Start Command | In `Procfile` or `railway.json` | In `Procfile` or `render.yaml` |

## Support

For issues specific to Railway:
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

For application-specific issues, check the application logs in Railway dashboard.

## Quick Commands

```bash
# View logs
railway logs

# Run a command
railway run python init_db.py

# Open service
railway open

# Check status
railway status
```
