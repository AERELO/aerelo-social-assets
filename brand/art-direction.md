# AERELO art direction for generated artwork

Generated images are **backgrounds, panels, textures and quiet visual concepts**. Headlines, body copy, CTAs, slide numbers,
diagrams, arrows, crossed-out text and the logo are always real layouts, never baked into an image. The look must read as AERELO at a glance and must not
read as "AI art".

## The look
- **Mood:** calm, precise, premium. Quiet confidence, not hustle-flyer noise. "Above the ordinary."
- **Night ground (default):** matte near-black `#121515` / `#181C1C`, fine grain, one soft light source.
- **Paper ground (about 1 post in 3):** warm paper `#F7F5F0`, ink `#0C2027`, soft shadow, no gloss.
- **Colour:** near-black, mist `#F4F9F9`, muted teal `#08808D`. Gold `#F5C13A` is the ONE accent: a single small dot, line or glow, never a fill.
- **Brand motifs (use sparingly, one per image):** a thin tilted orbit line, a needle through an open halo, a small gold sphere on an orbit.
  The real logo is never drawn or generated; it is placed from `brand/logo/`.
- **Space:** at least 40% deliberate empty space, placed where the text will sit. Say which side in the prompt.
- **Realism:** two modes.
  - *Abstract* (covers, backgrounds): materials, light and surfaces (matte stone, brushed metal edge, frosted glass, paper fibre, fine grain).
  - *Example / explainer scenes* (approved 2026-11-05): editorial still life of real objects that stand for the idea (notebook, index cards, a tray of cards, a phone face-down, keys, desk lamp, plant, a shop counter). Photographic, matte, one soft light, a MATCHED SET per post (same surface, light and camera angle, so before/after and process slides feel like one shoot). Same palette and one gold accent. See `brand/carousel-formats.md`.
  - Either mode: no faces, hands, screens or UI, and no text or numbers in the image.

## Never
Neon, lens flare, glossy 3D blobs, cyber grids, circuit boards, rockets, light bulbs, handshakes, generic "digital transformation" imagery, stock-photo
people, faces and hands, charts or fake interfaces, gradients used as decoration, and any text, letters, numbers, logos or watermarks in the picture.

## Prompt recipe (what Claude writes for each asset)
1. **One subject, one idea.** What is in the frame and why it fits this slide's message (a single sentence).
2. **Composition + empty space.** Camera/crop, and "leave the upper-left 45% empty for text".
3. **Material and light.** Surface, texture, one light direction.
4. **Palette.** Name the hex colours that matter; say where the single gold accent is.
5. **Exclusions.** Already covered by `art-direction-prompt.txt`, which is appended automatically to every prompt.

Good: "A single thin teal orbit line curving across a dark matte stone surface, a tiny gold sphere resting on the line in the lower right,
upper-left 45% left empty, soft grazing light from the left, fine grain."
Weak: "Futuristic website design with glowing digital elements and a rocket."

## Sizes
Generate portrait `1024x1536` for 4:5 carousels and stories (cropped with `cover`; use `focus` to choose the crop), `1024x1024` for squares.
Slides that are pure typography or stats need no image at all.

## Review checklist (Claude runs this on every generated original before using it)
- Does it follow the palette, with at most one gold accent?
- Is there real empty space where the text goes?
- Any text, faces, logos, clutter, or generic-AI tropes? If so: reject.
- Would it still look good cropped to 1080x1350 (and 1080x1920 for stories)?
- Do all images in one post feel like a set?
Reject and regenerate at most twice per asset (budget enforces this); if still weak, change the concept, not just the wording.
