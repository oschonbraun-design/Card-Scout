import re
from .identity import parse_identity

NOISE = ["topps","chrome","update","bowman","draft","panini","prizm","donruss","optic","select","mosaic","contenders","refractor","silver","gold","orange","red","blue","green","pink","purple","mojo","holo","rookie","rc","auto","autograph","psa","sgc","bgs","cgc","card"]

def player_from_query(q):
    s=q.lower()
    s=re.sub(r"\b20\d{2}(?:-\d{2})?\b"," ",s)
    s=re.sub(r"\b(?:10|9\.5|9|8\.5|8)\b"," ",s)
    for w in sorted(NOISE,key=len,reverse=True): s=re.sub(rf"\b{re.escape(w)}\b"," ",s)
    s=re.sub(r"[^a-z0-9 .'-]"," ",s)
    return re.sub(r"\s+"," ",s).strip() or q.lower().strip()

def card_key(title,q):
    player=player_from_query(q)
    ident,confidence=parse_identity(title,player)
    # Exact-only key. Missing fields remain explicit rather than being guessed.
    fields=[player,ident.year or "?",ident.product or "?",ident.parallel or "base/unknown",
            "auto" if ident.autograph else "nonauto",ident.serial or "unnumbered/unknown",
            ident.grader or "raw",ident.grade or "",ident.card_number or "#unknown"]
    key="|".join(str(x).lower().strip() for x in fields)
    label=" · ".join(x for x in [player.title(),ident.year,ident.product.title() if ident.product else "",ident.parallel.title() if ident.parallel else "Base/Unknown",("Auto" if ident.autograph else "Non-auto"),(f"/{ident.serial}" if ident.serial else ""),(ident.grader.upper()+(" "+ident.grade if ident.grade else "") if ident.grader!="raw" else "Raw"),("#"+ident.card_number if ident.card_number else "")] if x)
    # Require enough identity for automatic reuse. Ambiguous parallel/product means user can save,
    # but we won't silently cross-match a different variant.
    complete=bool(player and ident.year and ident.product and (ident.parallel or ident.card_number or ident.serial)) and not ident.uncertainty
    return key,label,complete,round(confidence*100)
