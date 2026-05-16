import os
from .errors import NotFoundError, ValidationError, DynamoError


class ShoppingCartDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())

    def create(self, cart_id: str, product_ids: list) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        normalized_products = self._normalize_product_ids(product_ids)
        try:
            item = {"UUID": normalized_id, "product_ids": normalized_products}
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
        return item

    def update(self, cart_id: str, product_ids: list) -> dict:
        normalized_id = self._normalize_cart_id(cart_id)
        normalized_products = self._normalize_product_ids(product_ids)
        try:
            response = self.table.update_item(
                Key={"UUID": normalized_id},
                UpdateExpression="SET product_ids = :product_ids",
                ExpressionAttributeValues={":product_ids": normalized_products},
                ConditionExpression="attribute_exists(UUID)",
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
                ConditionExpression="attribute_exists(UUID)",
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

    def _normalize_cart_id(self, cart_id: str) -> str:
        if not cart_id:
            raise ValidationError("cart_id is required")
        return str(cart_id).strip().upper()

    def _normalize_product_ids(self, product_ids: list) -> list:
        if product_ids is None:
            raise ValidationError("product_ids is required")
        if not isinstance(product_ids, list):
            raise ValidationError("product_ids must be a list")
        normalized = [str(pid).strip().lower() for pid in product_ids]
        if any(not value for value in normalized):
            raise ValidationError("product_ids cannot be empty")
        return normalized

    def _table_name(self) -> str:
        return os.getenv("DYNAMODB_TABLE_SHOPPING_CART", "ShoppingCart")


def _is_condition_failure(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not response:
        return False
    error = response.get("Error", {})
    return error.get("Code") in {"ConditionalCheckFailedException"}
