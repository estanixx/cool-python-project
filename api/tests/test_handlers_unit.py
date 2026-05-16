import json
import unittest
from unittest.mock import MagicMock, patch

from api.dal.errors import NotFoundError, ValidationError
import api.handlers.dictionary_handler as dictionary_module
import api.handlers.product_handler as product_module
import api.handlers.shopping_cart_handler as shopping_cart_module


class TestDictionaryHandler(unittest.TestCase):
    def test_create_returns_item(self):
        item = {"word": "Apple", "definition": "A fruit"}
        with patch.object(dictionary_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(dictionary_module, "DictionaryDAO") as dao_class:
                dao = MagicMock()
                dao.create.return_value = item
                dao_class.return_value = dao

                response = dictionary_module.handler(
                    {"operation": "create", "payload": {"word": "apple", "definition": "A fruit"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), item)

    def test_read_not_found(self):
        with patch.object(dictionary_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(dictionary_module, "DictionaryDAO") as dao_class:
                dao = MagicMock()
                dao.read.side_effect = NotFoundError("missing")
                dao_class.return_value = dao

                response = dictionary_module.handler(
                    {"operation": "read", "payload": {"word": "missing"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response["body"]), {"error": "missing"})


class TestProductHandler(unittest.TestCase):
    def test_create_accepts_camel_case_key(self):
        item = {"product_id": "uuid", "name": "Apple", "price": 1.0}
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.create.return_value = item
                dao_class.return_value = dao

                response = product_module.handler(
                    {
                        "operation": "create",
                        "payload": {"name": "Apple", "price": 1.0, "productId": "uuid"},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), item)

    def test_update_validation_error(self):
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.update.side_effect = ValidationError("no updates")
                dao_class.return_value = dao

                response = product_module.handler(
                    {"operation": "update", "payload": {"productId": "uuid"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"]), {"error": "no updates"})


class TestShoppingCartHandler(unittest.TestCase):
    def test_update_accepts_camel_case_keys(self):
        item = {"cart_id": "CART-1", "product_ids": ["abc"]}
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.update.return_value = item
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {
                        "operation": "update",
                        "payload": {"cartId": "CART-1", "productIds": ["ABC"]},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), item)
