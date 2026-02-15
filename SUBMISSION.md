# Submission Draft — GitHub Copilot CLI Challenge

Use this draft when publishing your post on DEV.  
**Template:** [DEV submission prefill](https://dev.to/challenges/github-2026-01-21)

**Tags:** `devchallenge`, `githubchallenge`, `cli`, `githubcopilot`

---

*This is a submission for the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21).*

---

## What I Built

**Cosmic SafeCLI** is a CLI security assistant that helps users understand shell commands before running them. It targets a common problem: accidentally running destructive commands (e.g. `rm -rf`, `git reset --hard`) because their effect isn’t obvious.

The tool does three things:

1. **Breaks down the command** — Parses the input and explains each token (command, flags, arguments) in plain English using a small JSON dictionary. This makes it clear what each part does.
2. **Detects dangerous patterns** — Checks the command against a configurable list of risky patterns, explains why they’re dangerous, and suggests safer practices (e.g. “double-check the path”, “use `rm -r` without `-f` to get prompts”).
3. **Integrates GitHub Copilot CLI** — When a dangerous pattern is found, the app calls GitHub Copilot CLI with a short safety prompt and displays a suggested safer alternative. The user can then choose to run that suggestion or cancel.

Cosmic SafeCLI is implemented in both **Python** and **Node.js** so it can be used regardless of the preferred runtime. The goal is to reduce mistakes at the terminal by combining transparent explanations with AI-generated safer options.

---

## Demo

- **Repository:** https://github.com/ANUJ-codes07/Cosmic-SafeCli
- **Quick run:**  
  `python safe.py "rm -rf project"`  
  You’ll see the token breakdown, a danger warning, and (if Copilot CLI is installed) a **Copilot-suggested safer alternative**, with an option to execute or skip.

**Demo assets:** Please add a short video or 1–2 screenshots showing (1) the header and token breakdown, and (2) the danger warning plus Copilot suggestion. This helps judges see the flow end-to-end.

---

## My Experience with GitHub Copilot CLI

Cosmic SafeCLI uses **GitHub Copilot CLI as a core component**: when the app detects a dangerous command, it constructs a safety-focused prompt (e.g. “The user wants to run: `rm -rf project`. Explain briefly why it’s dangerous and suggest a safer alternative. Keep the answer short.”) and invokes the Copilot CLI. The CLI’s response is shown as the “suggested safer alternative”; the user can then run that command or decline.

So Copilot CLI isn’t only used to *build* the project—it *powers* the main safety feature. The app is designed to work without it (explanations and danger warnings still appear), but with Copilot CLI installed, users get contextual, AI-generated alternatives. Error handling for a missing Copilot CLI or timeouts keeps the experience stable.

---

## Submission Checklist

- [x] Repo link set: https://github.com/ANUJ-codes07/Cosmic-SafeCli
- [ ] Add a short video walkthrough or 1–2 screenshots to the Demo section.
- [ ] Optionally add 1–2 sentences on how you used Copilot CLI while *developing* (e.g. prompt design, error handling, or tests).
- [ ] Publish the post on DEV with the tags above and link it from the challenge page.

Thanks for participating.
