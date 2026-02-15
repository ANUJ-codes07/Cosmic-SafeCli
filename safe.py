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
import shutil
from typing import List, Dict, Any


def run_command(cmd: str) -> int:
    """Run a shell command in an OS-appropriate way and return the exit code.

    On Windows prefer using cmd.exe for built-in commands (del, rmdir), but
    otherwise run via the system shell. This centralizes any OS-specific
    execution tweaks so the rest of the code can call a single helper.
    """
    try:
        if os.name == 'nt':
            # For Windows builtins, use cmd.exe /c to ensure they run correctly
            builtin_prefixes = ('del ', 'rmdir ', 'rd ', 'copy ', 'move ')
            trimmed = cmd.strip().lower()
            if any(trimmed.startswith(p) for p in builtin_prefixes):
                return subprocess.run(['cmd.exe', '/c', cmd], check=False).returncode
            # Otherwise let shell handle it (should invoke Powershell/ cmd depending on environment)
            return subprocess.run(cmd, shell=True, check=False).returncode
        else:
            # POSIX: using shell=True is acceptable for user-provided commands
            return subprocess.run(cmd, shell=True, check=False).returncode
    except Exception:
        return 1


def _safe_str(s: str) -> str:
    enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    try:
        s.encode(enc)
        return s
    except UnicodeEncodeError:
        return s.encode(enc, errors='replace').decode(enc)

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

# Use ASCII box chars when stdout can't encode Unicode (e.g. Windows cp1252)
def _box_chars():
    enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    try:
        '┌─┐└┘'.encode(enc)
        return ('┌', '┐', '└', '┘', '─')
    except (UnicodeEncodeError, TypeError):
        return ('+', '+', '+', '+', '-')

_BOX = _box_chars()


def _box_top(title: str) -> str:
    """Return top border line with title."""
    tl, tr, _, _, h = _BOX
    n = _BOX_W - 2 - len(title)
    left = n // 2
    right = n - left
    return tl + h * left + title + h * right + tr


def _box_bottom() -> str:
    _, _, bl, br, h = _BOX
    return bl + h * _BOX_W + br


def _box_section(title: str, lines: List[str]) -> None:
    """Print a box with title and content lines (each line prefixed with two spaces)."""
    print(_box_top(title))
    for line in lines:
        print('  ' + _safe_str(line))
    print(_box_bottom())


def _rule(char: str = None, length: int = None) -> str:
    if length is None:
        length = _BOX_W
    if char is None:
        char = _BOX[4]  # horizontal line char
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


