#!/usr/bin/env bash
# superinstance-api smoke — health, book, near, reflex round-trip, tile round-trip, MCP.
set -euo pipefail
BASE="https://superinstance-api.casey-digennaro.workers.dev"
TOKEN="$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")"
H="Authorization: Bearer $TOKEN"

echo "== health (no auth)"
curl -s "$BASE/health"

echo "== book"
curl -s -X POST "$BASE/book" -H "$H" -H 'content-type: application/json' \
  -d '{"gist":"superinstance-api v1 live — five seams + MCP surface","gamma":42,"eta":7,"books_to":"superinstance-api"}'

echo "== near"
curl -s "$BASE/near?q=five%20seams%20mcp&k=3" -H "$H" | head -c 500; echo

echo "== reflex compile-back"
curl -s -X POST "$BASE/pinch/compile" -H "$H" -H 'content-type: application/json' \
  -d '{"intent":"what is running on the gpu","reflex":"nvidia-smi via /usr/lib/wsl/lib/nvidia-smi","confidence":0.97}'

echo "== pinch (paraphrase — must FIRE or CONFIRM on semantics, not string match)"
curl -s -X POST "$BASE/pinch" -H "$H" -H 'content-type: application/json' \
  -d '{"intent":"show me whats running on the gpu"}'

echo "== tile round-trip"
curl -s -X POST "$BASE/room" -H "$H" -H 'content-type: application/json' -d '{"name":"fleet"}'
curl -s -X POST "$BASE/tile" -H "$H" -H 'content-type: application/json' \
  -d '{"room":"fleet","key":"status","content":"superinstance-api v1 deployed 2026-09-29"}'
curl -s "$BASE/tile?room=fleet&key=status" -H "$H"

echo "== tile demote without receipt (must 400 — honesty pin)"
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/tile/demote" -H "$H" -H 'content-type: application/json' \
  -d '{"room":"fleet","key":"status","to_tier":"gist"}'

echo "== tile demote WITH receipt"
curl -s -X POST "$BASE/tile/demote" -H "$H" -H 'content-type: application/json' \
  -d '{"room":"fleet","key":"status","to_tier":"gist","content":"v1 live","fact_survival":1.0,"lattice_snap":1.0,"method":"smoke"}'

echo "== field"
curl -s "$BASE/field" -H "$H" | head -c 400; echo

echo "== mcp tools/list"
curl -s -X POST "$BASE/mcp" -H "$H" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -c 400; echo

echo "== mcp tools/call near"
curl -s -X POST "$BASE/mcp" -H "$H" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"near","arguments":{"q":"reflex shell","k":2}}}' | head -c 400; echo

echo "== SMOKE DONE"
