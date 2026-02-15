#!/usr/bin/env python3
"""
Cosmic SafeCLI — Command-line security assistant.

Explains shell commands in plain English, detects dangerous patterns, and uses
GitHub Copilot CLI to suggest safer alternatives. Part of the GitHub Copilot CLI
Challenge (https://dev.to/challenges/github-2026-01-21).

Usage:
    python safe.py "rm -rf project"
    python safe.py   # interactive: prompt for command

Options: --copilot-path, --copilot-key, --db, --danger (see --help).
"""

import argparse
import json
import shlex
import subprocess
import sys
import os
from typing import List, Dict, Any

# Colored output: try to use colorama for Windows compatibility, otherwise use ANSI fallbacks
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
except Exception:
    class Fore:
        RED = '\u001b[31m'
        YELLOW = '\u001b[33m'
        GREEN = '\u001b[32m'
        CYAN = '\u001b[36m'
        RESET = '\u001b[0m'
    class Style:
        BRIGHT = '\u001b[1m'
        RESET_ALL = '\u001b[0m'

# Box-drawing for formatted output (width = 52)
_BOX_W = 52


def _box_top(title: str) -> str:
    """Return top border line with title: ┌──── TITLE ────┐"""
    n = _BOX_W - 2 - len(title)
    left = n // 2
    right = n - left
    return '┌' + '─' * left + title + '─' * right + '┐'


def _box_bottom() -> str:
    return '└' + '─' * _BOX_W + '┘'


def _box_section(title: str, lines: List[str]) -> None:
    """Print a box with title and content lines (each line prefixed with two spaces)."""
    print(_box_top(title))
    for line in lines:
        print('  ' + line)
    print(_box_bottom())


def _rule(char: str = '─', length: int = None) -> str:
    if length is None:
        length = _BOX_W
    return char * length


def parse_command(cmd_str: str) -> List[str]:
    """Split the input command into tokens while respecting quotes.

    Uses shlex.split to handle quoted arguments correctly.
    """
    try:
        return shlex.split(cmd_str)
    except ValueError:
        return cmd_str.strip().split()


def _expand_short_flags(token: str) -> List[str]:
    """Expand combined short flags like '-rf' into ['-r', '-f'].

    Long flags (starting with '--') are returned as-is.
    """
    if token.startswith('--') or not token.startswith('-') or len(token) <= 2:
        return [token]
    return ['-' + ch for ch in token[1:]]


def explain_tokens(tokens: List[str], commands_db: Dict[str, str]) -> List[tuple]:
    """Return a list of (token, explanation) pairs.

    This function will expand combined short flags and look up explanations in the
    provided commands_db dictionary. Unknown tokens are marked clearly so beginners
    know the lookup failed.
    """
    result = []
    for token in tokens:
        parts = _expand_short_flags(token) if token.startswith('-') and not token.startswith('--') else [token]
        for part in parts:
            explanation = commands_db.get(part, 'No explanation available')
            result.append((part, explanation))
    return result


