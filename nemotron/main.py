from openai import OpenAI
import numpy as np
import faiss

client = OpenAI(
  base_url = "https://api.brev.dev/v1",
  api_key = "brev_api_-35DV28tOosEzIPqAC1NfJ3KxyLD"
)


MODEL_ID = "nvcf:nvidia/nemotron-nano-9b-v2:dep-35DlFC5afupH0iGHCwyejhDcfgd"
EMBED_MODEL = "text-embedding-3-small" 

docs = [
    "Server GPU overheating on node 12. Fan speed at 80%.",
    "Error 504 timeout in cooling subsystem. Restart resolved issue.",
    "Routine maintenance requires GPU firmware update to version 2.4.",
    "Datacenter technician guide: check airflow, then power cycle rack."
]

# Create embeddings
embeddings = [client.embeddings.create(model=EMBED_MODEL, input=d).data[0].embedding for d in docs]
embedding_dim = len(embeddings[0])

# Build FAISS index
index = faiss.IndexFlatL2(embedding_dim)
index.add(np.array(embeddings, dtype="float32"))

def retrieve_context(query, k=2):
    q_emb = client.embeddings.create(model=EMBED_MODEL, input=query).data[0].embedding
    D, I = index.search(np.array([q_emb], dtype="float32"), k)
    return [docs[i] for i in I[0]]

def generate_with_context(query):
    context = "\n".join(retrieve_context(query))
    prompt = f"""You are a datacenter assistant.
Use the following context to answer the technician's query.

Context:
{context}

Question: {query}
"""

    completion = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": "You help datacenter technicians troubleshoot server and GPU issues."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        top_p=0.7,
        max_tokens=512,
        stream=True
    )

    print("\n--- Nemotron Response ---\n")
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")

query = "The GPU cluster is throttling at high temps, what should I do?"
generate_with_context(query)