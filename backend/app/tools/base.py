"""工具基类 — 扩展 LangChain BaseTool，增加标签分组能力"""

from langchain_core.tools import BaseTool


class TaggedTool:
    """混入类：为 Tool 添加标签属性，支持 ToolManager 按标签筛选。

    使用方式:
        @tool
        def my_tool(...): ...

        my_tool = my_tool  # 已是 BaseTool 实例
        TaggedTool.tag(my_tool, ["amap", "search"])
    """

    @staticmethod
    def tag(tool: BaseTool, tags: list[str]) -> BaseTool:
        tool._tags = tags  # type: ignore
        return tool

    @staticmethod
    def get_tags(tool: BaseTool) -> list[str]:
        return getattr(tool, "_tags", [])
