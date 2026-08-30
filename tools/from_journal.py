#!/usr/bin/env python3
"""Rebuild the extraction workflow's return value from its transcript directory.

The workflow's own return value is the normal input to build_data.py. This is
the fallback: it reads each agent transcript to recover which file that agent
was assigned, pairs extract results with their audit results, and writes the
same shape. Also useful for inspecting a run that is still in flight.

Usage:  python3 tools/from_journal.py <workflow-transcript-dir> [out.json]
"""

import json
import re
import sys
from pathlib import Path

FILE_RE = re.compile(r"univ/(\d{2}-[A-Za-z-]+\.md)")


def agent_prompt(path):
    """First user-role text in an agent transcript."""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = o.get("message") or o
        if msg.get("role") != "user":
            continue
        c = msg.get("content")
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            parts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            if parts:
                return "\n".join(parts)
    return ""


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: from_journal.py <workflow-transcript-dir> [out.json]")
    d = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else d.parent / "rebuilt.json"

    results = {}
    jl = d / "journal.jsonl"
    if jl.exists():
        for line in jl.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") == "result" and o.get("agentId"):
                results[o["agentId"]] = o.get("result")

    extracts, audits, skipped = {}, {}, []
    for t in sorted(d.glob("agent-*.jsonl")):
        aid = t.stem.replace("agent-", "")
        res = results.get(aid)
        if res is None:
            continue
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except json.JSONDecodeError:
                skipped.append((aid, "unparseable result"))
                continue
        if not isinstance(res, dict):
            skipped.append((aid, f"result is {type(res).__name__}"))
            continue

        prompt = agent_prompt(t)
        m = FILE_RE.search(prompt)
        if not m:
            skipped.append((aid, "no file in prompt"))
            continue
        fname = m.group(1)

        if "adversarial auditor" in prompt:
            audits[fname] = res
        else:
            extracts[fname] = res

    schools = []
    for fname in sorted(extracts):
        base = extracts[fname]
        a = audits.get(fname)
        schools.append({
            "file": fname,
            "base": base,
            "dims": (a or {}).get("dims") or base.get("dims", []),
            "scope": (a or {}).get("scope") or base.get("scope", ""),
            "changes": (a or {}).get("changes", []),
            "verdict": (a or {}).get("verdict", "audit_failed"),
        })

    out.write_text(json.dumps({"schools": schools}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"extracts {len(extracts)}   audits {len(audits)}   paired {len(schools)}")
    missing_audit = [s["file"] for s in schools if s["verdict"] == "audit_failed"]
    if missing_audit:
        print("no audit yet: " + ", ".join(missing_audit))
    for aid, why in skipped:
        print(f"  skipped {aid}: {why}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
