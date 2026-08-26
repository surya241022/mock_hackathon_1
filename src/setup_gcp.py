import os
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
LOCATION = os.getenv("GCP_REGION", "asia-south1")


def create_bucket():
    client = storage.Client(project=PROJECT_ID)

    bucket = client.bucket(BUCKET_NAME)

    if bucket.exists():
        print(f"Bucket already exists: gs://{BUCKET_NAME}")
        return

    bucket = client.create_bucket(
        bucket,
        location=LOCATION
    )

    print(f"Bucket created: gs://{bucket.name}")


if __name__ == "__main__":
    create_bucket()