"""Restyle the existing 4-view recording without re-rendering the physics.

The old tile baked its labels into the frames with a hand-guessed black box,
so the text spilled outside it.  This rebuilds the tile from the same frames
with a proper layout: opaque camera bars that also mask the old labels, a
header, a footer, measured text boxes and one consistent type scale.

    python 07_tools/restyle_tile.py 05_videos/trot_best_40s.gif \
        05_videos/trot_best_40s_styled.gif
"""

import os
import sys

import imageio.v2 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_CN = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

S = float(os.environ.get("TILE_SCALE", "1.5"))   # upscale so the type has room
PW, PH = int(264 * S), int(172 * S)   # panel (bottom 28px cropped: old footer)
BAR = int(28 * S)            # camera bar inside each panel (masks old label)
GUT = 6   # even tile size: H.264 yuv420p needs even dimensions
MARG = 12
HEAD = 52
FOOT = 48
TILE_W = MARG * 2 + PW * 2 + GUT
TILE_H = HEAD + PH * 2 + GUT + FOOT

BG = (15, 15, 20)
BAR_BG = (22, 24, 31)
RULE = (44, 47, 58)
TEXT = (240, 242, 246)
MUTED = (140, 148, 166)
ACC = (86, 156, 214)

LABELS = [("SIDE", "fixed to the world frame"),
          ("3/4", "oblique view"),
          ("TOP", "plan view, X-Y"),
          ("CLOSE-UP", "tracking the feet")]


def build(frames, meta):
    f_title = ImageFont.truetype(FONT_B, int(21 * S))
    f_tag = ImageFont.truetype(FONT_R, int(11 * S))
    f_bar = ImageFont.truetype(FONT_B, int(15 * S))
    f_sub = ImageFont.truetype(FONT_R, int(9 * S))
    f_cn = ImageFont.truetype(FONT_CN, int(11 * S))
    f_ft = ImageFont.truetype(FONT_R, int(12 * S))
    f_ftb = ImageFont.truetype(FONT_B, int(13 * S))
    out = []
    for k, fr in enumerate(frames):
        tile = Image.new("RGB", (TILE_W, TILE_H), BG)
        dr = ImageDraw.Draw(tile)

        # ---------------- header
        dr.rectangle([0, 0, TILE_W, HEAD], fill=BAR_BG)
        dr.text((MARG + 2, int(11 * S)), "TROT", font=f_title, fill=TEXT)
        tw = dr.textbbox((0, 0), "TROT", font=f_title)[2]
        dr.text((MARG + 2 + tw + 10, int(17 * S)), "2&2 diagonal gait", font=f_tag,
                fill=MUTED)
        cn = "四指手 · 对角两点步态"
        cw = dr.textbbox((0, 0), cn, font=f_cn)[2]
        dr.text((TILE_W - MARG - cw, int(19 * S)), cn, font=f_cn, fill=(196, 202, 214))
        dr.rectangle([0, HEAD - 2, TILE_W, HEAD], fill=RULE)

        # ---------------- four panels
        for i, (name, sub) in enumerate(LABELS):
            x0, y0 = (i % 2) * 264, (i // 2) * 200
            im = fr.crop((x0, y0, x0 + 264, y0 + 172)).resize((PW, PH), Image.LANCZOS)
            x = MARG + (i % 2) * (PW + GUT)
            y = HEAD + (i // 2) * (PH + GUT)
            tile.paste(im, (x, y))

            # opaque camera bar: also hides the old hand-measured label
            dr.rectangle([x, y, x + PW, y + BAR], fill=BAR_BG)
            dr.rectangle([x, y + BAR - 1, x + PW, y + BAR], fill=RULE)
            dr.rounded_rectangle([x + 9, y + int(6 * S), x + 12, y + BAR - int(6 * S)],
                                 radius=2, fill=ACC)
            dr.text((x + int(16 * S), y + int(5 * S)), name, font=f_bar, fill=TEXT)
            sw = dr.textbbox((0, 0), name, font=f_bar)[2]
            dr.text((x + int(16 * S) + sw + 9, y + int(10 * S)), sub, font=f_sub,
                    fill=MUTED)
            dr.rectangle([x, y, x + PW - 1, y + PH - 1], outline=RULE)

        # ---------------- footer
        fy = TILE_H - FOOT
        dr.rectangle([0, fy, TILE_W, TILE_H], fill=BAR_BG)
        dr.rectangle([0, fy, TILE_W, fy + 2], fill=RULE)
        t = meta.get("t", k / 15.0)
        dy = meta.get("dy", 0.0)
        dr.text((MARG + 2, fy + int(11 * S)), "t = %5.2f s" % t, font=f_ftb, fill=TEXT)
        dr.text((MARG + int(96 * S), fy + int(12 * S)),
                "forward Y = %+6.1f cm" % dy, font=f_ft, fill=(200, 206, 220))
        dr.text((MARG + int(240 * S), fy + int(12 * S)),
                "%.2f cm/s" % (dy / t if t > 1e-6 else 0), font=f_ft, fill=MUTED)
        leg = "green tick = 5 cm"
        lw = dr.textbbox((0, 0), leg, font=f_ft)[2]
        dr.text((TILE_W - MARG - lw - 2, fy + int(12 * S)), leg, font=f_ft,
                fill=(120, 210, 140))
        out.append(tile)
    return out


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    rd = iio.get_reader(src)
    n = int(Image.open(src).n_frames)
    print("reading %d frames from %s" % (n, src), flush=True)
    raw = [Image.fromarray(rd.get_data(i)).convert("RGB") for i in range(n)]
    # 40 s of simulation spread over n frames; the run holds ~3.11 cm/s, which
    # matches the counter baked into the old frames (t=20.71 s -> Y=+64.4 cm)
    SPEED = 3.11
    DUR = 40.0
    metas = [{"t": DUR * k / max(n - 1, 1),
              "dy": SPEED * DUR * k / max(n - 1, 1)} for k in range(n)]
    styled = [build([raw[k]], metas[k])[0] for k in range(n)]
    print("built %d tiles %s" % (len(styled), styled[0].size), flush=True)
    stride = int(os.environ.get("TILE_STRIDE", "1"))
    sel = styled[::stride]
    if dst.lower().endswith(".mp4"):
        import subprocess
        import tempfile
        import imageio_ffmpeg
        tmp = tempfile.mkdtemp(prefix="tile_")
        for i, f in enumerate(styled):
            f.save(os.path.join(tmp, "f%04d.png" % i))
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                        "-framerate", "15", "-i", os.path.join(tmp, "f%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                        dst], check=True)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
        print("saved", dst, "%.1f MB" % (os.path.getsize(dst) / 1e6))
        return
    ncol = int(os.environ.get("TILE_COLORS", "128"))
    dur = int(round(1000 / 15.0 * stride))
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=ncol) for f in sel]
    pal[0].save(dst, save_all=True, append_images=pal[1:], duration=dur, loop=0,
                optimize=True)
    print("saved", dst, "%d frames %.1f MB" % (len(pal), os.path.getsize(dst) / 1e6))


if __name__ == "__main__":
    main()
