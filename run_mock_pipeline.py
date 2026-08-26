"""End-to-End Mock Pipeline Runner for Evaluation without Live GCP Credentials.

Runs the complete lifecycle:
1. GCS Ingestion
2. BigQuery Bronze Loading
3. Dataform Silver & Gold Transformations
4. Vertex AI Tabular AutoML Model Training
5. BigQuery Vector Search & Gemini RAG
6. Sales Intelligence Agent Query
7. Airflow Orchestration DAG Validation
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mocks.mock_gcs import MockStorageClient
from mocks.mock_bigquery import MockBigQueryClient
from mocks.mock_dataform import run_mock_dataform_transformations
from mocks.mock_vertex_ml import MockVertexAI
from mocks.mock_rag import MockRAGSystem
from mocks.mock_agent import MockSalesAgent
from mocks.mock_airflow import run_mock_airflow_pipeline


def main():
    print("=" * 80)
    print("  GCP SALES INTELLIGENCE PLATFORM - END-TO-END OFFLINE / MOCK RUNNER")
    print("=" * 80)

    # 1. Mock GCS Ingestion
    print("\n[STAGE 1] INGESTION TO MOCK GOOGLE CLOUD STORAGE")
    gcs = MockStorageClient(project="mock-trail-project-1")
    bucket = gcs.create_bucket("mock-project-bucket-surya")
    
    data_files = ["customers.csv", "products.csv", "orders.csv", "daily_sales_summary.csv"]
    for f in data_files:
        src = PROJECT_ROOT / "data" / f
        if src.exists():
            blob = bucket.blob(f"raw/{f}")
            blob.upload_from_filename(str(src))

    # 2. Mock BigQuery Bronze Loading
    print("\n[STAGE 2] BIGQUERY BRONZE DATASET CREATION & INGESTION")
    bq = MockBigQueryClient(project="mock-trail-project-1")
    bq.create_dataset("mock-trail-project-1.bronze")
    
    bq.load_table_from_uri("gs://mock-project-bucket-surya/raw/customers.csv", "mock-trail-project-1.bronze.customers_raw")
    bq.load_table_from_uri("gs://mock-project-bucket-surya/raw/products.csv", "mock-trail-project-1.bronze.products_raw")
    bq.load_table_from_uri("gs://mock-project-bucket-surya/raw/orders.csv", "mock-trail-project-1.bronze.orders_raw")
    bq.load_table_from_uri("gs://mock-project-bucket-surya/raw/daily_sales_summary.csv", "mock-trail-project-1.bronze.daily_sales_summary_raw")

    # 3. Dataform Transformations (Silver & Gold)
    print("\n[STAGE 3] DATAFORM ELT TRANSFORMATIONS (BRONZE -> SILVER -> GOLD)")
    bq.create_dataset("mock-trail-project-1.silver")
    bq.create_dataset("mock-trail-project-1.gold")
    run_mock_dataform_transformations(bq)

    # 4. Vertex AI AutoML Training
    print("\n[STAGE 4] VERTEX AI AUTOML TABULAR MODEL TRAINING")
    vertex_ai = MockVertexAI(project="mock-trail-project-1", region="asia-south1")
    model = vertex_ai.train_automl_model()

    # 5. BigQuery Vector Search & Gemini RAG
    print("\n[STAGE 5] BIGQUERY VECTOR SEARCH & GEMINI RAG")
    rag = MockRAGSystem(project="mock-trail-project-1")
    rag.create_rag_documents_and_embeddings()
    test_question = "What are the total sales for electronics products in Maharashtra?"
    print(f"Question: '{test_question}'")
    _, answer = rag.search_and_answer(test_question)
    print("\nGenerated RAG Answer:")
    print(answer)

    # 6. Sales Intelligence Agent
    print("\n[STAGE 6] GOOGLE ADK SALES INTELLIGENCE AGENT")
    agent = MockSalesAgent(project="mock-trail-project-1")
    agent_query = "What is our overall sales revenue and top performing state?"
    print(f"Agent Query: '{agent_query}'")
    agent_response = agent.answer_query(agent_query)
    print("\nAgent Response:")
    print(agent_response)

    # 7. Airflow Validation Pipeline
    print("\n[STAGE 7] APACHE AIRFLOW PIPELINE ORCHESTRATION")
    run_mock_airflow_pipeline(bq)

    print("\n" + "=" * 80)
    print("  [OK] ALL 7 STAGES COMPLETED SUCCESSFULLY IN MOCK MODE (NO CREDENTIALS REQUIRED)")
    print("=" * 80)


if __name__ == "__main__":
    main()
