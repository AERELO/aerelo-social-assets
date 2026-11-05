#!/usr/bin/env python3
"""AERELO social pipeline: manifest -> (optional paid artwork) -> rendered Instagram slides.

  new       scaffold content/<slug>/ with a starter manifest
  validate  check the manifest (no API, no browser)
  dry-run   validate + list planned image requests (no API)
  generate  PAID: create missing artwork sequentially. Runs on its own inside budget.json caps
            (use --dry to preview only). Cached assets are reused.
  regen     PAID: regenerate ONE asset as a new version (same budget rules)
  review    FREE: contact sheet of the generated originals so they can be inspected before layout
  render    FREE: build editable HTML source + export PNGs + contact sheet (never calls the API)
  status    show asset state, history and estimated spend

Spending is governed by tools/social/budget.json (auto_approve + hard caps per post / per day / per asset).
Set "auto_approve": false there to go back to preview-unless---yes. --override-budget bypasses the caps.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imagegen as ig  # noqa: E402
import layouts as lay  # noqa: E402

REPO = ig.REPO
CONTENT = REPO / "content"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
COPY_FIELDS = ("label", "headline", "sub", "title", "lead", "stat", "caption", "source", "cta", "footer")
REQUIRED = {"cover": ("headline",), "content": ("title", "lead"), "stat": ("stat", "caption"),
            "close": ("headline",), "single": ("headline",)}
SLIDE_KEYS = set(COPY_FIELDS) | {"layout", "theme", "artwork", "headline_size", "title_size", "stat_size", "note"}
ART_KEYS = {"asset", "mode", "focus", "fit", "overlay"}
ASSET_KEYS = {"id", "prompt", "prompt_file", "existing", "model", "quality", "size", "complexity", "output", "note"}
PRICE_RE = re.compile(r"(US\$|J\$|\bJMD\b|\bUSD\b|[$£€]\s?\d|\d\s?(USD|JMD)\b)", re.I)


class UserError(Exception):
    pass


# ---- spend budget ------------------------------------------------------------------------------
BUDGET_FILE = Path(__file__).resolve().parent / "budget.json"
SPEND_LOG = CONTENT / "_spend" / "log.jsonl"          # git-ignored, local running count of requests
DEFAULT_BUDGET = {"auto_approve": True, "max_images_per_post": 6, "max_images_per_day": 20, "max_regens_per_asset": 2}


def load_budget() -> dict:
    b = dict(DEFAULT_BUDGET)
    if BUDGET_FILE.is_file():
        b.update(json.loads(BUDGET_FILE.read_text(encoding="utf-8")))
    return b


def requests_today() -> int:
    import datetime as _dt
    if not SPEND_LOG.is_file():
        return 0
    today = _dt.date.today().isoformat()
    return sum(1 for ln in SPEND_LOG.read_text(encoding="utf-8").splitlines() if ln and json.loads(ln).get("day") == today)


def log_spend(post: Path, asset_id: str) -> None:
    import datetime as _dt
    ig.append_jsonl(SPEND_LOG, {"day": _dt.date.today().isoformat(), "at": ig.now_iso(), "post": post.name, "asset": asset_id})


def post_requests(led: "Ledger") -> int:
    return sum(1 for e in led.data["assets"].values() for h in e["history"] if h.get("status") in ("completed", "unknown"))


def budget_problem(n_new: int, led: "Ledger", regen_of: str | None = None) -> str | None:
    b = load_budget()
    if post_requests(led) + n_new > b["max_images_per_post"]:
        return (f"budget: this post would use {post_requests(led) + n_new} paid images (cap {b['max_images_per_post']} per post). "
                "Raise max_images_per_post in tools/social/budget.json, or pass --override-budget.")
    if requests_today() + n_new > b["max_images_per_day"]:
        return (f"budget: {requests_today()} requests already today + {n_new} would exceed the daily cap of {b['max_images_per_day']}. "
                "Raise max_images_per_day in tools/social/budget.json, or pass --override-budget.")
    if regen_of:
        done = sum(1 for h in led.entry(regen_of)["history"] if h.get("status") == "completed")
        if max(done - 1, 0) >= b["max_regens_per_asset"]:
            return (f"budget: '{regen_of}' was already regenerated {done - 1} time(s) (cap {b['max_regens_per_asset']}). "
                    "Rework the prompt or concept, or pass --override-budget.")
    return None


def should_spend(args) -> bool:
    """Paid requests go ahead when the user passed --yes, or auto_approve is on and --dry was not given."""
    return bool(args.yes) or (load_budget()["auto_approve"] and not args.dry)


def shown(p: Path) -> str:
    """Repo-relative path when possible, else absolute (posts may live outside the repo, e.g. in tests)."""
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)


# ---- manifest ------------------------------------------------------------------------------
def post_dir_for(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir() and (p / "manifest.json").exists():
        return p.resolve()
    if SLUG_RE.match(arg) or arg.startswith("_"):
        return (CONTENT / arg).resolve()
    raise UserError(f"'{arg}' is neither a post slug nor a post directory")


def load_manifest(arg: str) -> tuple[dict, Path]:
    post = post_dir_for(arg)
    mf = post / "manifest.json"
    if not mf.is_file():
        raise UserError(f"{mf} not found")
    try:
        return json.loads(mf.read_text(encoding="utf-8")), post
    except json.JSONDecodeError as e:
        raise UserError(f"manifest.json is not valid JSON: {e}")


def export_size(m: dict) -> tuple[int, int, str]:
    fmt = m.get("format", "portrait")
    ex = m.get("export")
    if ex:
        return int(ex["width"]), int(ex["height"]), fmt
    w, h = lay.FORMATS[fmt]
    return w, h, fmt


def asset_params(m: dict, a: dict) -> dict:
    d = m.get("image_defaults", {})
    return {"model": a.get("model", d.get("model", ig.DEFAULT_MODEL)),
            "quality": a.get("quality", d.get("quality", "high")),
            "size": a.get("size", d.get("size", "1024x1536")),
            "complexity": a.get("complexity", d.get("complexity")),
            "allow_custom": bool(d.get("allow_custom_size", False))}


def asset_prompt(m: dict, a: dict, post: Path) -> str | None:
    if a.get("existing"):
        return None
    if a.get("prompt_file"):
        pf = (post / a["prompt_file"]).resolve()
        if not pf.is_file():
            raise UserError(f"asset '{a['id']}': prompt_file {a['prompt_file']} not found")
        text = pf.read_text(encoding="utf-8").strip()
    else:
        text = a.get("prompt", "").strip()
    d = m.get("image_defaults", {})
    if "prompt_suffix" in d:                       # explicit (an empty string turns the shared direction off)
        suffix = d["prompt_suffix"].strip()
    else:                                          # default: the brand art direction, appended to every prompt
        af = REPO / "brand" / "art-direction-prompt.txt"
        suffix = af.read_text(encoding="utf-8").strip() if af.is_file() else ""
    return f"{text}\n\n{suffix}" if suffix else text


def all_copy(m: dict) -> list[tuple[str, str]]:
    out = []
    for n, s in enumerate(m.get("slides", []), 1):
        for f in COPY_FIELDS:
            if isinstance(s.get(f), str):
                out.append((f"slide {n} {f}", s[f]))
    if isinstance(m.get("caption"), str):
        out.append(("caption", m["caption"]))
    if isinstance(m.get("topic"), str):
        out.append(("topic", m["topic"]))
    return out


def validate_manifest(m: dict, post: Path) -> tuple[list[str], list[str]]:
    E: list[str] = []
    W: list[str] = []
    slug = m.get("slug")
    if not isinstance(slug, str) or not (SLUG_RE.match(slug) or slug.startswith("_")):
        E.append("slug: required, lowercase letters/numbers/hyphens")
    elif post.name != slug:
        E.append(f"slug '{slug}' must match its folder name '{post.name}'")
    if not m.get("topic"):
        E.append("topic: required")
    fmt = m.get("format", "portrait")
    if fmt not in lay.FORMATS:
        E.append(f"format: must be one of {', '.join(lay.FORMATS)}")
    ex = m.get("export")
    if ex:
        if not (isinstance(ex, dict) and isinstance(ex.get("width"), int) and isinstance(ex.get("height"), int)
                and ex["width"] > 0 and ex["height"] > 0):
            E.append("export: needs positive integer width and height")
        elif fmt in lay.FORMATS and (ex["width"], ex["height"]) != lay.FORMATS[fmt]:
            W.append(f"export {ex['width']}x{ex['height']} differs from the default {lay.FORMATS[fmt][0]}x{lay.FORMATS[fmt][1]} for '{fmt}'")
    brand = m.get("brand", {})
    if brand.get("name", "AERELO") != "AERELO":
        E.append("brand.name must be exactly 'AERELO' (no 'Studios')")
    if brand.get("theme", "night") not in lay.THEMES:
        E.append(f"brand.theme must be one of {', '.join(lay.THEMES)}")
    for where, text in all_copy(m):
        if re.search(r"aerelo\s+studios?", text, re.I):
            E.append(f"{where}: company name is 'AERELO', not 'AERELO Studios'")
        if PRICE_RE.search(text):
            E.append(f"{where}: prices are not allowed on social posts")

    # assets
    assets = m.get("assets", [])
    if not isinstance(assets, list):
        E.append("assets: must be a list")
        assets = []
    ids: dict[str, dict] = {}
    for k, a in enumerate(assets, 1):
        if not isinstance(a, dict) or not ID_RE.match(str(a.get("id", ""))):
            E.append(f"assets[{k}]: needs an id (lowercase letters/numbers/-/_)")
            continue
        aid = a["id"]
        if aid in ids:
            E.append(f"asset '{aid}': duplicate id")
        ids[aid] = a
        for bad in set(a) - ASSET_KEYS:
            W.append(f"asset '{aid}': unknown field '{bad}' ignored")
        srcs = [x for x in ("prompt", "prompt_file", "existing") if a.get(x)]
        if len(srcs) != 1:
            E.append(f"asset '{aid}': give exactly one of prompt / prompt_file / existing")
            continue
        if a.get("existing"):
            ep = (post / a["existing"]) if not Path(a["existing"]).is_absolute() else Path(a["existing"])
            if not ep.resolve().is_relative_to(REPO):
                E.append(f"asset '{aid}': existing path must be inside the repo")
            elif not ep.is_file():
                E.append(f"asset '{aid}': existing file not found: {a['existing']}")
            continue
        try:
            if not asset_prompt(m, a, post):
                E.append(f"asset '{aid}': prompt is empty")
        except UserError as e:
            E.append(str(e))
        out = a.get("output", f"{aid}.png")
        if "/" in out or "\\" in out or not out.lower().endswith(".png"):
            E.append(f"asset '{aid}': output must be a plain .png filename")
        p = asset_params(m, a)
        try:
            for w in ig.validate_params(p["model"], p["quality"], p["size"], p["complexity"], p["allow_custom"]):
                W.append(f"asset '{aid}': {w}")
        except ig.ImageGenError as e:
            E.append(f"asset '{aid}': {e}")

    # slides
    slides = m.get("slides")
    if not isinstance(slides, list) or not slides:
        E.append("slides: need at least one slide")
        slides = []
    if len(slides) > 20:
        E.append("slides: Instagram carousels allow at most 20")
    used: set[str] = set()
    W_, H_, _ = export_size(m) if fmt in lay.FORMATS else (1080, 1350, fmt)
    for n, s in enumerate(slides, 1):
        if s.get("layout") not in lay.LAYOUTS:
            E.append(f"slide {n}: layout must be one of {', '.join(lay.LAYOUTS)}")
            continue
        for f in REQUIRED[s["layout"]]:
            if not isinstance(s.get(f), str) or not s[f].strip():
                E.append(f"slide {n} ({s['layout']}): '{f}' is required")
        for bad in set(s) - SLIDE_KEYS:
            W.append(f"slide {n}: unknown field '{bad}' ignored")
        if s.get("theme", brand.get("theme", "night")) not in lay.THEMES:
            E.append(f"slide {n}: theme must be one of {', '.join(lay.THEMES)}")
        art = s.get("artwork")
        if art:
            for bad in set(art) - ART_KEYS:
                W.append(f"slide {n}: unknown artwork field '{bad}' ignored")
            if art.get("asset") not in ids:
                E.append(f"slide {n}: artwork.asset '{art.get('asset')}' is not defined in assets")
                continue
            used.add(art["asset"])
            if art.get("mode", "full") not in ("full", "panel"):
                E.append(f"slide {n}: artwork.mode must be full or panel")
            if art.get("fit", "cover") not in ("cover", "contain"):
                E.append(f"slide {n}: artwork.fit must be cover or contain")
            ov = art.get("overlay", 0.6)
            if not isinstance(ov, (int, float)) or not 0 <= ov <= 1:
                E.append(f"slide {n}: artwork.overlay must be 0..1")
            elif art.get("mode", "full") == "full" and ov < 0.45:
                W.append(f"slide {n}: overlay {ov} is low; text legibility may suffer")
            a = ids[art["asset"]]
            if not a.get("existing") and art.get("fit", "cover") == "cover" and art.get("mode", "full") in ("full", "panel"):
                m_ = re.fullmatch(r"(\d+)x(\d+)", asset_params(m, a)["size"])
                if m_ and art.get("mode", "full") == "full":
                    ar_img, ar_box = int(m_[1]) / int(m_[2]), W_ / H_
                    lost = 1 - (min(ar_img, ar_box) / max(ar_img, ar_box))
                    if lost > 0.35:
                        W.append(f"slide {n}: cover-fit crops about {lost:.0%} of artwork '{art['asset']}'; check 'focus' or choose a closer size")
    for aid in ids:
        if aid not in used:
            W.append(f"asset '{aid}' is defined but no slide uses it")
    return E, W


# ---- ledger ----------------------------------------------------------------------------------
class Ledger:
    def __init__(self, post: Path):
        self.post = post
        self.path = post / "assets" / "ledger.json"
        self.data = {"version": 1, "assets": {}}
        if self.path.is_file():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def entry(self, aid: str) -> dict:
        return self.data["assets"].setdefault(aid, {"current": None, "pending": None, "history": []})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def total_estimate(self) -> tuple[float, int, int]:
        usd, n, n_known = 0.0, 0, 0
        for e in self.data["assets"].values():
            for h in e["history"]:
                if h.get("status") == "completed":
                    n += 1
                    if h.get("cost_estimate"):
                        usd += h["cost_estimate"]["usd"]
                        n_known += 1
        return usd, n, n_known


def asset_state(m: dict, a: dict, post: Path, led: Ledger) -> tuple[str, str]:
    """-> (state, detail). states: existing, cached, missing, stale, modified, pending"""
    if a.get("existing"):
        return "existing", a["existing"]
    e = led.data["assets"].get(a["id"])
    p = asset_params(m, a)
    want = ig.cache_key(asset_prompt(m, a, post), p["model"], p["quality"], p["size"], p["complexity"])
    if e and e.get("pending"):
        return "pending", "a previous request may have been charged - check your OpenAI usage first"
    cur = e and e.get("current")
    if not cur or not (post / cur["file"]).is_file():
        return "missing", ""
    if cur["cache_key"] != want:
        return "stale", "prompt/settings changed since this was generated; use `regen` to make a new version"
    if ig.sha256_file(post / cur["file"]) != cur["file_sha256"]:
        return "modified", "file edited on disk since generation (kept as-is)"
    return "cached", cur["file"]


def next_free(path: Path) -> Path:
    if not path.exists():
        return path
    k = 2
    while True:
        cand = path.with_name(f"{path.stem}-v{k}{path.suffix}")
        if not cand.exists():
            return cand
        k += 1


# ---- commands ----------------------------------------------------------------------------------
def print_issues(E, W):
    for w in W:
        print(f"  warning: {w}")
    for e in E:
        print(f"  ERROR:   {e}")


def must_validate(arg: str):
    m, post = load_manifest(arg)
    E, W = validate_manifest(m, post)
    if E:
        print(f"Manifest has {len(E)} error(s):")
        print_issues(E, W)
        raise UserError("fix the manifest and retry")
    return m, post, W


def cmd_validate(a) -> int:
    m, post = load_manifest(a.post)
    E, W = validate_manifest(m, post)
    w, h, fmt = export_size(m)
    print(f"{m.get('slug')}: {len(m.get('slides', []))} slide(s), {len(m.get('assets', []))} asset(s), {fmt} {w}x{h}")
    print_issues(E, W)
    print("INVALID" if E else "Manifest OK." + (" (with warnings)" if W else ""))
    return 2 if E else 0


def plan(m, post):
    led = Ledger(post)
    rows = []
    for a in m.get("assets", []):
        st, detail = asset_state(m, a, post, led)
        p = asset_params(m, a)
        out = None if a.get("existing") else str(next_free(post / "assets/originals" / a.get("output", f"{a['id']}.png")).relative_to(post))
        rows.append((a, st, detail, p, out))
    return led, rows


def print_plan(m, post, rows):
    w, h, fmt = export_size(m)
    print(f"Post: {m['slug']}  ({fmt} {w}x{h})   topic: {m['topic']}")
    print(f"Slides: {len(m['slides'])}    Assets: {len(rows)}")
    if rows:
        print(f"  {'asset':<18}{'state':<10}{'model / quality / size':<46}file")
    for a, st, detail, p, out in rows:
        spec = "(existing file)" if a.get("existing") else f"{p['model']} / {p['quality']} / {p['size']}"
        shown = detail if st in ("cached", "existing") else (out or "")
        print(f"  {a['id']:<18}{st:<10}{spec:<46}{shown}")
        if st in ("stale", "pending", "modified"):
            print(f"  {'':<18}  -> {detail}")
    n = sum(1 for r in rows if r[1] == "missing")
    print(f"\nPlanned paid image requests: {n} (sequential, 1 image each, no automatic retries).")
    print("Cost: not knowable before the run; each completed request records its reported usage and an")
    print("ESTIMATE based on the actual settings (list prices, not an invoice).")


def cmd_dry_run(a) -> int:
    m, post, W = must_validate(a.post)
    print_issues([], W)
    _, rows = plan(m, post)
    print_plan(m, post, rows)
    print("\nDry run only - no API call was made.")
    return 0


def record_for_ledger(rec: dict, post: Path) -> dict:
    r = dict(rec)
    r["file"] = str(Path(rec["file"]).resolve().relative_to(post))
    return r


def run_requests(m, post, led, jobs, key_file, override: bool = False) -> int:
    key, source = ig.load_api_key(key_file)
    client = ig.make_client(key)
    print(f"Key source: {source}. Sending {len(jobs)} request(s) sequentially.")
    done = 0
    for a, out_path, overwrite in jobs:
        p = asset_params(m, a)
        prompt = asset_prompt(m, a, post)
        if not override and requests_today() >= load_budget()["max_images_per_day"]:
            print("  STOPPED: daily image cap reached (budget.json). Nothing further was sent.")
            return 1
        e = led.entry(a["id"])
        log_spend(post, a["id"])
        e["pending"] = {"started_at": ig.now_iso(), "model": p["model"], "size": p["size"], "quality": p["quality"],
                        "file": str(out_path.relative_to(post))}
        led.save()
        print(f"[{done + 1}/{len(jobs)}] {a['id']} -> {out_path.relative_to(post)} ...", flush=True)
        try:
            rec = ig.generate_image(prompt, out_path, model=p["model"], quality=p["quality"], size=p["size"],
                                    complexity=p["complexity"], client=client, overwrite=overwrite)
        except ig.AmbiguousOutcome as exc:
            e["history"].append({"status": "unknown", "at": ig.now_iso(), "asset_id": a["id"], "error": ig.redact(exc)})
            led.save()                    # leave 'pending' set on purpose
            print(f"  STOPPED: {ig.redact(exc)}")
            return 1
        except ig.ImageGenError as exc:
            e["pending"] = None
            e["history"].append({"status": "failed", "at": ig.now_iso(), "asset_id": a["id"], "model": p["model"],
                                 "size": p["size"], "quality": p["quality"], "error": ig.redact(exc)})
            led.save()
            print(f"  FAILED: {ig.redact(exc)}\n  Stopping; nothing was retried. {done} request(s) completed earlier in this run.")
            return 1
        rec = record_for_ledger(rec, post)
        rec["asset_id"] = a["id"]
        e["history"].append(rec)
        e["current"] = {"file": rec["file"], "cache_key": rec["cache_key"], "file_sha256": rec["file_sha256"]}
        e["pending"] = None
        led.save()                         # persist after EVERY completed request
        done += 1
        print(ig.describe_result(dict(rec, file=rec["file"])))
    usd, n, known = led.total_estimate()
    print(f"\nPost total so far: {n} completed request(s)" + (f", est. ~${usd:.4f} ({known} with usage data) - ESTIMATE, not an invoice" if known else ""))
    return 0


def cmd_generate(a) -> int:
    m, post, W = must_validate(a.post)
    print_issues([], W)
    led, rows = plan(m, post)
    print_plan(m, post, rows)
    only = set(a.only or [])
    unknown = only - {r[0]["id"] for r in rows}
    if unknown:
        raise UserError(f"--only names unknown asset(s): {', '.join(sorted(unknown))}")
    todo = [r for r in rows if r[1] == "missing" and (not only or r[0]["id"] in only)]
    blocked = [r for r in rows if r[1] == "pending" and (not only or r[0]["id"] in only)]
    if blocked and not a.retry_pending:
        raise UserError("asset(s) with an unconfirmed earlier request: " + ", ".join(r[0]["id"] for r in blocked)
                        + ". Check your OpenAI usage page, then re-run with --retry-pending if you want to pay again.")
    if a.retry_pending:
        todo += [r for r in blocked]
    if not todo:
        print("\nNothing to generate: all assets are cached/existing (stale ones need `regen`).")
        return 0
    if not should_spend(a):
        print(f"\nPREVIEW ONLY - {len(todo)} paid request(s) would be sent (drop --dry, or set auto_approve in budget.json, to run).")
        return 0
    if not a.override_budget:
        prob = budget_problem(len(todo), led)
        if prob:
            raise UserError(prob)
    jobs = [(r[0], r[4] and (post / r[4]), False) for r in todo]
    return run_requests(m, post, led, jobs, a.env_file, a.override_budget)


def cmd_regen(a) -> int:
    m, post, W = must_validate(a.post)
    asset = next((x for x in m.get("assets", []) if x["id"] == a.asset), None)
    if not asset or asset.get("existing"):
        raise UserError(f"'{a.asset}' is not a generated asset in this manifest")
    led = Ledger(post)
    e = led.entry(asset["id"])
    if e.get("pending") and not a.retry_pending:
        raise UserError("an earlier request for this asset is unconfirmed; check OpenAI usage, then pass --retry-pending")
    base = post / "assets/originals" / asset.get("output", f"{asset['id']}.png")
    cur = e.get("current")
    if a.overwrite and cur:
        out, ow = post / cur["file"], True
    else:
        out, ow = next_free(base), False
    p = asset_params(m, asset)
    print(f"Regenerate '{asset['id']}': {p['model']} / {p['quality']} / {p['size']}")
    print(f"  -> {out.relative_to(post)}" + ("  (OVERWRITING the current original)" if ow else "  (new version; previous original is kept)"))
    if not should_spend(a):
        print("\nPREVIEW ONLY - 1 paid request would be sent (drop --dry, or set auto_approve in budget.json, to run).")
        return 0
    if not a.override_budget:
        prob = budget_problem(1, led, regen_of=asset["id"])
        if prob:
            raise UserError(prob)
    return run_requests(m, post, led, [(asset, out, ow)], a.env_file, a.override_budget)


def resolve_art(m, post, led, allow_ph: bool, used_ids: set[str]) -> tuple[dict, list[str]]:
    paths, placeholders = {}, []
    for a in m.get("assets", []):
        if a["id"] not in used_ids:
            continue
        if a.get("existing"):
            ep = Path(a["existing"])
            paths[a["id"]] = ep if ep.is_absolute() else (post / ep).resolve()
            continue
        cur = led.data["assets"].get(a["id"], {}).get("current")
        if cur and (post / cur["file"]).is_file():
            paths[a["id"]] = post / cur["file"]
            continue
        if not allow_ph:
            raise UserError(f"artwork '{a['id']}' has not been generated. Run `generate` (paid) or render with --placeholders.")
        w, h = (int(x) for x in asset_params(m, a)["size"].split("x"))
        ph = post / "assets/placeholders" / f"{a['id']}.png"
        lay.make_placeholder_image(ph, w, h, a["id"])
        paths[a["id"]] = ph
        placeholders.append(a["id"])
    return paths, placeholders


def cmd_render(a) -> int:
    m, post, W = must_validate(a.post)
    print_issues([], W)
    Wd, Hd, fmt = export_size(m)
    story = fmt == "story"
    slides = m["slides"]
    n = len(slides)
    only = None
    if a.only:
        only = {int(x) for x in a.only.split(",")}
        if not only <= set(range(1, n + 1)):
            raise UserError(f"--only must be slide numbers 1..{n}")
    led = Ledger(post)
    used = {s["artwork"]["asset"] for s in slides if s.get("artwork")}
    art, placeholders = resolve_art(m, post, led, a.placeholders, used)
    src = post / "source"
    logos, logo_ph, missing = lay.resolve_logos(a.placeholders, src / "_placeholder-logo")
    fonts = lay.font_css(src)
    default_theme = m.get("brand", {}).get("theme", "night")
    n_content = sum(1 for s in slides if s["layout"] == "content")
    pages, outs, counter = [], [], 0
    for k, s in enumerate(slides):
        if s["layout"] == "content":
            counter += 1
        if only and (k + 1) not in only:
            continue
        theme = s.get("theme", default_theme)
        ctx = {"theme": theme, "i": k, "n": n, "n_content": n_content, "num": f"{counter:02d}", "W": Wd, "H": Hd,
               "story": story, "logo_url": lay.rel_url(logos[theme], src),
               "art_url": lay.rel_url(art[s["artwork"]["asset"]], src) if s.get("artwork") else None}
        name = f"slide-{k + 1:02d}"
        hf = src / f"{name}.html"
        src.mkdir(parents=True, exist_ok=True)
        hf.write_text(lay.page_html(lay.build_slide(s, ctx), Wd, Hd, fonts, f"{m['slug']} {name}"), encoding="utf-8")
        pages.append((hf, name))
        outs.append(post / "exports" / f"{name}.png")
    print(f"Rendering {len(pages)} slide(s) at {Wd}x{Hd} (no API calls)...")
    reports = lay.render_pages(pages, outs, Wd, Hd, story)
    errors = 0
    for r in reports:
        errs = [i for i in r["issues"] if i["level"] == "error"]
        errors += len(errs)
        print(f"  {r['slide']}: " + ("OK" if not errs else f"{len(errs)} problem(s)"))
        for i in errs:
            print(f"      [{i['kind']}] {i['msg']}")
    all_pngs = [post / "exports" / f"slide-{k + 1:02d}.png" for k in range(n)]
    notes = []
    if placeholders:
        notes.append("PLACEHOLDER ARTWORK: " + ", ".join(placeholders))
    if logo_ph:
        notes.append("PLACEHOLDER LOGO")
    if all(p.exists() for p in all_pngs):
        lay.make_contact_sheet(all_pngs, post / "contact-sheet.png", " | ".join(notes) + (" - NOT FINAL" if notes else ""))
        print(f"Contact sheet: {shown(post / 'contact-sheet.png')}")
    (post / "source").mkdir(exist_ok=True)
    (post / "source/qa-report.json").write_text(json.dumps(
        {"placeholders_used": placeholders, "placeholder_logo": logo_ph, "missing_logo_files": missing,
         "slides": reports}, indent=2), encoding="utf-8")
    cap = post / "caption.md"
    if m.get("caption") and not cap.exists():
        cap.write_text(f"# Caption\n\n{m['caption'].strip()}\n", encoding="utf-8")
        print("Wrote caption.md")
    elif cap.exists():
        print("caption.md exists - left unchanged.")
    if notes:
        print("\n!! " + "; ".join(notes) + " - these exports are for layout checking only, not for posting.")
    if missing:
        print("Missing brand files: " + ", ".join(f"brand/logo/{x}" for x in missing))
    print(f"\n{'FAILED QA: ' + str(errors) + ' problem(s)' if errors else 'QA passed'}. Exports: {shown(post / 'exports')}/")
    return 1 if errors else 0


def cmd_status(a) -> int:
    m, post = load_manifest(a.post)
    led = Ledger(post)
    print(f"{m['slug']}: asset status")
    for x in m.get("assets", []):
        st, detail = asset_state(m, x, post, led)
        print(f"  {x['id']:<18}{st:<10}{detail}")
        for h in led.data["assets"].get(x["id"], {}).get("history", []):
            extra = f"req {h.get('request_id')}" if h.get("request_id") else ""
            est = f" ~${h['cost_estimate']['usd']:.4f}(est)" if h.get("cost_estimate") else ""
            print(f"      {h.get('status'):<10}{h.get('finished_at', h.get('at', ''))}  {h.get('file', '')}  {extra}{est}")
    usd, n, known = led.total_estimate()
    print(f"\nCompleted requests: {n}. " + (f"Estimated spend ~${usd:.4f} over {known} with usage data (ESTIMATE from list prices, not an invoice)." if known else "No usage data recorded yet."))
    return 0


def cmd_review(a) -> int:
    m, post = load_manifest(a.post)
    led = Ledger(post)
    files, labels = [], []
    for x in m.get("assets", []):
        if x.get("existing"):
            continue
        cur = led.data["assets"].get(x["id"], {}).get("current")
        if cur and (post / cur["file"]).is_file():
            files.append(post / cur["file"])
            labels.append(x["id"])
            print(f"  {x['id']:<18}{shown(post / cur['file'])}")
    if not files:
        raise UserError("no generated originals yet - run `generate` first")
    out = post / "assets" / "review-sheet.png"
    lay.make_contact_sheet(files, out, "Generated originals (unedited) - check against brand/art-direction.md", thumb_w=330, cols=4, labels=labels)
    print(f"\nReview sheet: {shown(out)}\nOpen each original too (full size) before building layouts around it.")
    return 0


STARTER = {
    "slug": "", "topic": "", "format": "portrait",
    "brand": {"name": "AERELO", "theme": "night"},
    "image_defaults": {"model": ig.DEFAULT_MODEL, "quality": "high", "size": "1024x1536",
                       "prompt_suffix": "No text, no letters, no logos, no people. Calm, premium, restrained. "
                                        "Near-black ground #121515, teal #08808D, one small warm gold #F5C13A accent."},
    "assets": [{"id": "hero", "prompt": "Abstract premium background: a thin luminous orbit arc over a dark, softly textured surface."}],
    "slides": [
        {"layout": "cover", "label": "Topic label", "headline": "Your headline\nhere.", "headline_size": 128,
         "artwork": {"asset": "hero", "mode": "panel", "focus": "50% 50%"}},
        {"layout": "content", "title": "First point", "lead": "One short supporting sentence."},
        {"layout": "close", "headline": "Start with the questions your site must answer.", "cta": "Message us to begin"},
    ],
    "caption": "Caption text goes here.",
}


def cmd_new(a) -> int:
    if not SLUG_RE.match(a.slug):
        raise UserError("slug must be lowercase letters/numbers/hyphens")
    post = CONTENT / a.slug
    if post.exists():
        raise UserError(f"{shown(post)} already exists; not touching it")
    for d in ("source", "assets/originals", "exports"):
        (post / d).mkdir(parents=True)
    m = json.loads(json.dumps(STARTER))
    m.update(slug=a.slug, topic=a.topic or a.slug.replace("-", " "), format=a.format)
    (post / "manifest.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created {shown(post)}/ with a starter manifest.json. Edit it, then: dry-run -> generate -> render.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def post_arg(p):
        p.add_argument("post", help="post slug (content/<slug>) or path to the post folder")

    p = sub.add_parser("new"); p.add_argument("slug"); p.add_argument("--topic"); p.add_argument("--format", default="portrait", choices=list(lay.FORMATS)); p.set_defaults(fn=cmd_new)
    for name, fn in (("validate", cmd_validate), ("dry-run", cmd_dry_run), ("status", cmd_status)):
        p = sub.add_parser(name); post_arg(p); p.set_defaults(fn=fn)
    p = sub.add_parser("generate"); post_arg(p)
    p.add_argument("--only", nargs="+", metavar="ASSET_ID"); p.add_argument("--yes", action="store_true", help="force-run even if auto_approve is off")
    p.add_argument("--dry", action="store_true", help="preview only, never spend")
    p.add_argument("--override-budget", action="store_true")
    p.add_argument("--retry-pending", action="store_true"); p.add_argument("--env-file", type=Path); p.set_defaults(fn=cmd_generate)
    p = sub.add_parser("regen"); post_arg(p); p.add_argument("asset", metavar="ASSET_ID")
    p.add_argument("--yes", action="store_true", help="force-run even if auto_approve is off"); p.add_argument("--overwrite", action="store_true")
    p.add_argument("--dry", action="store_true", help="preview only, never spend"); p.add_argument("--override-budget", action="store_true")
    p.add_argument("--retry-pending", action="store_true"); p.add_argument("--env-file", type=Path); p.set_defaults(fn=cmd_regen)
    p = sub.add_parser("review"); post_arg(p); p.set_defaults(fn=cmd_review)
    p = sub.add_parser("render"); post_arg(p)
    p.add_argument("--placeholders", action="store_true", help="use stand-in artwork/logo where real files are missing (layout test only)")
    p.add_argument("--only", help="comma-separated slide numbers, e.g. 1,3"); p.set_defaults(fn=cmd_render)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (UserError, ig.ImageGenError, lay.RenderError) as e:
        print(f"error: {ig.redact(e)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
