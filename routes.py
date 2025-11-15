from fastapi import FastAPI
from fastapi.responses import JSONResponse
import redis
from chatbot import ask_gpt  # your existing ask_gpt function
from state import ticket_state



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
async def get_answer(qs: str = None):
    if not qs:
        qs = r.lpop(REDIS_QUEUE)
        if not qs:
            return JSONResponse({"status": "empty", "answer": None})
    
    answer = ask_gpt(qs)
    return JSONResponse({"status": "success", "question": qs, "answer": answer})


@app.get("/help/ticket")
async def get_ticket():
    ts = ticket_state

    if ts["is_ticket_generated"] == 1:
        return JSONResponse({
            "status": "success",
            "ticket": ts["data"]
        })

    return JSONResponse({
        "status": "no_ticket",
        "message": "No ticket has been generated yet."
    })
