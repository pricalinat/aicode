#!/usr/bin/env python3
"""
MiniMax API 配额监控脚本
每分钟检查配额使用情况，超过 80% 时输出警告
"""

import subprocess
import json
import logging
import sys
import time
from datetime import datetime

# 配置
API_URL = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"
API_TOKEN = "sk-cp-mjBJmxDHEHvM8jYoUnpGfUS0bJLcS6Lc6lbIXseyS7j59dEEiy3iFV1R8SiwSuF23qS7H8_Ij8xKQuteDaNefFRlrPE4lhIUj5akR0RhUTcwDLH2DkEqQR0"
LOG_FILE = "/Users/rrp/.openclaw/workspace/monitoring/minimax_quota.log"
CHECK_INTERVAL = 60  # 秒
WARNING_THRESHOLD = 0.80  # 80%

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_quota():
    """调用 API 检查配额"""
    cmd = [
        'curl', '-s', '--location', API_URL,
        '--header', f'Authorization: Bearer {API_TOKEN}',
        '--header', 'Content-Type: application/json'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.error(f"API 请求失败: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"API 请求异常: {e}")
        return None


def parse_and_log(data):
    """解析 JSON 数据并记录日志"""
    if not data:
        return
    
    base_resp = data.get("base_resp", {})
    status_code = base_resp.get("status_code", -1)
    status_msg = base_resp.get("status_msg", "unknown")
    
    if status_code != 0:
        logger.warning(f"API 返回错误: {status_code} - {status_msg}")
        return
    
    model_remains = data.get("model_remains", [])
    
    if not model_remains:
        logger.info("配额数据为空")
        return
    
    for model in model_remains:
        model_name = model.get("model_name", "Unknown")
        total = model.get("current_interval_total_count", 0)
        used = model.get("current_interval_usage_count", 0)
        
        if total > 0:
            usage_percent = (used / total) * 100
            remaining = total - used
            
            log_msg = f"{model_name}: 已用 {used}/{total} ({usage_percent:.1f}%), 剩余 {remaining}"
            logger.info(log_msg)
            
            # 超过阈值时输出警告
            if usage_percent >= WARNING_THRESHOLD * 100:
                warning_msg = f"⚠️ 警告: {model_name} 使用量已达到 {usage_percent:.1f}%，超过 {int(WARNING_THRESHOLD*100)}% 阈值！"
                logger.warning(warning_msg)
                print(warning_msg, file=sys.stderr)
        else:
            logger.info(f"{model_name}: 无配额限制或数据异常")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("MiniMax API 配额监控启动")
    logger.info(f"日志文件: {LOG_FILE}")
    logger.info(f"告警阈值: {int(WARNING_THRESHOLD*100)}%")
    logger.info("=" * 50)
    
    # 首次运行立即检查
    logger.info("执行首次配额检查...")
    data = check_quota()
    parse_and_log(data)
    
    # 持续监控
    while True:
        time.sleep(CHECK_INTERVAL)
        logger.info("执行定时配额检查...")
        data = check_quota()
        parse_and_log(data)


if __name__ == "__main__":
    main()