def get_copilot_suggestion(command: str, timeout: int = 15, api_key: str = None, copilot_path: str = "copilot", model: str = "gpt-4.1") -> str:
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
    
    # Force non-interactive mode for new Copilot CLI (GitHub.Copilot package)
    env['CI'] = 'true'

    # Use standalone 'copilot' CLI only (no 'gh' variants). Prefer non-interactive
    # `--prompt` calls first to avoid hanging interactive invocations.

    # Ensure copilot binary is available
    if shutil.which(copilot_path) is None:
        return f"GitHub Copilot CLI not found. Install the standalone 'copilot' CLI and ensure it's on PATH."

    # Try legacy/non-interactive syntax first (safer)
    try:
        completed = subprocess.run(
            [copilot_path, '--prompt', prompt, '--model', model, '--silent'],
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
        if completed.returncode != 0:
            err = (completed.stderr or '').strip()
            if '402' in err or 'quota' in err.lower():
                return f"{Fore.RED}GitHub Copilot quota exceeded (HTTP 402).{Fore.RESET} You have no quota remaining."
            if err:
                return f"Copilot returned an error: {err}"
            # Fall through to try alternative invocation
    except subprocess.TimeoutExpired:
        print(f"{Fore.YELLOW}⚠ Copilot request timed out after {timeout}s{Fore.RESET}", file=sys.stderr)
    except FileNotFoundError:
        return f"GitHub Copilot CLI not found. Install the standalone 'copilot' CLI and ensure it's on PATH."
    except Exception as e:
        # Continue to try alternative invocation
        pass

    # Try the newer '-i' immediate invocation as a fallback
    try:
        new_cmd = [copilot_path, '-i', prompt, '--allow-all-tools']
        completed = subprocess.run(
            new_cmd,
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
        if completed.returncode != 0:
            copilot_error = (completed.stderr or '').strip() or f"Exit code {completed.returncode}"
            print(f"{Fore.YELLOW}⚠ copilot -i failed: {copilot_error}{Fore.RESET}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"{Fore.YELLOW}⚠ Copilot request timed out after {timeout}s{Fore.RESET}", file=sys.stderr)
        return "Copilot request timed out."
    except FileNotFoundError:
        return f"GitHub Copilot CLI not found. Install the standalone 'copilot' CLI and ensure it's on PATH."
    except Exception as e:
        return f"Failed to run Copilot: {e}"
    except subprocess.TimeoutExpired:
        print(f"{Fore.YELLOW}⚠ Copilot request timed out after {timeout}s{Fore.RESET}", file=sys.stderr)
        return "Copilot request timed out."
    except Exception as e:
        return f"Failed to run Copilot: {e}"



def generate_fallback(command_tokens: List[str]) -> str:
    """Generate a safer alternative command based on local rules.
    
    Used when Copilot/Gemini is unavailable or fails.
    """
    if not command_tokens:
        return "No safe automatic alternative available. Review command manually."

    cmd = command_tokens[0]
    args = command_tokens[1:]
    full_cmd = ' '.join(command_tokens)
    
    # 1. rm -rf <target> -> rm -ri <target> (Linux) / rd /s <target> (Windows)
    if cmd == 'rm':
        # Check for recursive and force flags
        has_r = any(arg.startswith('-') and 'r' in arg for arg in args)
        has_f = any(arg.startswith('-') and 'f' in arg for arg in args)
        
        if has_r:
            if os.name == 'nt':
                # Windows: 'rmdir /S /Q' avoids double confirmation prompts (User already confirmed in SafeCLI)
                # We need to extract the target (non-flag args)
                targets = [arg for arg in args if not arg.startswith('-')]
                if targets:
                    # Windows: Check if target exists to decide between rmdir (dir) and del (file)
                    # We take the first target for simplicity in this fallback
                    target = targets[0] 
                    is_file = os.path.isfile(target)
                    
                    quoted_targets = [f'"{t}"' for t in targets]
                    args_str = ' '.join(quoted_targets)
                    
                    if is_file:
                        return f"del /F /Q {args_str}"
                    else:
                        # Default to rmdir for 'rm -rf' (recursive intent) or if dir
                        return f"rmdir /S /Q {args_str}"
                return "echo 'Please specify a target directory'"
            else:
                # Docker/Linux: -ri
                new_args = []
                for arg in args:
                    if arg.startswith('-'):
                        if 'r' in arg and 'f' in arg:
                            new_args.append(arg.replace('f', 'i'))
                        elif 'f' in arg:
                             new_args.append(arg.replace('f', 'i'))
                        else:
                            new_args.append(arg)
                    else:
                        new_args.append(arg)
                return full_cmd.replace(' -rf ', ' -ri ').replace(' -fr ', ' -ir ').replace(' -f ', ' -i ')

    # 2. chmod 777 <file> -> chmod 755 <file>
    if cmd == 'chmod':
        if '777' in args:
            return full_cmd.replace(' 777 ', ' 755 ')
        if '-R' in args and '777' in args: # approximate
             return full_cmd.replace(' 777 ', ' 755 ')

    # 3. git reset --hard -> git restore --staged .
    if cmd == 'git' and 'reset' in args and '--hard' in args:
        return "git restore --staged .  # or consider 'git reset --soft <commit>' to avoid data loss"
        
    # 4. git clean -fd -> git clean -n
    if cmd == 'git' and 'clean' in args:
        if '-fd' in args or '-df' in args or ('-f' in args and '-d' in args):
            return "git clean -n"

    # 4b. git push --force -> git push --force-with-lease
    if cmd == 'git' and 'push' in args and ('--force' in args or '-f' in args):
        return "git push --force-with-lease"

    # 5. dd -> echo "Dangerous..."
    if cmd == 'dd':
         return 'echo "Dangerous disk overwrite command blocked"'

    # 6. mkfs -> echo "Filesystem..."
    if cmd == 'mkfs' or any(c.startswith('mkfs.') for c in command_tokens):
         return 'echo "Filesystem format prevented"'

    return "No safe automatic alternative available. Review command manually."


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


def load_env(env_path: str = '.env'):
    """Load environment variables from a .env file."""
    if not os.path.exists(env_path):
        return
        
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        print(f"{Fore.YELLOW}Warning:{Fore.RESET} Failed to load .env: {e}")


def main():
    # Load .env file
    load_env()
    
    # (No Gemini fallback) — only Copilot is used now

    parser = argparse.ArgumentParser(description='Cosmic SafeCLI — Understand Before You Execute')
    parser.add_argument('command', nargs='?', default=None, help='The full command to analyze (quote it if it contains spaces)')
    parser.add_argument('--db', default='commands.json', help='Path to commands explanations JSON')
    parser.add_argument('--danger', default='danger_patterns.json', help='Path to danger patterns JSON')
    parser.add_argument('--copilot-key', default=None, help='Optional Copilot API key (set COPILOT_API_KEY for the subprocess)')
    parser.add_argument('--copilot-path', default='copilot', help='Path to the Copilot CLI executable')
    parser.add_argument('--copilot-model', default='gpt-4.1', help='Model to use for Copilot CLI (default: gpt-4.1)')
    parser.add_argument('--copilot-timeout', type=int, default=15, help='Seconds to wait for Copilot CLI (default: 15)')
    args = parser.parse_args()

    # Header
    print(r"""
 ________  ________  ________  _____ ______   ___  ________          ________  ________  ________ _______   ________  ___       ___     
|\   ____\|\   __  \|\   ____\|\   _ \  _   \|\  \|\   ____\        |\   ____\|\   __  \|\  _____\\  ___ \ |\   ____\|\  \     |\  \    
\ \  \___|\ \  \|\  \ \  \___|\ \  \\\__\ \  \ \  \ \  \___|        \ \  \___|\ \  \|\  \ \  \__/\ \   __/|\ \  \___|\ \  \    \ \  \   
 \ \  \    \ \  \\\  \ \_____  \ \  \\|__| \  \ \  \ \  \            \ \_____  \ \   __  \ \   __\\ \  \_|/_\ \  \    \ \  \    \ \  \  
  \ \  ____\ \  \\\  \|____|\  \ \  \    \ \  \ \  \ \  \____        \|____|\  \ \  \ \  \ \  \_| \ \  \_|\ \ \  \____\ \  \____\ \  \ 
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

    # Command box (single line so we don't get extra box lines from newlines in cmd)
    print()
    _box_section(' COMMAND ', [cmd.replace('\n', ' ').strip()])

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
    print(_safe_str('🔍 Command Breakdown'))
    print(_rule())
    max_len = max(len(t) for t, _ in breakdown)
    for token, explanation in breakdown:
        print(_safe_str(f"  • {token.ljust(max_len)}  ->  {explanation}"))
    print(_rule())

        # Copilot suggestion box (if dangerous)
    if hits:
        print()
        print(f"{Fore.CYAN}Contacting GitHub Copilot...{Fore.RESET}")
        suggestion = get_copilot_suggestion(cmd, timeout=args.copilot_timeout, api_key=args.copilot_key, copilot_path=args.copilot_path, model=args.copilot_model)
        
        # Ensure suggestion is a string (Copilot timeout may return None)
        if suggestion is None:
            suggestion = 'Copilot request timed out.'

        # Check if Copilot returned an error; if so, use fallback
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_suggestion = ansi_escape.sub('', str(suggestion)).strip()
        
        err_starts = ('Copilot returned', 'Copilot CLI not found', 'Copilot did not',
                  'Copilot request', 'Failed to run Copilot', 'Did you mean:', 'For non-interactive',
                  'GitHub Copilot quota exceeded', 'No safe automatic alternative')

        is_error = any(clean_suggestion.startswith(s) for s in err_starts) or not clean_suggestion
        
        if is_error:
            # No Gemini fallback configured — use local safety rules
            print(f"{Fore.YELLOW}Copilot unavailable — using local safety rules.{Fore.RESET}")
            suggestion = generate_fallback(tokens)
            # Re-clean suggestion as it is now the fallback
            clean_suggestion = str(suggestion).strip()
        
        # First line as "Use: ..." if it looks like a command; otherwise show full suggestion
        suggestion_lines = suggestion.strip().splitlines()
        
        # Recalculate err_starts check for the new suggestion (fallback might be "No safe automatic...")
        # We need to ensure fallback error message is treated as error?
        # "No safe automatic alternative available. Review command manually." should probably NOT be executed.
        
        # Update err_starts to include the fallback specific error message if needed, 
        # BUT fallback function returns "No safe automatic..." which doesn't look like a command.
        # Let's add that to err_starts or handle it logic below.
        
        if suggestion_lines:
            first = suggestion_lines[0].strip().strip('`')
            # Check against original err_starts AND the fallback specific message
            is_fallback_error = first.startswith("No safe automatic")
            
            if (first and not first.startswith('Why') and not first.startswith('The')
                    and not any(first.startswith(s) for s in err_starts)
                    and not is_fallback_error):
                suggestion_display = ['Use: ' + first] + suggestion_lines[1:]
            else:
                suggestion_display = suggestion_lines
        else:
            suggestion_display = [suggestion.strip() or 'No suggestion.']
        _box_section(' 🤖 Copilot Safer Suggestion ', suggestion_display)

        # Execution capability removed: only display Copilot suggestions.
        # For safety we no longer prompt to execute or run suggested commands.
        print()
        print(_safe_str('Execution of suggested commands has been disabled for safety.'))
        print(_safe_str('Review the Copilot suggestion above and run any commands manually if you choose.'))
    else:
        print('\nNo known dangerous patterns detected.')


if __name__ == '__main__':
    main()
