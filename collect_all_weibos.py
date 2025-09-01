#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜集指定时间范围内的所有微博 - 基于可工作的报告生成器扩展
"""

import ssl
import urllib.request
import json
import re
import os
import glob
from datetime import datetime
import codecs
import time
from config import WEIBO_USER_ID, USER_NAME, OUTPUT_DIR, START_DATE, END_DATE


def format_chinese_date(date_str):
    """将日期转换为中文格式"""
    try:
        # 处理微博的时间格式，如: "Thu Apr 24 18:05:55 +0800 2025"
        if any(day in date_str for day in ['Thu', 'Fri', 'Mon', 'Tue', 'Wed', 'Sat', 'Sun']):
            # 去掉时区信息
            date_str = re.sub(r'\s+\+\d{4}', '', date_str)
            # 解析时间
            dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
            return f"{dt.year}年{dt.month}月{dt.day}日"
        # 处理其他时间格式
        else:
            return date_str
    except:
        return date_str


def is_in_date_range(date_str, start_date, end_date):
    """检查日期是否在指定范围内"""
    try:
        if any(day in date_str for day in ['Thu', 'Fri', 'Mon', 'Tue', 'Wed', 'Sat', 'Sun']):
            date_str = re.sub(r'\s+\+\d{4}', '', date_str)
            dt = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            return start_dt <= dt <= end_dt
        return True  # 对于无法解析的时间，默认包含
    except:
        return True


def download_image(image_url, weibo_id, image_index, images_dir):
    """下载图片"""
    try:
        # 确保图片目录存在
        os.makedirs(images_dir, exist_ok=True)
        
        # 获取图片扩展名
        if '.jpg' in image_url:
            ext = 'jpg'
        elif '.png' in image_url:
            ext = 'png'
        elif '.gif' in image_url:
            ext = 'gif'
        else:
            ext = 'jpg'
        
        filename = f"{weibo_id}_{image_index}.{ext}"
        filepath = os.path.join(images_dir, filename)
        
        # 如果文件已存在，跳过下载
        if os.path.exists(filepath):
            return filepath
        
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
            'Referer': 'https://m.weibo.cn/',
        }
        
        req = urllib.request.Request(image_url, headers=headers)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        response = urllib.request.urlopen(req, timeout=15, context=ssl_context)
        
        with open(filepath, 'wb') as f:
            f.write(response.read())
        
        print(f"✅ 下载图片: {filename}")
        return filepath
        
    except Exception as e:
        print(f"❌ 下载图片失败: {e}")
        return None


def collect_all_weibos():
    """搜集所有微博"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'https://m.weibo.cn/u/{WEIBO_USER_ID}',
    }
    
    def decode_text(text):
        if not text:
            return ""
        try:
            if '\\u' in text:
                decoded = json.loads(f'"{text}"')
                return decoded
            return text
        except:
            return text
    
    def clean_html(text):
        if not text:
            return ""
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        return decode_text(text).strip()
    
    def get_full_text(weibo_id):
        """获取微博全文"""
        full_text_url = f"https://m.weibo.cn/statuses/extend?id={weibo_id}"
        try:
            req = urllib.request.Request(full_text_url, headers=headers)
            response = urllib.request.urlopen(req, timeout=15, context=ssl_context)
            content = response.read().decode('utf-8')
            data = json.loads(content)
            if data.get('ok') == 1:
                full_text = data.get('data', {}).get('longTextContent', '')
                if full_text:
                    return clean_html(full_text)
        except Exception as e:
            print(f"获取全文失败: {e}")
        return None
    
    all_weibos = []
    page = 1
    max_pages = 10  # 限制最大页数防止无限循环
    images_dir = f"{OUTPUT_DIR}/images"
    
    print(f"🚀 开始搜集 {USER_NAME} 的微博...")
    print(f"📅 时间范围: {START_DATE} 到 {END_DATE}")
    
    while page <= max_pages:
        print(f"\n📖 正在获取第 {page} 页...")
        
        # 获取微博列表
        url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={WEIBO_USER_ID}&containerid=107603{WEIBO_USER_ID}&page={page}"
        
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=30, context=ssl_context)
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
                        created_at = mblog.get('created_at', '')
                        
                        # 检查时间范围
                        if not is_in_date_range(created_at, START_DATE, END_DATE):
                            continue
                        
                        weibo_id = mblog.get('id', '')
                        mid = mblog.get('mid', '')
                        
                        # 获取文本
                        raw_text = mblog.get('text', '')
                        clean_text = clean_html(raw_text)
                        
                        # 检查是否需要获取全文
                        if mblog.get('isLongText', False) or '全文' in clean_text:
                            print(f"📝 获取微博 {weibo_id} 的全文...")
                            full_text = get_full_text(weibo_id)
                            if full_text:
                                clean_text = full_text
                                print(f"✅ 全文获取成功: {len(full_text)} 字符")
                        
                        weibo_data = {
                            'id': weibo_id,
                            'mid': mid,
                            'created_at': created_at,
                            'text': clean_text,
                            'source': clean_html(mblog.get('source', '')),
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
                                    # 下载图片
                                    download_image(pic_url, weibo_id, i, images_dir)
                        
                        # 处理转发内容
                        if 'retweeted_status' in mblog:
                            rt = mblog['retweeted_status']
                            rt_text = clean_html(rt.get('text', ''))
                            rt_id = rt.get('id', '')
                            
                            # 检查转发内容是否也有全文
                            if rt.get('isLongText', False) or '全文' in rt_text:
                                rt_full_text = get_full_text(rt_id)
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
                                        download_image(pic_url, weibo_id, f"rt_{i}", images_dir)
                        
                        all_weibos.append(weibo_data)
                        page_weibos += 1
            
            print(f"✅ 第 {page} 页获取到 {page_weibos} 条微博")
            
            if page_weibos == 0:
                print("📝 没有更多符合条件的微博")
                break
            
            page += 1
            time.sleep(2)  # 请求间隔
            
        except Exception as e:
            print(f"❌ 第 {page} 页获取失败: {e}")
            break
    
    print(f"\n🎉 搜集完成！总共获取到 {len(all_weibos)} 条微博")
    return all_weibos


def generate_complete_report(weibos):
    """生成完整报告"""
    # 获取已下载的图片
    image_files = glob.glob(f"{OUTPUT_DIR}/images/*.jpg")
    
    # 确保报告目录存在
    os.makedirs(f"{OUTPUT_DIR}/reports", exist_ok=True)
    
    # 生成文件名
    date_range = f"{START_DATE.replace('-', '')}-{END_DATE.replace('-', '')}"
    filename = f"{OUTPUT_DIR}/reports/{USER_NAME}_完整微博内容_{date_range}.md"
    
    print(f"📝 生成完整报告: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {USER_NAME} - 完整微博内容报告\n")
        f.write(f"**时间范围**: {START_DATE} 至 {END_DATE}\n\n")
        
        f.write("## 📊 数据统计\n\n")
        f.write(f"- **用户**: {USER_NAME}\n")
        f.write(f"- **微博总数**: {len(weibos)} 条\n")
        f.write(f"- **图片总数**: {len(image_files)} 张\n")
        f.write(f"- **报告生成**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("---\n\n")
        
        # 微博内容
        if weibos:
            f.write("## 📝 微博内容 (完整版)\n\n")
            
            for i, weibo in enumerate(weibos, 1):
                f.write(f"### 微博 {i}\n\n")
                
                # 基本信息 - 使用中文日期格式
                created_at = weibo.get('created_at', '')
                chinese_date = format_chinese_date(created_at)
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
                
                # 图片展示 - 直接显示图片
                if 'images' in weibo and weibo['images']:
                    for idx, img_url in enumerate(weibo['images'], 1):
                        # 查找对应的本地文件
                        weibo_id = weibo.get('id', '')
                        local_pattern = f"{OUTPUT_DIR}/images/{weibo_id}_{idx}.jpg"
                        if os.path.exists(local_pattern):
                            # 使用相对路径 - 从reports目录到images目录
                            relative_path = f"../images/{weibo_id}_{idx}.jpg"
                            f.write(f"![图片{idx}]({relative_path})\n\n")
                        
                        # 检查转发图片
                        rt_pattern = f"{OUTPUT_DIR}/images/{weibo_id}_rt_{idx}.jpg"
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
    
    print(f"✅ 完整报告已生成: {filename}")
    return filename


if __name__ == "__main__":
    # 搜集所有微博
    all_weibos = collect_all_weibos()
    
    # 生成完整报告
    if all_weibos:
        generate_complete_report(all_weibos)
    else:
        print("❌ 没有找到符合条件的微博")