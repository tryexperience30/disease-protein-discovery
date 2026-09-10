#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$ROOT/.tools/node/bin:$PATH"
cd "$ROOT/frontend"
npm run dev
