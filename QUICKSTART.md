# 快速使用指南

## 🚀 一键启动

### Windows 用户
1. 双击 `scripts/install_dependencies.bat` 安装依赖
2. 双击 `scripts/run_tracker.bat` 启动程序

### 其他平台
```bash
# 安装依赖
pip install requests beautifulsoup4

# 运行程序
python scripts/website_tracker.py
```

## 📁 输出文件

程序运行后会生成3个文件：
- `website_results.txt` - 跳转结果
- `website_update_notice.txt` - 更新差异
- `website_tracker.log` - 运行日志

## ⚙️ 配置

编辑 `scripts/config.json` 修改设置：
- `max_index`: 处理的最大索引号（默认50）
- `min_delay`, `max_delay`: 请求间隔（秒）
- `max_retries`: 最大重试次数

## 🔄 断点续传

程序支持断点续传，中断后重启会自动从上次位置继续。

---
详细说明请查看 [README.md](README.md)
