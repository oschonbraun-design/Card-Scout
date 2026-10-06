# Card Scout v1.4 — The Card API + Soldgraph

- SerpApi finds current eBay listings.
- Analyze Sold Comps uses The Card API first for recent transactions.
- If recent evidence is thin, Card Scout automatically queries Soldgraph's eBay sold endpoint and polls pending search jobs until complete.
- Soldgraph Best Offer rows are excluded because Soldgraph does not verify the accepted offer amount.
- Exact-card matching rejects grade/grader, auto, year/product, parallel, serial-numbering, and card-number mismatches when identifiable.
- One exact sold match can create a clearly provisional score; 2+ matches provide stronger evidence.
- No trustworthy matches = no score. Active asking prices are never used as the market comp.
- Render needs SERPAPI_API_KEY, THECARDAPI_KEY, and SOLDGRAPH_KEY.
