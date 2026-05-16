import unittest

from backend.dal.errors import NotFoundError
from backend.dal.shopping_cart_dao import ShoppingCartDAO
from backend.tests import conftest


class TestShoppingCartIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conftest.configure_test_env()
        if not conftest.floci_available():
            raise unittest.SkipTest("Floci DynamoDB not available")
        conftest.ensure_tables()

    def setUp(self):
        conftest.clear_table("ShoppingCart", "UUID")
        self.dao = ShoppingCartDAO(conftest.dynamodb_resource())

    def test_create_and_read(self):
        created = self.dao.create("cart-1", ["P1", "P2"])
        self.assertEqual(created["UUID"], "CART-1")

        fetched = self.dao.read("cart-1")
        self.assertEqual(fetched["product_ids"], ["p1", "p2"])

    def test_read_missing_returns_not_found(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.read("missing-cart")
        self.assertIn("not found", str(context.exception))
