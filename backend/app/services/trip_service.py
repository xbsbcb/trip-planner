"""旅行规划服务层

位于 API 路由层和 Agent 层之间：
  server.py → trip_service.py → graph

职责:
  1. 构建 Graph 初始状态
  2. 执行 Graph（同步 / 流式）
  3. 解析 Planner 输出的 JSON 为结构化数据
"""

import json
from ..models.schemas import TripRequest, TripPlanResponse
from ..graph.trip_planner_graph import build_graph, TripPlannerState


# ============================================================
# 节点名 → 前端展示标签
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


# ============================================================
# 内部辅助
# ============================================================

def build_state(request: TripRequest) -> TripPlannerState:
    """从请求构建 Graph 初始状态"""
    return {
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


def parse_plan(state: dict) -> dict:
    """从最终 state 中解析 Planner 输出的 JSON"""
    plan_raw = state.get("plan_result", "")
    if not plan_raw:
        raise ValueError("规划结果为空")
    try:
        return json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
    except json.JSONDecodeError:
        raise ValueError("旅行计划格式错误")


# ============================================================
# 公共接口
# ============================================================

def execute_plan(request: TripRequest) -> TripPlanResponse:
    """同步执行旅行规划"""
    graph = build_graph()
    state = build_state(request)

    final_state = graph.invoke(state)
    plan_data = parse_plan(final_state)

    return TripPlanResponse(success=True, message="规划完成", data=plan_data)


def stream_plan(request: TripRequest):
    """流式执行旅行规划，返回 SSE 事件生成器

    每完成一个节点，yield 一条 `data: {json}\n\n`
    最后一条包含 `done: true` 和完整 `plan`
    """
    graph = build_graph()
    state = build_state(request)

    def generate():
        try:
            for chunk in graph.stream(state):
                for node_name, update in chunk.items():
                    label = NODE_LABELS.get(node_name, node_name)
                    event = {"node": node_name, "label": label}

                    if "attractions_result" in update:
                        event["preview"] = update["attractions_result"][:200]
                    elif "weather_result" in update:
                        event["preview"] = update["weather_result"][:200]
                    elif "hotel_result" in update:
                        event["preview"] = update["hotel_result"][:200]
                    elif "plan_result" in update:
                        try:
                            plan = parse_plan(update)
                            event["done"] = True
                            event["plan"] = plan
                        except ValueError as e:
                            event["error"] = str(e)

                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return generate()
