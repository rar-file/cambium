"""Every species-file value changed since a given commit, commit by commit.

    python tools/species_history.py c3fd2dc
"""
import subprocess
import sys

import yaml


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8").stdout


def flat(o, p=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flat(v, f"{p}.{k}" if p else str(k)))
    else:
        out[p] = o
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base = sys.argv[1]
    F = "species/betula_pendula.yaml"
    commits = git("log", "--reverse", "--format=%h %s", f"{base}^..HEAD", "--", F).strip().split("\n")
    prev = flat(yaml.safe_load(git("show", f"{base}^:{F}")))
    for line in commits:
        h, subject = line.split(" ", 1)
        cur = flat(yaml.safe_load(git("show", f"{h}:{F}")))
        ch = [(k, prev.get(k, "(new)"), cur.get(k, "(gone)")) for k in sorted(set(prev) | set(cur)) if prev.get(k, "(new)") != cur.get(k, "(gone)")]
        if ch:
            print(f"\n{h} {subject[:90]}")
            for k, a, b in ch:
                print(f"  {k}: {a} -> {b}")
        prev = cur


if __name__ == "__main__":
    main()
