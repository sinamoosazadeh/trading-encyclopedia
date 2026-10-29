import unittest

from md_builder import TABLE_HEADER, _item_line, _utc_now, build_category_file


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


if __name__ == "__main__":
    unittest.main()
