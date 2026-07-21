"""竞赛信息聚合平台 · 示例数据种子
首次启动（或手动执行 `python seed.py`）时写入一批真实感强的示例竞赛与分类。
"""
import json
import sqlite3
from database import get_db, init_db


CATEGORIES = [
    ("hackathon", "黑客松", "🚀", "限时组队、从 0 到 1 把想法做成产品的极客马拉松。", 1),
    ("data", "数据竞赛 / Kaggle", "📊", "数据挖掘、机器学习与 Kaggle 式排行榜竞赛。", 2),
    ("algorithm", "算法竞赛", "🧮", "ICPC、蓝桥杯、LeetCode 等算法与编程能力比拼。", 3),
    ("ctf", "网络安全 / CTF", "🛡️", "夺旗赛、渗透实战与信息安全攻防对抗。", 4),
    ("ai", "AI 大模型", "🤖", "大模型应用、Agent、微调与 AIGC 创新赛道。", 5),
    ("innovation", "创新创业", "💡", "商业计划、硬科技创业与产业落地挑战赛。", 6),
    ("dev", "软件开发大赛", "💻", "全栈、开源、云原生与行业软件系统开发。", 7),
    ("design", "视觉 / 产品竞赛", "🎨", "UI/UX、交互设计、产品创意与数字艺术。", 8),
]

