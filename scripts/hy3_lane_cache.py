#!/usr/bin/env python3
"""Lane HY3-CACHE — curated dog-fooding of tencent/Hy3 as a caching expert seat.

Runner (deepseek) curates; EXPERT (tencent/Hy3 via DeepInfra OpenAI-compatible API)
expands and designs. One model per expert thread: a single continued message array
(context carries), never re-seeded per turn (our cache-economics doctrine, practiced).

List-form subprocess only. Key read at use-time, never logged/written to an artifact.
"""
import json, os, sys, urllib.request

MODEL = "tencent/Hy3"
ENDPOINT = "https://api.deepinfra.com/v1/openai/chat/completions"
STATE = os.path.join(os.path.dirname(__file__), "..", "docs", "_hy3_lane_state.json")
STATE = os.path.abspath(STATE)


def _key():
    p = "/home/eileen/.config/deepinfra/token"
    if os.path.exists(p):
        with open(p) as f:
            k = f.read().strip()
            if k:
                return k
    # fallback: DEEPINFRA_KEY line in key.txt
    with open("/mnt/c/Users/casey/key.txt") as f:
        for line in f:
            if "DEEPINFRA_KEY" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no deepinfra key")


def call(messages, max_tokens=2600, temperature=0.6):
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": "Bearer " + _key(),
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    msg = d["choices"][0]["message"]
    u = d.get("usage", {})
    return msg.get("content") or "", u


SYSTEM = """You are the CACHING-DOMAIN EXPERT SEAT for a FLEET CONTEXT-BRAIN.

Environment (be concrete about THIS stack, never generic): a Cloudflare Worker
"superinstance-api" exposing MCP tools, backed by D1 (SQL: rooms/tiles/tile_versions/
demotion_receipts/bookings/intents), Vectorize (bge-m3 embeddings, /near semantic
recall), Workers KV (available but barely used), and a local RTX 4050 (6 GB WSL2,
~2.2 GB free seat; measured co-tenancy + serving-window non-determinism).

Fleet doctrine:
- "Not looking for the best — looking for WHAT IS PREFERRED WHEN." A cache is a
  statement of preference over time, not a truth store. Every caching decision is
  a bet on which future accesses matter; name the bet.
- TAPESTRY DOCTRINE: every idea states its FAILURE MODE first-class. Negative
  results are content. A cache that silently serves stale/wrong answers is worse
  than no cache. Name the failure, the detection, and the escape.
- Caches must be HONEST: a hit is a claim; the receipt (why this hit, what it
  supersedes, coherence window) is part of the answer.
- Prefer CF free-tier buildable + D1/Vectorize/KV. Local GPU only where a real
  probe is possible.
- Keep layers distinct: authority (tiles), meaning (vectors), reflex (intents),
  field (gamma/eta: gamma=compute cost, eta=surprise vs vector neighborhood),
  growth (quilt-dba staged cells). A cache decision must say which seam it lives on.

Output discipline: dense, structured, no preamble. Numbered ideas. For each:
MECHANISM (how it works, with the actual key/table/index), and HOW IT FAILS
(the concrete stale/thrash/poison/coherence failure + how you'd detect it).
You are allowed to say "this is a bad idea because..." — that is content.
"""


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"messages": [{"role": "system", "content": SYSTEM}], "calls": 0, "log": []}


def save(st):
    with open(STATE, "w") as f:
        json.dump(st, f, indent=1)


def turn(st, user_msg, tag, max_tokens=2600, temperature=0.6):
    st["messages"].append({"role": "user", "content": user_msg})
    content, usage = call(st["messages"], max_tokens, temperature)
    st["messages"].append({"role": "assistant", "content": content})
    st["calls"] += 1
    st["log"].append({"tag": tag, "usage": usage, "chars": len(content)})
    save(st)
    print("\n" + "=" * 78)
    print(f"### {tag}  (call {st['calls']}, in={usage.get('prompt_tokens')} "
          f"cached={usage.get('prompt_tokens_details',{}).get('cached_tokens')} "
          f"out={usage.get('completion_tokens')})")
    print("=" * 78)
    print(content)
    return content
