import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import md_builder
from md_builder import CAT_LABELS, TABLE_HEADER, _item_line, _utc_now, build_all, build_category_file, build_readme


class MarkdownBuilderTests(unittest.TestCase):
    def test_table_header_and_separator_have_twelve_columns(self):
        lines = TABLE_HEADER.splitlines()
        self.assertEqual(2, len(lines))
        for line in lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            self.assertEqual(12, len(cells))

    def test_item_row_has_same_number_of_columns_as_header(self):
        item = {
            "title": "Order Book Dynamics",
            "authors": "A. Author",
            "year": "2025",
            "pages": "1-12",
            "venue": "Journal of Market Structure",
            "doc_type": "article",
            "cited_by": 12,
            "source": "CrossRef",
            "access_level": "UNKNOWN",
            "keywords": "market microstructure",
            "abstract": "Order book dynamics are studied.",
            "url": "https://example.com/article",
        }
        row = _item_line(item)
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        self.assertEqual(12, len(cells))
        self.assertIn("[LINK](https://example.com/article)", cells[-1])

    def test_generated_timestamp_is_explicitly_utc(self):
        self.assertTrue(_utc_now().endswith("UTC"))

    def test_category_output_labels_its_row_count(self):
        output = build_category_file(
            "C01_Market_Microstructure_LOB",
            "Market Microstructure & Order Book",
            [{"title": "Order Book Dynamics", "url": "https://example.com/article"}],
        )
        self.assertIn("Items: **1**", output)
        self.assertIn("Generated: ", output)
        self.assertIn(" UTC", output)


    def test_generated_readme_always_links_to_curated_resource_index(self):
        self.assertIn("[RESOURCE_INDEX.md](RESOURCE_INDEX.md)", build_readme())

    def test_build_all_regenerates_curated_resource_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "output"
            category_dir = output_dir / "categories"
            export_dir = root / "external-export"
            categorized = {category: [] for category in CAT_LABELS}
            stats = {
                "unique_records": 0,
                "category_assignments": 0,
                "unclassified_records": 0,
                "source_stats": {},
                "per_category": {category: 0 for category in CAT_LABELS},
                "total": 0,
            }
            with patch.object(md_builder, "OUTPUT_DIR", str(output_dir)), \
                 patch.object(md_builder, "CATS_DIR", str(category_dir)), \
                 patch.object(md_builder, "SDCARD_DIR", str(export_dir)):
                build_all(categorized, stats)

            readme = (output_dir / "README.md").read_text(encoding="utf-8")
            resource_index = (output_dir / "RESOURCE_INDEX.md").read_text(encoding="utf-8")
            self.assertIn("[RESOURCE_INDEX.md](RESOURCE_INDEX.md)", readme)
            self.assertIn("# Curated Resource Index", resource_index)
            self.assertIn("https://docs.python.org/3/", resource_index)


if __name__ == "__main__":
    unittest.main()
