#!/usr/bin/env bash
# dispatch.sh — start one Codex worker for one issue in its own worktree and branch.
# usage: dispatch.sh <org/repo> <issue-number> <slug> <brief-file> [model]
# env:   CODEX_WORK (default ~/dev/oramasearch/codex-work), CODEX_MODEL (default gpt-5.6-sol),
#        CODEX_BASE (branch to start from and target the PR at; default main)
set -uo pipefail
ORG_REPO=$1; N=$2; SLUG=$3; BRIEF=$4; MODEL=${5:-${CODEX_MODEL:-gpt-5.6-sol}}
REPO=${ORG_REPO#*/}
BASE=${CODEX_BASE:-main}
ROOT=${CODEX_WORK:-$HOME/dev/oramasearch/codex-work}
HERE=$(cd "$(dirname "$0")/.." && pwd)
MAIN=$ROOT/$REPO; WT=$ROOT/wt/$REPO/issue-$N; BR=issue-$N-$SLUG; RUN=$ROOT/runs/$REPO-$N
mkdir -p "$ROOT/wt/$REPO" "$RUN"
[ -d "$MAIN/.git" ] || git clone -q --recurse-submodules "git@github.com:$ORG_REPO.git" "$MAIN" || exit 2
git -C "$MAIN" fetch -q origin || exit 2
if [ ! -d "$WT" ]; then
  git -C "$MAIN" worktree add -q -b "$BR" "$WT" "origin/$BASE" || exit 2
  git -C "$WT" submodule update --init --recursive -q 2>/dev/null || true
fi
sed -e "s|{{ORG_REPO}}|$ORG_REPO|g" -e "s|{{REPO}}|$REPO|g" -e "s|{{ISSUE}}|$N|g" \
    -e "s|{{BRANCH}}|$BR|g" -e "s|{{WT}}|$WT|g" -e "s|{{BASE}}|$BASE|g" "$HERE/templates/preamble.md" > "$RUN/brief.md"
printf '\n\n' >> "$RUN/brief.md"; cat "$BRIEF" >> "$RUN/brief.md"
echo "$(date -u +%FT%TZ) start repo=$ORG_REPO issue=$N branch=$BR base=$BASE worktree=$WT model=$MODEL" >> "$RUN/log"
command codex exec --yolo -C "$WT" -m "$MODEL" -c model_reasoning_effort="high" --enable fast_mode \
  -o "$RUN/last.md" - < "$RUN/brief.md" >> "$RUN/log" 2>&1
rc=$?
echo "$(date -u +%FT%TZ) exit=$rc" >> "$RUN/log"
exit $rc
