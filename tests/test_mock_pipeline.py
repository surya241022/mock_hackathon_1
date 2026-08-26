import unittest
from pathlib import Path
from mocks.mock_gcs import MockStorageClient
from mocks.mock_bigquery import MockBigQueryClient
from mocks.mock_dataform import run_mock_dataform_transformations
from mocks.mock_vertex_ml import MockVertexAI
from mocks.mock_rag import MockRAGSystem
from mocks.mock_agent import MockSalesAgent
from mocks.mock_airflow import run_mock_airflow_pipeline


class TestMockPipeline(unittest.TestCase):

    def setUp(self):
        self.bq_client = MockBigQueryClient(project="mock-trail-project-1")

    def test_mock_gcs_upload_and_exists(self):
        gcs = MockStorageClient(project="mock-trail-project-1")
        bucket = gcs.create_bucket("test-bucket")
        self.assertTrue(bucket.exists())

    def test_mock_dataform_transformations(self):
        fact_sales = run_mock_dataform_transformations(self.bq_client)
        self.assertFalse(fact_sales.empty)
        self.assertIn("total_sales", fact_sales.columns)
        self.assertIn("customer_key", fact_sales.columns)

    def test_mock_vertex_ai_training(self):
        vertex_ai = MockVertexAI(project="mock-trail-project-1")
        model = vertex_ai.train_automl_model()
        self.assertIsNotNone(model)
        self.assertGreater(model.metrics["au_roc"], 0.8)

    def test_mock_rag_system(self):
        rag = MockRAGSystem(project="mock-trail-project-1")
        count = rag.create_rag_documents_and_embeddings()
        self.assertGreater(count, 0)
        results, answer = rag.search_and_answer("Monitor sales in Maharashtra")
        self.assertTrue(len(results) > 0)
        self.assertIn("Monitor", answer)

    def test_mock_sales_agent(self):
        agent = MockSalesAgent(project="mock-trail-project-1")
        response = agent.answer_query("What is the total sales revenue?")
        self.assertIn("total completed sales revenue", response.lower())

    def test_mock_airflow_dag(self):
        results = run_mock_airflow_pipeline(self.bq_client)
        self.assertEqual(results["status"], "SUCCESS")
        self.assertGreater(results["fact_sales_rows"], 0)


if __name__ == "__main__":
    unittest.main()
