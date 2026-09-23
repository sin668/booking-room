#!/usr/bin/env node
// SessionStart hook: prefetch scoped ai-memory knowledge from the remote MCP.
const REMOTE = process.env.AI_MEMORY_URL || 'http://8.129.17.71:49374/mcp';
const SCOPE = { project: process.env.AI_MEMORY_PROJECT || 'booking-room', workspace: 'default' };

async function callTool(name, args) {
  const res = await fetch(REMOTE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }),
    signal: AbortSignal.timeout(6000),
  });
  const text = await res.text();
  const line = text.startsWith('{') ? text : (text.match(/^data: (.*)$/m) || [])[1];
  const msg = JSON.parse(line);
  if (!msg.result || msg.result.isError) return null;
  return JSON.parse(msg.result.content[0].text);
}

function dedup(hits) {
  const seen = new Set();
  return hits.filter((h) => !seen.has(h.path) && seen.add(h.path));
}

// FTS5 stores a CJK sentence as one token, so exact multi-char runs never match.
// Chunk into short non-overlapping terms and OR them; single CJK terms alone never match either.
function buildQuery(prompt) {
  const terms = [];
  const add = (t) => { if (t && t.length >= 2 && !terms.includes(t)) terms.push(t); };
  for (const w of prompt.split(/[\s,，。、；;：:!！?？()（）「」“”"'`\/\\|]+/)) {
    const runs = w.match(/[一-龥]{2,}|[^\s一-龥]{2,}/g) || [];
    for (const run of runs) {
      if (/^[一-龥]/.test(run)) for (let i = 0; i + 2 < run.length + 1; i += 3) add(run.slice(i, i + 3));
      else add(run);
    }
  }
  return terms.slice(0, 8).join(' OR ') || '项目 决策 规范';
}

async function search(query) {
  const [scoped, globalRes] = await Promise.all([
    callTool('memory_query', { query, limit: 6, ...SCOPE }).catch(() => null),
    callTool('memory_query', { query, limit: 6, global: true }).catch(() => null),
  ]);
  return dedup([...(scoped?.hits || []), ...(globalRes?.global_hits || [])].filter(
    (h) => !h.project_name || (h.project_name === SCOPE.project && h.workspace_name === SCOPE.workspace)
  ));
}

async function main() {
  let stdin = '';
  for await (const chunk of process.stdin) stdin += chunk;
  let prompt = '';
  try { prompt = (JSON.parse(stdin).prompt || '').trim(); } catch {}

  let hits = [];
  if (prompt) hits = (await search(buildQuery(prompt.slice(0, 200)))).slice(0, 8);
  if (!hits.length) hits = (await search('项目 决策 规范 pitfall 运行环境')).slice(0, 5);
  if (!hits.length) return;

  const lines = hits.map((h) => `- **${h.title}** (\`${h.path}\`)：${(h.snippet || '').replace(/<\/?mark>/g, '').replace(/\s+/g, ' ').slice(0, 160)}`);
  const context = [
    `## ai-memory 预检索（project=${SCOPE.project}，远端 ${REMOTE}）`,
    `与本次请求相关的历史记忆（已带作用域检索，需要全文时用 memory_read_page 并显式传 ${JSON.stringify(SCOPE)}）：`,
    ...lines,
  ].join('\n');
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: context } }));
}

main().catch(() => process.exit(0));
