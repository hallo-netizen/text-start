import unittest

from k0.engine.isolation_guard import check


class IsolationTests(unittest.TestCase):
    def test_k0_isolation(self):
        receipt = check()
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["external_runtime_references"], "NONE")
        self.assertFalse(receipt["publish_allowed"])


if __name__ == "__main__":
    unittest.main()
