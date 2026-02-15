# Push Cosmic SafeCLI to GitHub

Follow these steps to put your project on GitHub for the **GitHub Copilot CLI Challenge**.

---

## 1. Install Git (if needed)

- **Windows:** [Download Git for Windows](https://git-scm.com/download/win) and run the installer. Restart your terminal/IDE after installing.
- **macOS:** `brew install git` or install from [git-scm.com](https://git-scm.com/download/mac).
- **Linux:** `sudo apt install git` (Ubuntu/Debian) or your distro’s package manager.

Check: run `git --version` in a terminal.

---

## 2. Create a new repository on GitHub

1. Go to [github.com/new](https://github.com/new).
2. **Repository name:** `Cosmic-SafeCli` (must match for the clone/push URLs below).
3. **Description:** `CLI that explains shell commands and uses GitHub Copilot CLI to suggest safer alternatives. GitHub Copilot CLI Challenge.`
4. Choose **Public**.
5. **Do not** add a README, .gitignore, or license (this repo already has them).
6. Click **Create repository**.

---

## 3. Initialize Git and push from your machine

Open a terminal in the project folder (e.g. `c:\cosmic` or `~/cosmic`) and run:

```bash
# Initialize repo
git init

# Add all files (respects .gitignore)
git add .

# First commit
git commit -m "Initial commit: Cosmic SafeCLI for GitHub Copilot CLI Challenge"

# Rename branch to main (if needed)
git branch -M main

# Add your GitHub repo as remote
git remote add origin https://github.com/ANUJ-codes07/Cosmic-SafeCli.git

# Push to GitHub
git push -u origin main
```

**Example** for this repo:

```bash
git remote add origin https://github.com/ANUJ-codes07/Cosmic-SafeCli.git
git push -u origin main
```

If GitHub asks for credentials, use a **Personal Access Token** (Settings → Developer settings → Personal access tokens) as the password, or sign in with **GitHub CLI** (`gh auth login`) and use HTTPS/SSH as you prefer.

---

## 4. Update the README clone URL (optional)

The README clone URL is already set to:

```bash
git clone https://github.com/ANUJ-codes07/Cosmic-SafeCli.git
```

---

## 5. Submit to the challenge

1. Publish your submission post on DEV using the draft in [SUBMISSION.md](SUBMISSION.md).
2. In the post, add the link to this GitHub repo.
3. Submit the post on the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21) page.

Submissions are due **February 15, 2026, 11:59 PM PST**.
