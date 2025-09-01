#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web版微博爬虫 - 支持关键词搜索和Web界面
"""

import ssl
import urllib.request
import json
import re
import os
import glob
from datetime import datetime
import time
import zipfile
import base64


class WebWeiboScraper:
    def __init__(self, user_id, user_name, start_date, end_date, keywords=None, max_pages=10, request_delay=2, output_dir="weibo_output"):
        # 基本配置
        self.user_id = user_id
        self.user_name = user_name
        self.start_date = start_date
        self.end_date = end_date
        self.keywords = keywords or []  # 关键词列表
        self.max_pages = max_pages
        self.request_delay = request_delay
        self.output_dir = output_dir
        
        # SSL设置
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # HTTP请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'https://m.weibo.cn/u/{self.user_id}',
        }
        
        # 创建输出目录
        self.reports_dir = os.path.join(self.output_dir, "reports")
        self.images_dir = os.path.join(self.output_dir, "images")
        self.data_dir = os.path.join(self.output_dir, "data")
        
        for directory in [self.output_dir, self.reports_dir, self.images_dir, self.data_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 统计信息
        self.stats = {
            'total_weibos': 0,
            'filtered_weibos': 0,
            'images_downloaded': 0,
            'keyword_matches': 0,
            'pages_processed': 0
        }

    def format_chinese_date(self, date_str):
        """将日期转换为中文格式"""
        try:
            if any(day in date_str for day in ['Thu', 'Fri', 'Mon', 'Tue', 'Wed', 'Sat', 'Sun']):
                date_str = re.sub(r'\s+\+\d{4}', '', date_str)
                dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                return f"{dt.year}年{dt.month}月{dt.day}日"
            else:
                return date_str
        except:
            return date_str

    def is_in_date_range(self, date_str):
        """检查日期是否在指定范围内"""
        try:
            if any(day in date_str for day in ['Thu', 'Fri', 'Mon', 'Tue', 'Wed', 'Sat', 'Sun']):
                date_str = re.sub(r'\s+\+\d{4}', '', date_str)
                dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
                return start_dt <= dt <= end_dt
            return True
        except:
            return True

    def matches_keywords(self, text):
        """检查文本是否包含关键词"""
        if not self.keywords:  # 如果没有设置关键词，返回True（不过滤）
            return True
        
        text = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text:
                return True
        return False

    def decode_text(self, text):
        """解码Unicode文本"""
        if not text:
            return ""
        try:
            if '\\u' in text:
                decoded = json.loads(f'"{text}"')
                return decoded
            return text
        except:
            return text

    def clean_html(self, text):
        """清理HTML标签"""
        if not text:
            return ""
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        return self.decode_text(text).strip()

    def get_full_text(self, weibo_id):
        """获取微博全文"""
        full_text_url = f"https://m.weibo.cn/statuses/extend?id={weibo_id}"
        try:
            req = urllib.request.Request(full_text_url, headers=self.headers)
            response = urllib.request.urlopen(req, timeout=15, context=self.ssl_context)
            content = response.read().decode('utf-8')
            data = json.loads(content)
            if data.get('ok') == 1:
                full_text = data.get('data', {}).get('longTextContent', '')
                if full_text:
                    return self.clean_html(full_text)
        except Exception as e:
            print(f"获取全文失败: {e}")
        return None

    def download_image(self, image_url, weibo_id, image_index):
        """下载图片"""
        try:
            if '.jpg' in image_url:
                ext = 'jpg'
            elif '.png' in image_url:
                ext = 'png'
            elif '.gif' in image_url:
                ext = 'gif'
            else:
                ext = 'jpg'
            
            filename = f"{weibo_id}_{image_index}.{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            if os.path.exists(filepath):
                return filepath
            
            req = urllib.request.Request(image_url, headers=self.headers)
            response = urllib.request.urlopen(req, timeout=15, context=self.ssl_context)
            
            with open(filepath, 'wb') as f:
                f.write(response.read())
            
            print(f"✅ 下载图片: {filename}")
            self.stats['images_downloaded'] += 1
            return filepath
            
        except Exception as e:
            print(f"❌ 下载图片失败: {e}")
            return None

    def scrape_weibos(self, progress_callback=None):
        """爬取微博内容"""
        all_weibos = []
        page = 1
        
        print(f"🚀 开始搜集 {self.user_name} 的微博...")
        print(f"📅 时间范围: {self.start_date} 到 {self.end_date}")
        if self.keywords:
            print(f"🔍 关键词筛选: {', '.join(self.keywords)}")
        
        while page <= self.max_pages:
            if progress_callback:
                progress_callback(
                    int((page - 1) / self.max_pages * 100),
                    f"正在获取第 {page} 页..."
                )
            
            print(f"\n📖 正在获取第 {page} 页...")
            
            # 获取微博列表
            url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={self.user_id}&containerid=107603{self.user_id}&page={page}"
            
            try:
                req = urllib.request.Request(url, headers=self.headers)
                response = urllib.request.urlopen(req, timeout=30, context=self.ssl_context)
                content = response.read().decode('utf-8')
                data = json.loads(content)
                
                if data.get('ok') != 1:
                    print(f"❌ 第 {page} 页获取失败")
                    break
                
                cards = data.get('data', {}).get('cards', [])
                if not cards:
                    print(f"📝 第 {page} 页没有更多内容")
                    break
                
                page_weibos = 0
                for card in cards:
                    if card.get('card_type') == 9:
                        mblog = card.get('mblog', {})
                        if mblog:
                            self.stats['total_weibos'] += 1
                            
                            created_at = mblog.get('created_at', '')
                            
                            # 检查时间范围
                            if not self.is_in_date_range(created_at):
                                continue
                            
                            weibo_id = mblog.get('id', '')
                            
                            # 获取文本
                            raw_text = mblog.get('text', '')
                            clean_text = self.clean_html(raw_text)
                            
                            # 检查是否需要获取全文
                            if mblog.get('isLongText', False) or '全文' in clean_text:
                                print(f"📝 获取微博 {weibo_id} 的全文...")
                                full_text = self.get_full_text(weibo_id)
                                if full_text:
                                    clean_text = full_text
                                    print(f"✅ 全文获取成功: {len(full_text)} 字符")
                            
                            # 处理转发内容文本（用于关键词匹配）
                            full_content_for_matching = clean_text
                            if 'retweeted_status' in mblog:
                                rt = mblog['retweeted_status']
                                rt_text = self.clean_html(rt.get('text', ''))
                                rt_id = rt.get('id', '')
                                
                                if rt.get('isLongText', False) or '全文' in rt_text:
                                    rt_full_text = self.get_full_text(rt_id)
                                    if rt_full_text:
                                        rt_text = rt_full_text
                                
                                full_content_for_matching += " " + rt_text
                            
                            # 关键词筛选
                            if not self.matches_keywords(full_content_for_matching):
                                continue
                            
                            self.stats['keyword_matches'] += 1
                            
                            weibo_data = {
                                'id': weibo_id,
                                'mid': mblog.get('mid', ''),
                                'created_at': created_at,
                                'text': clean_text,
                                'source': self.clean_html(mblog.get('source', '')),
                                'reposts_count': mblog.get('reposts_count', 0),
                                'comments_count': mblog.get('comments_count', 0),
                                'attitudes_count': mblog.get('attitudes_count', 0),
                                'url': f"https://m.weibo.cn/detail/{weibo_id}",
                            }
                            
                            # 处理图片
                            if 'pics' in mblog and mblog['pics']:
                                weibo_data['images'] = []
                                for i, pic in enumerate(mblog['pics'], 1):
                                    pic_url = pic.get('large', {}).get('url', '')
                                    if pic_url:
                                        weibo_data['images'].append(pic_url)
                                        self.download_image(pic_url, weibo_id, i)
                            
                            # 处理转发内容
                            if 'retweeted_status' in mblog:
                                rt = mblog['retweeted_status']
                                rt_text = self.clean_html(rt.get('text', ''))
                                rt_id = rt.get('id', '')
                                
                                if rt.get('isLongText', False) or '全文' in rt_text:
                                    rt_full_text = self.get_full_text(rt_id)
                                    if rt_full_text:
                                        rt_text = rt_full_text
                                
                                weibo_data['retweeted'] = {
                                    'user_name': rt.get('user', {}).get('screen_name', ''),
                                    'text': rt_text
                                }
                                
                                # 下载转发内容的图片
                                if 'pics' in rt and rt['pics']:
                                    for i, pic in enumerate(rt['pics'], 1):
                                        pic_url = pic.get('large', {}).get('url', '')
                                        if pic_url:
                                            self.download_image(pic_url, weibo_id, f"rt_{i}")
                            
                            all_weibos.append(weibo_data)
                            page_weibos += 1
                            self.stats['filtered_weibos'] += 1
                
                print(f"✅ 第 {page} 页获取到 {page_weibos} 条符合条件的微博")
                
                if page_weibos == 0:
                    print("📝 没有更多符合条件的微博")
                    break
                
                self.stats['pages_processed'] = page
                page += 1
                
                if page <= self.max_pages:
                    time.sleep(self.request_delay)
                
            except Exception as e:
                print(f"❌ 第 {page} 页获取失败: {e}")
                break
        
        print(f"\n🎉 搜集完成！")
        print(f"📊 总共处理了 {self.stats['total_weibos']} 条微博")
        print(f"📊 筛选后得到 {self.stats['filtered_weibos']} 条微博")
        print(f"📊 下载了 {self.stats['images_downloaded']} 张图片")
        if self.keywords:
            print(f"📊 关键词匹配 {self.stats['keyword_matches']} 条")
        
        if progress_callback:
            progress_callback(100, f"爬取完成！获取到 {len(all_weibos)} 条微博")
        
        return all_weibos

    def generate_reports(self, weibos):
        """生成报告文件"""
        print("📝 生成报告文件...")
        
        # 文件名包含时间范围和关键词信息
        date_range = f"{self.start_date.replace('-', '')}-{self.end_date.replace('-', '')}"
        keyword_suffix = f"_{'_'.join(self.keywords[:3])}" if self.keywords else ""
        
        base_filename = f"{self.user_name}_微博内容_{date_range}{keyword_suffix}"
        md_filename = os.path.join(self.reports_dir, f"{base_filename}.md")
        html_filename = os.path.join(self.reports_dir, f"{base_filename}.html")
        
        # 生成Markdown报告
        self.generate_markdown_report(weibos, md_filename)
        
        # 生成HTML报告
        self.generate_html_report(weibos, html_filename, md_filename)
        
        # 创建完整压缩包（包含reports和images文件夹）
        complete_package = self.create_complete_package(md_filename, html_filename)
        
        return {
            'markdown_file': md_filename,
            'html_file': html_filename,
            'complete_package': complete_package,
            'weibo_count': len(weibos),
            'image_count': self.stats['images_downloaded'],
            'keyword_matches': self.stats['keyword_matches']
        }

    def generate_markdown_report(self, weibos, filename):
        """生成Markdown报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {self.user_name} - 微博内容报告\n")
            f.write(f"**时间范围**: {self.start_date} 至 {self.end_date}\n")
            if self.keywords:
                f.write(f"**关键词筛选**: {', '.join(self.keywords)}\n")
            f.write("\n")
            
            f.write("## 📊 数据统计\n\n")
            f.write(f"- **用户**: {self.user_name}\n")
            f.write(f"- **微博总数**: {len(weibos)} 条\n")
            f.write(f"- **图片总数**: {self.stats['images_downloaded']} 张\n")
            if self.keywords:
                f.write(f"- **关键词匹配**: {self.stats['keyword_matches']} 条\n")
            f.write(f"- **报告生成**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("---\n\n")
            
            if weibos:
                f.write("## 📝 微博内容 (完整版)\n\n")
                
                for i, weibo in enumerate(weibos, 1):
                    f.write(f"### 微博 {i}\n\n")
                    
                    # 基本信息
                    created_at = weibo.get('created_at', '')
                    chinese_date = self.format_chinese_date(created_at)
                    f.write(f"**🕒 发布时间**: {chinese_date}\n")
                    f.write(f"**🔗 微博链接**: {weibo.get('url', '')}\n")
                    f.write(f"**🆔 微博ID**: {weibo.get('id', '')}\n\n")
                    
                    # 完整内容
                    text = weibo.get('text', '').strip()
                    if text:
                        f.write(f"**📄 完整内容**:\n\n{text}\n\n")
                    
                    # 转发内容
                    if 'retweeted' in weibo:
                        rt = weibo['retweeted']
                        f.write(f"**🔄 转发内容**:\n")
                        f.write(f"> **@{rt.get('user_name', '')}**: {rt.get('text', '')}\n\n")
                    
                    # 图片展示
                    if 'images' in weibo and weibo['images']:
                        for idx, img_url in enumerate(weibo['images'], 1):
                            weibo_id = weibo.get('id', '')
                            local_pattern = os.path.join(self.images_dir, f"{weibo_id}_{idx}.jpg")
                            if os.path.exists(local_pattern):
                                relative_path = f"../images/{weibo_id}_{idx}.jpg"
                                f.write(f"![图片{idx}]({relative_path})\n\n")
                            
                            rt_pattern = os.path.join(self.images_dir, f"{weibo_id}_rt_{idx}.jpg")
                            if os.path.exists(rt_pattern):
                                relative_rt_path = f"../images/{weibo_id}_rt_{idx}.jpg"
                                f.write(f"![转发图片{idx}]({relative_rt_path})\n\n")
                    
                    # 互动数据
                    f.write(f"**📊 互动数据**:\n")
                    f.write(f"- 🔄 转发: {weibo.get('reposts_count', 0):,}\n")
                    f.write(f"- 💬 评论: {weibo.get('comments_count', 0):,}\n")
                    f.write(f"- ❤️ 点赞: {weibo.get('attitudes_count', 0):,}\n")
                    
                    if weibo.get('source'):
                        f.write(f"- 📱 来源: {weibo.get('source', '')}\n")
                    
                    f.write(f"\n---\n\n")
        
        print(f"✅ Markdown报告已生成: {filename}")

    def generate_html_report(self, weibos, html_filename, md_filename):
        """生成HTML报告，图片以base64嵌入"""
        print(f"📝 生成HTML报告: {html_filename}")
        
        def image_to_base64(image_path):
            """将图片转换为base64编码"""
            try:
                with open(image_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except:
                return None
        
        # HTML模板
        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
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
        
        # 生成HTML内容
        html_content = f"<h1>{self.user_name} - 微博内容报告</h1>\n"
        html_content += f"<p><strong>时间范围</strong>: {self.start_date} 至 {self.end_date}</p>\n"
        if self.keywords:
            html_content += f"<p><strong>关键词筛选</strong>: {', '.join(self.keywords)}</p>\n"
        html_content += "\n"
        
        html_content += "<h2>📊 数据统计</h2>\n"
        html_content += "<ul>\n"
        html_content += f"<li><strong>用户</strong>: {self.user_name}</li>\n"
        html_content += f"<li><strong>微博总数</strong>: {len(weibos)} 条</li>\n"
        html_content += f"<li><strong>图片总数</strong>: {self.stats['images_downloaded']} 张</li>\n"
        if self.keywords:
            html_content += f"<li><strong>关键词匹配</strong>: {self.stats['keyword_matches']} 条</li>\n"
        html_content += f"<li><strong>报告生成</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>\n"
        html_content += "</ul>\n"
        
        html_content += "<hr>\n"
        
        if weibos:
            html_content += "<h2>📝 微博内容 (完整版)</h2>\n"
            
            for i, weibo in enumerate(weibos, 1):
                html_content += f"<h3>微博 {i}</h3>\n"
                html_content += "<div class='weibo-content'>\n"
                
                # 基本信息
                created_at = weibo.get('created_at', '')
                chinese_date = self.format_chinese_date(created_at)
                html_content += f"<p class='weibo-meta'><strong>🕒 发布时间</strong>: {chinese_date}</p>\n"
                html_content += f"<p class='weibo-meta'><strong>🔗 微博链接</strong>: <a href='{weibo.get('url', '')}' target='_blank'>{weibo.get('url', '')}</a></p>\n"
                html_content += f"<p class='weibo-meta'><strong>🆔 微博ID</strong>: {weibo.get('id', '')}</p>\n"
                
                # 完整内容
                text = weibo.get('text', '').strip()
                if text:
                    html_content += f"<div class='weibo-text'><strong>📄 完整内容</strong>:<br>{text}</div>\n"
                
                # 转发内容
                if 'retweeted' in weibo:
                    rt = weibo['retweeted']
                    html_content += "<div class='retweet'>\n"
                    html_content += f"<strong>🔄 转发内容</strong>:<br>\n"
                    html_content += f"<blockquote><strong>@{rt.get('user_name', '')}</strong>: {rt.get('text', '')}</blockquote>\n"
                    html_content += "</div>\n"
                
                # 图片展示（base64嵌入）
                if 'images' in weibo and weibo['images']:
                    for idx, img_url in enumerate(weibo['images'], 1):
                        weibo_id = weibo.get('id', '')
                        local_pattern = os.path.join(self.images_dir, f"{weibo_id}_{idx}.jpg")
                        if os.path.exists(local_pattern):
                            base64_data = image_to_base64(local_pattern)
                            if base64_data:
                                html_content += f'<img src="data:image/jpeg;base64,{base64_data}" alt="图片{idx}" />\n'
                        
                        # 检查转发图片
                        rt_pattern = os.path.join(self.images_dir, f"{weibo_id}_rt_{idx}.jpg")
                        if os.path.exists(rt_pattern):
                            base64_data = image_to_base64(rt_pattern)
                            if base64_data:
                                html_content += f'<img src="data:image/jpeg;base64,{base64_data}" alt="转发图片{idx}" />\n'
                
                # 互动数据
                html_content += "<div class='stats'>\n"
                html_content += "<strong>📊 互动数据</strong>:\n"
                html_content += "<ul>\n"
                html_content += f"<li>🔄 转发: {weibo.get('reposts_count', 0):,}</li>\n"
                html_content += f"<li>💬 评论: {weibo.get('comments_count', 0):,}</li>\n"
                html_content += f"<li>❤️ 点赞: {weibo.get('attitudes_count', 0):,}</li>\n"
                if weibo.get('source'):
                    html_content += f"<li>📱 来源: {weibo.get('source', '')}</li>\n"
                html_content += "</ul>\n"
                html_content += "</div>\n"
                
                html_content += "</div>\n"
                html_content += "<hr>\n"
        
        # 生成最终HTML
        title = f"{self.user_name} - 微博内容报告 ({self.start_date} 至 {self.end_date})"
        final_html = html_template.format(title=title, content=html_content)
        
        # 写入HTML文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"✅ HTML报告已生成: {html_filename}")

    def create_complete_package(self, md_filename, html_filename):
        """创建完整的结果压缩包，包含reports和images文件夹"""
        package_name = f"{self.user_name}_{self.start_date.replace('-', '')}-{self.end_date.replace('-', '')}"
        zip_filename = os.path.join(self.output_dir, f"{package_name}.zip")
        
        print(f"📦 创建完整压缩包: {zip_filename}")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加reports文件夹
            if os.path.exists(md_filename):
                arcname = f"reports/{os.path.basename(md_filename)}"
                zipf.write(md_filename, arcname)
                print(f"   📄 添加Markdown报告: {arcname}")
            
            if os.path.exists(html_filename):
                arcname = f"reports/{os.path.basename(html_filename)}"
                zipf.write(html_filename, arcname)
                print(f"   📄 添加HTML报告: {arcname}")
            
            # 添加images文件夹
            if os.path.exists(self.images_dir):
                for root, dirs, files in os.walk(self.images_dir):
                    for file in files:
                        if file.endswith(('.jpg', '.png', '.gif', '.webp')):
                            file_path = os.path.join(root, file)
                            # 使用相对路径，保持images/文件名格式
                            arcname = f"images/{file}"
                            zipf.write(file_path, arcname)
                
                print(f"   🖼️ 添加图片文件: {self.stats['images_downloaded']} 张")
            
            # 修复报告中的图片路径为相对路径
            self.fix_image_paths_in_zip(zipf, md_filename, html_filename)
        
        print(f"✅ 完整压缩包已生成: {zip_filename}")
        return zip_filename
    
    def fix_image_paths_in_zip(self, zipf, md_filename, html_filename):
        """修复压缩包中报告文件的图片路径"""
        # 修复Markdown文件中的图片路径
        if os.path.exists(md_filename):
            with open(md_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 将相对路径改为压缩包内的路径
            content = re.sub(r'!\[(.*?)\]\(\.\./images/(.*?\.jpg)\)', r'![\1](images/\2)', content)
            
            # 写入修复后的文件到压缩包
            zipf.writestr(f"reports/{os.path.basename(md_filename)}", content)
        
        # 注意：HTML文件使用base64嵌入图片，不需要修复路径


def scrape_weibo_web(params, progress_callback=None):
    """Web接口调用的爬虫函数"""
    scraper = WebWeiboScraper(
        user_id=params['userId'],
        user_name=params['userName'],
        start_date=params['startDate'],
        end_date=params['endDate'],
        keywords=params.get('keywords', []),
        max_pages=params.get('maxPages', 10),
        request_delay=params.get('requestDelay', 2),
        output_dir="weibo_output"
    )
    
    # 爬取微博
    weibos = scraper.scrape_weibos(progress_callback)
    
    # 生成报告
    result = scraper.generate_reports(weibos)
    
    return result


if __name__ == "__main__":
    # 测试用例
    test_params = {
        'userId': '1317335037',
        'userName': '姜汝祥',
        'startDate': '2025-03-01',
        'endDate': '2025-09-01',
        'keywords': ['抖音', '创新'],  # 测试关键词筛选
        'maxPages': 3,
        'requestDelay': 2
    }
    
    result = scrape_weibo_web(test_params)
    print("测试完成:", result)