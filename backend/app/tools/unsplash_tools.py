"""Unsplash API 图片搜索工具"""

import json
import httpx
from langchain_core.tools import tool
from ..config import get_settings
from .base import TaggedTool


def _get_key() -> str:
    return get_settings().unsplash_access_key


@tool
def unsplash_search_photo(query: str, per_page: int = 5) -> str:
    """Unsplash图片搜索。

    根据关键词搜索高质量风景/城市/美食图片，返回图片URL列表。
    适用于为景点、美食、酒店推荐配图。

    Args:
        query: 搜索关键词，英文效果最佳，如"Beijing Forbidden City"、"West Lake Hangzhou"
        per_page: 返回图片数量，默认5，最大30
    """
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": min(per_page, 30),
        "orientation": "landscape",
    }
    headers = {
        "Accept-Version": "v1",
        "Authorization": f"Client-ID {_get_key()}",
    }

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as e:
        return f"Unsplash请求失败: {e}"

    results = data.get("results", [])
    if not results:
        return f"未找到与'{query}'相关的图片"

    return json.dumps([{
        "id": p.get("id", ""),
        "description": p.get("description") or p.get("alt_description", ""),
        "url_regular": p["urls"]["regular"],  # 1080px 适合展示
        "url_thumb": p["urls"]["thumb"],      # 200px 缩略图
        "photographer": p["user"]["name"],
        "photographer_url": f"https://unsplash.com/@{p['user']['username']}",
    } for p in results], ensure_ascii=False)


TaggedTool.tag(unsplash_search_photo, ["unsplash", "image"])
