#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成HTML版本的微博报告，确保图片正确显示
"""

import re
import base64
import os
from config import OUTPUT_DIR, USER_NAME, START_DATE, END_DATE

def image_to_base64(image_path):
    """将图片转换为base64编码"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

def generate_html_report():
    """生成HTML版本的报告"""
    date_range = f"{START_DATE.replace('-', '')}-{END_DATE.replace('-', '')}"
    md_filename = f"{OUTPUT_DIR}/reports/{USER_NAME}_完整微博内容_{date_range}.md"
    html_filename = f"{OUTPUT_DIR}/reports/{USER_NAME}_完整微博内容_{date_range}.html"
    
    print(f"🌐 生成HTML报告: {html_filename}")
    
    try:
        # 读取Markdown文件
        with open(md_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # HTML模板
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; margin-top: 25px; }}
        .weibo-content {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 15px 0;
            border-left: 4px solid #3498db;
        }}
        .weibo-meta {{ 
            color: #7f8c8d; 
            font-size: 0.9em; 
            margin-bottom: 10px;
        }}
        .weibo-text {{ 
            margin: 15px 0; 
            white-space: pre-line;
        }}
        .retweet {{ 
            background-color: #ecf0f1; 
            padding: 10px; 
            border-radius: 5px; 
            margin: 10px 0;
            border-left: 3px solid #95a5a6;
        }}
        .stats {{ 
            background-color: #fff; 
            padding: 10px; 
            border-radius: 5px; 
            border: 1px solid #bdc3c7;
            margin-top: 15px;
        }}
        .stats ul {{ margin: 0; padding-left: 20px; }}
        img {{ 
            max-width: 100%; 
            height: auto; 
            border-radius: 8px; 
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        hr {{ border: none; border-top: 1px solid #ecf0f1; margin: 30px 0; }}
        .summary {{ 
            background-color: #e8f5e8; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
        }}
        blockquote {{ 
            margin: 0; 
            padding-left: 15px; 
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
        
        # 转换Markdown到HTML
        html_content = content
        
        # 替换标题
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        
        # 替换粗体
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        
        # 替换链接
        html_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html_content)
        
        # 替换图片为base64嵌入
        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            # 将相对路径转换为绝对路径
            if img_path.startswith('../images/'):
                full_path = os.path.join(OUTPUT_DIR, 'images', img_path[10:])
            else:
                full_path = img_path
            
            # 转换为base64
            base64_data = image_to_base64(full_path)
            if base64_data:
                return f'<img src="data:image/jpeg;base64,{base64_data}" alt="{alt_text}" />'
            else:
                return f'<p>图片加载失败: {alt_text}</p>'
        
        html_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, html_content)
        
        # 替换引用块
        html_content = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html_content, flags=re.MULTILINE)
        
        # 替换水平线
        html_content = re.sub(r'^---$', r'<hr>', html_content, flags=re.MULTILINE)
        
        # 添加段落标签
        paragraphs = html_content.split('\n\n')
        formatted_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<'):
                p = f'<p>{p}</p>'
            formatted_paragraphs.append(p)
        
        html_content = '\n\n'.join(formatted_paragraphs)
        
        # 生成最终HTML
        title = f"{USER_NAME} - 完整微博内容报告 ({START_DATE} 至 {END_DATE})"
        final_html = html_template.format(title=title, content=html_content)
        
        # 写入HTML文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print("✅ HTML报告生成完成")
        print(f"📁 文件位置: {html_filename}")
        print("💡 提示: 用浏览器打开HTML文件即可看到带图片的完整报告")
        
    except Exception as e:
        print(f"❌ 生成HTML失败: {e}")

if __name__ == "__main__":
    generate_html_report()