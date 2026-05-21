import json
import unittest
from unittest.mock import MagicMock, patch

from api.dal.errors import NotFoundError, ValidationError
import api.handlers.dictionary_handler as dictionary_module
import api.handlers.product_handler as product_module
import api.handlers.shopping_cart_handler as shopping_cart_module
import api.handlers.utils as utils_module


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


class TestProductHandlerListSearch(unittest.TestCase):
    def test_list_returns_all_products(self):
        products = [
            {"uuid": "p1", "name": "Mouse", "price": 29.99},
            {"uuid": "p2", "name": "Keyboard", "price": 49.99},
        ]
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.list.return_value = products
                dao_class.return_value = dao

                response = product_module.handler(
                    {"operation": "list", "payload": {}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["products"], products)

    def test_list_empty_returns_empty_list(self):
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.list.return_value = []
                dao_class.return_value = dao

                response = product_module.handler(
                    {"operation": "list", "payload": {}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["products"], [])

    def test_search_returns_matching_products(self):
        products = [{"uuid": "p1", "name": "Wireless Mouse", "price": 29.99}]
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.search.return_value = products
                dao_class.return_value = dao

                response = product_module.handler(
                    {"operation": "search", "payload": {"term": "wireless"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["products"], products)
        dao.search.assert_called_once_with("wireless")

    def test_search_with_q_param(self):
        with patch.object(product_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(product_module, "ProductDAO") as dao_class:
                dao = MagicMock()
                dao.search.return_value = []
                dao_class.return_value = dao

                response = product_module.handler(
                    {"operation": "search", "payload": {"q": "mouse"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        dao.search.assert_called_once_with("mouse")


class TestShoppingCartHandlerProductOps(unittest.TestCase):
    def test_add_product_with_full_snapshot(self):
        """Add product with full snapshot (uuid + name + price) — uses snapshot directly."""
        product = {"uuid": "p1", "name": "Mouse", "price": 29.99}
        updated_cart = {
            "UUID": "CART-1",
            "products": [product],
        }
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.add_product.return_value = updated_cart
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {
                        "operation": "add_product",
                        "payload": {"cart_id": "CART-1", "product": product},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["products"], [product])
        dao.add_product.assert_called_once_with("CART-1", product)

    def test_add_product_with_uuid_only_fetches_product(self):
        """Add product with only uuid — fetches from ProductDAO and creates snapshot."""
        product_data = {"uuid": "p1", "name": "Wireless Mouse", "price": 39.99}
        updated_cart = {
            "UUID": "CART-1",
            "products": [{"uuid": "p1", "name": "Wireless Mouse", "price": 39.99}],
        }
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as cart_dao_class:
                cart_dao = MagicMock()
                cart_dao.add_product.return_value = updated_cart
                cart_dao_class.return_value = cart_dao

                with patch.object(shopping_cart_module, "ProductDAO") as prod_dao_class:
                    prod_dao = MagicMock()
                    prod_dao.read.return_value = product_data
                    prod_dao_class.return_value = prod_dao

                    response = shopping_cart_module.handler(
                        {
                            "operation": "add_product",
                            "payload": {"cart_id": "CART-1", "product": {"uuid": "p1"}},
                        },
                        None,
                    )

        self.assertEqual(response["statusCode"], 200)
        prod_dao.read.assert_called_once_with("p1")
        cart_dao.add_product.assert_called_once()
        snapshot = cart_dao.add_product.call_args[0][1]
        self.assertEqual(snapshot["uuid"], "p1")
        self.assertEqual(snapshot["name"], "Wireless Mouse")
        self.assertEqual(snapshot["price"], 39.99)

    def test_add_product_with_uuid_only_product_not_found_returns_404(self):
        """Add product with only uuid when product doesn't exist — returns 404."""
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as cart_dao_class:
                cart_dao = MagicMock()
                cart_dao_class.return_value = cart_dao

                with patch.object(shopping_cart_module, "ProductDAO") as prod_dao_class:
                    prod_dao = MagicMock()
                    prod_dao.read.side_effect = NotFoundError("product not found")
                    prod_dao_class.return_value = prod_dao

                    response = shopping_cart_module.handler(
                        {
                            "operation": "add_product",
                            "payload": {"cart_id": "CART-1", "product": {"uuid": "missing"}},
                        },
                        None,
                    )

        self.assertEqual(response["statusCode"], 404)
        body = json.loads(response["body"])
        self.assertIn("not found", body["error"])

    def test_add_product_not_found_returns_404(self):
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.add_product.side_effect = NotFoundError("shopping cart not found")
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {
                        "operation": "add_product",
                        "payload": {"cart_id": "NOPE", "product": {"uuid": "p1", "name": "X", "price": 1}},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 404)

    def test_remove_product_removes_from_cart(self):
        updated_cart = {"UUID": "CART-1", "products": []}
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.remove_product.return_value = updated_cart
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {
                        "operation": "remove_product",
                        "payload": {"cart_id": "CART-1", "product_uuid": "p1"},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        dao.remove_product.assert_called_once_with("CART-1", "p1")

    def test_get_total_returns_calculation(self):
        result = {"subtotal": 100.00, "tax": 7.00, "total": 107.00}
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.get_total.return_value = result
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {
                        "operation": "get_total",
                        "payload": {"cart_id": "CART-1", "tax_rate": 0.07},
                    },
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body, result)
        dao.get_total.assert_called_once_with("CART-1", 0.07)

    def test_get_total_default_tax_rate(self):
        result = {"subtotal": 50.00, "tax": 3.50, "total": 53.50}
        with patch.object(shopping_cart_module, "get_dynamodb_resource") as get_resource:
            get_resource.return_value = object()
            with patch.object(shopping_cart_module, "ShoppingCartDAO") as dao_class:
                dao = MagicMock()
                dao.get_total.return_value = result
                dao_class.return_value = dao

                response = shopping_cart_module.handler(
                    {"operation": "get_total", "payload": {"cart_id": "CART-1"}},
                    None,
                )

        self.assertEqual(response["statusCode"], 200)
        dao.get_total.assert_called_once_with("CART-1", None)


class TestParseEventQueryParamOverride(unittest.TestCase):
    def test_query_param_overrides_method_operation(self):
        """GET /product?operation=list should yield operation='list', not 'read'."""
        event = {
            "requestContext": {"http": {"method": "GET"}},
            "queryStringParameters": {"operation": "list"},
            "body": "{}",
        }
        operation, payload = utils_module.parse_event(event)
        self.assertEqual(operation, "list")

    def test_query_param_search_with_term(self):
        """GET /product?operation=search&term=mouse should yield operation='search'."""
        event = {
            "requestContext": {"http": {"method": "GET"}},
            "queryStringParameters": {"operation": "search", "term": "mouse"},
            "body": "{}",
        }
        operation, payload = utils_module.parse_event(event)
        self.assertEqual(operation, "search")
        self.assertEqual(payload.get("term"), "mouse")

    def test_no_query_param_uses_method_mapping(self):
        """GET without operation query param should use default 'read'."""
        event = {
            "requestContext": {"http": {"method": "GET"}},
            "body": "{}",
        }
        operation, payload = utils_module.parse_event(event)
        self.assertEqual(operation, "read")

    def test_legacy_format_unchanged(self):
        """Legacy custom format should still work."""
        event = {"operation": "list", "payload": {"foo": "bar"}}
        operation, payload = utils_module.parse_event(event)
        self.assertEqual(operation, "list")
        self.assertEqual(payload, {"foo": "bar"})
