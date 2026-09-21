import csv
import io
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from models.db import SessionLocal, ScrapedPage

S3_BUCKET = os.getenv("S3_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def pages_to_csv() -> io.StringIO:
    """Streams all scraped pages into an in-memory CSV buffer."""
    db = SessionLocal()
    try:
        pages = db.query(ScrapedPage).filter_by(status="done").all()

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "url", "title", "content_hash", "scraped_at", "last_seen_at", "content_preview"])

        for p in pages:
            writer.writerow([
                p.id,
                p.url,
                p.title or "",
                p.content_hash or "",
                p.scraped_at.isoformat() if p.scraped_at else "",
                p.last_seen_at.isoformat() if p.last_seen_at else "",
                (p.content or "")[:500].replace("\n", " "),
            ])

        buffer.seek(0)
        return buffer
    finally:
        db.close()


def upload_csv_to_s3(bucket: str = None, key_prefix: str = "scraper-exports") -> dict:
    """
    Generates the CSV and uploads it to S3. Requires standard AWS credentials
    to be available in the environment (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
    or an attached IAM role) — this function doesn't handle credential setup.
    """
    bucket = bucket or S3_BUCKET
    if not bucket:
        raise ValueError("No S3 bucket configured (set S3_BUCKET or pass one explicitly)")

    buffer = pages_to_csv()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    key = f"{key_prefix}/scraped_pages_{timestamp}.csv"

    s3 = boto3.client("s3", region_name=AWS_REGION)
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue().encode("utf-8"), ContentType="text/csv")
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")

    return {
        "bucket": bucket,
        "key": key,
        "url": f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}",
    }
