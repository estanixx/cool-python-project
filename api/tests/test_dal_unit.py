import unittest
from decimal import Decimal
from api.dal.dictionary_dao import DictionaryDAO
from api.dal.product_dao import ProductDAO
from api.dal.shopping_cart_dao import ShoppingCartDAO
from api.dal.errors import ValidationError, NotFoundError


class TestDALNormalization(unittest.TestCase):
    def test_dictionary_normalizes_word_casing(self):
        dao = DictionaryDAO(_FakeDynamoResource())
        self.assertEqual(dao._normalize_word("apple"), "Apple")
        self.assertEqual(dao._normalize_word("BaNaNa"), "Banana")

    def test_dictionary_requires_word(self):
        dao = DictionaryDAO(_FakeDynamoResource())
        with self.assertRaises(ValidationError):
            dao._normalize_word("")

    def test_product_uuid_normalization(self):
        dao = ProductDAO(_FakeDynamoResource())
        self.assertEqual(
            dao._normalize_uuid("550E8400-E29B-41D4-A716-446655440000"),
            "550e8400-e29b-41d4-a716-446655440000",
        )

    def test_product_uuid_requires_valid_value(self):
        dao = ProductDAO(_FakeDynamoResource())
        with self.assertRaises(ValidationError):
            dao._normalize_uuid("not-a-uuid")


class TestProductDAOListSearch(unittest.TestCase):
    def test_list_returns_all_items(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([
            {"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")},
            {"uuid": "p2", "name": "Keyboard", "price": Decimal("49.99")},
            {"uuid": "p3", "name": "Monitor", "price": Decimal("199.99")},
        ]))
        results = dao.list()
        self.assertEqual(len(results), 3)

    def test_list_returns_empty_when_no_items(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([]))
        results = dao.list()
        self.assertEqual(results, [])

    def test_search_filters_by_substring(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([
            {"uuid": "p1", "name": "Wireless Mouse", "price": Decimal("29.99")},
            {"uuid": "p2", "name": "USB Keyboard", "price": Decimal("49.99")},
            {"uuid": "p3", "name": "Wireless Headphones", "price": Decimal("79.99")},
        ]))
        results = dao.search("wireless")
        self.assertEqual(len(results), 2)
        names = {r["name"] for r in results}
        self.assertIn("Wireless Mouse", names)
        self.assertIn("Wireless Headphones", names)

    def test_search_is_case_insensitive(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([
            {"uuid": "p1", "name": "Wireless Mouse", "price": Decimal("29.99")},
        ]))
        results = dao.search("WIRELESS")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Wireless Mouse")

    def test_search_returns_empty_on_no_match(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([
            {"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")},
            {"uuid": "p2", "name": "Keyboard", "price": Decimal("49.99")},
        ]))
        results = dao.search("monitor")
        self.assertEqual(results, [])

    def test_search_requires_term(self):
        dao = ProductDAO(_FakeDynamoResourceWithItems([]))
        with self.assertRaises(ValidationError):
            dao.search("")


class TestShoppingCartDAOProducts(unittest.TestCase):
    def test_create_with_products_list(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
            {"uuid": "p2", "name": "Keyboard", "price": 49.99},
        ]
        result = dao.create("cart-1", products)
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 2)

    def test_create_validates_products_structure(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        with self.assertRaises(ValidationError):
            dao.create("cart-1", [{"uuid": "p1"}])  # missing name, price

    def test_create_requires_products_list(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        with self.assertRaises(ValidationError):
            dao.create("cart-1", None)

    def test_update_with_products_list(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [{"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")}]}
        ]))
        new_products = [{"uuid": "p2", "name": "Keyboard", "price": 49.99}]
        result = dao.update("cart-1", new_products)
        self.assertIn("products", result)

    def test_read_backward_compat_with_product_ids(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "product_ids": ["p1", "p2"]}
        ]))
        result = dao.read("cart-1")
        self.assertIn("products", result)
        self.assertEqual(result["products"], [])

    def test_read_returns_products_when_present(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [{"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")}]}
        ]))
        result = dao.read("cart-1")
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["name"], "Mouse")


