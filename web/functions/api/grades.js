/**
 * GET  /api/grades            – all grades for the current user
 * POST /api/grades            – upsert a grade for the current user
 */

function parseUser(request) {
  const email = request.headers.get("Cf-Access-Authenticated-User-Email");
  const jwt   = request.headers.get("Cf-Access-Jwt-Assertion");

  if (!email && !jwt) {
    return { email: "dev@localhost", sub: "dev" };
  }

  let sub = email ?? "unknown";
  if (jwt) {
    try {
      const payload = JSON.parse(
        atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
      );
      sub = payload.sub ?? payload.email ?? sub;
    } catch { /* keep sub = email */ }
  }

  return { email: email ?? "unknown", sub };
}

export async function onRequestGet({ request, env }) {
  const user = parseUser(request);
  const url  = new URL(request.url);
  const qid  = url.searchParams.get("question_id");

  let stmt;
  if (qid) {
    stmt = env.DB.prepare(
      "SELECT * FROM grades WHERE user_email = ? AND question_id = ?"
    ).bind(user.email, qid);
  } else {
    stmt = env.DB.prepare(
      "SELECT * FROM grades WHERE user_email = ? ORDER BY updated_at DESC"
    ).bind(user.email);
  }

  const { results } = await stmt.all();
  return Response.json({ grades: results });
}

export async function onRequestPost({ request, env }) {
  const user = parseUser(request);

  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const { question_id, difficulty_rating, question_valid, answer_valid, notes } = body;

  if (!question_id) {
    return Response.json({ error: "question_id is required" }, { status: 400 });
  }

  const now = new Date().toISOString();

  await env.DB.prepare(`
    INSERT INTO grades
      (user_email, user_sub, question_id, difficulty_rating, question_valid, answer_valid, notes, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (user_email, question_id) DO UPDATE SET
      difficulty_rating = excluded.difficulty_rating,
      question_valid    = excluded.question_valid,
      answer_valid      = excluded.answer_valid,
      notes             = excluded.notes,
      updated_at        = excluded.updated_at
  `)
    .bind(
      user.email,
      user.sub,
      question_id,
      difficulty_rating ?? null,
      question_valid    ?? null,
      answer_valid      ?? null,
      notes             ?? null,
      now,
      now,
    )
    .run();

  const grade = await env.DB.prepare(
    "SELECT * FROM grades WHERE user_email = ? AND question_id = ?"
  ).bind(user.email, question_id).first();

  return Response.json({ grade });
}
