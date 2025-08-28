#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站追踪器 - 重构版本
功能：跟踪网站跳转URL变化，生成统一格式的输出文件
作者：AI Assistant
日期：2025-08-28
"""

import requests
import time
import random
import os
import json
import sys
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class TrackerConfig:
    """追踪器配置类"""
    base_url: str
    min_index: int
    max_index: int
    min_delay: int
    max_delay: int
    results_file: str
    log_file: str
    title_sample_rate: int
    max_retries: int
    retry_delay: int
    anti_crawl_wait_min: int
    anti_crawl_wait_max: int


@dataclass
class ProcessResult:
    """处理结果类"""
    timestamp: str
    shizu_id: str
    original_url: str
    redirect_url: str
    status: str
    message: Optional[str] = None


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "base_url": "http://tians.06kd.mlkj888.cn/s/shizu",
        "min_index": 1,
        "max_index": 50,
        "min_delay": 10,
        "max_delay": 30,
        "results_file": "website_results.txt",
        "log_file": "website_tracker.log",
        "title_sample_rate": 5,
        "max_retries": 3,
        "retry_delay": 60,
        "anti_crawl_wait_min": 120,
        "anti_crawl_wait_max": 300
    }
    
    @staticmethod
    def load_config(config_path: str = "config.json") -> TrackerConfig:
        """加载配置文件"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, config_path)
            
            with open(full_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # 限制某些参数的最大值以确保安全
            config_data["max_retries"] = min(config_data.get("max_retries", 3), 3)
            config_data["retry_delay"] = min(config_data.get("retry_delay", 20), 30)
            config_data["anti_crawl_wait_min"] = min(config_data.get("anti_crawl_wait_min", 15), 15)
            config_data["anti_crawl_wait_max"] = min(config_data.get("anti_crawl_wait_max", 30), 30)
            
            return TrackerConfig(**config_data)
            
        except Exception as e:
            logging.warning(f"无法加载配置文件: {e}，使用默认配置")
            return TrackerConfig(**ConfigManager.DEFAULT_CONFIG)


class NetworkUtils:
    """网络工具类"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """获取随机用户代理"""
        return random.choice(NetworkUtils.USER_AGENTS)
    
    @staticmethod
    def get_redirect_url(url: str) -> Optional[str]:
        """获取URL重定向后的最终URL"""
        try:
            headers = {
                "User-Agent": NetworkUtils.get_random_user_agent(),
                "Referer": "http://tians.06kd.mlkj888.cn/",
            }
            
            response = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
            
            # 处理HTTP重定向
            if 300 <= response.status_code < 400:
                redirect_url = response.headers.get('Location')
                logging.info(f"重定向URL: {redirect_url}")
                
                # 检查反爬机制
                if redirect_url and "v.qq.com/txp/iframe/player.html" in redirect_url:
                    logging.warning("检测到反爬机制！")
                    return "ANTI_CRAWL_DETECTED"
                
                # 处理相对URL
                if redirect_url and not redirect_url.startswith('http'):
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    redirect_url = base_url + redirect_url
                
                return redirect_url
            
            # 处理Meta刷新重定向
            redirect_url = NetworkUtils._parse_meta_refresh(response.text)
            if redirect_url:
                logging.info(f"Meta刷新重定向: {redirect_url}")
                if not redirect_url.startswith('http'):
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    redirect_url = base_url + redirect_url
                return redirect_url
            
            logging.info(f"没有找到重定向，状态码: {response.status_code}")
            return url
            
        except Exception as e:
            logging.error(f"获取重定向URL时出错: {e}")
            return None
    
    @staticmethod
    def _parse_meta_refresh(html_content: str) -> Optional[str]:
        """解析Meta刷新重定向"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            meta_refresh = soup.find('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'refresh'})
            
            if meta_refresh and 'content' in meta_refresh.attrs:
                content = meta_refresh['content']
                if 'url=' in content.lower():
                    return content.split('url=', 1)[1].strip()
        except Exception:
            pass
        return None
    
    @staticmethod
    def get_page_title(url: str) -> str:
        """获取页面标题"""
        try:
            headers = {"User-Agent": NetworkUtils.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "无标题"
            return title.strip()
        except Exception as e:
            logging.error(f"获取页面标题时出错: {e}")
            return "获取标题失败"


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def ensure_file_exists(filepath: str, header: str):
        """确保文件存在，如果不存在则创建"""
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{header}\n\n")
    
    @staticmethod
    def write_result(filepath: str, result: ProcessResult):
        """写入处理结果到文件"""
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"时间戳: {result.timestamp}\n")
            f.write(f"直连网站: {result.original_url}\n")
            f.write(f"跳转网站: {result.redirect_url}\n")
            f.write(f"shizu编号: {result.shizu_id}\n")
            if result.message:
                f.write(f"备注: {result.message}\n")
            f.write("---\n")
    
    @staticmethod
    def load_progress(progress_file: str = "tracker_progress.json") -> Optional[Dict]:
        """加载处理进度"""
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"已加载进度: 上次处理到 {data.get('last_index', 'unknown')}")
                return data
        except Exception as e:
            logging.error(f"加载进度时出错: {e}")
        return None
    
    @staticmethod
    def save_progress(progress_file: str, current_index: int, consecutive_failures: int):
        """保存处理进度"""
        data = {
            "last_index": current_index,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "consecutive_failures": consecutive_failures
        }
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"进度已保存: 当前处理到 shizu{current_index}")
        except Exception as e:
            logging.error(f"保存进度时出错: {e}")


