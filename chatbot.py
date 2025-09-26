import json
import chromadb
from chromadb.utils import embedding_functions
import requests

embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_faq")
collection = client.get_or_create_collection(
    name="creator_faq",
    embedding_function=embedder
)

with open("faq_data.json", "r", encoding="utf-8") as f:
    faq_data = json.load(f)

if collection.count() == 0:
    ids = [str(item["id"]) for item in faq_data]
    docs = [f"Q: {item['label']}\nA: {item['answer']}" for item in faq_data]
    metas = [{"category": "faq", "type": "creator"} for _ in faq_data]
    collection.add(ids=ids, documents=docs, metadatas=metas)
    print(f"✅ {len(faq_data)} FAQ entries added to ChromaDB.")
else:
    print(f"ℹ️ ChromaDB already contains {collection.count()} entries.")



def ask_gpt(question, model="llama3.2:3b"):
    results = collection.query(query_texts=[question], n_results=3)
    docs = results.get("documents", [[]])[0]
    if not docs:
        return "Sorry, I couldn’t find any relevant info."

    context = "\n".join(docs)
    
    prompt = f"""
You are a highly intelligent support assistant for Fliqz World platform.
Use ONLY the context below to answer the question clearly and naturally.

Context:
{context}

Question:
{question}

Provide a concise, clear, and helpful answer.
"""

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "max_tokens": 400},
            timeout=120
        )
        lines = res.text.strip().split("\n")
        full_answer = ""
        import json
        for line in lines:
            try:
                obj = json.loads(line)
                text = obj.get("response", "")
                full_answer += text
            except Exception:
                continue

        full_answer = full_answer.strip()
        if not full_answer:
            return "⚠️ AI returned empty response."
        return full_answer

    except Exception as e:
        return f"⚠️ AI error: {e}"




if __name__ == "__main__":
    print("🤖 GPT FAQ Chatbot Ready! Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        answer = ask_gpt(user_input)
        print("Bot:", answer)
        print("-" * 50)
