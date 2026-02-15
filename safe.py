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
        print('  ' + line)
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

    # Try 'gh copilot suggest' first (GitHub CLI extension - Preferred)
    try:
        # Check if gh is available (by running specific command)
        # We use a nested try because we want to fallback to 'copilot' command if gh fails
        gh_cmd = ['gh', 'copilot', 'suggest', '-t', 'shell', prompt]
        
        # If 'gh' is not in PATH, try absolute path if on Windows default
        if shutil.which('gh') is None and os.name == 'nt':
             default_gh = r"C:\Program Files\GitHub CLI\gh.exe"
             if os.path.exists(default_gh):
                 gh_cmd[0] = default_gh

        gh_completed = subprocess.run(
            gh_cmd,
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        
        if gh_completed.returncode == 0:
            return gh_completed.stdout.strip()
        
        # If gh failed (e.g. extension not installed, or not auth), we might want to try legacy 'copilot'
        # BUT user asked to "use this instead", so maybe we should report the gh error if it looks like an auth/install issue?
        # Let's fallback to legacy 'copilot' only if 'gh' command itself wasn't found or returned specific error?
        # Actually safer to just try legacy copilot as fallback.
        
    except FileNotFoundError:
        pass # gh not found, proceed to legacy copilot
    except Exception:
        pass # gh failed, proceed

    # Standalone 'copilot' CLI (New and Legacy)
    try:
        # Check if we should use new syntax: `copilot --prompt "prompt"` (Clean, no extra flags)
        # The new Winget 'GitHub.Copilot' CLI uses -p/--prompt but fails with --silent or --model sometimes.
        # We'll try basic prompt execution first.
        
        # New Standalone Syntax (Clean)
        # Note: We use --prompt which is alias for -p, widely supported.
        new_cmd = [copilot_path, '--prompt', prompt]
        completed = subprocess.run(
            new_cmd,
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        
        if completed.returncode == 0 and completed.stdout.strip():
             return completed.stdout.strip()
             
        # If clean prompt failed, maybe it needs legacy flags (start-server, model, silent etc.)
        # Fallthrough...
        
    except (FileNotFoundError, Exception):
        pass

    try:
        # Legacy syntax with strict flags
        # Some older versions REQUIRE --model and --silent
        completed = subprocess.run(
            [copilot_path, '--prompt', prompt, '--model', model, '--silent'],
            env=env, capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace'
        )
        if completed.returncode != 0:
            err = completed.stderr.strip()
            if '402' in err or 'quota' in err.lower():
                return f"{Fore.RED}GitHub Copilot quota exceeded (HTTP 402).{Fore.RESET} You have no quota remaining."
            if err:
                return f"Copilot returned an error: {err}"
            return "Copilot did not return a suggestion."
        return completed.stdout.strip() or "Copilot returned no output."
    except FileNotFoundError:
        return f"GitHub Copilot CLI not found. Install 'gh' with 'copilot' extension."
    except subprocess.TimeoutExpired:
        return "Copilot request timed out. Try again or use --copilot-timeout 60 (or higher)."
    except Exception as e:
        return f"Failed to run Copilot: {e}"


def get_gemini_suggestion(command: str, api_key: str) -> str:
    """Call Google Gemini API for a safety suggestion.
    
    Uses standard library urllib to avoid extra dependencies.
    """
    if not api_key:
        return "Gemini API key not provided."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt_text = (
        "You are a Linux safety assistant. The user wants to run this command:\n"
        f"{command}\n\n"
        "Explain briefly why it is dangerous and suggest a safer alternative command.\n"
        "Keep answer short. Output only the safely suggested command if possible, or a very brief explanation."
    )
    
    data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    import time
    
    retries = 3
    for attempt in range(retries):
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            # Extract text from response
            try:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
            except (KeyError, IndexError, TypeError) as e:
                return f"Failed to parse Gemini response: {e}"
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt # 1s, 2s, 4s...
                    print(f"{Fore.YELLOW}Gemini rate limited. Retrying in {wait_time}s...{Fore.RESET}")
                    time.sleep(wait_time)
                    continue
            return f"Gemini API request failed: {e.code} {e.reason}"
        except Exception as e:
            return f"Gemini API error: {e}"


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
        return "git restore --staged ."
        
    # 4. git clean -fd -> git clean -n
    if cmd == 'git' and 'clean' in args:
        if '-fd' in args or '-df' in args or ('-f' in args and '-d' in args):
            return "git clean -n"

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
    
    # DEFAULT COMPATIBILITY KEY removed for security
    DEFAULT_GEMINI_KEY = None
    
    # Get Gemini key from environment or use default (None if not provided)
    gemini_key = os.environ.get('GEMINI_API_KEY') or DEFAULT_GEMINI_KEY

    parser = argparse.ArgumentParser(description='Cosmic SafeCLI — Understand Before You Execute')
    parser.add_argument('command', nargs='?', default=None, help='The full command to analyze (quote it if it contains spaces)')
    parser.add_argument('--db', default='commands.json', help='Path to commands explanations JSON')
    parser.add_argument('--danger', default='danger_patterns.json', help='Path to danger patterns JSON')
    parser.add_argument('--copilot-key', default=None, help='Optional Copilot API key (set COPILOT_API_KEY for the subprocess)')
    parser.add_argument('--copilot-path', default='copilot', help='Path to the Copilot CLI executable')
    parser.add_argument('--copilot-model', default='gpt-4.1', help='Model to use for Copilot CLI (default: gpt-4.1)')
    parser.add_argument('--copilot-timeout', type=int, default=15, help='Seconds to wait for Copilot CLI (default: 15)')
    parser.add_argument('--gemini-key', default=gemini_key, help='Google Gemini API key for fallback')
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
    print('🔍 Command Breakdown')
    print(_rule())
    max_len = max(len(t) for t, _ in breakdown)
    for token, explanation in breakdown:
        print(f"  • {token.ljust(max_len)}  ->  {explanation}")
    print(_rule())

        # Copilot suggestion box (if dangerous)
    if hits:
        print()
        print(f"{Fore.CYAN}Contacting GitHub Copilot...{Fore.RESET}")
        suggestion = get_copilot_suggestion(cmd, timeout=args.copilot_timeout, api_key=args.copilot_key, copilot_path=args.copilot_path, model=args.copilot_model)
        
        # Check if Copilot returned an error; if so, use fallback
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_suggestion = ansi_escape.sub('', suggestion).strip()
        
        err_starts = ('Copilot returned', 'Copilot CLI not found', 'Copilot did not',
                      'Copilot request', 'Failed to run Copilot', 'Did you mean:', 'For non-interactive',
                      'GitHub Copilot quota exceeded', 'No safe automatic alternative', 'Gemini API')

        is_error = any(clean_suggestion.startswith(s) for s in err_starts) or not clean_suggestion
        
        if is_error:
            # Try Gemini Fallback
            if args.gemini_key:
                print(f"{Fore.CYAN}Copilot unavailable. Contacting Google Gemini...{Fore.RESET}")
                gemini_suggestion = get_gemini_suggestion(cmd, args.gemini_key)
                
                # Check if Gemini failed
                clean_gemini = ansi_escape.sub('', gemini_suggestion).strip()
                if any(clean_gemini.startswith(s) for s in ('Gemini API', 'Failed to parse')):
                     print(f"{Fore.RED}Gemini fallback failed: {clean_gemini}{Fore.RESET}")
                     # Fall through to local rules
                else:
                    suggestion = gemini_suggestion
                    is_error = False # Gemini worked!
            
            # If still error (no Gemini key or Gemini failed), use local rules
            if is_error:
                print(f"{Fore.YELLOW}Copilot/Gemini unavailable — using local safety rules.{Fore.RESET}")
                suggestion = generate_fallback(tokens)
                # Re-clean suggestion as it is now the fallback
                clean_suggestion = suggestion.strip()
        
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

        # Ask the user whether to proceed with the suggested command ONLY if it's not an error
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_suggestion = ansi_escape.sub('', suggestion).strip()
        
        if not any(clean_suggestion.startswith(s) for s in err_starts):
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
                    # Fallback: take first non-empty line from Copilot suggestion (skip error messages)
                    exec_cmd = ''
                    err_prefixes = ('Copilot returned an error', 'Copilot CLI not found', 'Copilot did not',
                                    'Copilot request timed out', 'Failed to run Copilot', 'Did you mean:',
                                    'For non-interactive mode', 'Try ', 'Invalid command format',
                                    'GitHub Copilot quota exceeded')
                    for line in suggestion.splitlines():
                        line = line.strip().strip('`')
                        if line and not any(line.startswith(p) for p in err_prefixes):
                            exec_cmd = line
                            break
                if not exec_cmd:
                    print('No command to execute. Aborting.')
                else:
                    print(f'Running: {exec_cmd}')
                    try:
                        # Use capture_output=False to allow interactive commands (like rd /s confirmation)
                        subprocess.run(exec_cmd, shell=True, check=False)
                    except Exception as e:
                        print(f'Failed to execute command: {e}')
            else:
                print('Not executing suggested command.')
    else:
        print('\nNo known dangerous patterns detected.')


if __name__ == '__main__':
    main()
