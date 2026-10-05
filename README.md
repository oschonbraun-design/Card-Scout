# Card Scout v1.0
## Singles Scout
- Removes the misleading active-listing Opportunity Score.
- Newest / lowest / ending-soon discovery.
- Auctions show **Auction Watch**, which is urgency/current-price ranking only.
- Every listing has View Listing, eBay Sold, 130point and Card Ladder links.
- Enter a personally verified comp and Card Scout calculates exact % below/above comp.

## Lot Scout
- Dedicated lot search.
- Estimates card count from titles when possible.
- Calculates price per card.
- Highlights PSA/SGC/BGS, auto, rookie, refractor, numbered and similar signals.
- Warns on repack/mystery/custom/reprint/digital/break-style listings.
- Lot Interest is a discovery score based on observable listing features, not claimed market value.

## Deploy
Same Render service and same `SERPAPI_API_KEY`.
Build: `pip install -r requirements.txt`
Start: `gunicorn webapp:app`
