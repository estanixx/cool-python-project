import os
from typing import Dict, Iterable, Tuple

import boto3


DEFAULT_ENDPOINT = "http://localhost:4566"
DEFAULT_REGION = "us-east-1"

TABLE_DEFINITIONS: Dict[str, Tuple[str, str]] = {
    "Dictionary": ("Word", "S"),
    "Product": ("uuid", "S"),
    "ShoppingCart": ("UUID", "S"),
}


def configure_test_env() -> None:
    os.environ.setdefault("STAGE", "local")
    os.environ.setdefault("AWS_ENDPOINT_URL", DEFAULT_ENDPOINT)
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("AWS_DEFAULT_REGION", DEFAULT_REGION)
    os.environ.setdefault("DYNAMODB_TABLE_DICTIONARY", "Dictionary")
    os.environ.setdefault("DYNAMODB_TABLE_PRODUCT", "Product")
    os.environ.setdefault("DYNAMODB_TABLE_SHOPPING_CART", "ShoppingCart")


def dynamodb_resource():
    endpoint = os.environ.get("AWS_ENDPOINT_URL")
    if endpoint:
        return boto3.resource("dynamodb", endpoint_url=endpoint)
    return boto3.resource("dynamodb")


def dynamodb_client():
    endpoint = os.environ.get("AWS_ENDPOINT_URL")
    if endpoint:
        return boto3.client("dynamodb", endpoint_url=endpoint)
    return boto3.client("dynamodb")


def floci_available() -> bool:
    try:
        dynamodb_client().list_tables()
        return True
    except Exception:
        return False


def ensure_tables() -> None:
    configure_test_env()
    client = dynamodb_client()
    existing = set(client.list_tables().get("TableNames", []))
    for name, (hash_key, key_type) in TABLE_DEFINITIONS.items():
        if name in existing:
            continue
        client.create_table(
            TableName=name,
            KeySchema=[{"AttributeName": hash_key, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": hash_key, "AttributeType": key_type}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
    for name in TABLE_DEFINITIONS:
        dynamodb_resource().Table(name).wait_until_exists()


def clear_table(table_name: str, hash_key: str) -> None:
    table = dynamodb_resource().Table(table_name)
    response = table.scan(ProjectionExpression=hash_key)
    items: Iterable[dict] = response.get("Items", [])
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={hash_key: item[hash_key]})
