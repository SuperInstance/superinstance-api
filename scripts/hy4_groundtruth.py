#!/usr/bin/env python3
"""Fetch DeepInfra /v1/openai/models metadata as GROUND TRUTH for pricing/context.
List-form subprocess only. Key read at use-time, never logged/echoed/written.
"""
import json, urllib.request

ENDPOINT = "https://api.deepinfra.com/v1/openai/models"


def key():
    with open("/home/eileen/.config/deepinfra/token") as f:
        return f.read().strip()


def main():
    req = urllib.request.Request(
        ENDPOINT, headers={"Authorization": "Bearer " + key()}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    models = d.get("data", d if isinstance(d, list) else [])
    print("total models:", len(models))
    for m in models:
        mid = m.get("id", "")
        if "hy" in mid.lower() or "tencent" in mid.lower():
            print(json.dumps(m, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
