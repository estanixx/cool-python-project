import unittest
from decimal import Decimal
from api.utils import ShoppingCart, Product

class TestShoppingCart(unittest.TestCase):
    """Unit tests for the ShoppingCart class."""
    def setUp(self):
        """Set up a shopping cart and a product for testing."""
        self.cart = ShoppingCart()
        self.product = Product("apple", 1.0)

    def test_add_product(self):
        """Test adding a product to the shopping cart."""
        self.cart.add_product(self.product)
        self.assertIn(self.product, self.cart.items)

    def test_remove_product(self):
        """Test removing a product from the shopping cart."""
        self.cart.add_product(self.product)
        self.cart.remove_product(self.product.id)
        self.assertNotIn(self.product, self.cart.items)

    def test_total(self):
        """Test calculating the total cost of the items in the shopping cart."""
        self.cart.add_product(self.product)
        self.assertEqual(self.cart.total(), 1.07)

    def test_total_with_product_dicts(self):
        """Test total calculation with product dicts instead of Product objects."""
        self.cart.items = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
            {"uuid": "p2", "name": "Keyboard", "price": 49.99},
        ]
        self.assertAlmostEqual(self.cart.total(), 85.58, places=2)

    def test_total_empty_cart(self):
        """Test total calculation with empty cart."""
        self.assertEqual(self.cart.total(), 0.0)


class TestProductSerialization(unittest.TestCase):
    """Unit tests for Product to_dict/from_dict serialization."""

    def test_to_dict_returns_expected_keys(self):
        product = Product("Mouse", 29.99)
        result = product.to_dict()
        self.assertIn("uuid", result)
        self.assertIn("name", result)
        self.assertIn("price", result)
        self.assertEqual(result["name"], "Mouse")
        self.assertIsInstance(result["price"], Decimal)

    def test_from_dict_round_trip(self):
        original = Product("Keyboard", 49.99)
        data = original.to_dict()
        restored = Product.from_dict(data)
        self.assertEqual(restored.name, original.name)
        self.assertAlmostEqual(restored.price, original.price, places=2)
        self.assertEqual(str(restored.id), str(original.id))

    def test_from_dict_with_decimal_price(self):
        data = {"uuid": "550e8400-e29b-41d4-a716-446655440000", "name": "Monitor", "price": Decimal("199.99")}
        product = Product.from_dict(data)
        self.assertEqual(product.name, "Monitor")
        self.assertAlmostEqual(product.price, 199.99, places=2)


class TestShoppingCartSerialization(unittest.TestCase):
    """Unit tests for ShoppingCart to_dict/from_dict serialization."""

    def test_to_dict_with_products(self):
        cart = ShoppingCart(tax_rate=0.10)
        product = Product("Mouse", 29.99)
        cart.add_product(product)
        result = cart.to_dict()
        self.assertIn("items", result)
        self.assertIn("tax_rate", result)
        self.assertEqual(result["tax_rate"], 0.10)
        self.assertEqual(len(result["items"]), 1)

    def test_to_dict_with_product_dicts(self):
        cart = ShoppingCart()
        cart.items = [{"uuid": "p1", "name": "Mouse", "price": 29.99}]
        result = cart.to_dict()
        self.assertEqual(result["items"][0]["name"], "Mouse")

    def test_from_dict_restores_items(self):
        data = {
            "items": [
                {"uuid": "p1", "name": "Mouse", "price": 29.99},
                {"uuid": "p2", "name": "Keyboard", "price": 49.99},
            ],
            "tax_rate": 0.10,
        }
        cart = ShoppingCart.from_dict(data)
        self.assertEqual(len(cart.items), 2)
        self.assertAlmostEqual(cart.total(), 87.98, places=2)

    def test_from_dict_empty_items(self):
        data = {"items": [], "tax_rate": 0.07}
        cart = ShoppingCart.from_dict(data)
        self.assertEqual(len(cart.items), 0)
        self.assertEqual(cart.total(), 0.0)