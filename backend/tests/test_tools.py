"""tools 模块测试"""

from langchain_core.tools import BaseTool
from backend.app.tools import ToolManager, tool_manager
from backend.app.tools.base import TaggedTool
from backend.app.tools.amap_tools import (
    amap_text_search,
    amap_around_search,
    amap_weather,
    amap_geocode,
)


class TestTaggedTool:
    def test_tag_sets_tags(self):
        """tag 方法给工具挂载标签"""
        # amap_text_search 已有标签 ["amap", "search"]
        tags = TaggedTool.get_tags(amap_text_search)
        assert "amap" in tags
        assert "search" in tags

    def test_get_tags_untagged(self):
        """未打标签的工具返回空列表"""
        from langchain_core.tools import tool

        @tool
        def dummy(x: str) -> str:
            """test"""
            return x

        assert TaggedTool.get_tags(dummy) == []


class TestToolManager:
    def test_register_and_get(self):
        mgr = ToolManager()
        mgr.register(amap_text_search)
        assert mgr.get("amap_text_search") is amap_text_search
        assert mgr.get("nonexistent") is None

    def test_register_many(self):
        mgr = ToolManager()
        mgr.register_many([amap_text_search, amap_weather])
        assert len(mgr.list_all()) == 2

    def test_get_by_tag(self):
        mgr = ToolManager()
        mgr.register_many([amap_text_search, amap_around_search, amap_weather, amap_geocode])

        amap_tools = mgr.get_by_tag("amap")
        assert len(amap_tools) == 4

        search_tools = mgr.get_by_tag("search")
        assert len(search_tools) == 2  # text_search + around_search

        weather_tools = mgr.get_by_tag("weather")
        assert len(weather_tools) == 1

    def test_list_all_returns_base_tools(self):
        mgr = ToolManager()
        mgr.register(amap_text_search)
        tools = mgr.list_all()
        assert all(isinstance(t, BaseTool) for t in tools)

    def test_tool_names(self):
        mgr = ToolManager()
        mgr.register_many([amap_text_search, amap_weather])
        assert "amap_text_search" in mgr.tool_names
        assert "amap_weather" in mgr.tool_names


class TestGlobalToolManager:
    def test_all_tools_registered(self):
        """全局 tool_manager 已注册 5 个工具"""
        assert len(tool_manager.list_all()) == 5

    def test_all_are_base_tools(self):
        for t in tool_manager.list_all():
            assert isinstance(t, BaseTool), f"{t.name} is not BaseTool"

    def test_tags(self):
        """标签分组正确"""
        assert len(tool_manager.get_by_tag("amap")) == 4
        assert len(tool_manager.get_by_tag("unsplash")) == 1
        assert len(tool_manager.get_by_tag("image")) == 1
        assert len(tool_manager.get_by_tag("search")) == 2
        assert len(tool_manager.get_by_tag("weather")) == 1
        assert len(tool_manager.get_by_tag("geo")) == 1
