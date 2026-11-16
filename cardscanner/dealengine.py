"""Conservative CompSniper-backed deal discovery. No active asking-price valuation."""
import re, statistics, time
from .compsniper import historical, _keep
from .identity import parse_identity
from .compkey import player_from_query

# Cached per process to reduce paid search consumption on repeat scans.
_CACHE = {}
TTL = 6 * 3600
BLOCK = re.compile(r'\b(lot|lots|repack|mystery|custom|reprint|digital|break|box|case|pack|proxy|facsimile)\b', re.I)
BAD = re.compile(r'\b(variation|choose|pick your|you pick|random|read description)\b', re.I)

from .dealengine_identity import strict_identity, matching, sold_query

# Player names used only to identify the player in a listing, not to assert card identity.
DISCOVERY_PLAYERS = {
 'basketball':['Victor Wembanyama','Anthony Edwards','Shai Gilgeous-Alexander','Luka Doncic','Stephen Curry','Cade Cunningham','Paolo Banchero','Cooper Flagg','Dylan Harper','Tyrese Maxey'],
 'football':['Caleb Williams','Jayden Daniels','Drake Maye','Joe Burrow','Brock Purdy','Bijan Robinson','Jahmyr Gibbs','CJ Stroud','Patrick Mahomes','Bo Nix'],
 'baseball':['Shohei Ohtani','Aaron Judge','Paul Skenes','Elly De La Cruz','Bobby Witt Jr','Jackson Chourio','Jackson Holliday','Roman Anthony','Juan Soto','Gunnar Henderson']
}

def identify_player(title, names):
    from .dealengine_identity import tokens
    title_tokens=tokens(title)
    for name in names:
        if tokens(name).issubset(title_tokens):return name
    return None


def evaluate_candidate(item, player, fee_pct=.135, fulfillment=5.0):
    title=item['title']; identity=strict_identity(title,player)
    if not identity:
        return {'status':'unverified','reason':'Card identity is incomplete or ambiguous; no automated comp.'}
    q=sold_query(title,player,identity)
    cachekey=q.lower()
    if cachekey in _CACHE and time.time()-_CACHE[cachekey][0]<TTL:
        rows, reported, collected=_CACHE[cachekey][1]
    else:
        rows,reported,collected,_=historical(title,player,pages=1)
        _CACHE[cachekey]=(time.time(),(rows,reported,collected))
    # CompSniper historical rows are individually validated against the exact card.
    matches=[x for x in rows if matching(identity,x['title']) and x['price']>0]
    matches=_keep(matches)
    from datetime import date
    today=date.today()
    matches=[r for r in matches if r.get('date') and 0 <= (today-date.fromisoformat(r['date'][:10])).days <= 180]
    if len(matches)<3:
        return {'status':'unverified','reason':f'Only {len(matches)} trustworthy exact sales; need 3.',
                'sales':matches,'query':q}
    values=[x['price'] for x in matches]
    median=statistics.median(values)
    # Median can still be misleading when exact sale prices have high dispersion.
    if max(values)/min(values)>1.8:
        return {'status':'unverified','reason':'Matched sales disagree too much to price safely.',
                'sales':matches,'query':q}
    total=float(item['total'])
    # Conservative estimated net proceeds if resold at the historical median.
    net=median*(1-fee_pct)-.40-fulfillment
    profit=net-total
    roi=profit/total if total else 0
    discount=(median-total)/median if median else 0
    status='deal' if discount>=.25 and roi>=.20 and profit>=15 else 'pass'
    return {'status':status,'query':q,'comp':round(median,2),'discount':round(discount*100,1),
            'profit':round(profit,2),'roi':round(roi*100,1),'count':len(matches),
            'sales':matches,'reason': 'Meets discount, net-profit and ROI thresholds.' if status=='deal' else 'Fails discount or after-fee profit thresholds.'}

def scan_candidates(items, query, limit=8, player_names=None):
    player_names=player_names or [player_from_query(query)]
    candidates=[]; skipped=0; seen=set()
    # Prefer plausible low-priced listings, but do not repeatedly comp the same card.
    for item in sorted(items,key=lambda x:float(x.get('total') or 1e9)):
        player=identify_player(item.get('title',''),player_names)
        if not player:skipped+=1;continue
        identity=strict_identity(item.get('title',''),player)
        if not identity:skipped+=1;continue
        key=(identity['player'],identity['year'],identity['product'],identity['parallel'],identity['serial'],identity['grader'],identity['grade'],identity['auto'],identity['number'])
        if key in seen:continue
        seen.add(key);candidates.append((item,player))
        if len(candidates)>=limit:break
    results=[]
    for item,player in candidates:
        try:analysis=evaluate_candidate(item,player)
        except Exception as e:analysis={'status':'error','reason':str(e)}
        results.append({'item':item,'analysis':analysis})
        if analysis['status']=='error' and ('quota' in analysis['reason'].lower() or '429' in analysis['reason']):break
    results.sort(key=lambda x:(x['analysis']['status']=='deal',x['analysis'].get('roi',-999)),reverse=True)
    return results,skipped
