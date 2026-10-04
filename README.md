# Card Scout v0.5
Free-text eBay sports-card discovery using SerpApi.

## Render
Build: `pip install -r requirements.txt`
Start: `gunicorn webapp:app`
Environment: `SERPAPI_API_KEY` (secret)

## v0.5
- Search any player or eBay-style sports-card query.
- Up to 200 results requested per search.
- Grid shows many listings at once.
- Newest, lowest-price, or ending-soon sorting.
- $75–$150 defaults remain editable.
- Shows landed price, shipping, condition, seller feedback, listing date when supplied.
- Removes the misleading cross-card active-median/deal percentage.
- One submitted search = one SerpApi search request.
- Always verify exact sold comps before buying.
