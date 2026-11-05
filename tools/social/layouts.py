"""AERELO slide layouts + HTML->PNG renderer (Playwright / headless Chrome).

Reuses the palette, mono-label and dot helpers from templates/static/carousel_single_generator.py
so posts stay on-brand when that file changes. Layout geometry (continuous orbit line, gold rule,
footer lockup) mirrors that file exactly for portrait posts (see tests).

Text is real HTML/CSS (editable). Generated artwork is only ever an <img> with object-fit
cover/contain - it is never stretched.
"""
from __future__ import annotations

import html as _html
import importlib.util
import math
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent

# ---- reuse the existing static generator (palette + helpers) ------------------------------
_spec = importlib.util.spec_from_file_location("aerelo_static_gen", REPO / "templates/static/carousel_single_generator.py")
GEN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GEN)          # __main__ block in that file is guarded; import is side-effect free
TH = GEN.TH
mono = GEN.mono
dots = GEN.dots

FORMATS = {"portrait": (1080, 1350), "square": (1080, 1080), "story": (1080, 1920)}
LAYOUTS = ("cover", "content", "stat", "close", "single")
THEMES = tuple(TH)                      # night, paper
FONT_DIR = TOOLS / "node_modules" / "@fontsource"
FONT_FILES = [
    ("Jost", 300, "jost/files/jost-latin-300-normal.woff2"),
    ("Outfit", 300, "outfit/files/outfit-latin-300-normal.woff2"),
    ("Outfit", 400, "outfit/files/outfit-latin-400-normal.woff2"),
    ("DM Mono", 400, "dm-mono/files/dm-mono-latin-400-normal.woff2"),
]
LOGO_DIR = REPO / "brand" / "logo"
LOGO_FILES = {"night": "aerelo-mark-small-light.svg", "paper": "aerelo-mark-small-ink.svg"}
MARGIN_X = 84                           # templates/README.md: 84px text margin


class RenderError(Exception):
    pass


# ---- paths --------------------------------------------------------------------------------
def rel_url(target: Path, from_dir: Path) -> str:
    return Path(os.path.relpath(Path(target).resolve(), Path(from_dir).resolve())).as_posix()


def font_css(from_dir: Path) -> str:
    missing = [f for _, _, f in FONT_FILES if not (FONT_DIR / f).is_file()]
    if missing:
        raise RenderError("Brand fonts not installed. Run:  cd tools/social && npm install   (missing: "
                          + ", ".join(Path(m).name for m in missing) + ")")
    return "".join(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('{rel_url(FONT_DIR / f, from_dir)}')}}"
                   for fam, w, f in FONT_FILES)


def resolve_logos(allow_placeholder: bool, placeholder_dir: Path) -> tuple[dict, bool, list]:
    """Return ({theme: path}, is_placeholder, missing_official_files)."""
    missing = [n for n in LOGO_FILES.values() if not (LOGO_DIR / n).is_file()]
    if not missing:
        return {t: LOGO_DIR / n for t, n in LOGO_FILES.items()}, False, []
    if not allow_placeholder:
        raise RenderError("Official logo files are missing from brand/logo/: " + ", ".join(missing)
                          + ". Add the supplied AERELO logo SVGs (never recreate the logo), or render with "
                          "--placeholders for a layout-only test.")
    placeholder_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for theme, name in LOGO_FILES.items():
        col = "#F4F9F9" if theme == "night" else "#0C2027"
        p = placeholder_dir / name.replace(".svg", "-PLACEHOLDER.svg")
        p.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
            f'<circle cx="32" cy="32" r="22" fill="none" stroke="{col}" stroke-width="2" stroke-dasharray="4 3"/>'
            f'<text x="32" y="36" text-anchor="middle" font-family="monospace" font-size="9" fill="{col}">LOGO</text>'
            f'<circle cx="50" cy="16" r="5" fill="#F5C13A"/></svg>')
        out[theme] = p
    return out, True, missing


