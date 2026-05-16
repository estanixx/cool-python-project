import os
from .errors import NotFoundError, ValidationError, DynamoError


class DictionaryDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())

    def create(self, word: str, definition: str) -> dict:
        normalized_word = self._normalize_word(word)
        if not definition:
            raise ValidationError("definition is required")
        try:
            item = {"Word": normalized_word, "definition": definition}
            self.table.put_item(Item=item)
            return item
        except Exception as exc:  # pragma: no cover - boto specifics
            raise DynamoError("failed to create dictionary entry") from exc

    def read(self, word: str) -> dict:
        normalized_word = self._normalize_word(word)
        try:
            response = self.table.get_item(Key={"Word": normalized_word})
        except Exception as exc:  # pragma: no cover
            raise DynamoError("failed to read dictionary entry") from exc

        item = response.get("Item")
        if not item:
            raise NotFoundError("dictionary entry not found")
        return item

    def update(self, word: str, definition: str) -> dict:
        normalized_word = self._normalize_word(word)
        if not definition:
            raise ValidationError("definition is required")
        try:
            response = self.table.update_item(
                Key={"Word": normalized_word},
                UpdateExpression="SET definition = :definition",
                ExpressionAttributeValues={":definition": definition},
                ConditionExpression="attribute_exists(Word)",
                ReturnValues="ALL_NEW",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("dictionary entry not found") from exc
            raise DynamoError("failed to update dictionary entry") from exc

        return response["Attributes"]

    def delete(self, word: str) -> dict:
        normalized_word = self._normalize_word(word)
        try:
            response = self.table.delete_item(
                Key={"Word": normalized_word},
                ConditionExpression="attribute_exists(Word)",
                ReturnValues="ALL_OLD",
            )
        except Exception as exc:  # pragma: no cover
            if _is_condition_failure(exc):
                raise NotFoundError("dictionary entry not found") from exc
            raise DynamoError("failed to delete dictionary entry") from exc

        item = response.get("Attributes")
        if not item:
            raise NotFoundError("dictionary entry not found")
        return item

    def _normalize_word(self, word: str) -> str:
        if not word:
            raise ValidationError("word is required")
        return word.capitalize()

    def _table_name(self) -> str:
        return os.getenv("DYNAMODB_TABLE_DICTIONARY", "Dictionary")


def _is_condition_failure(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not response:
        return False
    error = response.get("Error", {})
    return error.get("Code") in {"ConditionalCheckFailedException"}