class TestShoppingCartDAOMutations(unittest.TestCase):
    def test_add_product_appends_to_list(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [{"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")}]}
        ]))
        result = dao.add_product("cart-1", {"uuid": "p2", "name": "Keyboard", "price": 49.99})
        self.assertEqual(len(result["products"]), 2)

    def test_add_product_to_nonexistent_cart_raises(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        with self.assertRaises(NotFoundError):
            dao.add_product("cart-999", {"uuid": "p1", "name": "Mouse", "price": 29.99})

    def test_add_product_validates_product_dict(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": []}
        ]))
        with self.assertRaises(ValidationError):
            dao.add_product("cart-1", {"uuid": "p1"})  # missing name, price

    def test_remove_product_filters_by_uuid(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [
                {"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")},
                {"uuid": "p2", "name": "Keyboard", "price": Decimal("49.99")},
            ]}
        ]))
        result = dao.remove_product("cart-1", "p1")
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["uuid"], "p2")

    def test_remove_nonexistent_product_no_error(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [
                {"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")},
            ]}
        ]))
        result = dao.remove_product("cart-1", "p999")
        self.assertEqual(len(result["products"]), 1)

    def test_get_total_calculates_correctly(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": [
                {"uuid": "p1", "name": "Mouse", "price": Decimal("100.00")},
                {"uuid": "p2", "name": "Keyboard", "price": Decimal("50.00")},
            ]}
        ]))
        result = dao.get_total("cart-1", tax_rate=0.10)
        self.assertAlmostEqual(result["subtotal"], 150.00, places=2)
        self.assertAlmostEqual(result["tax"], 15.00, places=2)
        self.assertAlmostEqual(result["total"], 165.00, places=2)

    def test_get_total_empty_cart(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([
            {"UUID": "CART-1", "products": []}
        ]))
        result = dao.get_total("cart-1", tax_rate=0.10)
        self.assertEqual(result["subtotal"], 0.0)
        self.assertEqual(result["tax"], 0.0)
        self.assertEqual(result["total"], 0.0)

    def test_get_total_nonexistent_cart_raises(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        with self.assertRaises(NotFoundError):
            dao.get_total("cart-999")

    def test_read_products_helper_with_legacy_format(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        result = dao._read_products({"product_ids": ["p1", "p2"]})
        self.assertEqual(result, [])

    def test_read_products_helper_with_products_format(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        products = [{"uuid": "p1", "name": "Mouse", "price": Decimal("29.99")}]
        result = dao._read_products({"products": products})
        self.assertEqual(result, products)

    def test_read_products_helper_empty(self):
        dao = ShoppingCartDAO(_FakeDynamoResourceWithItems([]))
        result = dao._read_products({})
        self.assertEqual(result, [])


class _FakeTable:
    def __init__(self, items=None):
        self._items = items or []

    def put_item(self, Item=None, **_kwargs):
        if Item:
            self._items.append(Item)
        return {}

    def get_item(self, Key=None, **_kwargs):
        if Key:
            for item in self._items:
                if item.get("UUID") == Key.get("UUID") or item.get("uuid") == Key.get("uuid"):
                    return {"Item": item}
        return {}

    def update_item(self, Key=None, UpdateExpression=None, ExpressionAttributeValues=None, **_kwargs):
        for item in self._items:
            if item.get("UUID") == Key.get("UUID"):
                if ExpressionAttributeValues:
                    for key, value in ExpressionAttributeValues.items():
                        attr_name = key.lstrip(":")
                        item[attr_name] = value
                return {"Attributes": item}
        # Simulate condition failure for non-existent items
        exc = Exception("ConditionalCheckFailedException")
        exc.response = {"Error": {"Code": "ConditionalCheckFailedException"}}
        raise exc

    def delete_item(self, **_kwargs):
        return {"Attributes": {}}

    def scan(self, **_kwargs):
        return {"Items": self._items}


class _FakeDynamoResource:
    def Table(self, _name):
        return _FakeTable()


class _FakeDynamoResourceWithItems:
    def __init__(self, items):
        self._items = items

    def Table(self, _name):
        return _FakeTable(self._items)