# (title, slug, summary, description, category_slug, organizer, location, mode,
#  prize, prize_amount, status, start, end, reg_deadline, tags, cover, source_url, featured)
COMPETITIONS = [
    ("2026 腾讯云 AI 游戏开发黑客松", "tencent-cloud-ai-game-hackathon-2026",
     "用大模型与实时渲染，48 小时打造一款可玩 AI 游戏。",
     "面向高校与独立开发者的 AI 游戏创作马拉松。提供腾讯云算力、混元大模型 API 与游戏引擎素材包。评审维度包含创意、技术完整度与可玩性。",
     "hackathon", "腾讯云开发者社区", "深圳", "offline", "¥ 150,000", 150000, "ongoing",
     "2026-06-14", "2026-08-19", "2026-07-30",
     ["AI游戏", "实时渲染", "独立开发"], "", "https://example.com/tc-ai-game", 1),

    ("2026 WAIC FutureTech OPC 独立先锋挑战赛", "waic-futuretech-opc-2026",
     "开源开放算力下的先锋 AI 应用黑客松。",
     "WAIC 2026 与 OpenCSG 联合主办，聚焦开源模型微调、Agent 编排与行业落地。提供 GPU 算力券与导师陪跑。",
     "hackathon", "WAIC 2026 组委会 & OpenCSG", "上海", "offline", "¥ 200,000", 200000, "ongoing",
     "2026-06-14", "2026-07-23", "2026-07-15",
     ["开源", "Agent", "算力"], "", "https://example.com/waic-opc", 1),

    ("2026 AdventureX 青年极客创客松", "adventurex-youth-maker-2026",
     "为 18-28 岁青年极客打造的硬件 + AI 创客马拉松。",
     "五天四夜沉浸式创客营，提供硬件套件、3D 打印与导师资源，最终路演角逐百万奖金池。",
     "hackathon", "AdventureX 组委会", "杭州", "offline", "¥ 1,000,000", 1000000, "upcoming",
     "2026-07-21", "2026-07-25", "2026-07-18",
     ["硬件", "创客", "青年"], "", "https://example.com/adventurex", 1),

    ("2026 哈佛黑客松中国挑战赛", "harvard-hackathon-china-2026",
     "HackHarvard 中国站：全球开发者同台竞技。",
     "哈佛大学 HackHarvard 团队主办，中英双语赛道，涵盖教育、气候、健康三大主题，优胜队伍直通哈佛决赛。",
     "hackathon", "哈佛大学 HackHarvard 团队", "杭州", "hybrid", "¥ 100,000", 100000, "upcoming",
     "2026-08-20", "2026-08-22", "2026-08-10",
     ["教育", "气候", "健康"], "", "https://example.com/harvard-cn", 0),

    ("HICOOL 2026 全球创业大赛开发者挑战赛", "hicool-2026-dev-challenge",
     "面向全球创业者的技术与商业双重挑战。",
     "北京海外高层次人才协会与摩尔线程联合主办，奖金 + 落地政策 + 投资对接三合一。",
     "innovation", "北京海外高层次人才协会 & 摩尔线程", "北京顺义", "offline", "¥ 250,000", 250000, "ongoing",
     "2026-05-31", "2026-08-29", "2026-08-01",
     ["创业", "投资", "硬科技"], "", "https://example.com/hicool", 0),

    ("2026 抖音 AI 创变者极客挑战赛", "douyin-ai-creator-challenge-2026",
     "用 AIGC 重新定义短视频创作。",
     "字节跳动与抖音开发平台主办，围绕大模型剪辑、数字人、智能脚本三大方向，提供流量扶持与现金奖励。",
     "ai", "字节跳动 & 抖音开发平台", "北京", "online", "¥ 300,000", 300000, "ended",
     "2026-05-19", "2026-06-24", "2026-05-15",
     ["AIGC", "数字人", "短视频"], "", "https://example.com/douyin-ai", 0),

    ("Kaggle · 城市交通流量预测大模型赛", "kaggle-city-traffic-forecast",
     "基于多源时序数据的城市路网拥堵预测。",
     "提供千万级交通卡口与 GPS 轨迹数据，评测 MAE / MAPE。设新手组与专业组双榜。",
     "data", "Kaggle × 某市交通研究院", "线上", "online", "$ 30,000", 210000, "ongoing",
     "2026-06-01", "2026-09-01", "2026-08-20",
     ["时序预测", "交通", "深度学习"], "", "https://example.com/kaggle-traffic", 1),

    ("天池 · 电商用户增长大模型算法赛", "tianchi-ecom-growth-llm",
     "用大模型理解用户意图，提升推荐转化率。",
     "阿里云天池主办，提供脱敏行为日志与商品知识图谱，考察召回、排序与生成式推荐。",
     "data", "阿里云天池", "线上", "online", "¥ 200,000", 200000, "upcoming",
     "2026-08-05", "2026-10-10", "2026-09-30",
     ["推荐系统", "大模型", "NLP"], "", "https://example.com/tianchi-ecom", 0),

    ("2026 全国高校 ICPC 程序设计竞赛（区域赛）", "icpc-regional-2026",
     "算法竞技的奥林匹克，三人一队五小时。",
     "覆盖网络赛、区域赛与 EC Final，考察数据结构、图论、动态规划与思维。",
     "algorithm", "中国大学生程序设计竞赛协会", "多城市", "offline", "荣誉 + 保研加分", 0, "upcoming",
     "2026-09-12", "2026-11-30", "2026-09-01",
     ["ACM", "图论", "DP"], "", "https://example.com/icpc", 1),

    ("蓝桥杯全国软件和信息技术专业人才大赛", "lanqiao-cup-2026",
     "覆盖算法、嵌入式与数字创新的综合性赛事。",
     "分省赛与国赛，设软件类、电子类与视觉设计类多个赛道，参与院校超千所。",
     "algorithm", "工业和信息化部人才交流中心", "多城市", "offline", "证书 + 奖金", 0, "ongoing",
     "2026-04-01", "2026-08-15", "2026-06-30",
     ["软件", "嵌入式", "综合"], "", "https://example.com/lanqiao", 0),

    ("2026 强网杯网络安全对抗赛（CTF）", "qiangwang-cup-ctf-2026",
     "国家级网络安全攻防 CTF 盛事。",
     "设 Web、Pwn、Reverse、Crypto、Misc 五方向，线上预选 + 线下决赛，优胜队入选人才库。",
     "ctf", "国家网络空间安全人才培养基地", "郑州", "hybrid", "¥ 200,000", 200000, "upcoming",
     "2026-08-28", "2026-09-01", "2026-08-20",
     ["Web", "Pwn", "Reverse"], "", "https://example.com/qiangwang", 1),

    ("XCTF 国际网络攻防联赛分站赛", "xctf-2026-stage",
     "与国际战队同场竞技的夺旗联赛。",
     "采用 Jeopardy + Attack-Defense 混合赛制，积分计入全球排行榜。",
     "ctf", "XCTF 联赛组委会", "线上", "online", "$ 15,000", 105000, "ended",
     "2026-05-10", "2026-06-08", "2026-05-05",
     ["Jeopardy", "AWD", "国际"], "", "https://example.com/xctf", 0),

    ("2026 大模型应用创新 Hackathon（智谱专场）", "zhipu-llm-app-hackathon-2026",
     "基于 GLM 系列模型构建生产级 AI 应用。",
     "提供 GLM-4 长上下文与工具调用能力，方向涵盖科研助手、代码智能与多模态。",
     "ai", "智谱 AI", "北京", "offline", "¥ 180,000", 180000, "upcoming",
     "2026-08-15", "2026-08-17", "2026-08-10",
     ["GLM", "工具调用", "多模态"], "", "https://example.com/zhipu-hack", 0),

    ("通义千问 · 智能体（Agent）开发大赛", "qwen-agent-dev-contest-2026",
     "构建能自主规划与调用的智能体。",
     "阿里通义千问主办，评测 Agent 的任务完成率、工具使用与稳定性，提供云资源与模型额度。",
     "ai", "阿里通义千问", "线上", "online", "¥ 220,000", 220000, "ongoing",
     "2026-06-20", "2026-09-15", "2026-08-30",
     ["Agent", "规划", "工具"], "", "https://example.com/qwen-agent", 1),

    ("2026 中国软件开源创新大赛", "china-oss-innovation-2026",
     "以开源协作驱动基础软件突破。",
     "设编译器、数据库、操作系统与 AI 框架四个赛道，强调 PR 贡献与社区协作。",
     "dev", "中国开源软件推进联盟", "多城市", "online", "¥ 150,000", 150000, "upcoming",
     "2026-09-01", "2026-12-01", "2026-11-01",
     ["开源", "基础软件", "协作"], "", "https://example.com/oss-cn", 0),

    ("华为云 · 云原生应用开发大赛", "huaweicloud-cloudnative-2026",
     "基于 Kubernetes 与 Serverless 构建弹性应用。",
     "考察微服务治理、可观测性与成本优化，提供华为云代金券与认证名额。",
     "dev", "华为云", "线上", "online", "¥ 120,000", 120000, "ended",
     "2026-04-15", "2026-06-30", "2026-06-15",
     ["K8s", "Serverless", "微服务"], "", "https://example.com/hw-cloudnative", 0),

    ("2026 中国高校计算机大赛——智能交互设计赛", "c4-chinteraction-2026",
     "以人为中心的产品与交互创新。",
     "覆盖无障碍设计、AR/VR 交互与 AI 产品，强调用户研究与原型可用性。",
     "design", "教育部计算机类教指委", "多城市", "offline", "证书 + 奖金", 0, "ongoing",
     "2026-05-20", "2026-08-25", "2026-07-31",
     ["交互", "AR/VR", "产品"], "", "https://example.com/c4-design", 0),

    ("NextStep 2026 黑客松（武汉站）", "nextstep-hackathon-wuhan-2026",
     "面向职场新人的轻量级黑客松。",
     "提供大模型 Token 与硬件套件，主题聚焦效率工具与 AI 助理。",
     "hackathon", "NextStep 组委会", "武汉", "offline", "大模型 Token 与硬件套件", 0, "ended",
     "2026-07-02", "2026-07-04", "2026-06-28",
     ["效率工具", "AI助理"], "", "https://example.com/nextstep-wh", 0),

    ("Web3 专门赛 · 去中心化金融黑客松", "web3-defi-forge",
     "在链上构建下一代 DeFi 协议。",
     "DeFi Forge 主办，覆盖 AMM、借贷与链上身份，提供审计扶持与生态资源。",
     "hackathon", "DeFi Forge 组委会", "线上", "online", "¥ 80,000", 80000, "ended",
     "2026-06-07", "2026-07-09", "2026-06-30",
     ["DeFi", "链上", "金融"], "", "https://example.com/defi-forge", 0),

    ("2026 百度之星 · 程序设计大赛", "baidu-star-2026",
     "面向中学生的算法启蒙与竞技。",
     "百度主办，题目趣味性强，设初中组与高中组，优秀者直通百度实习。",
     "algorithm", "百度", "线上", "online", "¥ 100,000", 100000, "upcoming",
     "2026-08-01", "2026-09-20", "2026-08-25",
     ["中学生", "趣味", "启蒙"], "", "https://example.com/baidu-star", 0),

    ("2026 腾讯广告算法大赛", "tencent-ads-algo-2026",
     "多模态广告转化率预估。",
     "提供亿级广告曝光与转化样本，考察多模态特征与冷启动建模。",
     "data", "腾讯广告", "线上", "online", "¥ 300,000", 300000, "upcoming",
     "2026-08-10", "2026-10-20", "2026-10-01",
     ["多模态", "CTR", "冷启动"], "", "https://example.com/tencent-ads", 1),

    ("2026 世界人工智能大会 · 黑客松", "wai-hackathon-2026",
     "WAIC 同期旗舰黑客松，顶级导师与资本在场。",
     "聚焦具身智能、科学计算与 AI for Science，决赛现场路演。",
     "ai", "世界人工智能大会组委会", "上海", "offline", "¥ 500,000", 500000, "upcoming",
     "2026-09-05", "2026-09-07", "2026-08-25",
     ["具身智能", "AI4S", "路演"], "", "https://example.com/wai-hack", 1),

    ("2026 中国工业互联网 APP 开发大赛", "industrial-internet-app-2026",
     "为工厂场景打造工业软件。",
     "覆盖设备预测性维护、工艺优化与数字孪生，提供真实产线数据。",
     "dev", "中国工业互联网研究院", "多城市", "offline", "¥ 160,000", 160000, "ongoing",
     "2026-06-01", "2026-09-30", "2026-09-01",
     ["数字孪生", "工业", "预测维护"], "", "https://example.com/iiot-app", 0),

    ("2026 全国大学生数字媒体科技作品竞赛", "digital-media-tech-2026",
     "技术与艺术交汇的创意舞台。",
     "设游戏、动画、交互影像与 VR 四个方向，强调技术与叙事的结合。",
     "design", "中国人工智能学会", "多城市", "offline", "证书 + 奖金", 0, "upcoming",
     "2026-10-01", "2026-12-15", "2026-11-15",
     ["游戏", "动画", "VR"], "", "https://example.com/dmt-2026", 0),
]


