# clients/ — connecting any agent to the fleet brain

One API, one token, every agent. Replace `<TOKEN>` with the value from
`~/.config/i2i/i2i-token` (read at use-time — never commit it, never echo it).

Base URL: `https://superinstance-api.casey-digennaro.workers.dev`
MCP endpoint: `/mcp` (JSON-RPC 2.0 over Streamable HTTP)
Tools: book, near, since, room_create, room_list, tile_write, tile_get,
tile_history, tile_demote, pinch, pinch_compile, intents_list, field_query,
witness_get (14)

---

## Claude Code

```bash
claude mcp add --transport http superinstance \
  https://superinstance-api.casey-digennaro.workers.dev/mcp \
  --header "Authorization: Bearer $(cat ~/.config/i2i/i2i-token)"
```

Or project-scoped `.mcp.json`:

```json
{
  "mcpServers": {
    "superinstance": {
      "type": "http",
      "url": "https://superinstance-api.casey-digennaro.workers.dev/mcp",
      "headers": { "Authorization": "Bearer ${SI_TOKEN}" }
    }
  }
}
```

## OpenCode

`opencode.json`:

```json
{
  "mcp": {
    "superinstance": {
      "type": "remote",
      "url": "https://superinstance-api.casey-digennaro.workers.dev/mcp",
      "headers": { "Authorization": "Bearer <TOKEN>" },
      "enabled": true
    }
  }
}
```

## OpenClaw

Config shape (`~/.openclaw/config.json` → `mcp.servers`), or via CLI:

```bash
openclaw mcp set superinstance '{"url":"https://superinstance-api.casey-digennaro.workers.dev/mcp","transport":"streamable-http","headers":{"Authorization":"Bearer <TOKEN>"}}'
openclaw mcp status --verbose   # verifies resolved transport + headers
```

```json
{
  "mcp": {
    "servers": {
      "superinstance": {
        "url": "https://superinstance-api.casey-digennaro.workers.dev/mcp",
        "transport": "streamable-http",
        "timeout": 20,
        "headers": { "Authorization": "Bearer <TOKEN>" }
      }
    }
  }
}
```

## Anything else (curl / scripts)

No MCP required — the REST surface is the same brain:

```bash
TOK=$(cat ~/.config/i2i/i2i-token)
BASE=https://superinstance-api.casey-digennaro.workers.dev

curl -s -X POST $BASE/book -H "Authorization: Bearer $TOK" -H 'content-type: application/json' \
  -d '{"gist":"<finding>","receipt_url":"<url>","books_to":"<lane>"}'

curl -s "$BASE/near?q=<topic>&k=5" -H "Authorization: Bearer $TOK"

curl -s -X POST $BASE/pinch -H "Authorization: Bearer $TOK" -H 'content-type: application/json' \
  -d '{"intent":"<intent>"}'
```

## Local reflex layer (lever-runner)

`scripts/lever_bridge.py` joins the fleet reflex with a local
[lever-runner](https://github.com/SuperInstance/lever-runner) HTTP API
(`127.0.0.1:8765`):

```bash
python3 scripts/lever_bridge.py "check disk usage"   # fleet pinch -> local lever -> compile back
python3 scripts/lever_bridge.py --pull-fleet         # fleet reflexes -> your local shell
python3 scripts/lever_bridge.py --push-local         # your local levers -> the fleet
```

Exit codes: `0` resolved, `2` needs confirmation, `1` unknown to both layers.

## Token hygiene

- One token per agent is the target (`SI_API_TOKENS="lucineer:tok,claude:tok,..."` — the
  token's agent name attributes every booking).
- Tokens live in files/env at use-time. They never enter chat, memory, git, or logs.
