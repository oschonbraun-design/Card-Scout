from flask import Blueprint, render_template_string, request
from cardscanner.serpapi_ebay import SerpApiEbayClient
from cardscanner.dealengine import scan_candidates

bp=Blueprint('deals',__name__)
PAGE='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout — Verified Deals</title><style>
*{box-sizing:border-box}body{background:#090d12;color:#edf2f7;font-family:system-ui;margin:0}.wrap{max-width:1100px;margin:auto;padding:28px}a{color:#a6d6ff}.panel,.item{background:#111821;border:1px solid #2a3749;border-radius:14px;padding:17px;margin:14px 0}.controls{display:flex;gap:8px;flex-wrap:wrap}input,button{padding:12px;border-radius:9px;border:1px solid #40536a}input{background:#0c121a;color:white}input[name=q]{flex:1;min-width:250px}button{background:#edf2f7;font-weight:800}.good{color:#55df95}.warn{color:#f4c76c}.muted{color:#a2afc1}.item{display:flex;gap:18px}.item img{width:140px;height:150px;object-fit:contain;background:white;border-radius:8px}.large{font-size:22px;font-weight:800}details{margin-top:10px}summary{cursor:pointer}@media(max-width:600px){.item{display:block}.item img{width:100%}}</style></head><body><main class="wrap"><p><a href="/">← Back to Card Scout</a></p><h1>Verified Deals Finder <small>v1.9</small></h1><p class="muted">Only real CompSniper sold listings can establish a comp. No active-listing estimates. Scans up to 4 distinct exact-card candidates per click to protect your API allowance.</p>
<form class="panel controls" method="get"><input name="q" required value="{{q}}" placeholder="Player + exact card, e.g. Drake Maye Prizm Silver PSA 10"><input type="number" name="min" min="0" value="{{minp}}" style="width:90px"><input type="number" name="max" min="1" value="{{maxp}}" style="width:90px"><button>Find Verified Deals</button></form>
{% if error %}<div class="panel warn">{{error}}</div>{% endif %}
{% if searched %}<div class="panel">Checked {{results|length}} distinct candidate cards. <b>{{deals|length}} qualified deals</b>. {{skipped}} ambiguous listings skipped before comping. This is a limited sample, not a comprehensive scan of eBay.</div>{% endif %}
{% for r in deals %}<article class="item"><img src="{{r.item.image}}"><div><div class="good large">Verified candidate · {{r.analysis.discount}}% below sold median</div><h3>{{r.item.title}}</h3><p><b>${{'%.2f'|format(r.item.total)}} landed</b> · median sold <b>${{'%.2f'|format(r.analysis.comp)}}</b> · {{r.analysis.count}} matched sales</p><p class="good">Estimated resale profit ${{'%.2f'|format(r.analysis.profit)}} · ROI {{r.analysis.roi}}% (assumes 13.5% fees + $0.40 + $5 fulfillment)</p><p><a target="_blank" href="{{r.item.url}}">View eBay listing</a></p><details><summary>Audit sold comps</summary><p class="muted">Search: {{r.analysis.query}}</p>{% for s in r.analysis.sales %}<p>${{'%.2f'|format(s.price)}} · {{s.date}} · <a target="_blank" href="{{s.url}}">{{s.title}}</a></p>{% endfor %}</details></div></article>{% endfor %}
{% if searched and not deals %}<div class="panel"><b>No verified deals in this sample.</b> This means the checked listings did not clear the exact-match and after-fee profit requirements; it does not mean eBay has no deals. Try a narrower card query or different price range.</div>{% endif %}
{% if results %}<details class="panel"><summary>See rejected or unverified candidates ({{results|length - deals|length}})</summary>{% for r in results if r.analysis.status!='deal' %}<p><b>{{r.item.title}}</b> — {{r.analysis.status}}: {{r.analysis.reason}}{% if r.analysis.comp %} · sold median ${{r.analysis.comp}} · projected profit ${{r.analysis.profit}}{% endif %}</p>{% endfor %}</details>{% endif %}
<p class="muted">CompSniper Best Offer displayed prices may not be the final accepted price; those are excluded. Verify the card photo, condition, and latest sold comps before buying. The scan does not guarantee a profit.</p></main></body></html>'''
@bp.get('/find-deals')
def find_deals():
    q=request.args.get('q','').strip()
    try: minp=max(0,float(request.args.get('min','25')))
    except ValueError: minp=25
    try: maxp=max(minp,float(request.args.get('max','250')))
    except ValueError: maxp=250
    results=[]; skipped=0; error=''
    if q:
        try:
            listings=SerpApiEbayClient().search(q,minp,maxp,200,'lowest','bin')
            results,skipped=scan_candidates(listings,q,limit=4)
        except Exception as exc: error=str(exc)
    deals=[x for x in results if x['analysis']['status']=='deal']
    return render_template_string(PAGE,q=q,minp=minp,maxp=maxp,results=results,deals=deals,skipped=skipped,error=error,searched=bool(q))
