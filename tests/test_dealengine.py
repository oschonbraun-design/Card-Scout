import unittest
from unittest.mock import patch
from cardscanner.dealengine import strict_identity, matching, evaluate_candidate, _CACHE

T='2025 Topps Chrome Dylan Harper Gold Refractor #125 PSA 10'

class DealTests(unittest.TestCase):
    def setUp(self): _CACHE.clear()
    def test_no_cross_grade_parallel_or_number(self):
        a=strict_identity(T,'Dylan Harper')
        self.assertTrue(matching(a,T))
        self.assertFalse(matching(a,T.replace('PSA 10','PSA 9')))
        self.assertFalse(matching(a,T.replace('Gold','Blue')))
        self.assertFalse(matching(a,T.replace('#125','#126')))
    @patch('cardscanner.dealengine.historical')
    def test_cheap_and_expensive(self, sold):
        sold.return_value=([{'title':T,'price':p,'date':'2026-11-01','url':'https://example.com','match':99} for p in (100,105,110)],1,3,'')
        self.assertEqual(evaluate_candidate({'title':T,'total':65},'Dylan Harper')['status'],'deal')
        self.assertEqual(evaluate_candidate({'title':T,'total':180},'Dylan Harper')['status'],'pass')
    @patch('cardscanner.dealengine.historical')
    def test_one_sale_never_qualifies(self, sold):
        sold.return_value=([{'title':T,'price':110,'date':'2026-11-01','url':'https://example.com','match':99}],1,1,'')
        self.assertEqual(evaluate_candidate({'title':T,'total':30},'Dylan Harper')['status'],'unverified')

if __name__=='__main__':unittest.main()

class IdentityRegressionTests(unittest.TestCase):
    def test_base_card_without_number_is_valid(self):
        from cardscanner.dealengine_identity import strict_identity
        self.assertIsNotNone(strict_identity('2023 Panini Prizm CJ Stroud PSA 10','CJ Stroud'))
    def test_number_mismatch_is_rejected(self):
        from cardscanner.dealengine_identity import strict_identity, matching
        a=strict_identity('2023 Panini Prizm CJ Stroud Silver #125 PSA 10','CJ Stroud')
        self.assertFalse(matching(a,'2023 Panini Prizm CJ Stroud Silver #126 PSA 10'))
    def test_parallel_mismatch_is_rejected(self):
        from cardscanner.dealengine_identity import strict_identity, matching
        a=strict_identity('2023 Panini Prizm CJ Stroud Silver PSA 10','CJ Stroud')
        self.assertFalse(matching(a,'2023 Panini Prizm CJ Stroud Gold PSA 10'))
