def score_deal(listing, stats, cfg):
    if not stats or stats["count"] < cfg["minimum_comps"]: return None
    if listing.confidence < cfg["minimum_match_confidence"]: return None
    market=stats["median"]
    landed=listing.landed_cost
    discount=(market-landed)/market if market else 0
    resale_net=market*(1-cfg["estimated_resale_fee_rate"])-cfg["estimated_outbound_shipping"]
    profit=resale_net-landed
    volatility=(stats["high"]-stats["low"])/market if market else 1
    confidence_penalty=max(0, (0.25-volatility))*0 + max(0, volatility-0.35)*0.15
    adjusted=discount-confidence_penalty
    t=cfg["deal_thresholds"]
    level = "STEAL" if adjusted>=t["steal"] else "GOOD" if adjusted>=t["good"] else "WATCH" if adjusted>=t["watch"] else "PASS"
    if profit < cfg["minimum_estimated_profit"]: level="PASS"
    return {"level":level,"discount":discount,"adjusted_discount":adjusted,"market":market,
            "profit":profit,"volatility":volatility,"comp_count":stats["count"]}
