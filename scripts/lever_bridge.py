#!/usr/bin/env python3
"""lever_bridge — join the fleet reflex (superinstance-api) with the local
trust compiler (lever-runner). Teach once, run forever; the fleet keeps the
shell.

Two reflex layers, one doctrine:
  fleet  /pinch        shared knowledge, cross-agent, zero LLM
  local  lever /run    this machine's taught commands, sandboxed, zero LLM

Flow for a single intent:
  1. POST {SI}/pinch {intent}
  2. FIRE      -> print reflex (exit 0)          # fleet already knows
  3. CONFIRM   -> print candidate + score (exit 2)
  4. ESCALATE  -> ask local lever (POST {LEVER}/run)
        lever resolves -> compile back to the fleet (POST {SI}/pinch/compile),
                          print command, exit 0
        lever unknown  -> print ESCALATE, exit 1  # thinking layer required

Sync modes:
  --pull-fleet   fleet /intents -> lever /teach (fleet knowledge in your shell)
  --push-local   lever export   -> fleet /pinch/compile (your shell in the fleet)

Auth: fleet token read at use-time from ~/.config/i2i/i2i-token (or $SI_TOKEN).
      lever token from $LEVER_TOKEN if the local API was started with one.
Never prints token values. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

SI = os.environ.get("SI_BASE", "https://superinstance-api.casey-digennaro.workers.dev")
LEVER = os.environ.get("LEVER_BASE", "http://127.0.0.1:8765")


def si_token() -> str:
    tok = os.environ.get("SI_TOKEN")
    if tok:
        return tok.strip()
    path = os.path.expanduser("~/.config/i2i/i2i-token")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    return ""


def post(url: str, body: dict, token: str = "") -> tuple[int, dict]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status, json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw or "{}")
        except json.JSONDecodeError:
            return e.code, {"error": raw[:200]}
    except Exception as e:  # connection refused etc.
        return 0, {"error": str(e)}


def get(url: str, token: str = "") -> tuple[int, dict]:
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status, json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw or "{}")
        except json.JSONDecodeError:
            return e.code, {"error": raw[:200]}
    except Exception as e:
        return 0, {"error": str(e)}


def cmd_run(intent: str, context: str, quiet: bool) -> int:
    tok = si_token()
    status, pinch = post(SI + "/pinch", {"intent": intent, "context": context}, tok)
    action = pinch.get("action", "?")
    conf = pinch.get("confidence", 0)
    eta = pinch.get("eta_measured", None)

    if action == "FIRE":
        print(pinch.get("reflex", ""))
        if not quiet:
            print(f"# fleet FIRE conf={conf:.3f} eta={eta} uses={pinch.get('uses')}", file=sys.stderr)
        return 0

    if action == "CONFIRM":
        print(f"# CONFIRM ({conf:.3f}) candidate: {pinch.get('candidate', '')}")
        print("# re-run with --confirm to accept and run it, or --compile to teach a new reflex")
        return 2

    # ESCALATE (or unknown) -> ask the local trust compiler
    if not quiet:
        print(f"# fleet ESCALATE (conf={conf:.3f}) — asking local lever", file=sys.stderr)
    lstatus, lres = post(
        LEVER + "/run",
        {"request": intent, "chat_id": os.environ.get("LEVER_CHAT_ID", "default")},
        os.environ.get("LEVER_TOKEN", ""),
    )
    if lstatus == 200 and (lres.get("command") or lres.get("result")):
        command = lres.get("command") or ""
        print(command or lres.get("result", ""))
        taught = lres.get("taught") or lres.get("source") or "lever"
        if not quiet:
            print(f"# lever resolved via {taught}", file=sys.stderr)
        # compile back: fleet learns the reflex for every agent
        cstatus, cres = post(SI + "/pinch/compile", {
            "intent": intent,
            "reflex": command or lres.get("result", ""),
            "confidence": float(os.environ.get("BRIDGE_COMPILE_CONF", "0.9")),
            "context": context,
        }, tok)
        if not quiet:
            print(f"# compiled back to fleet: {cstatus} {cres.get('vector_id', cres.get('error', ''))}", file=sys.stderr)
        return 0

    print("ESCALATE", file=sys.stderr)
    print("# neither the fleet nor the local lever knows this intent — thinking layer required",
          file=sys.stderr)
    return 1


def cmd_pull_fleet(limit: int) -> int:
    tok = si_token()
    status, res = get(f"{SI}/intents?limit={limit}", tok)
    if status != 200:
        print(f"fleet /intents failed: {status} {res}", file=sys.stderr)
        return 1
    intents = res.get("intents", [])
    ok = 0
    for it in intents:
        phrase, command = it.get("intent", ""), it.get("reflex", "")
        if not phrase or not command:
            continue
        ls, lr = post(LEVER + "/teach", {"intent_phrase": phrase, "command": command,
                                         "chat_id": os.environ.get("LEVER_CHAT_ID", "default")},
                      os.environ.get("LEVER_TOKEN", ""))
        if ls == 200:
            ok += 1
    print(f"pulled {ok}/{len(intents)} fleet reflexes into the local lever")
    return 0


def cmd_push_local() -> int:
    tok = si_token()
    try:
        out = subprocess.run(["lever", "export"], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("lever CLI not installed — pip install -e . in the lever-runner clone", file=sys.stderr)
        return 1
    if out.returncode != 0:
        print(f"lever export failed: {out.stderr[:200]}", file=sys.stderr)
        return 1
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        print("lever export did not return JSON", file=sys.stderr)
        return 1
    rows = data if isinstance(data, list) else data.get("commands", [])
    ok = 0
    for row in rows:
        phrase = row.get("intent_phrase") or row.get("phrase") or ""
        command = row.get("command") or ""
        if not phrase or not command:
            continue
        s, _ = post(SI + "/pinch/compile",
                    {"intent": phrase, "reflex": command, "confidence": 0.85}, tok)
        if s == 200:
            ok += 1
    print(f"pushed {ok}/{len(rows)} local levers to the fleet")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="fleet reflex <-> local trust compiler bridge")
    ap.add_argument("intent", nargs="?", help="what you want done")
    ap.add_argument("--context", default="", help="binding context for the reflex")
    ap.add_argument("--pull-fleet", action="store_true", help="fleet intents -> local lever")
    ap.add_argument("--push-local", action="store_true", help="local levers -> fleet")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    if args.pull_fleet:
        return cmd_pull_fleet(args.limit)
    if args.push_local:
        return cmd_push_local()
    if not args.intent:
        ap.print_help()
        return 64
    return cmd_run(args.intent, args.context, args.quiet)


if __name__ == "__main__":
    sys.exit(main())
