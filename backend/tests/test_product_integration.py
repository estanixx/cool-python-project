import unittest

from backend.dal.errors import NotFoundError
from backend.dal.product_dao import ProductDAO
from backend.tests import conftest


class TestProductIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conftest.configure_test_env()
        if not conftest.floci_available():
            raise unittest.SkipTest("Floci DynamoDB not available")
        conftest.ensure_tables()

    def setUp(self):
        conftest.clear_table("Product", "product_id")
        self.dao = ProductDAO(conftest.dynamodb_resource())

    def test_create_and_read(self):
        created = self.dao.create("Apple", 1.5)
        product_id = created["product_id"]

        fetched = self.dao.read(product_id)
        self.assertEqual(fetched["name"], "Apple")
        self.assertEqual(fetched["price"], 1.5)

    def test_read_missing_returns_not_found(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.read("550e8400-e29b-41d4-a716-446655440000")
        self.assertIn("not found", str(context.exception))
