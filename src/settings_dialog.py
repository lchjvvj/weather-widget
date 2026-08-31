"""
城市设置对话框模块
==================
提供城市管理界面：搜索、添加、删除、排序城市
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Tuple, Optional


# ============================================================
# 常用城市列表（按拼音排序，覆盖全国主要城市）
# ============================================================
COMMON_CITIES = [
    # 直辖市
    "北京", "上海", "天津", "重庆",
    # 广东
    "广州", "深圳", "东莞", "佛山", "珠海", "惠州", "中山", "汕头", "湛江", "肇庆",
    # 浙江
    "杭州", "宁波", "温州", "嘉兴", "绍兴", "金华", "台州", "湖州",
    # 江苏
    "南京", "苏州", "无锡", "常州", "南通", "徐州", "扬州", "镇江",
    # 山东
    "济南", "青岛", "烟台", "潍坊", "临沂", "淄博", "济宁",
    # 四川
    "成都", "绵阳", "德阳", "宜宾", "南充", "泸州",
    # 湖北
    "武汉", "襄阳", "宜昌", "荆州", "黄石",
    # 湖南
    "长沙", "株洲", "湘潭", "衡阳", "岳阳",
    # 福建
    "福州", "厦门", "泉州", "漳州", "莆田",
    # 河北
    "石家庄", "唐山", "保定", "邯郸", "廊坊", "秦皇岛", "迁安",
    # 河南
    "郑州", "洛阳", "开封", "南阳", "新乡",
    # 安徽
    "合肥", "芜湖", "蚌埠", "马鞍山",
    # 陕西
    "西安", "咸阳", "宝鸡", "延安", "榆林",
    # 辽宁
    "沈阳", "大连", "鞍山", "抚顺",
    # 江西
    "南昌", "九江", "赣州", "景德镇",
    # 广西
    "南宁", "桂林", "柳州", "北海",
    # 云南
    "昆明", "大理", "丽江", "曲靖",
    # 山西
    "太原", "大同", "长治", "临汾",
    # 吉林
    "长春", "吉林", "延边",
    # 黑龙江
    "哈尔滨", "大庆", "齐齐哈尔", "牡丹江",
    # 甘肃
    "兰州", "天水", "酒泉",
    # 贵州
    "贵阳", "遵义", "六盘水",
    # 海南
    "海口", "三亚", "乐东", "儋州",
    # 新疆
    "乌鲁木齐", "克拉玛依", "喀什",
    # 内蒙古
    "呼和浩特", "包头", "鄂尔多斯",
    # 宁夏
    "银川",
    # 青海
    "西宁",
    # 西藏
    "拉萨",
    # 港澳台
    "香港", "澳门", "台北", "高雄",
]


class CitySettingsDialog:
    """
    城市设置对话框

    支持功能：
    - 城市搜索/筛选（实时过滤）
    - 从常用城市列表多选添加
    - 手动输入自定义城市名
    - 删除已添加的城市
    - 上移/下移调整城市显示顺序
    - 实时预览城市列表变化
    """

    def __init__(
        self,
        parent: tk.Widget,
        cities: List[Tuple[str, str]],
        theme: dict,
    ):
        """
        Args:
            parent: 父窗口
            cities: 当前城市列表 [(key, name), ...]
            theme: 主题配色字典
        """
        self.parent = parent
        self.cities = [list(c) for c in cities]
        self.result: Optional[List[Tuple[str, str]]] = None
        self.theme = theme
        self._filtered_cities = list(COMMON_CITIES)  # 当前筛选后的城市列表

        # ---- 创建对话框窗口 ----
        self.window = tk.Toplevel(parent)
        self.window.title("🌤️ 管理城市列表")
        self.window.configure(bg=theme["bg"])
        self.window.geometry("500x560")
        self.window.minsize(460, 500)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # 居中显示
        self.window.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        dw, dh = 500, 560
        x = px + (pw - dw) // 2
        y = max(50, py + (ph - dh) // 2)
        self.window.geometry(f"+{x}+{y}")

        self._build_ui()

    # ============================================================
    # UI 构建
    # ============================================================
    def _build_ui(self):
        """构建对话框界面"""
        w = self.window
        bg = self.theme["bg"]
        fg = self.theme["fg"]
        fg2 = self.theme["fg2"]
        accent = self.theme["accent"]
        card_bg = self.theme["card_bg"]
        border = self.theme["border"]

        # ---- 标题 ----
        title_frame = tk.Frame(w, bg=bg)
        title_frame.pack(fill=tk.X, padx=15, pady=(12, 0))

        tk.Label(
            title_frame,
            text="🌤️ 管理城市列表",
            bg=bg,
            fg=accent,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor=tk.W)

        tk.Label(
            title_frame,
            text="搜索、添加、删除、排序城市，配置实时保存",
            bg=bg,
            fg=fg2,
            font=("Segoe UI", 9),
        ).pack(anchor=tk.W)

        # ---- 搜索框 ----
        search_frame = tk.Frame(w, bg=bg)
        search_frame.pack(fill=tk.X, padx=15, pady=(6, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)

        tk.Label(
            search_frame,
            text="🔍",
            bg=bg,
            fg=fg2,
            font=("Segoe UI", 12),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=card_bg,
            fg=fg,
            insertbackground=fg,
            font=("Segoe UI", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=border,
            relief=tk.FLAT,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.search_entry.bind("<Return>", lambda e: self._quick_add_first_city())

        # 清空搜索按钮
        self.clear_search_btn = tk.Button(
            search_frame,
            text="✕",
            bg=card_bg,
            fg=fg2,
            activebackground=accent,
            activeforeground="#000",
            font=("Segoe UI", 8),
            bd=0,
            padx=6,
            pady=0,
            cursor="hand2",
            command=self._clear_search,
        )
        self.clear_search_btn.pack(side=tk.RIGHT, padx=(3, 0))

        # ---- 主区域：左右分栏 ----
        main = tk.Frame(w, bg=bg)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=(6, 0))

        # ====== 左侧：当前城市列表 ======
        left_frame = tk.Frame(main, bg=bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self._build_current_list(left_frame, bg, fg, fg2, accent, card_bg, border)

        # ====== 右侧：添加城市 ======
        right_frame = tk.Frame(main, bg=bg)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self._build_add_panel(right_frame, bg, fg, fg2, accent, card_bg, border)

        # ---- 手动输入 ----
        self._build_manual_input(w, bg, fg, fg2, accent, card_bg, border)

        # ---- 底部按钮 ----
        self._build_bottom_buttons(w, bg, fg, accent)

        # 初始化列表显示
        self._refresh_listbox()
        self._update_filtered_list()

    def _build_current_list(self, parent, bg, fg, fg2, accent, card_bg, border):
        """构建左侧当前城市列表"""
        tk.Label(
            parent,
            text="📋 当前显示的城市：",
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 3))

        # 列表容器
        list_container = tk.Frame(parent, bg=card_bg, bd=0)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.city_listbox = tk.Listbox(
            list_container,
            bg=card_bg,
            fg=fg,
            selectbackground=accent,
            selectforeground="#000",
            font=("Segoe UI", 10),
            bd=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.city_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=2)

        scrollbar = tk.Scrollbar(
            list_container, orient=tk.VERTICAL, command=self.city_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.city_listbox.config(yscrollcommand=scrollbar.set)

        # 操作按钮行
        btn_row = tk.Frame(parent, bg=bg)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        self.up_btn = tk.Button(
            btn_row,
            text="↑ 上移",
            bg="#3a3a5a",
            fg=fg,
            activebackground=accent,
            activeforeground="#000",
            font=("Segoe UI", 8),
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._move_up,
        )
        self.up_btn.pack(side=tk.LEFT, padx=(0, 3))

        self.down_btn = tk.Button(
            btn_row,
            text="↓ 下移",
            bg="#3a3a5a",
            fg=fg,
            activebackground=accent,
            activeforeground="#000",
            font=("Segoe UI", 8),
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._move_down,
        )
        self.down_btn.pack(side=tk.LEFT, padx=(0, 3))

        self.del_btn = tk.Button(
            btn_row,
            text="🗑 删除",
            bg="#3a3a5a",
            fg=fg,
            activebackground="#ff6b6b",
            activeforeground="#fff",
            font=("Segoe UI", 8),
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._delete_city,
        )
        self.del_btn.pack(side=tk.LEFT, padx=(3, 0))

    def _build_add_panel(self, parent, bg, fg, fg2, accent, card_bg, border):
        """构建右侧添加城市面板"""
        tk.Label(
            parent,
            text="➕ 从常用城市添加：",
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 3))

        # 搜索结果标签
        self.search_result_label = tk.Label(
            parent,
            text="",
            bg=bg,
            fg=fg2,
            font=("Segoe UI", 8),
            anchor=tk.W,
        )
        self.search_result_label.pack(fill=tk.X)

        # 列表容器
        add_container = tk.Frame(parent, bg=card_bg, bd=0)
        add_container.pack(fill=tk.BOTH, expand=True)

        self.add_listbox = tk.Listbox(
            add_container,
            bg=card_bg,
            fg=fg,
            selectbackground=accent,
            selectforeground="#000",
            font=("Segoe UI", 9),
            bd=0,
            highlightthickness=0,
            selectmode=tk.MULTIPLE,
            activestyle="none",
        )
        self.add_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=2)

        scrollbar2 = tk.Scrollbar(
            add_container, orient=tk.VERTICAL, command=self.add_listbox.yview
        )
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.add_listbox.config(yscrollcommand=scrollbar2.set)

        # 确认添加按钮
        self.confirm_add_btn = tk.Button(
            parent,
            text="✅ 添加选中城市",
            bg=accent,
            fg="#000",
            activebackground="#ffb347",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=3,
            cursor="hand2",
            command=self._confirm_add_selected,
        )
        self.confirm_add_btn.pack(fill=tk.X, pady=(4, 0))

        # 双击添加
        self.add_listbox.bind("<Double-Button-1>", lambda e: self._confirm_add_selected())

    def _build_manual_input(self, w, bg, fg, fg2, accent, card_bg, border):
        """构建手动输入区域"""
        input_frame = tk.Frame(w, bg=bg)
        input_frame.pack(fill=tk.X, padx=15, pady=(4, 0))

        tk.Label(
            input_frame,
            text="手动输入城市名：",
            bg=bg,
            fg=fg2,
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT)

        self.city_entry = tk.Entry(
            input_frame,
            bg=card_bg,
            fg=fg,
            insertbackground=fg,
            font=("Segoe UI", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=border,
            relief=tk.FLAT,
        )
        self.city_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, ipady=3, padx=(5, 3)
        )
        self.city_entry.bind("<Return>", lambda e: self._confirm_custom_city())

        self.add_custom_btn = tk.Button(
            input_frame,
            text="确认添加",
            bg=accent,
            fg="#000",
            activebackground="#ffb347",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._confirm_custom_city,
        )
        self.add_custom_btn.pack(side=tk.RIGHT)

    def _build_bottom_buttons(self, w, bg, fg, accent):
        """构建底部按钮"""
        bottom_frame = tk.Frame(w, bg=bg)
        bottom_frame.pack(fill=tk.X, padx=15, pady=(6, 10))

        tk.Button(
            bottom_frame,
            text="✅ 保存并关闭",
            bg=accent,
            fg="#000",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._save,
        ).pack(side=tk.RIGHT, padx=3)

        tk.Button(
            bottom_frame,
            text="❌ 取消",
            bg="#3a3a5a",
            fg=fg,
            font=("Segoe UI", 10),
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self._cancel,
        ).pack(side=tk.RIGHT, padx=3)

        # 城市数量统计
        self.count_label = tk.Label(
            bottom_frame,
            text="",
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9),
        )
        self.count_label.pack(side=tk.LEFT)
        self._update_count_label()

    # ============================================================
    # 搜索功能
    # ============================================================
    def _on_search_changed(self, *args):
        """搜索框内容变化时更新列表"""
        self._update_filtered_list()

    def _clear_search(self):
        """清空搜索框"""
        self.search_var.set("")
        self.search_entry.focus()

    def _update_filtered_list(self):
        """根据搜索关键词更新右侧城市列表"""
        keyword = self.search_var.get().strip().lower()
        self.add_listbox.delete(0, tk.END)

        if keyword:
            # 按拼音/汉字过滤
            self._filtered_cities = [
                c for c in COMMON_CITIES if keyword in c.lower()
            ]
        else:
            self._filtered_cities = list(COMMON_CITIES)

        # 填充列表
        for city in self._filtered_cities:
            self.add_listbox.insert(tk.END, f"  🏙️ {city}")

        # 更新搜索结果提示
        total = len(COMMON_CITIES)
        found = len(self._filtered_cities)
        if keyword:
            self.search_result_label.config(
                text=f"找到 {found}/{total} 个城市" if found > 0 else "未找到匹配城市"
            )
        else:
            self.search_result_label.config(text=f"共 {total} 个常用城市")

    def _quick_add_first_city(self):
        """回车快速添加搜索到的第一个城市"""
        keyword = self.search_var.get().strip()
        if not keyword:
            return
        if self._filtered_cities:
            city_text = self._filtered_cities[0]
            if not any(k == city_text for k, _ in self.cities):
                self.cities.append([city_text, city_text])
                self._refresh_listbox()
                self._update_count_label()
                self.search_var.set("")
                self.search_entry.focus()
                # 显示提示
                self.search_result_label.config(
                    text=f"✅ 已添加「{city_text}」",
                    fg=self.theme["success"],
                )
                self.window.after(2000, lambda: self._update_filtered_list())

    # ============================================================
    # 业务逻辑
    # ============================================================
    def _refresh_listbox(self):
        """刷新当前城市列表显示"""
        self.city_listbox.delete(0, tk.END)
        for idx, (_, name) in enumerate(self.cities, 1):
            self.city_listbox.insert(tk.END, f"  {idx}. 🏙️ {name}")

    def _update_count_label(self):
        """更新城市数量标签"""
        self.count_label.config(text=f"当前 {len(self.cities)} 个城市")

    def _confirm_add_selected(self):
        """从常用城市列表中添加选中城市"""
        selections = self.add_listbox.curselection()
        if not selections:
            messagebox.showinfo("提示", "请先在右侧列表中选中要添加的城市（可多选或双击）")
            return

        added = 0
        for idx in selections:
            # 列表项格式为 "  🏙️ {city_name}"
            city_text = self.add_listbox.get(idx).strip(" 🏙️")
            if not any(k == city_text for k, _ in self.cities):
                self.cities.append([city_text, city_text])
                added += 1

        if added > 0:
            self._refresh_listbox()
            self._update_count_label()
            self.add_listbox.selection_clear(0, tk.END)
            messagebox.showinfo(
                "✅ 添加成功",
                f"已添加 {added} 个城市\n点击底部「保存并关闭」生效",
            )
        else:
            messagebox.showinfo("提示", "所选城市已在列表中，无需重复添加")

    def _confirm_custom_city(self):
        """手动输入城市名并添加"""
        text = self.city_entry.get().strip()
        if not text:
            messagebox.showinfo("提示", "请输入城市名")
            return

        # 支持 "城市名, 显示名" 格式
        if "," in text:
            parts = [p.strip() for p in text.split(",", 1)]
            key, name = parts[0], parts[1]
        else:
            key = name = text

        if any(k == key for k, _ in self.cities):
            messagebox.showinfo("提示", f"「{name}」已在列表中")
            return

        self.cities.append([key, name])
        self._refresh_listbox()
        self._update_count_label()
        self.city_entry.delete(0, tk.END)
        messagebox.showinfo(
            "✅ 添加成功",
            f"已添加「{name}」\n点击底部「保存并关闭」生效",
        )

    def _move_up(self):
        """将选中城市上移一位"""
        selection = self.city_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        idx = selection[0]
        self.cities[idx], self.cities[idx - 1] = (
            self.cities[idx - 1],
            self.cities[idx],
        )
        self._refresh_listbox()
        self.city_listbox.selection_set(idx - 1)

    def _move_down(self):
        """将选中城市下移一位"""
        selection = self.city_listbox.curselection()
        if not selection or selection[0] >= len(self.cities) - 1:
            return
        idx = selection[0]
        self.cities[idx], self.cities[idx + 1] = (
            self.cities[idx + 1],
            self.cities[idx],
        )
        self._refresh_listbox()
        self.city_listbox.selection_set(idx + 1)

    def _delete_city(self):
        """删除选中的城市"""
        selection = self.city_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选中要删除的城市")
            return

        idx = selection[0]
        if len(self.cities) <= 1:
            messagebox.showinfo("提示", "至少保留一个城市")
            return

        city_name = self.cities[idx][1]
        if messagebox.askyesno("确认删除", f"确定要删除「{city_name}」吗？"):
            self.cities.pop(idx)
            self._refresh_listbox()
            self._update_count_label()

    def _save(self):
        """保存并关闭对话框"""
        if len(self.cities) == 0:
            messagebox.showinfo("提示", "请至少添加一个城市")
            return
        self.result = self.cities
        self.window.destroy()

    def _cancel(self):
        """取消并关闭对话框"""
        if messagebox.askyesno("确认取消", "取消将不保存任何修改，确定吗？"):
            self.result = None
            self.window.destroy()
