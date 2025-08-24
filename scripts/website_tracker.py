import requests
import time
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse
import os
import json
import sys
from bs4 import BeautifulSoup
import logging

# 加载配置
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"无法加载配置文件: {e}")
    config = {
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config["log_file"], encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 从配置中获取参数
BASE_URL = config["base_url"]
RESULTS_FILE = config["results_file"]
MIN_DELAY = config["min_delay"]
MAX_DELAY = config["max_delay"]
MIN_INDEX = config["min_index"]
MAX_INDEX = config["max_index"]
TITLE_SAMPLE_RATE = config["title_sample_rate"]
MAX_RETRIES = min(config.get("max_retries", 3), 3)  # 确保最大重试次数不超过3次
RETRY_DELAY = min(config.get("retry_delay", 20), 30)  # 确保重试延迟不超过30秒
ANTI_CRAWL_WAIT_MIN = min(config.get("anti_crawl_wait_min", 15), 15)
ANTI_CRAWL_WAIT_MAX = min(config.get("anti_crawl_wait_max", 30), 30)

# 状态跟踪
retry_counts = {}
last_successful_run = datetime.now()
consecutive_failures = 0

def get_random_user_agent():
    """返回一个随机的用户代理字符串"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    return random.choice(user_agents)

def get_redirect_url(url):
    """获取URL重定向后的最终URL"""
    try:
        headers = {
            "User-Agent": get_random_user_agent(),
            "Referer": "http://tians.06kd.mlkj888.cn/",
        }
        
        # 禁用重定向自动跟踪
        response = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            logging.info(f"重定向URL: {redirect_url}")
            
            # 检查是否触发了反爬机制（腾讯视频播放页面）
            if redirect_url and "v.qq.com/txp/iframe/player.html" in redirect_url:
                logging.warning("检测到反爬机制！跳转到了腾讯视频播放页面")
                return "ANTI_CRAWL_DETECTED"
            
            # 判断是否是相对URL
            if redirect_url and not redirect_url.startswith('http'):
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                redirect_url = base_url + redirect_url
            
            return redirect_url
        else:
            # 检查页面中的meta刷新重定向
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_refresh = soup.find('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'refresh'})
            
            if meta_refresh and 'content' in meta_refresh.attrs:
                content = meta_refresh['content']
                if 'url=' in content.lower():
                    redirect_url = content.split('url=', 1)[1].strip()
                    logging.info(f"Meta刷新重定向: {redirect_url}")
                    
                    # 判断是否是相对URL
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

def get_page_title(url):
    """尝试获取页面标题"""
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "无标题"
        return title.strip()
    except Exception as e:
        logging.error(f"获取页面标题时出错: {e}")
        return "获取标题失败"

def save_progress(current_index):
    """保存当前进度到文件"""
    progress_file = "tracker_progress.json"
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

def load_progress():
    """从文件加载进度"""
    progress_file = "tracker_progress.json"
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"已加载进度: 上次处理到 shizu{data['last_index']}")
            return data
    except Exception as e:
        logging.error(f"加载进度时出错: {e}")
    return None

def main():
    global consecutive_failures
    
    # 确保结果文件存在，如果不存在则创建
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write("时间戳,链接编号,原始URL,跳转URL,页面标题,状态\n")
    
    # 尝试加载之前的进度
    progress = load_progress()
    i = progress['last_index'] + 1 if progress and progress['last_index'] < MAX_INDEX else MIN_INDEX
    consecutive_failures = progress['consecutive_failures'] if progress else 0
    
    print(f"开始处理：从 shizu{i} 到 shizu{MAX_INDEX}")
    
    try:
        while i <= MAX_INDEX:
            try:
                url = f"{BASE_URL}{i}"
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 检查是否已经尝试过这个URL太多次
                retry_count = retry_counts.get(i, 0)
                if retry_count >= MAX_RETRIES:
                    logging.warning(f"已达到最大重试次数 ({MAX_RETRIES}) 对于 shizu{i}，跳过...")
                    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{current_time},shizu{i},{url},超过最大重试次数,N/A,跳过\n")
                    i += 1
                    continue
                
                logging.info(f"处理 {url} (尝试 {retry_count + 1}/{MAX_RETRIES})")
                redirect_url = get_redirect_url(url)
                
                # 检查是否触发了反爬机制
                if redirect_url == "ANTI_CRAWL_DETECTED":
                    consecutive_failures += 1
                    retry_counts[i] = retry_count + 1
                    
                    logging.warning(f"检测到反爬机制，连续失败: {consecutive_failures}")
                    
                    # 记录触发反爬机制的情况
                    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{current_time},shizu{i},{url},触发反爬机制,N/A,需要重试\n")
                    
                    # 保存当前进度
                    save_progress(i - 1)
                    
                    # 根据连续失败次数适度增加等待时间，但不超过30秒
                    wait_factor = min(consecutive_failures, 1.5)  # 最多等待1.5倍时间
                    long_delay = min(random.uniform(ANTI_CRAWL_WAIT_MIN, ANTI_CRAWL_WAIT_MAX) * wait_factor, 30)
                    
                    logging.warning(f"触发反爬机制，等待 {long_delay:.2f} 秒后重试...")
                    time.sleep(long_delay)
                    
                    # 不增加索引，重新尝试同一个URL
                    continue
                    
                elif redirect_url:
                    # 重置连续失败计数
                    consecutive_failures = 0
                    retry_counts[i] = 0
                    
                    # 尝试获取页面标题，但不要过度访问
                    title = "跳过标题获取" if i % TITLE_SAMPLE_RATE != 0 else get_page_title(redirect_url)
                    
                    # 将结果写入文件
                    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{current_time},shizu{i},{url},{redirect_url},{title},成功\n")
                    
                    logging.info(f"已记录: shizu{i} -> {redirect_url}")
                else:
                    retry_counts[i] = retry_count + 1
                    logging.warning(f"无法获取重定向URL: {url}")
                    
                    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{current_time},shizu{i},{url},获取失败,N/A,失败\n")
                
                # 每处理5个链接保存一次进度
                if i % 5 == 0:
                    save_progress(i)
                
                # 随机延迟，避免触发防爬机制
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                logging.info(f"等待 {delay:.2f} 秒...")
                time.sleep(delay)
                
                # 成功处理后递增索引
                i += 1
                
            except Exception as e:
                logging.error(f"处理URL时出错: {e}")
                
                # 即使出错也添加记录
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{current_time},shizu{i},{BASE_URL}{i},处理出错,N/A,出错\n")
                
                # 记录重试次数
                retry_counts[i] = retry_counts.get(i, 0) + 1
                
                # 出错后稍微延迟长一点，但不超过30秒
                delay = min(random.uniform(MAX_DELAY, MAX_DELAY * 1.5), 30)
                logging.warning(f"处理出错，等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)
                
                # 如果已经达到最大重试次数，则移动到下一个URL
                if retry_counts[i] >= MAX_RETRIES:
                    logging.warning(f"已达到最大重试次数 ({MAX_RETRIES}) 对于 shizu{i}，跳过...")
                    i += 1
                
    except KeyboardInterrupt:
        # 捕获Ctrl+C，保存进度后退出
        logging.info("检测到用户中断，保存进度后退出...")
        save_progress(i - 1)
        print(f"\n程序已暂停。下次运行时将从 shizu{i} 继续。")
        sys.exit(0)

if __name__ == "__main__":
    logging.info("开始运行网站追踪器...")
    main()
    logging.info("网站追踪完成!")
