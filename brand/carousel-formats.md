# AERELO carousel format library (draft, 2026-11-05)

Research basis: secondary sources only (vendor blogs: SocialRails, CreatorFlow, ContentStudio, SocialChamp, Metricool best-practices page). Their engagement numbers are unverified, so **none of them may be used as a claim in a post**. What they agree on is used here as structure, not as data.

## What the sources agree on
- Educational carousels (tips, how-tos, frameworks, before/afters) get saved far more than promotional ones.
- Slide 1 carries the carousel: a specific promise or question. Slide 2 should also work as a second hook (the feed can re-show a carousel starting there).
- Roughly 5-8 slides is the safe range; fewer, sharper slides beat 10 diluted ones. One idea per slide.
- Service businesses do best with: before/after, "what's included", "how we work" process, common misconceptions.
- Same template, same logo position, 2-3 colours, 2 fonts on every slide (AERELO already does this).

## Formats to rotate (with the image each one wants)

| # | Format | Slide pattern | Generated image that helps |
|---|---|---|---|
| 1 | **Myth vs fact** | Cover (the myth) / Myth 1 -> Fact / Myth 2 -> Fact / close | One illustrative object per myth (a crossed-out idea is built in HTML, not the image) |
| 2 | **Before / after** | Cover / "Before" scene / "After" scene / what changed (3 bullets) / close | Two matching scenes: cluttered vs calm desk, same angle and light |
| 3 | **How it works (process)** | Cover / step 1..4 / close | One small still-life object per step (notebook, calendar card, key, phone) in the same set |
| 4 | **Checklist** | Cover / 3-5 checks / "score yourself" / close | Mostly HTML; one cover image |
| 5 | **Explainer (what is X)** | Cover / the problem / the idea / example / what to do / close | A scene that shows the idea (e.g. a handwritten-style contact list vs one organised card tray) |
| 6 | **Example / case breakdown** | Cover / the situation / what we did / result / close | A scene of the business type (salon counter, workshop bench), no faces |
| 7 | **One stat** | Cover / the stat (approved list only) / why it matters / what to do / close | Optional texture only |
| 8 | **Build in public** | Cover / what we're building / the decision / what's next / close | Behind-the-scenes still life of the work surface |

Rotation rule of thumb: educational formats (1, 2, 3, 5) most weeks; one build-in-public or example post per week; stats only from the approved list.

## Proposed art-direction change (needs your OK before I edit `art-direction.md`)
Today the art direction bans people, screens, UI and anything not abstract. To make examples and explainers possible while staying on-brand:

- **Allow:** editorial still-life scenes of real objects that stand for the idea (notebook, index cards, a tray of cards, a phone face-down, a desk lamp, keys, a plant, a counter). Photographic, matte, one soft light source, Night or Paper ground, one gold accent, 40% empty space for text.
- **Allow:** a matched *set* (same table, same light, same camera angle) across slides, so a before/after or process feels like one shoot.
- **Still ban:** faces and hands, text or numbers in the image, logos, screens with UI, charts, stock-photo clichés (handshakes, light bulbs, rockets), neon, glossy 3D.
- **Diagrams, lists, arrows, crossed-out text, numbers:** always HTML layouts on top of the image, never generated.

## Next step
Pick one format above for the next carousel. I will draft the slide copy, generate a small matched set of scene images (inside your caps), review them, render, and show you the finished carousel.


## Carousel styles (approved 2026-11-05)
Set with the manifest key `"style"`; omit for the default orbit look. Samples: `content/_style-samples/`.

| Style | Look | Use for | Images |
|---|---|---|---|
| orbit (default) | Orbit line + gold dot runs across slides | Covers, quiet statements, anything | optional |
| cards | Tilted paper cards on a ground; give each slide `theme` night/paper alternately | Myth vs fact, Q&A | none |
| spec | DM Mono spec sheet: ruled rows, gold tick boxes | Checklists, audits | none |
| pano | One 1536x1024 image across two slides (artwork `mode: pano`, `part`, `parts`) | Before/after, journeys | 1 wide |
| wireframe | Hairline browser mock; the discussed block is outlined in gold (slide key `wire`: phone, form, hours, note) | Website layout explainers | none |
| polaroid | Tilted print frame with mono caption (artwork `zoom`, `origin`, `focus` crop one photo) | Examples, before/after photos | 1-2 |
| zoom | Cover shows the whole scene; later slides crop tighter | One rich scene, detail by detail | 1 |
| editorial | Big Jost headlines, gold underline on key words (slide key `hl`) | Statements, myths | none |

Dropped: numeral (big numerals). Rule: never use the same style as any of the last 3 posts (`pick-style` checks).
