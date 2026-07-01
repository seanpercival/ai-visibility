#!/usr/bin/env bash
# Build the installable ai-visibility.skill bundle from this repo.
# Zero external tools required beyond Python 3.
set -euo pipefail
cd "$(dirname "$0")"

python3 - <<'PY'
import zipfile, os

OUT = "ai-visibility.skill"
PREFIX = "ai-visibility"           # internal folder inside the bundle
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"}
SKIP_FILES = {OUT, ".DS_Store"}
SKIP_EXT = (".pyc",)
SKIP_GENERATED = {"panel.json", "history.csv", "aeo_history.csv", "out.json"}

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn in SKIP_FILES or fn in SKIP_GENERATED or fn.endswith(SKIP_EXT):
                continue
            if fn.endswith("_results.json"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, ".")
            z.write(path, os.path.join(PREFIX, rel))
print(f"Built {OUT} ({os.path.getsize(OUT)} bytes)")
PY
