import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

LOCAL_DATA_DIR = Path("data")
GCS_PREFIX = "raw"


def upload_files():
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    files = [
        file for file in LOCAL_DATA_DIR.rglob("*")
        if file.is_file()
    ]

    if not files:
        print("No files found in data/")
        return

    for file_path in files:
        relative_path = file_path.relative_to(LOCAL_DATA_DIR)
        blob_name = f"{GCS_PREFIX}/{relative_path.as_posix()}"

        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(file_path))

        print(f"Uploaded: {file_path} -> gs://{BUCKET_NAME}/{blob_name}")


if __name__ == "__main__":
    upload_files()