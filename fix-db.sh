#!/usr/bin/env bash
set -euo pipefail
cd /home/eileen/projects/superinstance-api
WR=/home/eileen/.npm-global/bin/wrangler
"$WR" d1 execute superinstance-db --remote -y --command "DROP VIEW IF EXISTS field_budget; DROP TABLE IF EXISTS bookings;" || "$WR" d1 execute superinstance-db --remote --command "DROP VIEW IF EXISTS field_budget; DROP TABLE IF EXISTS bookings;"
"$WR" d1 execute superinstance-db --remote -y --file=schema.sql || "$WR" d1 execute superinstance-db --remote --file=schema.sql
echo "== DB FIXED"
