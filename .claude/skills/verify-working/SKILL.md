---
name: verify-working
description: Verify that the `resurrect` tool ACTUALLY resumes the current AI-CLI session end-to-end — not merely that it prints a well-formed string. Use after any change to the resurrect script and before committing/pushing. Runs a headless test that creates a real Claude session, runs resurrect, and confirms the emitted command revives the session while the old $HOME-based command fails. Covers the {Windows, WSL} x {Claude, Codex, Antigravity} matrix.
version: 1.0.0
---

# /verify-working — prove `resurrect` actually resumes

## The lesson this skill exists for

A `resurrect` fix is **NOT verified by checking the output string**. Versions v1-v3
emitted a perfectly-formed `cd C:\Users\maxno && claude -r <id>` — and it was *wrong*,
because AI-CLI sessions are **scoped to the directory they were created in** (Claude
stores them under `~/.claude/projects/<encoded-cwd>/<id>.jsonl`). The string looked
right; the resume failed with "No conversation found".

> **Rule:** a resume/round-trip fix is verified ONLY when you actually resume a real
> session and confirm it is found — AND confirm the buggy variant fails. Never trust
> output format alone.

## Definition of "working"

For each (OS, CLI) cell, the emitted `cd "<dir>" && <cli> resume <id>` must:
1. **SUCCEED** when run from the session's own directory (`<dir>` = where the session
   started = `$PWD`).
2. **FAIL** ("No conversation found") when run from a *different* directory (e.g.
   `$HOME`) — proving the directory matters and the script targets the right one.

## Automated verification — Claude (both OSes), no user needed

The repo ships `verify.sh` (at `~/repos/resurrect/verify.sh`) which does exactly this
headlessly with a throwaway Claude session. Run it in each environment and read the
final `VERDICT:` line:

- **Windows (Git Bash):**
  ```bash
  bash /c/Users/maxno/repos/resurrect/verify.sh
  ```
- **WSL** (its non-interactive PATH lacks `~/.local/bin`, so prepend it for `claude`;
  `MSYS_NO_PATHCONV=1` stops Git Bash mangling the `/mnt/c` path):
  ```bash
  MSYS_NO_PATHCONV=1 wsl -- bash -c 'export PATH="$HOME/.local/bin:$PATH"; bash /mnt/c/Users/maxno/repos/resurrect/verify.sh'
  ```

`PASS` requires `resume from session dir = OK` **and** `resume from $HOME = CORRECTLY-FAILED`.

How it works: `claude -p "..." --output-format json` creates a real, resumable session
scoped to the cwd; capture its `session_id`; run `resurrect` there to get the emitted
command; then `claude -r <id> -p "..."` from the emitted dir (expect success) and from
`$HOME` (expect "No conversation found"). Each `claude` call is a real API call (a few
seconds + tokens) — that cost is the price of genuine verification.

## Codex & Antigravity

Same directory-scoping principle — `codex resume` resumes "from the current directory",
`agy --conversation` likewise — so the `cd "$PWD"` fix covers them identically. Headless
self-verification is not yet wired up:
- **Codex** — feasible in principle (`codex exec` headless + `codex resume`). Extend
  `verify.sh` with a `codex` branch once headless thread-id capture is confirmed.
- **Antigravity** — `ANTIGRAVITY_CONVERSATION_ID` is injected only into the agent's
  tool subprocess, never the user shell, so a user-shell harness can't capture it.
  Verification is **manual**: ask the agent to run `resurrect`, then paste the result.

Until those are automated, the Codex/Antigravity cells are verified by the user's
manual check across the matrix.

## Procedure when invoked

1. Run `verify.sh` for Windows Git Bash and for WSL (commands above); report both `VERDICT`s.
2. If any cell `FAIL`s, do not commit — report exactly which assertion broke (couldn't
   capture session id / resume-from-dir failed / resume-from-$HOME unexpectedly succeeded).
3. State the Codex/Antigravity status honestly (covered by the fix logic; verified manually).
4. Only after the automatable cells PASS is the change safe to commit; push only after
   the user confirms the manual matrix on their machines.
