"""Alternative carousel styles (manifest key: "style"). The default "orbit" style lives in layouts.py.

cards   : each slide is a paper card on a ground (card theme is the opposite of the slide theme)
spec    : DM Mono spec-sheet / checklist look with ruled rows and gold tick boxes
pano    : one wide image runs across two adjacent slides (artwork mode "pano", with "part" and "parts")

All text is real HTML. Add a style per post with the manifest key "style"; omit it for the orbit default.
Run `python tools/social/social.py pick-style <kind>` to get a suggestion that avoids the last 3 styles used.
"""
from __future__ import annotations

import layouts as L

STYLES = ("orbit", "cards", "spec", "pano", "wireframe", "polaroid", "zoom", "editorial")
GOLD = "#F5C13A"


def _tick(t: dict, done: bool = True, size: int = 64) -> str:
    chk = (f'<path d="M{size*.24:.0f} {size*.54:.0f} L{size*.43:.0f} {size*.72:.0f} L{size*.78:.0f} {size*.3:.0f}" '
           f'fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="square"/>') if done else ""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block">'
            f'<rect x="1.5" y="1.5" width="{size-3}" height="{size-3}" fill="none" stroke="{t["dim"]}" stroke-width="2"/>{chk}</svg>')


def _btn(cta: str, margin_bottom: int) -> str:
    return (f'<div style="position:relative;align-self:flex-start;background:{GOLD};color:#121515;font-size:38px;font-weight:400;'
            f'padding:30px 56px;border-radius:60px;margin-bottom:{margin_bottom}px">{L.esc(cta)}</div>')


def _h(text: str, size: int, lh: float = 1.04) -> str:
    return (f'<h2 style="position:relative;margin:0;font-family:Jost;font-weight:300;font-size:{size}px;line-height:{lh};'
            f'letter-spacing:-.01em">{L.esc(text)}</h2>')


# ---- cards ---------------------------------------------------------------------------------
_ROT = (-1.4, 1.0, -0.7, 1.2, -1.0, 0.8)


