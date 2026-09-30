#!/usr/bin/env bash
set -euo pipefail
cd /home/eileen/projects/superinstance-api
node --check src/worker.js && echo SYNTAX_OK
python3 -m py_compile scripts/lever_bridge.py && echo PY_OK
bash deploy.sh 2>&1 | grep -E "Deployed|Current Version|ERROR" | head -4
TOK="$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")"
BASE="https://superinstance-api.casey-digennaro.workers.dev"
echo "== /intents (new endpoint)"
curl -s "$BASE/intents?limit=3" -H "Authorization: Bearer $TOK" | head -c 500; echo
echo "== /pinch still fires"
curl -s -X POST "$BASE/pinch" -H "Authorization: Bearer $TOK" -H 'content-type: application/json' \
  -d '{"intent":"show me whats running on the gpu"}' | head -c 220; echo
echo "== MCP tool count"
curl -s -X POST "$BASE/mcp" -H "Authorization: Bearer $TOK" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":9,"method":"tools/list"}' | python3 -c 'import json,sys
d=json.load(sys.stdin)
names=[t["name"] for t in d["result"]["tools"]]
print("tools:", len(names), names[-4:])'
git add -A && git commit -q -m "intents endpoint + intents_list MCP tool; lever-runner bridge; client configs

- GET /intents?limit= and MCP intents_list: fleet reflex inventory for local runners
- scripts/lever_bridge.py: fleet pinch <-> local lever-runner (teach once, run forever)
- clients/README.md: Claude Code, OpenCode, OpenClaw (streamable-http), curl
- README: lever-runner synergy section" && git push -q && echo PUSHED
