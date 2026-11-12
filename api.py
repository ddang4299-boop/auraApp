"""Tuỳ chọn: bọc Engine thành HTTP để app (bất kỳ ngôn ngữ nào) gọi.
pip install fastapi uvicorn anthropic ; uvicorn api:app --port 8000
Engine stateless => app/DB giữ `state` (JSON) và gửi lại mỗi lượt."""
import os
from typing import Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from Chatbot import Engine, make_llm

engine = Engine("Mona_Lisa", llm=make_llm())
app = FastAPI()

class StepReq(BaseModel):
    state: dict
    option_id: Optional[str] = None   # bấm nút
    text: Optional[str] = None        # nhập tự do

@app.post("/chat/start")
def start() -> Any:
    return engine.start()

@app.post("/chat/step")
def step(req: StepReq) -> Any:
    return engine.step(req.state, {"option_id": req.option_id} if req.option_id else (req.text or ""))