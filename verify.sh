#!/usr/bin/env bash
# verify.sh — prove `resurrect` emits a command that ACTUALLY resumes the current
# session (not just a well-formed string). Creates a throwaway Claude session, runs
# resurrect, then resumes from the emitted directory (must SUCCEED) and from $HOME
# (must FAIL — that was the v1-v3 bug). Works on Windows Git Bash and WSL.
#
# Usage:  bash verify.sh [path-to-resurrect]   # defaults to the resurrect beside this file
# Exit:   0 = PASS, 1 = FAIL, 2 = SKIP (claude not available)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RESURRECT="${1:-$HERE/resurrect}"
command -v claude >/dev/null 2>&1 || { echo "VERDICT: SKIP (claude not on PATH)"; exit 2; }

TD=$(mktemp -d); cd "$TD" || { echo "VERDICT: FAIL (tempdir)"; exit 1; }
echo "test dir: $TD"
RAW=$(timeout 180 claude -p "Reply with exactly: READY" --output-format json 2>&1)
SID=$(printf '%s' "$RAW" | jq -r '.session_id // .sessionId // empty' 2>/dev/null)
[ -z "$SID" ] && SID=$(printf '%s' "$RAW" | grep -oiE '[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}' | head -1)
[ -z "$SID" ] && { echo "VERDICT: FAIL (no session id); raw: $(printf '%s' "$RAW" | head -c 300)"; rm -rf "$TD"; exit 1; }
echo "session: $SID"

EMITTED=$(cd "$TD" && CLAUDE_CODE_SESSION_ID="$SID" "$RESURRECT"); echo "emitted: $EMITTED"

cd "$TD"; A=$(timeout 180 claude -r "$SID" -p "Reply RESUMED" --output-format json 2>&1)
printf '%s' "$A" | grep -qi "no conversation found" && AO=0 || AO=1
cd "$HOME"; B=$(timeout 120 claude -r "$SID" -p "x" 2>&1)
printf '%s' "$B" | grep -qi "no conversation found" && BF=1 || BF=0
rm -rf "$TD"

echo "resume from session dir : $([ "$AO" = 1 ] && echo OK || echo FAILED)"
echo "resume from \$HOME (bug) : $([ "$BF" = 1 ] && echo CORRECTLY-FAILED || echo WRONGLY-RESUMED)"
{ [ "$AO" = 1 ] && [ "$BF" = 1 ]; } && { echo "VERDICT: PASS"; exit 0; } || { echo "VERDICT: FAIL"; exit 1; }
