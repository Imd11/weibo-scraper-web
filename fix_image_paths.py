#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复现有报告中的图片路径问题
"""

import re
from config import OUTPUT_DIR, USER_NAME, START_DATE, END_DATE

def fix_image_paths_in_report():
    """修复报告中的图片路径"""
    date_range = f"{START_DATE.replace('-', '')}-{END_DATE.replace('-', '')}"
    filename = f"{OUTPUT_DIR}/reports/{USER_NAME}_完整微博内容_{date_range}.md"
    
    print(f"🔧 修复图片路径: {filename}")
    
    try:
        # 读取现有报告
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复图片路径：从 weibo_output/images/ 改为 ../images/
        # 匹配模式：![图片X](weibo_output/images/XXXXX.jpg)
        content = re.sub(
            r'!\[(.*?)\]\(weibo_output/images/(.*?\.jpg)\)', 
            r'![\1](../images/\2)', 
            content
        )
        
        # 写回文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 图片路径修复完成")
        
        # 统计修复的图片数量
        image_count = len(re.findall(r'!\[.*?\]\(\.\./images/.*?\.jpg\)', content))
        print(f"📸 修复了 {image_count} 个图片引用")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")

if __name__ == "__main__":
    fix_image_paths_in_report()