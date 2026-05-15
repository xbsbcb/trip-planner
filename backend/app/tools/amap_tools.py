"""高德地图 API 工具集

每个函数用 @tool 装饰器定义为 LangChain Tool。
工具函数内部负责: 请求构造 → API 调用 → JSON 解析 → 字段裁剪。
上层 Agent 无需了解 API 细节。
"""

import json
import httpx
from langchain_core.tools import tool

from ..config import get_settings
from .base import TaggedTool


def _get_key() -> str:
    return get_settings().amap_api_key


# ============================================================
# POI 搜索
# ============================================================


@tool
def amap_text_search(keywords: str, city: str, citylimit: bool = True) -> str:
    """高德地图POI关键词搜索。

    根据城市和关键词搜索景点、酒店、餐厅等兴趣点（POI），
    返回名称、地址、坐标、评分等信息。

    Args:
        keywords: 搜索关键词，如"故宫"、"历史文化"、"酒店"、"川菜"
        city: 城市名称，如"北京"、"上海"
        citylimit: 是否仅返回城市范围内的结果，默认True
    """
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": _get_key(),
        "keywords": keywords,
        "city": city,
        "citylimit": str(citylimit).lower(),
        "offset": 20,
        "extensions": "all",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as e:
        return f"网络请求失败: {e}"

    if data.get("status") != "1":
        return f"搜索失败: {data.get('info', '未知错误')}"

    pois = data.get("pois", [])
    if not pois:
        return f"在{city}未找到与'{keywords}'相关的结果"

    return json.dumps([{
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "type": p.get("type", ""),
        "address": p.get("address", ""),
        "location": p.get("location", ""),
        "tel": p.get("tel", ""),
        "rating": (p.get("biz_ext") or {}).get("rating", ""),
    } for p in pois], ensure_ascii=False)


# ============================================================
# 周边搜索
# ============================================================


@tool
def amap_around_search(
    location: str, keywords: str = "", radius: int = 3000
) -> str:
    """高德地图周边搜索。

    以指定坐标为中心，搜索周边半径内的POI。
    常用于搜索景点附近的酒店、餐厅等。

    Args:
        location: 中心点坐标，格式"经度,纬度"，如"116.397128,39.916527"
        keywords: 搜索关键词，如"酒店"、"餐厅"，留空则返回周边所有POI
        radius: 搜索半径(米)，默认3000
    """
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": _get_key(),
        "location": location,
        "keywords": keywords,
        "radius": radius,
        "offset": 20,
        "extensions": "all",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as e:
        return f"网络请求失败: {e}"

    if data.get("status") != "1":
        return f"周边搜索失败: {data.get('info', '未知错误')}"

    pois = data.get("pois", [])
    return json.dumps([{
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "type": p.get("type", ""),
        "address": p.get("address", ""),
        "location": p.get("location", ""),
        "distance": p.get("distance", ""),
        "rating": (p.get("biz_ext") or {}).get("rating", ""),
    } for p in pois], ensure_ascii=False)


# ============================================================
# 天气查询
# ============================================================


@tool
def amap_weather(city: str) -> str:
    """高德天气查询。

    查询指定城市未来几天的天气预报，返回每天的天天气、温度、风向风力。

    Args:
        city: 城市名称，如"北京"、"杭州"
    """
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": _get_key(),
        "city": city,
        "extensions": "all",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as e:
        return f"网络请求失败: {e}"

    if data.get("status") != "1":
        return f"天气查询失败: {data.get('info', '未知错误')}"

    forecasts = data.get("forecasts", [])
    if not forecasts:
        return f"未找到{city}的天气数据"

    return json.dumps([{
        "date": c.get("date", ""),
        "day_weather": c.get("dayweather", ""),
        "night_weather": c.get("nightweather", ""),
        "day_temp": c.get("daytemp", ""),
        "night_temp": c.get("nighttemp", ""),
        "wind_direction": c.get("daywind", ""),
        "wind_power": c.get("daypower", ""),
    } for c in forecasts[0].get("casts", [])], ensure_ascii=False)


# ============================================================
# 地理编码
# ============================================================


@tool
def amap_geocode(address: str, city: str = "") -> str:
    """高德地理编码。

    将地址转换为经纬度坐标，或查询城市编码(adcode)。

    Args:
        address: 地址名称，如"北京市朝阳区"、"天安门"
        city: 可选的城市限定
    """
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {"key": _get_key(), "address": address}
    if city:
        params["city"] = city
    try:
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as e:
        return f"网络请求失败: {e}"

    if data.get("status") != "1":
        return f"地理编码失败: {data.get('info', '未知错误')}"

    geocodes = data.get("geocodes", [])
    if not geocodes:
        return f"未找到'{address}'的坐标"

    return json.dumps([{
        "location": g.get("location", ""),
        "adcode": g.get("adcode", ""),
        "formatted_address": g.get("formatted_address", ""),
    } for g in geocodes], ensure_ascii=False)


# ============================================================
# 注册标签 — 由 ToolManager 按标签分组管理
# ============================================================

TaggedTool.tag(amap_text_search, ["amap", "search"])
TaggedTool.tag(amap_around_search, ["amap", "search"])
TaggedTool.tag(amap_weather, ["amap", "weather"])
TaggedTool.tag(amap_geocode, ["amap", "geo"])
