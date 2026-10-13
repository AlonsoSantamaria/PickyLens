// No-inference compatibility probe against an explicitly supplied installed bundle.
import {pathToFileURL} from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const bundle = process.argv[2];
if (!bundle) throw new Error('Supply the installed Gemini core bundle path');
const {HookRegistry, HookRunner} = await import(pathToFileURL(path.resolve(bundle)));
const root = process.cwd();
const extension = path.join(root, 'extensions/pickylens');
const hooks = JSON.parse(fs.readFileSync(path.join(extension, 'hooks/hooks.json'), 'utf8')).hooks;
for (const definitions of Object.values(hooks)) {
  for (const definition of definitions) for (const hook of definition.hooks) {
    hook.command = hook.command.replaceAll('${extensionPath}', extension);
    // Explicitly disable local .env loading and credentials for this probe.
    hook.env = {PICKYLENS_ENV: 'test', OPENAI_API_KEY: '',
      PICKYLENS_GEMINI_DB_PATH: path.join(root, 'work/gemini-protocol-probe.sqlite3')};
  }
}
const config = {
  isTrustedFolder: () => false, getHooks: () => undefined, getDisabledHooks: () => [],
  getExtensions: () => [{isActive: true, hooks}],
  sanitizationConfig: {}, storage: {getPlansDir: () => path.join(root, 'work')}
};
const registry = new HookRegistry(config);
await registry.initialize();
const entries = registry.getAllHooks();
if (entries.length !== 2) throw new Error('Expected exactly two registered hooks');
const runner = new HookRunner(config);
const report = [];
for (const entry of entries) {
  const input = {session_id: 'protocol-' + process.pid, cwd: root, transcript_path: '',
    timestamp: new Date().toISOString(), hook_event_name: entry.eventName,
    prompt: 'Compare the costs.', prompt_response: 'A costs 5; B costs 8.', stop_hook_active: false};
  const result = await runner.executeHook(entry.config, entry.eventName, input);
  if (!result.success || result.exitCode !== 0 || result.output?.decision !== 'allow' ||
      !result.output?.systemMessage?.includes('PickyLens')) {
    throw new Error('Advisory hook transport failed: ' + JSON.stringify({success: result.success,
      exitCode: result.exitCode, error: result.error?.message}));
  }
  report.push({event: entry.eventName, name: entry.config.name, source: entry.source,
    success: result.success, exitCode: result.exitCode, decision: result.output.decision,
    message: result.output.systemMessage});
}
console.log(JSON.stringify({inferenceCalls: 0, registeredHooks: report}, null, 2));
