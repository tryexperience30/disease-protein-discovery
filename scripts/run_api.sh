#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$ROOT/.tools/node/bin:$PATH"
cd "$ROOT/backend"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
