# Publish this marketplace

This folder is the complete public repo. First publish (you do this — needs your GitHub account):

1. Create a new PUBLIC repo at https://github.com/ZehnEinsDigital/skube (empty, no README).
2. From this folder:
   ```
   git init -b main && git add . && git commit -m "Skube plugin marketplace"
   git remote add origin https://github.com/ZehnEinsDigital/skube.git
   git push -u origin main
   ```

Re-publish after any change (the build preserves this folder's .git and bases a fresh
release branch on origin/main — the marketplace only re-ingests via PR + squash-merge,
a direct push to main does NOT ship):
   ```
   ../../build-plugin-release.sh ZehnEinsDigital/skube
   git add -A && git commit -m "skube <version>"
   git push -fu origin <the release-v… branch the build printed>
   gh pr create --fill --repo ZehnEinsDigital/skube
   gh pr merge <that branch> --squash --delete-branch --repo ZehnEinsDigital/skube
   ```

Users install with:
   ```
   /plugin marketplace add ZehnEinsDigital/skube
   /plugin install skube@skube
   ```
