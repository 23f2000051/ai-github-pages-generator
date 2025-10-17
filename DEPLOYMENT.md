# 🚀 Deployment Guide

## Step-by-Step: Push to GitHub

### **Step 1: Initialize Git Repository**

Open PowerShell in your project directory and run:

```powershell
cd C:\Users\Asus\Documents\tds\Project1

# Initialize git repository
git init

# Check status to see what files will be committed
git status
```

### **Step 2: Verify .gitignore is Working**

Make sure sensitive files are ignored:

```powershell
# Check that .env is NOT in the list
git status

# If .env shows up, make sure .gitignore contains .env
cat .gitignore
```

**✅ Expected:** You should NOT see `.env` in the list (it's gitignored)

### **Step 3: Stage Files for Commit**

```powershell
# Add all files except those in .gitignore
git add .

# Verify what's staged
git status
```

**✅ Expected output:**
```
Changes to be committed:
  new file:   .env.example
  new file:   .gitignore
  new file:   README.md
  new file:   requirements.txt
  new file:   app/app.py
  new file:   app/config.py
  ...
```

**⚠️ Make sure `.env` is NOT in this list!**

### **Step 4: Create Initial Commit**

```powershell
git commit -m "Initial commit: AI-powered GitHub Pages generator"
```

### **Step 5: Create GitHub Repository**

**Option A: Using GitHub Web UI** (Recommended)

1. Go to: https://github.com/new
2. **Repository name:** `ai-github-pages-generator` (or your preferred name)
3. **Description:** `Automated web app generator using LLM and GitHub Pages`
4. **Visibility:** Public (or Private if you prefer)
5. **⚠️ Do NOT initialize with README, .gitignore, or license** (we already have these)
6. Click **"Create repository"**

**Option B: Using GitHub CLI** (if installed)

```powershell
gh repo create ai-github-pages-generator --public --source=. --remote=origin
```

### **Step 6: Link Local Repo to GitHub**

Copy the commands from GitHub's "push an existing repository" section, or run:

```powershell
# Replace YOUR-USERNAME with your GitHub username
git remote add origin https://github.com/YOUR-USERNAME/ai-github-pages-generator.git

# Verify remote is added
git remote -v
```

**✅ Expected output:**
```
origin  https://github.com/YOUR-USERNAME/ai-github-pages-generator.git (fetch)
origin  https://github.com/YOUR-USERNAME/ai-github-pages-generator.git (push)
```

### **Step 7: Push to GitHub**

```powershell
# Create main branch and push
git branch -M main
git push -u origin main
```

**✅ Success!** Your code is now on GitHub! 🎉

Visit: `https://github.com/YOUR-USERNAME/ai-github-pages-generator`

---

## 🚀 Deploy Your API Server

Now let's deploy the actual FastAPI application so instructors can POST to it.

### **Deployment Options:**

#### **Option 1: Render.com (Free & Easy)** ⭐ Recommended

1. **Create account**: https://render.com/
2. **New Web Service**: Click "New +" → "Web Service"
3. **Connect GitHub**: Authorize Render to access your repo
4. **Configure:**
   - **Name:** `ai-pages-generator`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd app && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. **Environment Variables**: Add these in Render dashboard
   ```
   GITHUB_USER=your-username
   GITHUB_TOKEN=ghp_...
   AIPIPE_API_KEY=eyJ...
   AIPIPE_MODEL=gpt-4o
   API_SECRET=your-secret
   SKIP_GITHUB=0
   SKIP_LLM=0
   DEFAULT_REPO_PRIVATE=0
   ```
6. **Deploy**: Click "Create Web Service"

**Your API will be live at:** `https://ai-pages-generator.onrender.com`

---

#### **Option 2: Railway.app (Free Tier Available)**

1. **Create account**: https://railway.app/
2. **New Project**: Click "New Project" → "Deploy from GitHub"
3. **Select repo**: Choose your GitHub repository
4. **Settings:**
   - **Start Command:** `cd app && uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **Variables**: Add environment variables (same as above)
6. **Deploy**: Railway auto-deploys

**Your API will be live at:** Generated Railway URL

---

#### **Option 3: Fly.io (Free Tier)**

```powershell
# Install flyctl
irm https://fly.io/install.ps1 | iex

# Login
flyctl auth login

# Create app
flyctl launch

# Set secrets
flyctl secrets set GITHUB_TOKEN=ghp_...
flyctl secrets set AIPIPE_API_KEY=eyJ...
flyctl secrets set GITHUB_USER=your-username
flyctl secrets set API_SECRET=your-secret
flyctl secrets set AIPIPE_MODEL=gpt-4o

# Deploy
flyctl deploy
```

---

#### **Option 4: Local Development (Testing Only)**

For local testing (NOT for instructor submission):

```powershell
cd app
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**⚠️ Problem:** Your PC needs to be online 24/7 and accessible from internet

**Solution:** Use ngrok for temporary public URL:
```powershell
# Install ngrok: https://ngrok.com/download
ngrok http 8000
```

---

## ✅ Verify Deployment

### **Test Your Deployed API**

```powershell
# Replace with your deployed URL
$apiUrl = "https://ai-pages-generator.onrender.com/handle_task"

# Test payload
$payload = @{
    email = "test@example.com"
    secret = "your-secret"
    task = "hello-world"
    round = 1
    nonce = "test-001"
    brief = "Create a simple hello world page"
    checks = @("Repo has MIT license")
    evaluation_url = "https://webhook.site/your-unique-url"
    attachments = @()
} | ConvertTo-Json

# Send POST request
Invoke-RestMethod -Uri $apiUrl -Method POST -Body $payload -ContentType "application/json"
```

**✅ Expected Response:**
```json
{
  "status": "accepted",
  "email": "test@example.com",
  "task": "hello-world",
  "round": 1,
  "nonce": "test-001"
}
```

---

## 📝 Submit to Instructor

Once deployed, submit to your instructor's Google Form:

1. **API URL:** `https://ai-pages-generator.onrender.com/handle_task`
2. **Secret:** `your-secret` (from `.env`)
3. **GitHub Repo:** `https://github.com/YOUR-USERNAME/ai-github-pages-generator`

---

## 🔧 Troubleshooting

### **"Module not found" errors**

```powershell
# Regenerate requirements.txt with exact versions
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements.txt"
git push
```

### **Environment variables not working**

- Make sure you added them in your deployment platform dashboard
- **Do NOT** commit `.env` file to GitHub
- Use `.env.example` as reference

### **GitHub API errors (403, 401)**

- Check your `GITHUB_TOKEN` is valid
- Generate new token: https://github.com/settings/tokens/new
- Required scopes: `repo`, `workflow`

### **Deployment keeps failing**

Check logs:
- **Render:** Dashboard → Logs tab
- **Railway:** Dashboard → Deployments → View logs
- **Fly.io:** `flyctl logs`

---

## 🎯 Next Steps

1. ✅ Push code to GitHub
2. ✅ Deploy to Render/Railway/Fly.io
3. ✅ Add environment variables
4. ✅ Test with sample payload
5. ✅ Submit API URL to instructor
6. ✅ Wait for evaluation tasks! 🚀

---

**Good luck with your submission! 🎉**
