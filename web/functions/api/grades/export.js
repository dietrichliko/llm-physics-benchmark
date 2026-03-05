/**
 * GET /api/grades/export
 * Returns all grades from all users as a CSV download.
 * Protected by CF Access — any authenticated user can export,
 * but in practice you'd restrict this in the CF Access policy
 * or add an allowlist check here.
 */
export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    "SELECT * FROM grades ORDER BY user_email, question_id"
  ).all();

  const COLS = [
    "user_email", "user_sub", "question_id",
    "difficulty_rating", "question_valid", "answer_valid",
    "notes", "created_at", "updated_at",
  ];

  function csvCell(v) {
    const s = String(v ?? "");
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  }

  const rows = [
    COLS.join(","),
    ...results.map(r => COLS.map(c => csvCell(r[c])).join(",")),
  ];

  return new Response(rows.join("\n"), {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="physics-benchmark-grades.csv"',
    },
  });
}
