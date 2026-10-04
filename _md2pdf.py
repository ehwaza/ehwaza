# -*- coding: utf-8 -*-
"""MD -> HTML stylé (autoportant), puis Brave headless le rend en PDF."""
from pathlib import Path
import markdown

md = Path(r"F:\becvide\RAPPORT_TEST_DE_VIE.md").read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
html = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<style>
@page { size: A4; margin: 16mm 15mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 11pt; color:#1a1a1a; line-height:1.5; }
h1 { font-size: 21pt; border-bottom:3px solid #333; padding-bottom:6px; margin-bottom:4px; }
h2 { font-size: 15pt; margin-top:24px; border-bottom:1px solid #ccc; padding-bottom:3px; }
h3 { font-size: 12.5pt; margin-top:16px; }
code { background:#f2f2f2; padding:1px 4px; border-radius:3px; font-family: Consolas, monospace; font-size:10pt; }
table { border-collapse: collapse; width:100%; margin:10px 0; font-size:10pt; }
th, td { border:1px solid #bbb; padding:4px 8px; text-align:left; vertical-align:top; }
th { background:#ececec; }
hr { border:none; border-top:1px solid #ddd; margin:20px 0; }
strong { color:#000; }
</style></head><body>
""" + body + "\n</body></html>"
Path(r"F:\becvide\rapport.html").write_text(html, encoding="utf-8")
print("html ok ->", len(html), "octets")
