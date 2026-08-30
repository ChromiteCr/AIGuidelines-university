#!/usr/bin/env python3
"""univ/*.md  ->  data/policies.json

Three jobs, in order:

1. VERIFY. Every non-silent cell carries an evidence quote. Each quote is
   checked by exact string matching against the one file it claims to come
   from. A quote that is not literally in that file is a fabrication and the
   cell is demoted to unverified. A quote that turns up in some *other*
   school's file but not its own is hard evidence of cross-contamination and
   is reported by name.
2. NORMALIZE. Raw codes are validated against tools/codebook.py and joined to
   bilingual labels and strictness ranks.
3. AGGREGATE. Per-dimension distributions, silence rates, consensus and
   divergence, per-school coverage.

Usage:  python3 tools/build_data.py <raw-workflow-output.json>
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import codebook as cb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
UNIV = ROOT / "univ"
OUT = ROOT / "data" / "policies.json"

TAKEAWAY_HEADING = re.compile(r"^##+\s*.*takeaway", re.I | re.M)


# --- text normalisation ladder ---------------------------------------------
# Each rung is more forgiving than the last. We record which rung matched so
# the atlas can show "verbatim" vs "matched after normalising punctuation".

def n_raw(s):
    return s


def n_space(s):
    return re.sub(r"\s+", " ", s).strip()


def n_punct(s):
    s = unicodedata.normalize("NFKC", s)
    for a, b in [("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"),
                 ("—", "-"), ("–", "-"), ("…", "..."), (" ", " ")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def n_loose(s):
    return re.sub(r"[^a-z0-9]+", " ", n_punct(s).lower()).strip()


LADDER = [("verbatim", n_raw), ("whitespace", n_space),
          ("punctuation", n_punct), ("loose", n_loose)]


def locate(quote, text):
    """Return (rung, index) for the strictest rung that finds quote in text."""
    if not quote or not quote.strip():
        return None, -1
    for name, fn in LADDER:
        q, t = fn(quote), fn(text)
        if len(q) < 12:
            continue
        i = t.find(q)
        if i >= 0:
            return name, i
    return None, -1


def split_takeaways(text):
    """(university source text, collector-written takeaways text)"""
    m = TAKEAWAY_HEADING.search(text)
    if not m:
        return text, ""
    return text[:m.start()], text[m.start():]


SOURCE_NAME = re.compile(r"^\d{2}-[A-Za-z][A-Za-z-]*\.md$")


def load_files():
    """The 30 numbered source files and nothing else. COPYRIGHT.md is prose,
    and trim proposals (02-MIT.trimmed.md) are near-duplicates of a real
    source — either one swept in here would produce phantom
    cross-contamination hits against the file it was derived from."""
    files = {}
    for p in sorted(UNIV.glob("*.md")):
        if SOURCE_NAME.match(p.name):
            files[p.name] = p.read_text(encoding="utf-8")
    return files


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: build_data.py <raw-workflow-output.json>")

    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    schools_raw = raw.get("schools") or raw.get("result", {}).get("schools") or raw
    files = load_files()
    dim_order = cb.dim_index()

    problems = []
    schools = []

    for rec in schools_raw:
        fname = rec["file"]
        base = rec.get("base", {})
        text = files[fname]
        src_text, take_text = split_takeaways(text)
        num = int(fname.split("-")[0])
        slug = fname.replace(".md", "")

        cells = {}
        for entry in rec.get("dims", []):
            key = entry.get("key", "")
            if key not in cb.VALUES:
                problems.append(f"{slug}: unknown dimension key {key!r}")
                continue

            meta = cb.value_meta(key, entry.get("value", ""))
            if meta is None:
                problems.append(
                    f"{slug}/{key}: invalid value {entry.get('value')!r} -> demoted to not_addressed")
                meta = cb.value_meta(key, "not_addressed")

            quote = (entry.get("evidence") or "").strip()
            # Strip quotation marks an agent may have wrapped around the quote.
            if len(quote) > 2 and quote[0] in "\"“" and quote[-1] in "\"”":
                quote = quote[1:-1].strip()

            cell = {
                "dim": key,
                "value": meta["value"],
                "zh": meta["zh"],
                "en": meta["en"],
                "rank": meta["rank"],
                "short": cb.short_label(key, meta["value"]),
                "note": (entry.get("note") or "").strip(),
                "evidence": quote,
                "match": None,
                "from_takeaways": False,
            }

            if meta["value"] == "not_addressed":
                cell["evidence"] = ""
            elif not quote:
                cell["match"] = "missing"
                problems.append(f"{slug}/{key}: value {meta['value']} with no evidence -> demoted")
                cell.update(cb_demote(key))
            else:
                rung, _ = locate(quote, src_text)
                if rung:
                    cell["match"] = rung
                else:
                    # Not in the university source text. Is it in the collector's
                    # takeaways instead? Is it in some other school's file?
                    t_rung, _ = locate(quote, take_text)
                    if t_rung:
                        cell["match"] = "takeaways_only"
                        cell["from_takeaways"] = True
                        problems.append(
                            f"{slug}/{key}: evidence comes from the collector takeaways, not the source")
                    else:
                        elsewhere = [f for f, t in files.items()
                                     if f != fname and locate(quote, t)[0]]
                        if elsewhere:
                            cell["match"] = "wrong_school"
                            cell["found_in"] = elsewhere
                            problems.append(
                                f"{slug}/{key}: CROSS-CONTAMINATION, quote belongs to {elsewhere}")
                        else:
                            cell["match"] = "not_found"
                            problems.append(f"{slug}/{key}: evidence not found in the file")
                        cell.update(cb_demote(key))

            cells[key] = cell

        for key, _g, _zh, _en, _q in [(d[0], d[1], d[2], d[3], d[4]) for d in cb.DIMENSIONS]:
            if key not in cells:
                m = cb.value_meta(key, "not_addressed")
                cells[key] = {"dim": key, "value": m["value"], "zh": m["zh"], "en": m["en"],
                              "rank": 0, "short": cb.short_label(key, m["value"]),
                              "note": "", "evidence": "", "match": None,
                              "from_takeaways": False}
                problems.append(f"{slug}/{key}: dimension missing from extraction -> not_addressed")

        scope = rec.get("scope") or base.get("scope") or "university_wide"
        if scope not in cb.SCOPE:
            problems.append(f"{slug}: invalid scope {scope!r} -> university_wide")
            scope = "university_wide"

        quote_obj = base.get("quote") or {}
        q_text = (quote_obj.get("text") or "").strip()
        q_rung, _ = locate(q_text, src_text) if q_text else (None, -1)
        if q_text and not q_rung:
            problems.append(f"{slug}: notable_quote not verbatim in the file -> dropped")
            q_text = ""

        covered = sum(1 for c in cells.values() if c["rank"] > 0)
        schools.append({
            "id": slug,
            "num": num,
            "name": base.get("school") or slug.split("-", 1)[1].replace("-", " "),
            "short": short_name(slug),
            "file": "univ/" + fname,
            "scope": scope,
            "scope_zh": cb.SCOPE[scope][0],
            "scope_en": cb.SCOPE[scope][1],
            "scope_note": (base.get("scope_note") or "").strip(),
            "sources": [s for s in base.get("sources", []) if s.get("url")],
            "cells": [cells[d[0]] for d in cb.DIMENSIONS],
            "disclose": [d for d in base.get("disclose", []) if d in cb.DISCLOSE_ITEMS],
            "tiers": base.get("tiers", []),
            "takeaways": base.get("takeaways", []),
            "quote": {"text": q_text, "why": (quote_obj.get("why") or "").strip()},
            "covered": covered,
            "strictness": sum(c["rank"] for c in cells.values()),
            "audit": {"verdict": rec.get("verdict", "audit_failed"),
                      "changes": rec.get("changes", [])},
        })

    schools.sort(key=lambda s: s["num"])

    # --- aggregates ---------------------------------------------------------
    dimensions = []
    for key, group, zh, en, question in cb.DIMENSIONS:
        dist = {}
        for s in schools:
            c = s["cells"][dim_order[key]]
            dist.setdefault(c["value"], []).append(s["id"])
        ordered = []
        for v, vzh, ven, rank in cb.VALUES[key]:
            ids = dist.get(v, [])
            ordered.append({"value": v, "zh": vzh, "en": ven, "rank": rank,
                            "short": cb.short_label(key, v),
                            "n": len(ids), "schools": ids})
        silent = len(dist.get("not_addressed", []))
        covered = len(schools) - silent
        top = max((o for o in ordered if o["value"] != "not_addressed"),
                  key=lambda o: o["n"], default=None)
        binary = len(cb.VALUES[key]) == 2
        dimensions.append({
            "key": key, "group": group, "zh": zh, "en": en, "question": question,
            "binary": binary,
            "dist": ordered,
            "covered": covered, "silent": silent,
            "silence_rate": round(silent / len(schools), 3),
            "top_value": top["value"] if top else None,
            "top_n": top["n"] if top else 0,
            # how concentrated the non-silent answers are: 1.0 = total agreement
            "agreement": round(top["n"] / covered, 3) if covered and top else 0.0,
        })

    total_cells = len(schools) * len(cb.DIMENSIONS)
    filled = sum(1 for s in schools for c in s["cells"] if c["rank"] > 0)
    verbatim = sum(1 for s in schools for c in s["cells"] if c["match"] == "verbatim")
    matched = sum(1 for s in schools for c in s["cells"]
                  if c["match"] in ("verbatim", "whitespace", "punctuation", "loose"))

    data = {
        "meta": {
            "schools": len(schools),
            "dimensions": len(cb.DIMENSIONS),
            "cells": total_cells,
            "filled": filled,
            "silent": total_cells - filled,
            "evidence_verbatim": verbatim,
            "evidence_matched": matched,
            "problems": problems,
            "accessed": "2026-08-29",
        },
        "groups": [{"key": k, "zh": zh, "en": en, "hint": h} for k, zh, en, h in cb.GROUPS],
        "dimensions": dimensions,
        "values": {k: [{"value": v, "zh": zh, "en": en, "rank": r,
                        "short": cb.short_label(k, v)} for v, zh, en, r in vs]
                   for k, vs in cb.VALUES.items()},
        "disclose_items": {k: {"zh": v[0], "en": v[1]} for k, v in cb.DISCLOSE_ITEMS.items()},
        "scopes": {k: {"zh": v[0], "en": v[1], "hint": v[2]} for k, v in cb.SCOPE.items()},
        "verdicts": {k: {"zh": v[0], "en": v[1]} for k, v in cb.VERDICT.items()},
        "schools": schools,
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"schools           {len(schools)}")
    print(f"cells             {total_cells}  filled {filled}  silent {total_cells - filled}")
    print(f"evidence verbatim {verbatim}/{filled}   matched-after-normalising {matched}/{filled}")
    print(f"problems          {len(problems)}")
    for p in problems:
        print("  ! " + p)
    print(f"\nwrote {OUT.relative_to(ROOT)}")


def cb_demote(key):
    m = cb.value_meta(key, "not_addressed")
    return {"value": m["value"], "zh": m["zh"], "en": m["en"], "rank": 0,
            "short": cb.short_label(key, m["value"])}


SHORT = {
    "01-Stanford": "Stanford", "02-MIT": "MIT", "03-Harvard": "Harvard", "04-Yale": "Yale",
    "05-Cornell": "Cornell", "06-Penn": "Penn", "07-Columbia": "Columbia", "08-Duke": "Duke",
    "09-Northwestern": "Northwestern", "10-UChicago": "UChicago", "11-Princeton": "Princeton",
    "12-Caltech": "Caltech", "13-Johns-Hopkins": "Johns Hopkins", "14-Brown": "Brown",
    "15-Vanderbilt": "Vanderbilt", "16-UC-Berkeley": "UC Berkeley", "17-UCLA": "UCLA",
    "18-Rice": "Rice", "19-Dartmouth": "Dartmouth", "20-Notre-Dame": "Notre Dame",
    "21-Carnegie-Mellon": "Carnegie Mellon", "22-Michigan": "Michigan",
    "23-Georgetown": "Georgetown", "24-Emory": "Emory", "25-UNC-Chapel-Hill": "UNC Chapel Hill",
    "26-WashU": "WashU", "27-UVA": "UVA", "28-USC": "USC", "29-UC-San-Diego": "UC San Diego",
    "30-NYU": "NYU",
}


def short_name(slug):
    return SHORT.get(slug, slug.split("-", 1)[1].replace("-", " "))


if __name__ == "__main__":
    main()
