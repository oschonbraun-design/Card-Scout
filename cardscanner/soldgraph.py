import json, os, re, statistics
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .identity import parse_identity
from .compkey import player_from_query

BASE='https://api.soldgraph.com'
NOISE=re.compile(r'\b(lot|repack|digital|custom|reprint|break|case|box|pack)\b',re.I)
FLUFF=re.compile(r'\b(look|hot|invest|rare|ssp|sp|mint|gem mint|🔥|pop\s*\d+)\b',re.I)

def _norm(s): return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()
def _tokens(s): return set(_norm(s).split())
def clean_query(title):
    s=FLUFF.sub(' ',title)
    s=re.sub(r'\b\d+\s*/\s*(\d+)\b',r'/\1',s)
    s=re.sub(r'\b(ebay|nice|wow|invest|read|look)\b',' ',s,flags=re.I)
    return re.sub(r'\s+',' ',s).strip()[:180]

def _match(active, sold, player):
    st=sold.get('title','')
    if not st or NOISE.search(st): return False,0
    a,ac=parse_identity(active,player); b,bc=parse_identity(st,player)
    # Hard identity gates. Unknown sold fields never override a known active identity.
    if a.grader!=b.grader or (a.grade or '')!=(b.grade or ''): return False,0
    if bool(a.autograph)!=bool(b.autograph): return False,0
    for k in ('year','product','parallel','serial','card_number'):
        av=getattr(a,k,None); bv=getattr(b,k,None)
        if av and not bv: return False,0
        if av and bv and _norm(av)!=_norm(bv): return False,0
    pt=[x for x in _tokens(player) if len(x)>1]
    stoks=_tokens(st)
    if pt and not all(x in stoks for x in pt): return False,0
    ta,tb=_tokens(active),stoks
    sim=len(ta&tb)/max(1,min(len(ta),len(tb)))
    score=.50*sim+.25*ac+.25*bc
    return score>=.72,score

class SoldgraphClient:
    def __init__(self):
        self.key=os.getenv('SOLDGRAPH_KEY','').strip()
        if not self.key: raise RuntimeError('SOLDGRAPH_KEY is not set in Render.')
    def _get(self,url):
        req=Request(url,headers={'Authorization':'Bearer '+self.key,'User-Agent':'CardScout/1.6'})
        with urlopen(req,timeout=45) as r: return r.status,json.load(r)
    def sold(self,title,player,page=1):
        params={'q':clean_query(title),'page':page,'country':'us','count':200,'sort':'recently_sold'}
        status,obj=self._get(BASE+'/v1/ebay/sold?'+urlencode(params))
        if status==202 or obj.get('status')=='pending':
            poll=obj.get('poll_url') or (obj.get('job') or {}).get('poll_url')
            if not poll: raise RuntimeError('Soldgraph returned a pending search without a poll URL.')
            if not poll.startswith('http'): poll=BASE+poll
            sep='&' if '?' in poll else '?'
            for _ in range(4):
                _,obj=self._get(poll+sep+'wait=20')
                if obj.get('status')=='complete': break
                if obj.get('status')=='failed': raise RuntimeError((obj.get('error') or {}).get('code','Soldgraph job failed'))
            if obj.get('status')!='complete': raise RuntimeError('Soldgraph search did not finish in time. Try Analyze again.')
        result=obj.get('result') or {}
        rows=[]
        for sale in result.get('data',[]):
            # Soldgraph documents that accepted-offer displayed_price is the ASK, not the paid price.
            if sale.get('best_offer_accepted'): continue
            dp=sale.get('displayed_price') or {}; ds=sale.get('displayed_shipping') or {}
            try: price=float(dp.get('amount')) + float(ds.get('amount') or 0)
            except (TypeError,ValueError): continue
            ok,m=_match(title,sale,player)
            if ok:
                rows.append({'title':sale.get('title',''),'price':price,'date':sale.get('sold_date',''),'url':sale.get('link',''),'type':sale.get('format',''),'match':round(m*100),'id':sale.get('id',''),'source':'Soldgraph'})
        return rows, result.get('reported_total',0), result.get('collected_at','')

def _robust_keep(sales):
    if len(sales)<=2: return sales
    vals=sorted(x['price'] for x in sales)
    med=statistics.median(vals)
    deviations=[abs(v-med) for v in vals]
    mad=statistics.median(deviations)
    if mad>0:
        return [x for x in sales if abs(x['price']-med) <= 3.5*mad]
    return [x for x in sales if med*.75 <= x['price'] <= med*1.25]

def evaluate_soldgraph(title,total,search_query):
    player=player_from_query(search_query)
    try:
        sales,reported,collected=SoldgraphClient().sold(title,player)
    except Exception as e:
        return {'status':'error','sales':[],'count':0,'reason':'Soldgraph lookup failed: '+str(e),'source':'Soldgraph'}
    if not sales:
        return {'status':'insufficient','sales':[],'count':0,'reason':'Soldgraph returned no sold listings that passed the exact-card match rules.','source':'Soldgraph'}
    kept=_robust_keep(sales)
    if not kept:
        return {'status':'insufficient','sales':[],'count':0,'reason':'The sold prices were too inconsistent to establish a safe comp.','source':'Soldgraph'}
    med=statistics.median([x['price'] for x in kept])
    discount=(med-total)/med*100 if med else 0
    avgmatch=sum(x['match'] for x in kept)/len(kept)
    # A single sale is useful evidence, but never a high-confidence opportunity.
    if len(kept)==1:
        score=min(49,round(max(0,discount)*1.8*(avgmatch/100)))
        confidence='provisional'
    else:
        support=min(1.0,.72+.07*min(4,len(kept)-2))
        score=round(max(0,min(100,discount*2.65*support*(avgmatch/100))))
        confidence='verified' if len(kept)>=3 else 'moderate'
    status='strong' if discount>=20 and len(kept)>=2 else 'possible' if discount>=10 else 'pass'
    return {'status':status,'reference':round(med,2),'discount':round(discount,1),'score':score,'confidence':confidence,
            'count':len(kept),'sales':sorted(kept,key=lambda x:x.get('date',''),reverse=True)[:12],
            'reason':'Only one exact sold match; treat this as provisional.' if len(kept)==1 else '',
            'source':'Soldgraph','reported_total':reported,'collected_at':collected}
