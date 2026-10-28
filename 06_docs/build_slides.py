"""Render 06_docs/slide_deck.md into a slide-style self-contained HTML deck.

Each `<!--slide-->` marker starts a new slide card.  Images are inlined as
base64 so the deck is a single portable file; MathJax comes from a CDN.
"""

import base64
import os
import re

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "slide_deck.md")
OUT = os.path.join(HERE, "slide_deck.html")

text = open(SRC, encoding="utf-8").read()
chunks = re.split(r"<!--\s*slide\s*-->", text)


def inline_img(match):
    rel = match.group(1)
    path = os.path.normpath(os.path.join(HERE, rel))
    if not os.path.exists(path):
        return match.group(0)
    data = base64.b64encode(open(path, "rb").read()).decode()
    return 'src="data:image/png;base64,%s"' % data


slides = []
for ch in chunks:
    if not ch.strip():
        continue
    body = markdown.markdown(ch, extensions=["tables", "fenced_code", "attr_list"])
    body = re.sub(r'src="([^"]+\.(?:png|jpg|jpeg))"', inline_img, body)
    slides.append(body)

parts = []
for i, b in enumerate(slides):
    parts.append('<section class="slide" id="s%d">%s</section>' % (i + 1, b))
body = "\n".join(parts)
nav = " ".join('<a href="#s%d">%d</a>' % (i + 1, i + 1) for i in range(len(slides)))

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>让灵巧手走起来 · Slide Deck</title>
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
  :root { --fg:#1a1d23; --muted:#5a6472; --accent:#2563eb; --line:#d8dee9; --bg:#eef1f6; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font-family:-apple-system,"Segoe UI","Noto Sans SC","PingFang SC",
                     "Hiragino Sans GB","Microsoft YaHei",sans-serif;
         line-height:1.7; }
  .toolbar { position:sticky; top:0; z-index:20; background:rgba(255,255,255,.92);
             backdrop-filter:blur(6px); border-bottom:1px solid var(--line);
             padding:8px 20px; display:flex; gap:8px; align-items:center;
             font-size:.9rem; }
  .toolbar b { color:var(--accent); margin-right:6px; }
  .toolbar a { color:var(--muted); text-decoration:none; padding:2px 9px;
               border:1px solid var(--line); border-radius:999px; }
  .toolbar a:hover { background:var(--accent); color:#fff; border-color:var(--accent); }
  .deck { max-width:1080px; margin:0 auto; padding:28px 20px 100px; }
  .slide { background:#fff; border:1px solid var(--line); border-radius:14px;
           padding:40px 46px 48px; margin:0 0 30px;
           box-shadow:0 2px 14px rgba(20,30,50,.06); }
  .slide h1 { font-size:1.9rem; margin:0 0 .1em; letter-spacing:-.01em; }
  .slide h2 { font-size:1.55rem; margin:.1em 0 .5em; color:#0f172a;
              border-bottom:2px solid var(--accent); padding-bottom:.3em; }
  .slide h3 { font-size:1.12rem; margin:1.7em 0 .5em; color:#243b6b;
              border-left:4px solid var(--accent); padding-left:.55em; }
  .slide p, .slide li { font-size:1.02rem; }
  .slide img { max-width:100%; display:block; margin:1em auto;
               border:1px solid var(--line); border-radius:8px; background:#fff; }
  .slide table { border-collapse:collapse; margin:1em 0; width:100%; font-size:.94rem; }
  .slide th, .slide td { border:1px solid var(--line); padding:.5em .7em;
                         text-align:left; vertical-align:top; }
  .slide th { background:#eef2f9; font-weight:600; }
  .slide tr:nth-child(even) td { background:#fafbfd; }
  .slide blockquote { margin:1.1em 0; padding:.7em 1.1em; color:#334155;
                      border-left:4px solid var(--accent); background:#f5f8ff;
                      border-radius:0 8px 8px 0; }
  .slide code { background:#eef2f7; padding:.12em .4em; border-radius:4px;
                font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.88em; }
  .slide pre { background:#0d1117; color:#e6edf3; padding:14px 16px;
               border-radius:8px; overflow-x:auto; font-size:.86rem; }
  .slide pre code { background:none; color:inherit; padding:0; }
  .slide hr { border:0; border-top:1px solid var(--line); margin:2em 0; }
  .slide strong { color:#0b3d91; }
  .slide h1 + h2 { margin-top:.2em; }
  mjx-container { font-size:1.05em !important; }
  @media print {
    body { background:#fff; }
    .toolbar { display:none; }
    .deck { max-width:none; padding:0; }
    .slide { box-shadow:none; border:none; page-break-after:always;
             border-radius:0; margin:0; padding:24px; }
  }
</style>
</head>
<body>
<div class="toolbar"><b>Slide Deck</b>__NAV__</div>
<div class="deck">
__BODY__
</div>
</body></html>
"""

HTML = HTML.replace("__NAV__", nav).replace("__BODY__", body)
open(OUT, "w", encoding="utf-8").write(HTML)
print("wrote", OUT, "%.1f KB, %d slides" % (os.path.getsize(OUT) / 1024, len(slides)))
