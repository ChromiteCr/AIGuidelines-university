"""Minimal Markdown renderer for the univ/ and admissions/ source files, with
quotation highlighting.

It supports exactly what a survey of both corpora found in use: ATX headings,
paragraphs, unordered and ordered lists (nested by indentation), blockquotes,
horizontal rules, **bold**, *italic*, bare URLs, and — in admissions/ only —
[text](url) links and `inline code`. There are no tables and no raw HTML.

Links go through a caller-supplied resolver, because the admissions files point
at local research files that are not published: the resolver maps each target
to a site address, or returns None to keep only the link text.

Highlighting
------------
Callers pass spans as (start, end, label) in RAW-file character offsets — the
atlas evidence quotes are verified exact substrings of the raw file, so their
offsets come straight from str.find. Spans may overlap each other, cross line
and block boundaries, and start or end inside **bold** markup. None of that can
produce broken HTML here, because text is cut into runs wherever the style or
the set of covering labels changes, and every run is wrapped on its own:

    <a><strong><em><mark>run</mark></em></strong></a>

so a <mark> never straddles a block boundary or an inline tag boundary.

For each label the first run gets an empty anchor (<span id=...>) placed before
it, and the last run is followed by whatever tag_html(label) returns.

Block options
-------------
A block carrying "dim": True is wrapped, with its dimmed neighbours, in the
container dim_html opens; the school pages use it for source text that was not
part of the research. fold(heading_text, level) may return a <summary> label, and
that heading's section is then rendered inside a closed <details>.
"""

import html
import re

_H = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_HR = re.compile(r"^-{3,}\s*$")
_LI = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
_Q = re.compile(r"^>\s?(.*)$")
_BLANK = re.compile(r"^\s*$")
_KV = re.compile(r"^([A-Z][A-Za-z ]{1,40}):\s+(.*)$")
# admissions/ keys also use "/", "-" and parentheses: "Scope / authority",
# "Original campus-AI source file", "Related guidance (different scope)"
KV_WIDE = re.compile(r"^([A-Z][A-Za-z /()-]{1,64}):\s+(.*)$")
_URL = re.compile(r"https?://[^\s<>\"]+")
_MDLINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<![*\w])\*(?![*\s])([^*\n]+?)(?<![*\s])\*(?![*\w])")
_URL_TAIL = ".,;:)]’”\"'"


def _lines(raw):
    pos = 0
    for line in raw.split("\n"):
        yield pos, line
        pos += len(line) + 1


def _is_block_start(line):
    return bool(_BLANK.match(line) or _H.match(line) or _HR.match(line)
                or _Q.match(line) or _LI.match(line))


def parse(raw):
    """Raw text -> list of blocks. Every piece of content keeps its raw offset."""
    L = list(_lines(raw))
    blocks, i = [], 0
    while i < len(L):
        off, line = L[i]
        if _BLANK.match(line):
            i += 1
            continue
        m = _H.match(line)
        if m:
            blocks.append({"t": "h", "level": len(m.group(1)), "seg": (off + m.start(2), m.group(2))})
            i += 1
            continue
        if _HR.match(line):
            blocks.append({"t": "hr", "at": off})
            i += 1
            continue
        if _Q.match(line):
            paras, cur = [], []
            while i < len(L) and _Q.match(L[i][1]):
                o, l = L[i]
                mq = _Q.match(l)
                if mq.group(1).strip():
                    cur.append((o + mq.start(1), mq.group(1)))
                elif cur:
                    paras.append(cur)
                    cur = []
                i += 1
            if cur:
                paras.append(cur)
            blocks.append({"t": "quote", "paras": paras})
            continue
        if _LI.match(line):
            items = []
            while i < len(L):
                o, l = L[i]
                ml = _LI.match(l)
                if ml:
                    marker = ml.group(2)
                    items.append({
                        "indent": len(ml.group(1).expandtabs(4)),
                        "ordered": marker[0].isdigit(),
                        "num": int(marker[:-1]) if marker[0].isdigit() else None,
                        "segs": [(o + ml.start(3), ml.group(3))],
                    })
                    i += 1
                    continue
                if items and l[:1] in (" ", "\t") and not _BLANK.match(l):
                    body = l.lstrip()
                    items[-1]["segs"].append((o + len(l) - len(body), body))
                    i += 1
                    continue
                break
            blocks.append({"t": "list", "items": items})
            continue
        segs = []
        while i < len(L) and not _is_block_start(L[i][1]):
            segs.append(L[i])
            i += 1
        blocks.append({"t": "p", "segs": segs})
    return blocks


