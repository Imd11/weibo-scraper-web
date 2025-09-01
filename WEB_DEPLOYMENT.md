# 微博内容爬取工具 - Web版部署指南

## 🌟 项目概述

这是一个功能完整的Web版微博内容爬取工具，具有以下特点：

### ✨ 核心功能
- 🎯 **用户友好界面** - 美观的Web界面，无需命令行操作
- 🔍 **关键词筛选** - 支持多关键词筛选，精准定位目标内容
- 📅 **时间范围设置** - 灵活的日期范围选择
- 📝 **全文展开** - 自动获取微博完整内容
- 🖼️ **图片下载** - 自动下载所有相关图片
- 📊 **实时进度** - 实时显示爬取进度
- 📄 **多格式输出** - 支持Markdown、HTML格式和图片压缩包

### 🏗️ 技术架构
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **后端**: Python Flask
- **爬取引擎**: 自定义微博API爬虫
- **文件处理**: 自动图片下载和压缩

## 🚀 快速启动 (本地运行)

### 1. 环境要求
- Python 3.7+
- 网络连接 (能访问微博)

### 2. 一键启动
```bash
python3 start_web.py
```

启动后会自动：
- 安装依赖包
- 启动Web服务器
- 打开浏览器访问 http://localhost:5000

### 3. 手动启动 (可选)
```bash
# 安装依赖
pip install -r requirements_web.txt

# 启动服务器
python3 app.py
```

## 🌐 Web服务器部署

### 方案一：简单部署 (适合个人使用)

1. **上传项目文件到服务器**
```bash
# 上传整个项目目录
scp -r weibo_scraper/ user@your-server:/path/to/
```

2. **服务器上安装依赖**
```bash
cd /path/to/weibo_scraper/
pip3 install -r requirements_web.txt
```

3. **启动服务**
```bash
# 后台运行
nohup python3 app.py > server.log 2>&1 &

# 或使用screen
screen -S weibo_scraper
python3 app.py
# Ctrl+A+D 退出screen
```

4. **配置防火墙** (如果需要)
```bash
# 开放5000端口
sudo ufw allow 5000
```

### 方案二：生产部署 (使用Gunicorn)

1. **安装Gunicorn**
```bash
pip3 install gunicorn
```

2. **创建Gunicorn配置**
```python
# gunicorn_config.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 300
max_requests = 1000
preload_app = True
```

3. **启动Gunicorn服务**
```bash
gunicorn -c gunicorn_config.py app:app
```

4. **配置Nginx反向代理** (可选)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 增大上传文件限制
    client_max_body_size 100M;
}
```

### 方案三：Docker部署

1. **创建Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements_web.txt .
RUN pip install -r requirements_web.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

2. **构建和运行**
```bash
# 构建镜像
docker build -t weibo-scraper .

# 运行容器
docker run -d -p 5000:5000 --name weibo-scraper-app weibo-scraper
```

## 🎨 界面特性

### 美观设计
- **现代化UI** - 渐变背景、圆角卡片、平滑动画
- **响应式布局** - 支持桌面和移动设备
- **直观操作** - 表单验证、实时提示
- **视觉反馈** - 加载动画、进度条、状态指示

### 功能区域
1. **用户设置区** - 微博用户ID、用户名配置
2. **时间范围区** - 开始和结束日期选择
3. **关键词筛选区** - 多关键词标签管理
4. **高级设置区** - 页数限制、请求间隔
5. **进度显示区** - 实时进度条和状态信息
6. **结果展示区** - 统计数据和下载链接

## 🔧 使用说明

### 1. 基本操作
1. **填写目标用户信息**
   - 用户ID: 从微博URL获取 (如 weibo.com/u/1234567890)
   - 用户名: 用于文件命名

2. **设置时间范围**
   - 选择开始和结束日期
   - 支持长时间跨度爬取

3. **配置关键词筛选** (可选)
   - 输入关键词后按回车添加
   - 支持多个关键词
   - 留空表示不筛选

4. **调整高级设置**
   - 最大页数: 控制爬取范围
   - 请求间隔: 避免频率限制

5. **开始爬取**
   - 点击"开始爬取微博内容"
   - 实时查看进度和状态
   - 完成后下载结果文件

### 2. 结果文件
- **Markdown文件** - 适合阅读和编辑
- **HTML文件** - 包含嵌入图片，浏览器直接打开
- **图片压缩包** - 所有下载的图片文件

## ⚙️ 配置选项

### 环境变量配置
```bash
# 服务器配置
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_DEBUG=False

# 爬取配置
export MAX_PAGES_LIMIT=20
export REQUEST_DELAY_MIN=1
export REQUEST_DELAY_MAX=10
```

### 自定义设置
修改 `app.py` 中的配置：
```python
# 最大任务数量
MAX_CONCURRENT_TASKS = 5

# 任务超时时间 (秒)
TASK_TIMEOUT = 1800

# 文件保存路径
OUTPUT_BASE_DIR = "weibo_output"
```

## 🔒 安全注意事项

### 1. 访问控制
- 建议在内网或VPN环境下使用
- 可添加用户认证功能
- 限制访问IP地址

### 2. 资源限制
- 设置合理的最大页数限制
- 控制并发任务数量
- 定期清理输出文件

### 3. 合规使用
- 遵守微博使用条款
- 仅用于学习研究目的
- 不要爬取敏感或私人信息

## 🐛 常见问题

### Q: 服务器启动失败？
A: 检查端口是否被占用，Python版本是否符合要求

### Q: 爬取过程中断？
A: 检查网络连接，调整请求间隔时间

### Q: 图片下载失败？
A: 微博图片服务器可能有访问限制，属于正常情况

### Q: 关键词筛选不生效？
A: 确保关键词已正确添加，检查是否有拼写错误

## 📈 性能优化

### 1. 服务器优化
- 使用SSD存储
- 增加内存配置
- 优化网络连接

### 2. 代码优化
- 异步处理下载任务
- 缓存重复请求
- 压缩输出文件

### 3. 用户体验
- 添加WebSocket实时通信
- 优化前端资源加载
- 增加离线缓存功能

## 📝 更新日志

### v1.0.0 (2025-09-01)
- ✨ 首次发布Web版本
- 🎨 完整的用户界面设计
- 🔍 多关键词筛选功能
- 📊 实时进度显示
- 📁 多格式文件输出
- 🌐 支持Web服务器部署

---

**开发完成时间**: 2025年9月1日  
**项目状态**: ✅ 生产就绪  
**维护状态**: 🔄 持续更新