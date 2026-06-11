# resurrect

Print + copy the command to **resume the current AI-CLI session**. Run it inside a
session and it prints — and copies to your clipboard — a ready-to-paste command like:

```
cd C:\Users\you && claude -r <session-id>
```

Open a fresh terminal later, paste, and the session revives.

## Supported CLIs

`resurrect` auto-detects which assistant you're in via its session-id environment
variable, and emits that CLI's resume command:

| CLI | Env var | Resume command |
|-----|---------|----------------|
| Claude Code | `CLAUDE_CODE_SESSION_ID` | `claude -r <id>` |
| OpenAI Codex | `CODEX_THREAD_ID` | `codex resume <id>` |
| Google Antigravity | `ANTIGRAVITY_CONVERSATION_ID` | `agy --conversation=<id>` |

It also auto-detects the OS — Windows Git Bash (`cd C:\Users\you`) vs WSL/Linux
(`cd ~`) — so one script works everywhere.

### Antigravity note

Antigravity injects `ANTIGRAVITY_CONVERSATION_ID` only into the **agent's** tool
subprocess, not your interactive terminal. So typing `resurrect` yourself won't find
it — instead **ask the agent to run `resurrect`**, and it reads the id from its own
environment.

## Install

```bash
git clone https://github.com/max-nothacker/resurrect.git ~/repos/resurrect
ln -s ~/repos/resurrect/resurrect ~/.local/bin/resurrect   # once per environment
```

Do this in each environment you use (Windows Git Bash and WSL each have their own
`~/.local/bin`; both can symlink the same file).

## Update / uninstall

```bash
git -C ~/repos/resurrect pull     # update — the symlink serves the new version at once
rm ~/.local/bin/resurrect         # uninstall
```

## Requirements

A clipboard tool: `clip.exe` (present on Windows/WSL, used automatically) — falls back
to `xclip`, `wl-copy`, or `pbcopy` if available.

## License

MIT
