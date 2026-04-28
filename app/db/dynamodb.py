import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def get_dynamodb_client():
    return boto3.client(
        "dynamodb",
        endpoint_url=settings.DYNAMODB_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def create_tables() -> None:
    client = get_dynamodb_client()

    try:
        client.create_table(
            TableName=settings.DYNAMODB_TABLE_USER_PROFILES,
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            pass  # Table already exists
        else:
            raise
