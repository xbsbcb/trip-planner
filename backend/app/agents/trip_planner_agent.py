"""LangGraph Agent模块 — 多Agent旅行规划系统

每个Agent对应LangGraph中的一个节点，使用标准的 llm.bind_tools() 机制调用工具，
而非自定义的 [TOOL_CALL:...] 文本解析格式。
"""

from typing import Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool

from ..services.llm_service import get_llm

# ============================================================
# System Prompts — 纯语义描述，不再包含工具调用格式
# 工具调用由 LangChain 的 bind_tools 机制自动处理
# ============================================================

ATTRACTION_PROMPT = """你是景点搜索专家。你的任务是根据用户提供的城市和偏好，调用搜索工具查找合适的景点。

工作流程:
1. 根据用户的偏好标签（如"历史文化"、"自然风光"、"美食"）确定搜索关键词
2. 调用 amap_maps_text_search 工具搜索景点
3. 从搜索结果中筛选最合适的景点，整理成结构化信息返回

返回要求:
- 每个景点包含: 名称、地址、坐标、建议游览时间、描述、类别、门票价格
- 每天推荐 2-3 个景点
- 优先推荐评分高、与用户偏好匹配的景点
"""

WEATHER_PROMPT = """你是天气查询专家。你的任务是根据城市和日期范围查询天气信息。

工作流程:
1. 调用 amap_maps_weather 工具查询目标城市的天气
2. 整理天气数据为结构化格式

返回要求:
- 每天包含: 白天天气、夜间天气、白天温度、夜间温度、风向、风力
- 温度必须为纯数字（不带 °C 等单位）
"""

HOTEL_PROMPT = """你是酒店推荐专家。你的任务是根据城市和已选景点位置推荐合适的酒店。

工作流程:
1. 了解已选景点的位置分布
2. 调用 amap_maps_text_search 工具搜索酒店（关键词: "酒店" 或 "宾馆"）
3. 选择交通便利、性价比高的酒店

返回要求:
- 每个酒店包含: 名称、地址、坐标、价格范围、评分、距景点距离、类型、预估费用
"""

PLANNER_PROMPT = """你是行程规划专家。你的任务是根据景点、天气和酒店信息，生成完整的旅行计划。

工作流程:
1. 综合景点信息、天气信息、酒店信息
2. 按日期合理分配景点（考虑距离、游览时间）
3. 为每天安排早中晚三餐
4. 计算预算

返回要求 — 严格 JSON 格式:
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {"name": "...", "address": "...", "location": {"longitude": 0.0, "latitude": 0.0}, "price_range": "...", "rating": "...", "distance": "...", "type": "...", "estimated_cost": 0},
      "attractions": [{"name": "...", "address": "...", "location": {"longitude": 0.0, "latitude": 0.0}, "visit_duration": 0, "description": "...", "category": "...", "ticket_price": 0}],
      "meals": [{"type": "breakfast", "name": "...", "description": "...", "estimated_cost": 0}, {"type": "lunch", "name": "...", "description": "...", "estimated_cost": 0}, {"type": "dinner", "name": "...", "description": "...", "estimated_cost": 0}]
    }
  ],
  "weather_info": [{"date": "YYYY-MM-DD", "day_weather": "...", "night_weather": "...", "day_temp": 0, "night_temp": 0, "wind_direction": "...", "wind_power": "..."}],
  "overall_suggestions": "总体建议",
  "budget": {"total_attractions": 0, "total_hotels": 0, "total_meals": 0, "total_transportation": 0, "total": 0}
}

约束:
- weather_info 必须覆盖每一天
- 温度是纯数字
- 每天 2-3 个景点，必须包含早中晚三餐
- 考虑景点间距离和游览时间
"""


# ============================================================
# Agent 节点工厂
# 每个函数返回一个 LangGraph 可用的节点函数
# 节点函数签名: (state: dict) -> dict (StateGraph 的 update)
# ============================================================

def _build_messages(system_prompt: str, user_message: str) -> list:
    """构建 LLM 调用的消息列表"""
    return [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]


def create_attraction_node(tools: list[BaseTool]):
    """创建景点搜索Agent节点

    Args:
        tools: LangChain Tool 列表，应包含 amap_maps_text_search 工具

    Returns:
        LangGraph 节点函数
    """
    llm = get_llm().bind_tools(tools)

    def attraction_node(state: dict) -> dict:
        city = state.get("city", "")
        preferences = state.get("preferences", [])
        extra = state.get("free_text_input", "")

        user_msg = f"搜索 {city} 的景点。偏好: {', '.join(preferences) if preferences else '无特定偏好'}。{extra}".strip()
        messages = _build_messages(ATTRACTION_PROMPT, user_msg)

        response = llm.invoke(messages)
        return {
            "messages": [response],
            "attractions_raw": response,
        }

    return attraction_node


def create_weather_node(tools: list[BaseTool]):
    """创建天气查询Agent节点

    Args:
        tools: LangChain Tool 列表，应包含 amap_maps_weather 工具

    Returns:
        LangGraph 节点函数
    """
    llm = get_llm().bind_tools(tools)

    def weather_node(state: dict) -> dict:
        city = state.get("city", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        user_msg = f"查询 {city} 的天气，日期范围: {start_date} 至 {end_date}"
        messages = _build_messages(WEATHER_PROMPT, user_msg)

        response = llm.invoke(messages)
        return {
            "messages": [response],
            "weather_raw": response,
        }

    return weather_node


def create_hotel_node(tools: list[BaseTool]):
    """创建酒店推荐Agent节点

    Args:
        tools: LangChain Tool 列表，应包含 amap_maps_text_search 工具

    Returns:
        LangGraph 节点函数
    """
    llm = get_llm().bind_tools(tools)

    def hotel_node(state: dict) -> dict:
        city = state.get("city", "")
        accommodation = state.get("accommodation", "经济型酒店")

        user_msg = f"在 {city} 搜索酒店，住宿偏好: {accommodation}"
        messages = _build_messages(HOTEL_PROMPT, user_msg)

        response = llm.invoke(messages)
        return {
            "messages": [response],
            "hotel_raw": response,
        }

    return hotel_node


def create_planner_node():
    """创建行程规划Agent节点（不需要工具，纯规划）

    注意: Planner 不绑定工具，它接收前几个 Agent 收集的数据，输出结构化旅行计划。

    Returns:
        LangGraph 节点函数
    """
    llm = get_llm()

    def planner_node(state: dict) -> dict:
        city = state.get("city", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")
        travel_days = state.get("travel_days", 1)
        transportation = state.get("transportation", "")
        accommodation = state.get("accommodation", "")

        # 收集上游节点的结果
        attractions_data = state.get("attractions_result", "暂无景点数据")
        weather_data = state.get("weather_result", "暂无天气数据")
        hotel_data = state.get("hotel_result", "暂无酒店数据")

        user_msg = (
            f"请根据以下信息规划旅行:\n"
            f"城市: {city}\n"
            f"日期: {start_date} 至 {end_date}，共 {travel_days} 天\n"
            f"交通: {transportation}\n"
            f"住宿偏好: {accommodation}\n\n"
            f"=== 景点信息 ===\n{attractions_data}\n\n"
            f"=== 天气信息 ===\n{weather_data}\n\n"
            f"=== 酒店信息 ===\n{hotel_data}\n"
        )
        messages = _build_messages(PLANNER_PROMPT, user_msg)

        response = llm.invoke(messages)
        return {
            "messages": [response],
            "plan_raw": response,
        }

    return planner_node
