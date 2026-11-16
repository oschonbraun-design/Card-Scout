"""Conservative but non-brittle sports-card title matching."""
import re
from .identity import parse_identity

BLOCK=re.compile(r'\b(lot|lots|repack|mystery|custom|reprint|digital|break|box|case|pack|proxy|facsimile)\b',re.I)
VARIANTS=['negative','sepia','pink','silver','gold','orange','red','blue','green','purple','black','teal','mojo','wave','choice','refractor','x-fractor','zebra','tiger','elephant','genesis','holo','scope','hyper','shimmer','sparkle','disco','laser','cracked ice','stained glass','downtown','kaboom','color blast','base']
PRODUCTS=['topps chrome update','topps chrome','topps update','topps','bowman chrome draft','bowman chrome','bowman draft','bowman','panini prizm','prizm','donruss optic','optic','donruss','select','mosaic','contenders','national treasures','immaculate','flawless','photogenic','revolution','obsidian','spectra','certified','absolute','origins']

def normalized(s):return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()
def tokens(s):return set(normalized(s).split())
def phrase(s,p):return bool(re.search(r'(?<!\w)'+re.escape(p)+r'(?!\w)',s))
def _variant(s):
    return tuple(sorted(x for x in VARIANTS if phrase(s,x) and x!='base'))
def _product(s):
    for p in PRODUCTS:
        if phrase(s,p):return p
    return ''
def strict_identity(title,player):
    if not title or BLOCK.search(title):return None
    s=normalized(title); p=normalized(player)
    if not p or not tokens(p).issubset(tokens(s)):return None
    i,confidence=parse_identity(title,player)
    # Base cards and cards lacking a printed card number are legitimate.
    # We require a year and product, but never require a parallel or #.
    product=_product(s) or i.product
    if not i.year or not product:return None
    grade=re.search(r'\b(psa|sgc|bgs|cgc|beckett)\s*(10|9\.5|9|8\.5|8|7\.5|7|6)\b',s)
    grader=grade.group(1) if grade else 'raw'
    if grader=='beckett':grader='bgs'
    serial=re.search(r'(?<!\d)/\s*(\d{1,5})\b',title)
    card=re.search(r'(?:card\s*#|#)([a-z0-9-]{1,12})\b',title,re.I)
    variants=_variant(s)
    return {'player':p,'year':i.year,'product':product,'parallel':variants,'serial':serial.group(1) if serial else '',
            'grader':grader,'grade':grade.group(2) if grade else '',
            'auto':bool(re.search(r'\b(auto|autograph|autographed|signature|signed)\b',s)),
            'number':normalized(card.group(1)) if card else '', 'confidence':confidence}

def matching(active,sold):
    b=strict_identity(sold,active['player'])
    if not b:return False
    for k in ('player','year','product','parallel','serial','grader','grade','auto'):
        if active[k]!=b[k]:return False
    # A missing number in one title isn't an automatic rejection, but conflicting
    # explicit numbers always are.
    if active['number'] and b['number'] and active['number']!=b['number']:return False
    return True

def sold_query(title,player,ident):
    # Do not include card number, grade or parallel in initial API query: they
    # frequently disappear from sold titles. Verify those fields after retrieval.
    product=ident['product'].replace('panini ','').replace('donruss ','').replace('topps ','').replace('bowman ','')
    return ' '.join([player,str(ident['year']),product])[:190]
