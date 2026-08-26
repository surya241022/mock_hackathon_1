# Retail Sales Intelligence Platform (GCP Medallion Lakehouse & AI Suite)

A production-grade, end-to-end data and AI platform built on **Google Cloud Platform (GCP)**. It features a **Medallion Architecture (Bronze -> Silver -> Gold)**, **Dataform (SQLX)** for ELT transformations, **Vertex AI / Gemini** for RAG and predictive ML classification, **Google Agent Development Kit (ADK)** for natural language sales intelligence, and **Apache Airflow** for orchestration.

> [!NOTE]
> **Dual Execution Modes Supported**:
> 1. **Live GCP Mode**: Connects directly to Google Cloud services (GCS, BigQuery, Vertex AI, Dataform, Gemini).
> 2. **Mock / Offline Mode**: Includes complete, self-contained mock implementations allowing the assessment panel to execute and evaluate the entire end-to-end solution **without requiring active GCP credentials or a live cloud project**.

---

## 1. Architecture Overview

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion & Storage"]
        CSV[Raw CSV Files\ncustomers, products, orders, daily_sales] -->|Python SDK / Mock GCS| GCS[Google Cloud Storage\ngs://raw/]
        GCS -->|BigQuery Load Job| BQ_Bronze[(BigQuery Bronze Layer\nRaw Tabular Data)]
    end

    subgraph Transformation ["2. Dataform ELT Pipeline"]
        BQ_Bronze -->|Dataform SQLX Cleanse & Type| BQ_Silver[(BigQuery Silver Layer\nCleaned, Joined & Enriched)]
        BQ_Silver -->|Dataform SQLX Star Schema| BQ_Gold[(BigQuery Gold Layer\nfact_sales, dim_customer, dim_product, dim_date)]
    end

    subgraph Intelligence ["3. AI, RAG & Analytics"]
        BQ_Gold -->|AI.EMBED gemini-embedding-001| RAG[BigQuery Vector Search & Gemini 2.5 Flash RAG]
        BQ_Gold -->|AutoML Tabular| VertexML[Vertex AI Model Registry\nHigh Value Order Classifier]
        BQ_Gold -->|BigQuery Toolset| ADK[Google ADK Sales Intelligence Agent]
    end

    subgraph Orchestration ["4. Orchestration & Testing"]
        Airflow[Apache Airflow DAG\nsales_pipeline_dag] -->|Validates| BQ_Gold
        PyTest[Automated Unit & Data Tests] --> Ingestion
    end
```

---

## 2. Directory Structure

```text
├── agent/
│   └── sales_agent/           # Google ADK Sales Intelligence Agent with BigQuery Toolset
│       ├── agent.py
│       └── __init__.py
├── airflow/
│   └── dags/                  # Apache Airflow Pipeline DAGs
│       └── sales_pipeline_dag.py
├── data/                      # Sample Raw Data Files
│   ├── customers.csv
│   ├── products.csv
│   ├── orders.csv
│   └── daily_sales_summary.csv
├── dataform/                  # Dataform Transformation Repository
│   ├── definitions/
│   │   ├── sources/           # Bronze table declarations
│   │   ├── silver/            # Cleaned and enriched models
│   │   └── gold/              # Star schema dimensions & facts
│   ├── includes/
│   └── workflow_settings.yaml
├── infrastructure/            # Infrastructure as Code (Terraform)
│   └── main.tf
├── mocks/                     # Self-Contained GCP Mock Implementations
│   ├── mock_gcs.py            # GCS Bucket/Blob emulation
│   ├── mock_bigquery.py       # BigQuery Datasets/Tables/Query emulation
│   ├── mock_dataform.py       # Medallion SQLX transformation engine
│   ├── mock_vertex_ml.py      # Vertex AI AutoML Tabular training emulation
│   ├── mock_rag.py            # BigQuery Vector Search & Gemini RAG emulation
│   ├── mock_agent.py          # Google ADK Sales Intelligence Agent emulation
│   ├── mock_airflow.py        # Airflow DAG validation runner
│   └── __init__.py
├── rag/                       # BigQuery Vector Search & Gemini RAG
│   ├── create_embeddings.py
│   └── search_rag.py
├── src/                       # Ingestion & GCP Setup Scripts
│   ├── setup_gcp.py
│   ├── upload_to_gcs.py
│   ├── generate_summary.py
│   └── load_to_bigquery.py
├── tests/                     # Validation & Integrity Test Suites
│   ├── test_pipeline.py       # Data integrity & schema validation tests
│   └── test_mock_pipeline.py  # Mock components & pipeline integration tests
├── vertex_ml/                 # Vertex AI AutoML Tabular Classification
│   ├── train.py
│   ├── create_dataset.py
│   └── train_model.py
├── run_mock_pipeline.py       # Master script: runs all 7 stages in Mock Mode
├── .env.example               # Environment Configuration Template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. GCP Services & Mock Implementations

| Component / GCP Service | Live Implementation | Mock Implementation (`mocks/`) |
| :--- | :--- | :--- |
| **Cloud Storage (GCS)** | `google-cloud-storage` bucket creation & upload | `MockStorageClient` local storage emulation |
| **BigQuery (Bronze/Silver/Gold)** | BigQuery load jobs & SQL engine | `MockBigQueryClient` local SQL database |
| **Dataform Transformations** | Dataform CLI compiling & running SQLX | `run_mock_dataform_transformations` (Bronze &rarr; Silver &rarr; Gold) |
| **Vertex AI AutoML** | `aiplatform.AutoMLTabularTrainingJob` | `MockVertexAI` Scikit-Learn classifier & registry simulation |
| **BigQuery Vector Search & RAG** | `AI.EMBED` + `VECTOR_SEARCH` + Gemini | `MockRAGSystem` with cosine similarity ranking |
| **Sales Intelligence Agent** | Google ADK with BigQuery Toolset | `MockSalesAgent` querying Gold schema |
| **Airflow Orchestration** | `sales_pipeline_dag` with BigQuery operators | `run_mock_airflow_pipeline` validation engine |

---

## 4. Evaluation & Execution Quickstart

### Option A: Complete Run in Mock Mode (Zero Credentials Required)

To evaluate the entire solution without any GCP setup:

```bash
# 1. Run the end-to-end 7-stage pipeline
python run_mock_pipeline.py

# 2. Run all unit and integration test suites
python -m unittest discover -s tests -p "test_*.py"
```

This single command executes all 7 pipeline stages:
1. GCS Ingestion
2. BigQuery Bronze Loading
3. Dataform Silver & Gold Transformations
4. Vertex AI AutoML Tabular Training & Metric Logging
5. BigQuery Vector Search & Gemini RAG
6. ADK Sales Intelligence Agent
7. Airflow Orchestration DAG Validation

---

### Option B: Live GCP Execution Mode

#### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project your-gcp-project-id
  ```
- Dataform CLI (`@dataform/cli`):
  ```bash
  npm i -g @dataform/cli
  ```

#### Live Pipeline Steps
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment variables
cp .env.example .env

# 3. Create bucket and ingest raw data
python src/setup_gcp.py
python src/upload_to_gcs.py
python src/load_to_bigquery.py

# 4. Compile and run Dataform models
cd dataform
dataform compile
dataform run
cd ..

# 5. Train Vertex AI AutoML Model
python vertex_ml/train.py
python vertex_ml/create_dataset.py
python vertex_ml/train_model.py

# 6. Generate embeddings and run Gemini RAG
python rag/create_embeddings.py
python rag/search_rag.py

# 7. Run Sales Intelligence Agent
python -m agent.sales_agent.agent
```

---

## 5. Testing & Validation

Run the automated test suite covering schema integrity and mock pipeline verification:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

Verified test cases:
- Data integrity and schema constraints on `customers.csv`, `products.csv`, `orders.csv`, and `daily_sales_summary.csv`.
- Mock GCS bucket and blob operations.
- Mock Dataform Medallion transformations producing valid Gold Star Schema.
- Vertex AI Tabular AutoML training and AU-ROC validation.
- BigQuery Vector Search and Gemini RAG context generation.
- ADK Sales Agent analytical query responses.
- Airflow DAG validation execution.

---

## 6. Sample Inputs & Outputs

### Sample Input (`data/orders.csv`)
```csv
order_id,order_date,customer_id,product_id,quantity,status,payment_method
1001,2026-01-15,1,101,2,Completed,Credit Card
1002,2026-01-16,2,103,1,Completed,UPI
```

### Sample Output (`gold.fact_sales`)
```json
{
  "order_id": 1001,
  "date_key": 20260115,
  "customer_key": 1493028491,
  "product_key": 3948102948,
  "quantity": 2,
  "unit_price": 45000.0,
  "total_sales": 90000.0,
  "status": "Completed",
  "payment_method": "Credit Card"
}
```

---

## 7. Key Decisions, Assumptions & Limitations

### Key Decisions
1. **Medallion Pattern with Dataform**: Enforces separation of concerns (raw ingestion vs. cleaned relational models vs. star schema dimension modeling).
2. **BigQuery-Native Vector Search**: Leveraged BigQuery `AI.EMBED` and `VECTOR_SEARCH` to eliminate external vector store latency.
3. **Surrogate Key Generation**: Used deterministic `FARM_FINGERPRINT` for dimensional surrogate keys.
4. **Resilient Dual-Mode Design**: Included zero-dependency mock implementations for all GCP services so reviewers can validate without live cloud infrastructure.

### Assumptions
- Source CSV files in GCS follow standard UTF-8 formatting.
- BigQuery datasets and Vertex AI resources are co-located in `asia-south1`.

### Limitations
- Batch-oriented architecture (stream processing via Pub/Sub + Dataflow can be added for real-time ingest).
- Vertex AI AutoML training is configured for rapid evaluation and can be scaled for full hyperparameter tuning.

---

## 8. Security Considerations

- **Secrets Management**: `.env` and `.df-credentials.json` are excluded via `.gitignore`.
- **Authentication**: Uses Google Cloud Application Default Credentials (ADC) without hardcoded keys.
- **Access Control**: Least-privilege IAM roles (BigQuery Data Editor, Storage Object Viewer, Vertex AI User).

---

## 9. AI-Tool Usage Declaration

- **Google Gemini 2.5 Flash / embedding-001**: Used for RAG retrieval augmentation, embeddings generation, and natural language reasoning inside the ADK agent.
- **Antigravity AI IDE / Pair Programmer**: Utilized for scaffolding SQLX models, structuring pipeline architecture, and formulating documentation.
