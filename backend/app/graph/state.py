"""LangGraph State 定义

State 是贯穿所有节点的共享数据结构。
每个节点返回 dict，LangGraph 自动 merge 回 State。
"""

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class TripPlannerState(TypedDict):
    """旅行规划图的状态

    messages: 使用 add_messages 自动追加消息历史（支持 tool_call 循环）
    其他字段: 请求参数 + 中间结果 + 最终输出
    """

    # ── 对话历史（add_messages 自动累积） ──
    messages: Annotated[list[BaseMessage], add_messages]

    # ── 当前活动的 Agent（用于 tool 执行后路由回正确的 Agent） ──
    current_agent: str

    # ── 请求参数 ──
    city: str
    start_date: str
    end_date: str
    travel_days: int
    transportation: str
    accommodation: str
    preferences: list[str]
    free_text_input: str

    # ── 中间结果（各 Agent 的最终输出） ──
    attractions_result: str
    weather_result: str
    hotel_result: str

    # ── 最终输出 ──
    plan_result: str
