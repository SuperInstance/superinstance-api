#!/usr/bin/env bash
set -euo pipefail
BASE="https://superinstance-api.casey-digennaro.workers.dev"
TOKEN="$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")"
H="Authorization: Bearer $TOKEN"
echo "== book (full response — embedded + gamma/eta)"
curl -s -X POST "$BASE/book" -H "$H" -H 'content-type: application/json' \
  -d '{"gist":"superinstance-api v1 verified: tiles, meaning, reflex, field, growth seams green","gamma":60,"eta":5,"books_to":"superinstance-api"}'
echo "== pinch (paraphrase of compiled reflex — expect FIRE or CONFIRM)"
curl -s -X POST "$BASE/pinch" -H "$H" -H 'content-type: application/json' \
  -d '{"intent":"show me whats running on the gpu"}'
echo "== near (should find both bookings now)"
curl -s "$BASE/near?q=verified%20seams%20green&k=5" -H "$H" | python3 -c 'import json,sys
d=json.load(sys.stdin)
print("eta_measured:", d["eta_measured"])
for m in d["matches"]:
    b = m.get("booking")
    print(" ", m["id"][:16], m.get("kind"), round(m["score"],3), (b or {}).get("gist","")[:40])'
sleep 8
echo "== pinch again (post-propagation recheck)"
curl -s -X POST "$BASE/pinch" -H "$H" -H 'content-type: application/json' \
  -d '{"intent":"display the gpu processes"}'
