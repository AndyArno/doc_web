"""
服务端资源监控脚本 — 配合 Locust 性能测试使用

用法:
    # 在运行 Locust 的同时，另开一个终端启动此脚本
    python server_monitor.py

    # 指定采样间隔和输出文件
    python server_monitor.py --interval 1 --output monitor_result.csv

    # 监控完毕后按 Ctrl+C 停止，数据自动保存

工作原理:
    1. 自动查找 uvicorn 进程（匹配命令行中包含 uvicorn 的进程）
    2. 每隔 interval 秒采样一次该进程的内存和网络 IO
    3. 数据同时输出到终端和 CSV 文件
    4. 测试结束后按 Ctrl+C 停止，汇总统计信息

前置条件:
    pip install psutil
"""

import argparse
import csv
import sys
import time
import signal
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("错误：请先安装 psutil")
    print("  pip install psutil")
    sys.exit(1)


# ============================================================
# 进程发现
# ============================================================

def find_uvicorn_process() -> psutil.Process | None:
    """查找 uvicorn 主进程

    优先查找匹配 'uvicorn app.main:app' 的进程，
    若未找到则匹配任意 uvicorn 进程。
    """
    candidates = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            cmdline_str = " ".join(cmdline)
            if "uvicorn" in cmdline_str:
                candidates.append((proc, cmdline_str))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not candidates:
        return None

    # 优先匹配 app.main:app（项目的实际启动命令）
    for proc, cmdline in candidates:
        if "app.main:app" in cmdline or "app.main:app" in cmdline:
            return proc

    # 其次返回任意 uvicorn 进程
    return candidates[0][0]


def find_process_children(proc: psutil.Process) -> list[psutil.Process]:
    """获取进程的所有子进程（uvicorn 会有多个 worker）"""
    try:
        return proc.children(recursive=True)
    except psutil.NoSuchProcess:
        return []


# ============================================================
# 资源采样
# ============================================================

