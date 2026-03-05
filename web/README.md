# Physics Benchmark Review — Web Tool

A single-page review tool for the `physics_qa_bank.yaml` question bank.
Reviewers browse questions, reveal reference answers, and submit per-question
grades. Grades are stored per-user in a Cloudflare D1 (SQLite) database.
Access is gated by Cloudflare Zero Trust so only invited reviewers can log in.

---

## How deployment works

There are **two separate concerns**:

```text
┌─────────────────────────────────────────────────────────────────┐
│  1. CODE  — deployed automatically from GitHub                  │
│                                                                 │
│     git push  →  Cloudflare Pages sees the commit               │
│                  and publishes web/ immediately.                │
│                                                                 │
│     You never run any deploy command for this.                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  2. DATABASE  — set up once from your laptop with Wrangler      │
│                                                                 │
│     Wrangler is a CLI tool that talks to the Cloudflare API.    │
│     You use it exactly twice, at the start:                     │
│       a) create the D1 database in Cloudflare's cloud           │
│       b) run the SQL schema to create the grades table          │
│                                                                 │
│     After that, Wrangler is only needed for local development   │
│     or to query the database directly.                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## One-time setup

### Step 1 — Create a Cloudflare account and install Wrangler

```bash
npm install -g wrangler
wrangler login          # opens a browser → log in to your CF account
```

### Step 2 — Create the D1 database in Cloudflare's cloud

```bash
wrangler d1 create physics-benchmark
```

Wrangler prints something like:

```text
✅ Successfully created DB 'physics-benchmark'
[[d1_databases]]
binding = "DB"
database_name = "physics-benchmark"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

Copy that `database_id` into [`wrangler.toml`](wrangler.toml) where it says
`YOUR_D1_DATABASE_ID`. This file is only used for local development — the
production binding is configured in the dashboard in Step 5.

### Step 3 — Create the grades table in the database

```bash
# run from the repo root
wrangler d1 execute physics-benchmark --file=web/schema.sql
```

This sends the SQL to Cloudflare and creates the `grades` table. Done —
you won't need to touch the database again unless you want to inspect it.

### Step 4 — Connect the GitHub repo to Cloudflare Pages

This is done entirely in the Cloudflare dashboard, **not** via Wrangler.

1. Go to **Cloudflare dashboard → Workers & Pages → Create → Pages →
   Connect to Git**
2. Authorise Cloudflare to read your GitHub account and select this repo.
3. Set the build configuration:

   | Setting                | Value                                     |
   |------------------------|-------------------------------------------|
   | Production branch      | `main`                                    |
   | Build command          | `python scripts/export_questions_json.py` |
   | Build output directory | `web`                                     |

   Cloudflare Pages has Python in its build environment. On every push it
   runs the script, which regenerates `web/questions.json` from the YAML,
   and then publishes the `web/` folder. `questions.json` is **not**
   committed to the repo — the YAML is the single source of truth.

4. Click **Save and Deploy**.

Your site is now live at `https://physics-benchmark.pages.dev` (or similar).

### Step 5 — Attach the database to the Pages project

The Workers in `functions/` need access to the D1 database. Tell Cloudflare
which database to use:

1. Cloudflare dashboard → your Pages project → **Settings → Functions →
   D1 database bindings → Add binding**
2. Set:

   | Variable name | Database             |
   |---------------|----------------------|
   | `DB`          | `physics-benchmark`  |

3. Click **Save**. Cloudflare triggers one more automatic redeploy.

### Step 6 — Protect the site with Cloudflare Zero Trust

1. Cloudflare dashboard → **Zero Trust → Access → Applications →
   Add an application → Self-hosted**
2. Application name: `Physics Benchmark`
   Application domain: `physics-benchmark.pages.dev` (or your custom domain)
3. Add a policy:
   - Action: **Allow**
   - Include rule: *Emails ending in* `@oeaw.ac.at`
     (or use *Emails* with an explicit list of reviewer addresses)
4. Save.

From now on, visiting the URL shows a Cloudflare login page. The reviewer
enters their email, receives a one-time code, and is let in. Cloudflare
injects their verified email into every request — the Workers use this to
tag each grade record automatically.

---

## Day-to-day workflow

**Adding or editing questions:**

```bash
# Edit the YAML, commit, push — that's all.
git add data/physics_qa_bank.yaml
git commit -m "feat: add questions"
git push
```

Cloudflare Pages runs `python scripts/export_questions_json.py` as part of
its build, regenerates `web/questions.json` from the YAML, and publishes
the result. **You never touch `questions.json` manually.**

---

## Local development

```bash
# Apply schema to a local D1 copy
wrangler d1 execute physics-benchmark --local --file=web/schema.sql

# Serve the app locally (functions + static files)
wrangler pages dev web --d1=DB
```

Open `http://localhost:8788`. Because there are no Cloudflare Access headers
locally, the Workers fall back to `dev@localhost` as the user identity, so
you can grade freely while testing.

---

## Exporting grades

Any logged-in reviewer can download all grades as CSV:

```text
https://<your-domain>/api/grades/export
```

Columns: `user_email`, `user_sub`, `question_id`, `difficulty_rating`,
`question_valid`, `answer_valid`, `notes`, `created_at`, `updated_at`.

`user_email` is the reviewer's address from Cloudflare Access.
`user_sub` is a stable UUID from the Access JWT — use it as the primary
identifier if emails change.

You can also query the database directly from your laptop:

```bash
wrangler d1 execute physics-benchmark \
  --command "SELECT * FROM grades ORDER BY user_email, question_id"
```

---

## Grading fields

| Field               | Values                    | Meaning                              |
|---------------------|---------------------------|--------------------------------------|
| `difficulty_rating` | 1 – 5                     | 1 = trivial, 5 = expert              |
| `question_valid`    | `yes` / `partial` / `no`  | Is the question well-posed?          |
| `answer_valid`      | `yes` / `partial` / `no`  | Is the reference answer correct?     |
| `notes`             | free text                 | Corrections, suggested improvements  |

Submitting a grade twice for the same question overwrites the first entry.
