#!/usr/bin/env node
/**
 * Cosmic SafeCLI (Node.js) — Explains shell commands, detects danger patterns,
 * and uses GitHub Copilot CLI to suggest safer alternatives.
 * Usage: node cosmic-safecli.js  or  npm start
 */
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const readline = require('readline');

// Chalk interop for CJS/ESM
let chalk;
try {
  const _chalk = require('chalk');
  chalk = (_chalk && typeof _chalk.cyan === 'function') ? _chalk : (_chalk && _chalk.default && typeof _chalk.default.cyan === 'function') ? _chalk.default : null;
} catch (e) {
  chalk = null;
}
if (!chalk) {
  chalk = {
    bold: (s) => s,
    cyan: (s) => s,
    yellow: (s) => s,
    red: (s) => s,
    green: (s) => s,
    bgBlue: (s) => s,
    white: (s) => s,
  };
}

// Box-drawing for formatted output
const BOX_W = 52;
const boxTop = (title) => {
  const n = BOX_W - 2 - title.length;
  const left = Math.floor(n / 2);
  const right = n - left;
  return '┌' + '─'.repeat(left) + title + '─'.repeat(right) + '┐';
};
const boxBottom = () => '└' + '─'.repeat(BOX_W) + '┘';
const boxSection = (title, lines) => {
  console.log(boxTop(title));
  lines.forEach(line => console.log('  ' + line));
  console.log(boxBottom());
};
const rule = (len = BOX_W) => '─'.repeat(len);

const loadJson = (p) => {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    console.error(chalk.red(`Error: failed to load ${p}: ${e.message}`));
    process.exit(2);
  }
};

function parseCommand(input) {
  const re = /(?:"([^"]*)")|([^\s"]+)/g;
  const tokens = [];
  let m;
  while ((m = re.exec(input)) !== null) {
    if (m[1] !== undefined) tokens.push(m[1]);
    else if (m[2] !== undefined) tokens.push(m[2]);
  }
  return tokens;
}

function expandShortFlags(token) {
  if (!token.startsWith('-') || token.startsWith('--') || token.length <= 2) return [token];
  return token.slice(1).split('').map(c => '-' + c);
}

function explainTokens(tokens, db) {
  const out = [];
  tokens.forEach(t => {
    const parts = (t.startsWith('-') && !t.startsWith('--')) ? expandShortFlags(t) : [t];
    parts.forEach(p => out.push([p, db[p] || 'No explanation available']));
  });
  return out;
}

function detectDanger(cmdStr, dangerList) {
  const normalized = parseCommand(cmdStr).join(' ').toLowerCase();
  return dangerList.filter(e => {
    const pattern = (e.pattern || '').toLowerCase();
    return pattern && normalized.includes(pattern);
  });
}

function getCopilotSuggestion(command, copilotPath = 'copilot', timeout = 10000) {
  const prompt = `You are a Linux safety assistant. The user wants to run this command:\n${command}\nExplain briefly why it is dangerous and suggest a safer alternative. Keep answer short.`;
  return new Promise(resolve => {
    try {
      execFile(copilotPath, ['--prompt', prompt], { timeout }, (err, stdout, stderr) => {
        if (err) {
          if (err.code === 'ENOENT') return resolve(`Copilot CLI not found at '${copilotPath}'.`);
          if (stderr) return resolve(`Copilot error: ${stderr.trim()}`);
          return resolve('Copilot did not return a suggestion.');
        }
        resolve((stdout || '').trim() || 'Copilot returned no output.');
      });
    } catch (e) {
      resolve(`Failed to run Copilot: ${e.message}`);
    }
  });
}

