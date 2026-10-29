import unittest

from utils import deduplicate, get_access_level, is_valid_url, normalize


class UtilityTests(unittest.TestCase):
    def test_normalize_query_terms(self):
        self.assertEqual("market microstructure", normalize("Market_Microstructure"))

    def test_url_requires_valid_absolute_http_scheme(self):
        self.assertTrue(is_valid_url("https://example.com/docs"))
        self.assertFalse(is_valid_url("ftp://example.com/docs"))
        self.assertFalse(is_valid_url("https://user:password@example.com/docs"))
        self.assertFalse(is_valid_url("https:///missing-host"))
        self.assertFalse(is_valid_url("https://example.com:bad/path"))

    def test_host_matching_does_not_accept_a_lookalike_domain(self):
        access = get_access_level({"url": "https://github.com.evil.invalid/path"})
        self.assertEqual("UNKNOWN", access)

    def test_duplicate_doi_merges_missing_fields_and_tracks_sources(self):
        records = [
            {
                "title": "A Study of Financial Markets",
                "doi": "https://doi.org/10.1234/ABC",
                "authors": "A. Author",
                "year": "2024",
                "source": "CrossRef",
                "abstract": "",
            },
            {
                "title": "A Study of Financial Markets",
                "doi": "doi:10.1234/abc",
                "authors": "A. Author",
                "year": "2024",
                "source": "OpenAlex",
                "abstract": "A useful abstract.",
            },
        ]
        result = deduplicate(records)
        self.assertEqual(1, len(result))
        self.assertEqual("A useful abstract.", result[0]["abstract"])
        self.assertIn("CrossRef", result[0]["source_provenance"])
        self.assertIn("OpenAlex", result[0]["source_provenance"])

    def test_similar_title_prefixes_are_not_merged(self):
        prefix = "A" * 100
        records = [
            {"title": prefix + " alpha", "authors": "A. Author", "year": "2024"},
            {"title": prefix + " beta", "authors": "A. Author", "year": "2024"},
        ]
        self.assertEqual(2, len(deduplicate(records)))

    def test_distinct_dois_are_not_merged_for_identical_titles(self):
        records = [
            {"title": "Same title", "doi": "10.1234/first", "authors": "A", "year": "2022"},
            {"title": "Same title", "doi": "10.1234/second", "authors": "A", "year": "2022"},
        ]
        self.assertEqual(2, len(deduplicate(records)))

    def test_records_without_safe_identity_are_retained(self):
        records = [{"title": "Unknown source"}, {"title": "Unknown source"}]
        self.assertEqual(2, len(deduplicate(records)))


if __name__ == "__main__":
    unittest.main()
