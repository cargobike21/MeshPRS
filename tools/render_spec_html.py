"""Render spec/MeshPRS-Spec.md as one self-contained HTML page (MeshPRS-Spec.html, next to README.md).

    pip install markdown          (Python-Markdown 3.x; the only dependency)
    python tools/render_spec_html.py

The Markdown is the source of truth; never hand-edit the HTML, re-run this instead. Adds a title block, a contents
list, RFC 2119 keyword highlighting, and links from every "decision NNNN" to its record.
"""

import html
import posixpath
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "MeshPRS-Spec.md"
OUT = ROOT / "MeshPRS-Spec.html"

TITLE = "MeshPRS: APRS ↔ MeshCore Interface Standard"
META = [
    ("Document", "MeshPRS 1.0 Candidate"),
    ("Date", "30 October 2026"),
    ("Editor", "Alec Swinton, VK4AZ"),
    ("Frame version", "1 (layout frozen; version 0 accepted until 1.0 final)"),
    ("Identifiers", "MeshCore channel <code>#meshprs</code>, GRP_DATA type <code>0xFF4D</code>, tocall <code>APZKPG</code>"),
    ("Licence", "Text CC BY 4.0; test vectors CC0 1.0"),
]

CSS = """
:root{--bg:#fbfaf7;--paper:#fff;--ink:#1d2228;--muted:#5d6672;--line:#d7d3ca;--soft:#f2efe8;--code:#f4f2ec;--accent:#1f5f8b;--accent-bg:#e7f0f7;--must:#8a2d1f}
@media (prefers-color-scheme:dark){:root{--bg:#14171b;--paper:#1b1f24;--ink:#e4e7eb;--muted:#9aa3ae;--line:#353b43;--soft:#22272d;--code:#20252b;--accent:#7db4de;--accent-bg:#1c2b38;--must:#f08a77}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16.5px/1.6 Georgia,"Iowan Old Style","Palatino Linotype",serif}
main{max-width:920px;margin:0 auto;padding:28px 16px 80px;background:var(--paper);border-left:1px solid var(--line);border-right:1px solid var(--line)}
@media (min-width:960px){main{padding:40px 56px 90px}}
.titleblock{border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:22px}
.series{font:600 .78rem/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font-size:2rem;line-height:1.15;margin:8px 0 12px}
.meta{display:grid;grid-template-columns:max-content 1fr;gap:2px 14px;font:.9rem/1.5 system-ui,sans-serif;margin:0}
.meta dt{color:var(--muted)} .meta dd{margin:0}
.badge{display:inline-block;font:700 .75rem system-ui,sans-serif;letter-spacing:.08em;color:var(--accent);border:1.5px solid var(--accent);padding:1px 8px;border-radius:3px;margin-top:12px}
h2{font-size:1.35rem;margin:42px 0 10px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:1.08rem;margin:26px 0 6px} h4{font:600 .95rem system-ui,sans-serif;margin:18px 0 4px}
p{margin:9px 0} a{color:var(--accent)}
code,pre{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:.86em}
code{background:var(--code);padding:1px 4px;border-radius:3px;overflow-wrap:anywhere}
pre{background:var(--code);border:1px solid var(--line);border-radius:4px;padding:10px 12px;overflow-x:auto;line-height:1.45}
pre code{background:none;padding:0;overflow-wrap:normal}
.kw{font:700 .82em system-ui,sans-serif;letter-spacing:.03em;color:var(--must)}
.tw{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;font:.88rem/1.45 system-ui,sans-serif}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
ul,ol{padding-left:24px;margin:8px 0} li{margin:3px 0}
hr{display:none}
.status{border-left:3px solid var(--accent);background:var(--accent-bg);padding:8px 14px;margin:14px 0;font-size:.95rem}
.toc{columns:2;column-gap:32px;font:.9rem/1.6 system-ui,sans-serif;background:var(--soft);padding:12px 18px;border-radius:4px}
.toc a{text-decoration:none;color:var(--ink)} .toc a:hover{color:var(--accent)}
.toc ol{list-style:none;padding:0;margin:0} .toc li{break-inside:avoid;margin:0}
@media (max-width:640px){.toc{columns:1}}
footer{margin-top:50px;border-top:1px solid var(--line);padding-top:12px;font:.82rem system-ui,sans-serif;color:var(--muted)}
@media print{body{background:#fff;font-size:11pt} main{border:0;max-width:none;padding:0} h2{break-after:avoid} table{break-inside:avoid} a{color:inherit;text-decoration:none}}
"""

