"""LLM服务模块"""

from langchain_deepseek import ChatDeepSeek
from ..config import get_settings

_llm_instance: ChatDeepSeek | None = None


def get_llm() -> ChatDeepSeek:
    """获取LLM实例(单例模式)

    Returns:
        ChatDeepSeek实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()
        _llm_instance = ChatDeepSeek(
            model=settings.llm_model_id,
            api_key=settings.llm_api_key,
            api_base=settings.llm_base_url,
            timeout=settings.llm_timeout,
            max_retries=2,
            extra_body={"thinking": {"type": "disabled"}},
        )
        print(f"✅ LLM服务初始化成功")

    return _llm_instance


def reset_llm() -> None:
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None