async function showHeader() {
  const art = `
 ________  ________  ________  _____ ______   ___  ________          ________  ________  ________ _______   ________  ___       ___     
|\   ____\|\   __  \|\   ____\|\   _ \  _   \|\  \|\   ____\        |\   ____\|\   __  \|\  _____\\  ___ \ |\   ____\|\  \     |\  \    
\ \  \___|\ \  \|\  \ \  \___|\ \  \\\__\ \  \ \  \ \  \___|        \ \  \___|\ \  \|\  \ \  \__/\ \   __/|\ \  \___|\ \  \    \ \  \   
 \ \  \    \ \  \\\  \ \_____  \ \  \\|__| \  \ \  \ \  \            \ \_____  \ \   __  \ \   __\\ \  \_|/_\ \  \    \ \  \    \ \  \  
  \ \  \____\ \  \\\  \|____|\  \ \  \    \ \  \ \  \ \  \____        \|____|\  \ \  \ \  \ \  \_| \ \  \_|\ \ \  \____\ \  \____\ \  \ 
   \ \_______\ \_______\____\_\  \ \__\    \ \__\ \__\ \_______\        ____\_\  \ \__\ \__\ \__\   \ \_______\ \_______\ \_______\ \__\
    \|_______|\|_______|\_________\|__|     \|__|\|__|\|_______|       |\_________\|__|\|__|\|__|    \|_______|\|_______|\|_______|\|__|
                       \|_________|                                    \|_________|                                                     
`;

  try {
    console.log(art);
  } catch (e) {
    console.log(art);
  }
  console.log();
}

async function analyzeCommand(cmd, commandsDb, dangerDb) {
  const tokens = parseCommand(cmd);
  if (!tokens.length) {
    console.log(chalk.yellow('No command provided.')); return;
  }
  const hits = detectDanger(cmd, dangerDb);
  const breakdown = explainTokens(tokens, commandsDb);

  // Command box
  console.log();
  boxSection(' COMMAND ', [cmd]);

  // Warning box (if dangerous)
  if (hits.length) {
    const warningLines = [
      chalk.yellow.bold('⚠ DANGEROUS COMMAND DETECTED'),
      hits[0].explanation || 'No explanation provided.',
      chalk.red('⚠ DO NOT RUN THIS DIRECTLY'),
    ];
    hits.slice(1).forEach(h => {
      warningLines.push('');
      warningLines.push(h.explanation || 'No explanation provided.');
      if (h.advice) warningLines.push(h.advice);
    });
    console.log();
    boxSection(' WARNING ', warningLines);
  }

  // Command breakdown
  console.log();
  console.log('🔍 Command Breakdown');
  console.log(rule());
  const maxLen = breakdown.reduce((m, [t]) => Math.max(m, t.length), 0);
  breakdown.forEach(([t, expl]) => console.log(`  • ${t.padEnd(maxLen)}  ->  ${expl}`));
  console.log(rule());

  // Copilot suggestion box (if dangerous)
  if (hits.length) {
    console.log();
    const suggestion = await getCopilotSuggestion(cmd);
    const suggestionLines = suggestion.trim().split('\n');
    let suggestionDisplay;
    if (suggestionLines.length) {
      const first = suggestionLines[0].trim().replace(/^`|`$/g, '');
      if (first && !first.startsWith('Why') && !first.startsWith('The')) {
        suggestionDisplay = ['Use: ' + first, ...suggestionLines.slice(1)];
      } else {
        suggestionDisplay = suggestionLines;
      }
    } else {
      suggestionDisplay = [suggestion.trim() || 'No suggestion.'];
    }
    boxSection(' 🤖 Copilot Safer Suggestion ', suggestionDisplay);
  } else {
    console.log(chalk.green('\nNo known dangerous patterns detected.'));
  }
}

async function interactive() {
  const commandsDb = loadJson(path.join(__dirname, 'commands.json'));
  const dangerDb = loadJson(path.join(__dirname, 'danger_patterns.json'));

  await showHeader();

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const question = (q) => new Promise(res => rl.question(q, ans => res(ans)));

  while (true) {
    const cmd = (await question(chalk.cyan("Enter command to analyze (or type 'exit' to quit): "))).trim();
    if (!cmd || cmd.toLowerCase() === 'exit' || cmd.toLowerCase() === 'q') {
      console.log(chalk.green('\nGoodbye.'));
      rl.close();
      return;
    }
    await analyzeCommand(cmd, commandsDb, dangerDb);
    await question('\nPress Enter to analyze another command, or type exit to quit...');
  }
}

async function main() {
  // If a command is provided on argv, analyze once and exit
  const argvCmd = process.argv.slice(2).join(' ');
  if (argvCmd) {
    const commandsDb = loadJson(path.join(__dirname, 'commands.json'));
    const dangerDb = loadJson(path.join(__dirname, 'danger_patterns.json'));
    await showHeader();
    await analyzeCommand(argvCmd, commandsDb, dangerDb);
    return;
  }

  await interactive();
}

main();
