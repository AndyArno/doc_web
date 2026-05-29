#!/usr/bin/env python3
"""
性能测试脚本 - 同时运行Locust和监控
"""

import subprocess
import time
import sys
import os
from pathlib import Path

BACKEND_DIR = Path("/home/arno/project/document_web/backend")
TESTS_DIR = Path("/home/arno/project/document_web/tests")
RESULTS_DIR = TESTS_DIR / "results"
VENV_PYTHON = BACKEND_DIR / ".venv" / "bin" / "python"
VENV_LOCUST = BACKEND_DIR / ".venv" / "bin" / "locust"

def run_test(concurrency: int, spawn_rate: int, duration: str):
    """运行单组测试"""
    
    print(f"\n{'='*60}")
    print(f"开始 {concurrency} 并发测试")
    print(f"{'='*60}\n")
    
    # 启动监控（后台运行）
    monitor_output = RESULTS_DIR / f"monitor_{concurrency}.csv"
    monitor_proc = subprocess.Popen(
        [str(VENV_PYTHON), str(TESTS_DIR / "server_monitor.py"), 
         "--interval", "1", "--output", str(monitor_output)],
        cwd=str(TESTS_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"监控已启动 (PID: {monitor_proc.pid})")
    time.sleep(3)  # 等待监控采集基线数据
    
    # 运行Locust
    print(f"开始Locust压测...")
    locust_proc = subprocess.Popen(
        [str(VENV_LOCUST), "-f", "locustfile.py", 
         "--host=http://localhost:8000",
         "--headless", "-u", str(concurrency), "-r", str(spawn_rate), 
         "-t", duration,
         "--csv=results/perf_" + str(concurrency)],
        cwd=str(TESTS_DIR)
    )
    
    # 等待Locust完成
    locust_proc.wait()
    print(f"Locust测试完成")
    
    # 等待额外时间让监控采集收尾数据
    print("等待监控采集收尾数据...")
    time.sleep(5)
    
    # 终止监控
    monitor_proc.terminate()
    try:
        monitor_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        monitor_proc.kill()
        monitor_proc.wait()
    
    print(f"监控已停止")
    
    # 检查监控文件是否生成
    if monitor_output.exists():
        lines = len(monitor_output.read_text().strip().split('\n'))
        print(f"监控数据已保存: {monitor_output} ({lines} 行)")
    else:
        print(f"警告: 监控文件未生成")

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # 检查后端是否运行
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8000/docs", timeout=5)
        print("后端服务已就绪")
    except:
        print("错误: 后端服务未运行，请先启动后端")
        print("  cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # 运行三组测试
    run_test(50, 10, "2m")
    run_test(100, 20, "2m")
    run_test(200, 20, "2m")
    
    print(f"\n{'='*60}")
    print("所有测试完成！")
    print(f"{'='*60}")
    print(f"\n结果文件位于: {RESULTS_DIR}")

if __name__ == "__main__":
    main()
