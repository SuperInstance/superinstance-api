#!/usr/bin/env bash
cd /home/eileen/projects/superinstance-api
RAW="$(grep -m1 '^CF_API_TOKEN=' /mnt/c/Users/casey/key.txt | cut -d= -f2- | tr -d '\r\n')"
CLEAN="$(printf '%s' "$RAW" | python3 -c 'import sys,re; print(re.sub(r"[\"\x27\s]", "", sys.stdin.read()))')"
echo "raw length: ${#RAW}   clean length: ${#CLEAN}"
echo "== whoami WITHOUT env token (stored OAuth from earlier today?)"
/home/eileen/.npm-global/bin/wrangler whoami 2>&1 | head -6
echo "== whoami WITH sanitized token"
CLOUDFLARE_API_TOKEN="$CLEAN" /home/eileen/.npm-global/bin/wrangler whoami 2>&1 | head -6
