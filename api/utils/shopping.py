import uuid
from decimal import Decimal
# Use dynamodb

class Product:
    """A simple product class that represents an item in a shopping cart."""
    def __init__(self, name, price):
        self.id = uuid.uuid4()
        self.name = name
        self.price = price

    def to_dict(self) -> dict:
        """Serialize for DynamoDB storage: {uuid: str, name: str, price: Decimal}."""
        return {
            "uuid": str(self.id),
            "name": self.name,
            "price": Decimal(str(self.price)),
        }

    @staticmethod
    def from_dict(data: dict) -> "Product":
        """Deserialize from DynamoDB storage."""
        product = Product(name=data["name"], price=float(data["price"]))
        product.id = uuid.UUID(data["uuid"])
        return product

class ShoppingCart:
    """A simple shopping cart class that allows adding and removing products."""
    def __init__(self, tax_rate = 0.07):
        self.items = []
        self.tax_rate = tax_rate

    def add_product(self, product: Product):
        """Add a product to the shopping cart."""
        self.items.append(product)

    def remove_product(self, product_id):
        """Remove a product from the shopping cart."""
        self.items = [item for item in self.items if item.id != product_id]
    
    def total(self):
        """Calculate the total cost of the items in the shopping cart.
        Handles both Product objects and product dicts with 'price' key.
        """
        subtotal = 0
        for item in self.items:
            if isinstance(item, dict):
                subtotal += float(item.get("price", 0))
            else:
                subtotal += item.price
        subtotal = round(subtotal, 2)
        tax = round(subtotal * self.tax_rate, 2)
        return round(subtotal + tax, 2)

    def to_dict(self) -> dict:
        """Serialize cart for storage: {items: [...], tax_rate: float}."""
        return {
            "items": [
                item if isinstance(item, dict) else item.to_dict()
                for item in self.items
            ],
            "tax_rate": self.tax_rate,
        }

    @staticmethod
    def from_dict(data: dict) -> "ShoppingCart":
        """Deserialize from stored dict."""
        cart = ShoppingCart(tax_rate=data.get("tax_rate", 0.07))
        for item_data in data.get("items", []):
            if isinstance(item_data, dict) and "uuid" in item_data:
                cart.items.append(item_data)
            elif isinstance(item_data, Product):
                cart.items.append(item_data)
        return cart