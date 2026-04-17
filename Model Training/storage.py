"""
MinIO (S3-compatible) helpers.
All model .pkl files live here — never on local disk permanently.
"""
import io
import os
import boto3
from botocore.client import Config

MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT",   "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET     = os.getenv("MINIO_BUCKET",     "hpa-models")


def _client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_model(local_path: str, s3_key: str) -> str:
    """Upload .pkl to MinIO, return full s3:// URI."""
    client = _client()
    client.upload_file(local_path, MINIO_BUCKET, s3_key)
    return f"s3://{MINIO_BUCKET}/{s3_key}"


def download_model_to_buffer(s3_uri: str) -> io.BytesIO:
    """
    Download model from MinIO into an in-memory buffer.
    Never writes to disk — safe for ephemeral containers.
    """
    path = s3_uri.replace("s3://", "")
    bucket, key = path.split("/", 1)

    client = _client()
    buffer = io.BytesIO()
    client.download_fileobj(bucket, key, buffer)
    buffer.seek(0)
    return buffer
