import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from web_resource_collector import (
    DEFAULT_QUERY_PLAN,
    ProviderQuotaError,
    fetch_json,
    load_plan,
    merge_records,
    normalize_github,
    normalize_huggingface,
    normalize_zenodo,
    select_queries,
    validate_plan,
    write_jsonl_atomic,
)


class WebResourceCollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load_plan(DEFAULT_QUERY_PLAN)
        cls.queries = cls.plan["queries"]

    def test_query_plan_has_unique_ids_and_known_stages(self):
        self.assertEqual([], validate_plan(self.plan))
        ids = [query["id"] for query in self.queries]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(40, len(ids))

    def test_query_selection_is_provider_scoped_and_bounded(self):
        selected = select_queries(self.plan, "github", 3)
        self.assertEqual(3, len(selected))
        self.assertTrue(all(query["provider"] == "github" for query in selected))
        with self.assertRaises(ValueError):
            select_queries(self.plan, "github", 51)

    def test_unknown_query_id_is_rejected(self):
        with self.assertRaises(ValueError):
            select_queries(self.plan, "github", 3, ["does-not-exist"])

    def test_github_record_retains_source_url_and_query_provenance(self):
        query = next(query for query in self.queries if query["provider"] == "github")
        record = normalize_github({
            "full_name": "QuantConnect/Lean",
            "html_url": "https://github.com/QuantConnect/Lean",
            "description": "Algorithmic trading engine",
            "stargazers_count": 100,
            "forks_count": 20,
            "language": "C#",
            "license": {"spdx_id": "Apache-2.0"},
            "updated_at": "2026-01-01T00:00:00Z",
        }, query)
        self.assertIsNotNone(record)
        self.assertEqual("github:QuantConnect/Lean", record["id"])
        self.assertEqual(query["id"], record["search_query_id"])
        self.assertEqual("unreviewed", record["review_status"])

    def test_huggingface_model_url_and_metadata_are_normalized(self):
        query = next(query for query in self.queries if query["provider"] == "huggingface_models")
        record = normalize_huggingface({
            "id": "example/financial-model",
            "downloads": 120,
            "likes": 7,
            "lastModified": "2026-01-01T00:00:00Z",
            "pipeline_tag": "text-classification",
            "tags": ["finance", "sentiment"],
            "private": False,
            "gated": False,
        }, query)
        self.assertEqual("https://huggingface.co/example/financial-model", record["url"])
        self.assertEqual(120, record["metadata"]["downloads"])
        self.assertEqual("unreviewed", record["review_status"])

    def test_huggingface_dataset_uses_dataset_url_namespace(self):
        query = next(query for query in self.queries if query["provider"] == "huggingface_datasets")
        record = normalize_huggingface({"id": "example/market-data", "tags": ["time-series"]}, query)
        self.assertEqual("https://huggingface.co/datasets/example/market-data", record["url"])
        self.assertEqual("dataset", record["type"])

    def test_zenodo_record_preserves_doi_and_license_metadata(self):
        query = next(query for query in self.queries if query["provider"] == "zenodo")
        record = normalize_zenodo({
            "id": 12345,
            "updated": "2026-01-01T00:00:00Z",
            "links": {"html": "https://zenodo.org/records/12345"},
            "metadata": {
                "title": "A Market Microstructure Dataset",
                "doi": "10.5281/zenodo.12345",
                "description": "<p>Market data for a research project.</p>",
                "publication_date": "2025-10-10",
                "creators": [{"name": "Example Author"}],
                "keywords": ["limit order book"],
                "license": {"id": "cc-by-4.0"},
                "access_right": "open",
                "resource_type": {"title": "Dataset"},
            },
        }, query)
        self.assertEqual("zenodo:12345", record["id"])
        self.assertEqual("10.5281/zenodo.12345", record["metadata"]["doi"])
        self.assertIn("Market data", record["description"])
        self.assertEqual("Dataset", record["type"])

    def test_merge_preserves_all_query_provenance(self):
        first = {"id": "github:owner/repo", "name": "Repo", "search_query_id": "query-a", "metadata": {"stars": 1}}
        second = {"id": "github:owner/repo", "name": "Repo", "search_query_id": "query-b", "metadata": {"forks": 2}}
        merged, new_count = merge_records([first], [second])
        self.assertEqual(0, new_count)
        self.assertEqual(["query-a", "query-b"], merged[0]["query_provenance"])
        self.assertEqual({"stars": 1, "forks": 2}, merged[0]["metadata"])

    def test_atomic_jsonl_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subdir" / "records.jsonl"
            records = [{"id": "test:1", "name": "One"}, {"id": "test:2", "name": "Two"}]
            write_jsonl_atomic(path, records)
            decoded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records, decoded)

    def test_http_429_is_bounded_and_reported_as_quota_failure(self):
        response = requests.Response()
        response.status_code = 429
        response._content = b'{"message":"rate limited"}'
        response.headers = {}
        with patch("web_resource_collector.requests.get", return_value=response), \
             patch("web_resource_collector.time.sleep") as sleep:
            with self.assertRaises(ProviderQuotaError):
                fetch_json("github", "https://api.github.com/search/repositories", {"q": "test"}, max_retries=0)
            sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
