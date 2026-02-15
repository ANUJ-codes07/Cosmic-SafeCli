# Cosmic SafeCLI

> **Submission for the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21)**  
> *Understand before you execute.*

A command-line security assistant that explains shell commands in plain English, warns about dangerous operations, and uses **GitHub Copilot CLI** to suggest safer alternatives.

---

## 🏆 Challenge Submission

| | |
|---|---|
| **Challenge** | [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21) (DEV × GitHub) |
| **Category** | Productivity / Security CLI |
| **Judging** | Originality & Creativity · Usability & UX · **Use of GitHub Copilot CLI** |
| **Key dates** | Submissions due Feb 15, 2026 · Winners announced Feb 26, 2026 |

### How This Project Uses GitHub Copilot CLI

- **Core feature, not just tooling:** When a dangerous command is detected (e.g. `rm -rf`, `git reset --hard`), Cosmic SafeCLI calls **GitHub Copilot CLI** with a safety-focused prompt and displays the AI-suggested safer alternative in a formatted box. The user can then run that suggestion or skip.
- **Robust Fallback:** If Copilot CLI fails (quota exceeded, network issue), the tool automatically switches to **Google Gemini API** (if configured via `.env`) or falls back to **safe local rules** (e.g., suggesting `rm -ri` instead of `rm -rf`).
- **Graceful fallback:** If Copilot CLI is not installed, the app still explains commands and shows danger warnings; only the “safer suggestion” step is skipped.
- **Dual runtime:** Same behavior in **Python** (`safe.py`) and **Node.js** (`cosmic-safecli.js`) so judges can run it with either stack.

---

## Table of Contents

