import json, os, re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class SerpApiEbayClient:
    def __init__(self):
        self.api_key=os.getenv("SERPAPI_API_KEY","").strip()
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY is not set in Render.")

    @staticmethod
    def _shipping(v):
        if isinstance(v,dict):
            try: return float(v.get("extracted") or 0)
            except (TypeError,ValueError): return 0.0
        if not v or "free" in str(v).lower(): return 0.0
        m=re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)",str(v))
        return float(m.group(1)) if m else 0.0

    def search(self, query, min_price, max_price, limit=200, sort="newest", buying_format="bin"):
        sop={"newest":"10","lowest":"15","ending":"1"}.get(sort,"10")
        params={"engine":"ebay","ebay_domain":"ebay.com","_nkw":query,
                "_ipg":str(min(200,max(25,int(limit)))),"_sop":sop,
                "api_key":self.api_key,"_udlo":str(min_price),"_udhi":str(max_price)}
        if buying_format == "bin": params["buying_format"]="BIN"
        elif buying_format == "auction": params["buying_format"]="Auction"
        req=Request("https://serpapi.com/search.json?"+urlencode(params),
                    headers={"User-Agent":"CardScout/0.8"})
        with urlopen(req,timeout=35) as r: obj=json.load(r)
        if obj.get("error"): raise RuntimeError(obj["error"])
        out=[]
        for x in obj.get("organic_results",[]):
            price=x.get("price") or {}
            if not isinstance(price,dict) or price.get("extracted") is None: continue
            try: p=float(price["extracted"])
            except (TypeError,ValueError): continue
            ship=self._shipping(x.get("shipping")); total=p+ship
            if total < min_price or total > max_price: continue
            seller=x.get("seller") or {}
            try: feedback=float(seller.get("positive_feedback_in_percentage")) if seller.get("positive_feedback_in_percentage") is not None else None
            except (TypeError,ValueError): feedback=None
            try: reviews=int(seller.get("reviews")) if seller.get("reviews") is not None else None
            except (TypeError,ValueError): reviews=None
            out.append({
                "item_id":str(x.get("product_id","")), "title":x.get("title",""),
                "url":x.get("link",""), "image":x.get("thumbnail",""),
                "price":round(p,2),"shipping":round(ship,2),"total":round(total,2),
                "condition":x.get("condition",""),"seller":seller.get("username",""),
                "buying_format":x.get("buying_format",""),"buying_format_text":x.get("buying_format_text",""),
                "bids":(x.get("bids") or {}).get("count") if isinstance(x.get("bids"),dict) else x.get("bids",""),
                "time_left":(x.get("bids") or {}).get("time_left","") if isinstance(x.get("bids"),dict) else x.get("time_left",""),
                "best_offer":bool(x.get("best_offer")) or ("best offer" in str(x).lower()),
                "feedback":feedback,"reviews":reviews,"listing_date":x.get("listing_date",""),
                "new_listing":bool(x.get("new_listing")),"sponsored":bool(x.get("sponsored")),
                "quantity_sold":x.get("quantity_sold","")
            })
        # exact URL/item dedupe while preserving eBay's requested sort
        seen=set(); clean=[]
        for x in out:
            k=x["item_id"] or x["url"] or x["title"]
            if k in seen: continue
            seen.add(k); clean.append(x)
        return clean

    def sold_search(self, query, limit=100):
        params={"engine":"ebay","ebay_domain":"ebay.com","_nkw":query,
                "_ipg":str(min(200,max(25,int(limit)))),"show_only":"Sold",
                "api_key":self.api_key}
        req=Request("https://serpapi.com/search.json?"+urlencode(params),
                    headers={"User-Agent":"CardScout/0.9"})
        with urlopen(req,timeout=35) as r: obj=json.load(r)
        if obj.get("error"): raise RuntimeError(obj["error"])
        out=[]
        for x in obj.get("organic_results",[]):
            price=x.get("price") or {}
            if not isinstance(price,dict) or price.get("extracted") is None: continue
            try: p=float(price["extracted"])
            except (TypeError,ValueError): continue
            ship=self._shipping(x.get("shipping"))
            out.append({"title":x.get("title",""),"price":round(p,2),
                        "shipping":round(ship,2),"total":round(p+ship,2),
                        "url":x.get("link",""),"sold_date":x.get("sold_date") or x.get("listing_date","")})
        return out
