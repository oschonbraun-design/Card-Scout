"""CompSniper historical sold comps. API docs: https://api.compsniper.com/docs/sold-history"""
import os, json, statistics, datetime, time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from .dealengine_identity import strict_identity, matching, sold_query

BASE='https://api.compsniper.com'
CACHE={}; TTL=6*3600

def _get(path, params):
    key=os.getenv('COMPSNIPER_API_KEY','').strip()
    if not key: raise RuntimeError('COMPSNIPER_API_KEY is missing in Render Environment.')
    req=Request(BASE+path+'?'+urlencode(params),headers={'Authorization':'Bearer '+key,'Accept':'application/json','User-Agent':'CardScout/1.9'})
    with urlopen(req,timeout=65) as r:return json.load(r)

def _amount(value):
    if isinstance(value,dict): value=value.get('amount')
    try:return float(value)
    except (ValueError,TypeError):return 0.0

def _short_query(title,player):
    ident=strict_identity(title,player)
    if not ident:return None
    # Keep search short: research endpoint requires each keyword to be in the listing title.
    bits=[player,str(ident['year']),str(ident['product'])]
    if ident['parallel']:bits.append(ident['parallel'])
    if ident['grader']!='raw':bits.extend([ident['grader'],ident['grade']])
    return ' '.join(str(x) for x in bits if x)[:190]

def historical(title,player,pages=2):
    ident=strict_identity(title,player)
    if not ident:return [],0,0,'Card identity is ambiguous. Cannot verify exact historical comps.'
    query=_short_query(title,player)
    pages=max(1,min(5,int(pages)))
    cachekey=(query,pages)
    if cachekey in CACHE and time.time()-CACHE[cachekey][0]<TTL:return CACHE[cachekey][1]
    today=datetime.datetime.now(datetime.timezone.utc).date()
    start=today.replace(year=today.year-3) if not (today.month==2 and today.day==29) else today.replace(year=today.year-3,day=28)
    rows=[]; scanned=0; seen=set()
    for page in range(1,pages+1):
        obj=_get('/v1/research/sold',{'keyword':query,'startDate':start.isoformat(),'endDate':today.isoformat(),'sort':'lastSoldDescending','limit':50,'page':page,'singleUnitOnly':'true','relevance':'true','ebaySite':'ebay.com'})
        scanned+=1
        for s in obj.get('results',[]):
            if s.get('recordType')!='single_unit_listing' or int(s.get('soldUnits') or 0)!=1:continue
            title2=s.get('title') or ''
            if not matching(ident,title2):continue
            price=_amount(s.get('soldPrice'))
            if price<=0:continue
            ident2=str(s.get('itemId') or s.get('itemUrl') or title2)
            if ident2 in seen:continue
            seen.add(ident2)
            rows.append({'title':title2,'price':price,'date':s.get('soldDate') or s.get('lastSoldDate') or '', 'url':s.get('itemUrl') or '', 'type':s.get('listingFormat') or '', 'match':100,'source':'CompSniper'})
        if not obj.get('hasNextPage'):break
    rows.sort(key=lambda x:x['date'],reverse=True)
    result=(rows,scanned,len(rows),'')
    CACHE[cachekey]=(time.time(),result)
    return result

def _keep(rows):
    if len(rows)<3:return rows
    mid=statistics.median(r['price'] for r in rows)
    return [r for r in rows if mid*.6<=r['price']<=mid*1.65]

def evaluate_compsniper(title,total,search_query,pages=2):
    from .compkey import player_from_query
    player=player_from_query(search_query)
    try: rows,scanned,count,error=historical(title,player,pages)
    except Exception as e:return {'status':'error','reason':f'CompSniper request failed: {e}','sales':[],'count':0}
    if error:return {'status':'insufficient','reason':error,'sales':[],'count':0}
    kept=_keep(rows)
    if len(kept)<3:return {'status':'insufficient','reason':f'Only {len(kept)} exact historical sales found; need 3 for an automated valuation.','sales':rows,'count':len(kept),'pages_scanned':scanned}
    # Recent 180-day comps drive valuation, older sales shown as context.
    today=datetime.datetime.now(datetime.timezone.utc).date()
    recent=[]
    for r in kept:
        try:
            if (today-datetime.date.fromisoformat(r['date'][:10])).days<=180:recent.append(r)
        except (ValueError,TypeError):pass
    if len(recent)<3:return {'status':'insufficient','reason':'Historical sales found, but fewer than 3 matching sales in the last 180 days. Older sales are context, not a reliable current valuation.','sales':rows,'count':len(kept),'pages_scanned':scanned}
    median=statistics.median(r['price'] for r in recent)
    if max(r['price'] for r in recent)/min(r['price'] for r in recent)>1.8:return {'status':'insufficient','reason':'Recent exact sold prices are too dispersed to estimate value safely.','sales':rows,'count':len(kept),'pages_scanned':scanned}
    discount=(median-total)/median*100 if median else 0
    score=round(max(0,min(100,discount*3)))
    status='strong' if discount>=25 else 'possible' if discount>=10 else 'pass'
    return {'status':status,'reference':round(median,2),'discount':round(discount,1),'score':score,'count':len(kept),'recent_count':len(recent),'sales':rows,'pages_scanned':scanned,'reason':'Current value based on last 180 days; older sales are shown for history.','earliest_sale':min((x['date'] for x in rows if x['date']),default=''),'latest_sale':max((x['date'] for x in rows if x['date']),default=''),'confidence':'conservative'}
