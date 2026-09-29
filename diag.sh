#!/usr/bin/env bash
cd /home/eileen/projects/superinstance-api
echo "wrangler in path: $(command -v wrangler)"
ls -la "$HOME/.npm-global/bin/wrangler" 2>&1 | head -2
LINE="$(grep -m1 '^CF_API_TOKEN=' /mnt/c/Users/casey/key.txt | tr -d '\r')"
echo "token line chars: ${#LINE}"
export CLOUDFLARE_API_TOKEN="${LINE#CF_API_TOKEN=}"
echo "token length: ${#CLOUDFLARE_API_TOKEN}"
WR="$(command -v wrangler || echo "$HOME/.npm-global/bin/wrangler")"
echo "WR=$WR"
"$WR" --version 2>&1 | head -3
"$WR" d1 list --json 2>&1 | head -20
echo "EXIT=$?"
