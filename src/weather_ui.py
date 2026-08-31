"""
桌面窗口 UI 模块
=================
WeatherWidget - 主窗口类，负责天气信息的桌面展示
支持多城市卡片渲染、拖拽、右键菜单、自动刷新等
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Dict, Any
from datetime import datetime

from .config_manager import ConfigManager, DEFAULT_CITIES
from .weather_api import get_weather_data_async, clear_cache
from .settings_dialog import CitySettingsDialog


# ============================================================
# 主题配色
# ============================================================
DARK_THEME = {
    "bg": "#1a1a2e",
    "card_bg": "#252540",
    "card_bg2": "#2a2a45",
    "card_bg3": "#252545",
    "accent": "#f7971e",
    "fg": "#ffffff",
    "fg2": "#a0a0b0",
    "border": "#3a3a5a",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
}

# 刷新间隔（毫秒）
REFRESH_INTERVAL_MS = 30 * 60 * 1000  # 30 分钟


class WeatherWidget:
    """
    天气桌面小工具主窗口

    功能特性：
    - 多城市天气卡片同屏显示
    - 实时天气 + 未来3天预报
    - 深色主题，支持自定义背景图
    - 自由拖拽，右键快捷菜单
    - 每30分钟自动刷新，城市配置持久化
    - 数据缓存，断网时显示旧数据
    - 自动重试失败的请求
    """

    # 布局常量
    CARD_HEIGHT = 150
    HEADER_HEIGHT = 55
    FOOTER_HEIGHT = 38
    WINDOW_WIDTH = 400
    CARD_GAP = 6
    FORECAST_START_X = 190  # 右侧预报起始位置

    def __init__(self):
        """初始化天气小工具"""
        self.win = tk.Tk()
        self.win.title("天气桌面小工具")
        self.win.overrideredirect(False)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.95)

        # ---- 加载配置 ----
        self.cities = ConfigManager.load_cities()
        self.bg_path = ConfigManager.load_bg_path()
        self.bg_image = None
        self.bg_photo = None
        self.after_id = None
        self.dragging = False
        self.last_update_time = None
        self._weather_data_cache = None  # 缓存上次成功获取的数据

        # ---- 计算窗口尺寸 ----
        self._update_window_size()

        # ---- 设置窗口位置 ----
        saved_pos = ConfigManager.load_window_pos()
        if saved_pos:
            x, y = saved_pos
        else:
            screen_w = self.win.winfo_screenwidth()
            x = screen_w - self.WINDOW_WIDTH - 30
            y = 80
        self.win.geometry(f"{self.WINDOW_WIDTH}x{self.win_height}+{x}+{y}")
        self.win.resizable(False, False)
        self.win.minsize(self.WINDOW_WIDTH, 300)

        # ---- 加载背景图 ----
        self._load_bg_image()

        # ---- 构建主界面 ----
        self._build_main_ui()

        # ---- 绑定事件 ----
        self._bind_events()

        # ---- 首次加载 ----
        self._show_loading()
        self.update_weather()
        self._schedule_auto_refresh()

    # ============================================================
    # 窗口尺寸管理
    # ============================================================
    def _update_window_size(self):
        """根据城市数量动态计算窗口高度"""
        city_count = max(len(self.cities), 1)
        self.win_height = (
            self.HEADER_HEIGHT
            + city_count * (self.CARD_HEIGHT + self.CARD_GAP)
            + self.FOOTER_HEIGHT
            + 10
        )

    # ============================================================
    # UI 构建
    # ============================================================
    def _build_main_ui(self):
        """构建主界面框架"""
        self.main_frame = tk.Frame(
            self.win,
            bg=DARK_THEME["bg"],
            highlightbackground=DARK_THEME["border"],
            highlightthickness=1,
            bd=0,
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.WINDOW_WIDTH,
            height=self.win_height,
            bg=DARK_THEME["bg"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_events(self):
        """绑定鼠标和窗口事件"""
        # 拖拽
        self.canvas.bind("<Button-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # 右键菜单
        self.canvas.bind("<Button-3>", self._on_right_click)

        # 窗口关闭
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # ESC 键最小化
        self.win.bind("<Escape>", lambda e: self._minimize_to_taskbar())

        # F5 刷新
        self.win.bind("<F5>", lambda e: self.update_weather())

    # ============================================================
    # 背景图管理
    # ============================================================
    def _load_bg_image(self):
        """
        加载背景图片
        自动缩放到窗口尺寸，并压暗亮度以突出卡片内容
        """
        if not self.bg_path:
            self.bg_image = None
            self.bg_photo = None
            return

        try:
            from PIL import Image, ImageTk, ImageEnhance, ImageFilter

            img = Image.open(self.bg_path)
            img = img.resize(
                (self.WINDOW_WIDTH, self.win_height), Image.LANCZOS
            )
            # 压暗到 35% 亮度，让卡片内容更清晰
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.35)

            # 轻微模糊以减少噪点干扰
            try:
                img = img.filter(ImageFilter.GaussianBlur(radius=1))
            except Exception:
                pass

            self.bg_image = img
            self.bg_photo = ImageTk.PhotoImage(img)
        except ImportError:
            print("[UI] 未安装 Pillow，背景图功能不可用")
            self.bg_image = None
            self.bg_photo = None
        except Exception as e:
            print(f"[UI] 加载背景图失败: {e}")
            self.bg_image = None
            self.bg_photo = None

    def _draw_bg_image(self):
        """在画布上绘制背景图片"""
        if self.bg_photo:
            self.canvas.create_image(
                0, 0, image=self.bg_photo, anchor=tk.NW, tags="bg"
            )

    def _change_bg(self):
        """打开文件选择对话框，更换背景图"""
        path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("所有文件", "*.*"),
            ],
        )
        if path:
            self.bg_path = path
            ConfigManager.save_bg_path(path)
            self._load_bg_image()
            self.update_weather()

    def _reset_bg(self):
        """恢复默认背景（无背景图）"""
        self.bg_path = None
        self.bg_image = None
        self.bg_photo = None
        ConfigManager.save_bg_path(None)
        self.update_weather()

    # ============================================================
    # 绘制工具
    # ============================================================
    def _draw_rounded_rect(
        self, x1, y1, x2, y2, radius, tags="", **kwargs
    ):
        """绘制圆角矩形"""
        r = radius
        # 四个圆角
        self.canvas.create_arc(
            x1, y1, x1 + 2 * r, y1 + 2 * r,
            start=90, extent=90, tags=tags, **kwargs
        )
        self.canvas.create_arc(
            x2 - 2 * r, y1, x2, y1 + 2 * r,
            start=0, extent=90, tags=tags, **kwargs
        )
        self.canvas.create_arc(
            x1, y2 - 2 * r, x1 + 2 * r, y2,
            start=180, extent=90, tags=tags, **kwargs
        )
        self.canvas.create_arc(
            x2 - 2 * r, y2 - 2 * r, x2, y2,
            start=270, extent=90, tags=tags, **kwargs
        )
        # 中间矩形
        self.canvas.create_rectangle(
            x1 + r, y1, x2 - r, y2, tags=tags, **kwargs
        )
        self.canvas.create_rectangle(
            x1, y1 + r, x2, y2 - r, tags=tags, **kwargs
        )

    def _draw_card_bg(self, x1, y1, x2, y2, color):
        """绘制城市卡片背景"""
        self._draw_rounded_rect(
            x1, y1, x2, y2, 10, fill=color, outline=color
        )

    # ============================================================
    # 天气数据更新
    # ============================================================
    def update_weather(self):
        """异步更新所有城市的天气数据"""
        # 先清除画布，显示加载状态
        self.canvas.delete("all")
        self._draw_rounded_rect(
            0, 0, self.WINDOW_WIDTH, self.win_height,
            15,
            fill=DARK_THEME["bg"] if not self.bg_photo else "",
            outline=DARK_THEME["border"],
            width=1,
        )
        self._show_loading()

        # 异步获取数据（使用缓存加速）
        get_weather_data_async(self.cities, self._on_weather_ready, use_cache=True)

    def _on_weather_ready(self, data: List[Optional[Dict]]):
        """天气数据就绪回调 - 在 UI 线程中渲染"""
        self.win.after(0, self._render_weather, data)

    def _show_loading(self):
        """显示加载中提示"""
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2,
            self.win_height // 2,
            text="🌤️ 加载天气数据中...",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 14),
            tags="loading",
        )

    # ============================================================
    # 天气卡片渲染
    # ============================================================
    def _render_weather(self, data: List[Optional[Dict]]):
        """
        渲染天气卡片到画布

        Args:
            data: 天气数据列表（每个元素对应一个城市或 None）
        """
        self.canvas.delete("all")
        self._draw_bg_image()

        # 重新绘制背景
        self._draw_rounded_rect(
            0, 0, self.WINDOW_WIDTH, self.win_height,
            15,
            fill=DARK_THEME["bg"] if not self.bg_photo else "",
            outline=DARK_THEME["border"],
            width=1,
        )

        # 检查是否全部失败
        valid_data = [d for d in data if d is not None]
        has_any_data = len(valid_data) > 0

        if not has_any_data:
            # 如果有缓存数据，显示缓存数据 + 提示
            if self._weather_data_cache:
                self._render_stale_data_warning()
                self._render_weather_data(self._weather_data_cache)
                return
            else:
                self._render_error_state()
                return

        # 更新缓存
        self._weather_data_cache = data
        self.last_update_time = datetime.now()

        # 渲染数据
        self._render_weather_data(data)

    def _render_stale_data_warning(self):
        """在顶部显示旧数据警告"""
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2, 4,
            text="⚠️ 网络不可用，显示上次缓存数据",
            fill=DARK_THEME["warning"],
            font=("Segoe UI", 8),
            tags="stale_warning",
        )

    def _render_error_state(self):
        """渲染完全错误状态"""
        # 显示错误图标
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2,
            self.win_height // 2 - 30,
            text="🌐",
            fill=DARK_THEME["error"],
            font=("Segoe UI", 48),
            tags="error_icon",
        )
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2,
            self.win_height // 2 + 20,
            text="❌ 获取天气失败",
            fill=DARK_THEME["error"],
            font=("Segoe UI", 14, "bold"),
            tags="error_title",
        )
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2,
            self.win_height // 2 + 42,
            text="请检查网络连接后重试\n提示：F5 刷新 | 右键菜单刷新",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 10),
            justify=tk.CENTER,
            tags="error_hint",
        )

        # 添加重试按钮
        retry_tag = "error_retry"
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2,
            self.win_height // 2 + 75,
            text="🔄 点击重试",
            fill=DARK_THEME["accent"],
            font=("Segoe UI", 12, "bold"),
            tags=retry_tag,
        )
        self.canvas.tag_bind(
            retry_tag, "<Button-1>", lambda e: self.update_weather()
        )
        self.canvas.tag_bind(
            retry_tag, "<Enter>",
            lambda e: self.canvas.itemconfig(retry_tag, fill=DARK_THEME["success"]),
        )
        self.canvas.tag_bind(
            retry_tag, "<Leave>",
            lambda e: self.canvas.itemconfig(retry_tag, fill=DARK_THEME["accent"]),
        )

    def _render_weather_data(self, data: List[Optional[Dict]]):
        """
        渲染天气数据到画布

        Args:
            data: 天气数据列表
        """
        valid_data = [d for d in data if d is not None]
        if not valid_data:
            self._render_error_state()
            return

        # ---- 绘制标题栏 ----
        y_offset = 8
        city_count = len(valid_data)

        # 城市数量角标
        badge_colors = ["#f7971e", "#4ade80", "#60a5fa", "#f472b6", "#a78bfa"]
        badge_color = badge_colors[min(city_count - 1, len(badge_colors) - 1)]

        self.canvas.create_text(
            18, y_offset + 12,
            text=f"🌤️  天气 · {city_count}城",
            fill=DARK_THEME["accent"],
            font=("Segoe UI", 13, "bold"),
            anchor=tk.W,
            tags="title",
        )

        # 更新时间
        update_text = "更新中..."
        if self.last_update_time:
            update_text = f"更新于 {self.last_update_time.strftime('%H:%M')}"
        else:
            update_text = f"更新于 {datetime.now().strftime('%H:%M')}"

        self.canvas.create_text(
            18, y_offset + 30,
            text=f"🔄 {update_text}  ·  拖拽移动 · 右键菜单",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 8),
            anchor=tk.W,
            tags="subtitle",
        )

        y_offset = 50
        card_colors = [
            DARK_THEME["card_bg"],
            DARK_THEME["card_bg2"],
            DARK_THEME["card_bg3"],
        ]

        # ---- 绘制每个城市的天气卡片 ----
        for i, city in enumerate(valid_data):
            card_y = y_offset
            card_h = self.CARD_HEIGHT

            # 卡片背景
            self._draw_card_bg(
                8, card_y, self.WINDOW_WIDTH - 8, card_y + card_h,
                card_colors[i % 3]
            )

            # ===== 左侧：当前天气 =====
            # 城市名
            city_name = city.get("name", city.get("key", "未知"))
            self.canvas.create_text(
                18, card_y + 10,
                text=f"🏙️  {city_name}",
                fill=DARK_THEME["fg"],
                font=("Segoe UI", 11, "bold"),
                anchor=tk.W,
                tags=f"city_{i}",
            )

            # 大号天气图标
            self.canvas.create_text(
                20, card_y + 42,
                text=city.get("icon", "🌡️"),
                fill=DARK_THEME["fg"],
                font=("Segoe UI", 30),
                anchor=tk.W,
                tags=f"icon_{i}",
            )

            # 温度（大号加粗）
            temp = city.get("temp", "?")
            self.canvas.create_text(
                80, card_y + 38,
                text=f"{temp}°C",
                fill=DARK_THEME["fg"],
                font=("Segoe UI", 26, "bold"),
                anchor=tk.W,
                tags=f"temp_{i}",
            )

            # 天气描述
            desc = city.get("desc", "")
            self.canvas.create_text(
                20, card_y + 80,
                text=desc,
                fill=DARK_THEME["fg2"],
                font=("Segoe UI", 9),
                anchor=tk.W,
                tags=f"desc_{i}",
            )

            # 湿度 + 体感温度 + UV指数
            humidity = city.get("humidity", "?")
            feels = city.get("feels", "?")
            uv = city.get("uv_index", "")
            detail_text = f"💧 {humidity}%    🌡️ {feels}°C"
            if uv and uv != "0":
                detail_text += f"    ☀️ UV {uv}"

            self.canvas.create_text(
                20, card_y + 96,
                text=detail_text,
                fill=DARK_THEME["fg2"],
                font=("Segoe UI", 8),
                anchor=tk.W,
                tags=f"detail_{i}",
            )

            # 风速 + 能见度
            wind = city.get("wind", "?")
            vis = city.get("visibility", "")
            wind_text = f"💨 {wind}"
            if vis:
                wind_text += f"    👁️ {vis}km"
            self.canvas.create_text(
                20, card_y + 112,
                text=wind_text,
                fill=DARK_THEME["fg2"],
                font=("Segoe UI", 8),
                anchor=tk.W,
                tags=f"wind_{i}",
            )

            # ===== 右侧：未来3天预报 =====
            f_start_x = self.FORECAST_START_X
            forecast = city.get("forecast", [])
            for j, day in enumerate(forecast):
                day_x = f_start_x + j * 68

                # 星期几
                self.canvas.create_text(
                    day_x + 25, card_y + 10,
                    text=day.get("week", ""),
                    fill=DARK_THEME["fg2"],
                    font=("Segoe UI", 8),
                    tags=f"fw_{i}_{j}",
                )

                # 预报图标
                self.canvas.create_text(
                    day_x + 25, card_y + 30,
                    text=day.get("icon", "🌡️"),
                    fill=DARK_THEME["fg"],
                    font=("Segoe UI", 18),
                    tags=f"fi_{i}_{j}",
                )

                # 预报描述（截断过长描述）
                day_desc = day.get("desc", "")
                desc_short = (
                    day_desc[:4] + (".." if len(day_desc) > 4 else "")
                )
                self.canvas.create_text(
                    day_x + 25, card_y + 52,
                    text=desc_short,
                    fill=DARK_THEME["fg2"],
                    font=("Segoe UI", 7),
                    tags=f"fd_{i}_{j}",
                )

                # 最高/最低温
                high = day.get("high", "?")
                low = day.get("low", "?")
                self.canvas.create_text(
                    day_x + 25, card_y + 70,
                    text=f"{high}°/{low}°",
                    fill=DARK_THEME["fg"],
                    font=("Segoe UI", 9, "bold"),
                    tags=f"ft_{i}_{j}",
                )

            y_offset += card_h + self.CARD_GAP

        # ---- 底部操作栏 ----
        self._render_footer()

    def _render_footer(self):
        """渲染底部操作栏"""
        footer_y = self.win_height - 26
        self.canvas.create_line(
            15, footer_y - 3,
            self.WINDOW_WIDTH - 15, footer_y - 3,
            fill=DARK_THEME["border"],
            width=1,
            tags="footer_line",
        )

        # 刷新按钮
        refresh_tag = "refresh_footer"
        self.canvas.create_text(
            self.WINDOW_WIDTH // 2 - 35, footer_y + 5,
            text="🔄 刷新",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 10),
            tags=refresh_tag,
        )
        self.canvas.tag_bind(
            refresh_tag, "<Button-1>", lambda e: self.update_weather()
        )
        self.canvas.tag_bind(
            refresh_tag, "<Enter>",
            lambda e: self.canvas.itemconfig(refresh_tag, fill=DARK_THEME["accent"]),
        )
        self.canvas.tag_bind(
            refresh_tag, "<Leave>",
            lambda e: self.canvas.itemconfig(refresh_tag, fill=DARK_THEME["fg2"]),
        )

        # 设置按钮
        settings_tag = "footer_set"
        self.canvas.create_text(
            self.WINDOW_WIDTH - 15, footer_y + 5,
            text="⚙ 设置",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 10),
            anchor=tk.E,
            tags=settings_tag,
        )
        self.canvas.tag_bind(
            settings_tag, "<Button-1>", lambda e: self._open_settings()
        )
        self.canvas.tag_bind(
            settings_tag, "<Enter>",
            lambda e: self.canvas.itemconfig(settings_tag, fill=DARK_THEME["accent"]),
        )
        self.canvas.tag_bind(
            settings_tag, "<Leave>",
            lambda e: self.canvas.itemconfig(settings_tag, fill=DARK_THEME["fg2"]),
        )

        # 最小化按钮
        min_tag = "footer_min"
        self.canvas.create_text(
            12, footer_y + 5,
            text="🗕",
            fill=DARK_THEME["fg2"],
            font=("Segoe UI", 10),
            anchor=tk.W,
            tags=min_tag,
        )
        self.canvas.tag_bind(
            min_tag, "<Button-1>", lambda e: self._minimize_to_taskbar()
        )
        self.canvas.tag_bind(
            min_tag, "<Enter>",
            lambda e: self.canvas.itemconfig(min_tag, fill=DARK_THEME["accent"]),
        )
        self.canvas.tag_bind(
            min_tag, "<Leave>",
            lambda e: self.canvas.itemconfig(min_tag, fill=DARK_THEME["fg2"]),
        )

    # ============================================================
    # 设置对话框
    # ============================================================
    def _open_settings(self):
        """打开城市设置对话框"""
        dialog = CitySettingsDialog(self.win, self.cities, DARK_THEME)
        self.win.wait_window(dialog.window)

        if dialog.result is not None:
            self.cities = dialog.result
            ConfigManager.save_cities(self.cities)
            self._update_window_size()
            self.win.geometry(f"{self.WINDOW_WIDTH}x{self.win_height}")
            # 清除缓存，强制刷新数据
            clear_cache()
            self.update_weather()

    # ============================================================
    # 窗口拖拽
    # ============================================================
    def _on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.dragging = False

    def _on_drag_move(self, event):
        if (
            abs(event.x - self.drag_start_x) > 5
            or abs(event.y - self.drag_start_y) > 5
        ):
            self.dragging = True
            x = self.win.winfo_x() + event.x - self.drag_start_x
            y = self.win.winfo_y() + event.y - self.drag_start_y
            self.win.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        if self.dragging:
            # 保存窗口位置
            ConfigManager.save_window_pos(
                self.win.winfo_x(), self.win.winfo_y()
            )
        self.dragging = False

    # ============================================================
    # 右键菜单
    # ============================================================
    def _on_right_click(self, event):
        """右键弹出快捷菜单"""
        menu = tk.Menu(
            self.win,
            tearoff=0,
            bg=DARK_THEME["card_bg"],
            fg=DARK_THEME["fg"],
            activebackground=DARK_THEME["accent"],
            activeforeground="#000",
            font=("Segoe UI", 9),
        )

        menu.add_command(
            label="🔄 刷新天气 (F5)", command=self.update_weather
        )
        menu.add_command(
            label="🗕 最小化 (Esc)", command=self._minimize_to_taskbar
        )
        menu.add_separator()
        menu.add_command(
            label="⚙ 设置城市...", command=self._open_settings
        )
        menu.add_command(
            label="🎨 更换背景图...", command=self._change_bg
        )
        if self.bg_path:
            menu.add_command(
                label="↩ 恢复默认背景", command=self._reset_bg
            )
        menu.add_separator()

        # 显示版本信息
        try:
            from . import __version__, __author__
            about_text = f"关于 天气小工具 v{__version__}"
        except ImportError:
            about_text = "关于 天气小工具 v2.0"

        menu.add_command(
            label=about_text,
            command=lambda: self._show_about_dialog(),
        )
        menu.add_separator()
        menu.add_command(
            label="❌ 退出", command=self._on_close
        )

        menu.post(event.x_root, event.y_root)

    def _show_about_dialog(self):
        """显示关于对话框"""
        try:
            from . import __version__, __author__
        except ImportError:
            __version__ = "2.0.0"
            __author__ = "小U同学 × WangWq"

        messagebox.showinfo(
            "🌤️ 关于天气小工具",
            f"天气桌面小工具 v{__version__}\n\n"
            f"作者: {__author__}\n\n"
            "一款支持多城市同屏显示的桌面天气插件\n"
            "数据源: wttr.in (免费天气 API)\n\n"
            "功能特色:\n"
            "• 多城市天气卡片同屏显示\n"
            "• 实时天气 + 未来3天预报\n"
            "• 自定义城市列表 / 背景图片\n"
            "• 30分钟自动刷新 / 数据缓存\n"
            "• 拖拽移动 / 右键快捷菜单\n\n"
            "快捷键:\n"
            "  F5   刷新天气\n"
            "  Esc  最小化到任务栏",
        )

    def _minimize_to_taskbar(self):
        """最小化窗口到任务栏"""
        self.win.iconify()

    # ============================================================
    # 自动刷新
    # ============================================================
    def _schedule_auto_refresh(self):
        """安排30分钟后自动刷新"""
        if self.after_id:
            self.win.after_cancel(self.after_id)
        self.after_id = self.win.after(
            REFRESH_INTERVAL_MS, self._auto_refresh
        )

    def _auto_refresh(self):
        """自动刷新天气"""
        self.update_weather()
        self._schedule_auto_refresh()

    # ============================================================
    # 退出
    # ============================================================
    def _on_close(self):
        """关闭窗口并退出"""
        # 保存窗口位置
        try:
            ConfigManager.save_window_pos(
                self.win.winfo_x(), self.win.winfo_y()
            )
        except Exception:
            pass
        if self.after_id:
            self.win.after_cancel(self.after_id)
        self.win.quit()
        self.win.destroy()

    # ============================================================
    # 启动
    # ============================================================
    def run(self):
        """启动主循环"""
        try:
            self.win.mainloop()
        except KeyboardInterrupt:
            print("\n[WeatherWidget] 用户中断，退出程序")
            self._on_close()
