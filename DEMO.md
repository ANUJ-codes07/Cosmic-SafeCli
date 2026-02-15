# Hackathon Demo — Cosmic SafeCLI

Quick walkthrough for judges and reviewers. Run one command to see the full flow.

---

## Quick demo (30 seconds)

**Python:**

```bash
python safe.py "rm -rf project"
```

**Node.js:**

```bash
npm start
# When prompted, type: rm -rf project
# Or run with argument: node cosmic-safecli.js "rm -rf project"
```

You’ll see: **COMMAND** box → **WARNING** box → **🔍 Command Breakdown** → **🤖 Copilot Safer Suggestion** (if Copilot CLI is installed).

---

## What you’ll see

1. **COSMIC header** — ASCII art banner (unchanged).
2. **Command box** — The command you entered.
3. **Warning box** (for dangerous commands) — “⚠ DANGEROUS COMMAND DETECTED”, explanation, “⚠ DO NOT RUN THIS DIRECTLY”.
4. **Command breakdown** — Each token (e.g. `rm`, `-r`, `-f`) with a short explanation.
5. **Copilot suggestion box** (if dangerous + Copilot CLI installed) — AI-suggested safer command; you can run it or skip.

---

## Try it yourself

| Step | Command | What it shows |
|------|--------|----------------|
| 1 | `python safe.py "ls -la"` | Safe command — breakdown only, no warning. |
| 2 | `python safe.py "rm -rf /tmp/foo"` | Dangerous — full flow including Copilot suggestion. |
| 3 | `python safe.py "git reset --hard HEAD"` | Another dangerous pattern with explanation and suggestion. |

---

## One-line demo script

**Windows:** Double-click `run_demo.bat` or run:

```bash
run_demo.bat
```

**Linux/macOS:** `./run_demo.sh` or `bash run_demo.sh`

This runs the demo command so you can see the output immediately.

---

## For judges

- **No login required** — Everything runs locally.
- **Copilot CLI optional** — If not installed, you still get command explanation + danger warning; only the “Copilot Safer Suggestion” box is skipped.
- **Python or Node** — Use whichever you have; behavior is the same.
