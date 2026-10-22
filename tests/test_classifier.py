import unittest

from classifier import classify, classify_with_evidence


class ClassificationTests(unittest.TestCase):
    def test_query_bucket_does_not_force_irrelevant_document_into_category(self):
        categories = classify(
            "NF-kB signaling in inflammation",
            source_category="F04_SmartMoney_ICT",
        )
        self.assertNotIn("F04_SmartMoney_ICT", categories)
        self.assertEqual([], categories)

    def test_ambiguous_ict_acronym_without_trading_context_is_not_enough(self):
        categories = classify(
            "ICT interventions and outcomes in oncology",
            source_category="F04_SmartMoney_ICT",
        )
        self.assertNotIn("F04_SmartMoney_ICT", categories)

    def test_smart_money_concepts_have_direct_domain_evidence(self):
        categories = classify("Smart Money Concepts: Fair Value Gaps and Order Blocks")
        self.assertIn("F04_SmartMoney_ICT", categories)

    def test_ict_with_trading_context_is_classified(self):
        categories = classify("ICT trading setup using liquidity and fair value gaps")
        self.assertIn("F04_SmartMoney_ICT", categories)

    def test_financial_forecasting_context_is_classified(self):
        categories = classify("Forecasting stock returns with volatility models")
        self.assertIn("A03_Prediction_Forecasting", categories)

    def test_evidence_is_inspectable_and_not_a_probability(self):
        rows = classify_with_evidence(
            "Smart Money Concepts: Fair Value Gaps and Order Blocks",
            source_category="F04_SmartMoney_ICT",
        )
        row = next(item for item in rows if item["category"] == "F04_SmartMoney_ICT")
        self.assertTrue(row["direct_domain_evidence"])
        self.assertTrue(row["matched_patterns"])
        self.assertNotIn("probability", row)


if __name__ == "__main__":
    unittest.main()
