"""补全竞赛官网图片（og:image 横幅大图）。

用法（在本机、可联网环境下执行）：
    cd competition-hub
    python server/enrich_images.py            # 全部补全
    python server/enrich_images.py --limit 10 # 仅前 10 条（调试）

逻辑：为 competitions 表中 image 为空但 source_url 存在的记录，
抓取其官网页面的 og:image / twitter:image（退而求其次取首个 <img>），
写入 image 字段。该字段由前端作为卡片封面大图展示。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db  # noqa: E402
from collector import enrich_images  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="补全竞赛官网 og:image 图片")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 条（调试用）")
    args = parser.parse_args()

    init_db()
    print("开始补全官网图片……")
    result = enrich_images(limit=args.limit)
    print("完成：", result)


if __name__ == "__main__":
    main()
