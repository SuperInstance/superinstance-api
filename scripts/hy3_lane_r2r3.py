#!/usr/bin/env python3
"""R2 CURATE (runner scores + picks top 3) then R3 ROUGH-OUT (Hy3 designs)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hy3_lane_cache as H

st = H.load()

R2 = """R2 — RUNNER CURATION. I am the runner (deepseek). I scored your 60 ideas on four
frozen axes (each 0-5): BUILD (ships on CF free-tier Worker+D1+Vectorize+KV with no new
infra), LEVER (how much it changes fleet behavior), HONEST (does the idea carry a real,
detectable failure mode + escape, not receipt theater), PROBE (can we falsify the core
claim cheaply — a Worker route change or a 4050 run). Total /20.

TOP SCORES (full table goes in the artifact):
- S3#1 per-lane cache-hit accounting in D1 (cached_tokens/total) ......... 4/4/4/5 = 17  ← BUILD first
- S2#5 negative-intent cache ("I don't know" as a <50ms cached answer) .... 5/4/5/4 = 18  ← BUILD second
- S5#11 re-derive test = cache proof (nightly rebuild hash vs live tiles)  4/5/5/4 = 18  ← BUILD third
- S1#8 receipt honesty supersedes_version .............................. 5/4/5/3 = 17
- S2#10 compile-back starts at CONFIRM not known ....................... 5/5/5/4 = 19
- S1#1 access-frequency demotion + access_decay receipt ................ 4/4/4/3 = 15
- S4#10 near-dup receipt exact flag .................................... 5/3/5/3 = 16
- S5#6 "cache word poisons authority seam" (negative result) ........... 5/5/5/2 = 17
- S3#4/#12 serving-window-as-coherence-epoch + epoch receipt ........... 4/4/5/4 = 17

THREE WINNERS (and WHY), which you design in R3:
1. **S3#1 (+#4/#12 folded in) — LANE CACHE ACCOUNTING + SERVING-WINDOW EPOCH.** Won
   because it is the only surface we can measure TODAY with no new infra: this very
   thread is a live specimen (DeepInfra returns prompt_tokens_details.cached_tokens; our
   one-model-per-thread doctrine is the test). It converts your own doctrine into a
   receipt. Folds in the XP-C finding (a serving window IS a coherence epoch) so
   determinism/cost claims carry an epoch id.
2. **S2#5 + #10 — NEGATIVE-INTENT CACHE WITH COMPILE-BACK-AT-CONFIRM.** Won because the
   pincher seam is shipped and live (pinch returns known/CONFIRM/ESCALATE at <50ms). Your
   two ideas together close the worst failure of an answer-cache: serving a confidently
   wrong answer forever. "I don't know" cached with a TTL, and every compile-back row
   starts at CONFIRM (not known) until N uses or an outcome signal. Highest HONEST+PROBE.
3. **S5#11 — RE-DERIVE TEST = CACHE PROOF.** Won because it answers the surface-5 question
   ("is a cell a cache?") operationally instead of ontologically: a cell is a cache IFF
   its content is re-derivable (hash-match a rebuild) from bookings+tile_versions. Buildable
   as a Worker route; and it connects straight to XP-C (a non-deterministic seat makes
   re-derivation flaky → the test itself must declare its determinism window). 4050-testable.

RUNNER'S RESERVATIONS you must respect in R3:
(a) #1's provider cache metrics are provider-reported — treat cached_tokens as a CLAIM,
    verify by prefix hash (your own S3#6), don't trust the number.
(b) #2's negative cache must not become a permanent "I don't know" wall — TTL + tile-write
    invalidation both required.
(c) #3 cannot use the 4050 as the rebuild engine for anything replay-sensitive — XP-C
    proved the local seat is not byte-replay-safe under co-tenancy. State which engine
    (CPU deterministic vs GPU/LLM) is allowed and why.

In <=120 words before you design: name the strongest OBJECTION to this selection (or
"none"), then proceed. Do not restate my table."""

c = H.turn(st, R2, "R2-curate", max_tokens=700, temperature=0.4)

R3 = """R3 — ROUGH-OUT THE THREE WINNERS. Design each as an engineer would ship it on THIS
Worker (MCP tools, D1 tables, Vectorize, KV). Use exactly this template per design:

### DESIGN N — <name>
- INTERFACE: MCP tool name + JSON signature; D1 DDL (CREATE TABLE/INDEX); KV key shape.
- DATA FLOW: WRITE path (who writes what, when) / READ path (hit, miss, escape).
- INVALIDATION / COHERENCE: what marks it stale; the exact watermark field; the epoch story.
- RECEIPTS / OBSERVABILITY: what gets booked (gamma/eta or cached_tokens); the query/route
  that exposes hit-rate; the honesty field that admits a stale/incoherent hit.
- ROUGH COST: D1 rows/day at fleet scale (~10 agents, ~5k calls/day), Vectorize ops, KV
  reads; say if it fits free tier.
- SMALLEST FALSIFIABLE PROBE: one script or one Worker route; the exact pass/fail number;
  which engine (CF Worker / deterministic CPU / 4050 GPU) and why that engine.

Be concrete and terse — DDL and key shapes, not prose. End with: "BUILD ORDER: 1,2,3 or
another order" and one line why. Max ~1400 words total."""

d = H.turn(st, R3, "R3-designs", max_tokens=4000, temperature=0.5)

R3b = """R4 — RED-TEAM YOUR OWN DESIGNS, then grade. Be adversarial and brief.

1. For EACH of the three designs: the single most likely way it ships WRONG in the first
   week (a concrete scenario), and the cheapest instrumentation that would catch it.
2. Which design has a HIDDEN dependency that makes it fail in combination with another
   (e.g. negative-intent cache + epoch receipt disagreeing on what "stale" means)?
3. Honest self-grade of your own output this session: where were you weakest, and what did
   you fail to answer? Do not be diplomatic.
4. One idea that FAILED our curation (scores <15) that you still think the fleet is wrong
   to skip, and why in two lines.
Max ~600 words."""

e = H.turn(st, R3b, "R4-redteam", max_tokens=2000, temperature=0.5)

print("\n\n[state]", H.STATE, "calls:", st["calls"])
