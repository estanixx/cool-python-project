import json
from decimal import Decimal

from api.dal import ProductDAO, get_dynamodb_resource
from api.dal.errors import NotFoundError, ValidationError, DynamoError
from api.handlers.utils import parse_event


def handler(event, context):  # pylint: disable=unused-argument
    operation, payload = parse_event(event or {})
    dao = ProductDAO(get_dynamodb_resource())

    try:
        if operation == "options":
            return _response(200, {})
        if operation == "create":
            item = dao.create(
                payload.get("name"),
                payload.get("price"),
                payload.get("uuid") or payload.get("product_id") or payload.get("productId"),
            )
            return _response(200, item)
        if operation == "read":
            item = dao.read(payload.get("uuid") or payload.get("product_id") or payload.get("productId"))
            return _response(200, item)
        if operation == "update":
            item = dao.update(
                payload.get("uuid") or payload.get("product_id") or payload.get("productId"),
                payload.get("name"),
                payload.get("price"),
            )
            return _response(200, item)
        if operation == "delete":
            item = dao.delete(payload.get("uuid") or payload.get("product_id") or payload.get("productId"))
            return _response(200, item)
        if operation == "list":
            items = dao.list()
            return _response(200, {"products": items})
        if operation == "search":
            term = payload.get("term") or payload.get("q")
            items = dao.search(term)
            return _response(200, {"products": items})
        raise ValidationError("unsupported operation")
    except ValidationError as exc:
        return _error(400, str(exc))
    except NotFoundError as exc:
        return _error(404, str(exc))
    except DynamoError as exc:
        return _error(500, str(exc))


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "body": json.dumps(body, cls=_DecimalEncoder)}


def _error(status_code: int, message: str) -> dict:
    return {"statusCode": status_code, "body": json.dumps({"error": message})}
