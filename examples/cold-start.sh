#!/usr/bin/env bash
# Cold start — proves a stranger can run this with nothing but git and python3.
#
# Creates three throwaway git repos under examples/sandbox/, then runs `fleet open`
# against examples/fake-fleet.json. Touches nothing outside this directory.
#
#   ./examples/cold-start.sh          run it
#   ./examples/cold-start.sh --clean  remove the sandbox again
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
sandbox="$here/sandbox"

if [[ "${1:-}" == "--clean" ]]; then
  rm -rf "$sandbox"
  echo "removed $sandbox"
  exit 0
fi

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

echo
echo "== fleet open, on a config that points at nothing but this sandbox =="
"$root/fleet" --config "$here/fake-fleet.json" open
