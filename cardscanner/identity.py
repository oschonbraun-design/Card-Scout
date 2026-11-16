import re
from .models import CardIdentity

GRADERS = {"psa":"psa", "bgs":"bgs", "beckett":"bgs", "sgc":"sgc", "cgc":"cgc"}
PRODUCTS = [
    "bowman chrome", "bowman draft", "bowman", "topps chrome", "topps update", "topps",
    "panini prizm", "prizm", "donruss optic", "optic", "select", "mosaic", "contenders"
]
PARALLELS = [
    "stained glass jumbo", "stained glass", "silver prizm", "silver", "ruby wave",
    "red choice", "choice", "orange", "gold", "green", "blue", "red", "pink",
    "purple", "teal mojo", "red mojo", "mojo", "refractor", "x-fractor", "scope",
    "zebra", "tiger", "elephant", "genesis", "holo"
]

def _first(text, options):
    low = text.lower()
    for opt in sorted(options, key=len, reverse=True):
        if opt in low:
            return opt
    return ""

def parse_identity(title: str, player: str) -> tuple[CardIdentity, float]:
    low = title.lower().replace("–", "-")
    ident = CardIdentity(player=player)
    year = re.search(r"\b(20\d{2})(?:-\d{2})?\b", low)
    if year: ident.year = year.group(1)
    ident.product = _first(low, PRODUCTS)
    ident.parallel = _first(low, PARALLELS)
    ident.rookie = bool(re.search(r"\b(rc|rookie)\b", low))
    ident.autograph = bool(re.search(r"\b(auto|autograph|signature)\b", low))
    for k,v in GRADERS.items():
        m = re.search(rf"\b{k}\s*(10|9\.5|9|8\.5|8)\b", low)
        if m:
            ident.grader, ident.grade = v, m.group(1); break
    serial = re.search(r"(?:#?\s*\d+\s*/\s*(\d+)|/\s*(\d+)\b)", low)
    if serial: ident.serial = next(g for g in serial.groups() if g)
    cardnum = re.search(r"(?:card\s*#|#)([a-z0-9-]{1,12})\b", low)
    if cardnum: ident.card_number = cardnum.group(1)

    # Confidence deliberately penalizes ambiguous variation families.
    score = 0.42
    if player.lower() in low: score += 0.16
    if ident.year: score += 0.08
    if ident.product: score += 0.10
    if ident.parallel: score += 0.10
    if ident.grader != "raw": score += 0.08
    if ident.card_number: score += 0.04
    if ident.serial: score += 0.04

    if "stained glass" in low and "jumbo" not in low:
        ident.uncertainty.append("Stained Glass family: verify image is not Jumbo")
        score -= 0.12
    if "mosaic" in low and not ident.parallel:
        ident.uncertainty.append("Mosaic parallel not identified")
        score -= 0.10
    if any(x in low for x in ["lot", "repack", "digital", "custom", "reprint"]):
        ident.uncertainty.append("Excluded/ambiguous listing type")
        score -= 0.35
    if ident.serial and not ident.parallel:
        ident.uncertainty.append("Numbered card but parallel name missing")
        score -= 0.08
    return ident, max(0.0, min(score, 0.99))
