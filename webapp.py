import os
from urllib.parse import urlencode
from flask import Flask, render_template_string, request
from cardscanner.serpapi_ebay import SerpApiEbayClient
from cardscanner.auction import rank_auctions
from cardscanner.lots import rank_lots
from cardscanner.compkey import card_key
from cardscanner.cardapi import evaluate_listing

app=Flask(__name__)

def sold_url(title):
    return "https://www.ebay.com/sch/i.html?"+urlencode({"_nkw":title,"LH_Sold":"1","LH_Complete":"1"})

HTML=r"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Card Scout v1.3</title><style>
*{box-sizing:border-box}body{font-family:Inter,system-ui;margin:0;background:#090d12;color:#edf2f7}.wrap{max-width:1500px;margin:auto;padding:25px}.muted{color:#91a0b2}.tabs{display:flex;gap:8px;margin:18px 0}.tab,.btn,button{display:inline-block;padding:10px 13px;border-radius:10px;text-decoration:none;font-weight:750;border:1px solid #39465b}.tab{color:#dce5ef;background:#111821}.tab.on,.btn,button{background:#edf2f7;color:#0b0e13}.filters,.notice{background:#111821;border:1px solid #253142;border-radius:15px;padding:15px;margin:13px 0}.filters{display:flex;gap:8px;flex-wrap:wrap}.search{min-width:300px;flex:1}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:14px}.card{background:#111821;border:1px solid #253142;border-radius:15px;padding:14px;display:flex;flex-direction:column}.card img{width:100%;height:205px;object-fit:contain;background:#fff;border-radius:11px}.price{font-size:25px;font-weight:850;margin-top:auto}.meta{font-size:13px;color:#aab5c3;margin:5px 0}.pill{display:inline-block;padding:4px 8px;background:#1b2431;border-radius:999px;margin:3px;font-size:12px}.good{color:#51db86}.warn{color:#ffcc66}.bad{color:#ff7b7b}input,select{padding:10px;border-radius:9px;border:1px solid #39465b;background:#0d131c;color:white}.comp{display:flex;gap:5px;margin-top:9px}.comp input{width:110px}.compform{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.compform input{width:125px}summary{cursor:pointer}.result{font-weight:800;margin-top:7px}.actions{display:flex;gap:5px;flex-wrap:wrap}.actions .btn{font-size:12px}.sponsored{opacity:.65}</style>
<script>
const LIBKEY='cardScoutCompLibraryV11';
let dealsOnly=true;
function lib(){try{return JSON.parse(localStorage.getItem(LIBKEY)||'{}')}catch(e){return {}}}
function put(v){localStorage.setItem(LIBKEY,JSON.stringify(v))}
function daysOld(ds){if(!ds)return 999; return Math.max(0,(Date.now()-new Date(ds+'T12:00:00').getTime())/86400000)}
function reference(c){let clv=+c.clv||0,avg=+c.avg||0,last=+c.last||0;if(clv&&avg)return (clv*0.55+avg*0.45);if(clv)return clv;if(avg)return avg;return last}
function score(total,c){let ref=reference(c);if(!ref)return {score:null,ref:0,discount:0};let d=(ref-total)/ref*100;if(d<=0)return {score:0,ref:ref,discount:d};let base=Math.min(100,d*2.8);let age=daysOld(c.date),fresh=age<=30?1:age<=90?.9:age<=180?.75:.55;let n=+c.sales||1,evidence=(c.clv&&c.avg?.95:c.clv||c.avg?.88:.70)*Math.min(1,.72+n*.07);return {score:Math.round(base*fresh*evidence),ref:ref,discount:d}}
function paint(){let L=lib(),cards=[];document.querySelectorAll('.opp').forEach(el=>{let card=el.closest('.card'),k=el.dataset.key,c=L[k],complete=el.dataset.complete==='1',rank=-999;if(!c){el.textContent='Comp Needed';el.className='pill opp warn';card.dataset.deal='0'}else if(!complete){el.textContent='Verify Identity';el.className='pill opp warn';card.dataset.deal='0'}else{let r=score(+el.dataset.total,c);if(r.score===null){el.textContent='Comp Needed';card.dataset.deal='0'}else{rank=r.discount;card.dataset.deal=(r.discount>=10?'1':'0');card.dataset.rank=rank;el.textContent='Opportunity '+r.score+'/100 · '+(r.discount>=0?r.discount.toFixed(1)+'% below verified comp':Math.abs(r.discount).toFixed(1)+'% above verified comp');el.className='pill opp '+(r.discount>=20?'good':r.discount>=10?'warn':'bad');el.title='Verified reference $'+r.ref.toFixed(2)+' · verified '+(c.date||'date unknown')}}cards.push(card)});cards.sort((a,b)=>(+b.dataset.rank||-999)-(+a.dataset.rank||-999)).forEach(c=>c.parentNode.appendChild(c));applyDealFilter()}
function applyDealFilter(){document.querySelectorAll('.card').forEach(c=>{if(c.dataset.mode==='single')c.style.display=(dealsOnly&&c.dataset.deal!=='1')?'none':'flex'});let b=document.getElementById('dealToggle');if(b)b.textContent=dealsOnly?'Showing verified deals only':'Showing all listings'}
function toggleDeals(){dealsOnly=!dealsOnly;applyDealFilter()}
function saveComp(btn,complete){let box=btn.closest('.compform'),k=box.dataset.key,L=lib();let c={label:box.dataset.label,last:+box.querySelector('.last').value||0,avg:+box.querySelector('.avg').value||0,clv:+box.querySelector('.clv').value||0,sales:+box.querySelector('.sales').value||1,date:box.querySelector('.date').value||new Date().toISOString().slice(0,10),source:'Card Ladder/manual'};if(!reference(c)){btn.closest('details').querySelector('.savedmsg').textContent='Enter at least one Card Ladder value.';return}if(!complete&&!confirm('This title has an incomplete/ambiguous identity. Save only if you verified this exact variant in Card Ladder. Continue?'))return;L[k]=c;put(L);btn.closest('details').querySelector('.savedmsg').textContent='Saved. Exact matching listings will now use this verified comp.';paint()}
function copyCL(i){let t=document.getElementById('clq'+i).value;navigator.clipboard.writeText(t);alert('Card Ladder search copied: '+t)}
function showLibrary(){let d=document.getElementById('library'),L=lib();if(d.style.display==='block'){d.style.display='none';return}let rows=Object.entries(L);d.style.display='block';d.innerHTML='<b>Comp Library ('+rows.length+')</b>'+(rows.length?'':'<p>No saved comps yet.</p>')+rows.map(([k,c],i)=>'<div class="meta"><b>'+c.label+'</b> · reference $'+reference(c).toFixed(2)+' · '+(c.sales||1)+' sales · '+(c.date||'no date')+' <button type="button" onclick="delComp('+i+')">Delete</button></div>').join('');d.dataset.keys=JSON.stringify(rows.map(x=>x[0]))}
function delComp(i){let d=document.getElementById('library'),keys=JSON.parse(d.dataset.keys),L=lib();delete L[keys[i]];put(L);showLibrary();showLibrary();paint()}
window.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('.date').forEach(x=>x.value=new Date().toISOString().slice(0,10));paint()});
</script></head><body><div class="wrap">
<h1>Card Scout <span class="pill">v1.3</span></h1><div class="muted">Automatic sold-comp analysis powered by The Card API.</div>
<div class="tabs"><button id="dealToggle" type="button" onclick="toggleDeals()">Showing verified deals only</button><a class="tab {% if mode=='singles' %}on{% endif %}" href="/?mode=singles">Singles Scout</a><a class="tab {% if mode=='lots' %}on{% endif %}" href="/?mode=lots">Lot Scout</a><button type="button" onclick="showLibrary()">Comp Library</button></div><div id="library" class="notice" style="display:none"></div>
<form class="filters"><input type="hidden" name="mode" value="{{mode}}"><input class="search" name="q" required placeholder="{% if mode=='lots' %}e.g. baseball card lot rookies autos{% else %}e.g. Dylan Harper Topps Chrome{% endif %}" value="{{q}}">
<input name="min" type="number" min="0" value="{{minp}}" style="width:90px"><input name="max" type="number" min="1" value="{{maxp}}" style="width:90px">
<select name="format"><option value="bin" {% if fmt=='bin' %}selected{% endif %}>Buy It Now</option><option value="auction" {% if fmt=='auction' %}selected{% endif %}>Auctions</option><option value="all" {% if fmt=='all' %}selected{% endif %}>All</option></select>
<select name="sort"><option value="newest" {% if sort=='newest' %}selected{% endif %}>Newest</option><option value="lowest" {% if sort=='lowest' %}selected{% endif %}>Lowest price</option><option value="ending" {% if sort=='ending' %}selected{% endif %}>Ending soon</option></select><button>Scan eBay</button></form>
{% if mode=='singles' %}<div class="notice"><b>Automatic comps are live.</b> Click <b>Analyze Sold Comps</b> on a listing. Card Scout checks actual completed eBay sales through The Card API, rejects mismatched grade/auto/year/product/parallel/numbering/card-number sales when identifiable, and refuses to score cards without enough close matches.</div>
{% else %}<div class="notice"><b>Lot Scout:</b> searches listings marked/described as lots and ranks observable signals: estimated card count, price/card, hit keywords and junk/repack warnings. <b>Lot Interest is not a market-value score.</b> Inspect photos and comp the valuable cards before buying.</div>{% endif %}
{% if error %}<div class="notice bad">{{error}}</div>{% endif %}{% if searched and not error %}<div class="notice">{{items|length}} listings shown. One scan uses one SerpApi search.</div>{% endif %}
<div class="grid">{% for x in items %}<div class="card {% if x.sponsored %}sponsored{% endif %}" data-mode="{% if mode=='singles' %}single{% else %}lot{% endif %}">{% if x.image %}<img src="{{x.image}}" loading="lazy">{% endif %}<h3>{{x.title}}</h3>
<div><span class="pill opp" data-key="{{x.comp_key|e}}" data-total="{{x.total}}" data-complete="{{1 if x.comp_complete else 0}}">Comp Needed</span>{% if fmt=='auction' and x.auction_score is defined %}<span class="pill warn">Auction Watch {{x.auction_score}}/100</span>{% endif %}{% if mode=='lots' and x.lot_interest is defined %}<span class="pill">Lot Interest {{x.lot_interest}}/100</span>{% endif %}{% if x.new_listing %}<span class="pill good">New</span>{% endif %}</div>
<div class="price">${{"%.2f"|format(x.total)}} total</div><div class="meta">${{"%.2f"|format(x.price)}} item + ${{"%.2f"|format(x.shipping)}} shipping</div>
{% if x.time_left %}<div class="meta warn"><b>{{x.time_left}} left</b> · {{x.bids or 0}} bids</div>{% endif %}
{% if mode=='lots' %}{% if x.estimated_count %}<div class="meta">Estimated {{x.estimated_count}} cards · <b>${{"%.2f"|format(x.price_per_card)}}/card</b></div>{% endif %}{% if x.hit_words %}<div class="meta good">Signals: {{x.hit_words|join(', ')}}</div>{% endif %}{% if x.junk_flags %}<div class="meta bad"><b>Warning:</b> {{x.junk_flags|join(', ')}}</div>{% endif %}{% endif %}
{% if x.seller %}<div class="meta">{{x.seller}}{% if x.feedback %} · {{x.feedback}}% feedback{% endif %}</div>{% endif %}
<div class="meta"><b>Identity:</b> {{x.comp_label}}{% if not x.comp_complete %} <span class="warn">· verify variant before saving</span>{% endif %}</div><div class="actions"><a class="btn" target="_blank" href="{{x.url}}">View Listing</a>{% if mode=='singles' %}<a class="btn" href="/analyze?title={{x.title|urlencode}}&total={{x.total}}&q={{q|urlencode}}&url={{x.url|urlencode}}">Analyze Sold Comps</a>{% endif %}<a class="btn" target="_blank" href="{{x.sold_url}}">eBay Sold</a><a class="btn" target="_blank" href="https://130point.com/sales/">130point</a><button type="button" class="btn" onclick="copyCL({{loop.index}})">Copy CL Search</button><a class="btn" target="_blank" href="https://www.cardladder.com/">Open Card Ladder</a></div><input type="hidden" id="clq{{loop.index}}" value="{{x.comp_label|e}}">
{% if mode=='singles' %}<details class="notice"><summary><b>Save / update verified Card Ladder comp</b></summary><div class="compform" data-key="{{x.comp_key|e}}" data-label="{{x.comp_label|e}}"><input class="last" type="number" step=".01" placeholder="Last sale $"><input class="avg" type="number" step=".01" placeholder="Recent avg $"><input class="clv" type="number" step=".01" placeholder="CL Value $"><input class="sales" type="number" min="1" placeholder="# sales"><input class="date" type="date"><button type="button" onclick="saveComp(this,{{1 if x.comp_complete else 0}})">Save Verified Comp</button></div><div class="result savedmsg"></div></details>{% endif %}
</div>{% endfor %}</div></div></body></html>"""

@app.get("/")
def home():
    mode=request.args.get("mode","singles")
    q=request.args.get("q","").strip()
    try:minp=float(request.args.get("min","10" if mode=="lots" else "25"))
    except:minp=10
    try:maxp=float(request.args.get("max","500" if mode=="lots" else "250"))
    except:maxp=500
    fmt=request.args.get("format","bin"); sort=request.args.get("sort","newest")
    searched=bool(q); items=[]; error=""
    if searched:
        try:
            search_q=q
            if mode=="lots" and "lot" not in q.lower(): search_q=q+" card lot"
            api_sort="ending" if fmt=="auction" else sort
            items=SerpApiEbayClient().search(search_q,minp,maxp,200,api_sort,fmt,lots_only=(mode=="lots"))
            if mode=="lots":
                items=[x for x in items if ("lot" in x["title"].lower() or "cards" in x["title"].lower())]
                items=rank_lots(items)
            elif fmt=="auction":
                items=rank_auctions(items)
            for x in items:
                x["sold_url"]=sold_url(x["title"])
                x["comp_key"],x["comp_label"],x["comp_complete"],x["identity_confidence"]=card_key(x["title"],q)
        except Exception as e:error=str(e)
    return render_template_string(HTML,mode=mode,q=q,minp=minp,maxp=maxp,fmt=fmt,sort=sort,items=items,error=error,searched=searched)

@app.get("/analyze")
def analyze():
    title=request.args.get("title","")
    q=request.args.get("q","")
    url=request.args.get("url","")
    try: total=float(request.args.get("total","0"))
    except: total=0
    try: result=evaluate_listing(title,total,q)
    except Exception as e: result={"status":"error","reason":str(e),"sales":[],"count":0}
    return render_template_string(r"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comp Analysis</title><style>body{font-family:system-ui;background:#090d12;color:#edf2f7;max-width:950px;margin:auto;padding:28px}.box{background:#111821;border:1px solid #253142;border-radius:15px;padding:18px;margin:14px 0}.good{color:#51db86}.warn{color:#ffcc66}.bad{color:#ff7b7b}a{color:#9fd3ff}.score{font-size:38px;font-weight:900}.price{font-size:25px;font-weight:800}</style></head><body><a href="javascript:history.back()">← Back to scanner</a><h1>Sold Comp Analysis</h1><div class="box"><b>{{title}}</b><div class="price">Listing total: ${{"%.2f"|format(total)}}</div>{% if result.status in ['strong','possible','pass'] %}<div class="score {{'good' if result.status=='strong' else 'warn' if result.status=='possible' else 'bad'}}">Opportunity {{result.score}}/100</div><p>Sold reference: <b>${{"%.2f"|format(result.reference)}}</b> · {{result.count}} close matches · {% if result.discount>=0 %}<b>{{result.discount}}% below sold comp</b>{% else %}<b>{{-result.discount}}% ABOVE sold comp</b>{% endif %}</p>{% elif result.status=='insufficient' %}<h2 class="warn">No score — insufficient reliable comps</h2><p>{{result.reason}}</p>{% else %}<h2 class="bad">Comp lookup failed</h2><p>{{result.reason}}</p>{% endif %}</div><div class="box"><h2>Matched sold listings</h2>{% if result.sales %}{% for s in result.sales %}<p><b>${{"%.2f"|format(s.price)}}</b> · {{s.date}} · {{s.type}} · match {{s.match}}%<br>{{s.title}}{% if s.url %} · <a target="_blank" href="{{s.url}}">sold listing</a>{% endif %}</p>{% endfor %}{% else %}<p>No close matches returned. Check Card Ladder/130point manually rather than guessing.</p>{% endif %}</div>{% if url %}<p><a target="_blank" href="{{url}}">Open active eBay listing</a></p>{% endif %}</body></html>""",title=title,total=total,result=result,url=url)

@app.get("/health")
def health():return {"ok":True,"version":"1.3","serpapi_configured":bool(os.getenv("SERPAPI_API_KEY")),"cardapi_configured":bool(os.getenv("THECARDAPI_KEY"))}

if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))
