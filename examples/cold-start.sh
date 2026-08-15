#!/usr/bin/env bash
# Cold start — proves a stranger can run this with nothing but git and python3.
#
# Creates three throwaway git repos under examples/sandbox/, then runs all four
# commands against examples/fake-fleet.json — open, record, status, cost — so the
# whole loop is exercised rather than described. Touches nothing outside this directory.
#
#   ./examples/cold-start.sh          run it
#   ./examples/cold-start.sh --clean  remove the sandbox and the state file
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
sandbox="$here/sandbox"
state="$here/.fleet-state.json"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf "$sandbox"
  rm -f "$state"
  echo "removed $sandbox"
  echo "removed $state"
  exit 0
fi

# Start from no state, so `fleet status` below reports this run and not the last one.
rm -f "$state"

for name in api web infra; do
  d="$sandbox/$name"
  mkdir -p "$d"
  if [[ ! -d "$d/.git" ]]; then
    git -C "$d" init -q
    git -C "$d" config user.email "cold-start@example.invalid"
    git -C "$d" config user.name "cold start"
    echo "# $name" > "$d/README.md"
    git -C "$d" add README.md
    git -C "$d" commit -qm "init $name"
  fi
done

# One dirty file, so the DIRTY column is shown proving something rather than
# always reading zero. A column that can only ever print one value is decoration.
echo "scratch" > "$sandbox/web/uncommitted.txt"

fleet() { "$root/fleet" --config "$here/fake-fleet.json" "$@"; }

echo
echo "== fleet open — the lane table, checked against the sandbox repos =="
fleet open

echo
echo "== fleet record — a claim binds to the artifact that proves it =="
echo "   (a human types this; if the agent types it, the record is authored by"
echo "    the thing being measured — see rule 2 in RULES.md)"
fleet record backend internal "$sandbox/api/README.md"

echo
echo "== fleet status — what was recorded, with the artifact column =="
fleet status

echo
echo "== fleet cost — token spend read from harness logs, never self-reported =="
echo "   (fixtures under examples/fixtures/ stand in for your own transcripts)"
fleet cost

echo
echo "Done. ./examples/cold-start.sh --clean removes the sandbox and the state file."
