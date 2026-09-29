#!/usr/bin/env bash
cd /home/eileen/projects/superinstance-api
export CLOUDFLARE_API_TOKEN="$(grep -m1 '^CF_API_TOKEN=' /mnt/c/Users/casey/key.txt | cut -d= -f2- | tr -d '\r\n')"
echo "token length: ${#CLOUDFLARE_API_TOKEN}"
out="$(/home/eileen/.npm-global/bin/wrangler d1 list --json 2>&1)"; rc=$?
echo "RC=$rc"
echo "----- raw output -----"
echo "$out" | head -40