- [Demo](#demo)
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation & Usage](#installation--usage)
- [Examples](#examples)
- [Project Structure](#project-structure)
- [License](#license)

---

## Demo

**Quick demo (30 seconds)**

Run from the project root (the folder containing `safe.py`). The demo uses a **nonexistent path** so nothing in your project gets deleted.

Python:

```bash
python safe.py "rm -rf /nonexistent/cosmic-demo-safe"
```

Node.js:

```bash
npm start
# or: node cosmic-safecli.js "rm -rf /nonexistent/cosmic-demo-safe"
```

You’ll see: **COMMAND** box → **WARNING** box → **🔍 Command Breakdown** → **🤖 Copilot Safer Suggestion** (if Copilot CLI is installed).

Full walkthrough and more examples: [DEMO.md](DEMO.md)

---

## Overview

Cosmic SafeCLI reduces the risk of accidental destructive commands by:

1. **Explaining** each part of a command (tokens, flags, arguments) in plain language.
2. **Detecting** known dangerous patterns and explaining why they are risky.
3. **Suggesting** safer alternatives via **GitHub Copilot CLI** when danger is detected, with an option to run the suggestion or skip.

The tool is available in **Python** and **Node.js**; behavior is identical across both runtimes.

---

## Features

| Feature | Description |
|--------|-------------|
| **Token breakdown** | Splits the command using shell quoting rules and explains each token via a JSON dictionary (`commands.json`). |
| **Danger detection** | Matches against configurable patterns in `danger_patterns.json` with explanations and advice. |
| **Copilot CLI integration** | Invokes GitHub Copilot CLI with a safety prompt and displays the suggested safer command in a formatted box. Optional; the app degrades gracefully if Copilot CLI is not installed. |
| **Dual runtime** | Run with Python 3 (`safe.py`) or Node.js (`cosmic-safecli.js`). |
| **Formatted output** | Box-drawing UI for command, warning, breakdown, and Copilot suggestion sections. |

Optional: `colorama` (Python) for colored output on Windows.

---

## Tech Stack

- **Python 3.7+** — `argparse`, `shlex`, `subprocess`, `json`; optional `colorama`
- **Node.js** — stdlib + `chalk` for colors
- **GitHub Copilot CLI** — invoked as a subprocess for safety suggestions
- **Data** — JSON configs for command explanations and danger patterns (no database)

---

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  User command   │────▶│  Parse & explain  │────▶│  Danger detection   │
│  (e.g. stdin or │     │  (tokens + JSON)  │     │  (pattern match)     │
│   CLI argument) │     └──────────────────┘     └──────────┬──────────┘
└─────────────────┘                                            │
                                                               ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Run suggestion │◀────│  Show suggestion  │◀────│  Copilot CLI call    │
│  or cancel      │     │  (optional exec)  │     │  (safety prompt)     │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

When a dangerous pattern is detected, the app builds a short prompt (command + “explain why dangerous and suggest a safer alternative”), calls Copilot CLI, and displays the response in a box. The user can then execute the suggested command or decline.

---

## Prerequisites

- **Python 3.7+** (for `safe.py`) **or** **Node.js** (for `cosmic-safecli.js`)
- **GitHub Copilot CLI** (optional but recommended for full functionality)  
  — [Install guide](https://github.com/features/copilot/cli) · [npm](https://www.npmjs.com/package/@githubnext/github-copilot-cli) · [GitHub CLI extension](https://docs.github.com/copilot/using-github-copilot/using-github-copilot-in-the-command-line)

---

## Installation & Usage

### Python

```bash
git clone https://github.com/ANUJ-codes07/Cosmic-SafeCli.git
cd Cosmic-SafeCli

# Optional: colored output on Windows
pip install -r requirements.txt

# With a command (use nonexistent path for demo so nothing gets deleted)
python safe.py "rm -rf /nonexistent/cosmic-demo-safe"

# Interactive mode (prompts for command)
python safe.py
```

**Python options:**

| Option | Description |
|--------|-------------|
| `--copilot-path` | Path to Copilot CLI executable (default: `copilot`). Use `gh` for the GitHub CLI extension. |
| `--copilot-key` | Value for `COPILOT_API_KEY` in the subprocess environment. |
| `--db` | Path to `commands.json` (default: `commands.json`). |
| `--danger` | Path to `danger_patterns.json` (default: `danger_patterns.json`). |

### Node.js

```bash
npm install
npm start
# or: node cosmic-safecli.js
```

---

## Examples

```bash
# Safe command — breakdown only
python safe.py "ls -la"

# Dangerous pattern — breakdown + warning + Copilot suggestion
# (Uses nonexistent path so safe to run from project folder.)
python safe.py "rm -rf /nonexistent/cosmic-demo-safe"
python safe.py "git reset --hard HEAD"
python safe.py "chmod 777 script.sh"
```

Example output for a dangerous command: **COMMAND** box → **WARNING** box → **🔍 Command Breakdown** (bullets) → **🤖 Copilot Safer Suggestion** box → prompt to run or skip.

---

## Project Structure

| Path | Purpose |
|------|---------|
| `safe.py` | Main Python entrypoint (parser, tokenizer, Copilot subprocess). |
| `cosmic-safecli.js` | Node.js entrypoint; same behavior as `safe.py`. |
| `commands.json` | Map of tokens (e.g. `rm`, `-rf`) to short explanations. |
| `danger_patterns.json` | Dangerous patterns with `pattern`, `explanation`, and `advice`. |
| `requirements.txt` | Python dependencies (optional `colorama`). |
| `DEMO.md` | Hackathon demo walkthrough — quick run, what you’ll see, try-it-yourself. |
| `run_demo.bat` / `run_demo.sh` | One-click demo script (Windows / Linux & macOS). |
| `SUBMISSION.md` | Draft for the DEV challenge submission post. |
| `CONTRIBUTING.md` | How to run, extend, and contribute. |
| `PUSH_TO_GITHUB.md` | Step-by-step: push this repo to GitHub for the challenge. |

---

## License

MIT. See [LICENSE](LICENSE).

---

## Challenge Links

- [**Challenge page**](https://dev.to/challenges/github-2026-01-21) — Submit your DEV post here
- [**Contest rules**](https://dev.to/page/github-challenge-2026-01-21-contest-rules)
- [**GitHub Copilot CLI**](https://github.com/features/copilot/cli) — Install & docs

---

## Updated

- 2026-02-16: Synchronized README with recent code changes (removed automatic execution of Copilot suggestions in `safe.py`).
- Repository pushed from local workspace to remote (see git history for details).
