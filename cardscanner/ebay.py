import base64, json, os, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .models import Listing

class EbayBrowseClient:
    def __init__(self, marketplace="EBAY_US"):
        self.client_id=os.getenv("EBAY_CLIENT_ID", "")
        self.client_secret=os.getenv("EBAY_CLIENT_SECRET", "")
        self.marketplace=marketplace; self._token=""; self._expires=0
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET environment variables.")

    def _get_token(self):
        if self._token and time.time() < self._expires-60: return self._token
        auth=base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        data=urlencode({"grant_type":"client_credentials","scope":"https://api.ebay.com/oauth/api_scope"}).encode()
        req=Request("https://api.ebay.com/identity/v1/oauth2/token", data=data,
                    headers={"Authorization":f"Basic {auth}","Content-Type":"application/x-www-form-urlencoded"})
        with urlopen(req, timeout=20) as r: obj=json.load(r)
        self._token=obj["access_token"]; self._expires=time.time()+int(obj.get("expires_in",7200)); return self._token

    def search(self, query, player, min_price, max_price, limit=50):
        params={"q":query,"limit":str(limit),"filter":f"price:[{min_price}..{max_price}],priceCurrency:USD,buyingOptions:{{FIXED_PRICE}}"}
        url="https://api.ebay.com/buy/browse/v1/item_summary/search?"+urlencode(params)
        req=Request(url, headers={"Authorization":f"Bearer {self._get_token()}","X-EBAY-C-MARKETPLACE-ID":self.marketplace})
        with urlopen(req, timeout=25) as r: obj=json.load(r)
        for x in obj.get("itemSummaries",[]):
            ship=0.0
            opts=x.get("shippingOptions") or []
            if opts:
                try: ship=float(opts[0].get("shippingCost",{}).get("value",0) or 0)
                except ValueError: pass
            seller=x.get("seller") or {}
            try: fb=float(seller.get("feedbackPercentage")) if seller.get("feedbackPercentage") else None
            except ValueError: fb=None
            yield Listing(item_id=x.get("itemId",""), title=x.get("title",""), url=x.get("itemWebUrl",""),
                          price=float(x.get("price",{}).get("value",0)), shipping=ship, player=player,
                          image_url=(x.get("image") or {}).get("imageUrl",""), seller_feedback_pct=fb)
