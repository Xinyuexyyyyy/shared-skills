"""
Harvest Tool - 配置文件
"""

import os

# 抓取约束
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
MAX_FILES_TO_FETCH = 10  # 最多抓取的核心文件数
REQUEST_DELAY = 0.5  # 秒，避免触发限速

# 发现阶段
DEFAULT_REPO_COUNT = 10
MIN_STARS = 100  # 最低 star 数过滤

# 数据目录（各阶段中间产物）
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 工作区根目录
WORKSPACE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# 共识文档输出基目录（Stage 6 最终产物）
CONSENSUS_OUTPUT_DIR = os.path.join(
    WORKSPACE_ROOT,
    "task_draft",
    "consensus",
)
os.makedirs(CONSENSUS_OUTPUT_DIR, exist_ok=True)
