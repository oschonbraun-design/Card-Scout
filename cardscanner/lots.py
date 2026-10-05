import re, math
JUNK=("repack","mystery","hot pack","custom","reprint","digital","break spot","pick your team","py t")
HITS=("psa","sgc","bgs","cgc","auto","autograph","rookie","rc","refractor","prizm","chrome","numbered","/10","/25","/50","/99","/199")

def estimate_count(title):
    low=title.lower()
    pats=[r"\blot\s+(?:of\s+)?(\d{1,4})\b",r"\b(\d{1,4})\s*(?:card|cards|ct|count)\b",r"\b(\d{1,4})\s*x\b"]
    for p in pats:
        m=re.search(p,low)
        if m:
            n=int(m.group(1))
            if 2<=n<=5000:return n
    return None

def rank_lots(items):
    for x in items:
        low=x["title"].lower()
        count=estimate_count(x["title"])
        x["estimated_count"]=count
        x["price_per_card"]=round(x["total"]/count,2) if count else None
        x["junk_flags"]=[w for w in JUNK if w in low]
        x["hit_words"]=[w for w in HITS if w in low]
        # Discovery score only: observable listing features, never claimed as market value.
        count_bonus=min(25, math.log2(count)*3.5) if count else 0
        ppc_bonus=max(0,25-min(25,(x["price_per_card"] or 10)*4)) if count else 0
        hit_bonus=min(30,len(x["hit_words"])*6)
        penalty=45 if x["junk_flags"] else 0
        x["lot_interest"]=max(0,min(100,round(20+count_bonus+ppc_bonus+hit_bonus-penalty)))
    return sorted(items,key=lambda x:(x["lot_interest"],-(x["price_per_card"] or 9999)),reverse=True)
