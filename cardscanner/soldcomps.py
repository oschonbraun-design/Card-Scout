import re, statistics
from urllib.parse import urlencode
from .opportunity import fingerprint, similarity

NOISE=re.compile(r"\b(lot|repack|digital|custom|reprint)\b",re.I)

def comp_query(title):
    # eBay titles are already keyword-rich; remove sales fluff while preserving card identity.
    q=re.sub(r"\b🔥|💎|INVEST|HOT|L@@K|WOW\b"," ",title,flags=re.I)
    q=re.sub(r"\s+"," ",q).strip()
    return q[:180]

def ebay_sold_url(query):
    return "https://www.ebay.com/sch/i.html?"+urlencode({"_nkw":query,"LH_Sold":"1","LH_Complete":"1"})

def evaluate(active_title, active_total, sold_rows, player):
    target=fingerprint(active_title,player)
    matches=[]
    for row in sold_rows:
        if NOISE.search(row["title"]): continue
        fp=fingerprint(row["title"],player)
        sim=similarity(target,fp)
        # Stronger threshold than active-listing opportunity mode.
        if sim>=0.72:
            z=dict(row); z["similarity"]=round(sim*100); matches.append(z)
    matches.sort(key=lambda x:x["similarity"],reverse=True)
    if not matches:
        return {"status":"manual","matches":[],"median":None,"discount":None,"confidence":0}
    vals=[x["total"] for x in matches[:12]]
    med=statistics.median(vals)
    discount=(med-active_total)/med*100 if med else 0
    confidence=min(99, round((sum(x["similarity"] for x in matches[:8])/min(8,len(matches)))*(.75+.25*min(1,len(matches)/5))))
    status="strong" if len(matches)>=3 and confidence>=80 and discount>=20 else ("possible" if discount>=10 else "average")
    return {"status":status,"matches":matches[:12],"median":round(med,2),"discount":round(discount,1),"confidence":confidence}
