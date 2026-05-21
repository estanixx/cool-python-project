import json
from decimal import Decimal
from api.dal import ShoppingCartDAO, ProductDAO, get_dynamodb_resource
from api.dal.errors import NotFoundError, ValidationError, DynamoError
from api.handlers.utils import parse_event


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def handler(event, context):  # pylint: disable=unused-argument
    operation, payload = parse_event(event or {})
    dao = ShoppingCartDAO(get_dynamodb_resource())

    try:
        if operation == "options":
            return _response(200, {})
        if operation == "create":
            item = dao.create(
                payload.get("UUID") or payload.get("cart_id") or payload.get("cartId"),
                payload.get("products") or [],
            )
            return _response(200, item)
        if operation == "read":
            item = dao.read(payload.get("UUID") or payload.get("cart_id") or payload.get("cartId"))
            return _response(200, item)
        if operation == "update":
            item = dao.update(
                payload.get("UUID") or payload.get("cart_id") or payload.get("cartId"),
                payload.get("products") or [],
            )
            return _response(200, item)
        if operation == "delete":
            item = dao.delete(payload.get("UUID") or payload.get("cart_id") or payload.get("cartId"))
            return _response(200, item)
        if operation == "add_product":
            cart_id = payload.get("cart_id") or payload.get("cartId") or payload.get("UUID")
            product = payload.get("product") or {}
            
            product_uuid = product.get("uuid")
            if not product_uuid:
                raise ValidationError("product uuid is required")
            
            # Mode 1: Full snapshot provided (uuid + name + price)
            if "name" in product and "price" in product:
                item = dao.add_product(cart_id, product)
                return _response(200, item)
            
            # Mode 2: Only uuid provided — fetch product details from ProductDAO
            product_dao = ProductDAO(get_dynamodb_resource())
            try:
                product_data = product_dao.read(product_uuid)
            except NotFoundError:
                raise NotFoundError(f"product {product_uuid} not found — create it first or provide full snapshot")
            
            snapshot = {
                "uuid": product_uuid,
                "name": product_data.get("name", ""),
                "price": float(product_data.get("price", 0)),
            }
            item = dao.add_product(cart_id, snapshot)
            return _response(200, item)
        if operation == "remove_product":
            cart_id = payload.get("cart_id") or payload.get("cartId") or payload.get("UUID")
            product_uuid = payload.get("product_uuid") or payload.get("productUuid")
            item = dao.remove_product(cart_id, product_uuid)
            return _response(200, item)
        if operation == "get_total":
            cart_id = payload.get("cart_id") or payload.get("cartId") or payload.get("UUID")
            tax_rate = payload.get("tax_rate") or payload.get("taxRate")
            if tax_rate is not None:
                tax_rate = float(tax_rate)
            result = dao.get_total(cart_id, tax_rate)
            return _response(200, result)
        raise ValidationError("unsupported operation")
    except ValidationError as exc:
        return _error(400, str(exc))
    except NotFoundError as exc:
        return _error(404, str(exc))
    except DynamoError as exc:
        return _error(500, str(exc))


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "body": json.dumps(body, cls=_DecimalEncoder)}


def _error(status_code: int, message: str) -> dict:
    return {"statusCode": status_code, "body": json.dumps({"error": message})}
