from google.cloud import aiplatform


PROJECT_ID = "mock-trail-project-1"
REGION = "asia-south1"

BQ_SOURCE = (
    "bq://mock-trail-project-1.gold.ml_high_value_orders"
)


# Initialize Vertex AI
aiplatform.init(
    project=PROJECT_ID,
    location=REGION
)


print("Creating Vertex AI Tabular Dataset...")

dataset = aiplatform.TabularDataset.create(
    display_name="high-value-orders-dataset",
    bq_source=BQ_SOURCE,
)

print("\n[OK] Vertex AI dataset created")
print("Dataset name:", dataset.display_name)
print("Dataset resource:", dataset.resource_name)
