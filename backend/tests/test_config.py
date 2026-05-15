"""config 模块测试"""

import os
import pytest
from backend.app.config import Settings, get_settings, reset_settings


class TestSettings:
    def test_defaults(self):
        """默认值"""
        s = Settings(
            llm_api_key="sk-test",
            amap_api_key="amap-test",
            _env_file=None,
        )
        assert s.llm_model_id == "deepseek-v4-pro"
        assert s.llm_timeout == 60
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.log_level == "INFO"

    def test_type_conversion(self):
        """环境变量字符串自动转类型"""
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("LLM_TIMEOUT", "120")
            mp.setenv("PORT", "9000")
            s = Settings(
                llm_api_key="sk-test",
                amap_api_key="amap-test",
                _env_file=None,
            )
            assert isinstance(s.llm_timeout, int)
            assert isinstance(s.port, int)

    def test_missing_required_fails(self):
        """必填字段缺失应报错"""
        with pytest.raises(Exception):
            Settings(_env_file=None)  # 缺少 llm_api_key, amap_api_key

    def test_extra_fields_ignored(self):
        """.env 中未声明字段被忽略"""
        s = Settings(
            llm_api_key="sk-test",
            amap_api_key="amap-test",
            unsplash_access_key="unsplash-key",
            _env_file=None,
        )
        assert s.unsplash_access_key == "unsplash-key"

    def test_get_settings_singleton(self):
        """get_settings 返回单例"""
        reset_settings()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_reset_settings(self):
        """重置后获取新实例"""
        reset_settings()
        s1 = get_settings()
        reset_settings()
        s2 = get_settings()
        assert s1 is not s2
