from pathlib import Path
import json
import sqlite3
from contextlib import closing
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import re
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai.exceptions import UsageLimitExceeded, UnexpectedModelBehavior
if __package__:
    from . import auth, memory
    from .agent import load_agent, reply_to
    from .models import ChatRequest, ChatReply, ChatMessage
else:
    import auth, memory
    from agent import load_agent, reply_to
    from models import ChatRequest, ChatReply, ChatMessage
from fastapi.staticfiles import StaticFiles

DATA = Path(__file__).resolve().parents[1] / "data"
@asynccontextmanager
async def lifespan(app):
    auth.initialize()
    memory.initialize()
    async with load_agent() as agent:
        app.state.chat_agent = agent
        yield

app = FastAPI(title="Campus Customs API", lifespan=lifespan)
app.include_router(auth.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv('FRONTEND_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type', 'X-Campus-Request'],
)

def log_chat_error(exc, payload):
    # Full stack and chained exceptions, without local-variable dumps.
    detail = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    for key, value in os.environ.items():
        if value and any(word in key for word in ('KEY', 'TOKEN', 'SECRET')):
            detail = detail.replace(value, '[REDACTED]')
    for text in [payload.message, *(m.content for m in payload.history)]:
        if text: detail = detail.replace(text, '[CHAT TEXT REDACTED]')
    detail = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED KEY]', detail)
    logging.getLogger(__name__).error('Chat failed:\n%s', detail)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc):
    # Never echo submitted passwords in validation errors.
    return JSONResponse(status_code=422, content={"detail": "Please check all fields and their length limits."})

app.mount("/images", StaticFiles(directory=DATA / "products"), name="images")


def connect():
    db = sqlite3.connect(f"{(DATA / 'campus_customs.db').as_uri()}?mode=rw", uri=True)
    db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = sqlite3.Row
    return db


def serialize(row):
    product = dict(row)
    for field in ("colors", "search_tags"):
        product[field] = json.loads(product[field])
    product["image_url"] = "/images/" + Path(product["image_file_path"]).name
    return product


@app.get("/api/products")
def products():
    with closing(connect()) as db:
        return [serialize(row) for row in db.execute("SELECT c.*, (SELECT SUM(quantity) FROM inventory i WHERE i.product_id=c.product_id) AS total_stock FROM catalogue c ORDER BY name")]


@app.get("/api/products/{product_id}")
def product(product_id: str):
    with closing(connect()) as db:
        row = db.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        result = serialize(row)
        result["inventory"] = [dict(row) for row in db.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)
        )]
        return result


auth.connect = connect


@app.post('/api/chat', response_model=ChatReply)
async def chat(payload: ChatRequest, request: Request):
    auth.guard(request)
    user = auth.current_user(request)
    deps = memory.dependencies(user, payload.page)
    if user:
        payload = payload.model_copy(update={'history': [ChatMessage.model_validate({k:v for k,v in m.items() if k in ('role','content')}) for m in memory.history(user['id'], limit=6)]})
    agent = request.app.state.chat_agent
    if agent is None:
        raise HTTPException(503, 'Chat is not configured. Please try again later.')
    try:
        async with asyncio.timeout(50):
            result = await reply_to(agent, payload, deps)
            if user:
                current = auth.current_user(request)
                if current and current["id"] == user["id"]: memory.save(user["id"], payload, result)
            return result
    except HTTPException:
        raise
    except TimeoutError as exc:
        log_chat_error(exc, payload)
        raise HTTPException(504, 'The assistant took too long. Please try again.')
    except Exception as exc:
        log_chat_error(exc, payload)
        if isinstance(exc, UsageLimitExceeded):
            raise HTTPException(502, 'This request needed too many lookups. Please try one product or size at a time.')
        if isinstance(exc, UnexpectedModelBehavior):
            raise HTTPException(502, 'The assistant could not finish a valid reply. Please try again.')
        raise HTTPException(502, 'The assistant is temporarily unavailable. Please try again.')


@app.get('/api/chat/history')
def chat_history(request: Request):
    user = auth.current_user(request)
    return JSONResponse({'messages': memory.history(user['id']) if user else []}, headers={'Cache-Control':'no-store'})
