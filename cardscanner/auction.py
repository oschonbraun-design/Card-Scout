import re, math

def time_to_minutes(raw):
    if not raw: return None
    s=str(raw).lower().strip()
    total=0.0
    patterns=[("d",1440),("day",1440),("h",60),("hr",60),("hour",60),("m",1),("min",1),("s",1/60),("sec",1/60)]
    # Handles "2d 3h", "3h 12m", "45m", etc.
    found=False
    for num,unit in re.findall(r"(\d+(?:\.\d+)?)\s*(days?|d|hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b",s):
        found=True
        if unit.startswith("d"): mult=1440
        elif unit.startswith("h"): mult=60
        elif unit.startswith("m"): mult=1
        else: mult=1/60
        total+=float(num)*mult
    return total if found else None

def rank_auctions(items):
    # Auction score = low current total relative to this result set + urgency + bid pressure.
    prices=sorted(x["total"] for x in items)
    n=max(1,len(prices)-1)
    for x in items:
        mins=time_to_minutes(x.get("time_left"))
        x["minutes_left"]=mins
        try: bid_count=int(x.get("bids") or 0)
        except: bid_count=0
        if mins is None: urgency=.10
        elif mins<=15: urgency=1.0
        elif mins<=60: urgency=.92
        elif mins<=180: urgency=.82
        elif mins<=360: urgency=.70
        elif mins<=720: urgency=.55
        elif mins<=1440: urgency=.40
        else: urgency=.12
        cheaper=sum(1 for p in prices if p < x["total"])
        low_price=1-(cheaper/n if n else 0)
        bid_factor=1/(1+bid_count/10)
        # Short time is most important; low relative price is next.
        x["auction_score"]=round(100*(.52*urgency+.38*low_price+.10*bid_factor))
        x["bid_count"]=bid_count
        x["price_percentile"]=round(low_price*100)
    return sorted(items,key=lambda x:(x["auction_score"],-(x.get("minutes_left") or 10**9)),reverse=True)