LIST = re.compile(r"^( *)([-*]|\d+\.) ")


def prepare(md: str) -> str:
    """Adapt GitHub-style Markdown to Python-Markdown: a blank line before every list, 4-space nesting."""
    out, fence, prev_list = [], False, False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        if fence or line.lstrip().startswith("```"):
            out.append(line); prev_list = False; continue
        m = LIST.match(line)
        if m:
            if out and out[-1].strip() and not LIST.match(out[-1]):
                out.append("")
            line = " " * (len(m.group(1)) // 2 * 4) + line[len(m.group(1)):]
            prev_list = True
        elif prev_list and line.startswith("  ") and line.strip():
            line = "    " + line.lstrip()            # continuation of a list item
        else:
            prev_list = prev_list and not line.strip()
        out.append(line)
    return "\n".join(out)


def rewrite_links(h: str) -> str:
    def fix(m):
        href = m.group(1)
        if re.match(r"^(https?:|mailto:|#)", href):
            return m.group(0)
        return 'href="%s"' % posixpath.normpath(posixpath.join("spec", href))
    return re.sub(r'href="([^"]+)"', fix, h)


def decorate_text(h: str, records: dict) -> str:
    """RFC 2119 keywords and decision links, in text outside code, pre and links."""
    kw = re.compile(r"\b(MUST NOT|SHOULD NOT|MUST|SHOULD|MAY|REQUIRED|OPTIONAL)\b")
    dec = re.compile(r"\b(decisions?|records?|Decided in) ((?:\d{4})(?:(?:, | and | or )\d{4})*)")

    def link_nums(m):
        nums = re.sub(r"\d{4}", lambda n: '<a href="spec/decisions/%s">%s</a>' % (records[n.group(0)], n.group(0))
                      if n.group(0) in records else n.group(0), m.group(2))
        return "%s %s" % (m.group(1), nums)

    parts, depth = re.split(r"(<[^>]+>)", h), 0
    for i, p in enumerate(parts):
        if p.startswith("<"):
            t = re.match(r"</?(\w+)", p)
            if t and t.group(1) in ("code", "pre", "a"):
                depth += -1 if p.startswith("</") else 1
            continue
        if depth == 0 and p:
            p = kw.sub(r'<span class="kw">\1</span>', p)
            p = dec.sub(link_nums, p)
            parts[i] = p
    h = "".join(parts)
    # the §16.2 table: link the bare record numbers in its first column
    return re.sub(r"<td>(\d{4})</td>", lambda m: '<td><a href="spec/decisions/%s">%s</a></td>' % (records[m.group(1)], m.group(1))
                  if m.group(1) in records else m.group(0), h)


def main():
    records = {p.name[:4]: p.name for p in (ROOT / "spec" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")}
    src = SPEC.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = src.split("\n")
    assert lines[0].startswith("# ")
    body_md = "\n".join(lines[1:])
    # the status paragraph (first non-blank paragraph) goes in its own box
    status, _, rest = body_md.strip().partition("\n\n")
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                           extension_configs={"toc": {"toc_depth": "2-2"}})
    body = md.convert(prepare(rest))
    status_html = markdown.markdown(status)
    toc = "".join('<li><a href="#%s">%s</a></li>' % (t["id"], html.escape(html.unescape(t["name"])))
                  for t in md.toc_tokens)
    body = re.sub(r"<table>", '<div class="tw"><table>', body).replace("</table>", "</table></div>")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MeshPRS 1.0 Candidate</title>
<style>{CSS}</style>
</head>
<body>
<main>
<div class="titleblock">
  <div class="series">Amateur interface standard · 1.0 Candidate · open for comment</div>
  <h1>{html.escape(TITLE)}</h1>
  <dl class="meta">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in META)}</dl>
  <span class="badge">1.0 CANDIDATE · LAYOUT FROZEN · OPEN FOR COMMENT</span>
</div>
<div class="status">{status_html}</div>
<nav class="toc" aria-label="Contents"><ol>{toc}</ol></nav>
{body}
<footer>MeshPRS 1.0 Candidate. Generated from <code>spec/MeshPRS-Spec.md</code>, which is authoritative. Text licensed under
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>; credit "MeshPRS, Alec Swinton VK4AZ". Test vectors are
<a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a>.</footer>
</main>
</body>
</html>
"""
    page = decorate_text(rewrite_links(page), records)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
