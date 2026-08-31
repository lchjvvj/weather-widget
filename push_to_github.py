#!/usr/bin/env python3
"""
🌤️ 天气桌面小工具 - 推送到 GitHub
===================================
使用 Python 推送，无需系统安装 git
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import base64
from dulwich import porcelain, repo

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))


def get_github_token():
    """获取 GitHub Token"""
    token_file = os.path.expanduser("~/.config/weather-widget/github_token.txt")
    token = None
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            token = f.read().strip()
    if not token:
        token = input("请输入 GitHub 个人访问令牌 (Token): ").strip()
        save = input("是否保存 Token 以便下次使用？(y/N): ").strip().lower()
        if save == 'y':
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w") as f:
                f.write(token)
            os.chmod(token_file, 0o600)
            print(f"✅ Token 已保存到 {token_file}")
    return token


def check_repo_exists(username, repo_name, token):
    """检查 GitHub 仓库是否存在"""
    url = f"https://api.github.com/repos/{username}/{repo_name}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"✅ 仓库已存在: {data['html_url']}")
            return True, data['html_url']
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"⚠️ 仓库 {username}/{repo_name} 不存在")
            return False, None
        else:
            print(f"❌ API 错误: {e.code} {e.reason}")
            return False, None


def create_github_repo(username, repo_name, token):
    """在 GitHub 创建仓库"""
    url = "https://api.github.com/user/repos"
    data = json.dumps({
        "name": repo_name,
        "description": "🌤️ 多城市同屏天气桌面插件 - 实时天气+3天预报",
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
            return result['html_url']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ 创建仓库失败: {e.code}")
        print(f"   错误: {error_body[:200]}")
        return None


def push_to_github(username, repo_name, token):
    """推送代码到 GitHub"""
    repo_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    
    os.chdir(PROJECT_PATH)
    r = repo.Repo(".")
    
    print("📤 正在推送到 GitHub...")
    try:
        porcelain.push(r, repo_url, b'refs/heads/master')
        print(f"✅ 推送成功！")
        return f"https://github.com/{username}/{repo_name}"
    except Exception as e:
        print(f"❌ 推送失败: {e}")
        return None


def main():
    print("=" * 50)
    print("  🌤️  天气桌面小工具 - 推送到 GitHub")
    print("=" * 50)
    print()
    
    # 1. 获取 Token
    token = get_github_token()
    if not token:
        print("❌ Token 不能为空")
        sys.exit(1)
    
    # 2. 获取用户名
    username = input("请输入 GitHub 用户名: ").strip()
    if not username:
        print("❌ 用户名不能为空")
        sys.exit(1)
    
    repo_name = "weather-widget"
    
    # 3. 检查/创建仓库
    exists, repo_url = check_repo_exists(username, repo_name, token)
    if not exists:
        print("🔄 正在创建仓库...")
        repo_url = create_github_repo(username, repo_name, token)
        if not repo_url:
            sys.exit(1)
    
    # 4. 推送代码
    result = push_to_github(username, repo_name, token)
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
        print("  → 论坛资源 → AI专区 → AI 开发实验室")
        print("  标题: 【deepin插件开发活动】天气桌面小工具")
        print("=" * 50)


if __name__ == "__main__":
    main()
