import os
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional


class MockQueryRow:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, item):
        return self._data[item]

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __repr__(self):
        return str(self._data)


class MockQueryJob:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def result(self) -> List[MockQueryRow]:
        return [MockQueryRow(row) for row in self._df.to_dict(orient="records")]

    def to_dataframe(self) -> pd.DataFrame:
        return self._df


class MockDataset:
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.location = "asia-south1"


class MockLoadJob:
    def __init__(self, uri: str, table_ref: str):
        self.uri = uri
        self.table_ref = table_ref

    def result(self):
        print(f"[MOCK BIGQUERY] Completed LoadJob for {self.uri} -> {self.table_ref}")
        return True


class MockBigQueryClient:
    def __init__(self, project: str = "mock-trail-project-1", db_path: str = ".mock_bigquery.db"):
        self.project = project
        self.db_path = Path(db_path).resolve()
        self.datasets = set()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_dataset(self, dataset: Any):
        dataset_id = getattr(dataset, "dataset_id", str(dataset))
        self.datasets.add(dataset_id)
        print(f"[MOCK BIGQUERY] Dataset registered: {dataset_id}")
        return dataset

    def load_table_from_uri(self, uri: str, table_ref: str, job_config=None, location=None):
        clean_table = table_ref.replace(f"{self.project}.", "").replace(".", "_")
        filename = uri.split("/")[-1]
        
        # Look in mock GCS or data directory
        local_candidates = [
            Path(".mock_gcs") / "mock-project-bucket-surya" / "raw" / filename,
            Path("data") / filename,
            Path(__file__).resolve().parent.parent / "data" / filename
        ]
        
        source_path = None
        for candidate in local_candidates:
            if candidate.exists():
                source_path = candidate
                break

        if source_path:
            df = pd.read_csv(source_path)
            conn = self.get_connection()
            df.to_sql(clean_table, conn, if_exists="replace", index=False)
            conn.close()
            print(f"[MOCK BIGQUERY] Loaded {len(df)} rows into table '{table_ref}' (mapped to '{clean_table}')")
        else:
            print(f"[MOCK BIGQUERY] Warning: Could not find source file for {uri}")

        return MockLoadJob(uri, table_ref)

    def save_table(self, table_name: str, df: pd.DataFrame):
        clean_table = table_name.replace(f"{self.project}.", "").replace(".", "_")
        conn = self.get_connection()
        df.to_sql(clean_table, conn, if_exists="replace", index=False)
        conn.close()

    def get_table_df(self, table_name: str) -> pd.DataFrame:
        clean_table = table_name.replace(f"{self.project}.", "").replace(".", "_")
        conn = self.get_connection()
        try:
            df = pd.read_sql_query(f"SELECT * FROM {clean_table}", conn)
        except Exception:
            df = pd.DataFrame()
        finally:
            conn.close()
        return df

    def query(self, query_str: str, job_config=None) -> MockQueryJob:
        conn = self.get_connection()
        # Replace BQ backticks and dataset references with SQLite table equivalents
        cleaned_query = query_str
        for ds in ["bronze", "silver", "gold"]:
            cleaned_query = cleaned_query.replace(f"`{self.project}.{ds}.", f"{ds}_")
            cleaned_query = cleaned_query.replace(f"{self.project}.{ds}.", f"{ds}_")
            cleaned_query = cleaned_query.replace(f"`{ds}.", f"{ds}_")
            cleaned_query = cleaned_query.replace(f"{ds}.", f"{ds}_")
        cleaned_query = cleaned_query.replace("`", "")

        try:
            df = pd.read_sql_query(cleaned_query, conn)
        except Exception:
            # Return empty or fallback dataframe if query has BigQuery specific syntax (like AI.EMBED)
            df = pd.DataFrame([{"status": "MOCK_EXECUTED", "row_count": 100}])
        finally:
            conn.close()

        return MockQueryJob(df)
