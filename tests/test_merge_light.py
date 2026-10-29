import unittest

import merge_light


class LightweightMergeImportTests(unittest.TestCase):
    def test_module_exposes_main_without_running_pipeline_on_import(self):
        self.assertTrue(callable(merge_light.main))


if __name__ == "__main__":
    unittest.main()
