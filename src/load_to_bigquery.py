import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
BQ_LOCATION = os.getenv("BQ_LOCATION", "asia-south1")

DATASET = "bronze"


def create_dataset():
    """Create the BigQuery bronze dataset if it does not exist."""

    client = bigquery.Client(project=PROJECT_ID)

    dataset_id = f"{PROJECT_ID}.{DATASET}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = BQ_LOCATION

    try:
        client.create_dataset(dataset)
        print(f"Dataset created: {dataset_id}")

    except Exception as e:
        if "Already Exists" in str(e):
            print(f"Dataset already exists: {dataset_id}")
        else:
            raise


def load_csv_to_bigquery(file_name, table_name):
    """Load a CSV file from GCS into BigQuery."""

    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = f"{PROJECT_ID}.{DATASET}"
    table_ref = f"{dataset_ref}.{table_name}"

    uri = f"gs://{BUCKET_NAME}/raw/{file_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_uri(
        uri,
        table_ref,
        job_config=job_config,
        location=BQ_LOCATION,
    )

    job.result()

    print(f"Loaded: {uri}")
    print(f"BigQuery table: {table_ref}")


if __name__ == "__main__":

    # Create BigQuery dataset first
    create_dataset()

    # Load customers
    load_csv_to_bigquery(
        file_name="customers.csv",
        table_name="customers_raw",
    )

    # Load products
    load_csv_to_bigquery(
        file_name="products.csv",
        table_name="products_raw",
    )

    # Load orders
    load_csv_to_bigquery(
        file_name="orders.csv",
        table_name="orders_raw",
    )

    # Load generated summary
    load_csv_to_bigquery(
        file_name="daily_sales_summary.csv",
        table_name="daily_sales_summary_raw",
    )