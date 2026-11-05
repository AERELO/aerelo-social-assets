# AERELO logo files (supplied by you; never generated or redrawn)

The renderer needs these two files here. They are the filenames the existing static generator
already uses (it currently looks for them in a local `/home/claude/work/logo/` folder that is not in git):

| File | Used on |
|---|---|
| `aerelo-mark-small-light.svg` | Night slides (light mark) |
| `aerelo-mark-small-ink.svg`   | Paper slides (ink mark) |

Until they are added, `social.py render` refuses to produce real exports. `--placeholders` swaps in a
clearly-labelled dashed "LOGO" stand-in so you can still check layout. Exports made that way are marked
"NOT FINAL" on the contact sheet and in `source/qa-report.json`.

The design theme also lists `aerelo-profile-*.png` and `aerelo-full-logo-*.png`; add them here too if you want
them versioned with the repo (the carousel footer only needs the two SVGs above).
