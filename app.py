#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web服务器 - 微博内容爬取工具
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import threading
import queue
import os
import json
import time
from web_scraper import scrape_weibo_web
import traceback

app = Flask(__name__)
app.secret_key = 'weibo_scraper_secret_key_2025'

# 全局变量存储任务状态
task_status = {}
task_results = {}

class ProgressTracker:
    """进度跟踪器"""
    def __init__(self, task_id):
        self.task_id = task_id
        self.progress = 0
        self.status = "初始化中..."
    
    def update(self, progress, status):
        self.progress = progress
        self.status = status
        task_status[self.task_id] = {
            'progress': progress,
            'status': status,
            'completed': progress >= 100
        }

def background_scrape(task_id, params):
    """后台爬取任务"""
    progress_tracker = ProgressTracker(task_id)
    
    try:
        # 更新进度回调函数
        def progress_callback(progress, status):
            progress_tracker.update(progress, status)
        
        # 执行爬取
        progress_tracker.update(5, "开始爬取微博内容...")
        result = scrape_weibo_web(params, progress_callback)
        
        # 保存结果
        task_results[task_id] = {
            'success': True,
            'data': result
        }
        
        progress_tracker.update(100, "爬取完成！")
        
    except Exception as e:
        # 错误处理
        error_msg = str(e)
        print(f"爬取失败: {error_msg}")
        print(traceback.format_exc())
        
        task_results[task_id] = {
            'success': False,
            'error': error_msg
        }
        
        progress_tracker.update(0, f"爬取失败: {error_msg}")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def start_scrape():
    """开始爬取任务"""
    try:
        # 获取请求参数
        params = request.get_json()
        
        # 参数验证
        required_fields = ['userId', 'userName', 'startDate', 'endDate']
        for field in required_fields:
            if not params.get(field):
                return jsonify({'error': f'缺少必要参数: {field}'}), 400
        
        # 生成任务ID
        task_id = f"task_{int(time.time() * 1000)}"
        
        # 初始化任务状态
        task_status[task_id] = {
            'progress': 0,
            'status': '任务已创建，等待开始...',
            'completed': False
        }
        
        # 启动后台任务
        thread = threading.Thread(
            target=background_scrape,
            args=(task_id, params)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '任务已启动，正在后台处理...'
        })
        
    except Exception as e:
        return jsonify({'error': f'启动任务失败: {str(e)}'}), 500

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """获取任务进度"""
    if task_id not in task_status:
        return jsonify({'error': '任务不存在'}), 404
    
    status = task_status[task_id]
    
    # 如果任务完成，返回结果
    if status['completed'] and task_id in task_results:
        result = task_results[task_id]
        if result['success']:
            return jsonify({
                'progress': 100,
                'status': '完成',
                'completed': True,
                'result': result['data']
            })
        else:
            return jsonify({
                'progress': 0,
                'status': f"失败: {result['error']}",
                'completed': True,
                'error': result['error']
            })
    
    return jsonify(status)

@app.route('/download/<path:filename>')
def download_file(filename):
    """文件下载"""
    try:
        # 安全检查：只允许下载特定目录下的文件
        if not filename.startswith(('weibo_output/reports/', 'weibo_output/images.zip', 'weibo_output/')):
            return jsonify({'error': '不允许下载该文件'}), 403
        
        # 检查文件是否存在
        if not os.path.exists(filename):
            return jsonify({'error': '文件不存在'}), 404
        
        # 获取文件目录和文件名
        directory = os.path.dirname(filename)
        basename = os.path.basename(filename)
        
        return send_from_directory(directory, basename, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    return send_from_directory('static', filename)

@app.route('/api/test')
def api_test():
    """API测试接口"""
    return jsonify({
        'status': 'ok',
        'message': '微博爬虫API正常运行',
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

# 确保目录存在（用于本地和部署环境）
def ensure_directories():
    try:
        if not os.path.exists('templates'):
            os.makedirs('templates')
        if not os.path.exists('static'):
            os.makedirs('static')
        if not os.path.exists('weibo_output'):
            os.makedirs('weibo_output')
        if not os.path.exists('weibo_output/reports'):
            os.makedirs('weibo_output/reports')
        if not os.path.exists('weibo_output/images'):
            os.makedirs('weibo_output/images')
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")

# 初始化目录
ensure_directories()

# 启动开发服务器的配置
if __name__ == '__main__':
    print("🚀 微博内容爬取工具 Web服务启动中...")
    print("📝 访问地址: http://localhost:5001")
    print("🔧 开发模式: 启用")
    
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5001,       # 改为5001端口
        debug=True,      # 开发模式
        threaded=True    # 支持多线程
    )