class ResultAnalyzer:
    """结果分析器"""
    
    @staticmethod
    def load_results_from_file(filepath: str) -> Dict[str, str]:
        """从结果文件中加载最新结果"""
        result_map = {}
        if not os.path.exists(filepath):
            return result_map
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            records = content.split('---')
            for record in records:
                record = record.strip()
                if not record or '时间戳:' not in record:
                    continue
                
                shizu_id, redirect_url = None, None
                for line in record.split('\n'):
                    line = line.strip()
                    if line.startswith('shizu编号:'):
                        shizu_id = line.split(':', 1)[1].strip()
                    elif line.startswith('跳转网站:'):
                        redirect_url = line.split(':', 1)[1].strip()
                
                # 只记录成功跳转的结果
                if (shizu_id and redirect_url and 
                    redirect_url not in ['触发反爬机制', '获取失败', '处理出错', '超过最大重试次数']):
                    result_map[shizu_id] = redirect_url
                    
        except Exception as e:
            logging.error(f"读取结果文件时出错: {e}")
            
        return result_map
    
    @staticmethod
    def compare_results(old_results: Dict[str, str], new_results: Dict[str, str]) -> List[Tuple[str, str, str]]:
        """比较新旧结果，找出变化的网站"""
        updated_sites = []
        for shizu_id, new_url in new_results.items():
            old_url = old_results.get(shizu_id)
            if old_url and old_url != new_url:
                updated_sites.append((shizu_id, old_url, new_url))
        return updated_sites


