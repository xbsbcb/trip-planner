"""services/trip_service 模块测试"""

import json
import pytest
from backend.app.models.schemas import TripRequest, TripPlanResponse
from backend.app.services.trip_service import build_state, parse_plan, NODE_LABELS


class TestBuildState:
    def test_builds_state_from_request(self):
        req = TripRequest(
            city="杭州",
            start_date="2025-06-01",
            end_date="2025-06-03",
            travel_days=3,
            transportation="公共交通",
            accommodation="经济型酒店",
            preferences=["自然风光", "美食"],
            free_text_input="多安排一些山",
        )
        state = build_state(req)
        assert state["city"] == "杭州"
        assert state["travel_days"] == 3
        assert state["preferences"] == ["自然风光", "美食"]
        assert state["free_text_input"] == "多安排一些山"
        assert state["messages"] == []
        assert state["current_agent"] == ""

    def test_defaults(self):
        req = TripRequest(
            city="上海",
            start_date="2025-06-01",
            end_date="2025-06-02",
            travel_days=2,
            transportation="地铁",
            accommodation="酒店",
        )
        state = build_state(req)
        assert state["preferences"] == []
        assert state["free_text_input"] == ""


class TestParsePlan:
    def test_parse_valid_json(self):
        plan_json = json.dumps({"city": "北京", "days": []})
        state = {"plan_result": plan_json}
        result = parse_plan(state)
        assert result["city"] == "北京"

    def test_parse_dict(self):
        plan_dict = {"city": "北京", "days": []}
        state = {"plan_result": plan_dict}
        result = parse_plan(state)
        assert result["city"] == "北京"

    def test_parse_empty_raises(self):
        with pytest.raises(ValueError, match="规划结果为空"):
            parse_plan({"plan_result": ""})

    def test_parse_invalid_json_raises(self):
        with pytest.raises(ValueError, match="格式错误"):
            parse_plan({"plan_result": "not json"})


class TestNodeLabels:
    def test_all_nodes_have_labels(self):
        expected = [
            "attraction_agent",
            "weather_agent",
            "hotel_agent",
            "planner_agent",
            "tools_node",
            "attraction_done",
            "weather_done",
            "hotel_done",
            "planner_done",
        ]
        for node in expected:
            assert node in NODE_LABELS, f"Missing label for {node}"
