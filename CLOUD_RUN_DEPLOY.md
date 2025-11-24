# ☁️ Google Cloud Run Deployment Guide

## 🚀 Deploy ARK Agent AGI to Production

### Prerequisites
- Google Cloud account (free tier works!)
- `gcloud` CLI installed
- Your `GOOGLE_API_KEY` from Google AI Studio

---

## Quick Deploy (10 Minutes)

### Step 1: Install Google Cloud SDK

**Windows:**
```powershell
# Download from: https://cloud.google.com/sdk/docs/install
# Or use choco:
choco install gcloudsdk
```

**Verify:**
```bash
gcloud --version
```

### Step 2: Login & Setup Project
```bash
# Login to Google Cloud
gcloud auth login

# Create new project (or use existing)
gcloud projects create ark-agent-agi --set-as-default

# Set project
gcloud config set project ark-agent-agi

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 3: Build & Deploy
```bash
cd c:\Users\jaisu\ark-agent-agi

# Build container
gcloud builds submit --tag gcr.io/ark-agent-agi/demo-api

# Deploy to Cloud Run
gcloud run deploy ark-agent-demo \
  --image gcr.io/ark-agent-agi/demo-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_api_key_here,GEMINI_MODEL=gemini-1.5-pro
```

### Step 4: Get Your URL
```bash
# Cloud Run will output a URL like:
# https://ark-agent-demo-xxxxx-uc.a.run.app
```

---

## 🔧 Using Dockerfile

We already have `infra/Dockerfile` ready!

### Quick Deploy with script:
```bash
# Make executable
chmod +x infra/deploy_cloudrun.sh

# Run deployment
./infra/deploy_cloudrun.sh
```

---

## 🌐 Update Extension for Production

After deploying, update `extension/popup.js`:

```javascript
// Change from:
const API_URL = "http://localhost:8000/api/v1/run";

// To your Cloud Run URL:
const API_URL = "https://ark-agent-demo-xxxxx-uc.a.run.app/api/v1/run";
```

Reload extension in Chrome!

---

## 💰 Cost Estimate

**Free Tier Includes:**
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

**Expected Cost:** $0-5/month for demos!

---

## 🔐 Security (Optional)

### Add Authentication:
```bash
# Deploy with auth required
gcloud run deploy ark-agent-demo \
  --no-allow-unauthenticated

# Create service account for extension
gcloud iam service-accounts create extension-user
```

---

## 📊 Monitoring

### View Logs:
```bash
gcloud run logs read ark-agent-demo --limit 50
```

### View Metrics:
```
https://console.cloud.google.com/run
```

---

## 🎥 Demo URLs for Video

After deployment, you'll have:

1. **Production API**: `https://your-app.run.app`
2. **Health Check**: `https://your-app.run.app/health`
3. **API Docs**: `https://your-app.run.app/docs`
4. **Chrome Extension**: Works with production URL!

---

## 🐛 Troubleshooting

**Build fails?**
```bash
# Check Docker is running
docker --version

# Test local build first
docker build -t ark-demo -f infra/Dockerfile .
docker run -p 8000:8000 ark-demo
```

**Deployment permission errors?**
```bash
# Enable billing (required even for free tier)
gcloud alpha billing accounts list
gcloud alpha billing projects link ark-agent-agi --billing-account=XXXXX
```

**Extension can't reach Cloud Run?**
- Make sure `--allow-unauthenticated` is set
- Check CORS is enabled in API
- Verify the URL in popup.js is correct

---

**Your app will be live globally in ~2 minutes! 🌍**
