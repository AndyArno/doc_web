"""
Locust 性能测试脚本 — ROS教学网站

用法:
    # 安装 locust
    pip install locust

    # 启动 Web UI 模式（推荐）
    locust -f locustfile.py --host=http://localhost:8000

    # 无头模式（直接运行，生成 CSV 报告）
    locust -f locustfile.py --host=http://localhost:8000 \
        --headless -u 200 -r 20 -t 5m \
        --csv=performance_test

    参数说明:
        -u  : 总用户数
        -r  : 每秒新增用户数（ramp up）
        -t  : 测试持续时间

    Web UI 模式下在浏览器打开 http://localhost:8089，
    可手动设置用户数和 ramp up 速度。
"""

import random
import logging
import sys
from locust import HttpUser, task, between, events

logger = logging.getLogger(__name__)

# ============================================================
# 配置区域 — 根据实际环境修改
# ============================================================

# 测试账号（需提前在系统中创建）
TEST_ACCOUNTS = [
    {"account": "testuser1", "password": "Test1234"},
    {"account": "testuser2", "password": "Test1234"},
    {"account": "testuser3", "password": "Test1234"},
    {"account": "testuser4", "password": "Test1234"},
    {"account": "testuser5", "password": "Test1234"},
]

# 搜索关键词池（从教学场景选取）
SEARCH_KEYWORDS = [
    "ROS",
    "导航",
    "ROS 安装",
    "机器人",
    "launch文件",
    "话题通信",
    "服务通信",
    "参数服务器",
    "TF坐标变换",
    "Gazebo仿真",
    "SLAM",
    "MoveIt",
]


class TeachingWebsiteUser(HttpUser):
    """模拟教学网站用户行为

    任务权重分配（模拟典型教学场景）：
    - 教材浏览: 30%（学生浏览教材列表）
    - 章节阅读: 50%（学生阅读章节内容，最高频操作）
    - 全文搜索: 20%（学生检索知识点）
    """

    wait_time = between(1, 3)  # 两次操作间等待1-3秒
    host = "http://localhost:8000"

    def on_start(self):
        """用户启动时登录获取Token"""
        account_info = random.choice(TEST_ACCOUNTS)
        self.account = account_info["account"]

        with self.client.post(
            "/api/v1/auth/login",
            json={
                "account": account_info["account"],
                "password": account_info["password"],
            },
            name="/api/v1/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and data.get("data"):
                    self.token = data["data"]["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    response.success()
                else:
                    response.failure(f"登录业务错误: {data.get('message')}")
                    self.token = None
                    self.headers = {}
            else:
                response.failure(f"登录HTTP错误: {response.status_code}")
                self.token = None
                self.headers = {}

    @task(3)
    def browse_textbooks(self):
        """浏览教材列表 — 模拟首页加载"""
        if not self.token:
            return

        with self.client.get(
            "/api/v1/textbooks",
            params={"page": 1, "page_size": 20},
            headers=self.headers,
            name="/api/v1/textbooks [教材列表]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    response.success()
                else:
                    response.failure(f"业务错误: {data.get('message')}")
            else:
                response.failure(f"HTTP错误: {response.status_code}")

    @task(5)
    def read_chapter(self):
        """阅读章节内容 — 模拟章节加载"""
        if not self.token:
            return

        # 先获取教材列表
        with self.client.get(
            "/api/v1/textbooks",
            params={"page": 1, "page_size": 20},
            headers=self.headers,
            name="/api/v1/textbooks [章节阅读前置]",
            catch_response=True,
        ) as tb_response:
            if tb_response.status_code != 200:
                return
            tb_data = tb_response.json()
            if tb_data.get("code") != 200 or not tb_data.get("data", {}).get("items"):
                return
            textbooks = tb_data["data"]["items"]

        # 随机选一本教材，获取章节树
        textbook = random.choice(textbooks)
        textbook_id = textbook["id"]

        with self.client.get(
            f"/api/v1/chapters/textbook/{textbook_id}",
            headers=self.headers,
            name="/api/v1/chapters/textbook/{id} [章节树]",
            catch_response=True,
        ) as tree_response:
            if tree_response.status_code != 200:
                return
            tree_data = tree_response.json()
            if tree_data.get("code") != 200 or not tree_data.get("data"):
                return
            chapters = tree_data["data"].get("chapters", [])

        # 递归收集所有文章节点ID
        article_ids = []
        self._collect_article_ids(chapters, article_ids)

        if not article_ids:
            return

        # 随机选一个章节阅读
        chapter_id = random.choice(article_ids)
        with self.client.get(
            f"/api/v1/chapters/{chapter_id}",
            headers=self.headers,
            name="/api/v1/chapters/{id} [章节详情]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    response.success()
                else:
                    response.failure(f"业务错误: {data.get('message')}")
            else:
                response.failure(f"HTTP错误: {response.status_code}")

    @task(2)
    def search_content(self):
        """全文搜索 — 模拟学生检索知识点"""
        if not self.token:
            return

        keyword = random.choice(SEARCH_KEYWORDS)

        with self.client.get(
            "/api/v1/search",
            params={"q": keyword, "page": 1, "page_size": 20},
            headers=self.headers,
            name="/api/v1/search [全文搜索]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    response.success()
                else:
                    response.failure(f"业务错误: {data.get('message')}")
            else:
                response.failure(f"HTTP错误: {response.status_code}")

    def _collect_article_ids(self, nodes, ids):
        """递归收集章节树中的文章节点ID"""
        if not nodes:
            return
        for node in nodes:
            node_id = node.get("id") or node.get("node_id")
            node_type = node.get("node_type", "folder")
            if node_type == "article" and node_id:
                ids.append(node_id)
            children = node.get("children", [])
            if children:
                self._collect_article_ids(children, ids)


# ============================================================
# 测试结果事件监听 — 用于生成论文数据
# ============================================================

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时打印统计摘要，便于写入论文
    
    注意：使用 sys.exit(0) 提前退出，绕过 Locust 默认的 sorted() bug
    （Locust 在打印汇总时无法处理 None 键，会导致 TypeError）
    """
    stats = environment.stats
    print("\n" + "=" * 60)
    print("性能测试结果摘要")
    print("=" * 60)

    key_endpoints = [
        ("GET", "/api/v1/textbooks [教材列表]"),
        ("GET", "/api/v1/chapters/{id} [章节详情]"),
        ("GET", "/api/v1/search [全文搜索]"),
    ]

    print(f"\n{'接口':<45} {'平均(ms)':<10} {'中位数(ms)':<10} {'95%(ms)':<10} {'99%(ms)':<10} {'最大(ms)':<10}")
    print("-" * 95)

    for method, name in key_endpoints:
        try:
            entry = stats.get(name, method)
            if entry and entry.num_requests > 0:
                avg = round(entry.avg_response_time)
                med = round(entry.median_response_time)
                p95 = round(entry.get_response_time_percentile(0.95))
                p99 = round(entry.get_response_time_percentile(0.99))
                mx = round(entry.max_response_time)
                print(f"{name:<45} {avg:<10} {med:<10} {p95:<10} {p99:<10} {mx:<10}")
            else:
                print(f"{name:<45} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10}")
        except KeyError:
            print(f"{name:<45} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10}")

    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"失败数:   {stats.total.num_failures}")
    print(f"总RPS:    {round(stats.total.total_rps, 1)}")
    print("=" * 60)
    
    sys.exit(0)
