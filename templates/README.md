# AERELO production templates

Static (Paper / Night): `static/carousel_single_generator.py` builds 1080x1350 singles and N-slide carousels with the continuous orbit line, then renders PNGs with headless Chrome. Functions: `single_ring`, `carousel`, `render`.

Video (9:16, 1080x1920): `video/eng.py` is the scene engine (items with entrance direction, easing, timing; `setT(t)` renders any frame). Example scene files: speed.py (stat reel), myth.py (Paper), checks.py (checklist), stan.py (Paper stat), two.py (kinetic text). `mus.py` writes original synthesized music from a small JSON spec. `audit2.py` checks text margins (84px) and overlaps before rendering — run it on every new reel.

Rules: no prices on social posts; claims only from claims.md; keep top 250px and bottom 340px of 9:16 clear; stack CTA above logo, never side by side.
