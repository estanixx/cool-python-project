import os
import boto3


def get_dynamodb_resource():
    """Create a DynamoDB resource honoring local endpoint overrides."""
    stage = os.getenv("STAGE", "local")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")

    if stage == "local" and not endpoint_url:
        endpoint_url = "http://localhost:4566"

    if endpoint_url:
        return boto3.resource("dynamodb", endpoint_url=endpoint_url)

    return boto3.resource("dynamodb")
