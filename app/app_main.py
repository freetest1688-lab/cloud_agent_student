import sys
import os

# Make the agent/ directory importable as a package source.
AGENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent")
sys.path.insert(0, AGENT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from router import chat
from service.chat_service import init_agent_system

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_agent_system()
    yield
    # Shutdown (nothing to clean up for now)
    pass

app = FastAPI(title="Multi-Agent Cloud Service API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_main:app", host="0.0.0.0", port=8090, reload=True)
