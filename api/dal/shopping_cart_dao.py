import os
from decimal import Decimal
from .errors import NotFoundError, ValidationError, DynamoError


class ShoppingCartDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())

    def create(self, cart_id: str, products: list) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        normalized_products = self._normalize_products(products)
        try:
            item = {"UUID": normalized_id, "products": normalized_products}
            self.table.put_item(Item=item)
            return item
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to create shopping cart") from exc

    def read(self, cart_id: str) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        try:
            response = self.table.get_item(Key={"UUID": normalized_id})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read shopping cart") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("shopping cart not found")

        # Backward compatibility: convert legacy product_ids to products format
        if "product_ids" in item and "products" not in item:
            item["products"] = []

        return item

    def update(self, cart_id: str, products: list) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        normalized_products = self._normalize_products(products)
        try:
            response = self.table.update_item(
                Key={"UUID": normalized_id},
                UpdateExpression="SET products = :products",
                ExpressionAttributeValues={":products": normalized_products},
                ExpressionAttributeNames={"#uuid": "UUID"},
                ConditionExpression="attribute_exists(#uuid)",
                ReturnValues="ALL_NEW",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("shopping cart not found") from exc
            raise DynamoError("failed to update shopping cart") from exc

        return response["Attributes"]

    def delete(self, cart_id: str) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        try:
            response = self.table.delete_item(
                Key={"UUID": normalized_id},
                ExpressionAttributeNames={"#uuid": "UUID"},
                ConditionExpression="attribute_exists(#uuid)",
                ReturnValues="ALL_OLD",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("shopping cart not found") from exc
            raise DynamoError("failed to delete shopping cart") from exc

        item = response.get("Attributes")
        if not item:
            raise NotFoundError("shopping cart not found")
        return item

    def add_product(self, cart_id: str, product: dict) -> dict:
        """Append product snapshot to existing cart. Read-modify-write."""
        if not isinstance(product, dict):
            raise ValidationError("product must be a dict with uuid, name, price")
        if not all(k in product for k in ("uuid", "name", "price")):
            raise ValidationError("product must have uuid, name, and price")

        normalized_id = self._normalize_cart_id(cart_id)
        try:
            response = self.table.get_item(Key={"UUID": normalized_id})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read shopping cart") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("shopping cart not found")

        products = self._read_products(item)
        product_snapshot = {
            "uuid": str(product["uuid"]).strip().lower(),
            "name": str(product["name"]).strip(),
            "price": Decimal(str(product["price"])),
        }
        products.append(product_snapshot)

        try:
            response = self.table.update_item(
                Key={"UUID": normalized_id},
                UpdateExpression="SET products = :products",
                ExpressionAttributeValues={":products": products},
                ExpressionAttributeNames={"#uuid": "UUID"},
                ConditionExpression="attribute_exists(#uuid)",
                ReturnValues="ALL_NEW",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("shopping cart not found") from exc
            raise DynamoError("failed to add product to cart") from exc

        return response["Attributes"]

    def remove_product(self, cart_id: str, product_uuid: str) -> dict:
        """Remove product by UUID from cart. Read-modify-write."""
        if not product_uuid:
            raise ValidationError("product_uuid is required")

        normalized_id = self._normalize_cart_id(cart_id)
        try:
            response = self.table.get_item(Key={"UUID": normalized_id})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read shopping cart") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("shopping cart not found")

        products = self._read_products(item)
        normalized_uuid = str(product_uuid).strip().lower()
        filtered = [p for p in products if p.get("uuid", "").lower() != normalized_uuid]

        try:
            response = self.table.update_item(
                Key={"UUID": normalized_id},
                UpdateExpression="SET products = :products",
                ExpressionAttributeValues={":products": filtered},
                ExpressionAttributeNames={"#uuid": "UUID"},
                ConditionExpression="attribute_exists(#uuid)",
                ReturnValues="ALL_NEW",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("shopping cart not found") from exc
            raise DynamoError("failed to remove product from cart") from exc

        return response["Attributes"]

    def get_total(self, cart_id: str, tax_rate: float = None) -> dict:
        """Return {subtotal, tax, total} for cart's products."""
        if tax_rate is None:
            tax_rate = float(os.getenv("CART_TAX_RATE", "0.07"))

        normalized_id = self._normalize_cart_id(cart_id)
        try:
            response = self.table.get_item(Key={"UUID": normalized_id})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read shopping cart") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("shopping cart not found")

        products = self._read_products(item)
        subtotal = sum(float(p.get("price", 0)) for p in products)
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)

        return {
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "total": total,
        }

    def _read_products(self, cart_item: dict) -> list:
        """Read products list, handling legacy product_ids format."""
        if "products" in cart_item:
            return cart_item["products"]
        if "product_ids" in cart_item:
            # Legacy format — return empty; caller must re-populate
            return []
        return []

    def _normalize_cart_id(self, cart_id: str) -> str:
        if not cart_id:
            raise ValidationError("cart_id is required")
        return str(cart_id).strip().upper()

    def _normalize_products(self, products: list) -> list:
        if products is None:
            raise ValidationError("products is required")
        if not isinstance(products, list):
            raise ValidationError("products must be a list")
        normalized = []
        for p in products:
            if not isinstance(p, dict):
                raise ValidationError("each product must be a dict")
            if not all(k in p for k in ("uuid", "name", "price")):
                raise ValidationError("each product must have uuid, name, and price")
            normalized.append({
                "uuid": str(p["uuid"]).strip().lower(),
                "name": str(p["name"]).strip(),
                "price": Decimal(str(p["price"])),
            })
        return normalized

    def _table_name(self) -> str:
        return os.getenv("DYNAMODB_TABLE_SHOPPING_CART", "ShoppingCart")


def _is_condition_failure(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not response:
        return False
    error = response.get("Error", {})
    return error.get("Code") in {"ConditionalCheckFailedException"}
