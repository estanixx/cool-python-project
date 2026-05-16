import uuid
# Use dynamodb

class Product:
    """A simple product class that represents an item in a shopping cart."""
    def __init__(self, name, price):
        self.id = uuid.uuid4()
        self.name = name
        self.price = price

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
        """Calculate the total cost of the items in the shopping cart."""
        subtotal = sum(item.price for item in self.items)
        tax = subtotal * self.tax_rate
        return subtotal + tax