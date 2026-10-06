# Card Scout v1.5 — Soldgraph Only

Active listings come from SerpApi. Sold comps come only from Soldgraph.
The Card API is completely removed from the application path and is not required.

## Render environment
Required:
- SERPAPI_API_KEY
- SOLDGRAPH_KEY

THECARDAPI_KEY may be deleted from Render, but leaving an unused variable does not affect v1.5.

## Accuracy
- Active asking prices are never used as market comps.
- Soldgraph Best Offer rows are excluded because the displayed price is not a verified accepted-offer price.
- Exact-card matching rejects obvious grader/grade, auto, year/product, parallel, serial-numbering and card-number mismatches when identifiable.
- One matching sale is provisional; two or more matches are stronger evidence.
- No trustworthy match means no Opportunity Score.
- Soldgraph searches can return pending jobs; Card Scout polls the job with long polling before reading results.

## Usage
Scan active eBay listings normally, then click Analyze Sold Comps on a candidate. This intentionally avoids spending a Soldgraph request on every active listing because the free Soldgraph plan has a limited monthly allowance.

Same Render build/start:
- `pip install -r requirements.txt`
- `gunicorn webapp:app`
