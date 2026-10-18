import boto3
from botocore.config import Config

from config.settings import AWS_CONNECT_TIMEOUT_SECONDS, AWS_READ_TIMEOUT_SECONDS

def get_s3_client():
    session = boto3.Session()
    region = session.region_name
    return session.client(
        "s3",
        endpoint_url=f"https://s3.{region}.amazonaws.com" if region else None,
        config=Config(
            signature_version="s3v4",
            connect_timeout=AWS_CONNECT_TIMEOUT_SECONDS,
            read_timeout=AWS_READ_TIMEOUT_SECONDS,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )
