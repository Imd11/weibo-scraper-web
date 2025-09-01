#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 用户可以修改这里的参数来自定义爬取目标
"""

# 目标用户配置
WEIBO_USER_ID = "1317335037"  # 微博用户ID（从URL获取：weibo.com/u/后面的数字）
USER_NAME = "姜汝祥"           # 用户名称（用于文件命名）

# 时间范围配置 (YYYY-MM-DD 格式)
START_DATE = "2025-03-01"     # 开始日期
END_DATE = "2025-09-01"       # 结束日期

# 输出配置
OUTPUT_DIR = "weibo_output"   # 输出目录名
SIMPLE_FILENAME = True        # 使用简化文件名（True=简单，False=详细时间戳）

# 爬取配置
MAX_PAGES = 10               # 最大爬取页数（防止爬取过多）
DOWNLOAD_IMAGES = True       # 是否下载图片
GET_FULL_TEXT = True         # 是否获取全文（展开"...全文"）

# 请求配置
REQUEST_DELAY = 1            # 请求间隔（秒）
RETRY_TIMES = 3              # 失败重试次数