#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动微博爬虫
使用方法：python3 run.py
"""

import sys
import os
from config import WEIBO_USER_ID, USER_NAME, START_DATE, END_DATE

def main():
    print("🚀 微博内容爬虫")
    print("=" * 50)
    print(f"📝 目标用户: {USER_NAME}")
    print(f"🆔 用户ID: {WEIBO_USER_ID}")
    print(f"📅 时间范围: {START_DATE} 到 {END_DATE}")
    print("=" * 50)
    
    print("\n请选择操作:")
    print("1. 快速预览 - 生成示例报告（推荐新用户）")
    print("2. 完整爬取 - 爬取所有微博数据（耗时较长）")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🎯 开始生成快速预览报告...")
        os.system("python3 create_final_report.py")
    elif choice == "2":
        print("\n🎯 开始完整爬取（这可能需要几分钟）...")
        os.system("python3 organized_scraper.py")
    elif choice == "3":
        print("👋 再见！")
        sys.exit(0)
    else:
        print("❌ 无效选择，请重新运行程序")
        sys.exit(1)

if __name__ == "__main__":
    main()