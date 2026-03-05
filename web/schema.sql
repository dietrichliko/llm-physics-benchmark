-- D1 schema for the Physics Benchmark Review tool
-- Apply with: wrangler d1 execute physics-benchmark --file=web/schema.sql

CREATE TABLE IF NOT EXISTS grades (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email       TEXT    NOT NULL,
    user_sub         TEXT    NOT NULL,
    question_id      TEXT    NOT NULL,
    difficulty_rating INTEGER,           -- 1 (trivial) … 5 (expert)
    question_valid   TEXT CHECK (question_valid   IN ('yes', 'partial', 'no') OR question_valid   IS NULL),
    answer_valid     TEXT CHECK (answer_valid     IN ('yes', 'partial', 'no') OR answer_valid     IS NULL),
    notes            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_email, question_id)
);

CREATE INDEX IF NOT EXISTS idx_grades_user     ON grades (user_email);
CREATE INDEX IF NOT EXISTS idx_grades_question ON grades (question_id);
