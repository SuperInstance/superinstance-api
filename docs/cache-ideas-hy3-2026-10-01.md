# Cache ideas from Hy3 — lane HY3-CACHE (dog-fooding an expert seat)

**Lane:** HY3-CACHE · **Runner (curator):** deepseek-v4-flash · **EXPERT SEAT:**
`tencent/Hy3` via DeepInfra OpenAI-compatible API (verified live 2026-10-01 14:19 AKDT)
· **Date:** 2026-10-01 · **Target:** `superinstance-api` (five seams: tiles/rooms tiers,
meaning via `/near` Vectorize, reflex pinch compile-back, field exoj γ/η, growth quilt-dba).

**Method (the doctrine, practiced):** ONE model per expert thread — a single continued
message array, never re-seeded per turn, so the provider prefix cache stays hot and
context carries. **8 calls total** (5 expansion + curation + designs + red-team), plus
**1 call lost to a runner `makedirs` bug** (see §0). Raw transcript:
`docs/_hy3_lane_state.json`.

**Live cache receipt for the session itself (see Appendix A):** 52,741 prompt tokens,
**42,352 cached (80.3% prefix-cache hit)** — the thread is its own specimen for
Surface 3. This is the receipt Design 1 would automate.

---

## §0 — Honest lane defects (fail loud, mine)

