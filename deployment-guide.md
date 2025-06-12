# GitHub Deployment Guide for Enhanced ORA

## Step 1: Prepare for GitHub

1. **Create a new repository** on your GitHub account
2. **Push your code** to the repository:

```bash
git init
git add .
git commit -m "Initial commit: Enhanced ORA Therapeutic AI"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo-name.git
git push -u origin main
```

## Step 2: Choose a Hosting Platform

### Option A: Render (Recommended)
- Free tier available
- Automatic deployments from GitHub
- Good for Python apps
- Built-in database support

### Option B: Railway
- Simple deployment process
- Good free tier
- Automatic GitHub integration

### Option C: Heroku
- Popular choice
- Easy deployment
- Paid plans only now

## Step 3: Deploy on Render

1. **Go to [render.com](https://render.com)**
2. **Connect your GitHub account**
3. **Create a new Web Service**
4. **Select your repository**
5. **Configure deployment settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn enhanced_app:app`
   - **Environment**: Python 3
   - **Instance Type**: Free

6. **Add Environment Variables**:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PYTHON_VERSION=3.9.16
   ```

7. **Deploy**

## Step 4: Deploy on Railway (Alternative)

1. **Go to [railway.app](https://railway.app)**
2. **Connect GitHub**
3. **Deploy from repo**
4. **Add environment variables**
5. **Railway will auto-detect Python and deploy**

## Step 5: Environment Variables Needed

```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=production
```

## Step 6: Verify Deployment

After deployment, test these endpoints:
- `GET /` - Main interface
- `GET /health` - Health check
- `POST /classify` - Emotion classification
- `GET /enhanced_admin.html` - Admin panel

## Troubleshooting

### Common Issues:
1. **Build fails**: Check requirements.txt for version conflicts
2. **App won't start**: Verify gunicorn command
3. **Database errors**: Ensure SQLite file permissions
4. **Memory issues**: Some dependencies are large, may need paid tier

### Solutions:
- Use `gunicorn enhanced_app:app --bind 0.0.0.0:$PORT`
- Ensure all imports are available
- Check logs for specific errors

## File Structure for Deployment

Your repository should have:
```
/
├── enhanced_app.py          # Main application
├── app.py                   # Original app (backup)
├── requirements.txt         # Dependencies
├── runtime.txt             # Python version (optional)
├── Procfile                # For Heroku (optional)
├── render.yaml             # For Render (optional)
├── memory-api/             # Memory system
├── static/                 # Frontend files
├── templates/              # HTML templates
└── README.md               # Documentation
```

## Optional: Add Procfile for Heroku

```
web: gunicorn enhanced_app:app
```

## Optional: Add runtime.txt

```
python-3.9.16
```