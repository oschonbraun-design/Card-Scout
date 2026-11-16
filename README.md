# Card Scout v2.1 — Discovery Finder

Scan NBA, NFL, or MLB without knowing a specific card. A scan queries up to three player searches via SerpApi and attempts to verify up to eight distinct candidate card families against CompSniper. Players can be selected automatically or narrowed using the optional search field.

This is not a comprehensive scan of eBay. No active listing asking price is used as a comp. The website will flag only cards with three exact recent sold matches and sufficient projected profit after estimated fees; no match is not proof of no deal. CompSniper request quotas apply. The free tier is limited and scanning can consume several requests.

Render variables: SERPAPI_API_KEY and COMPSNIPER_API_KEY. Build: pip install -r requirements.txt. Start: gunicorn webapp:app.

**Known limitation:** Live CompSniper API calls cannot be tested without access to your private Render environment. Provider schema and authorization must be verified with a live test before relying on results for purchases. A title-based matcher cannot guarantee image-level variant identity. Always verify card photo, listing details, recent sales and seller before purchasing.
