"""FastAPI 服务 — 旅行规划 API

启动:
    uv run python -m backend.app.server
    或: uv run uvicorn backend.app.server:app --reload

API 文档: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .models.schemas import TripRequest, TripPlanResponse
from .services.trip_service import execute_plan, stream_plan


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"  Server: http://{settings.host}:{settings.port}")
    print(f"  Docs:   http://{settings.host}:{settings.port}/docs")
    yield


# ============================================================
# App
# ============================================================

app = FastAPI(
    title="Trip Planner API",
    description="基于 LangGraph 的多 Agent 旅行规划服务",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REST
# ============================================================

@app.post("/api/trip/plan", response_model=TripPlanResponse)
def create_trip_plan(request: TripRequest) -> TripPlanResponse:
    """同步创建旅行计划"""
    try:
        return execute_plan(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"规划失败: {str(e)}")


@app.post("/api/trip/plan/stream")
def stream_trip_plan(request: TripRequest):
    """SSE 流式旅行计划 — 实时显示 Agent 执行进度"""
    return StreamingResponse(
        stream_plan(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}
