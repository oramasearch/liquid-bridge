#!/usr/bin/env bash
# resume.sh — continue a worker's own session with a follow-up (answers, a fix list).
# usage: resume.sh <org/repo> <issue-number> <followup-file>
# Uses the session id recorded in runs/<repo>-<N>/log (never --last: parallel workers make it ambiguous).
set -uo pipefail
ORG_REPO=$1; N=$2; FOLLOWUP=$3
REPO=${ORG_REPO#*/}
ROOT=${CODEX_WORK:-$HOME/dev/oramasearch/codex-work}
WT=$ROOT/wt/$REPO/issue-$N; RUN=$ROOT/runs/$REPO-$N
SID=$(grep -i "session id:" "$RUN/log" | sed -E 's/.*session id:[[:space:]]*//' | cut -d' ' -f1 | tail -1)
[ -n "$SID" ] || { echo "no session id in $RUN/log" >&2; exit 2; }
cp "$FOLLOWUP" "$RUN/followup-$(date -u +%Y%m%dT%H%M%SZ).md"
echo "$(date -u +%FT%TZ) resume session=$SID" >> "$RUN/log"
(cd "$WT" && command codex exec resume "$SID" --dangerously-bypass-approvals-and-sandbox \
   -o "$RUN/last.md" - < "$FOLLOWUP" >> "$RUN/log" 2>&1)
rc=$?
echo "$(date -u +%FT%TZ) exit=$rc" >> "$RUN/log"
exit $rc
