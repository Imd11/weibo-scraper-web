#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动Web版微博爬取工具
"""

import os
import sys
import subprocess
import webbrowser
from threading import Timer

def install_requirements():
    """安装依赖包"""
    try:
        print("📦 检查并安装依赖包...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_web.txt"])
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def open_browser():
    """延迟打开浏览器"""
    url = "http://localhost:5000"
    print(f"🌐 打开浏览器: {url}")
    webbrowser.open(url)

def main():
    print("🚀 微博内容爬取工具 - Web版启动器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return
    
    # 检查是否存在必要文件
    required_files = ['app.py', 'web_scraper.py', 'templates/index.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return
    
    # 安装依赖
    if not install_requirements():
        print("请手动安装依赖包: pip install flask")
        return
    
    # 启动Web服务器
    print("🌐 启动Web服务器...")
    print("📝 访问地址: http://localhost:5000")
    print("💡 服务器启动后会自动打开浏览器")
    print("🛑 按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 延迟3秒打开浏览器
    timer = Timer(3.0, open_browser)
    timer.start()
    
    # 启动Flask应用
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()