#!/bin/bash
exec >> /home/aarish/news_app/anacron.log 2>&1
echo "=== News update run at $(date) ==="

cd /home/aarish/news_app || { echo "cd failed"; exit 1; }


# Run the updater
python3 update_news.py

# Commit & push only if news.json changed
git add news.json

if git diff --cached --quiet; then
  echo "No changes in news.json"
else
  git commit -m "Daily news update - $(date + %F)"
  git push origin main
fi
