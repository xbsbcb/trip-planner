"""FastAPI 服务 — 旅行规划 API

启动:
    uv run python -m backend.app.server
    或: uv run uvicorn backend.app.server:app --reload

API 文档: http://localhost:8000/docs
"""

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .models.schemas import TripRequest, TripPlanResponse
from .graph.trip_planner_graph import build_graph, TripPlannerState


# ============================================================
# 生命周期 — 编译 Graph 为模块级单例
# ============================================================

_graph = None


def get_graph():
    """获取编译好的 Graph 实例"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭"""
    settings = get_settings()
    print(f"  Server: http://{settings.host}:{settings.port}")
    print(f"  Docs:   http://{settings.host}:{settings.port}/docs")
    # 预热 Graph（首次编译可能耗时）
    get_graph()
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
    """创建旅行计划

    提交旅行城市、日期、偏好，返回结构化的旅行计划（景点、酒店、天气、预算）。
    """
    graph = get_graph()

    initial_state: TripPlannerState = {
        "messages": [],
        "current_agent": "",
        "city": request.city,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "travel_days": request.travel_days,
        "transportation": request.transportation,
        "accommodation": request.accommodation,
        "preferences": request.preferences,
        "free_text_input": request.free_text_input or "",
        "attractions_result": "",
        "weather_result": "",
        "hotel_result": "",
        "plan_result": "",
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"规划失败: {str(e)}")

    plan_raw = final_state.get("plan_result", "")
    if not plan_raw:
        raise HTTPException(status_code=500, detail="规划结果为空")

    # Planner 输出是 JSON 字符串，还原为 dict
    try:
        plan_data = json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="旅行计划格式错误",
        )

    return TripPlanResponse(success=True, message="规划完成", data=plan_data)


# ============================================================
# 节点名 → 中文标签映射
# ============================================================

NODE_LABELS = {
    "attraction_agent": "景点搜索中...",
    "weather_agent": "天气查询中...",
    "hotel_agent": "酒店搜索中...",
    "planner_agent": "行程规划中...",
    "tools_node": "数据获取中...",
    "attraction_done": "景点搜索完成",
    "weather_done": "天气查询完成",
    "hotel_done": "酒店搜索完成",
    "planner_done": "行程规划完成",
}


@app.post("/api/trip/plan/stream")
def stream_trip_plan(request: TripRequest):
    """SSE 流式返回旅行规划进度

    事件格式: data: {"node": "attraction_agent", "label": "景点搜索中..."}
    完成后发送: data: {"done": true, "plan": {...}}
    错误时发送: data: {"error": "错误信息"}
    """
    graph = get_graph()

    initial_state: TripPlannerState = {
        "messages": [],
        "current_agent": "",
        "city": request.city,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "travel_days": request.travel_days,
        "transportation": request.transportation,
        "accommodation": request.accommodation,
        "preferences": request.preferences,
        "free_text_input": request.free_text_input or "",
        "attractions_result": "",
        "weather_result": "",
        "hotel_result": "",
        "plan_result": "",
    }

    def generate():
        try:
            for chunk in graph.stream(initial_state):
                # chunk = {node_name: state_update, ...}
                for node_name, state_update in chunk.items():
                    label = NODE_LABELS.get(node_name, node_name)
                    event = {
                        "node": node_name,
                        "label": label,
                    }
                    # 附带当前阶段的中间结果
                    if "attractions_result" in state_update:
                        event["preview"] = state_update["attractions_result"][:200]
                    elif "weather_result" in state_update:
                        event["preview"] = state_update["weather_result"][:200]
                    elif "hotel_result" in state_update:
                        event["preview"] = state_update["hotel_result"][:200]
                    elif "plan_result" in state_update:
                        plan_raw = state_update["plan_result"]
                        try:
                            plan = json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
                            event["done"] = True
                            event["plan"] = plan
                        except json.JSONDecodeError:
                            event["error"] = "Plan JSON parse failed"
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


@app.get("/api/health")
def health():
    """健康检查"""
    return {"status": "ok"}
