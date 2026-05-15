"""工具管理模块

ToolManager 提供工具的统一注册、查询和分组导出。
Agent 通过 ToolManager.list_all() 或 .get_by_tag() 获取工具列表，
无需手动逐个 import。
"""

from langchain_core.tools import BaseTool

from .amap_tools import (
    amap_text_search,
    amap_around_search,
    amap_weather,
    amap_geocode,
)
from .base import TaggedTool


class ToolManager:
    """工具管理器 — 集中注册、查询、导出 LangChain Tool。

    使用方式:
        mgr = ToolManager()
        mgr.register(amap_text_search)
        tools = mgr.list_all()
        amap_tools = mgr.get_by_tag("amap")
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool

    def register_many(self, tools: list[BaseTool]) -> None:
        """批量注册"""
        for t in tools:
            self.register(t)

    def get(self, name: str) -> BaseTool | None:
        """按名称获取工具"""
        return self._tools.get(name)

    def get_by_tag(self, tag: str) -> list[BaseTool]:
        """按标签筛选工具"""
        return [t for t in self._tools.values() if tag in TaggedTool.get_tags(t)]

    def list_all(self) -> list[BaseTool]:
        """返回全部工具列表"""
        return list(self._tools.values())

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


# ============================================================
# 全局实例 — 导入高德工具并自动注册
# ============================================================

tool_manager = ToolManager()
tool_manager.register_many([
    amap_text_search,
    amap_around_search,
    amap_weather,
    amap_geocode,
])

# 快捷导出
ALL_TOOLS = tool_manager.list_all()
get_tool = tool_manager.get
get_tools_by_tag = tool_manager.get_by_tag
