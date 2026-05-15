# LangGraph 知识点与解决方案笔记

## 1. `@tool` 装饰器 vs `bind_tools()`

### 概念区分

| | `@tool` | `bind_tools(tools)` |
|---|---|---|
| **作用** | **定义**工具——把普通函数变为 LangChain Tool | **告知** LLM 有哪些工具可用 |
| **执行者** | 开发者实现工具函数体 | LangChain 自动将签名传给 LLM |
| **位置** | `tools/` 模块 | Agent 节点内部 |

### 工作流程

```
@tool 定义                     bind_tools 告知               LLM 决策
┌─────────────────┐          ┌──────────────────┐        ┌──────────────┐
│ @tool            │  传入    │ llm.bind_tools() │  schema│ LLM 推理      │
│ def search(...): │ ──────► │ → tools 签名列表  │ ─────► │ → 决定调不调  │
│   httpx.get(...) │          └──────────────────┘        │ → 生成参数    │
└─────────────────┘                                       └──────┬───────┘
                                                            AIMessage
                                                            .tool_calls
```

### 关键认知

- `@tool` 不剥夺 Agent 决策权，**恰恰相反**——没有工具 Agent 只能输出文本，有工具才能执行实际操作
- 调不调、何时调、传什么参数，全是 LLM 自主决策

---

## 2. 工具 Schema 自动生成

### 原理

LangChain 从 `@tool` 的函数签名 + docstring 自动生成 LLM 可读的 JSON Schema：

```python
@tool
def amap_text_search(keywords: str, city: str, citylimit: bool = True) -> str:
    """高德地图POI关键词搜索。根据城市和关键词搜索兴趣点。"""
```

自动生成：

```json
{
  "name": "amap_text_search",
  "description": "高德地图POI关键词搜索。根据城市和关键词搜索兴趣点。",
  "parameters": {
    "type": "object",
    "properties": {
      "keywords": {"type": "string", "description": "搜索关键词，如\"故宫\"、\"酒店\""},
      "city": {"type": "string", "description": "城市名称，如\"北京\"、\"上海\""},
      "citylimit": {"type": "boolean", "default": true}
    },
    "required": ["keywords", "city"]
  }
}
```

### 规则

- **类型注解** → `properties.type`
- **docstring 首行** → `description`
- **`Args:` 段** → 每个参数的 `description`
- **返回值** 必须是 `str` —— LLM 只读文本
- **错误处理**：不抛异常，return 错误信息字符串，LLM 可据此重试或换策略

---

## 3. ToolManager 模式

### 问题

多 API、多工具时，手动逐个 import 和注册导致代码冗长。

### 解决方案

```python
class ToolManager:
    _tools: dict[str, BaseTool]

    def register(tool)       # 注册
    def register_many(list)  # 批量注册
    def list_all()           # → 全部工具
    def get_by_tag(tag)      # → 按标签筛选
    def get(name)            # → 按名称获取
```

### 使用

```python
# Agent 获取工具
tools = tool_manager.list_all()           # 全部
tools = tool_manager.get_by_tag("amap")   # 按来源
tools = tool_manager.get_by_tag("search") # 按功能
```

### 新增工具步骤（2 步）

1. 在 `*.py` 添加 `@tool` 函数
2. 在 `ToolManager.register_many([...])` 加一行

---

## 4. TaggedTool — 工具分类标签

### 问题

LangChain `@tool` 不支持自定义元数据，无法按来源/功能分组。

### 解决方案（补丁）

```python
class TaggedTool:
    @staticmethod
    def tag(tool, tags: list[str]):
        tool._tags = tags  # 挂载标签属性

TaggedTool.tag(amap_text_search, ["amap", "search"])
```

ToolManager 的 `get_by_tag()` 依赖此标签。未来 langchain 原生支持后直接删掉此类。

---

## 5. LangGraph StateGraph 架构

### 核心概念

```
StateGraph
├── State        : 贯穿各节点的共享字典
├── Node         : 处理函数 (state → state_update)
├── Edge         : 节点间连接
└── ConditionalEdge : 条件分支（通常判断是否有 tool_call）
```

### 状态流转

```
用户请求 → [Node: Agent] → 有 tool_call?
                │                 │
                ↓ 否              ↓ 是
           [Node: Planner]   [ToolNode: 执行工具]
                │                 │
                ↓                 ↓
           [END]            [Node: Agent] ← 工具结果
```

### 节点函数签名

```python
def agent_node(state: dict) -> dict:
    """返回 dict，合并到 state 中"""
    response = llm.invoke(messages)
    return {"messages": [response]}
```

---

## 6. Agent 节点工厂模式

### 问题

多个 Agent 节点结构相似但系统提示和工具不同，避免重复代码。

### 模式

```python
def create_attraction_node(tools: list[BaseTool]):
    """工厂函数：返回配置好的节点函数"""
    llm = get_llm().bind_tools(tools)  # 闭包捕获

    def node(state: dict) -> dict:
        # 从 state 提取输入
        city = state.get("city", "")
        # 构建消息 + 调用 LLM
        response = llm.invoke(messages)
        return {"messages": [response], "attractions_raw": response}

    return node  # 返回节点函数
```

### 优势

- 创建节点 = 一行调用 `create_xxx_node(tools)`
- 工具由外部注入，解耦

---

## 7. MCP vs 本地工具

### 决策矩阵

| 维度 | 本地 `@tool` + httpx | MCP Server |
|------|---------------------|------------|
| 适用场景 | 单一项目 | 多项目共享同一工具集 |
| 运行时依赖 | Python only | Python + Node.js + npm 包 |
| 进程管理 | 无 | 需管理子进程启停 |
| 新增工具 | 写一个 `@tool` 函数 | 需同时改 server 和 client |
| 开销 | 直接 HTTP 调用 | stdio/SSE 通信 |

### 结论

- 工具只给当前项目用 → 本地 `@tool`
- 工具要给多个项目/团队共享 → MCP Server
- **不要**把 MCP 当工具基类——MCP 是跨进程传输协议，不是管理框架

---

## 8. 配置管理：`os.getenv` vs `pydantic-settings`

### 对比

| | `os.getenv` | `pydantic-settings` |
|---|---|---|
| 类型校验 | 无 | 启动时自动校验 |
| 类型转换 | 手动 `int()` | 自动 |
| 缺失检测 | 运行时 None 崩溃 | 启动即报错 |
| 集中管理 | 分散各文件 | 一个 Settings 类 |
| 测试覆盖 | 需改环境变量 | `Settings(key="test")` |

### 推荐写法

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env"}
    llm_api_key: str          # 必填，缺失启动报错
    llm_timeout: int = 60     # 有默认值 + 自动类型转换
```

---

## 9. 项目分层：自底向上构建顺序

```
1. config.py      → 配置集中管理
2. models/        → Pydantic 数据模型
3. tools/         → @tool 工具层
4. services/      → LLM 单例服务
5. agents/        → Agent 节点函数
6. graph/         → StateGraph 编排
7. server.py      → FastAPI 对外暴露
```

每层只依赖下层，上层构建时下层已就绪。