1. **`makedirs` bug (runner, mine).** `docs/` did not exist in the repo (README: "Pages
   still open"). The R1 driver's first turn fired a real Hy3 call, then died on
   `save()` (`FileNotFoundError`) — the state was never written, so that call's output
   was lost. Same bug class XP-C booked on 2026-10-01. Fixed (`mkdir -p docs`),
   re-run. Cost: 1 wasted API call, ~unquantified tokens.
2. **Runner-as-curator scoring is coarse.** The /20 scores in §2 are my judgment, not a
   measured quantity; they are an ordering device, not a receipt. Flagged so nobody
   mistakes them for evidence.

---

## §1 — R1 EXPAND (raw, verbatim from Hy3)

Prompt framing for every surface: state the mechanism on the *actual* schema, and how it
fails first-class. 12 ideas per surface, 60 total.

### Surface 1 — Tile tiers (full/gist/hint) + demotion receipts

1. **ACCESS-FREQUENCY DEMOTION TRIGGER (gamma-seam: compute cost).** MECHANISM: D1 query over `tile_versions.ts` per `(room_id,key)`; if no version write in N days AND reads < M/window, write `demotion_receipts(tile_id,'full','gist',fact_survival=read_ratio, lattice_snap=max(lamport)-min(lamport), method='access_decay')` and set `tiles.tier='gist'`. Full content stays in `tile_versions`. FAILS: Silent drift — a gist built from old full content lies when a later `tile_versions` insert changes semantics but tier stays gist. Detect via `tile_versions.lamport > tiles.updated_ts` while `tier='gist'`; escape = forced re-promote or gist rebuild on version delta.
2. **READ-ONLY REPEAT PROMOTION (reflex-seam: intents).** MECHANISM: Count `intents` reads on a gist/hint key; when reads cross threshold, promote: rebuild full from `tile_versions` latest `lamport`, update `tiles.content/tier`, write receipt `('gist','full',fact_survival=hit_rate, lattice_snap=vector neighborhood distance, method='read_promote')`. FAILS: Promotion thrash — bursty bot reads flip tier every window. Detect by `demotion_receipts.ts` delta < 1h same tile opposite directions; escape = cooldown counter in KV.
3. **FACT_SURVIVAL = VERSION ENTROPY RATIO (authority-seam).** MECHANISM: On demotion compute `fact_survival = 1 - (count(distinct content hash in tile_versions where tile_id) / count(*))`; near-1 = stable fact, safe to gist. Store in receipt. FAILS: Receipt theater — stable history but a pending `intent` writes new branch; gist served while full diverges. Detect: `intents` with lamport > latest receipt ts for that tile; escape = block demotion if open intent exists.
4. **LATTICE_SNAP = LAMPORT SPAN / VECTOR DRIFT (meaning-seam).** MECHANISM: `lattice_snap = (max(lamport)-min(lamport)) / (1 + vectorize distance to room centroid)`; low snap = coherent, demote safe. FAILS: Vectorize centroid stale after `/near` reindex; snap lies low. Detect: `vector_id` updated_ts vs receipt ts mismatch; escape = recompute on promote.
5. **WRITE-AMPLIFICATION GUARD ON RE-PROMOTE (gamma-seam).** MECHANISM: Re-promotion pays by tagging `bookings` actor; `UPDATE tiles SET content=(SELECT content FROM tile_versions WHERE tile_id=? ORDER BY lamport DESC LIMIT 1)` charged to caller quota in KV. FAILS: Poison — caller replays old `tile_versions` lamport via lamport forge; full content regresses. Detect: `lamport` not monotonic vs `updated_ts`; escape = reject if lamport < current tile lamport.
6. **INFER TIER FROM /near MISS (meaning-seam).** MECHANISM: If `Vectorize /near` returns no tile within room for key, auto-set `tier='hint'` + receipt `fact_survival=0`. Access pattern: semantic miss => cheap hint. FAILS: Hint lies when later `tile_versions` adds full; stale hint served. Detect: `tile_versions` insert after hint receipt with higher lamport; escape = promote on insert trigger.
7. **DEMOTION ON COHERENCE WINDOW EXPIRY (field-seam: eta=surprise).** MECHANISM: KV stores `coherence_window(tile_id, expires)`; on expiry if `eta` (surprise vs vector neighborhood) < threshold, demote full->gist, receipt `lattice_snap=eta`. FAILS: Window too long => gist stale after full changed; too short => receipt thrash. Detect: `updated_ts` of tile > coherence_window.expires while tier=gist; escape = shrink window.
8. **RECEIPT HONESTY: SUPERSEDES FIELD (authority-seam).** MECHANISM: Add `supersedes_version` to `demotion_receipts` = lamport of full content the gist was built from. Hit on gist must return receipt saying "built from vN, current vM". FAILS: Caller ignores receipt, treats gist as truth. Detect: downstream `bookings` reference gist while `tile_versions` has newer; escape = hard 412 if receipt ignored.
9. **PROMOTION BY BOOKING DEMAND (growth-seam: quilt-dba).** MECHANISM: `bookings` on a hint key trigger staged cell promote: pull all `tile_versions` into full in D1, write receipt `method='booking_promote'`. FAILS: Growth thrash — booking spikes promote then idle demotes. Detect: `demotion_receipts` method oscillation; escape = minimum dwell time in KV.
10. **FACT_SURVIVAL AS READ/WRITE RATIO (reflex-seam).** MECHANISM: `fact_survival = reads/(reads+writes)` from `intents`+`tile_versions`; high = read-only fact, demote to hint safe. FAILS: Write buried in `tile_versions` not captured by intents; survival overestimated. Detect: `tile_versions` count grows but survival static; escape = include version inserts in denominator.
11. **DEMOTION RECEIPT THEATER TRAP (negative result).** MECHANISM: This is a bad idea — auto-approve demotion if `lattice_snap` exists regardless of value. FAILS: Receipt passes while gist content = empty string (never rebuilt). Detect: `tiles.content` null on gist tier; escape = require content hash in receipt.
12. **TIER INFERENCE FROM ACCESS SHAPE (field-seam).** MECHANISM: Log access pattern in KV `access_shape(key, seq)`; if 90% reads same field => hint; full only if random field access. Update `tiles.tier` via receipt. FAILS: Shape changes after demotion; hint misses cause full rebuild loop. Detect: `tile_versions` reads > writes post-hint; escape = shape re-eval every K accesses.

### Surface 2 — Pinch compile-back as a write-through answer cache

1. **NEVER-EVICT RETENTION WITH CONFIDENCE DEMOTION (reflex-seam).** MECHANISM: intents never deleted; retention = decay `confidence` toward 0.75 floor via `UPDATE intents SET confidence=confidence*0.98 WHERE updated_ts < now()-30d`. Below 0.75 row stays but routes to ESCALATE. FAILS: Poisoned reflex frozen — a wrong intent at 0.91 never decays below fire threshold if decay window missed; serves wrong answer <50ms forever. Detect: `bookings` post-hoc contradiction vs intent.reflex; escape = external invalidation sweep.
2. **CONTEXT OVER-FIT GUARD VIA EMBEDDING RADIUS (meaning-seam).** MECHANISM: on pinch, require `vectorize /near` distance < 0.08 for context match; if intent+context pair fires but new query embedding drifts >0.15 from stored `vector_id`, force CONFIRM not known. FAILS: Context explosion — near-identical questions get distinct intent rows per tiny context var; cache fragments, hit rate collapses. Detect: count(intent) with same reflex > N; escape = merge on canonical phrasing.
3. **USES-GAMMA THRASH THROTTLE (field-seam: gamma=compute cost).** MECHANISM: `uses` increments per fire; if `uses`/day > 1000 and gamma (serving cost) low, pin intent in KV warm cache; if `uses`=0 for 90d, demote confidence 0.92→0.80. FAILS: False CONFIRM loop — high uses from a broken caller replaying same wrong query keeps confidence artificially high. Detect: `uses` up but `bookings` success rate down; escape = confidence also needs outcome signal.
4. **ETA-SURPRISE DEMOTION (field-seam: eta=surprise vs vector neighborhood).** MECHANISM: weekly compute eta = mean distance of new `/near` hits to intent.vector_id; if eta spikes (>0.3) old intent no longer neighborhood-coherent, set confidence 0.70 (ESCALATE). FAILS: Semantic drift poison — intent fires on historical neighborhood after room vectors reindexed; wrong answer at <50ms. Detect: `vector_id` ts vs Vectorize index ts mismatch; escape = re-embed on index bump.
5. **NEGATIVE-INTENT CACHE ("I DON'T KNOW") (authority-seam).** MECHANISM: ESCALATE resolution = null/unknown writes intent row `reflex='NULL', confidence=0.95, context='neg'`. Next pinch same embedding hits known-negative, returns "don't know" <50ms, no LLM. FAILS: Knowledge arrives later — negative cached forever blocks correct answer after tile promoted. Detect: `tile_versions` newer than negative intent.ts; escape = negative intent expires in 7d or on tile write.
6. **CANONICAL KEY vs EMBEDDING DUAL INDEX (meaning-seam).** MECHANISM: store `intent` canonical lowercased strip-punct; UNIQUE(intent,context) stays; but pinch first tries exact canonical, then vector_id. Embedding is fallback not key. FAILS: Canonical collision — two distinct meanings same phrasing (room A "status" vs room B "status") overwrite; wrong reflex. Detect: `vector_id` distance between same canonical >0.4; escape = scope canonical by room_id.
7. **CONFIDENCE RENEWAL ON BOOKING SUCCESS (growth-seam: quilt-dba).** MECHANISM: when `bookings` consumed intent and succeeded, `UPDATE intents SET confidence=min(0.99,confidence+0.01), updated_ts=now()`. Renews high-value reflexes. FAILS: Success theater — booking succeeds for unrelated reason; confidence inflated, poisoned reflex shielded. Detect: ablation = disable intent, booking still succeeds; escape = renewal needs causal tag.
8. **CACHE-WARM FROM BOOKINGS (reflex-seam).** MECHANISM: on `bookings` insert, pre-compile expected next intent via prior `intents` co-occurrence, write row confidence 0.80 pending confirm. FAILS: Warming poison — booking pattern shifts, warmed intent never confirmed but fires known at 0.80 (false known). Detect: warmed `uses`=0 after 14d; escape = warm rows start at CONFIRM not known.
9. **CONTEXT SCOPING COLLAPSE (negative result).** MECHANISM: bad idea — let context be free-text full user string. FAILS: over-fit extreme: every query unique context, intent table = 1:1 log, zero cache benefit, D1 grows unbounded. Detect: `uses`=1 for 99% rows; escape = context must be enumerated enum not blob.
10. **COMPILE-BACK POISON WRITE-THROUGH (reflex-seam).** MECHANISM: ESCALATE → thinking model writes new intent row `uses=0, confidence=0.92`. Immediate known-fire on next pinch. FAILS: Model hallucinates reflex, compiled as truth; <50ms wrong answer at fleet scale. Detect: `tile_versions` contradiction vs reflex; escape = new compile-back rows start at 0.75 CONFIRM for 10 uses.
11. **DEMOTION RECEIPT FOR INTENT (authority-seam).** MECHANISM: mirror tile demotion — intent confidence drop writes `demotion_receipts(tile_id=NULL, from_tier='known', to_tier='confirm', fact_survival=uses/eta, lattice_snap=vector drift, method='intent_decay')`. FAILS: Receipt theater — intent demoted but KV warm copy not invalidated, known still served. Detect: KV key ts > receipt ts; escape = receipt triggers KV purge.
12. **FALSE CONFIRM FROM 0.75-0.92 BAND (field-seam).** MECHANISM: CONFIRM band sends to thinking model for ok; if model lazy-returns reflex unchanged, intent stays. FAILS: model rubber-stamps wrong reflex repeatedly; confidence creeps to 0.92 via renewals; becomes known poison. Detect: CONFIRM outcomes all identical to reflex; escape = CONFIRM must mutate or downgrade.

### Surface 3 — Provider prompt-cache economics

1. **PER-LANE CACHE-HIT ACCOUNTING IN D1 (field-seam: gamma=compute cost).** MECHANISM: Worker logs every `/chat/completions` response: `INSERT INTO bookings(meta) VALUES (json({lane, cached_tokens, total_tokens, ts, model}))`; daily aggregate `cached_tokens/total_tokens` per lane. KV holds running `$/1M cached` vs `$/1M fresh`. FAILS: Cost illusion — provider counts cached_tokens but thread mutated mid-window so prefix partially invalid; reported cached but recompute happened. Detect: `total_tokens` spike vs prior window same length; escape: hash last cached prefix vs sent prefix, mismatch = lie.
2. **WARM-THREAD KEEP VS FRESH ON CONTEXT ROT (meaning-seam).** MECHANISM: keep thread if `tile_versions` touched in room < 3 since last call AND lamport delta small; else flush messages, new thread. Decision in KV `thread_state(lane, room, valid_until)`. FAILS: Stale prefix — keep thread but a demoted tile's gist changed underneath; model answers from old full context confidently wrong. Detect: `tiles.updated_ts` > thread_state.valid_until; escape: thread invalidated on any tile write in scope.
3. **MID-THREAD SEAT ROTATION BAN (reflex-seam).** MECHANISM: enforce "one model per expert thread" — `bookings` tags lane→model; Worker rejects seat switch if `thread_state.active=1`. Rotation only between threads. FAILS: Co-tenancy non-determinism — even same seat, 4050 window flip changes tokens; ban doesn't save determinism. Detect: replay hash mismatch on fixed seed; escape: pin determinism epoch id in receipt, not just model name.
4. **SERVING WINDOW AS COHERENCE EPOCH (field-seam).** MECHANISM: treat each WSL2 serving window as epoch `E`; receipt books `epoch_id, cached_tokens, gamma=local_gpu_cost, eta=surprise vs prior epoch`. Threads only valid inside E. FAILS: Epoch bleed — window ends mid-thread, prefix cache dead but Worker thinks warm; wrong answers <cost. Detect: `epoch_id` in thread_state expired vs local ts; escape: hard thread kill on epoch close.
5. **LANE-ROTATION COLD-START PENALTY METER (gamma-seam).** MECHANISM: on lane switch (fresh thread) book `gamma += cold_tokens * price`; compare to savings from better expert. Store in `demotion_receipts(method='lane_rotate', fact_survival=cache_hit_rate)`. FAILS: False economy — rotate to "cheaper" lane but its cold thread burns more than kept warm expert. Detect: aggregate `gamma` per lane rotation positive; escape: require warm-thread exists before rotate.
6. **CACHED-CONTEXT DETERMINISM RECEIPT (authority-seam).** MECHANISM: every cached hit returns receipt: `built_from_epoch=E, prefix_hash=H, supersedes=last tile lamport`. Claim: answer coherent with H. FAILS: Receipt theater — prefix hash matches but model output varied by temperature; determinism claim false. Detect: replay on same H yields diff tokens; escape: receipt must state temp/seed or "nondeterministic".
7. **ETA-DRIVEN THREAD FLUSH (field-seam: eta=surprise).** MECHANISM: if new query embedding distance to thread-start context > 0.4 (high surprise), flush + fresh thread to avoid stale prefix; else keep. FAILS: Over-flush thrash — noisy queries keep flushing, cache never warms, cost explodes. Detect: `cached_tokens`/day → 0 with high call vol; escape: eta threshold adaptive via KV.
8. **PROVIDER CACHE PRICE ILLUSION TRAP (negative result).** MECHANISM: bad idea — optimize lane by reported cached_tokens alone, ignore that DeepInfra bills minimum 1 min kept-warm per prefix. FAILS: Cost illusion — 90% cached but idle warm threads rack fixed fee; "savings" negative. Detect: `bookings` cost vs `cached_tokens` ratio climbs; escape: book `warm_minute_cost` separately.
9. **RECEIPT BOOKING: CACHED_TOKENS + GAMMA/ETA (growth-seam).** MECHANISM: compile-back from provider into `bookings`: `cached_tokens, gamma=($/token fresh-cache delta), eta=(query surprise vs thread)`. Quilt-dba stages cells per lane. FAILS: Poison — gamma computed from wrong price table; fleet thinks lane profitable, it bleeds. Detect: `gamma` sign vs real invoice mismatch; escape: price feed from billing API not hardcoded.
10. **CONTEXT ROT VS CACHE SAVINGS TRADEOFF METER (meaning-seam).** MECHANISM: A/B in KV: lane A keeps thread 24h, lane B flushes on tile write. Compare `cached_tokens` vs `bookings` contradiction rate. FAILS: Silent wrong — A saves 80% but serves stale gist; B costs more but correct. Doctrine violated quietly. Detect: downstream `intents` compiled from A contradict `tile_versions`; escape: correctness gate before cache metric.
11. **PIN DETERMINISM PER CACHE/WINDOW STATE (reflex-seam).** MECHANISM: serialize replay-sensitive lanes: `KV lock(lane, epoch)`; only one Worker tick drives seat; others wait. Mirrors XP-C finding. FAILS: Lock convoy — epoch long, all lanes stall behind one seat; throughput death. Detect: `bookings` latency p99 > window; escape: shard by room not lane.
12. **COHERENCE EPOCH RECEIPT HONESTY (authority-seam).** MECHANISM: answer from cached prefix must cite `epoch_id` + `cached_tokens` + "if epoch closed, this is stale". Caller sees bet. FAILS: Caller strips receipt, treats as fresh truth post-epoch. Detect: `bookings` reference answer after epoch close; escape: 412 if no epoch-valid ack.

### Surface 4 — /near semantic cache

1. **NEAR-DUP COLLAPSE AT 0.93 WITH KIND-GATED THRESHOLD (meaning-seam).** MECHANISM: `/near` hit if `score ≥ kind_threshold`: tiles 0.95, bookings 0.90, intents 0.93. Store `vector_id` + kind in metadata; on query filter by kind. Cache answer keyed by `vector_id` in KV with `coherence_window`. FAILS: False-merge — two tiles at 0.931 in same room collapse; served near-right gist while exact tile needed. Detect: `tile_versions` lamport divergence between merged pair; escape: raise tile threshold to 0.97, log collision.
2. **WRITE-TIME EMBEDDING DEDUP (authority-seam).** MECHANISM: before `Vectorize.upsert`, query `/near` at 0.99; if hit, update existing `vector_id` (new `tile_versions` row) instead of new vector. D1 `tiles.vector_id` reused. FAILS: Unbounded version chain — dedup keeps one vector but `tile_versions` grows forever; semantic cache serves old vector content after full rewrite. Detect: `tile_versions` count ≫ 1 per vector_id but `vector_id` unchanged; escape: re-embed on content hash change > threshold.
3. **METADATA FILTER EMPTY-RESULT FALLBACK (negative platform quirk).** MECHANISM: if filtered `/near` returns empty, retry unfiltered + post-filter in Worker; cache the "filter-quirk-miss" as receipt `method='meta_empty'`. FAILS: Silent wrong — unfiltered match is a different kind, post-filter drops it, returns null where answer existed. Detect: unfiltered hit kind != query kind but score high; escape: never serve cross-kind on fallback.
4. **NEGATIVE-SPACE "DOES NOT MATCH" STORAGE (meaning-seam).** MECHANISM: on ESCALATE miss, upsert `vector_id` with metadata `neg=1` (no hydration row). `/near` checks neg first: if score ≥ 0.93 and neg, return "known non-match" <50ms. FAILS: Poison — neg row from old room leaks after tile added; blocks exact match. Detect: `tiles` insert with vector distance <0.05 to neg vector; escape: neg expires on any same-kind write.
5. **ETA AS CACHE-QUALITY SIGNAL (field-seam: eta=surprise).** MECHANISM: per cached `/near` result, compute `eta = mean distance(new query, topK neighborhood)`; if eta < 0.1 cache "safe", else mark `stale_pending`. FAILS: Neighborhood drift — Vectorize reindex shifts all distances; eta lies low, near-dup served wrong. Detect: `vector_id` ts vs index ts; escape: eta recompute on index bump.
6. **VECTOR_ID PARITY INVALIDATION (authority-seam).** MECHANISM: `tiles.updated_ts` vs KV `vector_cache(vector_id, ts)`; on mismatch, purge KV + force re-`/near` + rehydrate. Receipt books `supersedes=old_vector_id`. FAILS: Parity race — tile write between `/near` and hydrate; cache serves pre-write content. Detect: `lamport` at hydrate > cache ts; escape: hydrate inside D1 txn with vector lock.
7. **THRESHOLD DRIFT BY ACCESS SHAPE (reflex-seam).** MECHANISM: KV `threshold(kind)` adapts: if false-merge rate (from `bookings` contradiction) > 5%, raise 0.01; if miss rate high, lower. FAILS: Drift overshoot — threshold oscillates per bursty traffic; cache flapping. Detect: threshold change > 3 in 1h; escape: exponential smoothing on signal.
8. **BOOKING VS TILE THRESHOLD SPLIT (growth-seam).** MECHANISM: bookings (ephemeral) at 0.88 (cheap near-match ok); tiles (authority) at 0.96 (exact). Separate `vectorize` queries. FAILS: Cross-contamination — booking near-dup collapses into tile semantic space via shared index; wrong kind served. Detect: metadata kind mismatch in result; escape: namespace index per kind.
9. **UNBOUNDED INDEX GROWTH TRAP (negative result).** MECHANISM: bad idea — never dedup, upsert every embedding. "Cache everything." FAILS: Index balloons, `/near` latency climbs, near-dup inflation (fleet-triage leak) hides real miss; cost explodes. Detect: vector count ≫ row count; escape: enforce write-time dedup #2.
10. **NEAR-DUP RECEIPT HONESTY (authority-seam).** MECHANISM: served from collapse carries receipt: `matched_vector_id=X, query_dist=0.94, exact=0`; caller sees "near-right, not exact". FAILS: Caller ignores receipt, treats near-right as exact in `bookings`; poison propagates. Detect: downstream `intents` reflex from collapsed pair; escape: 412 if exact flag required.
11. **SEMANTIC CACHE WARM FROM BOOKINGS (reflex-seam).** MECHANISM: on `bookings` insert, pre-`/near` expected next query, cache KV `near_cache(query_hash, vector_id, score)`. FAILS: Warm wrong — booking pattern shifts, warmed near-dup serves stale; false-merge at scale. Detect: warm `uses`=0 post-14d; escape: warm starts at eta-flagged not confirmed.
12. **LEAKY-SPLIT DETECTION VIA SELF-SIMILARITY (meaning-seam).** MECHANISM: weekly compute intra-index nearest-neighbor count at 0.93; if >20% pairs are cross-eval/train kind, flag leak; purge semantic cache. FAILS: Purge thrash — legit near-dup also caught; cache never warms. Detect: `cached_tokens` from /near → 0; escape: whitelist by room_id boundary.

### Surface 5 — Quilt cell state as routing between ledgers (is a cell a cache?)

1. **CELL AS MATERIALIZED VIEW OVER BOOKINGS+VERTIONS (authority-vs-cache seam).** MECHANISM: treat `rooms`+`tiles` at stage N as `SELECT ... FROM bookings JOIN tile_versions WHERE room_id=? GROUP BY key` materialization; KV `cell_state(room, stage, built_from_lamport)` records source watermark. Reads prefer cell if `built_from_lamport >= max(bookings.lamport)`. FAILS: Silent authority — cell served as truth after new bookings land but stage not advanced; tile content stale vs bookings. Detect: `bookings.lamport > cell_state.built_from_lamport` while reads hit cell; escape: cell reads forced to check watermark.
2. **STAGE-ADVANCE AS CACHE COMMIT RECEIPT (growth-seam).** MECHANISM: `quilt-dba` stage advance writes `demotion_receipts(tile_id=room, from_tier='stageN', to_tier='stageN+1', fact_survival=cell_hit_rate, lattice_snap=booking_lamport_span, method='stage_commit')`. Cell now "preferred." FAILS: Receipt theater — commit passes but rebuild skipped (cell content null); empty authority. Detect: `tiles.content` null at committed stage; escape: require content hash in receipt.
3. **WARM CELL VS COLD VECTOR ROUTING (meaning-seam).** MECHANISM: query router: if `cell_state.valid` and `eta(query,cell)<0.1` answer from tiles (warm, <1ms); else hit Vectorize + bookings (cold). KV flags route. FAILS: Warm lie — cell valid but its vectors drifted post-reindex; router serves near-right from stale cell. Detect: `vector_id` ts > cell_state.ts; escape: cell invalidated on index bump.
4. **COHERENCE BETWEEN STAGE AND SUPERSEDING BOOKINGS (field-seam).** MECHANISM: D1 trigger on `bookings` insert → mark `cell_state(room, stale=1)` if `lamport > built_from`. Worker rejects cell reads until stage advance. FAILS: Trigger race — booking inserts between check and read; cell served stale. Detect: `bookings.ts > cell_state.ts` and `stale=0`; escape: read inside txn with booking lock.
5. **BACKFILL/REBUILD FROM LEDGERS (authority-seam).** MECHANISM: `rebuild_cell(room)`: replay `bookings`+`tile_versions` into `tiles` full; reset `cell_state.built_from_lamport`. Charged to caller quota KV. FAILS: Poison — lamport forge in bookings replays old state; cell regresses. Detect: `lamport` non-monotonic vs `updated_ts`; escape: reject if lamport < current cell.
6. **"CACHE" WORD POISONS AUTHORITY SEAM (negative result).** MECHANISM: bad idea — call cell a cache universally; fleet treats tiles as evictable preference, stops writing receipts. FAILS: Authority loss — tile needed as truth in `intents` compile-back but evicted-by-doctrine; reflex builds on void. Detect: `intents.reflex` references missing tile; escape: split term: cell-view vs tile-authority.
7. **STAGE SKEW ACROSS ROOM FLEET (growth-seam).** MECHANISM: `quilt-dba` advances rooms independently; `cell_state.stage` per room. Routing logs skew. FAILS: Skew silent — room A at stage 3, room B at 1; cross-room query joins on stale B; wrong answer. Detect: `max(stage)` - `min(stage)` > 2 with active join; escape: gate cross-room on min stage.
8. **CELL EVICTION WITHOUT DELETE (doctrine: never delete).** MECHANISM: "evict" = demote cell to `tier=hint` in tiles, keep versions; `cell_state.evicted=1`. Preference withdrawn, rebuildable. FAILS: Hint lie — hint built pre-booking; new booking supersedes, hint served. Detect: `bookings.lamport > hint receipt ts`; escape: hint expires on booking.
9. **ROUTING BY GAMMA/ETA BETWEEN LEDGERS (field-seam).** MECHANISM: `gamma(cell)=cell_read_cost`, `eta(cell)=surprise vs bookings`; if `eta<0.05` route cell (cheap), else cold. Book both in `bookings.meta`. FAILS: Cost illusion — cell cheap but wrong (eta under-measured); fleet prefers lie. Detect: `intents` contradiction vs cold answer; escape: correctness gate before gamma.
10. **CELL AS PREFERENCE RECEIPT HONESTY (authority-seam).** MECHANISM: cell hit returns `built_from_lamport, supersedes=bookings.watermark, coherence=stage`. Claim: materialized preference. FAILS: Caller strips receipt, treats cell as source of record; bookings divergence hidden. Detect: `bookings` write after cell read unacked; escape: 412 if no watermark ack.
11. **RE-DERIVE TEST = CACHE PROOF (meaning-seam).** MECHANISM: nightly `rebuild_cell` vs live tiles hash; if match, cell=cache (safe demote); if diff, cell=authority (protect). FAILS: Flap — non-deterministic rebuild (4050 window) gives false diff; authority locked. Detect: rebuild hash varies on same input; escape: rebuild on deterministic CPU only.
12. **QUILT STAGE AS CACHE WINDOW EPOCH (reflex-seam).** MECHANISM: each stage = coherence epoch; `cell_state.valid_until=stage_advance_ts+window`. Like Surface 3 epoch. FAILS: Epoch bleed — window ends mid-query, cell dead but router warm; stale. Detect: `valid_until < now()` and route=cell; escape: hard route flip on epoch close.

---

## §2 — R2 CURATE (runner scores + top 3, and why)

Axes (0–5 each): **BUILD** (ships on CF free-tier Worker+D1+Vectorize+KV, no new infra),
**LEVER**, **HONEST** (real, detectable failure + escape, not receipt theater),
**PROBE** (falsifiable cheaply — a Worker route or a 4050 run). Total /20.

| # | Surface idea | BUILD | LEVER | HONEST | PROBE | Total |
|---|---|---|---|---|---|---|
| S2#10 | compile-back starts at CONFIRM not known | 5 | 5 | 5 | 4 | **19** |
| S2#5 | negative-intent cache ("I don't know") | 5 | 4 | 5 | 4 | **18** |
| S5#11 | re-derive test = cache proof | 4 | 5 | 5 | 4 | **18** |
| S3#1 | per-lane cache-hit accounting | 4 | 4 | 4 | 5 | **17** |
| S3#4/#12 | serving-window coherence epoch + receipt | 4 | 4 | 5 | 4 | **17** |
| S1#8 | receipt honesty `supersedes_version` | 5 | 4 | 5 | 3 | 17 |
| S4#6 | vector_id parity invalidation | 5 | 4 | 5 | 3 | 17 |
| S5#6 | "cache word poisons authority" (neg) | 5 | 5 | 5 | 2 | 17 |
| S2#2 | context over-fit guard (embedding radius) | 4 | 4 | 5 | 4 | 17 |
| S1#3 | fact_survival = version entropy ratio | 4 | 3 | 5 | 4 | 16 |
| S4#10 | near-dup receipt `exact` flag | 5 | 3 | 5 | 3 | 16 |
| S5#4 | coherence stage vs superseding bookings | 4 | 4 | 5 | 3 | 16 |
| S1#1 | access-frequency demotion + receipt | 4 | 4 | 4 | 3 | 15 |
| S4#2 | write-time embedding dedup | 4 | 4 | 4 | 3 | 15 |
| S1#11 | demotion receipt-theater trap (neg) | 5 | 3 | 5 | 2 | 15 |
| S3#8 | provider price-illusion trap (neg) | 5 | 3 | 5 | 2 | 15 |
| S5#1 | cell as materialized view | 4 | 4 | 4 | 3 | 15 |

(everything else scored < 15 — mostly variants or restatements.)

### The three winners (and why)

1. **S3#1 (+ #4/#12 folded in) — LANE CACHE ACCOUNTING + SERVING-WINDOW EPOCH.** Won
   because it is the only surface we can measure TODAY with no new infra: this very thread
   is a live specimen (DeepInfra returns `prompt_tokens_details.cached_tokens`; our
   one-model-per-thread doctrine is the test). It converts our own doctrine into a receipt,
   and folds in the XP-C finding (a serving window IS a coherence epoch) so determinism/cost
   claims carry an epoch id.
2. **S2#5 + #10 — NEGATIVE-INTENT CACHE WITH COMPILE-BACK-AT-CONFIRM.** Won because the
   pincher seam is shipped and live (pinch → known/CONFIRM/ESCALATE at <50ms). These two
   ideas together close the worst failure of an answer-cache: serving a confidently wrong
   answer forever. "I don't know" cached with a TTL, and every compile-back row starts at
   CONFIRM (not known) until N uses or an outcome signal. Highest HONEST+PROBE.
3. **S5#11 — RE-DERIVE TEST = CACHE PROOF.** Won because it answers the surface-5 question
   ("is a cell a cache?") operationally instead of ontologically: a cell is a cache IFF its
   content is re-derivable (hash-match a rebuild) from bookings+tile_versions. Buildable as a
   Worker route; connects straight to XP-C (a non-deterministic seat makes re-derivation flaky
   → the test must declare its determinism window). 4050-testable.

**Runner's reservations the design had to respect:** (a) provider cache metrics are
provider-reported — treat `cached_tokens` as a CLAIM, verify by prefix hash; (b) the negative
cache must not become a permanent "I don't know" wall — TTL + tile-write invalidation both
required; (c) Design 3 cannot use the 4050 as the rebuild engine for anything replay-sensitive
— XP-C proved the local seat is not byte-replay-safe under co-tenancy.

### Hy3's strongest objection to the selection (verbatim)

> Strongest objection: the three winners are individually coherent but share a blind spot —
> none instruments the **cross-ledger coherence gap** as a first-class receipt (S5#6 warns
> "cache" poisons authority, yet #3 still calls a cell a cache pre-proof). If S5#11 runs on
> CPU-deterministic rebuild but S3 epoch uses GPU-window claims, the fleet mixes coherence
> domains without a unifying epoch id. Respecting (a)(b)(c): prefix-hash verify, TTL+write-
> invalidate, CPU-only rebuild.

*(Runner ack: this objection is correct and is carried into the prereg — the probe must
declare an engine, and the epoch must be shared across ledgers.)*

---

## §3 — R3 ROUGH-OUT (verbatim designs from Hy3)

### DESIGN 1 — LANE CACHE ACCOUNTING + SERVING-WINDOW EPOCH
- **INTERFACE:** MCP `log_lane_usage({lane, model, cached_tokens, total_tokens, prefix_hash, epoch_id, ts})`;
  D1 `CREATE TABLE lane_usage(id INTEGER PRIMARY KEY, lane TEXT, model TEXT, cached_tokens INT, total_tokens INT, prefix_hash TEXT, epoch_id TEXT, ts INT); CREATE INDEX idx_lane_ts ON lane_usage(lane,ts);`
  KV `epoch:{lane}:{id}` → `{valid_until, gpu_window, model}`.
- **DATA FLOW:** WRITE — Worker on each `/chat/completions` response calls `log_lane_usage` with provider `cached_tokens` + computed `prefix_hash` of sent prefix; opens epoch on thread start. READ — `get_lane_hitrate(lane, since)` aggregates; hit = `cached_tokens/total_tokens`; escape: prefix_hash mismatch vs sent → `cached_claim_false`.
- **INVALIDATION / COHERENCE:** stale if `epoch.valid_until < now()`; watermark = `epoch_id`; epoch = serving window (XP-C); thread valid only inside epoch.
- **RECEIPTS / OBSERVABILITY:** books `gamma=$ delta`, `cached_tokens`; route `GET /lane-metrics` shows hit-rate; honesty field `prefix_hash_verified=0` on mismatch → "claimed cached, recomputed".
- **ROUGH COST:** ~5k rows/day D1 (free: 100k/day). Vectorize 0. KV ~10 epoch keys. Fits free tier.
- **SMALLEST FALSIFIABLE PROBE:** Worker route replays a fixed prompt, compares `prefix_hash` sent vs provider `cached_tokens>0`; pass = hash match & cached>0, fail = mismatch. Engine: CF Worker (deterministic hash, no GPU).

### DESIGN 2 — NEGATIVE-INTENT CACHE + COMPILE-BACK-AT-CONFIRM
- **INTERFACE:** MCP `upsert_intent({intent, context, reflex, confidence, vector_id, neg_ttl})`;
  D1 `ALTER TABLE intents ADD COLUMN neg_ttl INT; ADD COLUMN confirm_uses INT DEFAULT 0;`
  KV `negintent:{vector_id}` → `{reflex, expires}`.
- **DATA FLOW:** WRITE — ESCALATE→null writes `reflex='NULL', confidence=0.95, neg_ttl=now+7d, context='neg'`. Compile-back writes `confidence=0.75, confirm_uses=0` (CONFIRM); on `uses`≥10 or booking success → `confidence=0.92`. READ — pinch hits neg → "don't know" <50ms if `neg_ttl>now()`; escape: tile write invalidates KV neg.
- **INVALIDATION / COHERENCE:** stale if `tile_versions.ts > neg_ttl` or `neg_ttl` expired; watermark = `tile_versions.lamport`; epoch = vector index ts.
- **RECEIPTS / OBSERVABILITY:** books `eta=surprise`; route `GET /intent-quality` shows neg-hit vs contradiction; honesty `neg_expired=1` served as known → flagged.
- **ROUGH COST:** ~500 intents/day D1 (free). Vectorize ~5k `/near` day (free 100k). KV ~100 neg keys. Fits.
- **SMALLEST FALSIFIABLE PROBE:** script inserts a neg intent, waits TTL, asserts returns ESCALATE not "don't know"; pass = 412 after TTL. Engine: CF Worker (no GPU).

### DESIGN 3 — RE-DERIVE TEST = CACHE PROOF
- **INTERFACE:** MCP `rebuild_cell({room_id, engine})` → `rebuild_hash`;
  D1 `CREATE TABLE cell_proof(room_id TEXT, stage INT, rebuild_hash TEXT, src_watermark INT, engine TEXT, ts INT, PRIMARY KEY(room_id,stage));`
  KV `cellproof:{room_id}` → `{hash, watermark, engine, ts}`.
- **DATA FLOW:** WRITE — nightly Worker runs `rebuild_cell` on CPU-deterministic (replay bookings+versions→tiles hash); match vs live tiles hash → `cell_proof` row; mismatch → authority lock. READ — query `cell_proof` to route cell-as-cache (match) vs authority (diff).
- **INVALIDATION / COHERENCE:** stale if `bookings.lamport > src_watermark`; watermark = `max(lamport)`; epoch = CPU run id (no GPU).
- **RECEIPTS / OBSERVABILITY:** books `gamma=rebuild_cost`; route `GET /cell-proof` shows match rate; honesty `engine='cpu'` only, `gpu_used=0` enforced.
- **ROUGH COST:** ~10 rooms/day rebuild, D1 10 rows. Vectorize 0. KV 10 keys. Free tier.
- **SMALLEST FALSIFIABLE PROBE:** script feeds known bookings to CPU rebuild, asserts hash stable across 3 runs; pass = identical hash, fail = diff. Engine: deterministic CPU (WSL2 CPU, not 4050).
- **BUILD ORDER: 2, 1, 3** — negative-intent closes live wrong-answer risk first; lane accounting needs no new table shape; cell-proof last as it depends on ledger stability.

---

## §4 — R4 RED-TEAM (verbatim from Hy3)

**1. First-week ship-wrong + catch:**
- D1 (lane acct): Worker logs `cached_tokens` but forgets `prefix_hash` on 30% of paths → claim unverified silently. Catch: D1 query `WHERE prefix_hash IS NULL` alert >0.
- D2 (neg-intent): `neg_ttl` set but tile-write invalidation misses because the trigger keys on `tiles` not `tile_versions` → neg served past write. Catch: KV neg `expires` vs `tile_versions.ts` diff monitor.
- D3 (re-derive): rebuild runs on CPU but pulls `tile_versions` including GPU-compiled rows → hash flaky, not caught as an engine violation. Catch: assert `engine='cpu'` in `cell_proof` + block GPU-sourced rows.

**2. Hidden cross-design dependency:** D2 neg-intent uses Vectorize `vector_id` ts as epoch; D1 lane epoch is a GPU-window id. A neg intent compiled in lane epoch E but vector reindexed in E' → D2 says stale, D1 says warm. They disagree on "stale" with no join key. Fix: share `epoch_id` across KV.

**3. Self-grade:** Weakest — never specified the exact D1 triggers / Worker cron for D2 invalidation or D3 nightly (left as "Worker on write" hand-wave), so BUILD concreteness is weak there. Failed to answer: how `intents` UNIQUE(intent,context) interacts with a `context='neg'` collision (multiple rooms, same phrasing → one neg row, wrong scope). Also skipped cost of `rebuild_cell` CPU time at 10k rooms (not 10).

**4. Skipped idea worth keeping:** S1#3 (`fact_survival = version entropy`) scored 15; fleet skips it. Wrong: the entropy ratio is the only demotion signal that doesn't need access logs — it works cold. Access-frequency needs traffic we don't have yet; entropy is computable from `tile_versions` today and gates bad gists pre-launch.

---

## §5 — DOG-FOOD VERDICT: Hy3 as an expert seat

**Expansion quality — A−.** 60 ideas, none filler; each carries a *named, detectable* failure
mode and an escape, and almost all are anchored to the real schema (it used actual columns,
the UNIQUE(intent,context) constraint, the tier CHECK, the γ/η semantics). It re-derived the
same underlying principle — *a cache hit is a claim that needs a receipt* — independently in
all five surfaces, which is a genuine signal, not repetition. Negative results are first-class
(S1#11 receipt-theater trap, S2#9 context collapse, S4#9 index-growth trap, S5#6 "cache word
poisons authority"). This is exactly the tapestry doctrine.

**Design quality — B.** The R3 template is followed tightly and the DDL/KV shapes are
buildable as written. Two weaknesses, both self-identified in R4 (which is worth credit): the
invalidation mechanisms are hand-waved as "Worker on write" instead of a concrete D1 trigger /
cron schedule, and Design 3's probe as specified dodges the interesting engine question by
declaring CPU-only (a correct reading of my constraint (c), but it means the design doesn't
*itself* test the 4050 claim — the runner extends it in the prereg). Its R4 red-team found a
real cross-design coherence bug (two different notions of "epoch"/stale with no join key) —
that is a high-value catch.

**Hallucinations observed (concrete, minor, flagged):**
- **Invented columns.** It repeatedly says `bookings.lamport` and implies `intents` versioning
  — **neither table has a `lamport` column** (only `tiles` does). The *pattern* is defensible
  (those seams need a watermark), but as written the SQL would not run. This is the single most
  common factual slip across the session.
- **Invented platform quotas.** "DeepInfra bills minimum 1 min kept-warm per prefix" (S3#8) is
  stated as fact and is almost certainly fabricated; "Vectorize free: 100k `/near` day" (D2) is
  an approximation dressed as a limit. D1's "free: 100k rows/day" is roughly right. **Rule: any
  Hy3 platform-quota/price claim must be verified against docs before it enters a design.**
- No broken-reasoning hallucinations: it never invented a schema relation that would make a
  design incoherent, and it never faked a receipt.

**Which tasks it suits:**
- ✅ **R1-class expansion** with a schema in the prompt (its failure-mode-first discipline is
  strong and cheap).
- ✅ **Red-teaming / adversarial review** of its own or others' designs (found the cross-design
  epoch bug unprompted).
- ✅ **Doctrine synthesis** — turning "what is preferred when" into concrete cache mechanisms.
- ⚠️ **Not** for exact platform facts (quotas/prices/column inventories) without a verifier.
- ⚠️ **Not** for concrete scheduler/trigger engineering (it stops at prose).

**VERDICT: KEEP as a standing expert seat** (grade **B+**), with a standing rider: *verify any
platform-quota, price, or column-inventory claim against the schema/docs before shipping; do
not let it author triggers/cron without a concrete pass.* Cost is trivial (8 calls, ~52.7k
prompt tokens at 80.3% cached ≈ fractions of a cent).

**Hy4-preview trial? YES — but targeted, not wholesale.** Run a single-surface head-to-head on
**Surface 3** (provider prompt-cache economics), the surface where factual platform knowledge
matters most and where Hy3's quota hallucinations live. If Hy4-preview fixes the quota/price
facts and keeps the failure-mode discipline, promote it for the *economics* surfaces while
keeping Hy3 for expansion/red-team. If it doesn't, Hy3 stays. (One lane, ≤6 calls, same
one-model-per-thread protocol.)

---

## §6 — Probe / prereg

One 4050-testable probe was specified: **HY3C-rederive-coherence** —
`/home/eileen/projects/quilt-gpu-lab/proposals/runs/HY3C-rederive-coherence.md`.
It extends Design 3 to the engine question Hy3 (correctly) sidestepped: *is re-derivability of
a cell a property of the engine/serving-window?* Claim: CPU-derivable content is a cache;
LLM(4050)-derived content is an authority, because the local seat is not byte-replay-safe under
co-tenancy (XP-C). **Prereg only — no GPU run fired.**

Design 1 and Design 2 probes are **CF-Worker-testable** (no GPU), so they need no GPU prereg —
they are Worker route changes + a script, to be scheduled by the keeper.

---

## Appendix A — Live cache receipt for this lane (Surface-3 specimen)

Per-call usage from `tencent/Hy3` (one model, one continued thread):

| tag | prompt_tokens | cached_tokens | completion | cache hit |
|---|---|---|---|---|
| R1.1-tile-tiers | 742 | 720 | 1468 | 0.970 |
| R1.2-pinch-compileback | 2485 | 848 | 1420 | 0.341 |
| R1.3-provider-prompt-cache | 4210 | 2544 | 1390 | 0.604 |
| R1.4-near-semantic-cache | 5859 | 4336 | 1379 | 0.740 |
| R1.5-quilt-cell-as-cache | 7538 | 5984 | 1360 | 0.794 |
| R2-curate | 9882 | 7616 | 119 | 0.771 |
| R3-designs | 10310 | 9984 | 1253 | 0.968 |
| R4-redteam | 11715 | 10320 | 465 | 0.881 |
| **TOTAL** | **52741** | **42352** | **8854** | **0.803** |

Reading: the prefix cache stays hot precisely because the thread is continued (doctrine
"one model per thread" validated on our own traffic) — hit fraction climbs from ~0.34 (early,
short prefix, cache still warming) to 0.88–0.97 once the prefix stabilizes. This table *is*
Design 1's receipt, produced by hand for one lane.

## Appendix B — Artifacts

- Raw transcript (all 8 turns, full message array): `docs/_hy3_lane_state.json`
- Drivers: `scripts/hy3_lane_cache.py` (thread + API), `scripts/hy3_lane_r1.py` (R1),
  `scripts/hy3_lane_r2r3.py` (R2–R4)
- Prereg: `/home/eileen/projects/quilt-gpu-lab/proposals/runs/HY3C-rederive-coherence.md`
- Secret handling: key read at use-time from `/home/eileen/.config/deepinfra/token`;
  never echoed, logged, or written to any artifact (this doc included).

---

# §7 — HY4-PREVIEW TRIAL (lane HY4-TRIAL)

**Lane:** HY4-TRIAL (follow-up to HY3-CACHE) · **Runner (curator):** deepseek-v4-flash
· **EXPERT SEAT:** `tencent/Hy4-preview` via DeepInfra OpenAI-compatible API (live 2026-10-01)
· **Target:** the targeted head-to-head HY3 recommended — **single surface (Surface 3,
provider prompt-cache economics)**, Hy4-preview vs Hy3.

**Goal (from HY3 §5 rider):** test whether Hy4-preview fixes the quota/price/column
hallucinations that Hy3 produces on the surface *where factual platform knowledge matters
most*, while keeping the failure-mode discipline.

**Method.** Same standing expert system prompt (the §-in-quoted brief Hy3 got, reused
verbatim from `scripts/hy3_lane_cache.py`), same Surface-3 expansion brief
(`scripts/hy3_lane_r1.py::R1.3`), one continued message array (cache doctrine practiced),
**3 calls** (≤6 budget): (1) R1.3 expansion, (2) fact self-audit, (3) self-red-team.
Driver: `scripts/hy4_trial.py` · raw transcript: `docs/_hy4_trial_state.json`.
Key read at use-time; never echoed/logged/written.

**Disclosed asymmetry (fairness).** Calls 2–3 are a Hy4-only probe: Hy3 was never asked to
audit its own facts. The *primary* comparison is call 1, where both models answered the
*identical* brief cold. Hy3's quotes are pulled from its expansion/design transcript
(`docs/_hy3_lane_state.json`); Hy4's from its expansion + audit.

## 7.1 — Live trial receipt (Hy4-preview, one continued thread)

| tag | prompt_tokens | cached_tokens | completion | cache hit | reasoning chars |
|---|---|---|---|---|---|
| HY4.R1.3-expansion | 783 | 0 | 6000 | 0.000 | 15,280 |
| HY4.R2-fact-self-audit | 3,298 | 512 | 6000 | 0.155 | 15,188 |
| HY4.R4-red-team | 5,742 | 2,816 | 4,383 | 0.490 | 15,213 |
| **TOTAL** | **9,823** | **3,328** | **16,383** | **0.339** | 45,681 |

Reading: same warm-prefix doctrine holds (hit fraction climbs 0.00 → 0.49 as the prefix
stabilizes — the same shape Hy3 showed early in its run, 0.34 → 0.60 over its first calls).
**Both calls 1–2 hit the `max_tokens=6000` ceiling**, and ~15.2k chars of hidden
`reasoning_content` were emitted per call: Hy4-preview is a long-reasoning model whose
chain-of-thought competes for the same completion budget as the answer, so **the R1
expansion truncated inside idea 10** (Hy3 answered 12 complete ideas). Practical rider:
give Hy4 ≥2× the output budget.

## 7.2 — Side-by-side facts table (claim · Hy3 said · Hy4 said · ground truth)

Ground truth = DeepInfra `GET /v1/openai/models` metadata (live 2026-10-01, fetched by
`scripts/hy4_groundtruth.py`), Cloudflare docs (D1/Vectorize/KV pricing pages, Apr 2026),
DeepInfra prompt-caching docs + retention blog (Aug 2026), and `schema.sql`.

| # | Claim | Hy3 said | Hy4 said | Ground truth | Winner |
|---|---|---|---|---|---|
| 1 | DeepInfra cache billing | “DeepInfra **bills minimum 1 min kept-warm per prefix**” (S3#8), asserted as fact | No fee asserted; audit: ~60% that caches have a retention window, source=**inference**, no number given | **FALSE.** Automatic prefix cache is best-effort, no minimum kept-warm fee. Explicit retention is opt-in (`prompt_cache_options {mode:explicit, ttl:5m\|1h}`), billed a **write premium upfront** (`cache_write_tokens`), reused at cache-read rate. | **Hy4** (abstained) |
| 2 | Vectorize free quota | “Vectorize ~5k/`near` day (**free 100k**)” (D2 rough cost) | No quota asserted | **FALSE.** Workers Free = **30M queried vector dimensions/month**, 5M stored dims. No 100k/day `/near` allowance exists. | **Hy4** (abstained) |
| 3 | D1 free write quota | “~5k rows/day D1 (**free: 100k/day**)” (D1 rough cost) | No quota asserted (proposed a table, no limit claim) | **TRUE.** D1 Workers Free = **100,000 rows written/day** (5M read/day, 5 GB). | **Hy3** |
| 4 | `bookings.lamport` column | Used `bookings.lamport` / `max(bookings.lamport)` as a watermark (4 occurrences) | Never used; put watermarks in proposed tables | **FALSE.** `bookings` = id, agent, gist, body, receipt_url, books_to, vector_id, gamma, eta, ts, embedded. **No `lamport`.** | **Hy4** |
| 5 | `intents` version/lamport | Implied intents versioning | Not claimed | **FALSE.** `intents` = id, intent, context, reflex, confidence, vector_id, uses, created_ts, updated_ts. No `lamport`. | **Hy4** |
| 6 | `demotion_receipts` columns | `(tile_id, from_tier, to_tier, fact_survival, lattice_snap, method, ts)` | Wrote `demotion_receipts(tile_id, **version**, **reason**='epoch_close')` (idea 3); audit half-misattributed `version` to “the environment” | **Hy3 EXACT.** Real columns = tile_id, from_tier, to_tier, fact_survival, lattice_snap, method, ts. Real fix: invent `reason`/`method` usage, not `version`. | **Hy3** (Hy4 minor slip, disclosed) |
| 7 | Seat model prices (per 1M) | No per-token price asserted (only “fractions of a cent” for its own lane) | Audit: “All specific prices are **unsourced numbers I did not give**” — 0% on pricing | **Hy3** $0.13 in / **$0.033 cache-read** / $0.53 out · **Hy4-preview** $0.834 in / **$0.042 cache-read** / $2.501 out. | **tie** (both abstained) |
| 8 | Seat model facts | 295B MoE, 21B active, 3.8B MTP, ctx 262,144 | Never asserted its own arch | **Confirmed** (metadata): Hy3 295B MoE/21B active/262k ctx; Hy4-preview 770B MoE/49B active/1M ctx/**Gated DeepSeek Sparse Attention + IndexCache**, tags `prompt_cache`,`reasoning`. | **tie** (both silent / correct) |

**Facts score.** Checkable platform claims Hy3 volunteered: **2 true / 4 false** (~33%) —
and the two fabrications (#1, #2) are exactly the price/quota class the rider warned about.
Hy4-preview volunteered **0 fabricated platform facts** (1 minor schema slip, #6, which its
own audit surfaced) and explicitly abstained on every price/quota it could not source.
**Hy4 = A; Hy3 = D** on this surface's fact axis.

## 7.3 — Expansion quality (identical brief)

- **Hy3:** 12 complete ideas, dense, schema-anchored, each with a named failure +
  detect + escape. Re-derived “a hit is a claim needing a receipt” independently.
- **Hy4-preview:** 10 ideas (11th truncated by output budget), each **MECHANISM + HOW IT
  FAILS (stale/thrash/poison/coherence + detect + escape)**. Several are *sharper* than
  Hy3's: idea 2 replaces “one model per thread” doctrine with an enforceable
  **`prefix_hash` lease + fencing tokens**; idea 3 makes the **serving window a first-class
  `cache_epochs` row** carrying `gpu_uuid`/`driver_version`/`model_sha`; idea 8 adds a
  `model_pricing` join so blended cost isn't averaged across providers; idea 6 correctly
  scopes determinism to `seed ∧ epoch_id`.
- **Verdict on expansion:** *quality* — Hy4 ≥ Hy3 (deeper on the exact epoch/lease coupling
  Hy3 only gestured at); *volume/throughput* — Hy3 wins (12 complete vs 10 truncated, and
  ~4× cheaper). Both are failure-mode-first; neither is filler.

## 7.4 — Failure-mode honesty (verbatim evidence)

**Hy4 self-audit (call 2), verbatim:**
> “**Confidence:** 100% that I proposed exactly this schema; **0% confidence this corresponds
> to any existing production table.** … **Source:** My own design proposal / invention. Not
> from D1/docs/spec.” — and, on pricing: “**All specific prices are unsourced numbers I did
> not give.**”

**Hy4 self-red-team (call 3), verbatim:**
> “The lease is keyed on `prefix_hash` alone. But the *same* `prefix_hash` can be served
> across different `epoch_id`s … **Fix: book on `(prefix_hash, epoch_id)`, not `prefix_hash`
> alone.**”  — and it named its own truncated idea 10 as the weakest, and identified the
> unanswered half of the brief (“who calls `rotate`? what stops two lanes double-rotating?”).

**Hy3 red-team (R4), verbatim:** found a real cross-design epoch bug too — “D2 … uses
Vectorize `vector_id` ts as epoch; D1 lane epoch is a GPU-window id … They disagree on
‘stale’ with no join key.” The findings are the same *shape*; Hy4's is stated as an
enforcement fix. **Hy4 = A; Hy3 = B+** on honesty — Hy4 volunteers “I did not verify this”
unprompted; Hy3's defect (§0) is that its fabrications were stated as fact and only
caught by the runner's later verification.

## 7.5 — Does 1M-context + Gated-DSA show an expansion-quality difference?

**Null result, honest.** The Hy4 thread never exceeded **5,742 prompt tokens** — two orders
of magnitude below its 1M window — so long-context capability was *not exercised* and cannot
be credited for the quality delta. Gated DeepSeek Sparse Attention + IndexCache is a
prefill/attention-efficiency mechanism (latency/cost per token), invisible in answer
quality at this prefix size. The observed delta is **post-training, not architecture**:
~15.2k chars of hidden reasoning per call, markedly higher calibration (`0% confidence`,
explicit abstention, adversarial self-audit), and lower hallucination. What *is* attributable
to the 770B/1M/engineering-post-trained profile is **behaviour**: it chooses to abstain and
to flag its own unverified claims, whereas Hy3 fills the gap with a confident number.
Caveat: n=1 thread, single surface.

## 7.6 — Cost (the irony worth booking)

| lane | calls | prompt | cached | output | est. cost |
|---|---|---|---|---|---|
| Hy3 (Surface-3 lane, full) | 8 | 52,741 | 42,352 | 8,854 | **$0.0074** |
| Hy4-preview (this trial) | 3 | 9,823 | 3,328 | 16,383 | **$0.0465** |

Hy4-preview costs **~6.4× more on fresh input** ($0.834 vs $0.13/M), **4.7× on output**
($2.501 vs $0.53/M), and — the punchline for a *cache-economics* surface — **1.27× more on
cache-read tokens** ($0.042 vs $0.033/M). So the model that is *better at reasoning about
prompt-cache economics* is itself the *worse cache-read unit*. Any lane promoted to Hy4 for
volume would eat that premium on every cached call; at cached-read alone Hy4 ≈ +27%.

## 7.7 — VERDICT

> **PROMOTE `tencent/Hy4-preview` for the economics SURFACES — as the fact-bearing author,
> NOT as the cost engine. Hy3 stays** for bulk expansion/red-team and for any cost-sensitive
> lane.

Rationale: the rider's test was “does Hy4 fix the quota/price facts while keeping the
failure-mode discipline?” — **yes, decisively** (0 fabricated platform facts vs Hy3's 4;
self-audit and self-red-team are first-class). But the ground-truth price table flips the
naive reading: Hy4-preview is the **more expensive** seat on every axis (6.4×/4.7×/1.27×),
so promoting it wholesale would *spend more to save less* on the very surface it wins.

**Standing riders for Hy4-preview:**
1. **Fact-bearing only.** Use Hy4 for Surface-3-class *claims* (prices, quotas, cache
   semantics); route volume expansion and cost-sensitive bulk to Hy3. (Both cars, right lane.)
2. **Budget for reasoning.** It burns ~15k chars of hidden reasoning per call and will
   truncate at `max_tokens=6000`; give it ≥12k output tokens for schema-dense asks.
3. **Diff every schema proposal against `schema.sql` before shipping** — Hy4 clearly labels
   proposals, but it still invented `demotion_receipts.version` and half-attributed it to the
   environment. The gate is the same as Hy3's; Hy4 just tells you when it's guessing.
4. **n=1 caveat:** one surface, one thread. Re-test on a second economics surface before
   making this a standing routing rule (per the fleet's own probe discipline).

---

## Appendix C — HY4-TRIAL artifacts

- Raw transcript: `docs/_hy4_trial_state.json` (3 turns, full message array + reasoning)
- Drivers: `scripts/hy4_trial.py` (trial), `scripts/hy4_groundtruth.py` (metadata fetch)
- Ground-truth sources (fetched live 2026-10-01): DeepInfra `/v1/openai/models`;
  `docs.deepinfra.com/chat/prompt-caching`; `deepinfra.com/blog/prompt-cache-retention`;
  Cloudflare D1 / Vectorize / KV pricing pages; `schema.sql`.
- Secret handling: identical to Appendix B — read at use-time, never written.
