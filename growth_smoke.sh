#!/usr/bin/env bash
# superinstance-api growth-seam smoke — canon cells + stage-advance receipts.
# Repo test law: node --check + curl smoke (see smoke.sh / verify_push.sh).
# Usage: ./growth_smoke.sh                     (against LIVE)
#        BASE=http://127.0.0.1:8787 TOKEN=xxx ./growth_smoke.sh   (local wrangler dev)
# Note: local wrangler dev cannot run Vectorize ("needs to be run remotely");
# cells then report embedded:false — the growth logic itself is fully testable.
set -euo pipefail
BASE="${BASE:-https://superinstance-api.casey-digennaro.workers.dev}"
TOKEN="${TOKEN:-$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")}"
H="Authorization: Bearer $TOKEN"
CT='content-type: application/json'
FAILS=0

say() { echo "== $*"; }
# jcheck <label> <body-json> <python statements using d>; end with sys.exit(...)
jcheck() {
  if J="$2" python3 -c '
import json, os, sys
d = json.loads(os.environ["J"])
'"$3"'
sys.exit(1)
'; then
    echo "PASS: $1"
  else
    echo "FAIL: $1"; FAILS=$((FAILS+1))
  fi
}
check() { # check <label> <python-expr>
  if python3 -c "import sys; sys.exit(0 if ($2) else 1)"; then echo "PASS: $1"; else echo "FAIL: $1"; FAILS=$((FAILS+1)); fi
}
req() { # req <method> <path> [json-body] -> body (multi-line) + status on last line
  local m=$1 p=$2 b=${3:-}
  if [ -n "$b" ]; then
    curl -s -w '\n%{http_code}\n' -X "$m" "$BASE$p" -H "$H" -H "$CT" -d "$b"
  else
    curl -s -w '\n%{http_code}\n' -X "$m" "$BASE$p" -H "$H"
  fi
}
body() { sed '$d'; }
code() { tail -n1 | tr -d '[:space:]'; }

cd "$(dirname "$0")"
node --check src/worker.js && say "syntax OK"

ROOM="growth-smoke-$(date +%s)"
say "room: $ROOM"

say "room create"
R=$(req POST /room "{\"name\":\"$ROOM\"}")
check "room create 200" "$(printf '%s' "$R" | code) == 200"
jcheck "room created stage 1" "$(printf '%s' "$R" | body)" \
  'sys.exit(0 if d.get("room",{}).get("stage")==1 else 1)'

say "PUT cell 1 (advance 1->2)"
R=$(req PUT "/rooms/$ROOM/cells" '{"title":"genesis","body":"the first canon cell"}')
C1=$(printf '%s' "$R" | body); S1=$(printf '%s' "$R" | code)
check "cell1 200" "$S1 == 200"
jcheck "cell1 advance 1->2 receipted {room,from,to,cell_id,ts,agent}" "$C1" \
  'sys.exit(0 if d["ok"] and d["stage_advance"]["from_stage"]==1 and d["stage_advance"]["to_stage"]==2 and d["stage_advance"]["cell_id"]==d["cell"]["id"] and "ts" in d["stage_advance"] and "agent" in d["stage_advance"] and d["cell"]["stage"]==2 else 1)'

say "PUT cell 2 by numeric room id (advance 2->3)"
RID=$(curl -s "$BASE/rooms" -H "$H" | python3 -c "import json,sys; rs=json.load(sys.stdin)['rooms']; print(next(r['id'] for r in rs if r['name']=='$ROOM'))")
R=$(req PUT "/rooms/$RID/cells" '{"title":"second","body":"another canon cell"}')
C2=$(printf '%s' "$R" | body); S2=$(printf '%s' "$R" | code)
check "cell2 (by id) 200" "$S2 == 200"
jcheck "cell2 advance 2->3 (addressed by numeric id)" "$C2" \
  'sys.exit(0 if d["stage_advance"]["from_stage"]==2 and d["stage_advance"]["to_stage"]==3 and d["room"]=="'"$ROOM"'" else 1)'

say "duplicate title must 409 and NOT advance"
R=$(req PUT "/rooms/$ROOM/cells" '{"title":"genesis","body":"retry should be rejected"}')
check "duplicate 409" "$(printf '%s' "$R" | code) == 409"
R=$(req GET "/rooms/$ROOM/cells")
L=$(printf '%s' "$R" | body)
jcheck "stage still 3 after dup, 2 cells, 2 contiguous receipts, unique cell_ids" "$L" \
  'sys.exit(0 if d["stage"]==3 and len(d["cells"])==2 and len(d["receipts"])==2 and d["receipts"][0]["from_stage"]==1 and d["receipts"][0]["to_stage"]==2 and d["receipts"][1]["from_stage"]==2 and d["receipts"][1]["to_stage"]==3 and d["receipts"][0]["cell_id"]!=d["receipts"][1]["cell_id"] and all("agent" in r and "ts" in r for r in d["receipts"]) else 1)'

say "unknown room must 404"
R=$(req PUT "/rooms/no-such-room-$ROOM/cells" '{"title":"x"}')
check "unknown room 404" "$(printf '%s' "$R" | code) == 404"

say "unauthorized must 401"
R=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$BASE/rooms/$ROOM/cells" -H "$CT" -d '{"title":"x"}')
check "no token 401" "$R == 401"

say "MCP tools/list honesty (cell_add, cells_list present)"
R=$(curl -s -X POST "$BASE/mcp" -H "$H" -H "$CT" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}')
jcheck "mcp has both growth tools" "$R" \
  'ns=[t["name"] for t in d["result"]["tools"]]
sys.exit(0 if ("cell_add" in ns and "cells_list" in ns) else 1)'
NTOOLS=$(J="$R" python3 -c 'import json,os; print(len(json.loads(os.environ["J"])["result"]["tools"]))')
echo "   tool count: $NTOOLS"

say "MCP tools/call cell_add + cells_list round-trip"
R=$(curl -s -X POST "$BASE/mcp" -H "$H" -H "$CT" -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"cell_add\",\"arguments\":{\"room\":\"$ROOM\",\"title\":\"mcp-cell\",\"body\":\"grown via mcp\"}}}")
jcheck "mcp cell_add ok + advance 3->4, agent from token" "$R" \
  'c=json.loads(d["result"]["content"][0]["text"])
sys.exit(0 if (c["ok"] and c["stage_advance"]["from_stage"]==3 and c["stage_advance"]["to_stage"]==4 and c["stage_advance"]["agent"]=="smoke") else 1)'
R=$(curl -s -X POST "$BASE/mcp" -H "$H" -H "$CT" -d "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"cells_list\",\"arguments\":{\"room\":\"$ROOM\"}}}")
jcheck "mcp cells_list 3 cells stage 4" "$R" \
  'c=json.loads(d["result"]["content"][0]["text"])
sys.exit(0 if (c["stage"]==4 and len(c["cells"])==3 and len(c["receipts"])==3) else 1)'

echo
if [ "$FAILS" -eq 0 ]; then echo "GROWTH SMOKE: ALL PASS"; else echo "GROWTH SMOKE: $FAILS FAILURES"; exit 1; fi
