# resurrect

Print + copy the command to resume the current **Claude Code** session
(`cd <home> && claude -r <session-id>`). Run it inside a session; paste the
result into a fresh terminal to revive the session. Works on Windows (Git Bash)
and WSL — one script, OS auto-detected.

## Install

```bash
git clone https://github.com/max-nothacker/resurrect.git ~/repos/resurrect
ln -s ~/repos/resurrect/resurrect ~/.local/bin/resurrect   # once per environment
```

## Update / uninstall

```bash
git -C ~/repos/resurrect pull     # update (symlink serves it instantly)
rm ~/.local/bin/resurrect         # uninstall
```

## License

MIT
