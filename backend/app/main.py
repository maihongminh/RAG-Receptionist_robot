import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api.auth import router as auth_router
from app.api.ask import router as ask_router
from app.core.request_context import set_request_context, get_elapsed_ms


app = FastAPI(
    title="Robot Reception API",
    version="0.1.0",
    description="AI receptionist backend with core orchestrator and domain adapters.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router)
app.include_router(auth_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_context(request_id, time.perf_counter())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    elapsed_ms = get_elapsed_ms()
    if elapsed_ms is not None:
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
