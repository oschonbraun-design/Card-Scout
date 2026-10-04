import os
from flask import Flask, render_template_string, request
from cardscanner.serpapi_ebay import SerpApiEbayClient

app=Flask(__name__)

HTML=r"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout</title><style>
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui;margin:0;background:#090d12;color:#edf2f7}.wrap{max-width:1500px;margin:auto;padding:26px}.muted{color:#8d9aaa}.filters,.notice{background:#111821;border:1px solid #253142;border-radius:16px;padding:16px;margin:14px 0}.filters{display:flex;gap:9px;flex-wrap:wrap}.search{min-width:300px;flex:1}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(275px,1fr));gap:14px}.card{background:#111821;border:1px solid #253142;border-radius:16px;padding:14px;display:flex;flex-direction:column}.card img{width:100%;height:210px;object-fit:contain;background:#fff;border-radius:12px}.price{font-size:25px;font-weight:850;margin-top:auto}.meta{font-size:13px;color:#aab5c3;margin:5px 0}.pill{display:inline-block;padding:4px 8px;background:#1b2431;border-radius:999px;margin:3px 3px 3px 0;font-size:12px}.good{color:#51db86}.warn{color:#ffcc66}.bad{color:#ff7b7b}a.btn{display:inline-block;background:#edf2f7;color:#0b0e13;padding:10px 13px;border-radius:10px;text-decoration:none;font-weight:750;margin-top:8px}input,select,button{padding:10px;border-radius:9px;border:1px solid #39465b;background:#0d131c;color:white}button{cursor:pointer;font-weight:750}.brand{font-size:12px;color:#637084;margin-top:16px}h1{margin-bottom:3px}.topline{display:flex;justify-content:space-between;gap:10px;align-items:center}.sponsored{opacity:.68}
</style></head><body><div class="wrap">
<h1>Card Scout <span class="pill">v0.5</span></h1>
<div class="muted">Search any player. Browse real active eBay listings. Check sold comps yourself before buying.</div>
<form class="filters">
<input class="search" name="q" required placeholder="Type any player, e.g. Drake Maye" value="{{q}}">
<input name="min" type="number" min="0" step="1" value="{{minp}}" style="width:95px" title="Minimum total price">
<input name="max" type="number" min="1" step="1" value="{{maxp}}" style="width:95px" title="Maximum total price">
<select name="sort"><option value="newest" {% if sort=='newest' %}selected{% endif %}>Newest first</option><option value="lowest" {% if sort=='lowest' %}selected{% endif %}>Lowest price</option><option value="ending" {% if sort=='ending' %}selected{% endif %}>Ending soon</option></select>
<button>Search eBay</button>
</form>
<div class="notice"><b>No fake “market value” score.</b> Card Scout v0.5 does not compare unrelated cards or call an item a steal. It shows up to 200 results from one eBay search, including detected shipping and seller information. Use the listing details to find candidates, then verify the exact card on 130point.</div>
{% if error %}<div class="notice bad">{{error}}</div>{% endif %}
{% if searched and not error %}<div class="notice"><b>{{count}} listings shown</b> for “{{q}}” in the ${{minp}}–${{maxp}} total-price range. Sort: {{sort_label}}. One page load = one SerpApi search.</div>{% endif %}
<div class="grid">
{% for x in items %}<div class="card {% if x.sponsored %}sponsored{% endif %}">
{% if x.image %}<img src="{{x.image}}" loading="lazy" alt="listing image">{% endif %}
<h3>{{x.title}}</h3>
<div>{% if x.new_listing %}<span class="pill good">New listing</span>{% endif %}{% if x.sponsored %}<span class="pill">Sponsored</span>{% endif %}{% if x.condition %}<span class="pill">{{x.condition}}</span>{% endif %}</div>
<div class="price">${{"%.2f"|format(x.total)}}</div>
<div class="meta">${{"%.2f"|format(x.price)}} item{% if x.shipping %} + ${{"%.2f"|format(x.shipping)}} shipping{% else %} + free/detected $0 shipping{% endif %}</div>
{% if x.listing_date %}<div class="meta">Listed: {{x.listing_date}}</div>{% endif %}
{% if x.seller %}<div class="meta">Seller: <b>{{x.seller}}</b>{% if x.feedback is not none %} · {{x.feedback}}% positive{% endif %}{% if x.reviews is not none %} · {{x.reviews}} feedback{% endif %}</div>{% endif %}
{% if x.quantity_sold %}<div class="meta">{{x.quantity_sold}}</div>{% endif %}
<a class="btn" target="_blank" rel="noopener" href="{{x.url}}">View on eBay</a>
</div>{% endfor %}
</div>
<div class="brand">Powered by SerpApi eBay Search · Active listings are not sold comps · Card Scout does not calculate market value.</div>
</div></body></html>"""

@app.route("/")
def home():
    q=request.args.get("q","").strip()
    try: minp=float(request.args.get("min","75"))
    except: minp=75
    try: maxp=float(request.args.get("max","150"))
    except: maxp=150
    sort=request.args.get("sort","newest")
    if sort not in {"newest","lowest","ending"}: sort="newest"
    items=[]; error=""; searched=bool(q)
    if searched:
        if len(q)>100: error="Keep the search under 100 characters."
        elif minp<0 or maxp<=minp: error="Enter a valid minimum and maximum price."
        elif not os.getenv("SERPAPI_API_KEY"): error="SERPAPI_API_KEY is missing from Render Environment Variables."
        else:
            try: items=SerpApiEbayClient().search(q,minp,maxp,limit=200,sort=sort)
            except Exception as e: error=f"SerpApi connection error: {e}"
    labels={"newest":"Newest first","lowest":"Lowest price","ending":"Ending soon"}
    return render_template_string(HTML,q=q,minp=int(minp),maxp=int(maxp),sort=sort,sort_label=labels[sort],items=items,count=len(items),error=error,searched=searched)

@app.get("/health")
def health(): return {"ok":True,"version":"0.5","serpapi_configured":bool(os.getenv("SERPAPI_API_KEY"))}

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","8000")))
