# Contributing to Cosmic SafeCLI

Thanks for your interest in Cosmic SafeCLI. Here’s how to run it locally and extend it.

## Running locally

- **Python:** `pip install -r requirements.txt` (optional), then `python safe.py "your command"` or `python safe.py` for interactive mode.
- **Node.js:** `npm install` then `npm start` or `node cosmic-safecli.js`.

Ensure `commands.json` and `danger_patterns.json` are in the project root (or pass `--db` / `--danger` with Python).

## Extending command explanations

Edit **`commands.json`**. Keys are tokens (e.g. `rm`, `-r`, `--force`); values are short plain-English explanations. Add new entries for commands or flags you want the tool to explain.

## Adding danger patterns

Edit **`danger_patterns.json`**. Each entry should have:

- `pattern` — Substring to match in the normalized command (e.g. `"rm -rf"`, `"git reset --hard"`).
- `explanation` — Why this pattern is dangerous.
- `advice` — Optional safer practice or alternative.

The matcher is case-insensitive and uses normalized spacing.

## Copilot CLI integration

The Python entrypoint calls Copilot CLI via `get_copilot_suggestion()` in `safe.py`; the Node version uses `getCopilotSuggestion()` in `cosmic-safecli.js`. To change the safety prompt, edit the prompt string in those functions. Use `--copilot-path` (Python) to point to a different executable (e.g. `gh` for the GitHub CLI extension).

## Code style

- **Python:** Keep functions small and documented; use type hints where helpful.
- **Node:** Match existing style (CommonJS, async/await). No new dependencies without good reason.

If you open a pull request, please keep changes focused and describe what you’re changing and why.
