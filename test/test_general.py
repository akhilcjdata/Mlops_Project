"""General test module with basic test cases."""

import unittest


class TestGeneral(unittest.TestCase):
    """Test cases for general functionality."""

    def test_simple_assertion(self):
        """Test a simple assertion."""
        self.assertTrue(True)

    def test_math_operations(self):
        """Test basic math operations."""
        self.assertEqual(2 + 2, 4)
        self.assertEqual(10 - 5, 5)
        self.assertEqual(3 * 3, 9)

    def test_string_manipulation(self):
        """Test string operations."""
        self.assertEqual("hello" + " world", "hello world")
        self.assertIn("test", "testing")

    def test_list_operations(self):
        """Test list operations."""
        lst = [1, 2, 3]
        self.assertEqual(len(lst), 3)
        self.assertIn(2, lst)

    def test_dict_operations(self):
        """Test dictionary operations."""
        d = {"key": "value"}
        self.assertEqual(d["key"], "value")
        self.assertIn("key", d)


if __name__ == "__main__":
    unittest.main()
