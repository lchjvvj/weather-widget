"""
天气数据获取模块
================
负责从 wttr.in API 获取实时天气和预报数据
支持多城市并发请求、自动重试、数据缓存
"""

import json
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable

# ============================================================
# 天气图标映射表
# ============================================================
WEATHER_ICONS: Dict[str, str] = {
    # 晴
    "sunny": "☀️",
    "clear": "🌙",
    # 多云
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    # 雾霾
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌫️",
    "smoke": "🌫️",
    "smoky haze": "🌫️",
    # 雨
    "patchy rain nearby": "🌦️",
    "patchy light drizzle": "🌦️",
    "light drizzle": "🌦️",
    "light rain shower": "🌦️",
    "light rain": "🌦️",
    "moderate rain": "🌧️",
    "heavy rain": "🌧️",
    "torrential rain": "🌧️",
    "moderate or heavy rain shower": "🌧️",
    # 雷暴
    "thunder": "⛈️",
    "thundery outbreaks": "⛈️",
    "moderate or heavy rain with thunder": "⛈️",
    # 雪
    "snow": "❄️",
    "light snow": "🌨️",
    "patchy snow": "🌨️",
    "blowing snow": "🌨️",
    "heavy snow": "❄️",
    "blizzard": "❄️",
    # 特殊
    "sleet": "🌧️",
    "freezing drizzle": "🌧️",
    "ice pellets": "🌧️",
}

# ============================================================
# 星期映射
# ============================================================
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ============================================================
# 数据缓存
# ============================================================
_CACHE: Dict[str, tuple] = {}  # city_key -> (timestamp, data)
CACHE_TTL_SECONDS = 10 * 60  # 缓存有效期10分钟


def get_weather_icon(description: str) -> str:
    """
    根据天气描述返回对应的 Emoji 图标

    Args:
        description: 天气描述文本（如 "Sunny", "Light rain"）

    Returns:
        str: Emoji 图标，未匹配时返回默认 🌡️
    """
    desc_lower = description.lower()
    for keyword, icon in WEATHER_ICONS.items():
        if keyword in desc_lower:
            return icon
    return "🌡️"


