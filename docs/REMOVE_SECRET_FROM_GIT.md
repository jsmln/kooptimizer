# Removing Service Account Credentials from Git History

## ⚠️ CRITICAL: Your credentials are exposed in commit `03d99d1`

The file `service_account.json` contains sensitive Google Cloud credentials and has been committed to your repository. You need to:

1. **Remove it from git history** (steps below)
2. **Rotate/regenerate your credentials** in Google Cloud Console (IMPORTANT!)
3. **Force push** to update the remote repository

---

## Step 1: Remove from Git History

Since the file is in commit `03d99d1`, you have two options:

### Option A: Using git filter-branch (Built-in, slower)

```bash
# Remove the file from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch service_account.json" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up backup refs
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
```

### Option B: Using git filter-repo (Recommended, faster - needs installation)

```bash
# Install git-filter-repo first (if not installed)
# pip install git-filter-repo

# Remove the file from history
git filter-repo --path service_account.json --invert-paths --force
```

### Option C: Interactive Rebase (If it's only in recent commits)

```bash
# If the file was only added in recent commits, you can use interactive rebase
git rebase -i 7977da1  # Rebase from before the commit with the secret

# In the editor, change 'pick' to 'edit' for commit 03d99d1
# Then when it stops:
git rm --cached service_account.json
git commit --amend --no-edit
git rebase --continue
```

---

## Step 2: Force Push (⚠️ WARNING)

After removing from history, you MUST force push:

```bash
# Force push to update remote (this rewrites history)
git push origin final-dev1 --force
```

**⚠️ WARNING:** Force pushing rewrites history. If others are working on this branch, coordinate with them first!

---

## Step 3: Rotate Your Credentials (CRITICAL!)

**The credentials in the commit are now exposed. You MUST:**

1. Go to Google Cloud Console
2. Navigate to IAM & Admin > Service Accounts
3. Find the service account with email from the JSON file
4. **Delete the old key** or **Disable the service account**
5. **Create a new service account** or **generate a new key**
6. Update your local `service_account.json` with the new credentials

---

## Step 4: Verify Removal

After force pushing, verify the file is gone:

```bash
# Check that file is no longer in history
git log --all --full-history -- service_account.json

# Should return nothing if successfully removed
```

---

## Current Status

✅ File removed from git tracking (`git rm --cached`)
✅ Added to `.gitignore` (won't be committed again)
✅ Template file created (`service_account.json.template`)

⏳ **Still need to:**
- Remove from commit history (choose one option above)
- Force push to remote
- Rotate credentials in Google Cloud

---

## Prevention for Future

1. **Never commit credentials** - Always use `.gitignore`
2. **Use environment variables** for sensitive data
3. **Use secret management** services (Google Secret Manager, AWS Secrets Manager, etc.)
4. **Use pre-commit hooks** to scan for secrets before committing

---

## Quick Command Summary

```bash
# 1. Remove from history (choose one method above)
# 2. Force push
git push origin final-dev1 --force

# 3. Verify
git log --all --full-history -- service_account.json
```

