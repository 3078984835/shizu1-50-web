# 网站追踪器 (Website Tracker)

一个用于跟踪网站跳转URL变化的Python工具，具备自动重试、进度保存和差异检测功能。

## ✨ 特性

- 🔄 **自动重试机制**：遇到网络错误或反爬机制时智能重试
- 📊 **进度保存**：支持断点续传，程序中断后可从上次位置继续
- 🔍 **差异检测**：自动对比本次与上次的结果，检测网站更新
- 📝 **统一输出格式**：所有输出文件采用相同的分行格式
- ⚡ **高效处理**：支持批量处理，可配置延迟和重试策略
- 🛡️ **反爬对策**：智能检测反爬机制并采用退避算法，支持腾讯视频、美团视频等平台

## 📁 输出文件

程序运行后会生成3个核心文件：

### 1. `website_tracker.log` - 运行日志
记录程序运行状态、错误信息和调试信息
```
2025-08-28 15:30:01,123 - INFO - 开始运行网站追踪器...
2025-08-28 15:30:02,456 - INFO - 处理 http://example.com/s/shizu1 (尝试 1/3)
```

### 2. `website_results.txt` - 跳转结果
记录所有网站的跳转信息，采用统一的分行格式：
```
=== 网站跳转结果记录 ===

时间戳: 2025-08-28 15:30:01
直连网站: http://tians.06kd.mlkj888.cn/s/shizu1
跳转网站: http://mtvod.meituan.net/save-video/example.mp4
shizu编号: shizu1
---
```

### 3. `website_update_notice.txt` - 更新差异
记录本次与上次运行的差异：
```
=== 网站更新差异记录 ===

==== 2025-08-28 15:45:30 检测到更新 ====

时间戳: 2025-08-28 15:45:30
直连网站: http://tians.06kd.mlkj888.cn/s/shizu5
跳转网站: http://new-url.com/video.mp4
shizu编号: shizu5
变化说明: 从 http://old-url.com/video.mp4 更新到 http://new-url.com/video.mp4
---
```

## � 项目结构

```
shizu/
├── README.md                    # 项目说明文档  
├── tracker_progress.json        # 运行进度记录
├── website_results.txt          # 跳转结果记录  
├── website_tracker.log          # 运行日志
├── website_update_notice.txt    # 更新差异记录
└── scripts/                     # 脚本目录
    ├── website_tracker.py       # 主程序
    ├── config.json              # 配置文件  
    ├── run_tracker.bat          # 启动脚本（Windows）
    ├── install_dependencies.bat # 依赖安装脚本
    ├── generate_report.py       # 报告生成工具  
    └── generate_report.bat      # 报告生成脚本
```

## �🚀 快速开始

### 环境要求
- Python 3.7+
- 依赖包：`requests`, `beautifulsoup4`

### 安装依赖
```bash
pip install requests beautifulsoup4
```

### 配置文件
创建 `scripts/config.json` 文件（可选，程序会使用默认配置）：
```json
{
    "base_url": "http://tians.06kd.mlkj888.cn/s/shizu",
    "min_index": 1,
    "max_index": 50,
    "min_delay": 5,
    "max_delay": 15,
    "results_file": "website_results.txt",
    "log_file": "website_tracker.log",
    "title_sample_rate": 5,
    "max_retries": 3,
    "retry_delay": 20,
    "anti_crawl_wait_min": 15,
    "anti_crawl_wait_max": 30
}
```

### 运行程序
```bash
# 直接运行主程序
python scripts/website_tracker.py

# 或使用批处理文件（Windows）
scripts/run_tracker.bat
```

## ⚙️ 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `base_url` | 基础URL模板 | `"http://tians.06kd.mlkj888.cn/s/shizu"` |
| `min_index` | 起始索引 | `1` |
| `max_index` | 结束索引 | `50` |
| `min_delay` | 最小延迟（秒） | `5` |
| `max_delay` | 最大延迟（秒） | `15` |
| `max_retries` | 最大重试次数 | `3` |
| `anti_crawl_wait_min` | 反爬等待最小时间 | `15` |
| `anti_crawl_wait_max` | 反爬等待最大时间 | `30` |

## 🔧 高级功能

### 1. 断点续传
程序会自动保存进度到 `tracker_progress.json`，中断后重启会从上次位置继续。

### 2. 智能重试
- 遇到网络错误时使用指数退避算法
- 检测到反爬机制时增加等待时间
- 达到最大重试次数后跳过该URL

### 3. 差异检测
- 自动对比本次和上次的结果
- 只记录成功跳转的URL变化
- 生成详细的更新报告

### 4. 安全限制
- 限制最大重试次数不超过3次
- 限制单次等待时间不超过30秒
- 使用随机用户代理避免检测

## 📊 监控和调试

### 进度监控
程序会每处理5个链接保存一次进度，并在日志中输出当前状态。

### 错误处理
所有异常都会被捕获并记录到日志文件中，程序不会因为单个URL失败而崩溃。

## 🔧 高级功能

### 1. 断点续传
程序会自动保存进度到 `tracker_progress.json`，中断后重启会从上次位置继续。

### 2. 智能重试
- 遇到网络错误时使用指数退避算法
- 检测到反爬机制时增加等待时间
- 达到最大重试次数后跳过该URL

### 3. 差异检测
- 自动对比本次和上次的结果
- 只记录成功跳转的URL变化
- 生成详细的更新报告

## 📁 文件结构

```
shizu/
├── README.md                          # 项目说明文档
├── website_results.txt                # 跳转结果记录
├── website_update_notice.txt          # 更新差异记录
├── website_tracker.log               # 运行日志
├── website_results_snapshot.json     # 结果快照（自动生成）
├── tracker_progress.json             # 进度文件（自动生成）
└── scripts/
    ├── config.json                    # 配置文件
    ├── website_tracker.py             # 主程序
    ├── run_tracker.bat               # 启动脚本（Windows）
    ├── install_dependencies.bat      # 依赖安装脚本
    ├── generate_report.py            # 报告生成工具
    └── generate_report.bat           # 报告生成脚本（Windows）
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

> **注意**：使用本工具时请遵守目标网站的robots.txt和使用条款，合理设置请求频率以避免对服务器造成负担。
