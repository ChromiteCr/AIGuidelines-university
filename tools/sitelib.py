"""Shared helpers for the three page builders.

build_atlas.py, build_guidelines.py and build_home.py all publish Chinese prose
into docs/, and all three need the same two things: a way to compare text
without tripping over line wrapping, and the CJK line-break fix. Keeping them
here means a correction lands in one place instead of drifting between three
copies.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "policies.json"

# Chinese numerals and English number words, for assertions that have to match
# prose which spells a figure out rather than printing digits.
_UNITS = "零一二三四五六七八九"
EN_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
    8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
    19: "nineteen", 20: "twenty", 27: "twenty-seven", 29: "twenty-nine", 30: "thirty",
}

CJK = r"　-〿一-鿿＀-￯"
_PRE = re.compile(r"<pre\b.*?</pre>", re.S)


def cn(n):
    """Chinese numeral. Falls back to digits above 99, which is never spelled out."""
    if n >= 100:
        return str(n)
    if n < 10:
        return _UNITS[n]
    if n < 20:
        return "十" + (_UNITS[n - 10] if n > 10 else "")
    return _UNITS[n // 10] + "十" + (_UNITS[n % 10] if n % 10 else "")


def flat(s):
    """Collapse whitespace and case.

    Assertions have to survive line wrapping in the source, and an English
    number word is capitalised at the start of a sentence but not mid-sentence.
    Neither difference is a factual one, so neither should fail a check.
    """
    return re.sub(r"\s+", " ", s).lower()


def join_cjk(html):
    """Drop whitespace sitting between two CJK characters; leave <pre> alone.

    The sources wrap Chinese paragraphs at a readable width, but a newline
    between two CJK characters renders as a visible space in the browser.
    """
    keep = _PRE.findall(html)
    html = _PRE.sub("\x00PRE\x00", html)
    html = re.sub(rf"(?<=[{CJK}])\s+(?=[{CJK}])", "", html)
    for block in keep:
        html = html.replace("\x00PRE\x00", block, 1)
    return html


def load_data():
    """(data, dimensions-by-key, count(key, value), disclose(item))"""
    d = json.loads(DATA.read_text(encoding="utf-8"))
    dm = {x["key"]: x for x in d["dimensions"]}

    def count(key, value):
        e = next((y for y in dm[key]["dist"] if y["value"] == value), None)
        return e["n"] if e else 0

    def disclose(item):
        return sum(1 for s in d["schools"] if item in s["disclose"])

    return d, dm, count, disclose


def assertion_builder(collected):
    """Return an `add(label, value, *templates)` that registers text assertions.

    Each template is filled with {n} digits, {c} Chinese numeral and {e} English
    word, then must appear verbatim in the published document. A template using
    {e} for a number with no word form would silently degrade into a partial
    match, so that is an error rather than a quiet pass.
    """
    def add(label, value, *templates):
        for t in templates:
            if "{e}" in t and value not in EN_WORDS:
                raise KeyError(
                    f"{label}: 模板用了 {{e}} 但 EN_WORDS 里没有 {value}，"
                    f"填空后会退化成只匹配一部分的弱断言")
            collected.append(
                (label, value, flat(t.format(n=value, c=cn(value), e=EN_WORDS.get(value, "")))))
    return add


def verify_quotes(html):
    """Every <blockquote> must still be literally present in the file its <cite> names."""
    problems = []
    for m in re.finditer(r"<blockquote>(.*?)</blockquote>", html, re.S):
        block = m.group(1)
        cite = re.search(r"<cite>(.*?)</cite>", block, re.S)
        text = re.sub(r"<[^>]+>", " ", re.sub(r"<cite>.*?</cite>", "", block, flags=re.S))
        text = flat(text).strip().strip('"“”')
        if not cite:
            problems.append(f"blockquote 缺少 <cite>：{text[:60]}…")
            continue
        fname = re.search(r"(univ/[\w.-]+\.md)", cite.group(1))
        if not fname:
            problems.append(f"<cite> 未指明来源文件：{flat(cite.group(1))[:60]}")
            continue
        src = ROOT / fname.group(1)
        if not src.exists():
            problems.append(f"来源文件不存在：{fname.group(1)}")
            continue
        if text not in flat(src.read_text(encoding="utf-8")):
            problems.append(f"非逐字，未在 {fname.group(1)} 中找到：{text[:70]}…")
    return problems


def publish(src_html, dst, checks, label=""):
    """Run the checks against the source, then write the CJK-joined copy to dst."""
    import sys

    hay = flat(src_html)
    bad = [(lab, val, needle) for lab, val, needle in checks if needle not in hay]
    qbad = verify_quotes(src_html)

    tag = f"{label} " if label else ""
    print(f"{tag}数字核对   {len(checks) - len(bad)}/{len(checks)} 处断言与 data/policies.json 一致")
    for lab, val, needle in bad:
        print(f"  ! {lab}：数据是 {val}，文中找不到 {needle!r}")
    nq = len(re.findall(r"<blockquote>", src_html))
    print(f"{tag}引文核对   {nq - len(qbad)}/{nq} 条逐字命中其来源文件")
    for p in qbad:
        print(f"  ! {p}")
    if bad or qbad:
        sys.exit("\n构建中止：文中的断言与数据对不上。改文字，或重跑 build_data.py。")

    out = join_cjk(src_html)
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(out, encoding="utf-8")
    print(f"{tag}wrote {dst.relative_to(ROOT)}  ({len(out.encode('utf-8')) / 1024:.0f} KB, "
          f"去掉 {len(src_html) - len(out)} 处中文断行空格)")
