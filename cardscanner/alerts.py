import json, os
from urllib.request import Request, urlopen

def format_alert(listing, result, stats):
    ident=listing.identity
    uncertainty=(" | VERIFY: "+"; ".join(ident.uncertainty)) if ident.uncertainty else ""
    return (f"{result['level']} — {listing.player}\n{listing.title}\n"
            f"Buy: ${listing.landed_cost:.2f} landed | Exact-comp median: ${result['market']:.2f} "
            f"({result['comp_count']} comps) | Discount: {result['discount']:.1%}\n"
            f"Est. resale profit: ${result['profit']:.2f} | Match confidence: {listing.confidence:.0%}{uncertainty}\n{listing.url}")

def send_alert(message):
    print("\n"+message+"\n")
    url=os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url: return
    req=Request(url, data=json.dumps({"content":message[:1900]}).encode(), headers={"Content-Type":"application/json"})
    with urlopen(req, timeout=15): pass