def sample_process(proc: psutil.Process) -> dict:
    """采样单个进程的资源使用情况"""
    try:
        mem_info = proc.memory_info()
        io_info = proc.io_counters()
        return {
            "memory_rss_mb": round(mem_info.rss / 1024 / 1024, 1),
            "memory_vms_mb": round(mem_info.vms / 1024 / 1024, 1),
            "io_read_bytes": io_info.read_bytes,
            "io_write_bytes": io_info.write_bytes,
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {
            "memory_rss_mb": 0,
            "memory_vms_mb": 0,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
        }


def sample_all(proc: psutil.Process) -> dict:
    """采样主进程 + 所有子进程的汇总资源"""
    main = sample_process(proc)
    children = find_process_children(proc)

    total_rss = main["memory_rss_mb"]
    total_vms = main["memory_vms_mb"]

    # IO 需要累加
    total_io_read = main["io_read_bytes"]
    total_io_write = main["io_write_bytes"]

    for child in children:
        child_sample = sample_process(child)
        total_rss += child_sample["memory_rss_mb"]
        total_vms += child_sample["memory_vms_mb"]
        total_io_read += child_sample["io_read_bytes"]
        total_io_write += child_sample["io_write_bytes"]

    return {
        "memory_rss_mb": round(total_rss, 1),
        "memory_vms_mb": round(total_vms, 1),
        "io_read_mb": round(total_io_read / 1024 / 1024, 2),
        "io_write_mb": round(total_io_write / 1024 / 1024, 2),
    }


# ============================================================
# 网络带宽监控（系统级，按网卡）
# ============================================================

class NetworkMonitor:
    """监控系统网络IO，计算实时带宽"""

    def __init__(self):
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()

    def sample(self) -> dict:
        """采样并计算自上次以来的平均带宽"""
        current_io = psutil.net_io_counters()
        current_time = time.time()
        elapsed = current_time - self.last_time

        if elapsed <= 0:
            return {"net_send_kb_s": 0, "net_recv_kb_s": 0}

        send_rate = (current_io.bytes_sent - self.last_io.bytes_sent) / elapsed / 1024
        recv_rate = (current_io.bytes_recv - self.last_io.bytes_recv) / elapsed / 1024

        self.last_io = current_io
        self.last_time = current_time

        return {
            "net_send_kb_s": round(send_rate, 1),
            "net_recv_kb_s": round(recv_rate, 1),
        }


# ============================================================
# 主监控循环
# ============================================================

def run_monitor(interval: float, output_path: str):
    """运行监控主循环"""
    # 查找 uvicorn 进程
    proc = find_uvicorn_process()
    if proc is None:
        print("错误：未找到 uvicorn 进程，请先启动后端服务")
        print("  cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    print(f"已找到 uvicorn 进程: PID={proc.pid}")
    children = find_process_children(proc)
    if children:
        print(f"  子进程数: {len(children)}")

    # 初始化
    net_monitor = NetworkMonitor()
    time.sleep(interval)

    # CSV 输出
    csv_path = Path(output_path)
    fieldnames = [
        "timestamp", "elapsed_s",
        "memory_rss_mb", "memory_vms_mb",
        "io_read_mb", "io_write_mb",
        "net_send_kb_s", "net_recv_kb_s",
    ]

    rows = []
    start_time = time.time()

    # 信号处理（Ctrl+C 优雅退出）
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        running = False
        print("\n\n正在停止监控...")

    signal.signal(signal.SIGINT, signal_handler)

    print(f"\n开始监控 (采样间隔: {interval}s, 输出: {csv_path})")
    print("按 Ctrl+C 停止监控\n")
    print(f"{'时间':<12} {'内存RSS':<10} {'IO读MB':<9} {'IO写MB':<9} {'发送KB/s':<10} {'接收KB/s':<10}")
    print("-" * 64)

    while running:
        try:
            elapsed = round(time.time() - start_time, 1)
            proc_sample = sample_all(proc)
            net_sample = net_monitor.sample()
            now = datetime.now().strftime("%H:%M:%S")

            row = {
                "timestamp": now,
                "elapsed_s": elapsed,
                **proc_sample,
                **net_sample,
            }
            rows.append(row)

            # 终端输出
            print(
                f"{now:<12} "
                f"{proc_sample['memory_rss_mb']:<10} "
                f"{proc_sample['io_read_mb']:<9} "
                f"{proc_sample['io_write_mb']:<9} "
                f"{net_sample['net_send_kb_s']:<10} "
                f"{net_sample['net_recv_kb_s']:<10}"
            )

            time.sleep(interval)

        except psutil.NoSuchProcess:
            print("\nuvicorn 进程已退出，停止监控")
            running = False
        except Exception as e:
            print(f"\n采样异常: {e}")
            time.sleep(interval)

    # 写入 CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 汇总统计
    if rows:
        print("\n" + "=" * 60)
        print("资源监控结果摘要")
        print("=" * 60)
        print(f"监控时长: {rows[-1]['elapsed_s']}s")
        print(f"采样次数: {len(rows)}")

        mem_values = [r["memory_rss_mb"] for r in rows]
        net_send = [r["net_send_kb_s"] for r in rows]
        net_recv = [r["net_recv_kb_s"] for r in rows]

        print(f"\n内存 RSS:   平均 {sum(mem_values)/len(mem_values):.1f}MB  "
              f"最大 {max(mem_values):.1f}MB")
        print(f"网络发送:   平均 {sum(net_send)/len(net_send):.1f}KB/s  "
              f"最大 {max(net_send):.1f}KB/s")
        print(f"网络接收:   平均 {sum(net_recv)/len(net_recv):.1f}KB/s  "
              f"最大 {max(net_recv):.1f}KB/s")
        print("=" * 60)

    print(f"\n详细数据已保存到: {csv_path}")


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="服务端资源监控（配合 Locust 使用）")
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="采样间隔（秒），默认1秒"
    )
    parser.add_argument(
        "--output", type=str, default="monitor_result.csv",
        help="CSV 输出文件路径，默认 monitor_result.csv"
    )
    args = parser.parse_args()

    run_monitor(args.interval, args.output)
