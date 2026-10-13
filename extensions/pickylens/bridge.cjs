// Process transport only; all review behavior lives in Python services.
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const fallback = () => JSON.stringify({decision: 'allow', systemMessage: 'PickyLens review unavailable. Gemini may continue unchanged; no retry was requested.'});
try {
  const input = fs.readFileSync(0, 'utf8');
  if (Buffer.byteLength(input) > 1300000) throw new Error('input limit');
  const result = spawnSync(python, ['-X', 'utf8', '-m', 'app.adapters.gemini', 'hook'], {
    cwd: root, input, encoding: 'utf8', timeout: 50000, maxBuffer: 2000000,
    windowsHide: true, shell: false, env: process.env
  });
  const output = JSON.parse(result.stdout || '{}');
  if (result.status !== 0 || output.decision !== 'allow' || typeof output.systemMessage !== 'string') throw new Error('protocol');
  // Whitelist output fields so no accidental retry/context control can escape.
  process.stdout.write(JSON.stringify({decision: 'allow', systemMessage: output.systemMessage}));
} catch {
  process.stdout.write(fallback());
}
