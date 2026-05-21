import unittest

from api.dal.errors import NotFoundError
from api.dal.shopping_cart_dao import ShoppingCartDAO
from api.tests import conftest


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
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
            {"uuid": "p2", "name": "Keyboard", "price": 49.99},
        ]
        created = self.dao.create("cart-1", products)
        self.assertEqual(created["UUID"], "CART-1")

        fetched = self.dao.read("cart-1")
        self.assertEqual(len(fetched["products"]), 2)
        self.assertEqual(fetched["products"][0]["uuid"], "p1")

    def test_read_missing_returns_not_found(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.read("missing-cart")
        self.assertIn("not found", str(context.exception))

    def test_add_product_to_cart(self):
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
        ]
        self.dao.create("cart-add-test", products)

        new_product = {"uuid": "p2", "name": "Keyboard", "price": 49.99}
        result = self.dao.add_product("cart-add-test", new_product)

        self.assertEqual(len(result["products"]), 2)
        uuids = {p["uuid"] for p in result["products"]}
        self.assertIn("p1", uuids)
        self.assertIn("p2", uuids)

    def test_add_product_to_nonexistent_cart_raises(self):
        with self.assertRaises(NotFoundError) as context:
            self.dao.add_product("nonexistent-cart", {"uuid": "p1", "name": "Mouse", "price": 29.99})
        self.assertIn("not found", str(context.exception))

    def test_remove_product_from_cart(self):
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
            {"uuid": "p2", "name": "Keyboard", "price": 49.99},
            {"uuid": "p3", "name": "Monitor", "price": 199.99},
        ]
        self.dao.create("cart-remove-test", products)

        result = self.dao.remove_product("cart-remove-test", "p2")

        self.assertEqual(len(result["products"]), 2)
        uuids = {p["uuid"] for p in result["products"]}
        self.assertIn("p1", uuids)
        self.assertNotIn("p2", uuids)
        self.assertIn("p3", uuids)

    def test_remove_nonexistent_product_no_error(self):
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
        ]
        self.dao.create("cart-remove-missing", products)

        result = self.dao.remove_product("cart-remove-missing", "p999")

        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["uuid"], "p1")

    def test_get_total_with_tax(self):
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 100.00},
            {"uuid": "p2", "name": "Keyboard", "price": 50.00},
        ]
        self.dao.create("cart-total-test", products)

        result = self.dao.get_total("cart-total-test", tax_rate=0.10)

        self.assertAlmostEqual(result["subtotal"], 150.00, places=2)
        self.assertAlmostEqual(result["tax"], 15.00, places=2)
        self.assertAlmostEqual(result["total"], 165.00, places=2)

    def test_get_total_empty_cart(self):
        self.dao.create("cart-empty-total", [])

        result = self.dao.get_total("cart-empty-total", tax_rate=0.07)

        self.assertEqual(result["subtotal"], 0.0)
        self.assertEqual(result["tax"], 0.0)
        self.assertEqual(result["total"], 0.0)

    def test_get_total_default_tax_rate(self):
        products = [
            {"uuid": "p1", "name": "Item", "price": 100.00},
        ]
        self.dao.create("cart-default-tax", products)

        result = self.dao.get_total("cart-default-tax")

        self.assertAlmostEqual(result["subtotal"], 100.00, places=2)
        self.assertAlmostEqual(result["tax"], 7.00, places=2)
        self.assertAlmostEqual(result["total"], 107.00, places=2)
