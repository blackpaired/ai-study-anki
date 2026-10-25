#!/usr/bin/env bash
# Builds dist/study-anki.zip for AI apps that let you upload skills as a ZIP file.
# Some apps allow at most 200 characters in the skill description, so the ZIP gets this short one;
# the full SKILL.md description stays in the repo.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
short="Turns lecture notes into an Anki package (.apkg) with basic, cloze and image occlusion cards, checked against your notes. Use for Anki, flashcards, cloze or image occlusion."
[ ${#short} -le 200 ] || { echo "Short description is ${#short} characters (max 200)" >&2; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -r "$here/skills/study-anki" "$work/study-anki"
rm -rf "$work/study-anki/template" "$work/study-anki/__pycache__"

SHORT="$short" python3 -I - "$work/study-anki/SKILL.md" <<'PY'
import os, re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
s, n = re.subn(r"^description: .*$", lambda m: "description: " + os.environ["SHORT"], s, count=1, flags=re.M)
assert n == 1, "no description line found"
open(p, "w", encoding="utf-8").write(s)
PY
mkdir -p "$here/dist"
rm -f "$here/dist/study-anki.zip"
python3 -I -c 'import shutil, sys; shutil.make_archive(sys.argv[1], "zip", sys.argv[2], sys.argv[3])' "$here/dist/study-anki" "$work" "study-anki"
echo "Built: $here/dist/study-anki.zip"
