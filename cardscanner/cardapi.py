import json, os, re, statistics
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .identity import parse_identity
from .compkey import player_from_query

NOISE=re.compile(r'\b(lot|repack|digital|custom|reprint|break|case|box|pack)\b',re.I)

def _norm(s): return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()
def _tokens(s): return set(_norm(s).split())

def _query(title, player):
    # Keep discriminating title terms; strip marketplace fluff and serial numerator.
    s=re.sub(r'\b(look|hot|invest|rare|ssp|sp|mint|gem mint|🔥|📈)\b',' ',title,flags=re.I)
    s=re.sub(r'\b\d+\s*/\s*(\d+)\b',r'/\1',s)
    s=re.sub(r'\s+',' ',s).strip()
    return s[:180]

def _sale_match(target_title, sale, player):
    st=sale.get('title','')
    if NOISE.search(st): return False,0.0
    a,ac=parse_identity(target_title,player); b,bc=parse_identity(st,player)
    # Hard mismatches: these are the expensive errors.
    if a.grader != b.grader: return False,0.0
    if (a.grade or '') != (b.grade or ''): return False,0.0
    if bool(a.autograph) != bool(b.autograph): return False,0.0
    if a.year and b.year and a.year != b.year: return False,0.0
    if a.product and b.product and a.product != b.product: return False,0.0
    if a.parallel and b.parallel and a.parallel != b.parallel: return False,0.0
    if a.serial and b.serial and str(a.serial)!=str(b.serial): return False,0.0
    if a.card_number and b.card_number and _norm(a.card_number)!=_norm(b.card_number): return False,0.0
    # API structured fields add another hard check when populated.
    if sale.get('grader') and a.grader!='raw' and _norm(sale['grader'])!=_norm(a.grader): return False,0.0
    if sale.get('grade') and a.grade and str(sale['grade'])!=str(a.grade): return False,0.0
    if sale.get('year') and a.year and str(sale['year'])!=str(a.year): return False,0.0
    if sale.get('print_run') and a.serial and str(sale['print_run'])!=str(a.serial): return False,0.0
    if sale.get('card_number') and a.card_number and _norm(sale['card_number'])!=_norm(a.card_number): return False,0.0
    # Require player words in sold title unless API player is populated and matches.
    pwords=[x for x in _tokens(player) if len(x)>1]
    api_player=_norm(sale.get('player'))
    if api_player:
        if not all(w in api_player for w in pwords): return False,0.0
    elif not all(w in _tokens(st) for w in pwords): return False,0.0
    # Similarity is supporting evidence only after hard checks.
    ta=_tokens(target_title); tb=_tokens(st); common=len(ta&tb); denom=max(1,min(len(ta),len(tb)))
    sim=common/denom
    score=.45*sim+.275*ac+.275*bc
    return score>=.58,score

class CardApiClient:
    def __init__(self):
        self.key=os.getenv('THECARDAPI_KEY','').strip()
        if not self.key: raise RuntimeError('THECARDAPI_KEY is not set in Render.')
    def sales(self,title,player,limit=100):
        ident,_=parse_identity(title,player)
        params={'q':_query(title,player),'platform':'ebay','category':'sports','limit':min(250,max(25,limit)),'sort':'date_desc'}
        if ident.grader!='raw':
            params.update({'graded':'true','grader':ident.grader.upper()})
            if ident.grade: params['grade']=ident.grade
        else: params['graded']='false'
        if ident.serial: params.update({'print_run_min':ident.serial,'print_run_max':ident.serial})
        req=Request('https://thecardapi.com/api/v1/market/sales?'+urlencode(params),headers={'x-market-api-key':self.key,'User-Agent':'CardScout/1.3'})
        with urlopen(req,timeout=35) as r: obj=json.load(r)
        rows=[]
        for sale in obj.get('data',[]):
            try: price=float(sale.get('price'))
            except (TypeError,ValueError): continue
            if price<=0 or not sale.get('price_confirmed',True): continue
            ok,match=_sale_match(title,sale,player)
            if ok:
                rows.append({'title':sale.get('title',''),'price':price,'date':sale.get('sale_date',''),'url':sale.get('listing_url',''),'type':sale.get('listing_type',''),'match':round(match*100),'id':sale.get('id','')})
        # dedupe by id/title-price-date
        seen=set(); clean=[]
        for x in rows:
            k=x['id'] or (x['title'],x['price'],x['date'])
            if k not in seen: seen.add(k); clean.append(x)
        return clean

def evaluate_listing(title,total,search_query):
    player=player_from_query(search_query)
    sales=CardApiClient().sales(title,player)
    if len(sales)<2:
        return {'status':'insufficient','sales':sales[:8],'count':len(sales),'reason':'Need at least 2 close sold matches.'}
    vals=[x['price'] for x in sales]
    med=statistics.median(vals)
    # Remove wild outliers around median, then require support again.
    kept=[x for x in sales if med*.55 <= x['price'] <= med*1.80]
    if len(kept)<2:
        return {'status':'insufficient','sales':kept[:8],'count':len(kept),'reason':'Sold matches were too inconsistent.'}
    vals=[x['price'] for x in kept]; med=statistics.median(vals)
    discount=(med-total)/med*100 if med else 0
    support=min(1,len(kept)/5); matchavg=sum(x['match'] for x in kept)/len(kept)/100
    # Score only positive discounts. 25% below with good support is ~70-90.
    opp=round(max(0,min(100,discount*3.0*(.72+.28*support)*(.82+.18*matchavg))))
    if discount>=20 and len(kept)>=3: status='strong'
    elif discount>=10: status='possible'
    else: status='pass'
    return {'status':status,'reference':round(med,2),'discount':round(discount,1),'score':opp,'count':len(kept),'sales':kept[:8],'reason':''}
