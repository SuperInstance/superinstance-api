#!/usr/bin/env python3
"""Lane HY4-TRIAL — targeted head-to-head on Surface 3 (provider prompt-cache economics).

Hy4-preview vs Hy3, SAME standing expert system prompt, SAME Surface-3 expansion brief.
One model per continued thread (cache doctrine practiced). List-form subprocess only.
Key read at use-time from /home/eileen/.config/deepinfra/token; never logged/echoed/written.
"""
import json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hy3_lane_cache as H  # reuse SYSTEM verbatim

MODEL = "tencent/Hy4-preview"
ENDPOINT = "https://api.deepinfra.com/v1/openai/chat/completions"
STATE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs",
                                     "_hy4_trial_state.json"))


def call(messages, max_tokens=6000, temperature=0.6):
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Authorization": "Bearer " + H._key(),
                 "Content-Type": "application/json"},
    )
    delays = [30, 60, 90, 120, 180, 240]
    for attempt in range(len(delays) + 1):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == len(delays):
                raise
            ra = e.headers.get("Retry-After")
            wait = int(ra) if (ra and ra.isdigit()) else delays[attempt]
            print(f"[429] backing off {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
    msg = d["choices"][0]["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
    return content, reasoning, d.get("usage", {})


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"messages": [{"role": "system", "content": H.SYSTEM}],
            "calls": 0, "log": []}


def save(st):
    with open(STATE, "w") as f:
        json.dump(st, f, indent=1)


def turn(st, user_msg, tag, max_tokens=6000, temperature=0.6):
    st["messages"].append({"role": "user", "content": user_msg})
    content, reasoning, usage = call(st["messages"], max_tokens, temperature)
    st["messages"].append({"role": "assistant", "content": content})
    st["calls"] += 1
    ptd = usage.get("prompt_tokens_details", {}) or {}
    st["log"].append({"tag": tag, "usage": usage, "chars": len(content),
                      "reasoning_chars": len(reasoning)})
    save(st)
    print("\n" + "=" * 78)
    print(f"### {tag}  (call {st['calls']}, model={MODEL}, "
          f"in={usage.get('prompt_tokens')} cached={ptd.get('cached_tokens')} "
          f"out={usage.get('completion_tokens')} reasoning={len(reasoning)}c)")
    print("=" * 78)
    print(content)
    if reasoning:
        print("\n--- [reasoning_content] ---")
        print(reasoning[:4000])
    return content


SURFACE3 = """SURFACE 3 — PROVIDER PROMPT-CACHE ECONOMICS (the one we can measure TODAY).

Fleet runs expert lanes against DeepInfra / DeepSeek / z.ai (OpenAI-compatible
/chat/completions). Provider prompt caches are cheap on LONG threads: the API
returns usage.prompt_tokens_details.cached_tokens. Our doctrine: "ONE MODEL PER
EXPERT THREAD" — keep one continued message array so context carries and prefix
cache stays hot; vs rotating seat mid-thread (kills the prefix) vs lane rotation
(fresh thread per lane = cold).

Evidence: XP-C found that byte-identity at fixed seed is a property of the WHOLE
SERVING STACK IN A GIVEN WINDOW, not the model — co-tenancy on the 4050 flipped
tokens; "replay-sensitive lanes must serialize the seat or pin determinism per
cache/window state." So a serving window is itself a cache-coherence domain.

Give 8-12 RAW IDEAS on: measuring real cache-hit-rate/price per lane; when to
KEEP a warm thread vs start fresh (context rot vs cache savings); lane-rotation
vs mid-thread-rotation policy; treating the serving window as a coherence epoch;
how cached-context interacts with determinism claims; what receipts to book
(cached_tokens, gamma/eta). Each: mechanism + how it fails (cache stale prefix
giving confidently wrong answers; cost illusion). Dense, numbered."""

AUDIT = """SELF-AUDIT (no new ideas needed). List EVERY factual platform claim you made above
about DeepInfra pricing, prompt-cache behavior, cache-retention windows, Cloudflare
D1/Vectorize/KV quotas, or the schema columns. For each: (a) the exact claim as you
stated it, (b) your confidence 0-100, (c) the source you are relying on
(spec / docs / inference / guess). If you asserted a number you cannot source, say so
plainly. Be adversarial about your own numbers."""

REDTEAM = """RED-TEAM your own Surface-3 list. (1) Which of your 8-12 ideas is WEAKEST and
why? (2) Name a HIDDEN cross-idea dependency that could break in production.
(3) What question did you NOT answer that the brief asked? (4) Name one idea you
considered and rejected — why? Dense."""

if __name__ == "__main__":
    st = load()
    turn(st, SURFACE3, "HY4.R1.3-provider-prompt-cache")
    turn(st, AUDIT, "HY4.R2-fact-self-audit")
    turn(st, REDTEAM, "HY4.R4-redteam")
    print("\n[state]", STATE, "calls:", st["calls"])
