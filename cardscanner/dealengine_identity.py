"""Exact card identity parsing and matching."""
import re, statistics, time
from .identity import parse_identity
from .compkey import player_from_query

# Cached per process to reduce paid search consumption on repeat scans.
_CACHE = {}
TTL = 6 * 3600
BLOCK = re.compile(r'\b(lot|lots|repack|mystery|custom|reprint|digital|break|box|case|pack|proxy|facsimile)\b', re.I)
BAD = re.compile(r'\b(variation|choose|pick your|you pick|random|read description)\b', re.I)

def normalized(s): return re.sub(r'[^a-z0-9]+', ' ', str(s or '').lower()).strip()
def tokens(s): return set(normalized(s).split())

def strict_identity(title, player):
    i, confidence = parse_identity(title, player)
    low = normalized(title)
    # Missing/uncertain parallels are not reliably comparable to solds.
    valid = bool(i.year and i.product and (i.parallel or i.card_number) and player and all(t in tokens(title) for t in tokens(player))
                 and not i.uncertainty and not BLOCK.search(title) and not BAD.search(title))
    if not valid: return None
    # Distinguish common card-family terms that old parser conflated.
    if 'topps chrome update' in low: product='topps chrome update'
    elif 'bowman chrome draft' in low: product='bowman chrome draft'
    else: product=i.product
    parallel = i.parallel or ''
    if 'image variation' in low or 'photo variation' in low: return None
    if 'negative refractor' in low: parallel='negative refractor'
    if 'sepia refractor' in low: parallel='sepia refractor'
    if 'pink refractor' in low: parallel='pink refractor'
    if 'gold refractor' in low: parallel='gold refractor'
    if 'silver prizm' in low: parallel='silver prizm'
    if 'base' in tokens(title) and parallel: return None
    # Raw/graded must not be conflated; explicitly reject missing grade notation on sold.
    return {'player':normalized(player),'year':i.year,'product':product,'parallel':parallel,
            'serial':str(i.serial or ''),'grader':str(i.grader or 'raw'), 'grade':str(i.grade or ''),
            'auto':bool(i.autograph),'number':normalized(i.card_number or ''), 'confidence':confidence}

def matching(active, sold):
    if not sold or BLOCK.search(sold): return False
    player=active['player']
    b=strict_identity(sold, player)
    if not b: return False
    for k in ('player','year','product','parallel','serial','grader','grade','auto'):
        if active[k]!=b[k]: return False
    if active['number'] and b['number'] and active['number']!=b['number']: return False
    # Do not match unnumbered and numbered when seller omits denominator.
    if active['number'] and not b['number']:
        # Number omission in a sold title is too uncertain for an automated deal.
        return False
    return True

def sold_query(title, player, ident):
    bits=[player, ident['year'], ident['product']]
    if ident['parallel']: bits.append(ident['parallel'])
    if ident['number']: bits.append('#'+ident['number'])
    if ident['auto']: bits.append('auto')
    if ident['serial']: bits.append('/'+ident['serial'])
    if ident['grader']!='raw': bits.extend([ident['grader'],ident['grade']])
    return ' '.join(bits)[:195]

