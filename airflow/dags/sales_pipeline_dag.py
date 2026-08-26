from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator


PROJECT_ID = "mock-trail-project-1"
DATASET = "gold"


default_args = {
    "owner": "sales-data-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="sales_pipeline_dag",
    default_args=default_args,
    description="Orchestrates the sales analytics pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sales", "bigquery", "dataform"],
) as dag:

    # --------------------------------------------------
    # Task 1: Validate Gold layer
    # --------------------------------------------------

    validate_gold = BigQueryInsertJobOperator(
        task_id="validate_gold",

        configuration={
            "query": {
                "query": f"""
                    SELECT COUNT(*) AS row_count
                    FROM `{PROJECT_ID}.{DATASET}.fact_sales`
                """,
                "useLegacySql": False,
            }
        },

        location="asia-south1",
    )


    # --------------------------------------------------
    # Task 2: Validate dimensions
    # --------------------------------------------------

    validate_dimensions = BigQueryInsertJobOperator(
        task_id="validate_dimensions",

        configuration={
            "query": {
                "query": f"""
                    SELECT
                        (SELECT COUNT(*) 
                         FROM `{PROJECT_ID}.{DATASET}.dim_customer`) 
                            AS customer_count,

                        (SELECT COUNT(*) 
                         FROM `{PROJECT_ID}.{DATASET}.dim_product`) 
                            AS product_count,

                        (SELECT COUNT(*) 
                         FROM `{PROJECT_ID}.{DATASET}.dim_date`) 
                            AS date_count
                """,
                "useLegacySql": False,
            }
        },

        location="asia-south1",
    )


    # --------------------------------------------------
    # Dependencies
    # --------------------------------------------------

    validate_gold >> validate_dimensions