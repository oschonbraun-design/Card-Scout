import json, os, re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .models import Listing

class SerpApiEbayClient:
    def __init__(self):
        self.api_key=os.getenv('SERPAPI_API_KEY','').strip()
        if not self.api_key:
            raise RuntimeError('SERPAPI_API_KEY is not set in Render.')

    @staticmethod
    def _shipping(value):
        if isinstance(value, dict):
            x=value.get('extracted')
            try: return float(x or 0)
            except (TypeError,ValueError): return 0.0
        if not value or 'free' in str(value).lower(): return 0.0
        m=re.search(r'\$\s*([0-9]+(?:\.[0-9]+)?)',str(value))
        return float(m.group(1)) if m else 0.0

    def search(self, query, player, min_price, max_price, limit=100, newly_listed=True):
        params={'engine':'ebay','ebay_domain':'ebay.com','_nkw':query,'_ipg':str(min(200,max(25,int(limit)))),'api_key':self.api_key}
        if newly_listed: params['_sop']='10'
        req=Request('https://serpapi.com/search.json?'+urlencode(params),headers={'User-Agent':'CardScout/0.4'})
        with urlopen(req,timeout=35) as r: obj=json.load(r)
        if obj.get('error'): raise RuntimeError(obj['error'])
        for x in obj.get('organic_results',[]):
            price=x.get('price') or {}
            if not isinstance(price,dict) or price.get('extracted') is None: continue
            try: p=float(price['extracted'])
            except (TypeError,ValueError): continue
            ship=self._shipping(x.get('shipping'))
            total=p+ship
            if total < min_price or total > max_price: continue
            seller=x.get('seller') or {}
            try: fb=float(seller.get('positive_feedback_in_percentage')) if seller.get('positive_feedback_in_percentage') is not None else None
            except (TypeError,ValueError): fb=None
            yield Listing(item_id=str(x.get('product_id','')),title=x.get('title',''),url=x.get('link',''),price=p,shipping=ship,player=player,image_url=x.get('thumbnail',''),seller_feedback_pct=fb)
