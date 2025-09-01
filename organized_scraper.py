#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组织化微博爬虫 - 所有输出文件保存到指定目录结构
"""

import ssl
import urllib.request
import urllib.parse
import json
import re
import os
import hashlib
from datetime import datetime, timedelta
import codecs


class OrganizedWeiboScraper:
    def __init__(self, output_base_dir="weibo_output"):
        # SSL设置
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.uid = "1317335037"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': f'https://m.weibo.cn/u/{self.uid}',
            'Connection': 'keep-alive',
        }
        
        # 创建输出目录结构
        self.output_base = output_base_dir
        self.reports_dir = os.path.join(self.output_base, "reports")
        self.images_dir = os.path.join(self.output_base, "images")
        self.data_dir = os.path.join(self.output_base, "data")
        
        # 创建所有必要的目录
        for directory in [self.output_base, self.reports_dir, self.images_dir, self.data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 创建目录: {directory}")

    def decode_text_properly(self, text):
        """正确解码Unicode文本"""
        if not text:
            return ""
        
        try:
            if isinstance(text, str):
                # 检查是否包含Unicode转义序列
                if '\\u' in text:
                    try:
                        decoded = json.loads(f'"{text}"')
                        return decoded
                    except:
                        try:
                            decoded = codecs.decode(text, 'unicode_escape')
                            return decoded
                        except:
                            pass
                return text
            return str(text)
        except Exception as e:
            return str(text) if text else ""

    def clean_html_and_decode(self, text):
        """清理HTML并解码"""
        if not text:
            return ""
        
        # 先清理HTML标签
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 解码Unicode
        text = self.decode_text_properly(text)
        
        # 清理HTML实体
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '…'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text.strip()

    def make_request(self, url, max_retries=3):
        """发送HTTP请求"""
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                response = urllib.request.urlopen(req, timeout=30, context=self.ssl_context)
                
                content_bytes = response.read()
                try:
                    content = content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = content_bytes.decode('gbk')
                    except UnicodeDecodeError:
                        content = content_bytes.decode('utf-8', errors='ignore')
                
                return content
                
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    
        return None

    def get_full_text(self, weibo_id):
        """获取微博全文"""
        full_text_url = f"https://m.weibo.cn/statuses/extend?id={weibo_id}"
        
        try:
            content = self.make_request(full_text_url)
            if content:
                data = json.loads(content)
                if data.get('ok') == 1:
                    full_text = data.get('data', {}).get('longTextContent', '')
                    if full_text:
                        return self.clean_html_and_decode(full_text)
        except Exception as e:
            print(f"  获取全文失败: {e}")
        
        return None

    def download_image(self, image_url, weibo_id, image_index):
        """下载图片到images目录"""
        try:
            # 生成文件名
            image_ext = image_url.split('.')[-1].split('?')[0]
            if not image_ext or image_ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                image_ext = 'jpg'
            
            filename = f"{weibo_id}_{image_index}.{image_ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            # 如果文件已存在，跳过下载
            if os.path.exists(filepath):
                return filename
            
            # 下载图片
            req = urllib.request.Request(image_url, headers={
                'User-Agent': self.headers['User-Agent'],
                'Referer': 'https://weibo.com/'
            })
            
            response = urllib.request.urlopen(req, timeout=30, context=self.ssl_context)
            
            with open(filepath, 'wb') as f:
                f.write(response.read())
            
            print(f"    ✅ 下载图片: images/{filename}")
            return filename
            
        except Exception as e:
            print(f"    ❌ 下载图片失败: {image_url} - {e}")
            return None

    def generate_weibo_url(self, weibo_id, mid=None):
        """生成微博链接"""
        if mid:
            return f"https://weibo.com/{self.uid}/{mid}"
        else:
            return f"https://m.weibo.cn/detail/{weibo_id}"

    def parse_weibo_date(self, date_str):
        """解析微博时间"""
        try:
            date_str = re.sub(r'\s+\+\d{4}', '', date_str)
            
            months = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            parts = date_str.split()
            if len(parts) >= 5:
                month_str = parts[1]
                day = int(parts[2])
                time_str = parts[3]
                year = int(parts[4])
                
                if month_str in months:
                    month = months[month_str]
                    hour, minute, second = map(int, time_str.split(':'))
                    return datetime(year, month, day, hour, minute, second)
        except:
            pass
        
        return None

    def is_target_period(self, post_date):
        """检查是否在目标时间范围"""
        if not post_date:
            return False
        
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 9, 30, 23, 59, 59)
        return start_date <= post_date <= end_date

    def extract_weibo(self, mblog):
        """提取微博数据"""
        try:
            # 获取基本信息
            weibo_id = mblog.get('id', '')
            mid = mblog.get('mid', '')
            
            # 解析时间
            created_at = mblog.get('created_at', '')
            post_date = self.parse_weibo_date(created_at)
            
            if not self.is_target_period(post_date):
                return None
            
            # 获取文本内容
            raw_text = mblog.get('text', '')
            clean_text = self.clean_html_and_decode(raw_text)
            
            # 检查是否有全文
            is_long_text = mblog.get('isLongText', False)
            if is_long_text or '全文' in clean_text:
                print(f"    🔍 检测到长文本，获取全文...")
                full_text = self.get_full_text(weibo_id)
                if full_text:
                    clean_text = full_text
                    print(f"    ✅ 获取全文成功: {len(full_text)} 字符")
            
            weibo = {
                'id': weibo_id,
                'mid': mid,
                'created_at': created_at,
                'parsed_date': post_date,
                'formatted_date': post_date.strftime('%Y-%m-%d %H:%M:%S') if post_date else '',
                'text': clean_text,
                'source': self.clean_html_and_decode(mblog.get('source', '')),
                'reposts_count': mblog.get('reposts_count', 0),
                'comments_count': mblog.get('comments_count', 0),
                'attitudes_count': mblog.get('attitudes_count', 0),
                'url': self.generate_weibo_url(weibo_id, mid),
            }
            
            # 处理图片
            if 'pics' in mblog and mblog['pics']:
                print(f"    🖼️ 发现 {len(mblog['pics'])} 张图片，开始下载...")
                weibo['images'] = []
                for idx, pic in enumerate(mblog['pics'], 1):
                    pic_url = pic.get('large', {}).get('url', '') or pic.get('url', '')
                    if pic_url:
                        # 下载图片
                        local_filename = self.download_image(pic_url, weibo_id, idx)
                        weibo['images'].append({
                            'url': pic_url,
                            'local_file': local_filename
                        })
            
            # 处理转发内容
            if 'retweeted_status' in mblog:
                rt = mblog['retweeted_status']
                rt_text = self.clean_html_and_decode(rt.get('text', ''))
                
                # 检查转发内容是否也有全文
                rt_id = rt.get('id', '')
                if rt.get('isLongText', False) or '全文' in rt_text:
                    print(f"    🔍 转发内容检测到长文本...")
                    rt_full_text = self.get_full_text(rt_id)
                    if rt_full_text:
                        rt_text = rt_full_text
                
                weibo['retweeted'] = {
                    'user_name': rt.get('user', {}).get('screen_name', ''),
                    'text': rt_text,
                    'id': rt_id,
                }
                
                # 处理转发内容的图片
                if 'pics' in rt and rt['pics']:
                    print(f"    🖼️ 转发内容发现 {len(rt['pics'])} 张图片...")
                    if 'images' not in weibo:
                        weibo['images'] = []
                    
                    for idx, pic in enumerate(rt['pics'], len(weibo.get('images', [])) + 1):
                        pic_url = pic.get('large', {}).get('url', '') or pic.get('url', '')
                        if pic_url:
                            local_filename = self.download_image(pic_url, f"{weibo_id}_rt", idx)
                            weibo['images'].append({
                                'url': pic_url,
                                'local_file': local_filename,
                                'from_retweet': True
                            })
            
            return weibo
            
        except Exception as e:
            print(f"  ❌ 提取微博失败: {e}")
            return None

    def scrape_all_pages(self):
        """爬取所有页面"""
        container_id = "1076031317335037"
        all_weibos = []
        
        print(f"🔍 开始爬取用户 {self.uid} 的完整微博内容...")
        
        for page in range(1, 11):  # 先爬10页测试
            print(f"\n📄 爬取第 {page} 页...")
            
            url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={self.uid}&containerid={container_id}&page={page}"
            
            content = self.make_request(url)
            if not content:
                print(f"❌ 第 {page} 页请求失败")
                break
            
            try:
                data = json.loads(content)
                
                if data.get('ok') != 1:
                    print(f"❌ API错误: {data.get('msg', '未知')}")
                    break
                
                cards = data.get('data', {}).get('cards', [])
                if not cards:
                    print(f"⚠️ 第 {page} 页无数据")
                    break
                
                page_weibos = []
                for card in cards:
                    if card.get('card_type') == 9:
                        mblog = card.get('mblog')
                        if mblog:
                            print(f"  🔄 处理微博 ID: {mblog.get('id', '')}")
                            weibo = self.extract_weibo(mblog)
                            if weibo:
                                page_weibos.append(weibo)
                                print(f"    ✅ 成功: {weibo['formatted_date']}")
                                print(f"    📝 内容: {weibo['text'][:100]}...")
                
                if page_weibos:
                    all_weibos.extend(page_weibos)
                    print(f"📊 第 {page} 页获取 {len(page_weibos)} 条微博")
                else:
                    print(f"⚠️ 第 {page} 页无目标微博")
                
                import time
                time.sleep(3)  # 页面间延迟
                
            except Exception as e:
                print(f"❌ 处理第 {page} 页失败: {e}")
                break
        
        return all_weibos

    def save_data_json(self, weibos, filename):
        """保存原始数据为JSON格式到data目录"""
        filepath = os.path.join(self.data_dir, filename)
        
        data = {
            'user_id': self.uid,
            'user_name': '姜汝祥-',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(weibos),
            'weibos': weibos
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 原始数据已保存: data/{filename}")

    def generate_complete_markdown(self, weibos):
        """生成完整的Markdown到reports目录"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"姜汝祥_完整微博报告_{timestamp}.md"
        filepath = os.path.join(self.reports_dir, filename)
        
        # 按时间排序
        weibos.sort(key=lambda x: x.get('parsed_date', datetime.min), reverse=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 姜汝祥- 2025年3-9月完整微博内容\n\n")
            f.write("*✅ 包含全文展开、图片下载、微博链接的完整版本*\n\n")
            
            f.write("## 📁 文件组织结构\n\n")
            f.write("```\n")
            f.write(f"{self.output_base}/\n")
            f.write("├── reports/           # 微博报告文档\n")
            f.write("├── images/            # 下载的图片文件\n")
            f.write("├── data/              # 原始JSON数据\n")
            f.write("└── ...\n")
            f.write("```\n\n")
            
            f.write("## 📊 数据统计\n\n")
            f.write(f"- **用户**: 姜汝祥- (职场博主)\n")
            f.write(f"- **微博总数**: {len(weibos)} 条\n")
            f.write(f"- **时间范围**: 2025年3月-9月\n")
            f.write(f"- **数据获取**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **特色功能**: ✅ 全文展开 ✅ 图片下载 ✅ 微博链接\n\n")
            
            # 统计信息
            if weibos:
                total_reposts = sum(w.get('reposts_count', 0) for w in weibos)
                total_comments = sum(w.get('comments_count', 0) for w in weibos)
                total_likes = sum(w.get('attitudes_count', 0) for w in weibos)
                total_images = sum(len(w.get('images', [])) for w in weibos)
                
                f.write("### 📈 统计数据\n")
                f.write(f"- **总转发数**: {total_reposts:,}\n")
                f.write(f"- **总评论数**: {total_comments:,}\n") 
                f.write(f"- **总点赞数**: {total_likes:,}\n")
                f.write(f"- **总图片数**: {total_images} 张\n")
                f.write(f"- **平均互动**: 转发{total_reposts/len(weibos):.1f} 评论{total_comments/len(weibos):.1f} 点赞{total_likes/len(weibos):.1f}\n\n")
                
                f.write("---\n\n")
                f.write("## 📝 微博内容\n\n")
                
                for i, weibo in enumerate(weibos, 1):
                    f.write(f"### 第 {i} 条微博\n\n")
                    
                    # 基本信息
                    f.write(f"**🕒 发布时间**: {weibo.get('formatted_date')}\n")
                    f.write(f"**🔗 微博链接**: {weibo.get('url')}\n")
                    f.write(f"**🆔 微博ID**: {weibo.get('id')}\n\n")
                    
                    # 完整内容
                    text = weibo.get('text', '').strip()
                    if text:
                        f.write(f"**📄 完整内容**:\n\n{text}\n\n")
                    
                    # 转发内容
                    if 'retweeted' in weibo:
                        rt = weibo['retweeted']
                        f.write(f"**🔄 转发内容**:\n")
                        f.write(f"> **@{rt.get('user_name', '')}**: {rt.get('text', '')}\n\n")
                    
                    # 图片
                    if 'images' in weibo and weibo['images']:
                        f.write(f"**🖼️ 图片** ({len(weibo['images'])} 张):\n\n")
                        for idx, img in enumerate(weibo['images'], 1):
                            f.write(f"{idx}. **原链接**: {img['url']}\n")
                            if img.get('local_file'):
                                f.write(f"   **本地文件**: `../images/{img['local_file']}`\n")
                                # 如果是Markdown支持的图片格式，直接嵌入
                                if img['local_file'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                    f.write(f"   ![图片{idx}](../images/{img['local_file']})\n")
                            if img.get('from_retweet'):
                                f.write(f"   *（来自转发内容）*\n")
                            f.write("\n")
                    
                    # 互动数据
                    f.write(f"**📊 互动数据**:\n")
                    f.write(f"- 🔄 转发: {weibo.get('reposts_count', 0):,}\n")
                    f.write(f"- 💬 评论: {weibo.get('comments_count', 0):,}\n")
                    f.write(f"- ❤️ 点赞: {weibo.get('attitudes_count', 0):,}\n")
                    
                    # 来源
                    if weibo.get('source'):
                        f.write(f"- 📱 来源: {weibo['source']}\n")
                    
                    f.write(f"\n---\n\n")
            
            else:
                f.write("⚠️ 未获取到微博内容\n")
        
        print(f"📄 报告已生成: reports/{filename}")
        return filename

    def run(self):
        """主运行函数"""
        print("🚀 启动组织化微博爬虫...")
        print("🎯 功能: 全文+图片下载+微博链接+目录组织")
        print(f"📁 输出目录: {self.output_base}/")
        print("=" * 60)
        
        weibos = self.scrape_all_pages()
        
        print(f"\n📊 爬取完成: {len(weibos)} 条微博")
        
        if weibos:
            print("\n💾 保存数据文件...")
            
            # 保存JSON数据
            json_filename = f"weibo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.save_data_json(weibos, json_filename)
            
            # 生成Markdown报告
            report_filename = self.generate_complete_markdown(weibos)
            
            # 统计
            total_images = sum(len(w.get('images', [])) for w in weibos)
            
            print(f"\n✅ 任务完成!")
            print(f"📁 输出目录: {self.output_base}/")
            print(f"📄 报告文件: reports/{report_filename.split('/')[-1]}")
            print(f"💾 数据文件: data/{json_filename}")
            print(f"📊 微博数量: {len(weibos)} 条")
            print(f"🖼️ 图片下载: {total_images} 张 (保存在 images/ 目录)")
            
            return {
                'output_dir': self.output_base,
                'report_file': report_filename,
                'data_file': os.path.join(self.data_dir, json_filename),
                'weibo_count': len(weibos),
                'image_count': total_images
            }
        else:
            print("❌ 未获取到微博内容")
            return None


def main():
    # 可以自定义输出目录名称
    scraper = OrganizedWeiboScraper("weibo_output")
    result = scraper.run()
    return result


if __name__ == "__main__":
    main()