#!/usr/bin/env python3
"""Propose a fair-use trim of one source file, without touching the original.

Rule applied: keep the front matter and every section that contains text the
atlas actually cites; drop every section that contributes nothing to the
dataset, replacing it with an explicit omission marker naming the word count
and pointing at the official source. Nothing kept is paraphrased or reworded.

The proposal is written alongside the original as <name>.trimmed.md and every
cited quote is re-checked against it, so a trim that would silently break a
matrix cell fails loudly instead.

Pass --tight to also thin the kept sections down to the paragraphs that
actually carry a cited quote. Same guarantee either way: nothing is reworded,
and every citation is re-verified.

Usage:  python3 tools/propose_trim.py univ/02-MIT.md [--tight]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "policies.json"

SECTION = re.compile(r"^(#{2,6} .*)$", re.M)
OMIT = "\n> *[本节共 {n} 词，与本项目引用的条款无关，已略去；全文见上方官方来源。]*\n>\n> *[{n} words omitted here — not cited by this project; see the official source above.]*\n\n"
OMIT_PARA = "\n> *[本节另有 {n} 词未被本项目引用，已略去。]* *[{n} further words omitted.]*\n\n"


def words(s):
    return len(re.findall(r"[A-Za-z']+", s))


def cited_strings(school_id):
    d = json.loads(DATA.read_text(encoding="utf-8"))
    s = next((x for x in d["schools"] if x["id"] == school_id), None)
    if s is None:
        sys.exit(f"{school_id} not found in data/policies.json")
    out = [c["evidence"] for c in s["cells"] if c["evidence"]]
    if s["quote"]["text"]:
        out.append(s["quote"]["text"])
    return out, s


def thin(body, quotes):
    """Keep only the paragraphs carrying a cited quote; report what went."""
    paras = re.split(r"\n\s*\n", body)
    keep, gone = [], 0
    for para in paras:
        if not para.strip():
            continue
        if any(q in para for q in quotes):
            keep.append(para.strip())
        else:
            gone += words(para)
    if not keep:
        return body, 0
    out = "\n\n" + "\n\n".join(keep) + "\n"
    if gone:
        out += OMIT_PARA.format(n=gone)
    return out, gone


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: propose_trim.py univ/NN-Name.md [--tight]")
    tight = "--tight" in sys.argv
    src = ROOT / [a for a in sys.argv[1:] if not a.startswith("--")][0]
    school_id = src.stem
    text = src.read_text(encoding="utf-8")
    quotes, school = cited_strings(school_id)

    # split into [front matter, (heading, body), (heading, body), ...]
    parts = SECTION.split(text)
    front, sections = parts[0], []
    for i in range(1, len(parts), 2):
        sections.append((parts[i], parts[i + 1] if i + 1 < len(parts) else ""))

    kept, dropped, out = [], [], [front]
    for heading, body in sections:
        whole = heading + body
        hits = [q for q in quotes if q in whole]
        # A heading that only labels the section below it (no prose of its own)
        # is kept so the kept sections still read in order.
        if hits or words(body) <= 12:
            new_body = body
            if tight and hits:
                new_body, _ = thin(body, quotes)
            kept.append((heading, len(hits)))
            out.append(heading + (new_body if new_body.endswith("\n\n") else new_body.rstrip("\n") + "\n\n"))
        else:
            dropped.append((heading, words(whole)))
            out.append(heading + "\n" + OMIT.format(n=words(whole)))

    proposal = "".join(out)
    dst = src.with_name(src.stem + (".tight.md" if tight else ".trimmed.md"))
    dst.write_text(proposal, encoding="utf-8")

    # verification: every cited string must survive verbatim
    missing = [q for q in quotes if q not in proposal]

    print(f"source     {sys.argv[1]}          {words(text):>6} 词")
    print(f"proposal   {dst.relative_to(ROOT)}  {words(proposal):>6} 词"
          f"   ({words(proposal)/max(words(text),1):.0%})")
    print(f"\n保留 {len(kept)} 节 / 略去 {len(dropped)} 节\n")
    print("略去的章节（按体量）:")
    for h, w in sorted(dropped, key=lambda x: -x[1]):
        print(f"  {w:>5} 词  {h.strip()[:64]}")
    print("\n保留的章节:")
    for h, n in kept:
        mark = f"  ← {n} 条引文" if n else ""
        print(f"         {h.strip()[:64]}{mark}")

    print(f"\n引文校验：{len(quotes) - len(missing)}/{len(quotes)} 条在压缩版中逐字仍在")
    if missing:
        print("  !! 以下引文会丢失，不能直接替换：")
        for q in missing:
            print(f"     {q[:90]}…")
        sys.exit(1)
    print("\n原文件未改动。确认后替换：")
    print(f"  mv {dst.relative_to(ROOT)} {src.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
