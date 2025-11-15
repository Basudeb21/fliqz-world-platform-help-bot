import json
import requests
from difflib import SequenceMatcher
from state import user_states

TICKET_CATEGORIES = [
    "Payment Issue",
    "Order Not Delivered",
    "Account Access Issue",
    "Product Quality Issue",
    "Refund Request",
    "Other"
]


# Load FAQ data
with open("faq_data.json", "r", encoding="utf-8") as f:
    faq_data = json.load(f)

# Define greeting and acknowledgment patterns
GREETINGS = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
ACKNOWLEDGMENTS = ["ok", "okay", "thanks", "thank you", "got it", "understood", "alright", "cool", "nice"]

def is_greeting(text):
    """Check if the input is a greeting."""
    return any(word in text.lower().split() for word in GREETINGS)

def is_acknowledgment(text):
    """Check if the input is an acknowledgment."""
    return any(word in text.lower().split() for word in ACKNOWLEDGMENTS)


def search_faq(question, top_n=3):
    """Improved fuzzy + keyword-based search in the FAQ JSON."""
    question_lower = question.lower()
    matches = []

    for item in faq_data:
        label = item.get("label", "").lower()
        answer = item.get("answer", "").lower()
        combined_text = f"{label} {answer}"

        # Fuzzy similarity
        similarity = SequenceMatcher(None, question_lower, combined_text).ratio()

        # Keyword overlap
        q_words = set(question_lower.split())
        t_words = set(combined_text.split())
        common_words = len(q_words & t_words)

        # Weighted scoring
        score = similarity + (0.15 * common_words)

        if similarity > 0.25 or common_words > 0:
            matches.append((score, f"Q: {item['label']}\nA: {item['answer']}"))

    matches.sort(reverse=True)
    return [doc for _, doc in matches[:top_n]]


def ask_gpt(question,user_token, model="llama3"):

    # Initialize per-user ticket state
    if user_token not in user_states:
        user_states[user_token] = {
            "ticket_step": None,
            "is_ticket_generated": 0,
            "data": {"category": None, "subject": None, "description": None}
        }

    ts = user_states[user_token]

    # --- Ticket creation start ---
    if question.lower().strip() == "generate ticket":
        ts["is_ticket_generated"] = 0
        ts["ticket_step"] = "category"
        ts["data"] = {"category": None, "subject": None, "description": None}

        categories_list = "\n".join([f"- {c}" for c in TICKET_CATEGORIES])
        return f"Please select a category:\n{categories_list}"
    
    # ---- Category selection ----
    if ts["ticket_step"] == "category":
        if question in TICKET_CATEGORIES:
            ts["data"]["category"] = question
            ts["ticket_step"] = "subject"
            return "Great! Please enter a short subject for your issue."
        else:
            return "Please choose a valid category from the list."
        
     # ---- Subject step ----
    if ts["ticket_step"] == "subject":
        ts["data"]["subject"] = question
        ts["ticket_step"] = "description"
        return "Please describe your problem in detail."   
    

    # ---- Description step ----
    if ts["ticket_step"] == "description":
        ts["data"]["description"] = question
        ts["ticket_step"] = None
        ts["is_ticket_generated"] = 1
        return "Your ticket has been created successfully! 🎟️\n\nAny more queries?"


    



    # Handle greetings
    if is_greeting(question):
        return "👋 Hello! I'm the Fliqz World support assistant. How can I help you today?"
    
    # Handle acknowledgments
    if is_acknowledgment(question):
        return "😊 You're welcome! Is there anything else you'd like to know about Fliqz World?"
    
    # Search for relevant context
    context_docs = search_faq(question)
    
    # If no context found, provide contact information
    if not context_docs:
        return "I don't have specific information about that in my knowledge base.\n\n📞 For assistance with your query, please contact our support team:\n- Email: support@fliqzworld.com\n- Phone: +1-800-FLIQZ-HELP"
    
    # If context found, use it to answer
    context = "\n".join(context_docs)
    prompt = f"""
    You are a warm, friendly, and helpful support assistant for Fliqz World. 
    Your only source of truth is the information provided under "Context". 
    Always use the content from Context to answer the question directly and naturally. 
    If the answer clearly exists in the Context, do NOT say you lack information — use that answer to respond in a friendly, conversational way.

    Only if there is truly no relevant information in Context, then reply:
    "I don't have complete information about that. For more details, please contact our support team at support@fliqzworld.com or call +1-800-FLIQZ-HELP."

    Your tone should always be natural, kind, and conversational — like a real person helping a customer. 
    Write full, complete answers (2–4 sentences). 
    Do NOT mention or refer to the word "Context" in your reply under any circumstance.

    Context:
    {context}

    Question:
    {question}

    Now give a warm, friendly, and helpful answer using only the Context:
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
    except requests.exceptions.ConnectionError:
        return "⚠️ Unable to connect to the AI service. Please make sure Ollama is running.\n\n📞 For immediate assistance, contact:\n- Email: support@fliqzworld.com\n- Phone: +1-800-FLIQZ-HELP"
    except Exception as e:
        return f"⚠️ AI error: {e}\n\n📞 For assistance, contact:\n- Email: support@fliqzworld.com\n- Phone: +1-800-FLIQZ-HELP"

if __name__ == "__main__":
    print("🤖 Fliqz World Support Chatbot Ready! Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() in ["exit", "quit", "bye", "goodbye"]:
            print("👋 Goodbye! Thank you for using Fliqz World support!")
            break
        if not user_input.strip():
            continue
        answer = ask_gpt(user_input)
        print("Bot:", answer)
        print("-" * 50)