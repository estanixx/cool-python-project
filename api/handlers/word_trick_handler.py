import json
from api.utils import word_trick
from api.handlers.utils import parse_event


def handler(event, context):  # pylint: disable=unused-argument
    operation, payload = parse_event(event or {})

    try:
        if operation == "options":
            return _response(200, {})
        if operation == "create":
            sentence = payload.get("sentence") or payload.get("text") or ""
            result = word_trick(sentence)
            return _response(200, {"input": sentence, "result": result})
        raise ValueError("unsupported operation")
    except Exception as exc:
        return _error(400, str(exc))


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "body": json.dumps(body)}


def _error(status_code: int, message: str) -> dict:
    return {"statusCode": status_code, "body": json.dumps({"error": message})}
