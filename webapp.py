import os, json, statistics
from flask import Flask, render_template_string, request
from cardscanner.ebay import EbayBrowseClient
from cardscanner.identity import parse_identity

ROOT=os.path.dirname(__file__)
app=Flask(__name__)

def load_cfg():
    with open(os.path.join(ROOT,'config.json')) as f: return json.load(f)

def queries_for(p): return p.get('queries') or [p['name']]

HTML='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout</title><style>
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui;margin:0;background:#090d12;color:#edf2f7}.wrap{max-width:1200px;margin:auto;padding:26px}.top{display:flex;justify-content:space-between;align-items:end;gap:16px}.muted{color:#8d9aaa}.filters,.card,.notice{background:#111821;border:1px solid #253142;border-radius:16px;padding:16px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}.card{margin:0}.card img{width:100%;height:205px;object-fit:contain;background:#fff;border-radius:12px}.price{font-size:25px;font-weight:850}.score{font-weight:800;margin:5px 0}.hot{color:#51db86}.warn{color:#ffcc66}.bad{color:#ff7b7b}a.btn{display:inline-block;background:#edf2f7;color:#0b0e13;padding:10px 13px;border-radius:10px;text-decoration:none;font-weight:750}select,input,button{padding:9px;border-radius:8px;border:1px solid #39465b;background:#0d131c;color:white}button{cursor:pointer}.pill{display:inline-block;padding:4px 8px;background:#1b2431;border-radius:999px;margin:3px 3px 3px 0;font-size:12px}h1{margin-bottom:3px}.why{font-size:13px;color:#aab5c3}.empty{padding:30px}</style></head><body><div class="wrap">
<div class="top"><div><h1>Card Scout</h1><div class="muted">Surfaces unusually cheap eBay listings. Always verify sold comps before buying.</div></div></div>
<form class="filters"><select name="sport"><option value="all">All sports</option>{% for s in sports %}<option value="{{s}}" {% if sport==s %}selected{% endif %}>{{s}}</option>{% endfor %}</select> <input name="min" type="number" value="{{minp}}" style="width:80px"> – <input name="max" type="number" value="{{maxp}}" style="width:80px"> <button>Scan eBay</button></form>
<div class="notice"><b>How ranking works:</b> each player's new listings are compared with other active listings returned for that same search. Cheap outliers rise to the top. Variant uncertainty lowers confidence. <b>This is discovery, not a market-value estimate.</b></div>
{% if error %}<div class="notice bad">{{error}}</div>{% endif %}
<div class="grid">{% for x in deals %}<div class="card">{% if x.image %}<img src="{{x.image}}" alt="card">{% endif %}<h3>{{x.title}}</h3><div class="price">${{x.total}}</div><div class="score {% if x.discount>=25 %}hot{% elif x.discount>=15 %}warn{% endif %}">{{x.discount}}% below this search's active median</div><div><span class="pill">{{x.player}}</span><span class="pill">{{x.sport}}</span><span class="pill">ID {{x.conf}}%</span></div>{% if x.flags %}<p class="bad">⚠ {{x.flags|join(' · ')}}</p>{% endif %}<p class="why">Active reference median: ${{x.median}} · Search: {{x.query}}</p><a class="btn" target="_blank" rel="noopener" href="{{x.url}}">Open on eBay</a></div>{% else %}<div class="empty muted">No candidates to show yet.</div>{% endfor %}</div>
</div></body></html>'''

def scan(sport,minp,maxp):
    c=load_cfg(); client=EbayBrowseClient(c.get('marketplace','EBAY_US')); out=[]
    for p in c['players']:
        if sport!='all' and p['sport']!=sport: continue
        for q in queries_for(p):
            items=list(client.search(q,p['name'],minp,maxp,limit=50))
            if len(items)<5: continue
            costs=[i.landed_cost for i in items]
            med=statistics.median(costs)
            for it in items:
                ident,conf=parse_identity(it.title,p['name'])
                discount=((med-it.landed_cost)/med*100) if med else 0
                if discount < 12: continue
                out.append(dict(title=it.title,total=round(it.landed_cost,2),url=it.url,image=it.image_url,player=p['name'],sport=p['sport'],conf=round(conf*100),flags=ident.uncertainty,median=round(med,2),discount=round(discount,1),query=q))
    # dedupe listings appearing in multiple searches
    best={}
    for x in out:
        k=x['url'] or x['title']
        if k not in best or x['discount']>best[k]['discount']: best[k]=x
    return sorted(best.values(),key=lambda x:(x['discount'],x['conf']),reverse=True)[:100]

@app.route('/')
def home():
    c=load_cfg(); sports=sorted({p['sport'] for p in c['players']}); sport=request.args.get('sport','all')
    minp=float(request.args.get('min',c['budget']['min'])); maxp=float(request.args.get('max',c['budget']['max']))
    deals=[]; error=''
    if os.getenv('EBAY_CLIENT_ID') and os.getenv('EBAY_CLIENT_SECRET'):
        try: deals=scan(sport,minp,maxp)
        except Exception as e: error=f'eBay connection error: {e}'
    else: error='Add EBAY_CLIENT_ID and EBAY_CLIENT_SECRET to enable live scanning.'
    return render_template_string(HTML,deals=deals,sports=sports,sport=sport,minp=int(minp),maxp=int(maxp),error=error)

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','8000')))
