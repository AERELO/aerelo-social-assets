# AERELO social post rules

Hand this file to any session that makes AERELO social content (images, carousels, reels). Follow it exactly. Check every output against the checklist at the end before delivering.

## 1. Brand name and logo
- The company name is **AERELO**. Never write "Aerelo Studios" or "AERELO Studios" in copy, captions, hashtags, alt text or file names.
- Use the real AERELO logo (globe and orbit-ring mark with the gold dot, from the brand kit or website). Never replace it with typed text.
- Text and logos are rendered as real layouts (HTML/SVG), never baked into generated images.

## 2. Format and sizes
- Instagram and Facebook posts: 1080 x 1350 (4:5), margins 88px.
- Reels and TikTok: 1080 x 1920 (9:16). Keep the top 250px and bottom 340px clear of text (platform UI covers them).
- Reels: captions plus original music, no voiceover unless asked. Stack the CTA button above the logo, never side by side.

## 3. Colour and mix
- Palette: Night #121515, Paper #F7F5F0, Mist #F4F9F9, Gold #F5C13A (the one accent), Teal #08808D / #066B76 / #5BC0CC, Slate #A9B2B4, Ink #0C2027, Ink-2 #3E5257.
- Posts are **not only black and gold**. Mix Night and Paper grounds across the week and allow an occasional teal splash close to the existing design language.
- At most one splash of colour per post (a numeral, icon or rule). Never gold text on Paper; use teal for numerals on Paper.
- Fonts: Jost 300 for headlines, Outfit for body and the wordmark, DM Mono for small labels.

## 4. No duplicated information (most repeated mistake)
- If a carousel slide already shows a counter (for example "01 / 04" top left, or the dots top right), **do not add a numbered teal eyebrow ("01") above the heading**. Content slides carry the counter only.
- Never show the same fact twice on one slide (counter and eyebrow, heading and label saying the same thing, caption repeating the slide verbatim in a second line).
- Read every slide and look for repetition before delivering.

## 5. Labels
- **Cover slides and single posts** keep one short, specific mono label top left (for example "Homepage", "Design principle", "Copywriting", "Booking site"). It tells the reader what the post is about.
- Never use vague filler labels ("Content", "Info", "Post").
- **Closing / CTA slides have no label at all.** Never put "Next" in the top-left corner.
- Do not add decorative text only to fill empty space. If you cannot say what a piece of text is for, remove it.

## 6. Carousel structure
- Cover (topic label, headline, "Swipe" hint), content slides (counter, heading, one supporting line), closing slide (headline, button, footer).
- The orbit line must connect continuously from slide to slide and never end or drop off inside a slide. Formula used so far: y(x) = 1130 - 420u - 60 sin(pi u), u = x / (N x 1080), gold dot at local x = 900 - 130 i.
- The lead text sits directly under the heading; keep the ring away from all text.
- Same typography, spacing, colours and layout on every slide.

## 7. Copy and claims
- **No prices and no "starts at" lines** anywhere (images, captions, videos). Give the content or information, then a simple call to action ("Message us to begin").
- No invented features, guarantees, timelines or results.
- Statistics only from the approved list, always with the source and year, and say "participants" for the Stanford study:
  - Backlinko, 2019: first Google result gets 27.6% of clicks, page two 0.63% (no ratio claim).
  - Google/DoubleClick, 2016: 53% of mobile visitors leave if a page takes over 3 seconds.
  - Deloitte and Google, 2020: a 0.1s faster mobile site lifted retail conversions by 8.4% (mobile retail sites).
  - Stanford Persuasive Technology Lab, 2002: 46.1% of participants judged credibility partly by design.
- Plain, direct tone. Premium, not generic. Avoid AI-looking decoration and repeated templates.

## 8. Layout checks
- Headlines must not wrap awkwardly or overflow; nothing within 84px of the edge.
- Nothing overlaps (text over ring, text over icons, text over check circles).
- Check every rendered file by looking at it, not only by code.

## 9. Production and logging
- Image generation (when used) goes through the OpenAI image API in the repo AERELO/aerelo-social-assets, preferred model gpt-image-2.6-sunburst, no silent model substitution. Never ask the user to paste an API key into chat and never read or print secret files; the user enters keys themselves in the git-ignored .env.images.
- For carousels the user discusses the content, Claude makes the whole carousel and places the artwork without asking approval for each image. The user approves the finished carousel.
- Design in the Claude Design canvas with the saved "Aerelo Studios" design system (that is the design system's name, not brand copy). Use Moda only when asked.
- Cadence: 3 posts a day at 9am, 1pm and 6pm Jamaica time (UTC-5).
- Schedule statics in Metricool (blogId 7155620) for Instagram and Facebook using raw.githubusercontent.com image URLs. Reels can also be scheduled there as Instagram Reel plus Facebook Reel. The user posts TikTok themselves.
- **Every post is logged in the Notion Content Calendar**: publish date and time, platform, Instagram caption, TikTok caption, hashtags, file links, Metricool post ID. New posts start as "Needs review" with a blank date unless a date is given. Statuses: Idea, Draft, Needs review, Rejected, Approved, Scheduled, Posted. Add one or two posts per call because long calls failed before.
- When an image changes after scheduling, regenerate, push to the repo (new folder), update the Metricool post and the Notion row together.

## 10. Pre-delivery checklist
- [ ] Brand name is AERELO everywhere
- [ ] Real logo used
- [ ] No prices
- [ ] Every statistic is on the approved list with source and year
- [ ] No numbered eyebrow on carousel content slides
- [ ] No "Next" or any label on closing slides
- [ ] Cover and single labels are specific, not vague
- [ ] No duplicated information on any slide
- [ ] Orbit line continuous across all slides
- [ ] Night and Paper mix, at most one colour splash per post
- [ ] No overflow, no overlap, margins respected
- [ ] Logged in Notion and, if scheduled, in Metricool
