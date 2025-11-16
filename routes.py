from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis
from chatbot import ask_gpt  # your existing ask_gpt function
from state import user_states



app = FastAPI()
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
REDIS_QUEUE = "faq_questions"

# Route 1: push question to Redis
@app.get("/help/get/{qs}")
async def push_question(qs: str):
    r.rpush(REDIS_QUEUE, qs)
    return JSONResponse({"status": "queued", "question": qs})

# Route 2: get answer (either from URL param or Redis queue)
@app.get("/help/answer/{qs}")
async def get_answer(qs: str, request: Request):
    # Extract Bearer Token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else "guest"

    answer = ask_gpt(qs, user_token=token)

    return JSONResponse({
        "status": "success",
        "question": qs,
        "token_used": token,
        "answer": answer
    })


@app.get("/help/ticket")
async def get_ticket(request: Request):

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else "guest"

    if token in user_states and user_states[token]["is_ticket_generated"] == 1:
        return JSONResponse({
            "status": "success",
            "ticket": user_states[token]["data"]
        })

    return JSONResponse({
        "status": "no_ticket",
        "message": "No ticket has been generated yet."
    })
    