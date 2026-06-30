#!/usr/bin/env python
"""Detect whether a file lives inside an Obsidian vault.

Two signals, checked in order:
  1. The Obsidian vault registry (obsidian.json) -- every `vaults[*].path`.
  2. A `.obsidian/` marker directory in any ancestor of the file.

No username or absolute path is hardcoded: registry locations are derived from
$APPDATA / the home directory, so this module is safe to ship in a public repo.

Public API: is_in_vault(path) -> bool  /  vault_root_for(path) -> str | None
"""
import json
import os

# Lazily-built, normalized list of registered vault roots (cached per process).
_registry_roots = None


def _norm(p):
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def _registry_locations():
    """Candidate paths of Obsidian's obsidian.json, per platform."""
    home = os.path.expanduser("~")
    locs = []
    appdata = os.environ.get("APPDATA")
    if appdata:                                                       # Windows
        locs.append(os.path.join(appdata, "obsidian", "obsidian.json"))
    locs.append(os.path.join(                                         # macOS
        home, "Library", "Application Support", "obsidian", "obsidian.json"))
    locs.append(os.path.join(                                         # Linux
        home, ".config", "obsidian", "obsidian.json"))
    return locs


def _load_registry_roots():
    """Normalized vault roots from the registry; [] if unreadable/missing."""
    global _registry_roots
    if _registry_roots is not None:
        return _registry_roots
    roots = []
    for jf in _registry_locations():
        if not os.path.isfile(jf):
            continue
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        for v in (data.get("vaults") or {}).values():
            p = v.get("path") if isinstance(v, dict) else None
            if p:
                roots.append(_norm(p))
    _registry_roots = roots
    return roots


def _under(file_norm, root_norm):
    return file_norm == root_norm or file_norm.startswith(root_norm + os.sep)


def vault_root_for(path):
    """Return the vault root containing `path`, else None.

    Registry roots first (cheap, cached); then walk ancestors looking for a
    `.obsidian/` marker directory (catches vaults absent from the registry).
    """
    fn = _norm(path)
    for root in _load_registry_roots():
        if _under(fn, root):
            return root
    d = os.path.dirname(fn)
    prev = None
    while d and d != prev:
        if os.path.isdir(os.path.join(d, ".obsidian")):
            return d
        prev, d = d, os.path.dirname(d)
    return None


def is_in_vault(path):
    return vault_root_for(path) is not None


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        root = vault_root_for(arg)
        print(f"{'IN ' if root else 'OUT'}  {arg}  ->  {root}")
