"""
配置管理模块
============
负责应用配置的读写、城市列表的持久化存储、窗口位置记忆
"""

import json
import os
from typing import List, Tuple, Optional

# ============================================================
# 默认配置
# ============================================================
DEFAULT_CITIES: List[Tuple[str, str]] = [
    ("北京", "北京"),
    ("迁安", "河北迁安"),
    ("乐东", "海南乐东"),
]

# 配置文件路径
CONFIG_DIR = os.path.expanduser("~/.config/weather-widget")
CITIES_FILE = os.path.join(CONFIG_DIR, "cities.json")
BG_FILE = os.path.join(CONFIG_DIR, "bg_path.txt")
WINDOW_POS_FILE = os.path.join(CONFIG_DIR, "window_pos.json")


class ConfigManager:
    """配置管理器 - 统一管理应用的所有配置项"""

    @staticmethod
    def _ensure_dir() -> None:
        """确保配置目录存在"""
        os.makedirs(CONFIG_DIR, exist_ok=True)

    # ----------------------------------------------------------
    # 城市列表管理
    # ----------------------------------------------------------
    @staticmethod
    def load_cities() -> List[Tuple[str, str]]:
        """
        从配置文件中加载城市列表

        Returns:
            List[Tuple[str, str]]: [(key, display_name), ...]
        """
        try:
            if os.path.exists(CITIES_FILE):
                with open(CITIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return [(item["key"], item["name"]) for item in data]
        except (json.JSONDecodeError, KeyError, IOError, TypeError) as e:
            print(f"[Config] 加载城市配置失败: {e}，使用默认配置")
        return DEFAULT_CITIES.copy()

    @staticmethod
    def save_cities(cities: List[Tuple[str, str]]) -> None:
        """
        保存城市列表到配置文件

        Args:
            cities: [(key, display_name), ...]
        """
        ConfigManager._ensure_dir()
        data = [{"key": key, "name": name} for key, name in cities]
        try:
            with open(CITIES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[Config] 保存城市配置失败: {e}")

    # ----------------------------------------------------------
    # 背景图片管理
    # ----------------------------------------------------------
    @staticmethod
    def load_bg_path() -> Optional[str]:
        """
        加载背景图片路径

        Returns:
            Optional[str]: 图片路径，无配置时返回 None
        """
        try:
            if os.path.exists(BG_FILE):
                with open(BG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if path and os.path.exists(path):
                        return path
        except IOError as e:
            print(f"[Config] 加载背景配置失败: {e}")
        return None

    @staticmethod
    def save_bg_path(path: Optional[str]) -> None:
        """
        保存或清除背景图片路径

        Args:
            path: 图片路径，传 None 或空字符串表示清除
        """
        ConfigManager._ensure_dir()
        try:
            if path and os.path.exists(path):
                with open(BG_FILE, "w", encoding="utf-8") as f:
                    f.write(path)
            else:
                # 清除背景设置
                if os.path.exists(BG_FILE):
                    os.remove(BG_FILE)
        except IOError as e:
            print(f"[Config] 保存背景配置失败: {e}")

    # ----------------------------------------------------------
    # 窗口位置管理
    # ----------------------------------------------------------
    @staticmethod
    def load_window_pos() -> Optional[Tuple[int, int]]:
        """
        加载窗口位置

        Returns:
            Optional[Tuple[int, int]]: (x, y) 坐标
        """
        try:
            if os.path.exists(WINDOW_POS_FILE):
                with open(WINDOW_POS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                x, y = data["x"], data["y"]
                # 简单验证：确保坐标在屏幕范围内
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    return (int(x), int(y))
        except (json.JSONDecodeError, KeyError, IOError, TypeError):
            pass
        return None

    @staticmethod
    def save_window_pos(x: int, y: int) -> None:
        """
        保存窗口位置

        Args:
            x: 窗口左上角 x 坐标
            y: 窗口左上角 y 坐标
        """
        ConfigManager._ensure_dir()
        try:
            with open(WINDOW_POS_FILE, "w", encoding="utf-8") as f:
                json.dump({"x": x, "y": y}, f)
        except IOError as e:
            print(f"[Config] 保存窗口位置失败: {e}")
