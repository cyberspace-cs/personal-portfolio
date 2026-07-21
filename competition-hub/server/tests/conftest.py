"""竞赛信息聚合平台 · 测试夹具
在导入应用前设置临时数据库，确保测试与种子数据相互隔离。
"""
import os
import sys
import tempfile

# 必须在导入 main（及其依赖的 database 模块）之前设置数据库路径
_TMP = tempfile.mkdtemp(prefix="comp_hub_test_")
os.environ["DB_DIR"] = _TMP
os.environ["DB_NAME"] = "test.db"

# 将 server/ 加入导入路径，使 tests/ 内能 import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # TestClient 上下文会触发 startup（init_db + seed_if_empty）
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    # 每个用例前清空认证限流计数，避免相互干扰
    main._auth_hits.clear()
    yield
    main._auth_hits.clear()
