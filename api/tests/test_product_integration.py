import unittest
from decimal import Decimal

from api.dal.errors import NotFoundError
from api.dal.product_dao import ProductDAO
from api.tests import conftest


class TestProductIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conftest.configure_test_env()
        if not conftest.floci_available():
            raise unittest.SkipTest("Floci DynamoDB not available")
        conftest.ensure_tables()

    def setUp(self):
        conftest.clear_table("Product", "uuid")
        self.dao = ProductDAO(conftest.dynamodb_resource())

    def test_create_and_read(self):
        created = self.dao.create("Apple", 1.5)
        product_id = created["uuid"]

        fetched = self.dao.read(product_id)
        self.assertEqual(fetched["name"], "Apple")
        self.assertEqual(fetched["price"], Decimal("1.5"))

    def test_read_missing_returns_not_found(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.read("550e8400-e29b-41d4-a716-446655440000")
        self.assertIn("not found", str(context.exception))

    def test_list_returns_all_products(self):
        self.dao.create("Apple", 1.5)
        self.dao.create("Banana", 0.75)
        self.dao.create("Cherry", 3.0)

        results = self.dao.list()
        self.assertEqual(len(results), 3)
        names = {r["name"] for r in results}
        self.assertIn("Apple", names)
        self.assertIn("Banana", names)
        self.assertIn("Cherry", names)

    def test_list_empty_when_no_products(self):
        results = self.dao.list()
        self.assertEqual(results, [])

    def test_search_matches_substring(self):
        self.dao.create("Wireless Mouse", 29.99)
        self.dao.create("USB Keyboard", 49.99)
        self.dao.create("Wireless Headphones", 79.99)

        results = self.dao.search("wireless")
        self.assertEqual(len(results), 2)
        names = {r["name"] for r in results}
        self.assertIn("Wireless Mouse", names)
        self.assertIn("Wireless Headphones", names)

    def test_search_case_insensitive(self):
        self.dao.create("Wireless Mouse", 29.99)

        results = self.dao.search("WIRELESS")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Wireless Mouse")

    def test_search_returns_empty_on_no_match(self):
        self.dao.create("Mouse", 29.99)
        self.dao.create("Keyboard", 49.99)

        results = self.dao.search("monitor")
        self.assertEqual(results, [])
