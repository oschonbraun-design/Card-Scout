# Card Scout v1.9 — CompSniper history

Uses `SERPAPI_API_KEY` for active eBay listings and `COMPSNIPER_API_KEY` for sold comps. `SOLDGRAPH_KEY` is not used.

Deploy by uploading ZIP contents to your existing GitHub repository root; Render rebuilds automatically.

- `/find-deals` evaluates candidate listings with CompSniper historical sold results.
- `/analyze` retrieves 1, 2, or 5 pages of CompSniper's up-to-three-year eBay research results (50 rows/page).
- Exact single-unit matches only. Historical comps shown; last-180-day sales drive current valuation.
- Each page costs one CompSniper API request; free plan is limited.
- This is **not** an all-time sales database and results depend on seller titles and provider coverage.
- No live CompSniper API test was possible without your private Render key.
