# AERELO social pipeline (OpenAI artwork + editable layouts)

Plan -> generate artwork (optional, paid) -> render real text/brand in HTML -> export PNGs + contact sheet.
Headings, body, CTAs, slide dots and the logo are always real HTML/CSS. Generated images are only backgrounds,
panels and textures. The legacy `templates/static/carousel_single_generator.py` is untouched; this pipeline reuses
its palette and ring/dot/label helpers, and a test fails if portrait geometry ever drifts from it.

## One-time setup
```bash
pip install -r tools/social/requirements.txt          # openai, playwright, Pillow (Chrome must be installed)
(cd tools/social && npm install)                      # brand fonts: Jost, Outfit, DM Mono (self-hosted, Fontsource)
cp .env.images.example .env.images                    # then edit .env.images yourself and set OPENAI_API_KEY
python3 tools/social/imagegen.py check-access         # FREE: can this key see gpt-image-2.6-sunburst?
```
Put `aerelo-mark-small-light.svg` and `aerelo-mark-small-ink.svg` in `brand/logo/` (see its README).

## Commands (all from the repo root)
| Command | Spends money? |
|---|---|
| `python3 tools/social/social.py new <slug> --topic "..." [--format portrait\|square\|story]` | no |
| `python3 tools/social/social.py validate <slug>` | no |
| `python3 tools/social/social.py dry-run <slug>` (lists planned image requests) | no |
| `python3 tools/social/social.py generate <slug>` (missing assets only, sequential; runs inside the budget; `--dry` previews) | **yes** |
| `python3 tools/social/social.py generate <slug> --only hero` | **yes** |
| `python3 tools/social/social.py regen <slug> <asset-id>` (new `-vN` file; old original kept) | **yes** |
| `python3 tools/social/social.py review <slug>` (sheet of generated originals to inspect) | no |
| `python3 tools/social/social.py render <slug>` (copy edits, re-export) | no |
| `python3 tools/social/social.py render <slug> --placeholders [--only 1,3]` | no |
| `python3 tools/social/social.py status <slug>` | no |
| `python3 tools/social/imagegen.py gen --prompt-file <file> --yes` (one standalone test image) | **yes** |

## Budget (replaces per-call approval)
`tools/social/budget.json` holds the standing authorization: `auto_approve` (true = paid commands run on their own), `max_images_per_post` (6),
`max_images_per_day` (20), `max_regens_per_asset` (2). Caps are enforced before and during a run and stop the batch. Set `auto_approve` to `false` to go
back to preview-unless-`--yes`. `--override-budget` bypasses the caps once. The standalone `imagegen.py gen` test command still needs `--yes`.
The daily count is a local file (`content/_spend/log.jsonl`, git-ignored) and counts requests sent, including ones that failed or timed out.

## Brand look
`brand/art-direction.md` is the art direction and prompt recipe; `brand/art-direction-prompt.txt` is appended to every prompt automatically
(set `image_defaults.prompt_suffix` in a manifest to override, or `""` to turn it off). Changing either makes existing assets stale (never auto-paid).

## Where it runs
`api.openai.com` is blocked in the claude.ai cloud workspace, so generation runs in Claude Code on your own computer, in this repo. Rendering and
validation work anywhere. On Windows, use `python` or `py` instead of `python3`; if Chrome/Edge is not found, run `python -m playwright install chromium`.

## Post folder
```
content/<slug>/
  manifest.json            you/Claude edit this: copy, layouts, artwork prompts
  source/slide-NN.html     editable layouts (open in a browser, or edit and re-run render)
  source/qa-report.json    overflow / margin / font / distortion / dimension checks
  assets/originals/*.png   generated artwork, never overwritten (regen adds -v2, -v3 ...)
  assets/ledger.json       every request: prompt, model/quality/size, timestamps, request id, usage, estimate
  assets/placeholders/     throwaway stand-ins (git-ignored)
  exports/slide-NN.png     final Instagram slides
  caption.md               written once from manifest "caption"; never overwritten
  contact-sheet.png        all slides in order
```

## Manifest reference (see `content/sample-carousel/manifest.json`)
- `slug`, `topic`, `format` (`portrait` 1080x1350 | `square` 1080x1080 | `story` 1080x1920), optional `export: {width,height}`.
- `brand`: `name` must be `AERELO`; `theme` `night` (default) or `paper`; each slide may override `theme`.
- `image_defaults`: `model`, `quality`, `size` (generation size), optional `complexity`, `prompt_suffix` (shared look), `allow_custom_size`.
- `assets[]`: `id` plus exactly one of `prompt` | `prompt_file` | `existing` (a file already in the repo); optional per-asset `model/quality/size/output`.
- `slides[]` layouts: `cover` (headline, sub?), `content` (title, lead), `stat` (stat, caption, source?), `close` (headline, cta?, sub?), `single` (headline, sub?).
  Common: `label`, `theme`, `footer`, size fields, and `artwork: {asset, mode: "full"|"panel", fit: "cover"|"contain", focus: "50% 40%", overlay: 0..1}`.
- Copy is exact: it is HTML-escaped and `\n` becomes a line break. The manifest is rejected if copy says "AERELO Studios" or contains a price.

## Caching and cost
- An asset is **cached** when the ledger holds a completed request whose model/quality/size/complexity/prompt match and the file still exists. `generate` never re-requests cached assets.
- Editing a prompt marks the asset **stale**. Stale assets are listed but not auto-paid; run `regen`.
- A timeout or dropped connection may still have been billed. The asset is marked **pending** and blocked until you check your OpenAI usage page and pass `--retry-pending`.
- A failed request stops the batch immediately. Nothing is retried (SDK `max_retries=0`).
- Cost shown is an **estimate**: reported token usage x the list prices in `imagegen.PRICING_PER_M` (from the model page, 2026-11-05). It is not an invoice, and no per-image price is assumed. Check your OpenAI dashboard for real spend.

## What was verified against OpenAI docs (2026-11-05) and what was not
Verified: model id `gpt-image-2.6-sunburst`; `POST /v1/images/generations`; result at `data[0].b64_json`; `response_format` is not supported for GPT image models (not sent); `n` 1-10, `stream` default false, `output_format` png/jpeg/webp; standard sizes `1024x1024`, `1536x1024`, `1024x1536`; `quality` low/medium/high/auto.
Not confirmed for 2.6 by the pages available: custom sizes (documented for gpt-image-2/2.5; opt-in here), `xhigh`/`max` quality (documented for 2.5 only; rejected here), the exact `usage` shape (whatever the API returns is stored), your account's access (run `check-access`; a 403/404 on generate is reported and **no other model is substituted**). The 2.6 guide mentions a separate `complexity` setting (low/medium/high, default high); it is only sent if you set it.

## Tests (offline, no key, no spend)
`python3 -m unittest discover -s tools/social/tests -v`