def make_placeholder_image(path: Path, w: int, h: int, label: str) -> None:
    """Obviously-fake artwork stand-in. Lives in assets/placeholders/, never in assets/originals/."""
    img = Image.new("RGB", (w, h), "#1b2424")
    d = ImageDraw.Draw(img)
    for x in range(-h, w, 48):
        d.line([(x, h), (x + h, 0)], fill="#263232", width=2)
    d.rectangle([0, 0, w - 1, h - 1], outline="#F5C13A", width=4)
    try:
        f = ImageFont.load_default(size=max(18, w // 24))
    except TypeError:
        f = ImageFont.load_default()
    d.text((w // 2, int(h * 0.84)), f"PLACEHOLDER\n{label}\n{w}x{h}", fill="#F4F9F9", font=f, anchor="mm", align="center")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


# ---- building blocks (portrait output identical to the existing generator) -----------------
def esc(s: str) -> str:
    return _html.escape(str(s)).replace("\n", "<br>")


def ring_svg(i: int, n: int, t: dict, W: int, H: int, dotx: int | None = None) -> str:
    k, TW = H / 1350, W * n

    def y(x):
        u = min(max(x / TW, 0), 1)
        return k * (1130 - 420 * u - 60 * math.sin(math.pi * u))
    pts = " L".join(f"{lx},{y(i * W + lx):.1f}" for lx in range(-40, W + 41, 20))
    dl = (900 - 130 * i if i < 6 else 160) if dotx is None else dotx
    dy = y(i * W + dl)
    return (f'<svg style="position:absolute;left:0;top:0" width="{W}" height="{H}"><path d="M{pts}" fill="none" '
            f'stroke="{t["ring"]}" stroke-opacity="{t["ro"]}" stroke-width="2"/><circle cx="{dl}" cy="{dy:.1f}" r="26" '
            f'fill="#F5C13A" fill-opacity=".25"/><circle cx="{dl}" cy="{dy:.1f}" r="13" fill="#F5C13A"/></svg>')


def ring_single(t: dict, W: int, H: int) -> str:
    k = H / 1350
    pts = " L".join(f"{x},{k * (940 - 170 * ((x + 40) / 1160) - 36 * math.sin(math.pi * (x + 40) / 1160)):.1f}"
                    for x in range(-40, W + 41, 20))
    dy = k * (940 - 170 * (900 / 1160) - 36 * math.sin(math.pi * 900 / 1160))
    return (f'<svg style="position:absolute;left:0;top:0" width="{W}" height="{H}"><path d="M{pts}" fill="none" '
            f'stroke="{t["ring"]}" stroke-opacity=".28" stroke-width="2"/><circle cx="860" cy="{dy:.1f}" r="26" '
            f'fill="#F5C13A" fill-opacity=".25"/><circle cx="860" cy="{dy:.1f}" r="13" fill="#F5C13A"/></svg>')


def topbar(t: dict, label: str, i: int | None = None, n: int | None = None) -> str:
    d = dots(i, n, t) if n else ""
    return (f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between">'
            f'<div style="{mono(t["lab"])}">{esc(label)}</div>{d}</div>'
            f'<div style="position:relative;margin-top:28px;width:60px;height:3px;background:#F5C13A"></div>')


def foot(t: dict, right: str, logo_url: str) -> str:
    return (f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between">'
            f'<div style="display:flex;align-items:center;gap:20px"><img src="{logo_url}" style="height:64px;display:block">'
            f'<div style="font-family:Outfit;font-weight:300;font-size:30px;letter-spacing:.3em;text-transform:uppercase;'
            f'color:{t["fg"]}">Aerelo</div></div><div style="{mono(t["lab"], 22)}">{esc(right)}</div></div>')


def wrap(t: dict, inner: str, W: int, H: int, story: bool) -> str:
    pad = "250px 88px 340px 88px" if story else "96px 88px 80px 88px"
    return (f'<div style="width:{W}px;height:{H}px;box-sizing:border-box;padding:{pad};background:{t["bg"]};'
            f'color:{t["fg"]};font-family:Outfit,sans-serif;display:flex;flex-direction:column;position:relative;'
            f'overflow:hidden">{inner}</div>')


def _img_style(fit: str, focus: str) -> str:
    return (f"position:absolute;left:0;top:0;width:100%;height:100%;object-fit:{fit};"
            f"object-position:{focus};display:block")


def artwork_parts(s: dict, t: dict, art_url: str | None) -> tuple[str, str]:
    """-> (behind_html, spacer_html). The spacer is the flexible negative space; a 'panel' fills it."""
    plain = '<div style="flex:1"></div>'
    a = s.get("artwork")
    if not a or not art_url:
        return "", plain
    fit, focus = a.get("fit", "cover"), a.get("focus", "50% 50%")
    if a.get("mode", "full") == "panel":
        return "", (f'<div style="position:relative;flex:1;min-height:180px;margin:48px 0;border-radius:2px;overflow:hidden;'
                    f'border:1px solid {t["rule"]};background:{t["bg"]}"><img data-art="1" src="{art_url}" '
                    f'style="{_img_style(fit, focus)}"></div>')
    bg = (18, 21, 21) if t is TH["night"] else (247, 245, 240)
    ov = float(a.get("overlay", 0.6))
    return (f'<img data-art="1" src="{art_url}" style="{_img_style(fit, focus)}">'
            f'<div style="position:absolute;inset:0;background:rgba({bg[0]},{bg[1]},{bg[2]},{ov})"></div>'), plain


# ---- layouts -----------------------------------------------------------------------------
def build_slide(s: dict, ctx: dict) -> str:
    """ctx: theme, i, n, n_content, num, W, H, story, logo_url, art_url"""
    t = TH[ctx["theme"]]
    W, H, story = ctx["W"], ctx["H"], ctx["story"]
    i, n = ctx["i"], ctx["n"]
    behind, spacer = artwork_parts(s, t, ctx.get("art_url"))
    L = s["layout"]
    ft = lambda default: foot(t, s.get("footer", default), ctx["logo_url"])  # noqa: E731
    sub_css = f'color:{t["sub"]}'
    if L == "cover":
        body = (ring_svg(i, n, t, W, H) + topbar(t, s.get("label", ""), i, n)
                + f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 128)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{esc(s["headline"])}</h1>'
                + (f'<div style="position:relative;margin-top:36px;width:820px;font-size:38px;line-height:1.35;{sub_css}">{esc(s["sub"])}</div>'
                   if s.get("sub") else "")
                + spacer + ft("Swipe →"))
    elif L == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (ring_svg(i, n, t, W, H) + topbar(t, label, i, n)
                + f'<div style="position:relative;margin-top:110px;{mono(t["num"], 30)}">{ctx["num"]}</div>'
                  f'<h2 style="position:relative;margin:24px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("title_size", 118)}px;'
                  f'line-height:1.04;letter-spacing:-.01em">{esc(s["title"])}</h2>'
                  f'<div style="position:relative;margin-top:56px;width:860px;font-size:44px;line-height:1.35;{sub_css}">{esc(s["lead"])}</div>'
                + spacer + ft(""))
    elif L == "stat":
        body = (ring_svg(i, n, t, W, H) + topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:90px;font-family:Jost;font-weight:300;font-size:{s.get("stat_size", 300)}px;'
                  f'line-height:1;color:{t["num"]}">{esc(s["stat"])}</div>'
                  f'<div style="position:relative;margin-top:36px;width:860px;font-size:44px;line-height:1.35;{sub_css}">{esc(s["caption"])}</div>'
                + (f'<div style="position:relative;margin-top:32px;{mono(t["dim"], 22)}">{esc(s["source"])}</div>' if s.get("source") else "")
                + spacer + ft(""))
    elif L == "close":
        body = (ring_svg(i, n, t, W, H) + topbar(t, s.get("label", "Next"), i, n)
                + f'<h2 style="position:relative;margin:110px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 104)}px;'
                  f'line-height:1.06;letter-spacing:-.01em">{esc(s["headline"])}</h2>'
                + (f'<div style="position:relative;margin-top:36px;width:820px;font-size:38px;line-height:1.35;{sub_css}">{esc(s["sub"])}</div>'
                   if s.get("sub") else "")
                + spacer
                + f'<div style="position:relative;align-self:flex-start;background:#F5C13A;color:#121515;font-size:38px;font-weight:400;'
                  f'padding:30px 56px;border-radius:60px;margin-bottom:{40 if story else 80}px">{esc(s.get("cta", "Message us to begin"))}</div>'
                + ft("Above the ordinary."))
    elif L == "single":
        body = (ring_single(t, W, H) + topbar(t, s.get("label", ""))
                + f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 150)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{esc(s["headline"])}</h1>'
                + spacer
                + f'<div style="position:relative;width:820px;font-size:38px;line-height:1.35;{sub_css};margin-bottom:96px">{esc(s.get("sub", ""))}</div>'
                + ft("Above the ordinary."))
    else:
        raise RenderError(f"unknown layout '{L}'")
    return wrap(t, behind + body, W, H, story)


def page_html(body: str, W: int, H: int, fonts: str, title: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{_html.escape(title)}</title>"
            f"<style>{fonts}body{{margin:0;width:{W}px;height:{H}px;background:#000}}</style></head><body>{body}</body></html>")


# ---- QA run inside the page -----------------------------------------------------------------
QA_JS = """
async (cfg) => {
  await document.fonts.ready;
  const issues = [];
  const add = (level, kind, msg) => issues.push({level, kind, msg});
  const loaded = [...document.fonts].filter(f => f.status === 'loaded')
      .map(f => f.family.replace(/["']/g, '') + '|' + f.weight);
  const texts = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const used = new Set();
  while (tw.nextNode()) {
    const nd = tw.currentNode;
    if (!nd.nodeValue.trim()) continue;
    const el = nd.parentElement, cs = getComputedStyle(el);
    used.add(cs.fontFamily.split(',')[0].replace(/["']/g, '').trim() + '|' + cs.fontWeight);
    const r = document.createRange(); r.selectNodeContents(nd);
    const b = r.getBoundingClientRect();
    // line boxes (height = line-height, not the font's taller content area) for the overlap test
    const lh = parseFloat(cs.lineHeight);
    const lines = [...r.getClientRects()].map(q => {
      const c = (q.top + q.bottom) / 2, h = isNaN(lh) ? q.height : Math.min(lh, q.height);
      return {l: q.left, r: q.right, tp: c - h / 2, bt: c + h / 2};
    });
    texts.push({t: nd.nodeValue.trim().slice(0, 40), l: b.left, r: b.right, tp: b.top, bt: b.bottom, lines, el});
  }
  for (const u of used) if (!loaded.includes(u)) add('error', 'font', 'font not loaded: ' + u);
  for (const x of texts) {
    if (x.l < cfg.mx - 1 || x.r > cfg.W - cfg.mx + 1) add('error', 'margin', `"${x.t}" outside ${cfg.mx}px side margins (${x.l.toFixed(0)}..${x.r.toFixed(0)})`);
    if (x.tp < cfg.top - 1 || x.bt > cfg.H - cfg.bottom + 1) add('error', 'safe-zone', `"${x.t}" outside vertical safe zone (${x.tp.toFixed(0)}..${x.bt.toFixed(0)})`);
    const e = x.el;
    if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).display !== 'inline') add('error', 'overflow', `"${x.t}" overflows its box`);
  }
  for (let a = 0; a < texts.length; a++) for (let b = a + 1; b < texts.length; b++) {
    const p = texts[a], q = texts[b];
    let hit = false;
    for (const u of p.lines) for (const v of q.lines) {
      const w = Math.min(u.r, v.r) - Math.max(u.l, v.l), h = Math.min(u.bt, v.bt) - Math.max(u.tp, v.tp);
      if (w > 2 && h > 2) hit = true;
    }
    if (hit) add('error', 'overlap', `"${p.t}" overlaps "${q.t}"`);
  }
  for (const im of document.images) {
    const name = (im.getAttribute('src') || '').split('/').pop();
    if (!im.complete || im.naturalWidth === 0) { add('error', 'image', 'image failed to load: ' + name); continue; }
    if (im.dataset.art) {
      const of = getComputedStyle(im).objectFit;
      if (of !== 'cover' && of !== 'contain') add('error', 'distortion', `artwork ${name} uses object-fit:${of} (would stretch)`);
    } else {
      const r = im.getBoundingClientRect();
      if (Math.abs(r.width / r.height - im.naturalWidth / im.naturalHeight) > 0.02) add('error', 'distortion', `${name} aspect ratio changed`);
    }
  }
  return {issues, textCount: texts.length};
}
"""


def find_chrome() -> str | None:
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).exists():
        return env
    for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        for rel in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
            if base and (Path(base) / rel).exists():
                return str(Path(base) / rel)
    return None                      # falls back to Playwright's bundled Chromium (python -m playwright install chromium)


def render_pages(pages: list[tuple[Path, str]], out_paths: list[Path], W: int, H: int, story: bool) -> list[dict]:
    """pages: [(html_file, name)] already written to disk. Returns per-slide QA dicts."""
    from playwright.sync_api import sync_playwright
    cfg = {"W": W, "H": H, "mx": MARGIN_X, "top": 250 if story else 60, "bottom": 340 if story else 60}
    reports = []
    with sync_playwright() as p:
        kw = {"args": ["--no-sandbox", "--allow-file-access-from-files"]}
        chrome = find_chrome()
        if chrome:
            kw["executable_path"] = chrome
        browser = p.chromium.launch(**kw)
        pg = browser.new_page(viewport={"width": W, "height": H})
        for (hf, name), out in zip(pages, out_paths):
            pg.goto("file://" + str(Path(hf).resolve()))
            pg.wait_for_load_state("load")
            res = pg.evaluate(QA_JS, cfg)
            out.parent.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(out))
            issues = list(res["issues"])
            with Image.open(out) as im:
                if im.size != (W, H):
                    issues.append({"level": "error", "kind": "dimensions", "msg": f"exported {im.size}, expected {(W, H)}"})
            reports.append({"slide": name, "file": str(out), "issues": issues})
        browser.close()
    return reports


def make_contact_sheet(pngs: list[Path], out: Path, note: str = "", thumb_w: int = 270, cols: int = 6,
                       labels: list[str] | None = None) -> None:
    """Thumbnails in slide order, numbered. Aspect ratio preserved."""
    ims = [Image.open(p).convert("RGB") for p in pngs]
    th = [im.resize((thumb_w, round(im.height * thumb_w / im.width)), Image.LANCZOS) for im in ims]
    cols = min(cols, len(th))
    rows = -(-len(th) // cols)
    gap, lab = 24, 40
    cell_h = max(t.height for t in th) + lab
    top = 56 if note else 24
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * gap, rows * cell_h + (rows + 1) * gap + top), "#0b0d0d")
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.load_default(size=22)
    except TypeError:
        f = ImageFont.load_default()
    if note:
        d.text((gap, 18), note, fill="#F5C13A", font=f)
    for k, t in enumerate(th):
        r, c = divmod(k, cols)
        x, y = gap + c * (thumb_w + gap), top + gap + r * (cell_h + gap)
        sheet.paste(t, (x, y + lab))
        d.text((x, y + 6), labels[k] if labels else f"{k + 1:02d}", fill="#F4F9F9", font=f)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
