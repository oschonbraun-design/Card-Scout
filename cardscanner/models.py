from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CardIdentity:
    player: str
    year: str = ""
    product: str = ""
    parallel: str = ""
    card_number: str = ""
    serial: str = ""
    rookie: bool = False
    autograph: bool = False
    grader: str = "raw"
    grade: str = ""
    uncertainty: list[str] = field(default_factory=list)

    def fingerprint(self) -> str:
        vals = [self.year, self.product, self.player, self.parallel,
                "rc" if self.rookie else "", self.grader, self.grade, self.card_number]
        return "|".join(v.strip().lower() for v in vals)

@dataclass
class Listing:
    item_id: str
    title: str
    url: str
    price: float
    shipping: float
    player: str
    image_url: str = ""
    seller_feedback_pct: Optional[float] = None
    identity: Optional[CardIdentity] = None
    confidence: float = 0.0

    @property
    def landed_cost(self) -> float:
        return self.price + self.shipping
