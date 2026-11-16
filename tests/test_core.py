import unittest
from cardscanner.identity import parse_identity
from cardscanner.models import Listing
from cardscanner.scoring import score_deal

class Tests(unittest.TestCase):
    def test_jumbo_distinguished(self):
        a,_=parse_identity("2024 Mosaic Drake Maye Stained Glass Jumbo RC", "Drake Maye")
        b,_=parse_identity("2024 Mosaic Drake Maye Stained Glass RC", "Drake Maye")
        self.assertEqual(a.parallel,"stained glass jumbo")
        self.assertEqual(b.parallel,"stained glass")
        self.assertNotEqual(a.fingerprint(),b.fingerprint())
        self.assertTrue(b.uncertainty)
    def test_score(self):
        l=Listing("1","x","u",110,5,"Drake Maye",confidence=.95)
        cfg={"minimum_comps":3,"minimum_match_confidence":.88,"estimated_resale_fee_rate":.13,
             "estimated_outbound_shipping":5,"minimum_estimated_profit":15,
             "deal_thresholds":{"watch":.2,"good":.25,"steal":.3}}
        r=score_deal(l,{"count":5,"median":170,"low":160,"high":180},cfg)
        self.assertEqual(r["level"],"STEAL")
if __name__=="__main__": unittest.main()
