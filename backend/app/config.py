"""应用配置模块 — 基于 pydantic-settings 的集中配置管理

所有环境变量在此定义、校验，其他模块通过 get_settings() 获取，
不再直接使用 os.getenv()。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 忽略 .env 中未声明的字段（如 Unsplash）
    }

    # LLM
    llm_model_id: str = "deepseek-v4-pro"
    llm_api_key: str
    llm_base_url: str = "https://api.deepseek.com"
    llm_timeout: int = 60

    # 高德地图
    amap_api_key: str
    amap_js_api_key: str = ""

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # 日志
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """重置配置（测试用）"""
    global _settings
    _settings = None
