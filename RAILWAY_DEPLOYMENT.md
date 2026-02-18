# 🚀 Railway Deployment Guide

Railway par YouTube Downloader API deploy karne ka complete guide!

## 📋 Prerequisites

1. **GitHub Account** - Code upload karne ke liye
2. **Railway Account** - [railway.app](https://railway.app) par free signup karo

---

## 🔧 Step-by-Step Deployment

### Step 1: GitHub Repository Banao

1. GitHub par jao: https://github.com/new
2. Repository name: `youtube-downloader-api` (ya koi bhi naam)
3. **Public** ya **Private** select karo
4. "Create repository" click karo

### Step 2: Code Upload Karo

Terminal mein:

```bash
cd /path/to/your/project

# Git initialize karo
git init

# Files add karo
git add .

# Commit karo
git commit -m "Initial commit - YouTube Downloader API"

# GitHub repository connect karo (apna URL dalo)
git remote add origin https://github.com/YOUR_USERNAME/youtube-downloader-api.git

# Push karo
git branch -M main
git push -u origin main
```

**Required Files (sab included hain):**
- ✅ `ytdl_simple.py` - Main API
- ✅ `requirements.txt` - Dependencies
- ✅ `Procfile` - Railway startup command
- ✅ `railway.json` - Railway configuration
- ✅ `runtime.txt` - Python version
- ✅ `.gitignore` - Ignore files

### Step 3: Railway Par Deploy Karo

1. **Railway par jao**: https://railway.app
2. "Login with GitHub" click karo
3. "New Project" button click karo
4. "Deploy from GitHub repo" select karo
5. Apni repository select karo: `youtube-downloader-api`
6. Railway automatically detect kar lega aur deploy karega! 🎉

### Step 4: Domain URL Get Karo

Deploy hone ke baad:

1. Project dashboard par jao
2. "Settings" tab click karo
3. "Networking" section mein jao
4. "Generate Domain" button click karo
5. Tumhe ek URL milega: `https://your-project.up.railway.app`

---

## 🌐 API URLs (Live)

Tumhara deployed API:
```
https://your-project.up.railway.app
```

**Examples:**

Check qualities:
```
https://your-project.up.railway.app/dl?url=https://youtu.be/VIDEO_ID
```

Download 720p:
```
https://your-project.up.railway.app/dl?url=https://youtu.be/VIDEO_ID&q=720p
```

---

## ⚙️ Important Notes

### 1. **Railway Free Tier Limits**
- ✅ 500 hours/month execution time
- ✅ $5 free credit monthly
- ⚠️ Projects sleep after inactivity (10 mins)
- 💡 First request wake karta hai (~30 seconds)

### 2. **Storage Warning**
Railway par files temporary hain. Har deployment par downloads folder reset ho jayega. Ye sirf temporary downloads ke liye hai.

### 3. **Timeout Settings**
Large videos (>100MB) download hone mein time lagta hai. Maine timeout 300 seconds (5 minutes) set kiya hai Procfile mein.

### 4. **Environment Variables** (Optional)
Agar kuch secrets add karne hain:
1. Railway dashboard → "Variables" tab
2. Key-Value pairs add karo
3. Code mein `os.environ.get('KEY')` se access karo

---

## 🔄 Update Code (Future mein)

Code change karne ke baad:

```bash
git add .
git commit -m "Updated features"
git push
```

Railway automatically redeploy kar dega! ✨

---

## 📊 Monitor Your API

Railway Dashboard mein:
- **Logs** - Real-time logs dekho
- **Metrics** - CPU/Memory usage
- **Deployments** - History dekho

---

## 🐛 Troubleshooting

### Problem: "Application failed to respond"
**Solution:** 
- Logs check karo Railway dashboard mein
- `railway.json` file present hai confirm karo
- Port `$PORT` environment variable use kar raha hai confirm karo

### Problem: Video download slow hai
**Solution:**
- Railway free tier slow ho sakta hai
- Smaller quality select karo (480p, 360p)
- Direct YouTube URLs use karo (response mein milte hain)

### Problem: App sleeping hai
**Solution:**
- Free tier par apps sleep hote hain
- Paid plan upgrade karo ($5/month)
- Ya keep-alive service use karo (like UptimeRobot)

---

## 💰 Pricing

**Free Tier:**
- $5 credit/month
- 500 execution hours
- Perfect for personal use!

**Hobby Plan:** $5/month
- More resources
- No sleep
- Better for public APIs

---

## 🎉 Done!

Ab tumhara YouTube Downloader API live hai!

Share karo:
```
https://your-project.up.railway.app
```

Happy Downloading! 🚀