def _kv_split(seg, kv_re=_KV):
    """'Official source: https://…' -> ('Official source', value_seg) or None."""
    off, text = seg
    m = kv_re.match(text)
    if not m:
        return None
    return m.group(1), (off + m.start(2), m.group(2))


def block_span(b):
    """(first, last) raw offset of a block's content, or None for an empty block."""
    if b["t"] == "h":
        segs = [b["seg"]]
    elif b["t"] == "p":
        segs = b["segs"]
    elif b["t"] == "quote":
        segs = [s for para in b["paras"] for s in para]
    elif b["t"] == "list":
        segs = [s for it in b["items"] for s in it["segs"]]
    else:
        return (b["at"], b["at"] + 1) if "at" in b else None
    if not segs:
        return None
    return segs[0][0], segs[-1][0] + len(segs[-1][1])


def _omission(paras):
    """MIT's trim markers → (n_words, is_further) or None."""
    text = " ".join(t for para in paras for _, t in para)
    if "words omitted" not in text:
        return None
    m = re.search(r"(\d+)\s+(further\s+)?words omitted", text)
    return (int(m.group(1)), bool(m.group(2))) if m else None


class Renderer:
    def __init__(self, raw, spans, tag_html, anchor_id, kv_label=None, omission_html=None,
                 resolve=None, kv_re=None, dim_html=None, fold=None):
        self.raw = raw
        self.spans = spans
        self.tag_html = tag_html
        self.anchor_id = anchor_id
        self.kv_label = kv_label or (lambda k: html.escape(k))
        self.omission_html = omission_html
        self.resolve = resolve or (lambda url: url)
        self.kv_re = kv_re or _KV
        self.dim_html = dim_html or '<div class="dim">'
        self.fold = fold or (lambda text, level: None)
        self.first, self.last = {}, {}
        self.anchored, self.tagged = set(), set()
        self._cache = {}

    # ---- character-level analysis of one content segment -------------------
    def _chars(self, seg):
        if seg in self._cache:
            return self._cache[seg]
        off, text = seg
        n = len(text)
        emit = [True] * n
        bold = [False] * n
        ital = [False] * n
        link = [None] * n
        code = [False] * n
        # `code` first: its content is literal, so nothing inside it is a link or emphasis
        for m in _CODE.finditer(text):
            emit[m.start()] = emit[m.end() - 1] = False
            for k in range(m.start() + 1, m.end() - 1):
                code[k] = True
        # [text](target): the brackets and target are markup; the resolver decides
        # whether the text becomes a link or stays plain
        for m in _MDLINK.finditer(text):
            if any(code[k] for k in range(m.start(), m.end())):
                continue
            target = self.resolve(m.group(2))
            for k in list(range(m.start(), m.start(1))) + list(range(m.end(1), m.end())):
                emit[k] = False
            if target:
                for k in range(m.start(1), m.end(1)):
                    link[k] = target
        for m in _URL.finditer(text):
            url = m.group(0).rstrip(_URL_TAIL)
            span = range(m.start(), m.start() + len(url))
            if any(link[k] or code[k] or not emit[k] for k in span):
                continue
            for k in span:
                link[k] = url
        for m in _BOLD.finditer(text):
            s, e = m.start(), m.end()
            if any(link[k] for k in range(s, e)):
                continue
            if any(code[k] or not emit[k] for k in (s, s + 1, e - 2, e - 1)):
                continue
            emit[s] = emit[s + 1] = emit[e - 1] = emit[e - 2] = False
            for k in range(s + 2, e - 2):
                bold[k] = True
        for m in _ITAL.finditer(text):
            s, e = m.start(), m.end()
            if link[s] or link[e - 1] or not emit[s] or not emit[e - 1] or code[s] or code[e - 1]:
                continue
            emit[s] = emit[e - 1] = False
            for k in range(s + 1, e - 1):
                ital[k] = True
        hl = [frozenset()] * n
        for a, b, lab in self.spans:
            lo, hi = max(a, off), min(b, off + n)
            for k in range(lo, hi):
                hl[k - off] = hl[k - off] | {lab}
        res = (emit, bold, ital, link, hl, code)
        self._cache[seg] = res
        return res

    def _measure(self, seg):
        emit, _, _, _, hl, _ = self._chars(seg)
        for k, e in enumerate(emit):
            if not e:
                continue
            p = seg[0] + k
            for lab in hl[k]:
                self.first[lab] = min(self.first.get(lab, p), p)
                self.last[lab] = max(self.last.get(lab, p), p)

    def inline(self, seg):
        emit, bold, ital, link, hl, code = self._chars(seg)
        off, text = seg
        runs = []
        for k, ch in enumerate(text):
            if not emit[k]:
                continue
            key = (link[k], bold[k], ital[k], hl[k], code[k])
            if runs and runs[-1][0] == key:
                runs[-1][2] = off + k
                runs[-1][3].append(ch)
            else:
                runs.append([key, off + k, off + k, [ch]])
        out = []
        for (lnk, b, it, labs, cd), s_abs, e_abs, chars in runs:
            for lab in sorted(labs):
                if lab not in self.anchored and s_abs <= self.first[lab] <= e_abs:
                    out.append(f'<span class="ev-anchor" id="{self.anchor_id(lab)}"></span>')
                    self.anchored.add(lab)
            h = html.escape("".join(chars), quote=False)
            if labs:
                h = f'<mark data-ev="{" ".join(sorted(labs))}">{h}</mark>'
            if cd:
                h = f"<code>{h}</code>"
            if it:
                h = f"<em>{h}</em>"
            if b:
                h = f"<strong>{h}</strong>"
            if lnk:
                # only off-site links open a new tab; links within the site do not
                ext = ' target="_blank" rel="noopener noreferrer"' if lnk.startswith(("http://", "https://")) else ""
                h = f'<a href="{html.escape(lnk, quote=True)}"{ext}>{h}</a>'
            out.append(h)
            for lab in sorted(labs):
                if lab not in self.tagged and s_abs <= self.last[lab] <= e_abs:
                    out.append(self.tag_html(lab))
                    self.tagged.add(lab)
        return "".join(out)

    # ---- block level --------------------------------------------------------
    def _item_segs(self, item, kv):
        if kv:
            key, val = _kv_split(item["segs"][0], self.kv_re)
            return [val] + item["segs"][1:]
        return item["segs"]

    def is_kv(self, items):
        return all(_kv_split(it["segs"][0], self.kv_re) for it in items)

    def _walk_segs(self, blocks):
        """Every content segment in document order — must mirror render()."""
        for b in blocks:
            if b["t"] == "h":
                yield b["seg"]
            elif b["t"] == "p":
                yield from b["segs"]
            elif b["t"] == "quote":
                if not _omission(b["paras"]):
                    for para in b["paras"]:
                        yield from para
            elif b["t"] == "list":
                kv = self.is_kv(b["items"])
                for it in b["items"]:
                    yield from self._item_segs(it, kv)

    def _list(self, items):
        kv = self.is_kv(items)
        out, stack = [], []
        for it in items:
            tag = "ol" if it["ordered"] else "ul"
            if not stack or it["indent"] > stack[-1][0]:
                start = f' start="{it["num"]}"' if tag == "ol" and it["num"] not in (None, 1) else ""
                cls = ' class="kv"' if kv else ""
                out.append(f"<{tag}{cls}{start}>")
                stack.append((it["indent"], tag))
            else:
                while len(stack) > 1 and it["indent"] < stack[-1][0]:
                    out.append(f"</li></{stack.pop()[1]}>")
                out.append("</li>")
            if kv:
                key, val = _kv_split(it["segs"][0], self.kv_re)
                body = [f'<span class="k">{self.kv_label(key)}</span> <span class="v">{self.inline(val)}</span>']
                body += [self.inline(s) for s in it["segs"][1:]]
            else:
                body = [self.inline(s) for s in it["segs"]]
            out.append("<li>" + "\n".join(body))
        while stack:
            out.append(f"</li></{stack.pop()[1]}>")
        return "".join(out)

    def render_all(self, front_items, blocks, takeaway_label):
        """(front-matter html, body html). Both share one measuring pass, so a
        quotation that happens to sit in the front matter is still anchored."""
        front_block = [{"t": "list", "items": front_items}] if front_items else []
        for seg in self._walk_segs(front_block + blocks):
            self._measure(seg)
        front_html = self._list(front_items) if front_items else ""
        return front_html, self._render_blocks(blocks, takeaway_label)

    def _render_blocks(self, blocks, takeaway_label):
        out, in_take, in_dim, fold_level = [], False, False, None
        for b in blocks:
            t = b["t"]
            # a folded section ends at the next heading of the same or a higher level
            ends_fold = fold_level is not None and t == "h" and b["level"] <= fold_level
            starts_take = (not in_take and t == "h" and b["level"] >= 2
                           and re.search(r"takeaway", b["seg"][1], re.I))
            # close innermost first: a dimmed run, then a fold, so tags always nest
            if in_dim and (not b.get("dim") or ends_fold or starts_take):
                out.append("</div>")
                in_dim = False
            if fold_level is not None and (ends_fold or starts_take):
                out.append("</details>")
                fold_level = None
            if t == "h":
                lvl = min(b["level"] + 1, 6)
                # Same boundary build_data.py uses: from the first "takeaway"
                # heading to the end of the file is the collector's own writing.
                if starts_take:
                    out.append(f'<div class="takeaways">{takeaway_label}')
                    in_take = True
                summary = self.fold(b["seg"][1], b["level"]) if fold_level is None else None
                if summary:
                    if in_dim:
                        out.append("</div>")
                        in_dim = False
                    out.append(f'<details class="fold"><summary>{summary}</summary>')
                    fold_level = b["level"]
                    continue
            if b.get("dim") and not in_dim:
                out.append(self.dim_html)
                in_dim = True
            if t == "h":
                out.append(f'<h{lvl} class="src-h{b["level"]}">{self.inline(b["seg"])}</h{lvl}>')
            elif t == "hr":
                out.append("<hr>")
            elif t == "p":
                out.append("<p>" + "\n".join(self.inline(s) for s in b["segs"]) + "</p>")
            elif t == "quote":
                om = _omission(b["paras"])
                if om and self.omission_html:
                    out.append(self.omission_html(*om))
                else:
                    paras = ["<p>" + "\n".join(self.inline(s) for s in para) + "</p>" for para in b["paras"]]
                    out.append("<blockquote>" + "".join(paras) + "</blockquote>")
            elif t == "list":
                out.append(self._list(b["items"]))
        if in_dim:
            out.append("</div>")
        if fold_level is not None:
            out.append("</details>")
        if in_take:
            out.append("</div>")
        return "\n".join(out)

    def missing(self):
        """Labels with a span that never got an anchor or a closing tag."""
        labels = {lab for _, _, lab in self.spans}
        return sorted(labels - self.anchored), sorted(labels - self.tagged)


def split_front(blocks):
    """(title, front-matter list items, remaining blocks).

    The files open with an H1 and a key/value list (Accessed, Format note, …)
    about the file itself. Those are metadata, not the university's text.
    """
    title, front, rest = None, None, []
    for b in blocks:
        if title is None and b["t"] == "h" and b["level"] == 1:
            title = b["seg"][1]
            continue
        if front is None and not rest and b["t"] == "list":
            front = b["items"]
            continue
        rest.append(b)
    return title, front or [], rest
