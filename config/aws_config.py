import boto3
from botocore.config import Config

from config.settings import AWS_CONNECT_TIMEOUT_SECONDS, AWS_READ_TIMEOUT_SECONDS

def get_s3_client():
    return boto3.client(
        "s3",
        config=Config(
            connect_timeout=AWS_CONNECT_TIMEOUT_SECONDS,
            read_timeout=AWS_READ_TIMEOUT_SECONDS,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )
