#!/usr/bin/env python3
"""
🌤️ 天气桌面小工具 - 推送到 GitHub
===================================
使用纯 Python (dulwich) 推送，无需系统安装 git。

Token 安全策略（按优先级）：
  1. 环境变量 GITHUB_TOKEN（推荐，不落盘）
  2. 系统密钥环 keyring（可选，安全存储）
  3. 交互式输入（仅内存，不写入磁盘）

用法：
  export GITHUB_TOKEN=ghp_xxx
  python3 push_to_github.py late-autumn414
"""

import os
import sys
import json
import urllib.request
from dulwich import porcelain, repo

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
REPO_NAME = "weather-widget"
SERVICE = "weather-widget"
KEYRING_USER = "github-token"


def get_github_token() -> str:
    """获取 GitHub Token：环境变量优先，其次 keyring，最后交互输入"""
    # 1. 环境变量（推荐，不落盘）
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        print("✅ 已从环境变量 GITHUB_TOKEN 读取 Token")
        return token

    # 2. 系统密钥环（可选）
    try:
        import keyring
        token = keyring.get_password(SERVICE, KEYRING_USER) or ""
        if token:
            print("✅ 已从系统密钥环读取 Token")
            return token
    except ImportError:
        pass  # keyring 未安装，跳过

    # 3. 交互式输入（仅内存，不写入磁盘）
    token = input("请输入 GitHub 个人访问令牌 (Token): ").strip()
    if token:
        use_keyring = input("是否保存到系统密钥环以便下次使用？(y/N): ").strip().lower()
        if use_keyring == "y":
            try:
                import keyring
                keyring.set_password(SERVICE, KEYRING_USER, token)
                print(f"✅ Token 已安全保存到系统密钥环（{SERVICE}）")
            except ImportError:
                print("⚠️ 未安装 keyring，Token 仅本次会话有效")
    return token


def check_repo_exists(username: str, token: str):
    """检查 GitHub 仓库是否存在"""
    url = f"https://api.github.com/repos/{username}/{REPO_NAME}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"✅ 仓库已存在: {data['html_url']}")
            return True, data["html_url"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"ℹ️ 仓库 {username}/{REPO_NAME} 不存在，将自动创建")
            return False, None
        print(f"❌ API 错误: {e.code} {e.reason}")
        return False, None


def create_github_repo(username: str, token: str):
    """在 GitHub 创建公开仓库"""
    url = "https://api.github.com/user/repos"
    data = json.dumps({
        "name": REPO_NAME,
        "description": "🌤️ 多城市同屏天气桌面插件 - 实时天气+3天预报 | MIT License",
        "private": False,
        "auto_init": False,
        "has_issues": True,
        "has_wiki": True,
    }).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"✅ 仓库已创建: {result['html_url']}")
            return result["html_url"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 创建仓库失败: {e.code}")
        print(f"   错误: {error_body[:300]}")
        return None


def push_to_github(username: str, token: str):
    """推送代码到 GitHub"""
    repo_url = f"https://{username}:{token}@github.com/{username}/{REPO_NAME}.git"

    os.chdir(PROJECT_PATH)
    r = repo.Repo(".")

    print(f"📤 正在推送 {len(r.object_store)} 个对象到 GitHub...")
    try:
        porcelain.push(r, repo_url, b"refs/heads/master")
        print("✅ 推送成功！")
        return f"https://github.com/{username}/{REPO_NAME}"
    except Exception as e:
        print(f"❌ 推送失败: {e}")
        return None


def main():
    print("=" * 50)
    print("  🌤️  天气桌面小工具 - 推送到 GitHub")
    print("=" * 50)
    print()

    # 1. 获取 Token（环境变量 / keyring / 交互）
    token = get_github_token()
    if not token:
        print("❌ Token 不能为空")
        sys.exit(1)

    # 2. 获取用户名（命令行参数或交互输入）
    username = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not username:
        username = input("请输入 GitHub 用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        sys.exit(1)

    # 3. 检查/创建仓库
    exists, _ = check_repo_exists(username, token)
    if not exists:
        print("🔄 正在创建仓库...")
        repo_url = create_github_repo(username, token)
        if not repo_url:
            sys.exit(1)

    # 4. 推送代码
    result = push_to_github(username, token)
    if result:
        print()
        print("=" * 50)
        print("  ✅ 恭喜！推送完成！")
        print("=" * 50)
        print()
        print(f"  仓库地址: {result}")
        print()
        print("  下一步：去 deepin 论坛发帖提交作品")
        print("  → https://bbs.deepin.org")
        print("  标题: 【deepin插件开发活动】天气桌面小工具")
        print("=" * 50)


if __name__ == "__main__":
    main()
