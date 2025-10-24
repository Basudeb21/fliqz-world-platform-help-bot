import json
import requests

# Load FAQ data
with open("faq_data.json", "r", encoding="utf-8") as f:
    faq_data = json.load(f)

def search_faq(question, top_n=3):
    """Keyword-based search in the FAQ JSON."""
    question_lower = question.lower()
    matches = []

    for item in faq_data:
        label = item.get("label", "").lower()
        answer = item.get("answer", "")
        score = 0
        for word in question_lower.split():
            if word in label:
                score += 1
        if score > 0:
            matches.append((score, f"Q: {item['label']}\nA: {answer}"))

    matches.sort(reverse=True)
    return [doc for _, doc in matches[:top_n]]

def ask_gpt(question, model="llama3.2:3b"):
    context_docs = search_faq(question)
    if not context_docs:
        return "⚠️ I can only answer questions related to Fliqz World. Please ask something about the platform."

    context = "\n".join(context_docs)

    prompt = f"""
You are a support assistant for Fliqz World platform.
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
        answer = ""
        for line in lines:
            try:
                obj = json.loads(line)
                answer += obj.get("response", "")
            except Exception:
                continue

        return answer.strip() if answer else "⚠️ AI returned empty response."
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
