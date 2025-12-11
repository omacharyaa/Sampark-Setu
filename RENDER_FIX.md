# Fix for Render Deployment Error

## Problem
Error: `gunicorn.errors.AppImportError: Failed to find attribute 'app' in 'app'`

This happens when Render tries to use `gunicorn app:app` instead of `gunicorn run:app`.

## Solution

### Option 1: Check Render Dashboard Settings (Recommended)

1. Go to your Render dashboard
2. Click on your web service
3. Go to **Settings** tab
4. Scroll to **Start Command**
5. Make sure it says:
   ```
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - run:app
   ```
6. If it says `app:app`, change it to `run:app`
7. Save and redeploy

### Option 2: Use wsgi.py (Alternative)

If you prefer, you can use the `wsgi.py` file:

1. In Render dashboard, set Start Command to:
   ```
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - wsgi:app
   ```

### Option 3: Verify render.yaml is Being Used

1. Make sure `render.yaml` is in the root of your repository
2. When creating a new service, Render should auto-detect it
3. If you created the service manually, you may need to:
   - Delete and recreate the service, OR
   - Manually set the start command as in Option 1

## Why This Happens

- Render sometimes auto-detects the start command incorrectly
- Manual service creation doesn't always use `render.yaml`
- The `render.yaml` file might not be in the root directory

## Verification

After fixing, the logs should show:
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:XXXX
[INFO] Using worker: eventlet
```

Instead of the import error.

