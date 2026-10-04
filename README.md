# Card Scout v0.6
Sports-card listing discovery through SerpApi.

## Main behavior
- Free-text player/search query.
- Buy It Now is the default; unfinished auctions no longer dominate normal searches.
- Optional Auctions and All Listings modes.
- Auction mode automatically uses Ending Soon when Newest was selected.
- Newest / Lowest Price / Ending Soon sort controls.
- Up to 200 results requested per submitted search.
- Shows item + shipping total, image, seller data, condition, Best Offer when detected, and auction metadata when supplied.
- No market-value or fake deal percentage. Verify exact sold comps before buying.

## Render
Build: `pip install -r requirements.txt`
Start: `gunicorn webapp:app`
Secret environment variable: `SERPAPI_API_KEY`
