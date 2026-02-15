#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const readline = require('readline');

let chalk;
try {
  // Try requiring chalk and support both CJS and ESM interop shapes
  const _chalk = require('chalk');
  if (_chalk && typeof _chalk.cyan === 'function') {
    chalk = _chalk;
  } else if (_chalk && _chalk.default && typeof _chalk.default.cyan === 'function') {
    chalk = _chalk.default;
  } else {
    throw new Error('chalk API not available');
  }
} catch (e) {
  // Minimal fallback if chalk is not installed or incompatible
  chalk = {
    cyan: (s) => s,
    yellow: (s) => s,
    red: (s) => s,
    green: (s) => s,
    bold: (s) => s,
  };
}

const loadJson = (p) => {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    console.error(chalk.red(`Error: failed to load ${p}: ${e.message}`));
    process.exit(2);
  }
};

function parseCommand(input) {
  // Simple tokenizer that respects double quotes
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
      execFile(copilotPath, [prompt], { timeout }, (err, stdout, stderr) => {
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

async function runInteractive() {
  const commandsDb = loadJson(path.join(__dirname, 'commands.json'));
  const dangerDb = loadJson(path.join(__dirname, 'danger_patterns.json'));

  console.log(chalk.bold(chalk.cyan('Cosmic SafeCLI — Understand Before You Execute')));

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const question = (q) => new Promise(res => rl.question(q, answer => res(answer)));

  const input = (process.argv[2]) ? process.argv.slice(2).join(' ') : await question('Enter command to analyze: ');
  const cmd = input.trim();
  if (!cmd) {
    console.log('No command provided.');
    rl.close();
    return;
  }

  const tokens = parseCommand(cmd);
  const breakdown = explainTokens(tokens, commandsDb);

  console.log('\nBreakdown:');
  const maxLen = breakdown.reduce((m, [t]) => Math.max(m, t.length), 0);
  breakdown.forEach(([t, expl]) => {
    console.log(`  ${t.padEnd(maxLen)} -> ${expl}`);
  });

  const hits = detectDanger(cmd, dangerDb);
  if (hits.length) {
    console.log('\n' + chalk.yellow.bold('⚠ DANGEROUS COMMAND'));
    console.log(chalk.red('⚠ DO NOT RUN THIS DIRECTLY'));
    hits.forEach(h => {
      console.log(`\nWhy: ${h.explanation || 'No explanation provided.'}`);
      if (h.advice) console.log(`Safer advice: ${h.advice}`);
    });

    console.log('\n' + chalk.cyan.bold('🤖 Copilot Suggested Safer Alternative'));
    const suggestion = await getCopilotSuggestion(cmd);
    console.log(suggestion);

    const proceed = (await question('\nExecute suggested command? (y/N): ')).trim().toLowerCase();
    if (['y', 'yes'].includes(proceed)) {
      let execCmd = (await question('Enter command to execute (leave empty to use Copilot suggestion): ')).trim();
      if (!execCmd) {
        execCmd = suggestion.split('\n').map(l => l.trim().replace(/^`|`$/g, '')).find(l => l);
      }
      if (!execCmd) {
        console.log('No command to execute. Aborting.');
      } else {
        console.log(`Running: ${execCmd}`);
        try {
          execFile(execCmd, { shell: true }, (err, stdout, stderr) => {
            if (stdout) console.log('\n--- STDOUT ---\n' + stdout);
            if (stderr) console.log('\n--- STDERR ---\n' + stderr);
            if (err) console.error(chalk.red(`Failed to execute: ${err.message}`));
            rl.close();
          });
          return;
        } catch (e) {
          console.error(chalk.red(`Failed to execute command: ${e.message}`));
        }
      }
    } else {
      console.log('Not executing suggested command.');
    }
  } else {
    console.log('\n' + chalk.green('No known dangerous patterns detected.'));
  }

  rl.close();
}

runInteractive();
