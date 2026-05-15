"""LangGraph 旅行规划图

多 Agent 顺序协作:
  Attraction Agent → Weather Agent → Hotel Agent → Planner Agent → END

每个 Agent 内部是 ReAct 循环: Agent ⇄ ToolNode
- Agent 调用 LLM，LLM 决定是否调用工具
- 有 tool_call → ToolNode 执行 → 返回 Agent 继续
- 无 tool_call → 存储结果 → 下一个 Agent

路由逻辑:
  1. Agent 节点 → tools_condition:
     - 有 tool_calls → "tools_node"
     - 无 tool_calls → "transition" → 下一个 Agent
  2. tools_node → route_after_tools:
     - 根据 state["current_agent"] 返回对应 Agent 节点
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import TripPlannerState
from ..agents.trip_planner_agent import (
    ATTRACTION_PROMPT,
    WEATHER_PROMPT,
    HOTEL_PROMPT,
    PLANNER_PROMPT,
)
from ..services.llm_service import get_llm
from ..tools import tool_manager


# ============================================================
# Agent 节点工厂
# ============================================================

def _make_agent_node(
    system_prompt: str,
    tools: list,
    agent_name: str,
    result_key: str,
    build_user_msg,
):
    """创建 Agent 节点。

    节点职责:
    1. 首次进入：用 state 参数构建 HumanMessage
    2. tool 执行后再次进入：基于累积 messages 继续对话
    3. 最终无 tool_call 时：结果由 transition 节点存入 state
    """
    llm = get_llm().bind_tools(tools) if tools else get_llm()

    def node(state: TripPlannerState) -> dict:
        messages = state.get("messages", [])

        # 判断是否为本 Agent 的首次调用：
        # messages 中没有当前 agent 的 SystemPrompt → 首次，建初始消息
        sys_in_msgs = any(
            isinstance(m, SystemMessage) and m.content == system_prompt
            for m in messages
        )
        if not sys_in_msgs:
            user_msg = build_user_msg(state)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_msg)]

        response = llm.invoke(messages)
        return {
            # 首次调用时同步返回 Sys+Human+AI，确保后续 tool 循环有完整上下文
            "messages": messages + [response] if not sys_in_msgs else [response],
            "current_agent": agent_name,
        }

    return node


# ============================================================
# 构建用户消息的辅助函数
# ============================================================

def _attraction_user_msg(state: TripPlannerState) -> str:
    prefs = state.get("preferences", [])
    extra = state.get("free_text_input", "")
    return (
        f"搜索 {state['city']} 的景点。"
        f"偏好: {', '.join(prefs) if prefs else '无特定偏好'}。"
        f"{extra}"
    ).strip()

def _weather_user_msg(state: TripPlannerState) -> str:
    return f"查询 {state['city']} 的天气，日期范围: {state['start_date']} 至 {state['end_date']}"

def _hotel_user_msg(state: TripPlannerState) -> str:
    acc = state.get("accommodation", "经济型酒店")
    return f"在 {state['city']} 搜索酒店，住宿偏好: {acc}"

def _planner_user_msg(state: TripPlannerState) -> str:
    return (
        f"请根据以下信息规划旅行:\n"
        f"城市: {state['city']}\n"
        f"日期: {state['start_date']} 至 {state['end_date']}，共 {state['travel_days']} 天\n"
        f"交通: {state.get('transportation', '')}\n"
        f"住宿偏好: {state.get('accommodation', '')}\n\n"
        f"=== 景点信息 ===\n{state.get('attractions_result', '暂无景点数据')}\n\n"
        f"=== 天气信息 ===\n{state.get('weather_result', '暂无天气数据')}\n\n"
        f"=== 酒店信息 ===\n{state.get('hotel_result', '暂无酒店数据')}\n"
    )


# ============================================================
# Transition 节点 — Agent 完成时存储结果并清空 messages
# ============================================================

def _make_transition(result_key: str):
    """创建过渡节点: 将当前 Agent 的输出存入 state[result_key]，
    然后清空 messages 为下一个 Agent 做准备。
    """

    def transition(state: TripPlannerState) -> dict:
        messages = state["messages"]
        # 取最后一条 AIMessage（不含 tool_calls）的内容作为结果
        result = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) and not m.tool_calls:
                result = m.content
                break

        return {
            result_key: result,
            "messages": [],  # 清空消息，为下一个 Agent 提供干净上下文
        }

    return transition


# ============================================================
# 路由函数
# ============================================================

def _route_after_tools(state: TripPlannerState) -> str:
    """Tool 执行后的统一路由: 根据 current_agent 回到调用者"""
    agent = state.get("current_agent", "")
    return f"{agent}_agent"


def _make_route_after_agent(
    tools_node_name: str,
    transition_node_name: str,
):
    """Agent 节点后的条件路由。

    基于 LangGraph 的 tools_condition:
    - 最后一条消息有 tool_calls → tools_node
    - 无 tool_calls → transition_node（存储结果，去往下一 Agent）
    """

    def route(state: TripPlannerState) -> str:
        messages = state["messages"]
        if not messages:
            return transition_node_name
        last = messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return tools_node_name
        return transition_node_name

    return route


# ============================================================
# 构建 Graph
# ============================================================

def build_graph() -> StateGraph:
    """构建旅行规划 StateGraph

    Agent 执行顺序:
      attraction → weather → hotel → planner → END

    每个 Agent 内部:
      Agent ⇄ ToolNode (ReAct 循环)
    """

    all_tools = tool_manager.list_all()
    search_tools = tool_manager.get_by_tag("search")   # text_search + around_search
    weather_tools = tool_manager.get_by_tag("weather")  # weather
    # hotel uses search_tools too

    builder = StateGraph(TripPlannerState)

    # ── Agent 节点 ──
    builder.add_node(
        "attraction_agent",
        _make_agent_node(
            ATTRACTION_PROMPT, search_tools, "attraction",
            "attractions_result", _attraction_user_msg,
        ),
    )
    builder.add_node(
        "weather_agent",
        _make_agent_node(
            WEATHER_PROMPT, weather_tools, "weather",
            "weather_result", _weather_user_msg,
        ),
    )
    builder.add_node(
        "hotel_agent",
        _make_agent_node(
            HOTEL_PROMPT, search_tools, "hotel",
            "hotel_result", _hotel_user_msg,
        ),
    )
    builder.add_node(
        "planner_agent",
        _make_agent_node(
            PLANNER_PROMPT, [], "planner",
            "plan_result", _planner_user_msg,
        ),
    )

    # ── ToolNode（共享，LangGraph 根据 state["current_agent"] 路由回正确 Agent） ──
    builder.add_node("tools_node", ToolNode(all_tools))

    # ── Transition 节点（Agent 完成后的清理 + 结果存储） ──
    builder.add_node("attraction_done", _make_transition("attractions_result"))
    builder.add_node("weather_done", _make_transition("weather_result"))
    builder.add_node("hotel_done", _make_transition("hotel_result"))
    builder.add_node("planner_done", _make_transition("plan_result"))

    # ── 边 ──

    # Entry
    builder.add_edge(START, "attraction_agent")

    # 每个 Agent 的条件路由: 有 tool_call → tools_node, 无 → done
    builder.add_conditional_edges(
        "attraction_agent",
        _make_route_after_agent("tools_node", "attraction_done"),
        {"tools_node": "tools_node", "attraction_done": "attraction_done"},
    )
    builder.add_conditional_edges(
        "weather_agent",
        _make_route_after_agent("tools_node", "weather_done"),
        {"tools_node": "tools_node", "weather_done": "weather_done"},
    )
    builder.add_conditional_edges(
        "hotel_agent",
        _make_route_after_agent("tools_node", "hotel_done"),
        {"tools_node": "tools_node", "hotel_done": "hotel_done"},
    )

    # tools_node 的路由: 根据 current_agent 回到调用者
    # 一个节点只能有一条条件边，合并三个 Agent 的回退路由
    builder.add_conditional_edges(
        "tools_node",
        _route_after_tools,
        {
            "attraction_agent": "attraction_agent",
            "weather_agent": "weather_agent",
            "hotel_agent": "hotel_agent",
        },
    )

    # done → 下一个 Agent
    builder.add_edge("attraction_done", "weather_agent")
    builder.add_edge("weather_done", "hotel_agent")
    builder.add_edge("hotel_done", "planner_agent")

    # Planner → done → END（Planner 不需要工具，直接过渡）
    builder.add_edge("planner_agent", "planner_done")
    builder.add_edge("planner_done", END)

    return builder.compile()


# ============================================================
# 便捷入口
# ============================================================

def run_trip_planner(
    city: str,
    start_date: str,
    end_date: str,
    travel_days: int,
    transportation: str = "公共交通",
    accommodation: str = "经济型酒店",
    preferences: list[str] | None = None,
    free_text_input: str = "",
) -> dict:
    """运行旅行规划图

    Args:
        city: 目的地城市
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        travel_days: 旅行天数
        transportation: 交通方式
        accommodation: 住宿偏好
        preferences: 偏好标签列表
        free_text_input: 额外要求

    Returns:
        最终 State dict，包含 plan_result 等字段
    """
    app = build_graph()

    initial_state: TripPlannerState = {
        "messages": [],
        "current_agent": "",
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "travel_days": travel_days,
        "transportation": transportation,
        "accommodation": accommodation,
        "preferences": preferences or [],
        "free_text_input": free_text_input,
        "attractions_result": "",
        "weather_result": "",
        "hotel_result": "",
        "plan_result": "",
    }

    return app.invoke(initial_state)
