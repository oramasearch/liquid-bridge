#!/usr/bin/env bash
# status.sh — one line per run: repo-issue, alive?, log age, PR, last log line.
ROOT=${CODEX_WORK:-$HOME/dev/oramasearch/codex-work}
now=$(date +%s)
for d in "$ROOT"/runs/*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d"); repo=${name%-*}; n=${name##*-}
  wt="$ROOT/wt/$repo/issue-$n"
  sid=$(grep -m1 -i 'session id:' "$d/log" 2>/dev/null | sed -E 's/.*session id:[[:space:]]*//' | cut -d' ' -f1)
  alive=$(pgrep -f "codex exec.*(${sid:-__none__}|$wt)" >/dev/null 2>&1 && echo alive || echo done)
  age=$(( now - $(stat -f %m "$d/log" 2>/dev/null || echo "$now") ))
  br=$(git -C "$wt" branch --show-current 2>/dev/null)
  pr=""; [ -n "$br" ] && pr=$(gh pr list --repo "oramasearch/$repo" --head "$br" --state all --json url,state --jq '.[0] // empty | "\(.state) \(.url)"' 2>/dev/null)
  last=$(grep -v '^\s*$' "$d/log" 2>/dev/null | tail -1 | cut -c1-100)
  printf '%-28s %-5s %5ss  %-60s %s\n' "$name" "$alive" "$age" "${pr:--}" "$last"
done
