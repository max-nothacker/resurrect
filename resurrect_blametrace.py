#!/usr/bin/env python
"""Single source of truth for the `blame_trace` frontmatter stamp.

Records which AI-CLI session created/edited a Markdown note, so the session can
later be resurrected (`cd <cwd> && claude -r <session-id>`). Each touch becomes
one inline-flow mapping in a `blame_trace:` block list, deduped by session:

    blame_trace:
      - {orchestrator: claude-code, session-id: <uuid>, cwd: '<dir>', timestamp: <iso>}

Two entry points, one format (this file):
  * PostToolUse hook  -> no argv, reads the hook JSON on stdin.
  * `resurrect --markdown <file>` -> argv, reads --file/--session/--cwd/...

Frontmatter is edited as a protected text region (no YAML library) so existing
hand-styled frontmatter is never reflowed. Fail-open: any problem -> leave the
file untouched, exit 0.
"""
import argparse
import json
import os
import sys
from datetime import datetime

# Toggle: True -> only stamp files inside an Obsidian vault (via detect_obsidian).
#         False -> stamp every .md the hook sees.
OBSIDIAN_ONLY = True

BOM = "\ufeff"

# Make the sibling detect_obsidian module importable when run as a real file.
# Under the PostToolUse exec(open()) shim __file__ is undefined and the hook
# command injects the repo dir onto sys.path instead.
if "__file__" in globals():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Per-note opt-outs + write-protection flags (matched against frontmatter head).
FM_PROTECT = (
    "llm_write_allowed: false", 'llm_write_allowed: "false"',
    "llm_write: false", 'llm_write: "false"',
    "blame_trace: false", 'blame_trace: "false"',
)


def is_protected_file(content):
    c = content[1:] if content.startswith(BOM) else content
    if not c.startswith("---"):
        return False
    end = c.find("\n---", 3)
    head = c[:end if end != -1 else 400].lower()
    return any(flag in head for flag in FM_PROTECT)


def _yq(s):
    """Render a YAML single-quoted scalar (backslashes stay literal)."""
    return "'" + s.replace("'", "''") + "'"


def render_entry(orchestrator, session_id, cwd, timestamp):
    return (f"{{orchestrator: {orchestrator}, session-id: {session_id}, "
            f"cwd: {_yq(cwd)}, timestamp: {timestamp}}}")


def upsert(content, entry, session_id, nl):
    """Insert/update the blame_trace entry; return the new content."""
    bom = ""
    if content.startswith(BOM):
        bom, content = BOM, content[1:]
    item_line = f"  - {entry}{nl}"
    sid_token = f"session-id: {session_id}"

    def fresh():
        return f"{bom}---{nl}blame_trace:{nl}{item_line}---{nl}{nl}{content}"

    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return fresh()

    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:                      # malformed (no closing fence) -> prepend fresh
        return fresh()

    inner = list(lines[1:close])
    bt = next((i for i, l in enumerate(inner) if l.lstrip().startswith("blame_trace:")), None)

    if bt is None:                         # no key yet -> add it at end of frontmatter
        inner += [f"blame_trace:{nl}", item_line]
    else:
        j = bt + 1
        items = []
        while j < len(inner) and inner[j].lstrip().startswith("-"):
            items.append(j)
            j += 1
        replaced = False
        for idx in items:                  # dedup: same session -> refresh in place
            if sid_token in inner[idx]:
                inner[idx] = item_line
                replaced = True
                break
        if not replaced:
            at = (items[-1] + 1) if items else (bt + 1)
            inner.insert(at, item_line)

    return bom + lines[0] + "".join(inner) + lines[close] + "".join(lines[close + 1:])


def stamp(file_path, session_id, cwd, orchestrator, timestamp):
    if not file_path or not file_path.lower().endswith(".md"):
        return
    if not session_id:
        return
    if OBSIDIAN_ONLY:
        try:
            import detect_obsidian
        except Exception:
            return                          # detector unavailable -> don't stamp
        if not detect_obsidian.is_in_vault(file_path):
            return
    if not os.path.isfile(file_path):
        return
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return
    if is_protected_file(content):
        return
    if not timestamp:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    nl = "\r\n" if "\r\n" in content else "\n"
    new = upsert(content, render_entry(orchestrator, session_id, cwd, timestamp),
                 session_id, nl)
    if new != content:
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
        except OSError:
            return


def main():
    argv = sys.argv[1:]
    if argv:                                # CLI mode (resurrect --markdown)
        ap = argparse.ArgumentParser(description="Stamp blame_trace into a Markdown file.")
        ap.add_argument("--file", required=True)
        ap.add_argument("--session", required=True)
        ap.add_argument("--cwd", default="")
        ap.add_argument("--orchestrator", default="claude-code")
        ap.add_argument("--timestamp", default=None)
        a = ap.parse_args(argv)
        stamp(a.file, a.session, a.cwd, a.orchestrator, a.timestamp)
    else:                                   # hook mode (PostToolUse JSON on stdin)
        try:
            data = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError, EOFError):
            return
        ti = data.get("tool_input") or {}
        stamp(ti.get("file_path") or "",
              data.get("session_id") or "",
              data.get("cwd") or "",
              "claude-code", None)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
