#!/bin/bash
# Setup Git for Trading Encyclopedia
# Run once before first git_sync.py

cd ~/encyclopedia

echo "Setting up Git..."
git init 2>/dev/null || true
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/sinamoosazadeh/trading-encyclopedia.git
git config user.email "sinamoosazadeh@github.com"
git config user.name "Sina Moosazadeh"

# Create .gitignore
cat > .gitignore << EOF
data/
__pycache__/
*.pyc
*.tmp
run.log
preflight_report.json
EOF

echo "Git configured."
echo ""
echo "Next time you push, enter your GitHub token as password."
echo "Repo: https://github.com/sinamoosazadeh/trading-encyclopedia"
