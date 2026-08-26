import os
import shutil
from pathlib import Path


class MockBlob:
    def __init__(self, bucket_name: str, name: str, base_dir: Path):
        self.bucket_name = bucket_name
        self.name = name
        self.base_dir = base_dir
        self.file_path = base_dir / bucket_name / name

    def upload_from_filename(self, filename: str):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filename, self.file_path)
        print(f"[MOCK GCS] Uploaded '{filename}' to 'gs://{self.bucket_name}/{self.name}'")

    def download_to_filename(self, filename: str):
        if not self.file_path.exists():
            raise FileNotFoundError(f"Blob gs://{self.bucket_name}/{self.name} does not exist.")
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.file_path, filename)
        print(f"[MOCK GCS] Downloaded 'gs://{self.bucket_name}/{self.name}' to '{filename}'")

    def exists(self) -> bool:
        return self.file_path.exists()


class MockBucket:
    def __init__(self, name: str, client: "MockStorageClient"):
        self.name = name
        self.client = client
        self.bucket_dir = client.base_dir / name

    def exists(self) -> bool:
        return self.bucket_dir.exists()

    def blob(self, blob_name: str) -> MockBlob:
        return MockBlob(self.name, blob_name, self.client.base_dir)


class MockStorageClient:
    def __init__(self, project: str = "mock-trail-project-1", base_dir: str = ".mock_gcs"):
        self.project = project
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def bucket(self, bucket_name: str) -> MockBucket:
        return MockBucket(bucket_name, self)

    def create_bucket(self, bucket, location: str = "asia-south1") -> MockBucket:
        bucket_name = bucket.name if isinstance(bucket, MockBucket) else str(bucket)
        b = MockBucket(bucket_name, self)
        b.bucket_dir.mkdir(parents=True, exist_ok=True)
        print(f"[MOCK GCS] Bucket created: gs://{bucket_name} in location {location}")
        return b
