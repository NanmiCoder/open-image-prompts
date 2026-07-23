#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

fail() {
  printf '\nError: %s\n' "$1" >&2
  exit 1
}

printf '\n[1/4] Preparing Git LFS data...\n'
command -v git >/dev/null 2>&1 || fail "Git is required: https://git-scm.com/downloads"
git lfs version >/dev/null 2>&1 || fail "Git LFS is required: https://git-lfs.com/"
git lfs install --local
git lfs pull
[ -f "$ROOT_DIR/db/prompts.db.gz" ] || fail "The public database is missing. Clone this repository with Git LFS enabled."
DB_SIZE=$(wc -c < "$ROOT_DIR/db/prompts.db.gz")
[ "$DB_SIZE" -ge 1024 ] || fail "The public database is still a Git LFS pointer. Run git lfs pull and try again."

printf '\n[2/4] Preparing Python with uv...\n'
UV_INSTALL_DIR="$ROOT_DIR/.oip/tools/uv"
if command -v uv >/dev/null 2>&1; then
  UV_BIN=$(command -v uv)
elif [ -x "$UV_INSTALL_DIR/uv" ]; then
  UV_BIN="$UV_INSTALL_DIR/uv"
else
  command -v curl >/dev/null 2>&1 || fail "curl is required to install uv: https://docs.astral.sh/uv/getting-started/installation/"
  mkdir -p "$UV_INSTALL_DIR"
  curl -LsSf https://astral.sh/uv/install.sh \
    | env UV_INSTALL_DIR="$UV_INSTALL_DIR" UV_NO_MODIFY_PATH=1 sh
  UV_BIN="$UV_INSTALL_DIR/uv"
  [ -x "$UV_BIN" ] || fail "uv was installed but its executable could not be found at $UV_BIN"
fi
"$UV_BIN" sync --locked

printf '\n[3/4] Installing frontend dependencies...\n'
command -v node >/dev/null 2>&1 || fail "Node.js 20.19+ or 22.12+ is required: https://nodejs.org/"
command -v npm >/dev/null 2>&1 || fail "npm is required and normally ships with Node.js: https://nodejs.org/"
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (!((major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22)) { console.error("Node.js " + process.versions.node + " is unsupported. Install Node.js 20.19+ or 22.12+."); process.exit(1) }'
npm --prefix web ci

printf '\n[4/4] Starting Open Image Prompts...\n'
OIP_PYTHON="$ROOT_DIR/.venv/bin/python"
[ -x "$OIP_PYTHON" ] || fail "uv did not create the expected Python environment at $OIP_PYTHON"
export OIP_PYTHON
exec node web/scripts/with_api.mjs dev
