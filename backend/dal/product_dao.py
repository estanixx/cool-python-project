import os
import uuid
from decimal import Decimal
from .errors import NotFoundError, ValidationError, DynamoError


class ProductDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())

    def create(self, name: str, price: float, product_id: str = None) -> dict:
        if not name:
            raise ValidationError("name is required")
        if price is None:
            raise ValidationError("price is required")

        product_uuid = self._normalize_uuid(product_id or str(uuid.uuid4()))
        try:
            item = {"uuid": product_uuid, "name": name, "price": Decimal(str(price))}
            self.table.put_item(Item=item)
            return item
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to create product") from exc

    def read(self, product_id: str) -> dict:
        normalized_id = self._normalize_uuid(product_id)
        try:
            response = self.table.get_item(Key={"uuid": normalized_id})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read product") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("product not found")
        return item

    def update(self, product_id: str, name: str = None, price: float = None) -> dict:
        normalized_id = self._normalize_uuid(product_id)
        updates = []
        values = {}
        attr_names = {"#pk": "uuid"}
        if name is not None:
            updates.append("#nm = :name")
            values[":name"] = name
            attr_names["#nm"] = "name"
        if price is not None:
            updates.append("#pr = :price")
            values[":price"] = price
            attr_names["#pr"] = "price"
        if not updates:
            raise ValidationError("no updates provided")

        try:
            response = self.table.update_item(
                Key={"uuid": normalized_id},
                UpdateExpression="SET " + ", ".join(updates),
                ExpressionAttributeValues=values,
                ExpressionAttributeNames=attr_names,
                ConditionExpression="attribute_exists(#pk)",
                ReturnValues="ALL_NEW",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("product not found") from exc
            raise DynamoError("failed to update product") from exc

        return response["Attributes"]

    def delete(self, product_id: str) -> dict:
        normalized_id = self._normalize_uuid(product_id)
        try:
            response = self.table.delete_item(
                Key={"uuid": normalized_id},
                ConditionExpression="attribute_exists(#pk)",
                ExpressionAttributeNames={"#pk": "uuid"},
                ReturnValues="ALL_OLD",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("product not found") from exc
            raise DynamoError("failed to delete product") from exc

        item = response.get("Attributes")
        if not item:
            raise NotFoundError("product not found")
        return item

    def _normalize_uuid(self, value: str) -> str:
        if not value:
            raise ValidationError("product_id is required")
        try:
            return str(uuid.UUID(str(value)))
        except Exception as exc:
            raise ValidationError("product_id must be a valid UUID") from exc

    def _table_name(self) -> str:
        return os.getenv("DYNAMODB_TABLE_PRODUCT", "Product")


def _is_condition_failure(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not response:
        return False
    error = response.get("Error", {})
    return error.get("Code") in {"ConditionalCheckFailedException"}
