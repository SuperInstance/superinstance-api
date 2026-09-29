#!/usr/bin/env bash
set -euo pipefail
BASE="https://superinstance-api.casey-digennaro.workers.dev"
TOKEN="$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")"
H="Authorization: Bearer $TOKEN"
echo "== near (minutes after book)"
curl -s "$BASE/near?q=five%20seams%20mcp&k=3" -H "$H" | head -c 600; echo
echo "== pinch (minutes after compile-back)"
curl -s -X POST "$BASE/pinch" -H "$H" -H 'content-type: application/json' \
  -d '{"intent":"show me whats running on the gpu"}'
echo "== unfiltered near on the intent text (filter-bug probe)"
curl -s "$BASE/near?q=what%20is%20running%20on%20the%20gpu&k=5" -H "$H" | python3 -c 'import json,sys
d=json.load(sys.stdin)
print("matches:", [(m["id"][:16], m.get("kind"), round(m["score"],3)) for m in d["matches"]])'
