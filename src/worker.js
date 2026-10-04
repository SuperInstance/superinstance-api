/**
 * superinstance-api — the fleet's growing context brain, with MCP tooling.
 * Design receipt: ../README.md   Schema: ../schema.sql
 *
 * Five seams:
 *   Authority  tiles/rooms, Lamport versions, tiers full>gist>hint (plato-cf)
 *   Meaning    bge-m3 -> Vectorize, /near recall (i2i-ledger pattern)
 *   Reflex     pinch: semantic intent-match -> FIRE/CONFIRM/ESCALATE (pincher)
 *   Field      gamma (compute) + eta (surprise) on bookings; conservation view (exoj/quilt-dba)
 *   Growth     rooms stage-tagged; adding cells = advancing stages (quilt-dba)
 *
 * REST routes:
 *   GET  /health                      (no auth)
 *   POST /book                        {gist, body?, receipt_url?, books_to?, gamma?, eta?, ts?}
 *   GET  /near?q=&k=
 *   GET  /since?ts=
 *   POST /room {name}   /  GET /rooms
 *   PUT  /rooms/:id/cells {title, body?}   — growth seam: add canon cell = advance stage (receipted)
 *   GET  /rooms/:id/cells                  — cells + stage + stage-advance receipts (:id = id or name)
 *   POST /tile {room,key,content,tier?}  /  GET /tile?room=&key=  /  GET /tile/history?room=&key=
 *   POST /tile/demote {room,key,to_tier,content?,fact_survival?,lattice_snap?,method}
 *   POST /pinch {intent, context?}
 *   POST /pinch/compile {intent, reflex, confidence, context?}
 *   GET  /field?agent=     /  GET /witness?id=
 *   POST /mcp                         JSON-RPC 2.0 (initialize, tools/list, tools/call)
 *
 * Auth: Authorization: Bearer <token>; env SI_API_TOKENS = "agent:token,agent:token".
 * The token's agent name attributes every booking — identity comes from the credential.
 * Bindings: DB = D1, INDEX = Vectorize (1024-d cosine), AI = Workers AI.
 */