class WebsiteTracker:
    """网站追踪器主类"""
    
    def __init__(self, config: TrackerConfig):
        self.config = config
        self.retry_counts = {}
        self.consecutive_failures = 0
        self._setup_logging()
        
        # 确保必要文件存在
        FileManager.ensure_file_exists(self.config.results_file, "=== 网站跳转结果记录 ===")
        
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _create_result(self, shizu_id: str, original_url: str, redirect_url: str, status: str, message: str = None) -> ProcessResult:
        """创建处理结果对象"""
        return ProcessResult(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            shizu_id=shizu_id,
            original_url=original_url,
            redirect_url=redirect_url,
            status=status,
            message=message
        )
    
    def _wait_with_backoff(self, base_delay: float, multiplier: float = 1.0):
        """带退避算法的等待"""
        delay = min(base_delay * multiplier, 30.0)  # 最大等待30秒
        logging.info(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def process_single_url(self, index: int) -> bool:
        """处理单个URL，返回是否成功"""
        url = f"{self.config.base_url}{index}"
        shizu_id = f"shizu{index}"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查重试次数
        retry_count = self.retry_counts.get(index, 0)
        if retry_count >= self.config.max_retries:
            logging.warning(f"已达到最大重试次数 ({self.config.max_retries}) 对于 {shizu_id}，跳过...")
            result = self._create_result(shizu_id, url, "超过最大重试次数", "skipped")
            FileManager.write_result(self.config.results_file, result)
            return True  # 跳过算作处理完成
        
        try:
            logging.info(f"处理 {url} (尝试 {retry_count + 1}/{self.config.max_retries})")
            redirect_url = NetworkUtils.get_redirect_url(url)
            
            if redirect_url == "ANTI_CRAWL_DETECTED":
                return self._handle_anti_crawl(index, url, shizu_id)
            elif redirect_url:
                return self._handle_success(index, url, shizu_id, redirect_url)
            else:
                return self._handle_failure(index, url, shizu_id, "获取失败")
                
        except Exception as e:
            logging.error(f"处理URL时出错: {e}")
            return self._handle_failure(index, url, shizu_id, "处理出错")
    
    def _handle_anti_crawl(self, index: int, url: str, shizu_id: str) -> bool:
        """处理反爬机制"""
        self.consecutive_failures += 1
        self.retry_counts[index] = self.retry_counts.get(index, 0) + 1
        
        logging.warning(f"检测到反爬机制，连续失败: {self.consecutive_failures}")
        
        result = self._create_result(shizu_id, url, "触发反爬机制", "retry_needed")
        FileManager.write_result(self.config.results_file, result)
        
        # 使用退避算法等待
        wait_factor = min(self.consecutive_failures, 1.5)
        base_delay = random.uniform(self.config.anti_crawl_wait_min, self.config.anti_crawl_wait_max)
        self._wait_with_backoff(base_delay, wait_factor)
        
        return False  # 需要重试
    
    def _handle_success(self, index: int, url: str, shizu_id: str, redirect_url: str) -> bool:
        """处理成功情况"""
        self.consecutive_failures = 0
        self.retry_counts[index] = 0
        
        result = self._create_result(shizu_id, url, redirect_url, "success")
        FileManager.write_result(self.config.results_file, result)
        
        logging.info(f"已记录: {shizu_id} -> {redirect_url}")
        return True
    
    def _handle_failure(self, index: int, url: str, shizu_id: str, error_type: str) -> bool:
        """处理失败情况"""
        self.retry_counts[index] = self.retry_counts.get(index, 0) + 1
        logging.warning(f"无法获取重定向URL: {url} - {error_type}")
        
        result = self._create_result(shizu_id, url, error_type, "failed")
        FileManager.write_result(self.config.results_file, result)
        
        if self.retry_counts[index] >= self.config.max_retries:
            return True  # 达到最大重试次数，算作完成
        
        return False  # 需要重试
    
    def run(self):
        """运行追踪器"""
        logging.info("开始运行网站追踪器...")
        
        # 加载进度
        progress = FileManager.load_progress()
        start_index = (progress['last_index'] + 1 
                      if progress and progress['last_index'] < self.config.max_index 
                      else self.config.min_index)
        self.consecutive_failures = progress['consecutive_failures'] if progress else 0
        
        print(f"开始处理：从 shizu{start_index} 到 shizu{self.config.max_index}")
        
        try:
            current_index = start_index
            while current_index <= self.config.max_index:
                success = self.process_single_url(current_index)
                
                if success:
                    # 处理成功，移动到下一个
                    if current_index % 5 == 0:
                        FileManager.save_progress("tracker_progress.json", current_index, self.consecutive_failures)
                    
                    # 随机延迟
                    delay = random.uniform(self.config.min_delay, self.config.max_delay)
                    self._wait_with_backoff(delay)
                    
                    current_index += 1
                # 如果失败，会在下次循环中重试同一个URL
                
        except KeyboardInterrupt:
            logging.info("检测到用户中断，保存进度后退出...")
            FileManager.save_progress("tracker_progress.json", current_index - 1, self.consecutive_failures)
            print(f"\n程序已暂停。下次运行时将从 shizu{current_index} 继续。")
            sys.exit(0)
        
        logging.info("网站追踪完成!")


class UpdateNotifier:
    """更新通知器"""
    
    def __init__(self, config: TrackerConfig):
        self.config = config
        self.snapshot_file = 'website_results_snapshot.json'
        self.update_notice_file = 'website_update_notice.txt'
        
        # 确保更新通知文件存在
        FileManager.ensure_file_exists(self.update_notice_file, "=== 网站更新差异记录 ===")
    
    def check_and_notify_updates(self):
        """检查并通知更新"""
        # 读取上次快照
        old_results = self._load_snapshot()
        
        # 读取本次最新结果
        new_results = ResultAnalyzer.load_results_from_file(self.config.results_file)
        
        # 比较结果
        updated_sites = ResultAnalyzer.compare_results(old_results, new_results)
        
        if updated_sites:
            self._write_update_notice(updated_sites)
            print(f"检测到 {len(updated_sites)} 个网站有更新，详情见 {self.update_notice_file}")
            logging.info(f"检测到 {len(updated_sites)} 个网站有更新，详情见 {self.update_notice_file}")
        else:
            print("本次未检测到网站跳转URL变化。")
            logging.info("本次未检测到网站跳转URL变化。")
        
        # 更新快照
        self._save_snapshot(new_results)
    
    def _load_snapshot(self) -> Dict[str, str]:
        """加载快照"""
        if os.path.exists(self.snapshot_file):
            try:
                with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"读取快照文件时出错: {e}")
        return {}
    
    def _save_snapshot(self, results: Dict[str, str]):
        """保存快照"""
        try:
            with open(self.snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存快照文件时出错: {e}")
    
    def _write_update_notice(self, updated_sites: List[Tuple[str, str, str]]):
        """写入更新通知"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.update_notice_file, 'a', encoding='utf-8') as f:
            f.write(f"\n==== {timestamp} 检测到更新 ====\n\n")
            
            for shizu_id, old_url, new_url in updated_sites:
                shizu_num = shizu_id.replace('shizu', '')
                original_url = f"{self.config.base_url}{shizu_num}"
                
                f.write(f"时间戳: {timestamp}\n")
                f.write(f"直连网站: {original_url}\n")
                f.write(f"跳转网站: {new_url}\n")
                f.write(f"shizu编号: {shizu_id}\n")
                f.write(f"变化说明: 从 {old_url} 更新到 {new_url}\n")
                f.write("---\n")


def main():
    """主函数"""
    # 加载配置
    config = ConfigManager.load_config()
    
    # 创建并运行追踪器
    tracker = WebsiteTracker(config)
    tracker.run()
    
    # 检查更新并通知
    notifier = UpdateNotifier(config)
    notifier.check_and_notify_updates()


if __name__ == "__main__":
    main()
