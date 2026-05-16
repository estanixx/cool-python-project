import unittest
from backend.utils import ShoppingCart, Product

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