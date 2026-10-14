import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import health, ingestion, list_docs, chat, sessions, admin, usage, me, platform
from db.sessions import init_db
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.rate_limit import limiter
from dotenv import load_dotenv
import os 

load_dotenv()
app = FastAPI(title="RAG Agent API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
init_db()
logging.basicConfig(level=logging.INFO)
allowed = os.getenv("ALLOWED_ORIGINS")



app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed],  # exact origin required, not "*", when credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingestion.router)
app.include_router(list_docs.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(admin.router)
app.include_router(usage.router) 
app.include_router(me.router)
app.include_router(platform.router)
