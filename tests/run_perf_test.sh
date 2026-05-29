#!/bin/bash
# 性能测试脚本 - 按照测试操作流程.md执行

set -e

BACKEND_DIR="/home/arno/project/document_web/backend"
TESTS_DIR="/home/arno/project/document_web/tests"
RESULTS_DIR="$TESTS_DIR/results"

# 创建结果目录
mkdir -p "$RESULTS_DIR"

echo "============================================================"
echo "ROS教学网站性能测试"
echo "============================================================"

# 函数：等待后端就绪
wait_for_backend() {
    echo "等待后端服务就绪..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            echo "后端服务已就绪"
            return 0
        fi
        sleep 1
    done
    echo "错误: 后端服务启动超时"
    return 1
}

# 函数：运行单组测试
run_test() {
    local users=$1
    local spawn_rate=$2
    local duration=$3
    
    echo ""
    echo "============================================================"
    echo "开始 ${users} 并发测试 (持续时间: ${duration})"
    echo "============================================================"
    
    # 启动监控
    echo "启动资源监控..."
    cd "$TESTS_DIR"
    uv run python server_monitor.py --interval 1 --output "$RESULTS_DIR/monitor_${users}.csv" &
    MONITOR_PID=$!
    sleep 2
    
    # 运行Locust
    echo "启动Locust压测..."
    cd "$TESTS_DIR"
    uv run locust -f locustfile.py --host=http://localhost:8000 \
        --headless -u $users -r $spawn_rate -t $duration \
        --csv="$RESULTS_DIR/perf_${users}" \
        --html="$RESULTS_DIR/perf_${users}.html"
    
    # 停止监控
    echo "停止资源监控..."
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    
    echo "${users} 并发测试完成"
}

# 主流程
cd "$BACKEND_DIR"

# 检查是否已有后端在运行
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "检测到后端服务已运行"
else
    echo "启动后端服务..."
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    wait_for_backend
fi

echo ""
echo "后端PID: $(pgrep -f 'uvicorn app.main:app' | head -1)"

# 运行三组测试
run_test 50 10 "2m"
run_test 100 20 "2m"
run_test 200 20 "2m"

echo ""
echo "============================================================"
echo "所有测试完成！结果保存在 $RESULTS_DIR"
echo "============================================================"
echo ""
echo "生成的文件:"
ls -la "$RESULTS_DIR"

# 如果是我们启动的后端，关闭它
if [ -n "$BACKEND_PID" ]; then
    echo ""
    echo "关闭后端服务..."
    kill $BACKEND_PID 2>/dev/null || true
fi