def detect_danger(cmd_str: str, danger_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect dangerous patterns from the danger_patterns list.

    Uses a simple normalized substring match (case-insensitive) which is easy to
    understand and robust for typical dangerous examples like 'rm -rf' or
    'git reset --hard'.
    """
    normalized = ' '.join(parse_command(cmd_str)).lower()
    hits = []
    for entry in danger_patterns:
        pattern = entry.get('pattern', '').lower()
        if pattern and pattern in normalized:
            hits.append(entry)
    return hits


def get_copilot_suggestion(command: str, timeout: int = 10, api_key: str = None, copilot_path: str = "copilot") -> str:
    """Call the GitHub Copilot CLI with a safety prompt and return its output.

    If the 'copilot' command is not available, return a friendly message instead.
    """
    prompt = (
        "You are a Linux safety assistant.\n"
        "The user wants to run this command:\n"
        f"{command}\n\n"
        "Explain briefly why it is dangerous and suggest a safer alternative command.\n"
        "Keep answer short."
    )

    env = os.environ.copy()
    if api_key:
        env['COPILOT_API_KEY'] = api_key

    try:
        # Call copilot CLI with the prompt as a single argument. The Copilot CLI may
        # accept the prompt as a single parameter; this is a reasonable default.
        completed = subprocess.run([copilot_path, prompt], env=env, capture_output=True, text=True, timeout=timeout)
        # If copilot exits with a non-zero code but provided stderr, include it.
        if completed.returncode != 0:
            # If command not found, a FileNotFoundError would be raised instead.
            err = completed.stderr.strip()
            if err:
                return f"Copilot returned an error: {err}"
            return "Copilot did not return a suggestion."
        return completed.stdout.strip() or "Copilot returned no output."
    except FileNotFoundError:
        return f"Copilot CLI not found at '{copilot_path}'. Install GitHub Copilot CLI or ensure '{copilot_path}' is available."
    except subprocess.TimeoutExpired:
        return "Copilot request timed out. Try again or increase timeout."
    except Exception as e:
        return f"Failed to run Copilot: {e}"


def load_json(path: str):
    """Load JSON from disk and return the parsed data.

    Exits the program with an error message if the file is missing or invalid so
    beginners get clear feedback.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}Error:{Fore.RESET} Required file not found: {path}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}Error:{Fore.RESET} Failed to parse {path}: {e}")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description='Cosmic SafeCLI — Understand Before You Execute')
    parser.add_argument('command', nargs='?', default=None, help='The full command to analyze (quote it if it contains spaces)')
    parser.add_argument('--db', default='commands.json', help='Path to commands explanations JSON')
    parser.add_argument('--danger', default='danger_patterns.json', help='Path to danger patterns JSON')
    parser.add_argument('--copilot-key', default=None, help='Optional Copilot API key (set COPILOT_API_KEY for the subprocess)')
    parser.add_argument('--copilot-path', default='copilot', help='Path to the Copilot CLI executable')
    args = parser.parse_args()

    # Header
    print(r"""
 ________  ________  ________  _____ ______   ___  ________          ________  ________  ________ _______   ________  ___       ___     
|\   ____\|\   __  \|\   ____\|\   _ \  _   \|\  \|\   ____\        |\   ____\|\   __  \|\  _____\\  ___ \ |\   ____\|\  \     |\  \    
\ \  \___|\ \  \|\  \ \  \___|\ \  \\\__\ \  \ \  \ \  \___|        \ \  \___|\ \  \|\  \ \  \__/\ \   __/|\ \  \___|\ \  \    \ \  \   
 \ \  \    \ \  \\\  \ \_____  \ \  \\|__| \  \ \  \ \  \            \ \_____  \ \   __  \ \   __\\ \  \_|/_\ \  \    \ \  \    \ \  \  
  \ \  \____\ \  \\\  \|____|\  \ \  \    \ \  \ \  \ \  \____        \|____|\  \ \  \ \  \ \  \_| \ \  \_|\ \ \  \____\ \  \____\ \  \ 
   \ \_______\ \_______\____\_\  \ \__\    \ \__\ \__\ \_______\        ____\_\  \ \__\ \__\ \__\   \ \_______\ \_______\ \_______\ \__\
    \|_______|\|_______|\_________\|__|     \|__|\|__|\|_______|       |\_________\|__|\|__|\|__|    \|_______|\|_______|\|_______|\|__|
                       \|_________|                                    \|_________|                                                     
""")

    if args.command is None:
        try:
            cmd = input('Enter command to analyze: ').strip()
        except EOFError:
            print('No command provided.')
            sys.exit(0)
    else:
        cmd = args.command.strip()

    tokens = parse_command(cmd)
    if not tokens:
        print('No command provided.')
        sys.exit(0)

    commands_db = load_json(args.db)
    danger_db = load_json(args.danger)
    hits = detect_danger(cmd, danger_db)
    breakdown = explain_tokens(tokens, commands_db)

    # Command box
    print()
    _box_section(' COMMAND ', [cmd])

    # Warning box (if dangerous)
    if hits:
        warning_lines = [
            Fore.YELLOW + Style.BRIGHT + '⚠ DANGEROUS COMMAND DETECTED' + Style.RESET_ALL + Fore.RESET,
            hits[0].get('explanation', 'No explanation provided.'),
            Fore.RED + '⚠ DO NOT RUN THIS DIRECTLY' + Fore.RESET,
        ]
        for h in hits[1:]:
            warning_lines.append('')
            warning_lines.append(h.get('explanation', 'No explanation provided.'))
            if h.get('advice'):
                warning_lines.append(h.get('advice'))
        print()
        _box_section(' WARNING ', warning_lines)

    # Command breakdown
    print()
    print('🔍 Command Breakdown')
    print(_rule())
    max_len = max(len(t) for t, _ in breakdown)
    for token, explanation in breakdown:
        print(f"  • {token.ljust(max_len)}  ->  {explanation}")
    print(_rule())

    # Copilot suggestion box (if dangerous)
    if hits:
        print()
        suggestion = get_copilot_suggestion(cmd, api_key=args.copilot_key, copilot_path=args.copilot_path)
        # First line as "Use: ..." if it looks like a command; otherwise show full suggestion
        suggestion_lines = suggestion.strip().splitlines()
        if suggestion_lines:
            first = suggestion_lines[0].strip().strip('`')
            if first and not first.startswith('Why') and not first.startswith('The'):
                suggestion_display = ['Use: ' + first] + suggestion_lines[1:]
            else:
                suggestion_display = suggestion_lines
        else:
            suggestion_display = [suggestion.strip() or 'No suggestion.']
        _box_section(' 🤖 Copilot Safer Suggestion ', suggestion_display)

        # Ask the user whether to proceed with the suggested command
        try:
            proceed = input('\nExecute suggested command? (y/N): ').strip().lower()
        except EOFError:
            proceed = 'n'
        if proceed in ('y', 'yes'):
            try:
                exec_cmd = input('Enter command to execute (leave empty to use Copilot suggestion): ').strip()
            except EOFError:
                exec_cmd = ''
            if not exec_cmd:
                # Fallback: take first non-empty line from Copilot suggestion
                exec_cmd = ''
                for line in suggestion.splitlines():
                    line = line.strip().strip('`')
                    if line:
                        exec_cmd = line
                        break
            if not exec_cmd:
                print('No command to execute. Aborting.')
            else:
                print(f'Running: {exec_cmd}')
                try:
                    completed = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True)
                    print('\n--- STDOUT ---')
                    print(completed.stdout)
                    print('\n--- STDERR ---')
                    print(completed.stderr)
                except Exception as e:
                    print(f'Failed to execute command: {e}')
        else:
            print('Not executing suggested command.')
    else:
        print('\nNo known dangerous patterns detected.')


if __name__ == '__main__':
    main()
