import os, json, statistics
from flask import Flask, render_template_string, request
from cardscanner.serpapi_ebay import SerpApiEbayClient
from cardscanner.identity import parse_identity

ROOT=os.path.dirname(__file__)
app=Flask(__name__)

def load_cfg():
    with open(os.path.join(ROOT,'config.json')) as f: return json.load(f)

HTML="""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout</title><style>
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui;margin:0;background:#090d12;color:#edf2f7}.wrap{max-width:1200px;margin:auto;padding:26px}.top{display:flex;justify-content:space-between;align-items:end;gap:16px}.muted{color:#8d9aaa}.filters,.card,.notice{background:#111821;border:1px solid #253142;border-radius:16px;padding:16px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}.card{margin:0}.card img{width:100%;height:205px;object-fit:contain;background:#fff;border-radius:12px}.price{font-size:25px;font-weight:850}.score{font-weight:800;margin:5px 0}.hot{color:#51db86}.warn{color:#ffcc66}.bad{color:#ff7b7b}a.btn{display:inline-block;background:#edf2f7;color:#0b0e13;padding:10px 13px;border-radius:10px;text-decoration:none;font-weight:750}select,input,button{padding:9px;border-radius:8px;border:1px solid #39465b;background:#0d131c;color:white}button{cursor:pointer}.pill{display:inline-block;padding:4px 8px;background:#1b2431;border-radius:999px;margin:3px 3px 3px 0;font-size:12px}h1{margin-bottom:3px}.why{font-size:13px;color:#aab5c3}.empty{padding:30px}.brand{font-size:12px;color:#637084;margin-top:8px}</style></head><body><div class="wrap">
<div class="top"><div><h1>Card Scout <span class="pill">v0.4</span></h1><div class="muted">Find unusually cheap active eBay sports-card listings. Verify sold comps before buying.</div></div></div>
<form class="filters"><select name="player">{% for p in players %}<option value="{{p.name}}" {% if player==p.name %}selected{% endif %}>{{p.sport}} - {{p.name}}</option>{% endfor %}</select> <input name="min" type="number" value="{{minp}}" style="width:80px"> - <input name="max" type="number" value="{{maxp}}" style="width:80px"> <button>Scan newest listings</button></form>
<div class="notice"><b>Free-plan friendly:</b> one player scan = one SerpApi eBay search. Card Scout compares that player's newly listed results, filters to your price range, and surfaces cheap outliers. <b>Below median is not a sold comp.</b> Always verify the exact card on 130point before buying.</div>
{% if error %}<div class="notice bad">{{error}}</div>{% endif %}
{% if searched and not error %}<div class="notice">Scanned <b>{{player}}</b> - {{count}} qualifying listings in ${{minp}}-${{maxp}} - active reference median ${{median if median else 'N/A'}}</div>{% endif %}
<div class="grid">{% for x in deals %}<div class="card">{% if x.image %}<img src="{{x.image}}" alt="card">{% endif %}<h3>{{x.title}}</h3><div class="price">${{x.total}}</div><div class="score {% if x.discount>=25 %}hot{% elif x.discount>=15 %}warn{% endif %}">{{x.discount}}% below active median</div><div><span class="pill">{{x.player}}</span><span class="pill">{{x.sport}}</span><span class="pill">ID {{x.conf}}%</span></div>{% if x.flags %}<p class="bad">Warning: {{x.flags|join(' / ')}}</p>{% endif %}<p class="why">Active reference median: ${{x.median}} - includes detected shipping</p><a class="btn" target="_blank" rel="noopener" href="{{x.url}}">View on eBay</a></div>{% else %}{% if searched and not error %}<div class="empty muted">No listings were at least 12% below this search's active median.</div>{% endif %}{% endfor %}</div>
<div class="brand">Powered by SerpApi eBay Search - Card Scout does not calculate true market value.</div>
</div></body></html>"""

def player_query(p):
    return p.get('scan_query') or p['name']+' sports card'

def scan(p,minp,maxp):
    client=SerpApiEbayClient(); q=player_query(p)
    items=list(client.search(q,p['name'],minp,maxp,limit=100,newly_listed=True))
    if not items: return [],0,None
    costs=[i.landed_cost for i in items]; med=statistics.median(costs); out=[]
    for it in items:
        ident,conf=parse_identity(it.title,p['name'])
        discount=((med-it.landed_cost)/med*100) if med else 0
        if discount < 12 or conf < .55: continue
        out.append(dict(title=it.title,total=round(it.landed_cost,2),url=it.url,image=it.image_url,player=p['name'],sport=p['sport'],conf=round(conf*100),flags=ident.uncertainty,median=round(med,2),discount=round(discount,1)))
    best={}
    for x in out:
        k=x['url'] or x['title']
        if k not in best or x['discount']>best[k]['discount']: best[k]=x
    return sorted(best.values(),key=lambda x:(x['discount'],x['conf']),reverse=True)[:60],len(items),round(med,2)

@app.route('/')
def home():
    c=load_cfg(); players=c['players']; default=players[0]['name']
    player=request.args.get('player',default); minp=float(request.args.get('min',c['budget']['min'])); maxp=float(request.args.get('max',c['budget']['max']))
    chosen=next((p for p in players if p['name']==player),players[0]); deals=[]; error=''; count=0; median=None; searched=bool(request.args)
    if searched:
        if not os.getenv('SERPAPI_API_KEY'): error='SERPAPI_API_KEY is missing from Render Environment Variables.'
        elif minp<0 or maxp<=minp: error='Enter a valid minimum and maximum price.'
        else:
            try: deals,count,median=scan(chosen,minp,maxp)
            except Exception as e: error=f'SerpApi connection error: {e}'
    return render_template_string(HTML,deals=deals,players=players,player=chosen['name'],minp=int(minp),maxp=int(maxp),error=error,searched=searched,count=count,median=median)

@app.get('/health')
def health(): return {'ok':True,'version':'0.4','serpapi_configured':bool(os.getenv('SERPAPI_API_KEY'))}

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','8000')))
