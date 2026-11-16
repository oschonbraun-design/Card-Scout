import csv
from datetime import date, datetime
from pathlib import Path
from statistics import median

class CsvCompProvider:
    """Verified exact-card comps. This intentionally does not scrape sold listings."""
    def __init__(self, path: str, max_age_days: int = 120):
        self.path = Path(path); self.max_age_days = max_age_days

    def get(self, fingerprint: str):
        if not self.path.exists(): return []
        out=[]; today=date.today()
        with self.path.open(newline="", encoding="utf-8") as f:
            rows=(r for r in f if not r.lstrip().startswith("#"))
            for r in csv.DictReader(rows):
                if r.get("fingerprint", "").strip().lower() != fingerprint.lower(): continue
                try:
                    d=datetime.strptime(r["sold_date"], "%Y-%m-%d").date()
                    if (today-d).days <= self.max_age_days:
                        out.append({**r, "sold_price":float(r["sold_price"]), "sold_date":d})
                except (ValueError, KeyError): pass
        return out

def comp_stats(comps):
    if not comps: return None
    prices=sorted(c["sold_price"] for c in comps)
    med=median(prices)
    # Robust band to expose volatile cards rather than hiding it.
    lo=prices[max(0, int(len(prices)*0.2)-1)]
    hi=prices[min(len(prices)-1, int(len(prices)*0.8))]
    return {"count":len(prices), "median":med, "low":lo, "high":hi, "prices":prices}
