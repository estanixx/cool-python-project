import json
from api.dal import DictionaryDAO, get_dynamodb_resource
from api.dal.errors import NotFoundError, ValidationError, DynamoError
from api.handlers.utils import parse_event


def handler(event, context):  # pylint: disable=unused-argument
    operation, payload = parse_event(event or {})
    dao = DictionaryDAO(get_dynamodb_resource())

    try:
        if operation == "create":
            item = dao.create(payload.get("Word") or payload.get("word"), payload.get("definition"))
            return _response(200, item)
        if operation == "read":
            item = dao.read(payload.get("Word") or payload.get("word"))
            return _response(200, item)
        if operation == "update":
            item = dao.update(payload.get("Word") or payload.get("word"), payload.get("definition"))
            return _response(200, item)
        if operation == "delete":
            item = dao.delete(payload.get("Word") or payload.get("word"))
            return _response(200, item)
        raise ValidationError("unsupported operation")
    except ValidationError as exc:
        return _error(400, str(exc))
    except NotFoundError as exc:
        return _error(404, str(exc))
    except DynamoError as exc:
        return _error(500, str(exc))


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "body": json.dumps(body)}


def _error(status_code: int, message: str) -> dict:
    return {"statusCode": status_code, "body": json.dumps({"error": message})}
