"""Render 06_docs/dynamics_analysis.md into a self-contained HTML page.

Images are inlined as base64 so the file can be moved anywhere; MathJax is
loaded from a CDN so the equations typeset when the page is opened.
"""

import base64
import os
import re
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = os.path.splitext(sys.argv[1] if len(sys.argv) > 1 else "dynamics_analysis")[0]
SRC = os.path.join(HERE, STEM + ".md")
OUT = os.path.join(HERE, STEM + ".html")

text = open(SRC, encoding="utf-8").read()

body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "attr_list"])


def inline_img(match):
    rel = match.group(1)
    path = os.path.join(HERE, rel)
    if not os.path.exists(path):
        return match.group(0)
    data = base64.b64encode(open(path, "rb").read()).decode()
    return 'src="data:image/png;base64,%s"' % data


body = re.sub(r'src="([^"]+\.png)"', inline_img, body)

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>四指手 · 动力学与稳定性</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>
window.MathJax = {
  tex: {inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true},
  svg: {fontCache: 'global'}
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
<style>
  :root { --fg:#1f2328; --muted:#59636e; --accent:#0969da; --line:#d1d9e0; }
  body { margin:0; background:#f6f8fa; color:var(--fg);
         font-family:-apple-system,"Segoe UI","Noto Sans SC","PingFang SC",
                     "Hiragino Sans GB","Microsoft YaHei",sans-serif;
         line-height:1.75; }
  main { max-width:900px; margin:0 auto; padding:48px 32px 96px;
         background:#fff; box-shadow:0 0 0 1px var(--line); }
  h1 { font-size:2rem; border-bottom:2px solid var(--line); padding-bottom:.4em; }
  h2 { margin-top:2.4em; font-size:1.45rem; border-bottom:1px solid var(--line);
       padding-bottom:.3em; }
  h3 { margin-top:1.8em; font-size:1.15rem; color:#24292f; }
  p, li { font-size:1rem; }
  img { max-width:100%; display:block; margin:1.4em auto;
        border:1px solid var(--line); border-radius:6px; background:#fff; }
  table { border-collapse:collapse; margin:1.2em 0; width:100%; font-size:.94rem; }
  th, td { border:1px solid var(--line); padding:.45em .7em; text-align:left; }
  th { background:#f0f3f6; font-weight:600; }
  tr:nth-child(even) td { background:#fafbfc; }
  blockquote { margin:1.2em 0; padding:.6em 1em; color:var(--muted);
               border-left:3px solid var(--accent); background:#f6f8fa; }
  code { background:#f0f3f6; padding:.15em .4em; border-radius:4px;
         font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.9em; }
  pre { background:#0d1117; color:#e6edf3; padding:14px 16px; border-radius:8px;
        overflow-x:auto; }
  pre code { background:none; color:inherit; padding:0; }
  hr { border:0; border-top:1px solid var(--line); margin:2.4em 0; }
  strong { color:#0a3069; }
</style>
</head>
<body><main>
__BODY__
</main></body></html>
"""

HTML = HTML.replace("__BODY__", body)

open(OUT, "w", encoding="utf-8").write(HTML)
print("wrote", OUT, "%.1f KB" % (os.path.getsize(OUT) / 1024))
