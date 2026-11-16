# Card Scout v2.0 — Under-Comps Finder

Deploy to Render with the existing GitHub project. Required environment variables: `SERPAPI_API_KEY` and `COMPSNIPER_API_KEY`. `SOLDGRAPH_KEY` is not used.

## What changed
- Removed v1.9's mistaken requirement for a parallel or card number: ordinary base cards are now eligible.
- Search uses shorter CompSniper queries to avoid requiring every title keyword to match.
- Strict comparison still rejects known mismatches in year, product, parallel, grade, autograph, numbering, and player.
- Under-Comps Finder examines the returned active listings and analyzes up to eight distinct low-priced card identities, flags only those clearing 25% below sold median, $15 estimated net profit, and 20% ROI.
- All available matched sales are shown in the comp audit. Current value requires at least three matching sales within 180 days.

## Limitations
- A single scan is not a comprehensive market crawl. CompSniper historical requests are limited by your plan and the API's results. Eight candidates can use eight requests, and more if you open separate comp pages.
- No live integration test was possible without the private API keys; review Render logs and returned API errors if your provider's response shape differs.
- Title matching is conservative but cannot verify image-only parallels, altered cards, hidden condition, or listing fraud. Confirm photos and sales manually before purchase.
