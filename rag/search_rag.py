from google.cloud import bigquery
from google import genai


PROJECT_ID = "mock-trail-project-1"
DATASET = "gold"

client = bigquery.Client(project=PROJECT_ID)

# Gemini client using Vertex AI
genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location="global"
)


question = input("\nAsk a question: ")


# ---------------------------------------------------------
# 1. Convert question into an embedding
# ---------------------------------------------------------

query = f"""
WITH query_embedding AS (
    SELECT
        AI.EMBED(
            @question,
            endpoint => 'gemini-embedding-001',
            task_type => 'RETRIEVAL_QUERY'
        ).result AS embedding
)

SELECT
    base.record_id,
    base.content,
    distance

FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET}.rag_embeddings`,
    'embedding',
    TABLE query_embedding,
    'embedding',
    top_k => 5,
    distance_type => 'COSINE'
)

ORDER BY distance
"""


job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter(
            "question",
            "STRING",
            question
        )
    ]
)


# ---------------------------------------------------------
# 2. Retrieve relevant records
# ---------------------------------------------------------

print("\nSearching RAG knowledge base...\n")

results = list(
    client.query(
        query,
        job_config=job_config
    ).result()
)


# ---------------------------------------------------------
# 3. Build context for Gemini
# ---------------------------------------------------------

context_parts = []

for row in results:
    context_parts.append(
        f"""
Record ID: {row.record_id}
Similarity distance: {row.distance}
Content: {row.content}
"""
    )

context = "\n".join(context_parts)


# ---------------------------------------------------------
# 4. Ask Gemini using ONLY retrieved context
# ---------------------------------------------------------

prompt = f"""
You are a sales analytics assistant.

Answer the user's question using ONLY the
retrieved sales records below.

Do not use outside knowledge.
Do not invent information.
If the retrieved records do not contain enough
information to answer the question, say so.

User question:
{question}

Retrieved sales records:
{context}

Provide a concise, factual answer.
"""


response = genai_client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)


# ---------------------------------------------------------
# 5. Display final answer
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("RAG ANSWER")
print("=" * 80)

print(response.text)