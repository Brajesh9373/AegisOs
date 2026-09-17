#!/usr/bin/env bash
#
# Mirror this website folder into the standalone WorkSimplified_Website repo.
#
# The site lives inside the AegisOs tree, but GitHub only sees the contents of
# this directory. Run this after changing anything under website/ to publish it.
#
#   ./scripts/sync-to-github.sh
#
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="https://github.com/Brajesh9373/WorkSimplified_Website.git"
BRANCH="main"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if git clone --quiet --branch "$BRANCH" "$REMOTE" "$WORK/repo"; then
  :
else
  git init --quiet --initial-branch="$BRANCH" "$WORK/repo"
  git -C "$WORK/repo" remote add origin "$REMOTE"
fi

rsync -a --delete \
  --exclude '.git/' \
  --exclude 'node_modules/' \
  --exclude '.next/' \
  --exclude '.commandcode/' \
  --exclude 'tsconfig.tsbuildinfo' \
  "$SRC/" "$WORK/repo/"

cd "$WORK/repo"
git add -A

if git diff --cached --quiet; then
  echo "Already up to date - nothing to push to $REMOTE"
  exit 0
fi

echo "--- changes to publish ---"
git diff --cached --stat

SOURCE_REV="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"
git commit --quiet -F - <<EOF
chore(website): sync from AegisOs@$SOURCE_REV

Co-authored-by: CommandCodeBot <noreply@commandcode.ai>
EOF

git push --quiet origin "$BRANCH"
echo "Pushed to $REMOTE ($BRANCH)"
