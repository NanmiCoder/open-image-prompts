# AGENTS.md

Instructions for coding agents working in or starting up this repository.

## What this repository is

An open, local-first visual prompt archive plus two installable Agent Skills.
The application is a read-only SQLite API (Python, standard library only) behind
a React/Vite frontend. Nothing here trains, labels, or writes prompt data.

## Get it running

Prerequisites: Node.js 20.19+ or 22.12+, and Git. Python arrives via `uv`, which
`start.sh` installs into `.oip/tools/` if it is missing.

```bash
./start.sh          # macOS/Linux; Windows: start.bat
```

`start.sh` is the whole setup: it prepares Python, downloads the dataset,
installs frontend packages, and starts the API and frontend together. **Open the
URL it prints**, not a URL you assumed — see "Ports" below.

To skip the ~4 GB of image packs (the gallery then falls back to each record's
original source URL):

```bash
OIP_FETCH_SKIP_IMAGES=1 ./start.sh
```

Step-by-step instead of the launcher:

```bash
uv sync --locked
npm run data:pull        # or data:pull:db to skip image packs
npm --prefix web ci
npm run dev
```

## The dataset is not in Git

A clone gives you code, Skills, taxonomy, and small indexes — not the corpus.
`db/prompts.db.gz` (~80 MB) and `images/` (~4.2 GB across nine monthly packs)
are downloaded from GitHub Releases by `scripts/fetch_dataset.py`, which verifies
every asset's sha256 against `data/dataset-manifest.json`. Both paths are
gitignored, and re-running the fetch is safe: verified assets are skipped.

Expect this layout after a full pull:

```text
db/prompts.db.gz          # compressed archive from Releases
images/<tweet_id>/N.jpg   # extracted image packs
.oip/runtime/prompts.db   # expanded read-only SQLite, created on first start
.oip/packs/*.sha256       # extraction markers so unchanged packs are skipped
```

Search and retrieval work without the image packs. Only local image preview
needs them.

## Ports

Nothing binds a predictable port unconditionally, so never hardcode one.

- Frontend: starts at `5173` and moves to the next free port when taken. It
  prints the URL it actually serves. Pin it with `OIP_WEB_HOST`/`OIP_WEB_PORT`;
  an explicit `OIP_WEB_PORT` is strict and a collision fails loudly.
- Skill gallery bridge: starts at `4173`, falls back to a free port, and returns
  the real URL in its JSON response. Read `url`, do not rebuild it.
- SQLite API: always an ephemeral loopback port, reached through the frontend
  proxy at `/api` and `/health`.

Everything binds `127.0.0.1` only.

## The Skills

`skills/img-gen-taste` needs nothing beyond its bundled style cards.
`skills/img-gen-prompts` needs this checkout for its archive and gallery.

```bash
export OIP_REPO_ROOT="$PWD"      # PowerShell: $env:OIP_REPO_ROOT = (Get-Location)
npm run status                   # expects "ready": true and oip-visual-v2
python3 skills/img-gen-prompts/scripts/oip.py search --intent "..." --limit 5
python3 skills/img-gen-prompts/scripts/oip.py stop   # when done browsing
```

If the Skill was installed as a copy outside a checkout (`npx skills add -g`),
`OIP_REPO_ROOT` is required — the script cannot find the repository on its own
and its error message tells you how to create one.

The gallery process is detached on purpose, so it outlives the command that
started it. Call `stop` when finished; as a backstop it exits after four hours
without gallery traffic (`OIP_GALLERY_IDLE_TIMEOUT` in seconds, `0` disables).

## Before you commit

```bash
npm test          # docs, public-data boundary, API, gallery ports, retrieval benchmark, frontend
npm run lint
npm run build
```

`npm run verify:docs` needs neither the database nor the network, so run it first
when you touched documentation or dataset counts. Dataset counts quoted in prose
are checked against `data/public-corpus.json`; update the data, not just the
sentence.

`npm run test:retrieval` ends in a gated benchmark that **fails closed**: every
`related` result a query returns must carry a verdict in
`evals/retrieval/intents.jsonl` — `related_relevant_ids` to accept a reference,
`related_rejected_ids` to record that it was reviewed and turned down. Publishing a
new dataset can surface references nobody has judged yet, and the benchmark then
fails by design. Resolving it means looking at the images and recording a real
verdict — never invent an entry to turn the suite green. A rejected reference still
counts against `related_precision`, which is intended: a reference a reviewer
turned down should not be reaching users.

Re-running the pull after a release that dropped records leaves unreferenced files
in `images/`; `verify:data` reports them and continues. Clear them with
`python3 scripts/fetch_dataset.py --prune`.

If a start times out on a slow machine, raise `OIP_STARTUP_TIMEOUT` (seconds,
default 180) rather than assuming the application is broken.

CI covers `start.sh` on Ubuntu and macOS, `start.bat` on Windows, and the full
check suite on Ubuntu.

## Boundaries

- Treat the database as read-only. The API and Skill open SQLite in immutable
  mode; never add a write path, migration, or labeling job.
- Never commit `db/`, `images/`, or `.oip/` contents.
- The public DB deliberately excludes labeling candidates, model and provider
  settings, run IDs, rationales, and evaluation tables. Do not reintroduce them.
- Source prompts are reproduced byte-for-byte with attribution. Translations and
  derived prompts are separate fields, never a substitute.
