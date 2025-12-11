# Quick Deployment Guide for Render

## 🚀 Deploy to Render in 5 Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Sign up or log in

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

4. **Wait for Deployment**
   - First build takes 5-10 minutes
   - Render will automatically:
     - Create PostgreSQL database
     - Set environment variables
     - Build and deploy your app

5. **Access Your App**
   - Your app will be live at: `https://sampark-setu.onrender.com`
   - (URL will be different based on your service name)

## 📝 Important Notes

### File Storage
- **Free tier**: Files are lost on restart (ephemeral storage)
- **Solution**: Use cloud storage (S3, Cloudinary) for production

### Database
- PostgreSQL is automatically created
- Tables are auto-initialized on first deployment
- Migrations run automatically via `init_db.py`

### Environment Variables
- `SECRET_KEY`: Auto-generated
- `DATABASE_URL`: Auto-set from database
- `GIPHY_API_KEY`: Optional (get from https://developers.giphy.com/)

## 🔧 Manual Configuration (if needed)

If `render.yaml` doesn't work:

**Build Command:**
```
pip install -r requirements.txt && python init_db.py
```

**Start Command:**
```
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 run:app
```

**Environment Variables:**
- `SECRET_KEY`: Generate random string
- `DATABASE_URL`: From PostgreSQL service
- `RENDER`: `true`
- `ASYNC_MODE`: `eventlet`

## 📚 Full Documentation

See `RENDER_DEPLOYMENT.md` for detailed instructions.

