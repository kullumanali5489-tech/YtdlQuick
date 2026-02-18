#!/bin/bash

echo "🚀 Railway Deployment Setup"
echo "=============================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git not installed. Install it first:"
    echo "   pkg install git  (for Termux)"
    exit 1
fi

echo "📝 Enter your GitHub username:"
read username

echo ""
echo "📝 Enter repository name (e.g., youtube-downloader-api):"
read repo_name

echo ""
echo "🔧 Setting up Git..."

# Initialize git if not already
if [ ! -d .git ]; then
    git init
    echo "✅ Git initialized"
fi

# Add all files
git add .
echo "✅ Files staged"

# Commit
git commit -m "Initial commit - YouTube Downloader API"
echo "✅ Changes committed"

# Add remote
git remote add origin "https://github.com/$username/$repo_name.git" 2>/dev/null || \
git remote set-url origin "https://github.com/$username/$repo_name.git"
echo "✅ Remote added"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "=============================="
echo "✅ Code pushed to GitHub!"
echo ""
echo "📌 Next Steps:"
echo "1. Go to https://railway.app"
echo "2. Login with GitHub"
echo "3. Create New Project"
echo "4. Deploy from GitHub repo: $repo_name"
echo "5. Generate domain in Settings"
echo ""
echo "🎉 Done!"
