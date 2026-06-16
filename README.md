# resurrect

Print + copy the command to **resume the current AI-CLI session**. Run it inside a
session and it prints — and copies to your clipboard — a ready-to-paste command like:

```
cd "C:\Users\you\my-project" && claude -r <session-id>
```

Open a fresh terminal later, paste, and the session revives. The `cd` targets **the
directory the session was started in** — AI-CLI sessions are scoped to their working
directory, so resuming from anywhere else fails with "No conversation found".

## Supported CLIs

`resurrect` auto-detects which assistant you're in via its session-id environment
variable, and emits that CLI's resume command:

| CLI | Env var | Resume command |
|-----|---------|----------------|
| Claude Code | `CLAUDE_CODE_SESSION_ID` | `claude -r <id>` |
| OpenAI Codex | `CODEX_THREAD_ID` | `codex resume <id>` |
| Google Antigravity | `ANTIGRAVITY_CONVERSATION_ID` | `agy --conversation=<id>` |

It also auto-detects the OS, emitting a Windows path (`cd "C:\..."`) in Git Bash vs a
POSIX path (`cd "/home/..."`) in WSL/Linux — always pointing at the session's own
working directory.

### Antigravity note

Antigravity injects `ANTIGRAVITY_CONVERSATION_ID` only into the **agent's** tool
subprocess, not your interactive terminal. So typing `resurrect` yourself won't find
it — instead **ask the agent to run `resurrect`**, and it reads the id from its own
environment.

## Install

```bash
git clone https://github.com/max-nothacker/resurrect.git ~/repos/resurrect
ln -s ~/repos/resurrect/resurrect ~/.local/bin/resurrect   # WSL / Linux / macOS / Git Bash
```

### Windows

Different CLIs use different `!` shells on Windows: **Claude Code** runs Git Bash
(the script above), while **Codex** and **Antigravity** use PowerShell/cmd, which
can't execute a bash script. For those, also install the `.cmd` shim and put
`~/.local/bin` on your Windows PATH:

```bash
ln -s ~/repos/resurrect/resurrect.cmd ~/.local/bin/resurrect.cmd
```
```powershell
# PowerShell, once — add %USERPROFILE%\.local\bin to your User PATH:
[Environment]::SetEnvironmentVariable('PATH',
  [Environment]::GetEnvironmentVariable('PATH','User') + ';' + "$env:USERPROFILE\.local\bin", 'User')
```

`resurrect.cmd` holds **no logic** — it just re-runs the bash `resurrect` via Git
Bash, keeping a single source of truth.

## Update / uninstall

```bash
git -C ~/repos/resurrect pull                          # update (symlinks serve it at once)
rm ~/.local/bin/resurrect ~/.local/bin/resurrect.cmd   # uninstall
```

## Requirements

Git Bash (for the Windows `.cmd` shim) and a clipboard tool: `clip.exe` on
Windows/WSL (used automatically), falling back to `xclip`, `wl-copy`, or `pbcopy`.

## Verify

`bash verify.sh` proves the emitted command actually works: it creates a throwaway
Claude session, runs `resurrect`, then resumes from the emitted directory (must
succeed) **and** from `$HOME` (must fail) — catching the directory-scoping bug that a
string check alone would miss. Run it in Git Bash and in WSL.

## License

MIT
