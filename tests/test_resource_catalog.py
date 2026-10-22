import tempfile
import unittest
from pathlib import Path

from resource_catalog import (
    DEFAULT_CATALOG,
    export_markdown,
    load_catalog,
    search_articles,
    search_registry,
    validate_catalog,
)


class ResourceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(DEFAULT_CATALOG)

    def test_catalog_has_unique_valid_metadata(self):
        self.assertEqual([], validate_catalog(self.catalog))
        self.assertGreaterEqual(len(self.catalog["resources"]), 50)

    def test_registry_search_finds_python_documentation(self):
        results = search_registry(
            self.catalog,
            "Python Documentation",
            limit=10,
            resource_type="programming-docs",
        )
        self.assertTrue(any(item["id"] == "lang-python" for item in results))

    def test_registry_stage_filter_uses_lifecycle_metadata(self):
        results = search_registry(
            self.catalog,
            "exchange",
            limit=20,
            stage="exchange-integration",
        )
        self.assertTrue(all("exchange-integration" in item["lifecycle_stages"] for item in results))
        self.assertTrue(results)

    def test_generated_article_table_search_is_local_and_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            table = directory / "C01_OrderBook.md"
            table.write_text(
                "# Sample\n\n"
                "| Title | Authors | Year | Link |\n"
                "|---|---|---|---|\n"
                "| Liquidity and Order Book Dynamics | A. Author | 2025 | "
                "[LINK](https://example.com/paper) |\n",
                encoding="utf-8",
            )
            results = search_articles("liquidity order book", directory, limit=5)
            self.assertEqual(1, len(results))
            self.assertEqual("https://example.com/paper", results[0]["url"])

    def test_markdown_export_contains_source_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "RESOURCE_INDEX.md"
            export_markdown(self.catalog, target)
            content = target.read_text(encoding="utf-8")
            self.assertIn("# Curated Resource Index", content)
            self.assertIn("https://docs.python.org/3/", content)
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
