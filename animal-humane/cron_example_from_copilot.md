```
#!/bin/bash

# Set paths for your repo and your generated data location
REPO_DIR="$HOME/path/to/your/repo"                 # <-- update this!
GENERATED_DATA_DIR="$HOME/path/to/generated/data"  # <-- update this!

# Copy new JSON files into the repo (public/data is an example, adjust as needed)
cp ${GENERATED_DATA_DIR}/*.json ${REPO_DIR}/public/data/

# Change to your repo directory
cd "$REPO_DIR"

# Add/commit/push any changes to JSON files
git add public/data/*.json
git diff --cached --quiet # checks if there are staged changes
if [ $? -eq 1 ]; then
  git commit -m "Auto-update dashboard data ($(date '+%Y-%m-%d %H:%M'))"
  git push origin main     # or your Vercel deploy branch
else
  echo "No changes to commit. Skipping push."
fi
```

Instructions:

* Update $REPO_DIR to the local path of your repo cloned on your laptop.
* Update $GENERATED_DATA_DIR to the folder where your analysis script outputs its JSON files.
* Adjust public/data/ to match wherever your Vercel frontend expects to find the data (could be just public/, etc).
* Add this script as your cron job, or call it after your analysis step in your automation chain.

How to schedule this with cron (example for every 4 hours):

```
0 */4 * * * /path/to/this-script.sh >> /tmp/dashboard-cron.log 2>&1
```

What this does:

* Copies freshly generated JSON files into your repo
* Commits and pushes only if there are changes
* Your Vercel deployment auto-triggers. Site stays up to date
