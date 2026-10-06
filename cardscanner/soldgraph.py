import json, os, re, statistics
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .identity import parse_identity
from .compkey import player_from_query

BASE='https://api.soldgraph.com'
NOISE=re.compile(r'\b(lot|repack|digital|custom|reprint|break|case|box|pack)\b',re.I)
def _norm(s): return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()
def _tokens(s): return set(_norm(s).split())
def clean_query(title):
    s=re.sub(r'\b(look|hot|invest|rare|ssp|sp|mint|gem mint)\b',' ',title,flags=re.I)
    s=re.sub(r'\b\d+\s*/\s*(\d+)\b',r'/\1',s)
    return re.sub(r'\s+',' ',s).strip()[:180]

def _match(active, sold, player):
    st=sold.get('title','')
    if NOISE.search(st): return False,0
    a,ac=parse_identity(active,player); b,bc=parse_identity(st,player)
    if a.grader!=b.grader or (a.grade or '')!=(b.grade or ''): return False,0
    if bool(a.autograph)!=bool(b.autograph): return False,0
    for k in ('year','product','parallel','serial','card_number'):
        av=getattr(a,k,None); bv=getattr(b,k,None)
        if av and bv and _norm(av)!=_norm(bv): return False,0
    p=[x for x in _tokens(player) if len(x)>1]
    if p and not all(x in _tokens(st) for x in p): return False,0
    ta,tb=_tokens(active),_tokens(st); sim=len(ta&tb)/max(1,min(len(ta),len(tb)))
    score=.45*sim+.275*ac+.275*bc
    return score>=.60,score

class SoldgraphClient:
    def __init__(self):
        self.key=os.getenv('SOLDGRAPH_KEY','').strip()
        if not self.key: raise RuntimeError('SOLDGRAPH_KEY is not set in Render.')
    def _get(self,url):
        req=Request(url,headers={'Authorization':'Bearer '+self.key,'User-Agent':'CardScout/1.4'})
        with urlopen(req,timeout=40) as r: return r.status,json.load(r)
    def sold(self,title,player,page=1):
        url=BASE+'/v1/ebay/sold?'+urlencode({'q':clean_query(title),'page':page,'country':'us'})
        status,obj=self._get(url)
        if status==202 or obj.get('status')=='pending':
            poll=obj.get('poll_url') or (obj.get('job') or {}).get('poll_url')
            if not poll: return []
            if not poll.startswith('http'): poll=BASE+poll
            sep='&' if '?' in poll else '?'
            for _ in range(3):
                _,obj=self._get(poll+sep+'wait=20')
                if obj.get('status')=='complete': break
                if obj.get('status')=='failed': return []
        result=obj.get('result') or {}
        rows=[]
        for sale in result.get('data',[]):
            # Soldgraph cannot verify the accepted price on Best Offer rows, so exclude them.
            if sale.get('best_offer_accepted'): continue
            price=(sale.get('displayed_price') or {}).get('amount')
            ship=(sale.get('displayed_shipping') or {}).get('amount') or 0
            try: price=float(price)+float(ship)
            except (TypeError,ValueError): continue
            ok,m=_match(title,sale,player)
            if ok: rows.append({'title':sale.get('title',''),'price':price,'date':sale.get('sold_date',''),'url':sale.get('link',''),'type':sale.get('format',''),'match':round(m*100),'id':sale.get('id',''),'source':'Soldgraph'})
        return rows

def evaluate_soldgraph(title,total,search_query):
    player=player_from_query(search_query)
    try:
        sales=SoldgraphClient().sold(title,player)
    except Exception as e:
        return {'status':'insufficient','sales':[],'count':0,'reason':'Soldgraph lookup failed: '+str(e),'source':'Soldgraph'}
    if not sales:
        return {'status':'insufficient','sales':[],'count':0,'reason':'No trustworthy exact Soldgraph matches found.','source':'Soldgraph'}
    vals=[x['price'] for x in sales]
    med=statistics.median(vals)
    kept=[x for x in sales if med*.55<=x['price']<=med*1.80]
    if not kept:
        return {'status':'insufficient','sales':[],'count':0,'reason':'Sold matches were too inconsistent.','source':'Soldgraph'}
    med=statistics.median([x['price'] for x in kept])
    discount=(med-total)/med*100 if med else 0
    avgmatch=sum(x.get('match',70) for x in kept)/len(kept)/100
    evidence=.68 if len(kept)==1 else .84 if len(kept)==2 else min(1,.88+.03*min(4,len(kept)-3))
    score=round(max(0,min(100,discount*3.0*evidence*(.85+.15*avgmatch))))
    if discount>=20 and len(kept)>=2: status='strong'
    elif discount>=10: status='possible'
    else: status='pass'
    return {'status':status,'reference':round(med,2),'discount':round(discount,1),'score':score,
            'count':len(kept),'sales':kept[:10],
            'reason':'1-sale provisional comp' if len(kept)==1 else '', 'source':'Soldgraph'}
