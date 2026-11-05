# AERELO social assets: working instructions

The company name is **AERELO** (never "AERELO Studios") in all copy, captions and file names.

## Existing workflow (unchanged; this file only adds to it)
- Cadence: 3 posts a day (9am / 1pm / 6pm Jamaica time, UTC-5). Every post is logged in the Notion Content Calendar.
- Statics are rendered to PNG in this repo and scheduled in Metricool from `raw.githubusercontent.com` URLs. Scheduling or publishing only happens when the user asks for it.
- Text-only statics can still use `templates/static/carousel_single_generator.py`. Videos use `templates/video/` (run `audit2.py` before rendering any reel). Both are untouched.
- Rules: no prices on social posts; claims only from `claims.md`; one continuity device per carousel (orbit line by default, or another style from `brand/carousel-formats.md`); Night is the default ground, Paper about one post in three; one gold accent; at most one splash of teal; 84px text margins; 9:16 keeps top 250px and bottom 340px clear.
- Brand source of truth is the Project docs: `aerelo-design-theme.md`, `aerelo-design-system.md`, `aerelo-production-workflow.md`.

## Social content with generated artwork (OpenAI Images)
Full docs: `tools/social/README.md`. Entry points: `tools/social/social.py` (posts) and `tools/social/imagegen.py` (single image, access check). Brand look for artwork: `brand/art-direction.md`.
On Windows use `python` (or `py`) where these docs say `python3`.

### Standing authorization (set by the user)
The user has pre-authorized OpenAI image generation **inside the caps in `tools/social/budget.json`**. Do not ask permission per image or per run. The user's approval is for the **finished carousel**, before anything is scheduled or published. If a cap blocks a request, stop and tell the user what the cap is; do not use `--override-budget` unless they say so.

### Where this can run
Generation needs to reach `api.openai.com`. The claude.ai cloud workspace blocks it (verified: HTTP 403 from the proxy), so real generation runs in **Claude Code on the user's own computer, opened in this repo**, where `.env.images` lives. If a run fails with a network 403/connection error, say so, finish everything that does not need the API (manifest, prompts, copy, placeholder render), and stop. Do not look for workarounds.

### When a request is for a carousel or social graphic
1. **Discuss and plan.** Objective, audience, format, hook, slide-by-slide exact copy, visual direction. Follow the brand voice and rules above.
2. **Decide which slides need artwork.** Covers, backgrounds, textures, illustrations and visual concepts only. Never generate text, the logo, slide numbers, CTAs or precise diagrams; those are HTML layouts. Reuse one piece of artwork across slides. Fewer images is better (the budget is 6 per post).
3. **Choose a style:** `python tools/social/social.py pick-style <kind>` (kinds: myth-vs-fact, checklist, before-after, explainer, process, example, statement, build-in-public, stat). Set `"style"` in the manifest; omit for the orbit default. Never repeat a style used in the last 3 posts.
   **Write `content/<slug>/manifest.json`** (`social.py new <slug>` scaffolds it). Write each asset prompt with the recipe in `brand/art-direction.md`: one subject, composition with named empty space where text will go, material and light, palette, one gold accent. The shared art-direction text is appended automatically.
4. **Sanity-check:** `social.py dry-run <slug>` (validates, lists planned requests, no API call).
5. **Generate:** `social.py generate <slug>`. It runs on its own inside the budget, sequentially, and reuses cached assets.
6. **Review the artwork yourself before using it.** Run `social.py review <slug>`, then open each original at full size and apply the review checklist in `brand/art-direction.md` (palette, one gold accent, empty space where text goes, no text/faces/clutter/generic-AI tropes, crops well, set feels consistent). Reject weak images and fix them with `social.py regen <slug> <asset-id>` (max 2 per asset). If it is still weak, change the concept, not just the wording. Never put an image you would not post into a carousel.
7. **Render:** `social.py render <slug>` (never calls the API; free to re-run for any copy or layout change). Read the QA output (overflow, margins, fonts, distortion, dimensions, order) and fix problems. Do not hand over exports that failed QA.
8. **Present for approval:** show `contact-sheet.png` and the key slides, with `caption.md`. Then wait. Scheduling/publishing and logging in the Notion calendar happen only after the user approves, following the existing workflow.

### Changing artwork
- Prompt or art direction edited -> the asset becomes **stale** and is not regenerated automatically; use `regen`.
- `regen` writes a new `-vN` file and keeps the old original. `--overwrite` replaces in place and needs the user's explicit request.
- Never overwrite artwork, delete originals, or bulk-regenerate without being asked.

### Credentials and spend: hard rules
- The key lives only in `OPENAI_API_KEY` or the git-ignored `.env.images`. **Never read `.env.images` or `.env*` files, print or echo the key, dump environment variables, paste keys into chat, or commit credentials.** If the key is missing, tell the user to add it to `.env.images` themselves.
- Never retry a failed or timed-out paid request on your own; report it. Caps live in `tools/social/budget.json` (images per post, per day, regenerations per asset); do not edit them yourself. A pending/unknown request means check the OpenAI usage page first (`--retry-pending` only if the user confirms).
- Do not substitute another model. If `gpt-image-2.6-sunburst` is unavailable, report the error and ask.
- Costs are estimates from reported usage and list prices, not invoices. Quote them as estimates and never as a flat per-image price.
- Do not publish or schedule from this pipeline unless the user asks.

### Brand assets
- Logos come only from `brand/logo/` (`aerelo-mark-small-light.svg`, `aerelo-mark-small-ink.svg`). Never recreate or generate a logo. If those files are missing, say so; `--placeholders` exports are layout tests only and must not be posted.
- Fonts: Jost (headlines, weight 300), Outfit (body/UI), DM Mono (labels), installed with `cd tools/social && npm install`.
- Export sizes: portrait carousel 1080x1350, square 1080x1080, story 1080x1920. These are independent of the generation size (default 1024x1536, `gpt-image-2.6-sunburst`, quality `high`); artwork is cropped (`cover`) or padded (`contain`), never stretched.

### Verify the tooling after changes
`python3 -m unittest discover -s tools/social/tests -v` (offline; no key, no spend).

- Post rules (hand to every session, check before delivering): `brand/post-rules.md`.
