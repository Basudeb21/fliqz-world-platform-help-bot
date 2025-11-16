from fastapi import FastAPI
from fastapi.responses import JSONResponse
import redis
from chatbot import ask_gpt  

app = FastAPI()
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
REDIS_QUEUE = "faq_questions"

@app.get("/help/get/{qs}")
async def push_question(qs: str):
    r.rpush(REDIS_QUEUE, qs)
    return JSONResponse({"status": "queued", "question": qs})

@app.get("/help/answer/{qs}")
async def get_answer(qs: str = None):
    if not qs:
        qs = r.lpop(REDIS_QUEUE)
        if not qs:
            return JSONResponse({"status": "empty", "answer": None})
    
    answer = ask_gpt(qs)
    return JSONResponse({"status": "success", "question": qs, "answer": answer})
