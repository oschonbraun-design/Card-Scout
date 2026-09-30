# Card Deal Scanner v0.1

A conservative eBay sports-card scanner designed to flag genuinely underpriced fixed-price listings while avoiding false matches between similar parallels (for example, **Mosaic Stained Glass vs Stained Glass Jumbo**).

## What it does

- Searches eBay active Buy It Now listings for a configurable player watchlist.
- Defaults to a $75-$150 scan window (edit `config.json`).
- Parses year, product, parallel, rookie status, autograph status, serial numbering, grader/grade and card number from titles.
- Gives every identification a confidence score and **refuses to score low-confidence cards**.
- Treats Stained Glass/Jumbo and other parallel names as different fingerprints.
- Compares only against comps with the **same exact fingerprint**.
- Uses median recent comps, not the highest comp.
- Estimates discount and after-fee resale profit.
- Sends console and optional Discord alerts.
- Remembers eBay item IDs in SQLite so you are not repeatedly alerted about the same listing.

## Important data limitation

As of Sept. 30, 2026, eBay's Browse API is for active purchasable inventory. eBay's official sold-history Marketplace Insights API is restricted and is not open to new users. This project therefore does **not** scrape eBay or 130point and does not pretend active asking prices are sold comps.

Version 0.1 uses `data/comps.csv` as the verified sold-comp provider. Add exact sold transactions you have verified (for example using eBay's own research tools or a comp service you are permitted to use). The comp provider is isolated so an approved sold-data API can be added later without changing the scanner/scoring logic.

## Setup

1. Create an eBay Developers account and production application credentials.
2. Copy `.env.example` values into environment variables (do not put secrets in the code).
3. Add verified exact-card comps to `data/comps.csv`.
4. Optional: create a Discord webhook and set `DISCORD_WEBHOOK_URL`.
5. Run from this directory:

```bash
export EBAY_CLIENT_ID='...'
export EBAY_CLIENT_SECRET='...'
export DISCORD_WEBHOOK_URL='...'
python3 scanner.py
```

Continuous scan:

```bash
python3 scanner.py --loop
```

The default interval is 300 seconds. Stay within your API permissions/rate limits and eBay's applicable API terms.

## Adding a comp

The fingerprint format is:

`year|product|player|parallel|rc-if-rookie|grader|grade|card-number`

Example:

```csv
fingerprint,sold_price,sold_date,source,source_url
2024|panini prizm|drake maye|silver prizm|rc|psa|10|,165,2026-09-20,manual,
2024|panini prizm|drake maye|silver prizm|rc|psa|10|,172,2026-09-24,manual,
2024|panini prizm|drake maye|silver prizm|rc|psa|10|,168,2026-09-28,manual,
```

A listing is not scored unless it has at least 3 exact recent comps and meets the configured identity-confidence threshold.

## Default deal logic

- WATCH: adjusted discount >= 20%
- GOOD: >= 25%
- STEAL: >= 30%
- Minimum exact comps: 3
- Minimum match confidence: 88%
- Minimum estimated profit: $15
- Estimated resale fee rate: 13% (editable; use your actual selling costs)
- Estimated outbound shipping: $5

These are screening thresholds, not guarantees of profit. Taxes, seller fees, shipping, returns, condition, authenticity and market movement can change the result.

## Why this is safer than naive title matching

The parser explicitly checks longer/more-specific parallel names before shorter ones, so `stained glass jumbo` is not silently reduced to `stained glass`. Ambiguous Stained Glass titles are penalized and marked for manual image verification. The same principle can be extended to Prizm/Select/Bowman parallel families.

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Best next upgrades

1. Add image-assisted identification for listings whose title is incomplete.
2. Add a licensed/approved sold-data provider implementing the same comp interface.
3. Build a small web dashboard showing rejected listings and why they were rejected.
4. Add separate liquidity rules by sport/player/card type.
5. Add Telegram/SMS/email alert adapters if desired.

## Website mode (no comp database)

`webapp.py` is a browser dashboard designed for discovery rather than valuation. It searches the configured liquid players, compares each new candidate with the active-listing prices returned by the same eBay search, and ranks unusually cheap listings. It deliberately does **not** claim those prices are true market values. Verify sold comps yourself before buying.

### Run the website

1. Create a free eBay Developers account/application and copy your production App ID and Cert ID.
2. Copy `.env.example` values into environment variables named `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`.
3. Install: `pip install -r requirements.txt`
4. Start: `python webapp.py`
5. Open `http://localhost:8000`.

### Put it online

The folder is deployment-ready for a basic Python web host. Set the same two environment variables in the host's secret/environment settings and use `python webapp.py` as the start command (the included `Procfile` already specifies this). Do not put your eBay secret in browser-side JavaScript or commit it to a public repository.

### Ranking limitations

An active-listing median is not a sold comp. Asking prices can be inflated and broad searches can mix parallels. The dashboard therefore exists to surface candidates for manual checking, not to tell you what to buy. Variant warnings from the identity parser are shown directly on cards.
