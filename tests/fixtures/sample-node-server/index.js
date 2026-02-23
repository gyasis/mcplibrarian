#!/usr/bin/env node
// Minimal stub MCP server for testing — no SDK dependency required
process.stdin.setEncoding('utf8');
let buffer = '';

process.stdin.on('data', (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const msg = JSON.parse(line);
      let response;
      if (msg.method === 'initialize') {
        response = {
          jsonrpc: '2.0', id: msg.id,
          result: {
            protocolVersion: '2024-11-05',
            capabilities: { tools: {} },
            serverInfo: { name: 'sample-node-server', version: '1.0.0' }
          }
        };
      } else if (msg.method === 'tools/list') {
        response = { jsonrpc: '2.0', id: msg.id, result: { tools: [] } };
      } else {
        response = { jsonrpc: '2.0', id: msg.id, result: {} };
      }
      process.stdout.write(JSON.stringify(response) + '\n');
    } catch (_) {}
  }
});

process.stdin.on('end', () => process.exit(0));
