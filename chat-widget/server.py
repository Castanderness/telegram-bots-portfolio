"""
FastAPI backend for chat widget.
Embed widget.html on any site, point API_URL to this server.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="."), name="static")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT",
    "You are a helpful website assistant. Be concise and friendly. Answer in Russian.")

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = req.history[-10:]  # keep last 10 messages
    messages.append({"role": "user", "content": req.message})
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return {"reply": response.content[0].text}

@app.get("/")
async def index():
    from fastapi.responses import FileResponse
    return FileResponse("widget.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