def cards(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ct = L.TH["paper" if ctx["theme"] == "night" else "night"]
    rot = _ROT[i % len(_ROT)]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    shadow = "0 22px 44px rgba(0,0,0,.30)" if ctx["theme"] == "night" else "0 18px 40px rgba(12,32,39,.16)"

    def card(inner: str) -> str:
        return (f'<div style="position:relative;flex:1;margin:56px 0 52px;min-height:560px">'
                f'<div style="position:absolute;inset:0;background:{ct["bg"]};opacity:.38;border-radius:4px;'
                f'transform:translate({-14 * (1 if rot > 0 else -1)}px,14px) rotate({-rot * 1.8:.2f}deg)"></div>'
                f'<div style="position:absolute;inset:0;background:{ct["bg"]};color:{ct["fg"]};border-radius:4px;box-shadow:{shadow};'
                f'transform:rotate({rot}deg);padding:72px 72px 64px;box-sizing:border-box;display:flex;flex-direction:column">{inner}</div></div>')
    if L_ == "cover":
        inner = (f'<div style="{L.mono(ct["lab"])}">{L.esc(s.get("label", ""))}</div>'
                 f'<div style="margin-top:28px;width:60px;height:3px;background:{GOLD}"></div>'
                 f'<h1 style="margin:70px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 118)}px;line-height:1.02;'
                 f'letter-spacing:-.015em">{L.esc(s["headline"])}</h1>')
        body = L.topbar(t, "", i, n) + card(inner) + ft("Swipe →")
    elif L_ == "content":
        inner = (f'<h2 style="margin:0;font-family:Jost;font-weight:300;font-size:{s.get("title_size", 104)}px;line-height:1.04;'
                 f'letter-spacing:-.01em">{L.esc(s["title"])}</h2>'
                 f'<div style="margin:44px 0;height:1px;background:{ct["rule"]}"></div>'
                 f'<div style="font-size:44px;line-height:1.38;color:{ct["sub"]}">{L.esc(s["lead"])}</div>')
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = L.topbar(t, label, i, n) + card(inner) + ft("")
    elif L_ == "close":
        inner = (f'<h2 style="margin:0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 100)}px;line-height:1.06;'
                 f'letter-spacing:-.01em">{L.esc(s["headline"])}</h2><div style="flex:1"></div>'
                 f'<div style="align-self:flex-start;background:{GOLD};color:#121515;font-size:38px;font-weight:400;padding:30px 56px;'
                 f'border-radius:60px">{L.esc(s.get("cta", "Message us to begin"))}</div>')
        body = L.topbar(t, s.get("label", ""), i, n) + card(inner) + ft("Above the ordinary.")
    else:
        raise L.RenderError(f"style cards: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- spec ----------------------------------------------------------------------------------
def _rows(t: dict, k: int, done: bool) -> str:
    return "".join(f'<div style="position:relative;display:flex;align-items:center;justify-content:space-between;'
                   f'border-top:1px solid {t["rule"]};height:104px"><div style="width:520px;height:10px;background:{t["rule"]}"></div>'
                   f'{_tick(t, done, 56)}</div>' for _ in range(k)) + f'<div style="border-top:1px solid {t["rule"]}"></div>'


def spec(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    if L_ == "cover":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 124)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{L.esc(s["headline"])}</h1>'
                + '<div style="flex:1"></div>' + f'<div style="position:relative;margin-bottom:48px">{_rows(t, ctx["n_content"], False)}</div>'
                + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n)
                + f'<div style="position:relative;margin-top:84px;border-top:1px solid {t["rule"]};display:flex;align-items:center;'
                  f'justify-content:space-between;padding:26px 0"><div style="{L.mono(t["lab"])}">Check</div>{_tick(t, True)}</div>'
                  f'<div style="position:relative;border-top:1px solid {t["rule"]};padding:52px 0">{_h(s["title"], s.get("title_size", 108))}</div>'
                  f'<div style="position:relative;border-top:1px solid {t["rule"]};border-bottom:1px solid {t["rule"]};padding:44px 0">'
                  f'<div style="width:860px;font-size:44px;line-height:1.38;color:{t["sub"]}">{L.esc(s["lead"])}</div></div>'
                + '<div style="flex:1"></div>' + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:90px">{_h(s["headline"], s.get("headline_size", 100), 1.06)}</div>'
                + '<div style="flex:1"></div>' + f'<div style="position:relative;margin-bottom:48px">{_rows(t, ctx["n_content"], True)}</div>'
                + _btn(s.get("cta", "Message us to begin"), 56) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style spec: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- pano ----------------------------------------------------------------------------------
BAND_H = 560


def _band(s: dict, ctx: dict, t: dict) -> str:
    a = s.get("artwork")
    if not a or not ctx.get("art_url"):
        return f'<div style="flex:1"></div>'
    parts, part = int(a.get("parts", 2)), int(a.get("part", 0))
    W = ctx["W"]
    return (f'<div style="position:relative;margin:auto -88px 44px;height:{BAND_H}px;overflow:hidden">'
            f'<img data-art="1" src="{ctx["art_url"]}" style="position:absolute;left:{-part * W}px;top:0;width:{parts * W}px;'
            f'height:{BAND_H}px;object-fit:cover;object-position:{a.get("focus", "50% 50%")};display:block"></div>')


def pano(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    band = _band(s, ctx, t)
    if L_ == "cover":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 124)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{L.esc(s["headline"])}</h1>' + band + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n)
                + f'<div style="position:relative;margin-top:84px">{_h(s["title"], s.get("title_size", 104))}'
                  f'<div style="margin-top:36px;width:860px;font-size:44px;line-height:1.35;color:{t["sub"]}">{L.esc(s["lead"])}</div></div>'
                + band + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:110px">{_h(s["headline"], s.get("headline_size", 104), 1.06)}</div>'
                + band + ('<div style="flex:1"></div>' if not s.get("artwork") else "")
                + _btn(s.get("cta", "Message us to begin"), 56) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style pano: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- wireframe -----------------------------------------------------------------------------
_WF = {  # name: (x, y, w, h)
    "phone": (40, 84, 824, 72), "form": (40, 176, 520, 250), "hours": (584, 176, 280, 160), "note": (584, 356, 280, 70)}


def _wire_svg(t: dict, hl: str | None, all_hl: bool = False) -> str:
    dim = t["dim"]

    def box(name):
        x, y, w, h = _WF[name]
        on = all_hl or hl == name
        st = (f'stroke="{GOLD}" stroke-width="4" fill="{GOLD}" fill-opacity=".08"' if on
              else f'stroke="{dim}" stroke-width="1.5" stroke-opacity=".7" fill="none"')
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" {st}/>'

    def bar(x, y, w):
        return f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="5" fill="{dim}" fill-opacity=".35"/>'
    form_on = all_hl or hl == "form"
    inner = (box("phone") + f'<circle cx="84" cy="120" r="16" fill="none" stroke="{dim}" stroke-width="1.5"/>' + bar(124, 115, 300)
             + box("form")
             + f'<rect x="64" y="204" width="472" height="44" rx="3" fill="none" stroke="{dim}" stroke-opacity=".6" stroke-width="1.5"/>'
             + f'<rect x="64" y="264" width="472" height="88" rx="3" fill="none" stroke="{dim}" stroke-opacity=".6" stroke-width="1.5"/>'
             + f'<rect x="64" y="372" width="170" height="40" rx="20" fill="{GOLD if form_on else dim}" fill-opacity="{1 if form_on else .35}"/>'
             + box("hours") + bar(608, 204, 200) + bar(608, 232, 160) + bar(608, 260, 220) + bar(608, 288, 120)
             + box("note") + bar(608, 376, 220) + bar(608, 400, 140))
    return (f'<svg width="904" height="470" viewBox="0 0 904 520" preserveAspectRatio="xMinYMin meet" style="display:block">'
            f'<rect x="1" y="1" width="902" height="518" rx="8" fill="none" stroke="{dim}" stroke-width="2"/>'
            f'<line x1="1" y1="56" x2="903" y2="56" stroke="{dim}" stroke-width="1.5" stroke-opacity=".7"/>'
            + "".join(f'<circle cx="{28 + 24 * k}" cy="28" r="6" fill="none" stroke="{dim}" stroke-width="1.5"/>' for k in range(3))
            + f'<rect x="110" y="14" width="420" height="28" rx="14" fill="none" stroke="{dim}" stroke-width="1.5" stroke-opacity=".7"/>'
            + inner + f'<line x1="40" y1="470" x2="864" y2="470" stroke="{dim}" stroke-width="1.5" stroke-opacity=".5"/></svg>')


def wireframe(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    wf = f'<div style="position:relative;margin-bottom:36px">{_wire_svg(t, s.get("wire"))}</div>'
    if L_ == "cover":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<h1 style="position:relative;margin:90px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 118)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{L.esc(s["headline"])}</h1><div style="flex:1"></div>' + wf + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n)
                + f'<div style="position:relative;margin-top:56px">{_h(s["title"], s.get("title_size", 96))}'
                  f'<div style="margin-top:28px;width:860px;font-size:42px;line-height:1.35;color:{t["sub"]}">{L.esc(s["lead"])}</div></div>'
                + '<div style="flex:1"></div>' + wf + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:90px">{_h(s["headline"], s.get("headline_size", 100), 1.06)}</div>'
                + '<div style="flex:1"></div>' + f'<div style="position:relative;margin-bottom:36px">{_wire_svg(t, None, True)}</div>'
                + _btn(s.get("cta", "Message us to begin"), 40) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style wireframe: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- shared image crop (polaroid, zoom) ----------------------------------------------------
def _crop_img(s: dict, ctx: dict, box_css: str) -> str:
    a = s.get("artwork")
    if not a or not ctx.get("art_url"):
        return f'<div style="{box_css};background:{L.TH[ctx["theme"]]["rule"]}"></div>'
    z, o, f = a.get("zoom", 1), a.get("origin", "50% 50%"), a.get("focus", "50% 50%")
    return (f'<div style="{box_css};overflow:hidden"><img data-art="1" src="{ctx["art_url"]}" style="position:absolute;left:0;top:0;'
            f'width:100%;height:100%;object-fit:cover;object-position:{f};transform:scale({z});transform-origin:{o};display:block"></div>')


# ---- polaroid ------------------------------------------------------------------------------
def polaroid(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    night = ctx["theme"] == "night"
    ct = L.TH["paper"] if night else {"bg": "#FFFFFF", "fg": "#0C2027", "lab": "#3E5257"}
    rot = _ROT[i % len(_ROT)] * 0.9
    shadow = "0 22px 44px rgba(0,0,0,.34)" if night else "0 16px 36px rgba(12,32,39,.18)"

    def frame(caption: str) -> str:
        return (f'<div style="position:relative;align-self:center;width:880px;box-sizing:border-box;background:{ct["bg"]};padding:36px 36px 28px;'
                f'border-radius:3px;box-shadow:{shadow};transform:rotate({rot}deg);margin-top:60px">'
                + _crop_img(s, ctx, "position:relative;width:808px;height:480px")
                + f'<div style="{L.mono(ct["lab"], 24)}padding-top:30px">{L.esc(caption)}</div></div>')
    if L_ == "cover":
        body = (L.topbar(t, "", i, n) + frame(s.get("label", ""))
                + f'<h1 style="position:relative;margin:64px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 110)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{L.esc(s["headline"])}</h1><div style="flex:1"></div>' + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n) + frame(s["title"])
                + f'<div style="position:relative;margin-top:64px;width:860px;font-size:44px;line-height:1.38;color:{t["sub"]}">{L.esc(s["lead"])}</div>'
                + '<div style="flex:1"></div>' + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:110px">{_h(s["headline"], s.get("headline_size", 104), 1.06)}</div>'
                + '<div style="flex:1"></div>' + _btn(s.get("cta", "Message us to begin"), 56) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style polaroid: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- zoom ----------------------------------------------------------------------------------
def zoom(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    band = _crop_img(s, ctx, "position:relative;margin:44px -88px 0;height:620px") if s.get("artwork") else '<div style="flex:1"></div>'
    if L_ == "cover":
        body = (L.topbar(t, s.get("label", ""), i, n) + band
                + f'<h1 style="position:relative;margin:56px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 110)}px;'
                  f'line-height:1.0;letter-spacing:-.015em">{L.esc(s["headline"])}</h1><div style="flex:1"></div>' + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n) + band
                + f'<div style="position:relative;margin-top:48px">{_h(s["title"], s.get("title_size", 92))}'
                  f'<div style="margin-top:24px;width:860px;font-size:42px;line-height:1.35;color:{t["sub"]}">{L.esc(s["lead"])}</div></div>'
                + '<div style="flex:1"></div>' + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<div style="position:relative;margin-top:110px">{_h(s["headline"], s.get("headline_size", 104), 1.06)}</div>'
                + '<div style="flex:1"></div>' + _btn(s.get("cta", "Message us to begin"), 56) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style zoom: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


# ---- editorial -----------------------------------------------------------------------------
def _hl(text: str, sub: str | None) -> str:
    if not sub or sub not in text:
        return L.esc(text)
    a, b = text.split(sub, 1)
    return (L.esc(a) + f'<span style="text-decoration:underline;text-decoration-color:{GOLD};text-decoration-thickness:6px;'
            f'text-underline-offset:14px">{L.esc(sub)}</span>' + L.esc(b))


def editorial(s: dict, ctx: dict, t: dict) -> str:
    W, H, story, i, n = ctx["W"], ctx["H"], ctx["story"], ctx["i"], ctx["n"]
    L_ = s["layout"]
    ft = lambda r: L.foot(t, r, ctx["logo_url"])  # noqa: E731
    if L_ == "cover":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<h1 style="position:relative;margin:110px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 138)}px;'
                  f'line-height:1.0;letter-spacing:-.02em">{_hl(s["headline"], s.get("hl"))}</h1><div style="flex:1"></div>'
                + f'<div style="position:relative;border-top:1px solid {t["rule"]};margin-bottom:36px"></div>' + ft("Swipe →"))
    elif L_ == "content":
        label = s.get("label") or f'{ctx["num"]} / {ctx["n_content"]:02d}'
        body = (L.topbar(t, label, i, n)
                + f'<h2 style="position:relative;margin:250px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("title_size", 132)}px;'
                  f'line-height:1.02;letter-spacing:-.02em">{_hl(s["title"], s.get("hl"))}</h2>'
                  f'<div style="position:relative;margin-top:56px;width:560px;border-top:1px solid {t["rule"]};padding-top:34px;'
                  f'font-size:40px;line-height:1.4;color:{t["sub"]}">{L.esc(s["lead"])}</div><div style="flex:1"></div>' + ft(""))
    elif L_ == "close":
        body = (L.topbar(t, s.get("label", ""), i, n)
                + f'<h2 style="position:relative;margin:110px 0 0;font-family:Jost;font-weight:300;font-size:{s.get("headline_size", 116)}px;'
                  f'line-height:1.04;letter-spacing:-.02em">{_hl(s["headline"], s.get("hl"))}</h2><div style="flex:1"></div>'
                + _btn(s.get("cta", "Message us to begin"), 56) + ft("Above the ordinary."))
    else:
        raise L.RenderError(f"style editorial: layout '{L_}' not supported")
    return L.wrap(t, body, W, H, story)


BUILDERS = {"cards": cards, "spec": spec, "pano": pano, "wireframe": wireframe,
            "polaroid": polaroid, "zoom": zoom, "editorial": editorial}


def build(s: dict, ctx: dict, t: dict) -> str:
    return BUILDERS[ctx["style"]](s, ctx, t)


# ---- style picker --------------------------------------------------------------------------
STYLE_GUIDE = {
    "orbit": "default look; covers, quiet statements, anything",
    "cards": "myth vs fact, Q&A, two-sided posts (alternate Night/Paper per slide)",
    "spec": "checklists, audits, 'check these' posts",
    "pano": "before/after and journeys (one 1536x1024 image runs across two slides)",
    "wireframe": "website layout explainers (set slide key 'wire': phone|form|hours|note, or edit _WF)",
    "polaroid": "examples, before/after photos, build in public (needs 1-2 photos)",
    "zoom": "one rich scene explored detail by detail (needs 1 photo, crops via zoom/origin)",
    "editorial": "bold statements and myths; use slide key 'hl' to underline the key words",
}
KIND_FIT = {
    "myth-vs-fact": ["cards", "editorial"],
    "checklist": ["spec", "wireframe"],
    "before-after": ["pano", "polaroid"],
    "explainer": ["wireframe", "zoom", "orbit"],
    "process": ["spec", "wireframe", "orbit"],
    "example": ["polaroid", "zoom", "pano"],
    "statement": ["editorial", "orbit"],
    "build-in-public": ["polaroid", "zoom", "orbit"],
    "stat": ["editorial", "orbit"],
}


def recent_styles(content_dir, n: int = 3) -> list[str]:
    """Styles of the n most recently edited real posts (folders starting with '_' or 'style-sample' are ignored)."""
    import json as _json
    rows = []
    for mf in content_dir.glob("*/manifest.json"):
        name = mf.parent.name
        if name.startswith("_") or name.startswith("style-sample") or name.startswith("sample"):
            continue
        try:
            rows.append((mf.stat().st_mtime, _json.loads(mf.read_text(encoding="utf-8")).get("style", "orbit")))
        except ValueError:
            continue
    rows.sort(reverse=True)
    return [st for _, st in rows[:n]]


def pick_style(kind: str, content_dir) -> tuple[list[str], list[str]]:
    """-> (ranked candidates not used in the last 3 posts, the recent styles). Never repeats the most recent style."""
    recent = recent_styles(content_dir)
    fit = KIND_FIT[kind]
    fresh = [x for x in fit if x not in recent]
    rest = [x for x in fit if x in recent and x != (recent[0] if recent else None)]
    return fresh + rest, recent
