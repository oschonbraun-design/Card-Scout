from flask import Blueprint, render_template_string, request
from cardscanner.serpapi_ebay import SerpApiEbayClient
from cardscanner.dealengine import scan_candidates, DISCOVERY_PLAYERS

bp=Blueprint('deals',__name__)
PAGE='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout — Verified Deals</title><style>
*{box-sizing:border-box}body{background:#090d12;color:#edf2f7;font-family:system-ui;margin:0}.wrap{max-width:1100px;margin:auto;padding:28px}a{color:#a6d6ff}.panel,.item{background:#111821;border:1px solid #2a3749;border-radius:14px;padding:17px;margin:14px 0}.controls{display:flex;gap:8px;flex-wrap:wrap}input,button{padding:12px;border-radius:9px;border:1px solid #40536a}input{background:#0c121a;color:white}input[name=q]{flex:1;min-width:250px}button{background:#edf2f7;font-weight:800}.good{color:#55df95}.warn{color:#f4c76c}.muted{color:#a2afc1}.item{display:flex;gap:18px}.item img{width:140px;height:150px;object-fit:contain;background:white;border-radius:8px}.large{font-size:22px;font-weight:800}details{margin-top:10px}summary{cursor:pointer}@media(max-width:600px){.item{display:block}.item img{width:100%}}</style></head><body><main class="wrap"><p><a href="/">← Back to Card Scout</a></p><h1>Under-Comps Deal Finder <small>v2.1</small></h1><p class="muted">Only real CompSniper sold listings can establish a comp. No active-listing estimates. Discover potential deals without typing a specific card. Each scan checks a limited number of candidates against CompSniper sold prices; unverified cards are never flagged as deals.</p>
<form class="panel controls" method="get"><select name="sport" style="padding:12px;background:#0c121a;color:white;border:1px solid #40536a;border-radius:9px"><option value="basketball" {% if sport=="basketball" %}selected{% endif %}>NBA</option><option value="football" {% if sport=="football" %}selected{% endif %}>NFL</option><option value="baseball" {% if sport=="baseball" %}selected{% endif %}>MLB</option></select><input name="q" value="{{q}}" placeholder="Optional player name (leave blank to discover)"><input type="number" name="min" min="0" value="{{minp}}" style="width:90px"><input type="number" name="max" min="1" value="{{maxp}}" style="width:90px"><button name="scan" value="1">Scan for Under-Comps Deals</button></form>
{% if error %}<div class="panel warn">{{error}}</div>{% endif %}
{% if searched %}<div class="panel">Checked {{results|length}} distinct candidate cards across {{searched_players}} player searches. <b>{{deals|length}} qualified deals</b>. {{skipped}} ambiguous listings skipped before comping. This is a limited sample, not a comprehensive scan of eBay.</div>{% endif %}
{% for r in deals %}<article class="item"><img src="{{r.item.image}}"><div><div class="good large">Under-comps candidate · {{r.analysis.discount}}% below sold median</div><h3>{{r.item.title}}</h3><p><b>${{'%.2f'|format(r.item.total)}} landed</b> · median sold <b>${{'%.2f'|format(r.analysis.comp)}}</b> · {{r.analysis.count}} matched sales</p><p class="good">Estimated resale profit ${{'%.2f'|format(r.analysis.profit)}} · ROI {{r.analysis.roi}}% (assumes 13.5% fees + $0.40 + $5 fulfillment)</p><p><a target="_blank" href="{{r.item.url}}">View eBay listing</a></p><details><summary>Audit sold comps</summary><p class="muted">Search: {{r.analysis.query}}</p>{% for s in r.analysis.sales %}<p>${{'%.2f'|format(s.price)}} · {{s.date}} · <a target="_blank" href="{{s.url}}">{{s.title}}</a></p>{% endfor %}</details></div></article>{% endfor %}
{% if searched and not deals %}<div class="panel"><b>No verified deals in this sample.</b> This means the checked listings did not clear the exact-match and after-fee profit requirements; it does not mean eBay has no deals. Try another sport, price range, or player. Cards without matching sold history cannot be verified.</div>{% endif %}
{% if results %}<details class="panel"><summary>See rejected or unverified candidates ({{results|length - deals|length}})</summary>{% for r in results if r.analysis.status!='deal' %}<p><b>{{r.item.title}}</b> — {{r.analysis.status}}: {{r.analysis.reason}}{% if r.analysis.comp %} · sold median ${{r.analysis.comp}} · projected profit ${{r.analysis.profit}}{% endif %}</p>{% endfor %}</details>{% endif %}
<p class="muted">CompSniper Best Offer displayed prices may not be the final accepted price; those are excluded. Verify the card photo, condition, and latest sold comps before buying. The scan does not guarantee a profit.</p></main></body></html>'''
@bp.get('/find-deals')
def find_deals():
    q=request.args.get('q','').strip()
    try: minp=max(0,float(request.args.get('min','25')))
    except ValueError: minp=25
    try: maxp=max(minp,float(request.args.get('max','250')))
    except ValueError: maxp=250
    sport=request.args.get('sport','basketball')
    if sport not in DISCOVERY_PLAYERS:sport='basketball'
    scanning=request.args.get('scan')=='1'
    results=[]; skipped=0; error=''; searched_players=0
    if scanning:
        try:
            from cardscanner.dealengine_identity import tokens
            roster=DISCOVERY_PLAYERS[sport]
            # A typed player name narrows discovery; otherwise search a rotating basket of players.
            if q:
                roster=[name for name in roster if tokens(q).issubset(tokens(name))] or [q]
            # Each search covers a broad set of singles. Max 3 searches / 8 comp candidates.
            listings=[]; seen_urls=set()
            for player in roster[:3]:
                found=SerpApiEbayClient().search(player,minp,maxp,200,'lowest','bin')
                searched_players+=1
                for item in found:
                    k=item.get('item_id') or item.get('url')
                    if k not in seen_urls:
                        seen_urls.add(k);listings.append(item)
            results,skipped=scan_candidates(listings,q,limit=8,player_names=roster)
        except Exception as exc:error=str(exc)
    deals=[x for x in results if x['analysis']['status']=='deal']
    return render_template_string(PAGE,q=q,sport=sport,searched_players=searched_players,minp=minp,maxp=maxp,results=results,deals=deals,skipped=skipped,error=error,searched=scanning)
