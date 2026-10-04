import re, statistics
from .identity import parse_identity

BAD_WORDS=("lot","repack","digital","custom","reprint")

def _grade_bucket(title):
    low=title.lower()
    m=re.search(r"\b(psa|sgc|bgs|cgc|beckett)\s*(10|9\.5|9|8\.5|8)\b",low)
    return (m.group(1),m.group(2)) if m else ("raw","")

def fingerprint(title, player):
    ident,conf=parse_identity(title,player)
    grader,grade=_grade_bucket(title)
    return {
      "year":ident.year or "", "product":ident.product or "", "parallel":ident.parallel or "",
      "auto":bool(ident.autograph),"rookie":bool(ident.rookie),"serial":ident.serial or "",
      "grader":grader,"grade":grade,"card_number":ident.card_number or "","confidence":conf
    }

def similarity(a,b):
    # Hard mismatches that commonly create terrible comparisons.
    for k in ("grader","grade","auto"):
        if a[k]!=b[k]: return 0
    if a["serial"] and b["serial"] and a["serial"]!=b["serial"]: return 0
    score=0; possible=0
    weights={"year":2,"product":3,"parallel":4,"serial":3,"card_number":2,"rookie":1}
    for k,w in weights.items():
        if a[k] or b[k]:
            possible+=w
            if a[k] and b[k] and a[k]==b[k]: score+=w
    return score/possible if possible else 0

def rank_opportunities(items, player):
    enriched=[]
    for x in items:
        y=dict(x); y["fp"]=fingerprint(y["title"],player)
        low=y["title"].lower()
        y["excluded"]=any(w in low for w in BAD_WORDS)
        enriched.append(y)
    for x in enriched:
        peers=[y for y in enriched if y is not x and not y["excluded"] and similarity(x["fp"],y["fp"])>=0.72]
        prices=[y["total"] for y in peers]
        x["peer_count"]=len(prices); x["reference"]=None; x["opportunity_score"]=None; x["discount"]=None
        if len(prices)>=2 and not x["excluded"]:
            ref=statistics.median(prices)
            disc=(ref-x["total"])/ref*100 if ref else 0
            # Conservative: only rank positive outliers; confidence and peer count cap the score.
            confidence=min(1.0,x["fp"]["confidence"])
            support=min(1.0,len(prices)/5)
            score=max(0,min(100,disc*2.2*confidence*(0.65+0.35*support)))
            x["reference"]=round(ref,2); x["discount"]=round(disc,1); x["opportunity_score"]=round(score)
    return sorted(enriched,key=lambda x:(x["opportunity_score"] is not None,x["opportunity_score"] or -1,-x["total"]),reverse=True)