def fetch_single_city(city_key: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """
    获取单个城市的天气数据（带重试机制）

    Args:
        city_key: 城市名称（如 "北京"）
        max_retries: 最大重试次数

    Returns:
        Optional[Dict]: 原始 JSON 数据，失败返回 None
    """
    # 检查缓存
    if city_key in _CACHE:
        cached_time, cached_data = _CACHE[city_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    encoded_city = urllib.parse.quote(city_key)
    url = f"https://wttr.in/{encoded_city}?format=j1"

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_data = json.loads(response.read().decode("utf-8"))

                # 写入缓存
                _CACHE[city_key] = (time.time(), raw_data)
                return raw_data

        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            if e.code == 500:  # 服务器内部错误，可能是城市名无效
                print(f"[WeatherAPI] 城市 '{city_key}' 查询失败: {last_error}")
                return None  # 无效城市，不重试
        except urllib.error.URLError as e:
            last_error = f"网络错误: {e.reason}"
        except json.JSONDecodeError as e:
            last_error = f"JSON 解析错误: {e}"
        except Exception as e:
            last_error = f"未知错误: {e}"

        if attempt < max_retries:
            wait = 2 ** attempt  # 指数退避：1s, 2s
            print(f"[WeatherAPI] 重试 {city_key} ({attempt + 1}/{max_retries})，等待 {wait}s...")
            time.sleep(wait)

    print(f"[WeatherAPI] 获取 '{city_key}' 天气最终失败: {last_error}")
    return None


def parse_weather_data(
    city_key: str, city_name: str, raw_data: Optional[Dict]
) -> Optional[Dict[str, Any]]:
    """
    解析原始天气数据为结构化字典

    Args:
        city_key: 城市标识
        city_name: 显示名称
        raw_data: 原始 JSON 数据

    Returns:
        Optional[Dict]: 结构化天气数据
    """
    if not raw_data or "current_condition" not in raw_data:
        return None

    try:
        current = raw_data["current_condition"][0]
        forecast_days = raw_data.get("weather", [])[:3]

        # ---- 解析当前天气 ----
        description = current.get("weatherDesc", [{}])[0].get("value", "")

        # ---- 解析未来3天预报 ----
        forecast = []
        for day in forecast_days:
            try:
                date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
                weekday = WEEKDAY_NAMES[date_obj.weekday()]
            except (ValueError, IndexError):
                weekday = ""

            # 取中午12点（第4个时段，索引4）的描述作为当日概括
            hourly_desc = (
                day.get("hourly", [{}])[4]
                .get("weatherDesc", [{}])[0]
                .get("value", "")
            )

            forecast.append(
                {
                    "week": weekday,
                    "high": day.get("maxtempC", "?"),
                    "low": day.get("mintempC", "?"),
                    "desc": hourly_desc,
                    "icon": get_weather_icon(hourly_desc),
                }
            )

        return {
            "name": city_name,
            "key": city_key,
            "temp": current.get("temp_C", "?"),
            "feels": current.get("FeelsLikeC", "?"),
            "humidity": current.get("humidity", "?"),
            "desc": description,
            "icon": get_weather_icon(description),
            "wind": (
                f"{current.get('windspeedKmph', '?')} km/h "
                f"{current.get('winddir16Point', '')}"
            ),
            "pressure": current.get("pressureMB", ""),
            "visibility": current.get("visibility", "?"),
            "uv_index": current.get("uvIndex", "0"),
            "cloudcover": current.get("cloudcover", "?"),
            "forecast": forecast,
        }
    except (KeyError, IndexError, TypeError) as e:
        print(f"[WeatherAPI] 数据解析失败 ({city_key}): {e}")
        return None


def get_weather_data(
    cities: List[tuple],
    use_cache: bool = True,
) -> List[Optional[Dict[str, Any]]]:
    """
    批量获取多城市天气数据（多线程并发）

    Args:
        cities: [(city_key, display_name), ...]
        use_cache: 是否使用缓存

    Returns:
        List[Optional[Dict]]: 每个城市的天气数据列表
    """
    if not use_cache:
        clear_cache()

    results: List[Optional[Dict]] = [None] * len(cities)
    lock = threading.Lock()

    def fetch_and_parse(index: int, city_key: str, city_name: str) -> None:
        """线程任务：获取并解析单个城市的数据"""
        raw = fetch_single_city(city_key)
        parsed = parse_weather_data(city_key, city_name, raw)
        with lock:
            results[index] = parsed

    threads = []
    for i, (city_key, city_name) in enumerate(cities):
        thread = threading.Thread(
            target=fetch_and_parse, args=(i, city_key, city_name), daemon=True
        )
        thread.start()
        threads.append(thread)

    # 等待所有线程完成（最多等30秒）
    for thread in threads:
        thread.join(timeout=30)

    return results


def get_weather_data_async(
    cities: List[tuple],
    callback: Callable[[List[Optional[Dict]]], None],
    use_cache: bool = True,
) -> threading.Thread:
    """
    异步获取天气数据（非阻塞，通过回调返回结果）

    Args:
        cities: [(city_key, display_name), ...]
        callback: 回调函数，接收 weather_data 列表参数
        use_cache: 是否使用缓存

    Returns:
        threading.Thread: 后台线程对象
    """

    def task():
        data = get_weather_data(cities, use_cache=use_cache)
        callback(data)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()
    return thread


def clear_cache() -> None:
    """清除天气数据缓存"""
    global _CACHE
    _CACHE = {}
    print("[WeatherAPI] 缓存已清除")


def get_cache_info() -> Dict[str, float]:
    """获取缓存信息"""
    return {k: v[0] for k, v in _CACHE.items()}
