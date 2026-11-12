"""Convert the publications DOCX into data/publications.json.

Usage:
    python tools/import_publications.py "path/to/Collins_CV_Publications.docx"

Standard library only. Each paragraph styled "Heading1" starts a section and
each "Papers" paragraph becomes one entry. Bold/italic runs and hyperlinks
are kept as HTML.
"""
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"


def q(tag, ns=W):
    return f"{{{ns}}}{tag}"


def run_html(r):
    text = "".join(t.text or "" for t in r.iter(q("t")))
    if not text:
        return ""
    out = html.escape(text, quote=False)
    rpr = r.find(q("rPr"))
    if rpr is not None:
        b = rpr.find(q("b"))
        i = rpr.find(q("i"))
        if b is not None and b.get(q("val")) not in ("0", "false"):
            out = f"<strong>{out}</strong>"
        if i is not None and i.get(q("val")) not in ("0", "false"):
            out = f"<em>{out}</em>"
    return out


def para_html(p, rels):
    parts = []
    for child in p:
        if child.tag == q("r"):
            parts.append(run_html(child))
        elif child.tag == q("hyperlink"):
            inner = "".join(run_html(r) for r in child.iter(q("r")))
            url = rels.get(child.get(q("id", R)), "")
            if url.startswith(("http://", "https://")) and inner:
                parts.append(f'<a href="{html.escape(url)}" rel="noopener">{inner}</a>')
            else:
                # Local file or empty target: drop the link and its "(link)" label.
                parts.append("\x00DEAD\x00")
    s = "".join(parts)
    if "\x00DEAD\x00" in s:
        print("WARNING: dropped a non-web link in:", re.sub(r"<[^>]+>", "", s)[:90], "...")
        s = re.sub(r"\s*\(\x00DEAD\x00\)", "", s).replace("\x00DEAD\x00", "")
    s = s.replace("</strong><strong>", "").replace("</em><em>", "")
    return re.sub(r"\s+", " ", s).strip()


def main(path):
    z = zipfile.ZipFile(path)
    rels = {
        r.get("Id"): r.get("Target")
        for r in ET.fromstring(z.read("word/_rels/document.xml.rels")).iter(q("Relationship", PR))
        if r.get("TargetMode") == "External"
    }
    body = ET.fromstring(z.read("word/document.xml")).find(q("body"))
    sections, note = [], ""
    for p in body.iter(q("p")):
        st = p.find(f"{q('pPr')}/{q('pStyle')}")
        style = st.get(q("val")) if st is not None else "Normal"
        text = "".join(t.text or "" for t in p.iter(q("t"))).strip()
        if not text:
            continue
        if style == "Heading1":
            m = re.match(r"(.*?)\s*\((\d+)\)\s*$", text)
            title, count = (m.group(1), int(m.group(2))) if m else (text, None)
            sections.append({"title": title, "declared": count, "items": []})
        elif style == "Papers" and sections:
            sections[-1]["items"].append(para_html(p, rels))
        elif style == "Text1":
            note = text.lstrip("* ").strip()
    for s in sections:
        if s["declared"] is not None and s["declared"] != len(s["items"]):
            print(f"WARNING: {s['title']}: heading says {s['declared']}, found {len(s['items'])}")
        s.pop("declared")
    dead = sum(1 for s in sections for i in s["items"] if "(link)" in i and "<a " not in i)
    if dead:
        print(f"WARNING: {dead} entries show '(link)' without a URL")
    out = Path(__file__).resolve().parent.parent / "data" / "publications.json"
    out.write_text(json.dumps({"note": note, "sections": sections}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out} ({sum(len(s['items']) for s in sections)} entries)")


if __name__ == "__main__":
    main(sys.argv[1])
