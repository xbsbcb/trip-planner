"""models/schemas 模块测试"""

import pytest
from pydantic import ValidationError
from backend.app.models.schemas import (
    TripRequest,
    TripPlan,
    TripPlanResponse,
    Location,
    Attraction,
    Hotel,
    WeatherInfo,
    Budget,
    DayPlan,
    Meal,
)


class TestTripRequest:
    def test_valid_minimal(self):
        """最少必填字段"""
        r = TripRequest(
            city="北京",
            start_date="2025-06-01",
            end_date="2025-06-03",
            travel_days=3,
            transportation="地铁",
            accommodation="酒店",
        )
        assert r.city == "北京"
        assert r.preferences == []

    def test_valid_full(self):
        """全部字段"""
        r = TripRequest(
            city="北京",
            start_date="2025-06-01",
            end_date="2025-06-03",
            travel_days=3,
            transportation="地铁",
            accommodation="酒店",
            preferences=["历史文化", "美食"],
            free_text_input="想去故宫",
        )
        assert len(r.preferences) == 2
        assert r.free_text_input == "想去故宫"

    def test_travel_days_range(self):
        """旅行天数校验"""
        with pytest.raises(ValidationError):
            TripRequest(
                city="北京",
                start_date="2025-06-01",
                end_date="2025-06-03",
                travel_days=0,  # 小于最小值 1
                transportation="地铁",
                accommodation="酒店",
            )


class TestWeatherInfo:
    def test_parse_temperature_string(self):
        """温度字符串解析——去除 °C"""
        w = WeatherInfo(
            date="2025-06-01",
            day_temp="25℃",
            night_temp="15°C",
        )
        assert w.day_temp == 25
        assert w.night_temp == 15

    def test_parse_temperature_int(self):
        """温度已是整数"""
        w = WeatherInfo(
            date="2025-06-01",
            day_temp=30,
            night_temp=20,
        )
        assert w.day_temp == 30
        assert isinstance(w.day_temp, int)


class TestTripPlanResponse:
    def test_success(self):
        resp = TripPlanResponse(success=True, message="ok")
        assert resp.success is True
        assert resp.data is None

    def test_with_data(self):
        plan = TripPlan(
            city="北京",
            start_date="2025-06-01",
            end_date="2025-06-02",
            days=[],
            overall_suggestions="玩得开心",
        )
        resp = TripPlanResponse(success=True, message="ok", data=plan)
        assert resp.data.city == "北京"


class TestLocation:
    def test_valid(self):
        loc = Location(longitude=116.397, latitude=39.916)
        assert loc.longitude == 116.397