def _slug_to_id(conn, slug):
    row = conn.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
    return row["id"] if row else None


def seed():
    """写入分类与示例竞赛（幂等：已存在则跳过）"""
    conn = get_db()
    # 分类
    for slug, name, icon, desc, order in CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (slug, name, icon, description, sort_order) VALUES (?,?,?,?,?)",
            (slug, name, icon, desc, order),
        )
    # 竞赛
    for c in COMPETITIONS:
        (title, slug, summary, description, cslug, organizer, location, mode,
         prize, prize_amount, status, start, end, reg_deadline, tags, cover, source_url, featured) = c
        if conn.execute("SELECT 1 FROM competitions WHERE slug=?", (slug,)).fetchone():
            continue
        cat_id = _slug_to_id(conn, cslug)
        conn.execute(
            """INSERT INTO competitions
               (title, slug, summary, description, category_id, organizer, location, mode,
                prize, prize_amount, status, start_date, end_date, reg_deadline, tags, cover, source_url, featured)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title, slug, summary, description, cat_id, organizer, location, mode,
             prize, prize_amount, status, start, end, reg_deadline,
             json.dumps(tags, ensure_ascii=False), cover, source_url, featured),
        )
    conn.commit()
    conn.close()
    print(f"[seed] 已写入 {len(CATEGORIES)} 个分类、{len(COMPETITIONS)} 条示例竞赛。")


def seed_if_empty():
    """仅当竞赛表为空时才自动种子（用于应用启动时）"""
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) AS n FROM competitions").fetchone()["n"]
    conn.close()
    if n == 0:
        seed()


if __name__ == "__main__":
    init_db()
    seed()
