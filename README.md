# Card Scout v1.3 — Automatic Sold Comps

SerpApi finds live eBay listings. The Card API analyzes actual completed eBay sales.

Each Singles result has **Analyze Sold Comps**. Card Scout filters sold results conservatively and refuses to score when it cannot find enough close matches. It hard-rejects mismatches in grading company/grade, autograph status, year, product, parallel, serial print run and card number when those fields are identifiable. The analysis page shows every sold listing used so you can audit the result.

Opportunity Score is based on percentage below the median of close, confirmed sold matches, adjusted for match quality and number of comps. Cards at/above sold comp score 0. Fewer than two close matches produces **No score — insufficient reliable comps**.

Environment variables on Render:
- `SERPAPI_API_KEY`
- `THECARDAPI_KEY`

Build: `pip install -r requirements.txt`
Start: `gunicorn webapp:app`
