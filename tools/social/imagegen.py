#!/usr/bin/env python3
"""AERELO image generation via the OpenAI Images API (POST /v1/images/generations).

One image per request, PNG out, streaming off, no SDK retries, never overwrites.
Every paid command needs --yes; without it the command only prints what it WOULD send.

Commands
  check-access   Free: asks the API whether this key can see the model (GET /v1/models/{id}).
  gen            PAID : generate one image from a prompt/prompt file.

Credentials: OPENAI_API_KEY from the environment, else from .env.images (git-ignored).
The key is never printed, logged or written anywhere.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = REPO / ".env.images"

# ---- Verified against OpenAI docs on 2026-11-05 (see tools/social/README.md) -------------
DEFAULT_MODEL = "gpt-image-2.6-sunburst"
QUALITIES = ("low", "medium", "high", "auto")          # documented for the GPT image models
STANDARD_SIZES = ("1024x1024", "1536x1024", "1024x1536")
COMPLEXITIES = ("low", "medium", "high")                # 2.6 only; omitted unless you set it
OUTPUT_FORMAT = "png"
DEFAULT_TIMEOUT_S = 360.0
# Custom WxH rules are documented for gpt-image-2 / 2.5. They are NOT confirmed for 2.6,
# so custom sizes are opt-in (--custom-size) and always warn.
CUSTOM_SIZE_RULES = "each side divisible by 16, aspect ratio between 1:3 and 3:1, max 3840x2160"

# Cost ESTIMATE inputs: list prices on the model page, USD per 1M tokens. Edit if they change.
PRICING_PER_M = {
    "gpt-image-2.6-sunburst": {"text_in": 5.00, "image_in": 8.00, "image_out": 30.00},
}


class ImageGenError(Exception):
    """Expected, user-facing failure (no traceback needed)."""


class MissingKey(ImageGenError):
    pass


class AmbiguousOutcome(ImageGenError):
    """Timeout / dropped connection: the request may have been processed and billed."""


# ---- secrets -----------------------------------------------------------------------------
_KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


def redact(text: str) -> str:
    return _KEY_RE.sub("sk-***redacted***", str(text))


def _looks_placeholder(v: str) -> bool:
    low = v.lower()
    return (not v) or "replace" in low or "your_key" in low or "your-key" in low or "xxxx" in low or v.startswith("<")


def _is_git_ignored(path: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", str(path)], capture_output=True)
        if r.returncode in (0, 1):
            return r.returncode == 0
    except FileNotFoundError:
        pass
    gi = REPO / ".gitignore"          # fallback when git is unavailable
    return gi.is_file() and path.name in {ln.strip() for ln in gi.read_text().splitlines()}


def load_api_key(env_file: Path | None = None) -> tuple[str, str]:
    """Return (key, source). Reads ONLY OPENAI_API_KEY; never dumps the environment."""
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if k and not _looks_placeholder(k):
        return k, "environment"
    path = Path(env_file) if env_file else DEFAULT_ENV_FILE
    if path.is_file():
        try:
            inside = path.resolve().is_relative_to(REPO)
        except Exception:
            inside = False
        if inside and not _is_git_ignored(path):
            raise ImageGenError(f"Refusing to read {path.name}: it is not git-ignored. Add it to .gitignore first.")
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, val = line.partition("=")
            name = name.replace("export ", "").strip()
            if name == "OPENAI_API_KEY":
                val = val.strip().strip("'\"")
                if val and not _looks_placeholder(val):
                    return val, str(path.name)
    raise MissingKey(
        "OPENAI_API_KEY not found. Copy .env.images.example to .env.images and enter your key there "
        "yourself (or export OPENAI_API_KEY in your shell). Do not paste it into chat."
    )


# ---- request building & validation -------------------------------------------------------
def validate_params(model: str, quality: str, size: str, complexity: str | None = None,
                    allow_custom_size: bool = False) -> list[str]:
    """Raise ImageGenError on bad params. Return warnings."""
    warns: list[str] = []
    if not model or not isinstance(model, str):
        raise ImageGenError("model must be a non-empty string")
    if model != DEFAULT_MODEL:
        warns.append(f"model '{model}' is not the preferred '{DEFAULT_MODEL}'; no automatic substitution is ever made")
    if quality not in QUALITIES:
        raise ImageGenError(f"quality '{quality}' not accepted here. Documented values: {', '.join(QUALITIES)}")
    if complexity is not None and complexity not in COMPLEXITIES:
        raise ImageGenError(f"complexity '{complexity}' invalid. Values: {', '.join(COMPLEXITIES)}")
    if size not in STANDARD_SIZES:
        m = re.fullmatch(r"(\d+)x(\d+)", size or "")
        if not m:
            raise ImageGenError(f"size '{size}' must look like 1024x1536")
        if not allow_custom_size:
            raise ImageGenError(
                f"size '{size}' is not a standard size ({', '.join(STANDARD_SIZES)}). Custom sizes are only documented "
                f"for gpt-image-2/2.5, not confirmed for 2.6. Pass --custom-size to try one ({CUSTOM_SIZE_RULES}).")
        w, h = int(m[1]), int(m[2])
        if w % 16 or h % 16 or not (1 / 3 <= w / h <= 3) or w > 3840 or h > 3840 or w * h > 3840 * 2160:
            raise ImageGenError(f"custom size {size} breaks the documented rules: {CUSTOM_SIZE_RULES}")
        warns.append(f"custom size {size} is unverified for {model}")
    return warns


def build_request(prompt: str, model: str, quality: str, size: str, complexity: str | None = None) -> dict:
    """Exact kwargs sent to client.images.generate. NOTE: no response_format (GPT image models reject it)."""
    if not prompt or not prompt.strip():
        raise ImageGenError("prompt is empty")
    kw = dict(model=model, prompt=prompt, size=size, quality=quality, n=1, output_format=OUTPUT_FORMAT, stream=False)
    if complexity:
        kw["complexity"] = complexity
    return kw


def cache_key(prompt: str, model: str, quality: str, size: str, complexity: str | None = None) -> str:
    blob = json.dumps([model, quality, size, complexity, OUTPUT_FORMAT, prompt], ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---- client ------------------------------------------------------------------------------
def make_client(api_key: str, timeout_s: float = DEFAULT_TIMEOUT_S):
    from openai import OpenAI, Timeout    # SDK-exported Timeout works across httpx/httpx2 SDK builds
    # max_retries=0: a paid request is never silently repeated by the SDK.
    return OpenAI(api_key=api_key, max_retries=0, timeout=Timeout(timeout_s, connect=15.0))


def estimate_cost(usage: dict | None, model: str) -> dict | None:
    """ESTIMATE from reported token usage x list prices. Not an invoice."""
    price = PRICING_PER_M.get(model)
    if not usage or not price or usage.get("output_tokens") is None:
        return None
    det = usage.get("input_tokens_details") or {}
    text_in = det.get("text_tokens")
    img_in = det.get("image_tokens") or 0
    if text_in is None:
        text_in = max((usage.get("input_tokens") or 0) - img_in, 0)
    usd = (text_in * price["text_in"] + img_in * price["image_in"] + usage["output_tokens"] * price["image_out"]) / 1e6
    return {"usd": round(usd, 4),
            "basis": "ESTIMATE: reported token usage x list prices in imagegen.PRICING_PER_M; not an invoice"}


def classify_error(exc: Exception, model: str) -> str:
    import openai
    if isinstance(exc, openai.APITimeoutError):
        return ("Timed out waiting for the API. The request may STILL have been processed and billed - "
                "check your OpenAI usage page before trying again. Nothing was retried.")
    if isinstance(exc, openai.AuthenticationError):
        return "Authentication failed (HTTP 401). Check the key in .env.images."
    if isinstance(exc, (openai.PermissionDeniedError, openai.NotFoundError)):
        return (f"Model '{model}' is not available to this account (HTTP {exc.status_code}): {redact(exc.message)}. "
                "No other model was substituted. Check API access / organization verification.")
    if isinstance(exc, openai.RateLimitError):
        return f"Rate limited or out of quota (HTTP 429): {redact(exc.message)}. Not retried."
    if isinstance(exc, openai.BadRequestError):
        return f"API rejected the request (HTTP 400): {redact(exc.message)}"
    if isinstance(exc, openai.APIStatusError):
        return f"API error (HTTP {exc.status_code}): {redact(exc.message)}"
    if isinstance(exc, openai.APIConnectionError):
        return "Could not reach the API (network). The request may or may not have been received; not retried."
    return f"{type(exc).__name__}: {redact(exc)}"


# ---- the one paid call ---------------------------------------------------------------------
def generate_image(prompt: str, out_path: Path, *, model: str = DEFAULT_MODEL, quality: str = "high",
                   size: str = "1024x1536", complexity: str | None = None, client=None,
                   overwrite: bool = False) -> dict:
    """Make ONE request. Returns a ledger-safe record (never contains base64 or secrets).

    Raises ImageGenError for expected failures; the caller decides what to record.
    """
    from PIL import Image
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        raise ImageGenError(f"{out_path} already exists; refusing to overwrite (use a new name or --overwrite).")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw = build_request(prompt, model, quality, size, complexity)
    started = now_iso()
    try:
        raw = client.images.with_raw_response.generate(**kw)
        request_id = raw.headers.get("x-request-id")
        resp = raw.parse()
    except ImageGenError:
        raise
    except Exception as exc:  # noqa: BLE001
        import openai
        cls = AmbiguousOutcome if isinstance(exc, (openai.APITimeoutError, openai.APIConnectionError)) else ImageGenError
        raise cls(classify_error(exc, model)) from None
    finished = now_iso()
    try:
        b64 = resp.data[0].b64_json
    except (AttributeError, IndexError, TypeError):
        b64 = None
    if not b64:
        raise ImageGenError(f"Response had no data[0].b64_json (request id: {request_id}). Nothing was written.")
    blob = base64.b64decode(b64)
    img = Image.open(io.BytesIO(blob))
    img.verify()
    img = Image.open(io.BytesIO(blob))
    if overwrite:
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        tmp.write_bytes(blob)
        os.replace(tmp, out_path)
    else:
        with open(out_path, "xb") as f:      # 'x' = fail if it appeared meanwhile
            f.write(blob)
    usage = None
    u = getattr(resp, "usage", None)
    if u is not None:
        usage = u.model_dump() if hasattr(u, "model_dump") else dict(u)
    return {
        "status": "completed", "started_at": started, "finished_at": finished,
        "model": model, "quality": quality, "size": size, "complexity": complexity,
        "output_format": OUTPUT_FORMAT, "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "cache_key": cache_key(prompt, model, quality, size, complexity),
        "request_id": request_id, "usage": usage, "cost_estimate": estimate_cost(usage, model),
        "file": str(out_path), "file_sha256": sha256_file(out_path), "image_size": list(img.size),
    }


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def describe_result(rec: dict) -> str:
    lines = [f"  file        : {rec['file']}", f"  image size  : {rec['image_size'][0]}x{rec['image_size'][1]}",
             f"  model       : {rec['model']}  quality={rec['quality']}  size={rec['size']}"]
    if rec.get("request_id"):
        lines.append(f"  request id  : {rec['request_id']}")
    if rec.get("usage"):
        lines.append(f"  usage       : {json.dumps(rec['usage'], sort_keys=True)}")
    else:
        lines.append("  usage       : (not returned)")
    if rec.get("cost_estimate"):
        lines.append(f"  est. cost   : ~${rec['cost_estimate']['usd']:.4f}  [{rec['cost_estimate']['basis']}]")
    return "\n".join(lines)


# ---- CLI ---------------------------------------------------------------------------------
def _read_prompt(args) -> str:
    if args.prompt and args.prompt_file:
        raise ImageGenError("give --prompt OR --prompt-file, not both")
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise ImageGenError("a prompt is required (--prompt or --prompt-file)")


def cmd_gen(args) -> int:
    prompt = _read_prompt(args)
    warns = validate_params(args.model, args.quality, args.size, args.complexity, args.custom_size)
    out_dir = Path(args.out_dir)
    name = args.filename or (f"{Path(args.prompt_file).stem if args.prompt_file else 'image'}-"
                             f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.png")
    if not name.lower().endswith(".png"):
        raise ImageGenError("filename must end in .png (output is always PNG)")
    out_path = out_dir / name
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    if out_path.exists() and not args.overwrite:
        raise ImageGenError(f"{out_path} already exists; refusing to overwrite (pick another --filename or pass --overwrite).")
    print(f"Planned request: model={args.model} quality={args.quality} size={args.size} n=1 format=png stream=off")
    print(f"  prompt ({len(prompt)} chars): {prompt[:90]}{'...' if len(prompt) > 90 else ''}")
    print(f"  output: {out_path}")
    if not args.yes:
        print("\nDRY RUN - no API call made. Add --yes to send this PAID request.")
        return 0
    key, source = load_api_key(args.env_file)
    print(f"Sending 1 paid request (key source: {source}). Timeout {args.timeout:.0f}s, no automatic retries...")
    client = make_client(key, args.timeout)
    try:
        rec = generate_image(prompt, out_path, model=args.model, quality=args.quality, size=args.size,
                             complexity=args.complexity, client=client, overwrite=args.overwrite)
    except ImageGenError as e:
        append_jsonl(out_dir / "generation-log.jsonl",
                     {"status": "failed", "at": now_iso(), "model": args.model, "quality": args.quality,
                      "size": args.size, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                      "error": redact(e)})
        raise
    append_jsonl(out_dir / "generation-log.jsonl", rec)
    print("Done.\n" + describe_result(rec))
    return 0


def cmd_check_access(args) -> int:
    key, source = load_api_key(args.env_file)
    client = make_client(key, 30)
    print(f"Checking model '{args.model}' (free metadata call, key source: {source})...")
    try:
        m = client.models.retrieve(args.model)
    except Exception as exc:  # noqa: BLE001
        raise ImageGenError(classify_error(exc, args.model)) from None
    print(f"OK: the API lists '{m.id}' for this key. (This does not guarantee image-generation quota or org verification.)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check-access", help="free: confirm the key can see the model")
    c.add_argument("--model", default=DEFAULT_MODEL)
    c.add_argument("--env-file", type=Path)
    c.set_defaults(fn=cmd_check_access)
    g = sub.add_parser("gen", help="PAID: generate one image (needs --yes)")
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    g.add_argument("--out-dir", default=str(REPO / "content" / "_tests"))
    g.add_argument("--filename")
    g.add_argument("--model", default=DEFAULT_MODEL)
    g.add_argument("--quality", default="high")
    g.add_argument("--size", default="1024x1536", help="generation size (standard: " + ", ".join(STANDARD_SIZES) + ")")
    g.add_argument("--complexity", help="2.6 only; omitted from the request unless set")
    g.add_argument("--custom-size", action="store_true", help="allow a non-standard WxH (unverified for 2.6)")
    g.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    g.add_argument("--overwrite", action="store_true")
    g.add_argument("--env-file", type=Path)
    g.add_argument("--yes", action="store_true", help="actually send the paid request")
    g.set_defaults(fn=cmd_gen)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except ImageGenError as e:
        print(f"error: {redact(e)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
