# Card Scout v1.1 — Verified Comp Opportunity Scores

## What changed
- Opportunity Score is back, but **only** when the browser has a saved verified comp for the exact card identity.
- No comp = `Comp Needed`; incomplete identity = `Verify Identity`.
- Comp Library persists in browser localStorage, so no Card Ladder password/API key is stored.
- Save Last Sale, Recent Average, CL Value, sale count and verification date.
- Reference prefers CL Value + recent average, then CL Value, then recent average, then last sale.
- Score is reduced for stale comps and weak evidence. Above-comp listings score 0.
- Hard identity key separates player, year, product, parallel, auto/non-auto, serial denominator, grader, grade and card number when available.
- Card Ladder workflow: Copy CL Search -> Open Card Ladder -> verify exact card/same grade -> save evidence once.
- Lot Scout and Auction Watch remain.

## Accuracy rule
Card Scout never creates a market-value Opportunity Score from active asking prices. A score requires a user-verified comp. Ambiguous titles are not silently treated as another parallel/grade.

## Deploy
Same Render service and `SERPAPI_API_KEY`.
Build: `pip install -r requirements.txt`
Start: `gunicorn webapp:app`