const EMBED_MODEL = "@cf/baai/bge-m3"; // 1024-dim
const EMBED_DIMS = 1024;
const TIER_ORDER = { full: 2, gist: 1, hint: 0 };
const PINCH_FIRE = 0.92;      // >= : known reflex fires, zero LLM
const PINCH_CONFIRM = 0.75;   // between: candidate returned for confirmation

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2) + "\n", {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function nowSec() { return Math.floor(Date.now() / 1000); }

function str(v) { return typeof v === "string" ? v.trim() : ""; }

function bearerToken(request) {
  const m = /^Bearer\s+(.+)$/.exec(request.headers.get("Authorization") || "");
  return m ? m[1].trim() : null;
}

function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

/** Returns the agent name owning this token, or null. */
function auth(request, env) {
  const token = bearerToken(request) || "";
  for (const pair of (env.SI_API_TOKENS || "").split(",")) {
    const i = pair.indexOf(":");
    if (i <= 0) continue;
    if (safeEqual(token, pair.slice(i + 1).trim())) return pair.slice(0, i).trim();
  }
  return null;
}

/** Accept epoch seconds or milliseconds; default now. Integer seconds. */
function normalizeTs(v) {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return nowSec();
  return n > 1e12 ? Math.floor(n / 1000) : Math.floor(n);
}

function clampInt(v, lo, hi, dflt) {
  const n = parseInt(v, 10);
  if (!Number.isFinite(n)) return dflt;
  return Math.max(lo, Math.min(hi, n));
}

async function embed(env, text) {
  const res = await env.AI.run(EMBED_MODEL, { text: [text] });
  const raw = res && Array.isArray(res.data) ? res.data[0] : null;
  const vector = Array.isArray(raw) ? raw
    : raw && Array.isArray(raw.embedding) ? raw.embedding : null;
  if (!Array.isArray(vector) || vector.length !== EMBED_DIMS) {
    throw new Error("bad embedding from " + EMBED_MODEL);
  }
  return vector;
}

async function sha256hex32(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}

// ───────────────────────────── core operations ─────────────────────────────

async function coreBook(args, env, agent) {
  const gist = str(args.gist);
  if (!gist) throw new HttpError(400, "gist is required");
  const body = typeof args.body === "string" ? args.body : "";
  const receiptUrl = str(args.receipt_url);
  const booksTo = str(args.books_to);
  // token identity wins over claimed agent — bookings attribute honestly
  const who = agent || str(args.agent);
  if (!who) throw new HttpError(400, "agent required (token or body)");
  const gamma = clampInt(args.gamma, 0, 1e9, 0);
  const eta = clampInt(args.eta, 0, 100000, 0);
  const ts = normalizeTs(args.ts);
  const id = crypto.randomUUID();

  // D1 row of record first; vector lag reported honestly (embedded:false, 207).
  await env.DB.prepare(
    "INSERT INTO bookings (id, agent, gist, body, receipt_url, books_to, gamma, eta, ts, embedded) " +
    "VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,0)"
  ).bind(id, who, gist, body, receiptUrl, booksTo, gamma, eta, ts).run();

  try {
    const vector = await embed(env, (gist + "\n" + body).trim());
    // Empty-string metadata values get upserts rejected — omit absent fields.
    const meta = { kind: "booking", agent: who, ts };
    if (receiptUrl) meta.url = receiptUrl;
    await env.INDEX.upsert([{ id, values: vector, metadata: meta }]);
    await env.DB.prepare("UPDATE bookings SET embedded=1, vector_id=?1 WHERE id=?2").bind(id, id).run();
    return { ok: true, id, agent: who, ts, gamma, eta, embedded: true };
  } catch (err) {
    return { ok: true, id, agent: who, ts, gamma, eta, embedded: false, error: String(err) };
  }
}

async function coreNear(args, env) {
  const q = str(args.q);
  if (!q) throw new HttpError(400, "q is required");
  const k = clampInt(args.k, 1, 50, 8);
  const vector = await embed(env, q);
  const res = await env.INDEX.query(vector, { topK: k, returnMetadata: "all" });
  const matches = (res && res.matches) || [];
  const ids = matches.map((m) => m.id);
  const byId = new Map();
  if (ids.length) {
    const ph = ids.map((_, i) => "?" + (i + 1)).join(", ");
    const rows = await env.DB.prepare(
      "SELECT id, agent, gist, body, receipt_url, books_to, gamma, eta, ts FROM bookings WHERE id IN (" + ph + ")"
    ).bind(...ids).all();
    for (const r of (rows && rows.results) || []) byId.set(r.id, r);
  }
  return {
    query: q, k,
    eta_measured: matches.length ? Math.round(1000 * (1 - matches[0].score)) : 1000,
    matches: matches.map((m) => ({
      id: m.id, score: m.score,
      kind: (m.metadata && m.metadata.kind) || null,
      meta: m.metadata || null,
      booking: byId.get(m.id) || null,
    })),
  };
}

async function coreSince(args, env) {
  if (args.ts == null || str(String(args.ts)) === "") throw new HttpError(400, "ts is required (epoch seconds)");
  const ts = normalizeTs(args.ts);
  const rows = await env.DB.prepare(
    "SELECT id, agent, gist, receipt_url, books_to, gamma, eta, ts, embedded FROM bookings WHERE ts > ?1 ORDER BY ts ASC LIMIT 500"
  ).bind(ts).all();
  return { after: ts, count: ((rows && rows.results) || []).length, entries: (rows && rows.results) || [] };
}

async function getRoom(env, name) {
  return env.DB.prepare("SELECT id, name, stage, created_ts FROM rooms WHERE name=?1").bind(name).first();
}

/** Growth seam addresses rooms by id (digits) or name — both resolve honestly. */
async function resolveRoom(env, idOrName) {
  if (/^\d+$/.test(idOrName)) {
    const byId = await env.DB.prepare("SELECT id, name, stage, created_ts FROM rooms WHERE id=?1").bind(Number(idOrName)).first();
    if (byId) return byId;
  }
  return getRoom(env, idOrName);
}

async function coreRoomCreate(args, env) {
  const name = str(args.name);
  if (!name) throw new HttpError(400, "name is required");
  const stage = clampInt(args.stage, 1, 100, 1);
  const existing = await getRoom(env, name);
  if (existing) return { ok: true, room: existing, existed: true };
  const ts = nowSec();
  const ins = await env.DB.prepare("INSERT INTO rooms (name, stage, created_ts) VALUES (?1,?2,?3)").bind(name, stage, ts).run();
  return { ok: true, room: { id: ins.meta.last_row_id, name, stage, created_ts: ts }, existed: false };
}

async function coreRoomList(_args, env) {
  const rows = await env.DB.prepare("SELECT id, name, stage, created_ts FROM rooms ORDER BY id").all();
  return { rooms: (rows && rows.results) || [] };
}

async function coreTileWrite(args, env) {
  const room = str(args.room), key = str(args.key), content = str(args.content);
  if (!room || !key || !content) throw new HttpError(400, "room, key, content are required");
  const tier = str(args.tier) || "full";
  if (!(tier in TIER_ORDER)) throw new HttpError(400, "tier must be full|gist|hint");
  const roomRow = await getRoom(env, room);
  if (!roomRow) throw new HttpError(404, "room not found: " + room + " (POST /room first)");
  const ts = nowSec();
  const existing = await env.DB.prepare("SELECT id, lamport FROM tiles WHERE room_id=?1 AND key=?2").bind(roomRow.id, key).first();
  let tileId, lamport;
  if (existing) {
    tileId = existing.id; lamport = existing.lamport + 1;
    await env.DB.batch([
      env.DB.prepare("UPDATE tiles SET lamport=?1, content=?2, tier=?3, updated_ts=?4 WHERE id=?5").bind(lamport, content, tier, ts, tileId),
      env.DB.prepare("INSERT INTO tile_versions (tile_id, lamport, content, tier, ts) VALUES (?1,?2,?3,?4,?5)").bind(tileId, lamport, content, tier, ts),
    ]);
  } else {
    lamport = 1;
    const ins = await env.DB.prepare(
      "INSERT INTO tiles (room_id, key, lamport, content, tier, created_ts, updated_ts) VALUES (?1,?2,1,?3,?4,?5,?5)"
    ).bind(roomRow.id, key, content, tier, ts).run();
    tileId = ins.meta.last_row_id;
    await env.DB.prepare("INSERT INTO tile_versions (tile_id, lamport, content, tier, ts) VALUES (?1,1,?2,?3,?4)").bind(tileId, content, tier, ts).run();
  }
  let embedded = false, err = null;
  const vectorId = "tile:" + (await sha256hex32(room + "\u0000" + key));
  try {
    const vector = await embed(env, room + " / " + key + "\n" + content);
    await env.INDEX.upsert([{ id: vectorId, values: vector, metadata: { kind: "tile", room, key, ts } }]);
    await env.DB.prepare("UPDATE tiles SET vector_id=?1 WHERE id=?2").bind(vectorId, tileId).run();
    embedded = true;
  } catch (e) { err = String(e); }
  return { ok: true, room, key, lamport, tier, embedded, ...(err ? { error: err } : {}) };
}

async function resolveTile(env, room, key) {
  const roomRow = await getRoom(env, room);
  if (!roomRow) throw new HttpError(404, "room not found: " + room);
  const tile = await env.DB.prepare("SELECT * FROM tiles WHERE room_id=?1 AND key=?2").bind(roomRow.id, key).first();
  if (!tile) throw new HttpError(404, "tile not found: " + room + "/" + key);
  return tile;
}

async function coreTileGet(args, env) {
  const room = str(args.room), key = str(args.key);
  if (!room || !key) throw new HttpError(400, "room and key are required");
  const t = await resolveTile(env, room, key);
  return { room, key, content: t.content, tier: t.tier, lamport: t.lamport, updated_ts: t.updated_ts };
}

async function coreTileHistory(args, env) {
  const room = str(args.room), key = str(args.key);
  if (!room || !key) throw new HttpError(400, "room and key are required");
  const t = await resolveTile(env, room, key);
  const rows = await env.DB.prepare(
    "SELECT lamport, content, tier, ts FROM tile_versions WHERE tile_id=?1 ORDER BY lamport ASC"
  ).bind(t.id).all();
  return { room, key, versions: (rows && rows.results) || [] };
}

async function coreTileDemote(args, env) {
  const room = str(args.room), key = str(args.key);
  const toTier = str(args.to_tier), method = str(args.method);
  if (!room || !key) throw new HttpError(400, "room and key are required");
  if (!(toTier in TIER_ORDER)) throw new HttpError(400, "to_tier must be full|gist|hint");
  // Honesty pin: demotion is a measured act, never a guess.
  const factSurvival = args.fact_survival == null ? null : Number(args.fact_survival);
  const latticeSnap = args.lattice_snap == null ? null : Number(args.lattice_snap);
  if (!method || (factSurvival == null && latticeSnap == null)) {
    throw new HttpError(400, "demotion requires a measurement receipt: method + fact_survival and/or lattice_snap");
  }
  const t = await resolveTile(env, room, key);
  if (!(TIER_ORDER[toTier] < TIER_ORDER[t.tier])) {
    throw new HttpError(400, "to_tier must be a downgrade (current tier: " + t.tier + ")");
  }
  const content = str(args.content) || t.content; // caller may supply the compressed form
  const ts = nowSec();
  const lamport = t.lamport + 1;
  await env.DB.batch([
    env.DB.prepare("UPDATE tiles SET lamport=?1, content=?2, tier=?3, updated_ts=?4 WHERE id=?5").bind(lamport, content, toTier, ts, t.id),
    env.DB.prepare("INSERT INTO tile_versions (tile_id, lamport, content, tier, ts) VALUES (?1,?2,?3,?4,?5)").bind(t.id, lamport, content, toTier, ts),
    env.DB.prepare("INSERT INTO demotion_receipts (tile_id, from_tier, to_tier, fact_survival, lattice_snap, method, ts) VALUES (?1,?2,?3,?4,?5,?6,?7)")
      .bind(t.id, t.tier, toTier, factSurvival, latticeSnap, method, ts),
  ]);
  return { ok: true, room, key, lamport, tier: toTier, receipt: { from: t.tier, to: toTier, fact_survival: factSurvival, lattice_snap: latticeSnap, method, ts } };
}

async function corePinch(args, env) {
  const intent = str(args.intent);
  if (!intent) throw new HttpError(400, "intent is required");
  const context = str(args.context);
  const vector = await embed(env, context ? intent + "\n" + context : intent);
  // NOTE: Vectorize metadata filter returned empty results in practice (4.118 /
  // compat 2025-09-01) even when unfiltered queries matched the same vectors —
  // so we query wide and filter by kind in JS. Revisit when filter behaves.
  const res = await env.INDEX.query(vector, { topK: 10, returnMetadata: "all" });
  const candidates = ((res && res.matches) || []).filter((m) => m.metadata && m.metadata.kind === "intent");
  const match = candidates[0];
  if (!match) {
    return { action: "ESCALATE", confidence: 0, eta_measured: 1000, reason: "no reflexes known yet" };
  }
  const score = match.score;
  const etaMeasured = Math.round(1000 * (1 - score));
  const row = await env.DB.prepare(
    "SELECT id, intent, context, reflex, confidence, uses FROM intents WHERE vector_id=?1"
  ).bind(match.id).first();
  if (!row) return { action: "ESCALATE", confidence: score, eta_measured: etaMeasured, reason: "vector row not resolved" };
  if (score >= PINCH_FIRE) {
    await env.DB.prepare("UPDATE intents SET uses=uses+1, updated_ts=?1 WHERE id=?2").bind(nowSec(), row.id).run();
    return { action: "FIRE", intent_id: row.id, reflex: row.reflex, confidence: score, eta_measured: etaMeasured, uses: row.uses + 1 };
  }
  if (score >= PINCH_CONFIRM) {
    return { action: "CONFIRM", intent_id: row.id, candidate: row.reflex, confidence: score, eta_measured: etaMeasured };
  }
  return { action: "ESCALATE", confidence: score, eta_measured: etaMeasured, nearest_intent: row.intent };
}

async function corePinchCompile(args, env) {
  const intent = str(args.intent), reflex = str(args.reflex);
  if (!intent || !reflex) throw new HttpError(400, "intent and reflex are required");
  const context = str(args.context);
  const confidence = Number(args.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
    throw new HttpError(400, "confidence must be 0..1");
  }
  const ts = nowSec();
  const vectorId = "intent:" + (await sha256hex32(intent + "\u0000" + context));
  await env.DB.prepare(
    "INSERT INTO intents (intent, context, reflex, confidence, vector_id, uses, created_ts, updated_ts) " +
    "VALUES (?1,?2,?3,?4,?5,0,?6,?6) " +
    "ON CONFLICT(intent, context) DO UPDATE SET reflex=excluded.reflex, confidence=excluded.confidence, updated_ts=excluded.updated_ts"
  ).bind(intent, context, reflex, confidence, vectorId, ts).run();
  let embedded = false, err = null;
  try {
    const vector = await embed(env, context ? intent + "\n" + context : intent);
    await env.INDEX.upsert([{ id: vectorId, values: vector, metadata: { kind: "intent", intent, ts } }]);
    embedded = true;
  } catch (e) { err = String(e); }
  return { ok: true, vector_id: vectorId, embedded, ...(err ? { error: err } : {}) };
}

async function coreField(args, env, agent) {
  const who = str(args.agent) || agent;
  if (!who) throw new HttpError(400, "agent required (token or query)");
  const rows = await env.DB.prepare(
    "SELECT agent, day, gamma_sum, eta_sum, total, remaining FROM field_budget WHERE agent=?1 ORDER BY day DESC LIMIT 30"
  ).bind(who).all();
  return { agent: who, budget: 1585, days: (rows && rows.results) || [] };
}

async function coreWitness(args, env) {
  const id = str(args.id);
  if (!id) throw new HttpError(400, "id is required");
  const row = await env.DB.prepare(
    "SELECT id, agent, gist, body, receipt_url, books_to, gamma, eta, ts, embedded FROM bookings WHERE id=?1"
  ).bind(id).first();
  if (!row) throw new HttpError(404, "no booking with id " + id);
  return row;
}

/** Fleet reflex inventory — used by local runners (lever-runner) to sync. */
async function coreIntents(args, env) {
  const limit = clampInt(args.limit, 1, 500, 100);
  const rows = await env.DB.prepare(
    "SELECT id, intent, context, reflex, confidence, uses, created_ts, updated_ts FROM intents ORDER BY updated_ts DESC LIMIT ?1"
  ).bind(limit).all();
  const intents = (rows && rows.results) || [];
  return { count: intents.length, intents };
}

// ── Growth seam (quilt-dba): adding a canon cell IS advancing a stage ──────
// Design receipt (README §5) prescribes the doctrine but is silent on table/
// endpoint specifics, so this is the minimal doctrine-true shape: one canon
// cell added -> room.stage + 1, always, with a first-class stage receipt
// {room, from_stage, to_stage, cell_id, ts, agent}. Duplicate title = 409, no
// advance, no receipt (no phantom stages on retry). Stages never regress.

async function coreCellAdd(args, env, agent) {
  const roomRef = str(args.room);
  const title = str(args.title);
  if (!roomRef || !title) throw new HttpError(400, "room and title are required");
  const body = typeof args.body === "string" ? args.body : "";
  const who = agent || str(args.agent) || ""; // token identity wins
  const roomRow = await resolveRoom(env, roomRef);
  if (!roomRow) throw new HttpError(404, "room not found: " + roomRef + " (POST /room first)");
  const dup = await env.DB.prepare("SELECT id FROM canon_cells WHERE room_id=?1 AND title=?2").bind(roomRow.id, title).first();
  if (dup) throw new HttpError(409, "cell exists: " + roomRow.name + "/" + title + " — stage not advanced");
  const ts = nowSec();
  const fromStage = roomRow.stage;
  const toStage = fromStage + 1;
  const ins = await env.DB.prepare(
    "INSERT INTO canon_cells (room_id, title, body, stage, agent, created_ts) VALUES (?1,?2,?3,?4,?5,?6)"
  ).bind(roomRow.id, title, body, toStage, who, ts).run();
  const cellId = ins.meta.last_row_id;
  await env.DB.batch([
    env.DB.prepare("UPDATE rooms SET stage=?1 WHERE id=?2").bind(toStage, roomRow.id),
    env.DB.prepare("INSERT INTO stage_receipts (room_id, cell_id, from_stage, to_stage, agent, ts) VALUES (?1,?2,?3,?4,?5,?6)")
      .bind(roomRow.id, cellId, fromStage, toStage, who, ts),
  ]);
  // meaning seam (best-effort): canon cells are recallable via /near
  let embedded = false, err = null;
  const vectorId = "cell:" + (await sha256hex32(roomRow.name + "\u0000" + title));
  try {
    const vector = await embed(env, roomRow.name + " / " + title + "\n" + body);
    await env.INDEX.upsert([{ id: vectorId, values: vector, metadata: { kind: "cell", room: roomRow.name, title, ts } }]);
    await env.DB.prepare("UPDATE canon_cells SET vector_id=?1 WHERE id=?2").bind(vectorId, cellId).run();
    embedded = true;
  } catch (e) { err = String(e); }
  return {
    ok: true,
    room: roomRow.name,
    cell: { id: cellId, title, body, stage: toStage, agent: who, created_ts: ts },
    stage_advance: { room: roomRow.name, from_stage: fromStage, to_stage: toStage, cell_id: cellId, ts, agent: who },
    embedded, ...(err ? { error: err } : {}),
  };
}

async function coreCellList(args, env) {
  const roomRef = str(args.room);
  if (!roomRef) throw new HttpError(400, "room is required");
  const roomRow = await resolveRoom(env, roomRef);
  if (!roomRow) throw new HttpError(404, "room not found: " + roomRef);
  const cells = await env.DB.prepare(
    "SELECT id, title, body, stage, agent, vector_id, created_ts FROM canon_cells WHERE room_id=?1 ORDER BY stage ASC, id ASC"
  ).bind(roomRow.id).all();
  const receipts = await env.DB.prepare(
    "SELECT id, cell_id, from_stage, to_stage, agent, ts FROM stage_receipts WHERE room_id=?1 ORDER BY id ASC"
  ).bind(roomRow.id).all();
  return {
    room: { id: roomRow.id, name: roomRow.name },
    stage: roomRow.stage,
    cells: (cells && cells.results) || [],
    receipts: (receipts && receipts.results) || [],
  };
}

// ─────────────────────────────── MCP surface ───────────────────────────────

const TOOL_SCHEMAS = {
  book: { gist: "string (required)", body: "string", receipt_url: "string", books_to: "string", gamma: "int", eta: "int", ts: "epoch seconds" },
  near: { q: "string (required)", k: "int 1..50" },
  since: { ts: "epoch seconds (required)" },
  room_create: { name: "string (required)", stage: "int >=1" },
  room_list: {},
  tile_write: { room: "string (required)", key: "string (required)", content: "string (required)", tier: "full|gist|hint" },
  tile_get: { room: "string (required)", key: "string (required)" },
  tile_history: { room: "string (required)", key: "string (required)" },
  tile_demote: { room: "string (required)", key: "string (required)", to_tier: "full|gist|hint (required)", content: "string (compressed form)", fact_survival: "number", lattice_snap: "number", method: "string (required)" },
  pinch: { intent: "string (required)", context: "string" },
  pinch_compile: { intent: "string (required)", reflex: "string (required)", confidence: "number 0..1 (required)", context: "string" },
  intents_list: { limit: "int 1..500" },
  field_query: { agent: "string" },
  witness_get: { id: "string (required)" },
};

const CORE_BY_TOOL = {
  book: coreBook, near: coreNear, since: coreSince,
  room_create: coreRoomCreate, room_list: coreRoomList,
  tile_write: coreTileWrite, tile_get: coreTileGet, tile_history: coreTileHistory, tile_demote: coreTileDemote,
  pinch: corePinch, pinch_compile: corePinchCompile,
  intents_list: coreIntents,
  field_query: coreField, witness_get: coreWitness,
};

function jsonType(v) {
  if (v === "string (required)" || v === "string" || v.startsWith("full|") || v === "string (compressed form)") return "string";
  return "number";
}

const MCP_TOOLS = Object.entries(TOOL_SCHEMAS).map(([name, props]) => {
  const properties = {};
  const required = [];
  for (const [p, d] of Object.entries(props)) {
    properties[p] = { type: jsonType(d), description: d };
    if (d.includes("required")) required.push(p);
  }
  return {
    name,
    description: "superinstance-api: " + name.replace(/_/g, " "),
    inputSchema: { type: "object", properties, ...(required.length ? { required } : {}) },
  };
});

async function handleMcp(request, env, agent) {
  let rpc;
  try { rpc = await request.json(); } catch { return json({ error: "invalid JSON body" }, 400); }
  if (!rpc || typeof rpc !== "object" || rpc.jsonrpc !== "2.0") {
    return json({ jsonrpc: "2.0", id: null, error: { code: -32600, message: "not a JSON-RPC 2.0 request" } }, 400);
  }
  if (!("id" in rpc)) return new Response(null, { status: 202 }); // notification

  const { id, method, params } = rpc;
  const reply = (result) => json({ jsonrpc: "2.0", id, result });
  const fail = (code, message) => json({ jsonrpc: "2.0", id, error: { code, message } });

  try {
    if (method === "initialize") {
      return reply({
        protocolVersion: (params && params.protocolVersion) || "2025-03-26",
        capabilities: { tools: {} },
        serverInfo: { name: "superinstance-api", version: "0.1.0" },
      });
    }
    if (method === "ping") return reply({});
    if (method === "tools/list") return reply({ tools: MCP_TOOLS });
    if (method === "tools/call") {
      const name = params && params.name;
      const fn = CORE_BY_TOOL[name];
      if (!fn) return fail(-32602, "unknown tool: " + name);
      const args = (params && params.arguments) || {};
      let result;
      if (name === "book") result = await coreBook(args, env, agent);
      else if (name === "field_query") result = await coreField(args, env, agent);
      else result = await fn(args, env);
      return reply({ content: [{ type: "text", text: JSON.stringify(result) }] });
    }
    return fail(-32601, "method not found: " + method);
  } catch (err) {
    if (err instanceof HttpError) return fail(-32000, err.message);
    return fail(-32603, String((err && err.message) || err));
  }
}

// ─────────────────────────────── REST router ───────────────────────────────

async function argsFrom(request, url) {
  const args = {};
  for (const [k, v] of url.searchParams) args[k] = v;
  if (request.method === "POST" || request.method === "PUT") {
    try {
      const body = await request.json();
      if (body && typeof body === "object") Object.assign(args, body);
    } catch { throw new HttpError(400, "invalid JSON body"); }
  }
  return args;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const agent = auth(request, env);

    try {
      if (path === "/health") {
        return json({ ok: true, service: "superinstance-api", version: "0.1.0", seams: ["tiles", "meaning", "reflex", "field", "growth"], mcp: "/mcp" });
      }

      if (path === "/mcp") {
        if (!agent) return json({ error: "unauthorized" }, 401);
        if (request.method === "GET") return json({ error: "GET /mcp unsupported (stateless server)" }, 405);
        if (request.method !== "POST") return json({ error: "method not allowed" }, 405);
        return await handleMcp(request, env, agent);
      }

      if (!agent) return json({ error: "unauthorized" }, 401);
      const args = await argsFrom(request, url);

      if (request.method === "POST" && path === "/book") return json(await coreBook(args, env, agent));
      if (request.method === "GET" && path === "/near") return json(await coreNear(args, env));
      if (request.method === "GET" && path === "/since") return json(await coreSince(args, env));
      if (request.method === "POST" && path === "/room") return json(await coreRoomCreate(args, env));
      if (request.method === "GET" && path === "/rooms") return json(await coreRoomList(args, env));
      {
        const m = /^\/rooms\/([^/]+)\/cells$/.exec(path);
        if (m) {
          const roomRef = decodeURIComponent(m[1]);
          if (request.method === "PUT") return json(await coreCellAdd({ ...args, room: roomRef }, env, agent));
          if (request.method === "GET") return json(await coreCellList({ ...args, room: roomRef }, env));
        }
      }
      if (request.method === "POST" && path === "/tile") return json(await coreTileWrite(args, env));
      if (request.method === "GET" && path === "/tile") return json(await coreTileGet(args, env));
      if (request.method === "GET" && path === "/tile/history") return json(await coreTileHistory(args, env));
      if (request.method === "POST" && path === "/tile/demote") return json(await coreTileDemote(args, env));
      if (request.method === "POST" && path === "/pinch") return json(await corePinch(args, env));
      if (request.method === "POST" && path === "/pinch/compile") return json(await corePinchCompile(args, env));
      if (request.method === "GET" && path === "/field") return json(await coreField(args, env, agent));
      if (request.method === "GET" && path === "/witness") return json(await coreWitness(args, env));
      if (request.method === "GET" && path === "/intents") return json(await coreIntents(args, env));

      return json({ error: "not found", service: "superinstance-api", routes: ["POST /book", "GET /near", "GET /since", "POST /room", "GET /rooms", "PUT /rooms/:id/cells", "GET /rooms/:id/cells", "POST /tile", "GET /tile", "GET /tile/history", "POST /tile/demote", "POST /pinch", "POST /pinch/compile", "GET /field", "GET /witness", "GET /intents", "POST /mcp"] }, 404);
    } catch (err) {
      if (err instanceof HttpError) return json({ error: err.message }, err.status);
      return json({ error: String((err && err.message) || err) }, 500);
    }
  },
};
