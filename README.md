# Card Scout v0.9 — Sold Comp Check
- Keeps v0.8 live BIN and auction discovery.
- Adds **Analyze eBay Sold Comps** to every listing.
- Uses the existing `SERPAPI_API_KEY`; no new account/key.
- On demand, searches eBay sold results and strictly matches card identity.
- Shows matched sold median, discount vs sold reference, match confidence, and actual matched sold rows.
- Strong Candidate requires >=3 matches, >=80% confidence, and >=20% below matched sold median.
- If sold automation is unavailable or matching is weak, it refuses to invent a value and provides an exact eBay Sold Search link.
- Adds one-click 130point verification.
- Each comp analysis uses an additional SerpApi search, so it is intentionally on-demand to conserve quota.
