#!/usr/bin/env bash
# Publish ONLY an allowlisted generated directory. Keep source edits and repository history.
set -euo pipefail
branch=${GITHUB_REF_NAME:?GitHub Actions branch is required}
[[ "$branch" == feature/qulay-prototype-20261002 ]] || { echo 'Wrong branch'; exit 2; }
target=${1:?generated directory required};shift
case "$target" in electronics/generated|mechanical/generated-r1|generated/verification) ;; *) echo 'Directory not allowlisted';exit 2;; esac
(( $# > 0 )) || { echo 'Input paths required for stale-build protection';exit 2; }
built=$(git rev-parse HEAD)
snapshot=$(mktemp -d);worktree=$(mktemp -d)
trap 'git worktree remove --force "$worktree" 2>/dev/null || true; rm -rf "$snapshot" "$worktree"' EXIT
cp -a "$target/." "$snapshot/"
git fetch origin "$branch"
git worktree add --detach "$worktree" "origin/$branch"
git -C "$worktree" config user.name qulay-build
git -C "$worktree" config user.email '41898282+github-actions[bot]@users.noreply.github.com'
for attempt in 1 2 3; do
  git fetch origin "$branch"
  if ! git diff --quiet "$built" "origin/$branch" -- "$@"; then
    echo 'Inputs changed during build. Retaining artifact, refusing to publish stale outputs.'
    exit 3
  fi
  # This reset touches only our temporary detached publication worktree, never the remote branch.
  git -C "$worktree" reset --hard "origin/$branch"
  mkdir -p "$worktree/$target"
  rsync -a --delete "$snapshot/" "$worktree/$target/"
  git -C "$worktree" add -- "$target"
  if git -C "$worktree" diff --cached --quiet; then exit 0;fi
  git -C "$worktree" commit -m "build: publish checked $target [skip ci]"
  if git -C "$worktree" push origin "HEAD:$branch";then exit 0;fi
  sleep 2
done
echo 'Branch changed repeatedly; artifact retained, remote history unchanged.'
exit 4
