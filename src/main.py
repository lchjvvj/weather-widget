#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌤️ 天气桌面小工具 — 主入口
=============================
一款支持多城市同屏显示、可自定义的桌面天气插件

功能：
  - 多城市同屏显示实时天气 + 未来3天预报
  - 自定义城市管理（搜索/添加/删除/排序）
  - 自定义背景图片
  - 深色护眼主题
  - 窗口自由拖拽
  - 30分钟自动刷新 + 数据缓存

使用方法：
  python3 src/main.py          # 直接运行
  python3 main.py              # 在 src 目录下运行
  ./setup.sh                   # 一键安装

依赖：
  - Python 3.8+
  - tkinter（系统自带）
  - Pillow（可选，用于背景图片支持）

作者: 小U同学 × WangWq
版本: 2.0.0
"""

import sys
import os


def fix_import_path():
    """
    修复 Python 导入路径，确保无论从哪个目录启动都能正确导入

    支持以下启动方式：
    1. python3 src/main.py          (项目根目录)
    2. cd src && python3 main.py    (src 目录内)
    3. python3 /path/to/main.py     (绝对路径)
    """
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    # 如果脚本在 src/ 目录下，项目根目录是上一级
    if os.path.basename(script_dir) == "src":
        project_root = os.path.dirname(script_dir)
    else:
        project_root = script_dir

    # 将项目根目录加入 sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    return project_root


def main():
    """主函数：创建并启动天气小工具"""
    # 修复导入路径
    project_root = fix_import_path()

    # 导入依赖
    try:
        # 检查 tkinter
        import tkinter
    except ImportError:
        print("❌ 错误: 需要 tkinter 支持")
        print("   请安装: sudo apt install python3-tk")
        sys.exit(1)

    try:
        from src.weather_ui import WeatherWidget
    except ImportError:
        # 如果从 src 目录运行，直接导入
        try:
            sys.path.insert(0, os.path.join(project_root, ".."))
            from src.weather_ui import WeatherWidget
        except ImportError:
            print(f"❌ 错误: 无法导入天气小工具模块")
            print(f"   项目路径: {project_root}")
            print(f"   Python 路径: {sys.path}")
            sys.exit(1)

    # 启动应用
    try:
        app = WeatherWidget()
        app.run()
    except KeyboardInterrupt:
        print("\n[WeatherWidget] 用户中断，退出程序")
    except Exception as e:
        print(f"[WeatherWidget] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
