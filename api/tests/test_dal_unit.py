import unittest
from api.dal.dictionary_dao import DictionaryDAO
from api.dal.product_dao import ProductDAO
from api.dal.shopping_cart_dao import ShoppingCartDAO
from api.dal.errors import ValidationError


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

    def test_shopping_cart_normalizes_keys(self):
        dao = ShoppingCartDAO(_FakeDynamoResource())
        self.assertEqual(dao._normalize_cart_id(" cart-1 "), "CART-1")
        self.assertEqual(
            dao._normalize_product_ids([" ABC ", "Def "]),
            ["abc", "def"],
        )

    def test_shopping_cart_requires_product_list(self):
        dao = ShoppingCartDAO(_FakeDynamoResource())
        with self.assertRaises(ValidationError):
            dao._normalize_product_ids("not-a-list")


class _FakeTable:
    def put_item(self, **_kwargs):
        return {}

    def get_item(self, **_kwargs):
        return {}

    def update_item(self, **_kwargs):
        return {"Attributes": {}}

    def delete_item(self, **_kwargs):
        return {"Attributes": {}}


class _FakeDynamoResource:
    def Table(self, _name):
        return _FakeTable()
