from google.cloud import aiplatform


PROJECT_ID = "mock-trail-project-1"
REGION = "asia-south1"

aiplatform.init(
    project=PROJECT_ID,
    location=REGION
)


print("Finding Vertex AI dataset...")

# List datasets in this project/location
datasets = aiplatform.TabularDataset.list()

dataset = None

for ds in datasets:
    print(f"Found dataset: {ds.display_name}")
    
    if ds.display_name == "high-value-orders-dataset":
        dataset = ds
        break


if dataset is None:
    raise RuntimeError(
        "Could not find high-value-orders-dataset in Vertex AI."
    )


print("\n[OK] Vertex AI dataset found")
print("Name:", dataset.display_name)
print("Resource:", dataset.resource_name)


# ---------------------------------------------------------
# Create AutoML classification training job
# ---------------------------------------------------------

print("\nStarting AutoML training...")


job = aiplatform.AutoMLTabularTrainingJob(
    display_name="high-value-order-classifier",
    optimization_prediction_type="classification",
    optimization_objective="maximize-au-roc",
)


model = job.run(
    dataset=dataset,
    target_column="high_value_order",

    model_display_name="high-value-order-model",

    budget_milli_node_hours=1000,

    disable_early_stopping=False,
)


print("\n===================================")
print("[OK] MODEL TRAINING COMPLETED")
print("===================================")

print("Model:", model.display_name)
print("Model resource:", model.resource_name)
