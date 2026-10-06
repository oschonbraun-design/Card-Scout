# Card Scout v1.6 — Soldgraph Only, Clean Build

This build removes all Card API and manual Comp Library UI/code from the website.

- SerpApi: active eBay listings only.
- Soldgraph: sold comps only.
- No active asking-price median is ever used as a market comp.
- Soldgraph accepted Best Offer rows are excluded because Soldgraph documents that the displayed amount is the asking price, not the verified paid price.
- Exact-card matching is stricter: known active year/product/parallel/serial/card number must also be identifiable and matching in a sold title; grade/grader and auto status are hard gates.
- Up to 200 recently-sold rows are requested in one Soldgraph search.
- Robust outlier filtering is applied before the median comp.
- One exact sale is provisional and can never create a high Opportunity Score; 2+ matching sales are required for a strong deal.
- The analysis page displays the sold listings used so the result can be audited.

Render environment required: `SERPAPI_API_KEY` and `SOLDGRAPH_KEY`.
`THECARDAPI_KEY` is not referenced anywhere in this build.
