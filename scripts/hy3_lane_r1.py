#!/usr/bin/env python3
"""R1 EXPAND — five surfaces, one continued Hy3 thread."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hy3_lane_cache as H

st = H.load()

BRIEFS = [
# ── 1. tile tiers + demotion ──
("R1.1-tile-tiers",
 """SURFACE 1 — TILE TIERS (full/gist/hint) + DEMOTION RECEIPTS.

D1: tiles(id, room_id, key, lamport, content, tier CHECK in full|gist|hint,
vector_id, created_ts, updated_ts, UNIQUE(room_id,key)); tile_versions(tile_id,
lamport, content, tier, ts) holds EVERY version ever; demotion_receipts(tile_id,
from_tier, to_tier, fact_survival REAL, lattice_snap REAL, method, ts).

Today demotion is manual and requires a receipt. Nothing is ever deleted — the
old tier's content lives in tile_versions, so "demote" is really "serve less".

Give 8-12 RAW IDEAS on: WHEN to demote (trigger from access patterns?), WHAT a
fact_survival / lattice_snap receipt should actually measure, how a demoted tile
gets RE-PROMOTED (and who pays to rebuild full content from versions), and how to
INFER the right tier from access patterns. For each: mechanism on THIS schema +
how it fails (stale gist after the full tile changed? promotion thrash?
receipt theater that passes while the gist lies?). Dense, numbered."""),
# ── 2. pinch compile-back ──
("R1.2-pinch-compileback",
 """SURFACE 2 — PINCH COMPILE-BACK AS A WRITE-THROUGH ANSWER CACHE.

The reflex seam: intents(intent, context, reflex, confidence, vector_id, uses,
created_ts, updated_ts, UNIQUE(intent,context)). pinch{intent,context} →
known ≥0.92 fires (<50ms, zero LLM); 0.75-0.92 CONFIRM; else ESCALATE to a
thinking model, whose resolution is COMPILED BACK as a new intent row.
vector_id = semantic match key in Vectorize.

So the intent table IS an answer cache that fills itself on miss. Give 8-12 RAW
IDEAS on: RETENTION POLICY for compiled intents (evict? never? demote confidence?),
context scoping (when does intent+context over-fit and start firing wrong answers
for a near-identical question?), confidence decay/renewal, using `uses` + gamma/eta
as an access-frequency+surprise signal, negative-intent caching (cache "I don't
know"), key design (canonical phrasing vs embedding), and cache-warming from
bookings. Each: mechanism + how it fails (poisoned reflex serving wrong answers
forever at <50ms; false CONFIRM; context explosion). Dense, numbered."""),
# ── 3. provider prompt-cache economics ──
("R1.3-provider-prompt-cache",
 """SURFACE 3 — PROVIDER PROMPT-CACHE ECONOMICS (the one we can measure TODAY).

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
giving confidently wrong answers; cost illusion). Dense, numbered."""),
# ── 4. /near semantic cache ──
("R1.4-near-semantic-cache",
 """SURFACE 4 — /near SEMANTIC CACHE (near-duplicate collapse + embedding dedup).

/near: query text → bge-m3 embedding → Vectorize topK → hydrated rows with scores.
Bookings and tiles share one provider-tagged index identity (fleet-memory).

Two lessons from the fleet cut both ways: "fleet-triage's leaky-split lesson" —
a train/eval split leaked near-duplicates, inflating scores; the same
near-duplicate structure means a semantic cache can serve a NEARLY-right answer
for a question that needed the exact one. And Vectorize metadata filters
returned empty results even when unfiltered queries matched — platform quirk.

Give 8-12 RAW IDEAS on: near-duplicate collapse (when is 0.93 "the same
question"?), embedding dedup at write time (dedupe before upsert?), threshold
policy per kind (booking vs tile vs intent), negative-space / "this does NOT
match" storage, cache invalidation when a source row changes (vector_id parity),
and using eta (surprise vs neighborhood) as the cache-quality signal. Each:
mechanism + how it fails (false-merge serving near-right answer; threshold drift;
unbounded index growth). Dense, numbered."""),
# ── 5. quilt cell as cache ──
("R1.5-quilt-cell-as-cache",
 """SURFACE 5 — QUILT CELL STATE AS ROUTING BETWEEN LEDGERS: IS A CELL A CACHE?

quilt-dba: rooms have a `stage`; cells load in stages; "adding a cell IS
advancing a stage." Rooms/tiles are one ledger; bookings are another; intents a
third. A "cell" (room, in this schema) holds state that other layers read.

Question: is a cell (a room + its tiles at a stage) a CACHE — i.e., a materialized
preference over the bookings/vectors that generated it — or is it a primary store?
If tile content can be RE-DERIVED from bookings + versions, then the cell is a
cache and gets cache semantics (staleness window, coherence, eviction... but we
never delete). If not, it's authority.

Give 8-12 RAW IDEAS on: the materialized-view framing of rooms/tiles; a
stage-advance as a cache commit; routing a query BETWEEN ledgers (when to answer
from the warm cell vs hit the cold vector index); coherence between a cell's
stage and the bookings that superseded it; backfill/rebuild; and whether "cache"
is even the right word here or it poisons the authority seam. Each: mechanism +
how it fails (cell silently authoritative while bookings moved on; stage
skew). Dense, numbered."""),
]

for tag, brief in BRIEFS:
    H.turn(st, brief, tag)

print("\n\n[state]", H.STATE, "calls:", st["calls"])
