# Deployment Guide - Railway.app

This guide will help you deploy your FastAPI dummy server to Railway.app with CI/CD using GitHub Actions.

## 🚀 Railway.app Deployment

### Prerequisites

1. **Railway.app Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Environment Variables**: Prepare your production secrets

### Step 1: Prepare Your Project

Your project is already configured with these deployment files:

- ✅ `railway.toml` - Railway configuration
- ✅ `Procfile` - Process configuration
- ✅ `main.py` - Updated for Railway environment variables
- ✅ `pyproject.toml` - UV dependencies

### Step 2: Create Railway Project

1. **Log in to Railway.app**
   ```bash
   # Install Railway CLI (optional)
   npm install -g @railway/cli
   railway login
   ```

2. **Create New Project**
   - Go to [railway.app/new](https://railway.app/new)
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect it as a Python app

3. **Configure Build Settings**
   Railway should automatically detect:
   - **Build Command**: `uv sync` (auto-detected)
   - **Start Command**: `python main.py` (from Procfile)
   - **Health Check**: `/health` (from railway.toml)

### Step 3: Set Environment Variables

In your Railway project dashboard, add these environment variables:

#### Required Variables:
```bash
# JWT Secret Key (generate a secure random string)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here

# Python Path (Railway auto-sets this usually)
PYTHONPATH=/app

# Port (Railway auto-sets this)
PORT=8000
```

#### Generate JWT Secret Key:
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Step 4: Deploy

1. **Automatic Deployment**
   - Railway will automatically deploy when you push to `main` branch
   - Check the deployment logs in Railway dashboard

2. **Manual Deployment**
   ```bash
   # Using Railway CLI
   railway up
   ```

### Step 5: Verify Deployment

1. **Get Your Railway URL**
   - Check Railway dashboard for your app's URL
   - Format: `https://your-app-name.up.railway.app`

2. **Test Endpoints**
   ```bash
   # Health check
   curl https://your-app-name.up.railway.app/health
   
   # API docs
   open https://your-app-name.up.railway.app/docs
   
   # Create session
   curl -X POST https://your-app-name.up.railway.app/api/auth/session
   ```

## 🔄 GitHub Actions CI/CD

### Setup GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

```bash
# Railway deployment
RAILWAY_TOKEN=your-railway-token
RAILWAY_SERVICE_ID=your-service-id
RAILWAY_URL=https://your-app-name.up.railway.app

# Application secrets  
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
```

#### Get Railway Token:
1. Go to Railway.app → Account Settings → Tokens
2. Create a new token
3. Copy and add to GitHub secrets

#### Get Service ID:
1. Go to your Railway project dashboard
2. Copy the service ID from the URL or settings

### GitHub Actions Workflows

Your repository now includes:

#### 1. **CI Workflow** (`.github/workflows/ci.yml`)
**Triggers**: Push to `main`/`develop`, Pull Requests to `main`

**Jobs**:
- ✅ **Test**: Run all pytest tests with UV
- ✅ **Build**: Validate imports and OpenAPI schema  
- ✅ **Security**: Check for hardcoded secrets
- ✅ **Performance**: Basic response time tests

#### 2. **Railway Auto-Deployment**
**Triggers**: Push to `main` branch (when GitHub is connected)

**Features**:
- ✅ **Zero-config deployment** - Railway handles everything
- ✅ **Automatic builds** with Nixpacks
- ✅ **Built-in health monitoring** 
- ✅ **Instant rollbacks** via Railway dashboard

### Workflow Status

Check your GitHub repository's "Actions" tab to see:
- ✅ Build status
- ✅ Test results  
- ✅ Deployment status
- ✅ Health check results

## 🔧 Configuration Details

### Railway Configuration (`railway.toml`)

```toml
[build]
builder = "nixpacks"  # Railway's build system

[deploy]
healthcheckPath = "/health"  # Health endpoint
healthcheckTimeout = 300     # 5 minute timeout
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[[services]]
name = "backend"

[services.variables]
PORT = "8000"           # Default port
PYTHONPATH = "/app"     # Python module path
```

### Production Optimizations

The app automatically detects Railway environment:

```python
# In main.py
is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None

uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=port,
    reload=not is_production,  # Disable reload in production
    log_level="info"
)
```

### Security Features

- ✅ **Environment Variables**: JWT secret from env vars
- ✅ **Production Mode**: Auto-detected Railway environment
- ✅ **Health Checks**: Built-in health monitoring
- ✅ **CORS**: Configured for production use
- ✅ **Error Handling**: Consistent error responses

## 🚨 Troubleshooting

### Common Issues:

#### 1. **Build Failures**
```bash
# Check Railway logs
railway logs

# Local testing
uv sync
uv run python main.py
```

#### 2. **Health Check Failures**
```bash
# Test health endpoint locally
curl http://localhost:8000/health

# Check Railway health check settings
```

#### 3. **Environment Variable Issues**
```bash
# Verify variables in Railway dashboard
# Ensure JWT_SECRET_KEY is set and secure
```

#### 4. **Import Errors**
```bash
# Verify PYTHONPATH is set correctly
# Check all dependencies are in pyproject.toml
```

### Health Check Endpoint

Your app includes a health endpoint for monitoring:

```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "message": "Dummy server is running"
}
```

## 📊 Monitoring

### Railway Dashboard
- **Deployments**: Track deployment history
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, network usage
- **Health**: Uptime monitoring

### GitHub Actions
- **Build Status**: Pass/fail for each commit
- **Test Results**: Detailed test output
- **Deployment Status**: Success/failure tracking

## 🔄 Development Workflow

1. **Development**
   ```bash
   # Local development
   uv run python main.py
   ```

2. **Testing**
   ```bash
   # Run tests locally
   uv run pytest tests/ -v
   ```

3. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin main
   ```

4. **Automatic Deployment**
   - GitHub Actions runs CI
   - If tests pass, deploys to Railway
   - Health check verifies deployment

## 🎯 Production Checklist

Before going live:

- ✅ **Secrets**: JWT_SECRET_KEY set securely
- ✅ **Environment**: Railway environment variables configured
- ✅ **Health Check**: `/health` endpoint responding
- ✅ **API Docs**: `/docs` accessible
- ✅ **Tests**: All tests passing in CI
- ✅ **Monitoring**: Railway dashboard set up
- ✅ **Domain**: Custom domain configured (optional)

## 🔗 Useful Links

- **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **GitHub Actions**: [docs.github.com/actions](https://docs.github.com/en/actions)
- **FastAPI Deployment**: [fastapi.tiangolo.com/deployment](https://fastapi.tiangolo.com/deployment/)

Your FastAPI dummy server is now production-ready and will automatically deploy to Railway.app with full CI/CD! 🚀