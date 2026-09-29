#!/usr/bin/env bash
# superinstance-api deploy — idempotent-ish: creates D1 + Vectorize on first run.
set -euo pipefail
cd "$(dirname "$0")"

# Auth: wrangler stored OAuth (~/.wrangler/config/default.toml) — verified 15:47.
# Do NOT set CLOUDFLARE_API_TOKEN from key.txt: that value fails API verify (6111).
WR="$(command -v wrangler || echo "$HOME/.npm-global/bin/wrangler")"

dbid() {
  "$WR" d1 list --json 2>/dev/null | python3 -c 'import json,sys
try: dbs=json.load(sys.stdin)
except Exception: dbs=[]
print(next((str(d.get("uuid") or d.get("database_id") or "") for d in dbs if d.get("name")=="superinstance-db"), ""))'
}

echo "== D1"
DB_ID="$(dbid)"
if [ -z "$DB_ID" ]; then
  "$WR" d1 create superinstance-db
  DB_ID="$(dbid)"
fi
echo "DB_ID=$DB_ID"
[ -n "$DB_ID" ] || { echo "FATAL: no D1 id"; exit 1; }

python3 - "$DB_ID" <<'PYEOF'
import re, sys
s = open("wrangler.toml").read()
s = re.sub(r'database_id = ".*"', 'database_id = "%s"' % sys.argv[1], s)
open("wrangler.toml", "w").write(s)
print("wrangler.toml patched with", sys.argv[1])
PYEOF

echo "== Vectorize"
if ! "$WR" vectorize list 2>/dev/null | grep -q superinstance-index; then
  "$WR" vectorize create superinstance-index --dimensions 1024 --metric cosine
fi

echo "== dry run"
"$WR" deploy --dry-run

echo "== deploy"
"$WR" deploy

echo "== schema"
"$WR" d1 execute superinstance-db --remote -y --file=schema.sql || "$WR" d1 execute superinstance-db --remote --file=schema.sql

echo "== secret"
SI_TOKEN="$(tr -d '\r\n' < "$HOME/.config/i2i/i2i-token")"
printf 'lucineer:%s' "$SI_TOKEN" | "$WR" secret put SI_API_TOKENS

echo "== DONE"
