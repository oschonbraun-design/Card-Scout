# Card Scout v0.4 — SerpApi Edition

Card Scout discovers unusually cheap **active eBay sports-card listings**. It does not claim to know sold-market value; verify exact sold comps before buying.

## Render setup

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn webapp:app`
- Environment variable: `SERPAPI_API_KEY` = your private SerpApi key
- Do **not** put the API key in GitHub.

## Free-plan design

A scan searches one selected player and uses one SerpApi eBay search. This is intentional to conserve the free monthly search allowance. Results are sorted by eBay's newly-listed order, filtered to the chosen price range, then compared against the active-listing median for that search. Listings at least 12% below that median can surface as candidates.

The score is a discovery signal, not a valuation. Different parallels, grades, autos, numbered cards, lots, and variants can have very different values. Always inspect the listing and verify sold comps manually.
