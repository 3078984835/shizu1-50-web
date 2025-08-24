import os
import json
import pandas as pd
from datetime import datetime

def generate_report():
    """生成网站追踪报告"""
    # 检查结果文件是否存在
    results_file = "website_results.txt"
    if not os.path.exists(results_file):
        print("结果文件不存在，无法生成报告。")
        return
    
    # 加载数据
    try:
        df = pd.read_csv(results_file)
        
        # 基本统计
        total_urls = len(df)
        successful = df[df['状态'] == '成功'].shape[0]
        failed = df[df['状态'] == '失败'].shape[0]
        retries = df[df['状态'] == '需要重试'].shape[0]
        errors = df[df['状态'] == '出错'].shape[0]
        skipped = df[df['状态'] == '跳过'].shape[0]
        
        # 计算成功率
        success_rate = (successful / total_urls) * 100 if total_urls > 0 else 0
        
        # 获取追踪的日期范围
        if not df.empty:
            start_date = pd.to_datetime(df['时间戳']).min()
            end_date = pd.to_datetime(df['时间戳']).max()
            date_range = f"{start_date.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_date.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            date_range = "无数据"
        
        # 生成报告
        report = f"""
网站追踪报告 (生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
======================================================

追踪日期范围: {date_range}

总体统计:
  - 总链接数: {total_urls}
  - 成功访问: {successful} ({success_rate:.2f}%)
  - 访问失败: {failed}
  - 需要重试: {retries}
  - 发生错误: {errors}
  - 已跳过: {skipped}

详细统计:
  - 链接范围: {df['链接编号'].min()} 到 {df['链接编号'].max()}
"""
        
        # 将报告写入文件
        report_file = "tracking_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"报告已生成: {report_file}")
        
    except Exception as e:
        print(f"生成报告时出错: {e}")

if __name__ == "__main__":
    generate_report()
