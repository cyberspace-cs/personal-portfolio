"""专属刷题教练 · 后端 API 服务
FastAPI + SQLite · TRAE AI 创造力大赛复赛
"""
import hashlib
import json
import os
from datetime import date, datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from database import get_db, init_db, DB_DIR
from models import (
    ChatIn, ExamRecordIn, ExamRecordOut, ExplainIn, GenIn, MasteryOut, QuestionOut,
    QuizRecordIn, QuizRecordOut, ReportIn, StreakOut, UserLogin,
    UserOut, UserRegister, WrongBookIn, WrongBookOut,
)

# 定制化备考 Agent（多智能体编排 / 工具调用 / 分层记忆）
from agent.router import router as agent_router
from agent.memory import ensure_tables as ensure_agent_tables
from agent.eval import ensure_eval_table

# ---- AI 配置（统一复用 Agent 多厂商注册表：智谱/Kimi/混元/豆包/千问/DeepSeek/OpenAI） ----
# 由 agent/llm.py 的多厂商注册表解析激活厂商（LLM_PROVIDER 指定，或自动选第一个有 Key 的厂商）。
from agent.llm import call_llm_tool, active_provider, HAS_KEY
_act = active_provider()
print(f"[coach-ai] AI 厂商：{_act['label']}（{_act['name']} · {_act['model']}）"
      f" · {'真实大模型' if HAS_KEY else '降级模式（无需 Key，前端功能不受影响）'}")
from agent.inference import QUANT_CONFIG
_awq_state = "开" if QUANT_CONFIG["enabled"] else "关"
print(f"[coach-ai] 推理优化(Phase F)：KV前缀缓存/上下文压缩/投机解码/知识蒸馏/连续批处理/"
      f"工具替代生成/量化AWQ={_awq_state} 已启用；调用 /api/agent/infer/optimize 查看量化结果")
print(f"[coach-ai] 多厂商可切换：GET /api/agent/providers 查看，POST /api/agent/providers/switch 切换")
from agent.channel import HUB
print(f"[coach-ai] 接入渠道(Agent-native Harness)：{[c['name'] for c in HUB.list_channels()]}；"
      f" GET /api/agent/channels 查看；MCP 内置 exam_syllabus/question_bank_search")


# Hermes Agent（智能答疑转发，内网代理，绝不公网暴露）
HERMES_CONFIG = {
    "BASE": os.getenv("HERMES_BASE", ""),
    "KEY": os.getenv("HERMES_KEY", "") or os.getenv("HERMES_API_KEY", ""),
    "MODEL": os.getenv("HERMES_MODEL", "hermes-agent"),
}
HAS_HERMES = bool(HERMES_CONFIG["BASE"] and HERMES_CONFIG["KEY"])
print(f"[coach-ai] Hermes 答疑： {'已接入' if HAS_HERMES else '未接入（/api/chat 走降级文案）'}")

# 简易内存缓存（按 prompt 指纹）
_AI_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 30 * 60  # 秒


def _cache_get(key: str):
    hit = _AI_CACHE.get(key)
    if hit and (datetime.now().timestamp() - hit[0]) < _CACHE_TTL:
        return hit[1]
    return None


def _cache_set(key: str, val: dict):
    if len(_AI_CACHE) > 500:
        _AI_CACHE.clear()
    _AI_CACHE[key] = (datetime.now().timestamp(), val)


# ---- 结构化输出 schema（虚拟工具范式：用 Function Calling 约束 JSON，替代脆弱的 json_object） ----
# 参考 HKUDS/nanobot「虚拟工具」技巧：发一个 function definition，截获 tool_calls.arguments 作为严格结构，
# 不真实执行该工具。多厂商 OpenAI 兼容端点对 Function Calling 支持比 json_object 更稳定。
_EXPLAIN_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "tips": {"type": "string"},
    },
    "required": ["summary", "steps", "tips"],
}
_GEN_SCHEMA = {
    "type": "object",
    "properties": {
        "baseTopic": {"type": "string"},
        "variants": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "stem": {"type": "string"},
                "opts": {"type": "array", "items": {"type": "string"}},
                "answer": {"type": "array", "items": {"type": "integer"}},
                "explain": {"type": "string"},
            },
            "required": ["stem", "opts", "answer", "explain"],
        }},
    },
    "required": ["baseTopic", "variants"],
}
_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall": {"type": "string"},
        "prediction": {"type": "string"},
        "focusTopics": {"type": "string"},
        "plan": {"type": "array", "items": {"type": "string"}},
        "encouragement": {"type": "string"},
    },
    "required": ["overall", "prediction", "focusTopics", "plan", "encouragement"],
}


async def _structured_llm(system: str, user: str, tool_name: str, schema: dict, max_tokens: int = 700) -> dict:
    """用虚拟工具范式向激活厂商要结构化 JSON；返回空 dict 表示失败（调用方应降级）。"""
    return await call_llm_tool(system, user, tool_name, schema, max_tokens)

# 启动时初始化数据库（lifespan 事件，替代已弃用的 on_event）
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    init_db()
    seed_questions()
    ensure_agent_tables()   # 持久化 Agent 记忆表（长期画像 + 短期对话）
    ensure_eval_table()      # 评测闭环日志表
    yield

app = FastAPI(title="专属刷题教练 API", version="3.7.0-channel-history-mcp", lifespan=lifespan)
app.include_router(agent_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ================================================================
# 题库种子数据
# ================================================================
SEED_QUESTIONS = [
    # ── 考研（12 道） ──
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设随机变量 X 服从参数为 λ 的泊松分布，则 E(X) 与 D(X) 的关系为？",
     "opts": json.dumps(["E(X) > D(X)", "E(X) = D(X)", "E(X) < D(X)", "无法确定"]),
     "answer": json.dumps([1]), "explain": "泊松分布的期望与方差均等于参数 λ，因此 E(X)=D(X)=λ。",
     "topic": "概率统计", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列关于矩阵可逆的说法中，正确的有？（多选）",
     "opts": json.dumps(["行列式不为零", "秩等于阶数", "存在零特征值", "各行向量线性无关"]),
     "answer": json.dumps([0, 1, 3]), "explain": "矩阵可逆 ⇔ 行列式非零 ⇔ 满秩 ⇔ 行向量线性无关。存在零特征值意味着行列式为零。",
     "topic": "线性代数", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "马克思主义哲学认为，世界的统一性在于它的？",
     "opts": json.dumps(["运动性", "物质性", "矛盾性", "发展性"]),
     "answer": json.dumps([1]), "explain": "辩证唯物主义认为世界统一于物质，物质是世界的本原。",
     "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "The word \"ubiquitous\" is closest in meaning to？",
     "opts": json.dumps(["rare", "everywhere", "hidden", "dangerous"]),
     "answer": json.dumps([1]), "explain": "ubiquitous 意为\"无处不在的\"，与 everywhere 意思最接近。",
     "topic": "英语词汇", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设 f(x) 在 [a,b] 上连续，在 (a,b) 内可导，且 f(a)=f(b)，则至少存在一点 ξ∈(a,b) 使得？",
     "opts": json.dumps(["f(ξ)=0", "f'(ξ)=0", "f''(ξ)=0", "f(ξ)=f'(ξ)"]),
     "answer": json.dumps([1]), "explain": "罗尔定理：若 f(a)=f(b)，则存在 ξ∈(a,b) 使 f'(ξ)=0。",
     "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "计算机组成原理中，冯·诺依曼体系结构的核心思想是？",
     "opts": json.dumps(["程序存储与程序控制", "并行处理", "分布式计算", "面向对象"]),
     "answer": json.dumps([0]), "explain": "冯·诺依曼结构核心是\"存储程序\"，将指令和数据预先存入存储器中自动执行。",
     "topic": "计算机组成", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列属于英国宪章运动时期工人阶级诉求的有？（多选）",
     "opts": json.dumps(["普选权", "秘密投票", "八小时工作制", "废除议会"]),
     "answer": json.dumps([0, 1]), "explain": "宪章运动六项要求包括普选权、秘密投票等，但八小时工作制和废除议会不在其中。",
     "topic": "政治·近代史", "difficulty": "hard"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "数据结构中，栈的典型特征是？",
     "opts": json.dumps(["FIFO", "LIFO", "随机存取", "顺序存取"]),
     "answer": json.dumps([1]), "explain": "栈是后进先出(LIFO)结构，队列是先进先出(FIFO)。",
     "topic": "数据结构", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "定积分 ∫₀^π sin x dx 的值为？",
     "opts": json.dumps(["0", "1", "2", "π"]),
     "answer": json.dumps([2]), "explain": "∫₀^π sin x dx = [-cos x]₀^π = -cosπ - (-cos0) = 1 + 1 = 2。",
     "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "英语中 \"It is high time that we ____ measures.\" 应填？",
     "opts": json.dumps(["take", "took", "will take", "have taken"]),
     "answer": json.dumps([1]), "explain": "It is high time (that)... 后用虚拟语气，谓语动词用一般过去时（took）。",
     "topic": "英语语法", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "判断题", "stem": "矛盾的基本属性是同一性和斗争性，二者缺一不可。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([0]), "explain": "正确。矛盾的同一性与斗争性是相反相成、不可分割的两种基本属性。",
     "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "进程与线程的区别，下列说法正确的有？（多选）",
     "opts": json.dumps(["进程是资源分配的基本单位", "线程是CPU调度的基本单位", "同一进程内的线程共享地址空间", "线程之间不能并发执行"]),
     "answer": json.dumps([0, 1, 2]), "explain": "进程是资源分配单位，线程是调度单位，同进程线程共享内存；线程同样可以并发。",
     "topic": "操作系统", "difficulty": "medium"},

    # ── 考公（12 道） ──
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "某工程队 8 天完成一项工程的 2/5，照此速度，完成剩余工程还需多少天？",
     "opts": json.dumps(["10 天", "12 天", "14 天", "16 天"]),
     "answer": json.dumps([1]), "explain": "8 天完成 2/5，即每天 1/20。剩余 3/5，需 (3/5)÷(1/20)=12 天。",
     "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "行政诉讼中，被告对作出的行政行为负有举证责任。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([0]), "explain": "正确。《行政诉讼法》规定被告对其作出的行政行为承担举证责任。",
     "topic": "公共基础·法律", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "甲、乙、丙、丁四人参加比赛，赛前：甲说\"乙能得第一\"；乙说\"丙能得第一\"；丙说\"我不能得第一\"；丁说\"甲能得第一\"。已知只有一人说对了，请问谁得了第一？",
     "opts": json.dumps(["甲", "乙", "丙", "丁"]),
     "answer": json.dumps([2]), "explain": "逐一假设验证：若丙得第一，则乙说对、丙说错、甲说错、丁说错，只有一人说对，满足条件。",
     "topic": "行测·逻辑判断", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "2020年某市GDP为5000亿元，2023年为6655亿元，年均增长率约为？",
     "opts": json.dumps(["8%", "10%", "12%", "15%"]),
     "answer": json.dumps([1]), "explain": "5000×(1+r)³=6655, (1+r)³=1.331, r≈10%。",
     "topic": "行测·资料分析", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "下列成语与历史人物对应正确的是？",
     "opts": json.dumps(["卧薪尝胆—勾践", "纸上谈兵—赵括", "破釜沉舟—项羽", "以上都对"]),
     "answer": json.dumps([3]), "explain": "三个成语分别对应勾践、赵括、项羽，全部正确。",
     "topic": "行测·常识判断", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "申论写作中，\"总—分—总\"结构的核心是？",
     "opts": json.dumps(["先提观点再论证最后总结", "先讲故事再分析", "直接罗列论据", "只写结论"]),
     "answer": json.dumps([0]), "explain": "申论\"总—分—总\"结构要求开篇提出观点、中间分论点论证、结尾总结升华。",
     "topic": "申论", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "我国宪法规定，中华人民共和国的一切权力属于？",
     "opts": json.dumps(["全国人民代表大会", "国务院", "人民", "中国共产党"]),
     "answer": json.dumps([2]), "explain": "《宪法》第二条规定：中华人民共和国的一切权力属于人民。",
     "topic": "公共基础·宪法", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "图形推理：题干图形依次为○、△、□、○、△，下一个应是？",
     "opts": json.dumps(["○", "△", "□", "☆"]),
     "answer": json.dumps([2]), "explain": "周期为 3 的循环：○、△、□ 重复，第 6 个应为 □。",
     "topic": "行测·图形推理", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "多选题", "stem": "下列属于我国国家机构的有？（多选）",
     "opts": json.dumps(["全国人民代表大会", "国务院", "中央军事委员会", "中国人民政治协商会议"]),
     "answer": json.dumps([0, 1, 2]), "explain": "人大、国务院、中央军委均属国家机构；政协是爱国统一战线组织，非国家机构。",
     "topic": "公共基础·宪法", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "若 a:b = 3:4，b:c = 2:5，则 a:c 等于？",
     "opts": json.dumps(["3:5", "3:10", "6:5", "4:5"]),
     "answer": json.dumps([1]), "explain": "由 b:c=2:5 得 b:c=4:10，故 a:b:c=3:4:10，a:c=3:10。",
     "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "公务员录用考试笔试一般包括行政职业能力测验和申论两科。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([0]), "explain": "正确。中央及地方公务员笔试通常含行测与申论。",
     "topic": "公共基础·常识", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "类比推理：医生∶病人 相当于？",
     "opts": json.dumps(["教师∶学生", "司机∶汽车", "作家∶书店", "警察∶小偷"]),
     "answer": json.dumps([0]), "explain": "医生服务病人，教师服务学生，均为职业与服务对象关系，最贴切。",
     "topic": "行测·类比推理", "difficulty": "easy"},

    # ── 大厂（12 道） ──
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "对一个已排序数组进行查找，采用二分查找的时间复杂度为？",
     "opts": json.dumps(["O(1)", "O(log n)", "O(n)", "O(n log n)"]),
     "answer": json.dumps([1]), "explain": "二分查找每次将搜索范围折半，时间复杂度为 O(log n)。",
     "topic": "算法", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "下列属于进程间通信(IPC)方式的有？（多选）",
     "opts": json.dumps(["管道 Pipe", "共享内存", "消息队列", "局部变量"]),
     "answer": json.dumps([0, 1, 2]), "explain": "管道、共享内存、消息队列、信号量、Socket 均为 IPC 方式。局部变量不能跨进程。",
     "topic": "操作系统", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "TCP 协议中，三次握手过程的第三个报文段包含的标志位是？",
     "opts": json.dumps(["SYN", "SYN+ACK", "ACK", "FIN"]),
     "answer": json.dumps([2]), "explain": "三次握手：客户端SYN→服务器SYN+ACK→客户端ACK（第三个报文只有ACK标志）。",
     "topic": "计算机网络", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "Java 中，HashMap 的底层数据结构在 JDK 1.8 之后是？",
     "opts": json.dumps(["数组+链表", "数组+链表+红黑树", "纯数组", "纯链表"]),
     "answer": json.dumps([1]), "explain": "JDK 1.8 后 HashMap 采用数组+链表+红黑树，当链表长度超过 8 时转为红黑树。",
     "topic": "Java基础", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "设计一个短链接系统，最核心的考量是？",
     "opts": json.dumps(["前端美观度", "哈希冲突与唯一性", "数据库选型", "部署环境"]),
     "answer": json.dumps([1]), "explain": "短链接系统最核心的是生成唯一短码，需解决哈希冲突、唯一性保证和分布式ID生成问题。",
     "topic": "系统设计", "difficulty": "hard"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "CSS 中，实现水平垂直居中的 flexbox 写法是？",
     "opts": json.dumps(["display:flex; justify-content:center", "display:flex; align-items:center", "display:flex; justify-content:center; align-items:center", "display:flex; text-align:center"]),
     "answer": json.dumps([2]), "explain": "justify-content:center 实现主轴居中，align-items:center 实现交叉轴居中，两者组合实现水平垂直居中。",
     "topic": "前端基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "快速排序平均时间复杂度是？",
     "opts": json.dumps(["O(n)", "O(n log n)", "O(n²)", "O(log n)"]),
     "answer": json.dumps([1]), "explain": "快排平均时间复杂度为 O(n log n)，最坏 O(n²)。",
     "topic": "算法", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "关于 HTTP 与 HTTPS，下列说法正确的有？（多选）",
     "opts": json.dumps(["HTTPS 默认端口 443", "HTTPS 基于 TLS/SSL 加密", "HTTP 是明文传输", "HTTPS 比 HTTP 慢所以不安全"]),
     "answer": json.dumps([0, 1, 2]), "explain": "HTTPS 默认 443、基于 TLS 加密、HTTP 明文；HTTPS 虽稍慢但更安全。",
     "topic": "计算机网络", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "二叉树的前序遍历顺序是？",
     "opts": json.dumps(["根-左-右", "左-根-右", "左-右-根", "根-右-左"]),
     "answer": json.dumps([0]), "explain": "前序遍历：先访问根节点，再左子树，后右子树（根-左-右）。",
     "topic": "数据结构", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "数据库事务的 ACID 特性中，I 指的是？",
     "opts": json.dumps(["原子性", "一致性", "隔离性", "持久性"]),
     "answer": json.dumps([2]), "explain": "ACID：Atomicity 原子性、Consistency 一致性、Isolation 隔离性、Durability 持久性。",
     "topic": "数据库", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "判断题", "stem": "Python 中列表(list)是可变对象，而元组(tuple)是不可变对象。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([0]), "explain": "正确。list 可变、tuple 不可变，这是二者核心区别。",
     "topic": "Python基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "在分布式系统中，CAP 理论指出不可能同时满足？",
     "opts": json.dumps(["一致性与可用性", "一致性与分区容错性", "可用性与分区容错性", "三者可同时满足"]),
     "answer": json.dumps([1]), "explain": "CAP 指出在网络分区(P)发生时，一致性(C)与可用性(A)不可兼得。",
     "topic": "系统设计", "difficulty": "hard"},

    # ── 考研 追加（共 20 道） ──
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "英语中 \"ambiguous\" 的含义最接近？",
     "opts": json.dumps(["明确的", "模棱两可的", "遥远的", "熟悉的"]),
     "answer": json.dumps([1]), "explain": "ambiguous 意为\"含糊不清的、模棱两可的\"。",
     "topic": "英语词汇", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设函数 f(x)=x³-3x，则 f(x) 的极小值点为？",
     "opts": json.dumps(["x=-1", "x=0", "x=1", "x=2"]),
     "answer": json.dumps([2]), "explain": "f'(x)=3x²-3，令为0得x=±1；f''(1)=6>0为极小值点，极小值在x=1。",
     "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列不等式中，对任意实数 x 恒成立的有？（多选）",
     "opts": json.dumps(["x²≥0", "x²+1>0", "|x|≥x", "x+1>x"]),
     "answer": json.dumps([0, 1, 2, 3]), "explain": "平方非负、平方加1恒正、绝对值不小于自身、x+1恒大于x，均恒成立。",
     "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "操作系统页式存储管理中，页表的作用是？",
     "opts": json.dumps(["映射逻辑页到物理块", "管理文件", "调度进程", "分配内存给内核"]),
     "answer": json.dumps([0]), "explain": "页表建立逻辑地址中页号到物理内存块号的映射关系，实现地址转换。",
     "topic": "操作系统", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "TCP 与 UDP 的区别，下列正确的是？",
     "opts": json.dumps(["TCP 面向连接，UDP 无连接", "UDP 可靠，TCP 不可靠", "TCP 速度快于 UDP", "二者均为广播协议"]),
     "answer": json.dumps([0]), "explain": "TCP 面向连接、可靠；UDP 无连接、尽力交付。UDP 通常更快但不保证可靠。",
     "topic": "计算机网络", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "判断题", "stem": "二叉树的中序遍历结果可以唯一确定一棵二叉树的结构。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([1]), "explain": "错误。仅中序遍历无法确定结构，需配合前序或后序遍历才能唯一确定。",
     "topic": "数据结构", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "马克思主义哲学中，实践是认识的来源，这表明？",
     "opts": json.dumps(["认识先于实践", "认识来源于实践", "实践等于认识", "认识可以脱离实践"]),
     "answer": json.dumps([1]), "explain": "马克思主义认识论强调实践是第一性的，认识来源于实践并反作用于实践。",
     "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "数据库事务的隔离级别中，可避免脏读的最低级别是？",
     "opts": json.dumps(["读未提交", "读已提交", "可重复读", "串行化"]),
     "answer": json.dumps([1]), "explain": "读已提交(Read Committed)可防止脏读，是避免脏读的最低隔离级别。",
     "topic": "数据库", "difficulty": "medium"},

    # ── 考公 追加（共 20 道） ──
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "某商品原价 100 元，先提价 20% 再打八折出售，现价为？",
     "opts": json.dumps(["96 元", "100 元", "104 元", "120 元"]),
     "answer": json.dumps([0]), "explain": "100×1.2=120，再×0.8=96 元。提价与打折比例不同，现价低于原价。",
     "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "我国现行宪法历经几次全面修改？自 1982 年宪法以来修正案共几件？",
     "opts": json.dumps(["3 次修改，52 件修正案", "未全面修改，52 件修正案", "5 次修改，无修正案", "1 次修改，18 件修正案"]),
     "answer": json.dumps([1]), "explain": "1982 年宪法沿用至今未全面修改，通过 52 件宪法修正案（1988/1993/1999/2004/2018 五次修宪共52条）。",
     "topic": "公共基础·宪法", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "多选题", "stem": "下列关于公文格式的说法，正确的有？（多选）",
     "opts": json.dumps(["公文标题一般由发文机关+事由+文种组成", "主送机关顶格书写", "成文日期用阿拉伯数字", "密级和保密期限可不标注"]),
     "answer": json.dumps([0, 1, 2]), "explain": "公文标题三要素、主送顶格、成文日期用阿拉伯数字均正确；密级依需标注，非必须。",
     "topic": "公共基础·公文", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "俗语\"一着不慎，满盘皆输\"体现的哲理是？",
     "opts": json.dumps(["整体统帅部分", "关键部分对整体起决定作用", "部分无关紧要", "整体等于部分之和"]),
     "answer": json.dumps([1]), "explain": "关键局部（一着）影响整体（满盘），体现关键部分对整体的决定作用。",
     "topic": "政治·马哲", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "资料分析：某省 2022 年粮食产量 6000 万吨，同比增长 2%，则增量约为？",
     "opts": json.dumps(["约 118 万吨", "约 120 万吨", "约 130 万吨", "约 150 万吨"]),
     "answer": json.dumps([0]), "explain": "增量=6000-6000/1.02≈6000×0.0196≈117.6 万吨，约 118 万吨。",
     "topic": "行测·资料分析", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "行政复议是行政诉讼的必经前置程序。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([1]), "explain": "错误。多数情形可复议也可直接诉讼，仅法律特别规定事项才需复议前置。",
     "topic": "公共基础·法律", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "类比推理：天平∶重量 相当于？",
     "opts": json.dumps(["温度计∶温度", "尺子∶长度", "钟表∶时间", "以上都正确"]),
     "answer": json.dumps([3]), "explain": "天平测重量、温度计测温度、尺子测长度、钟表测时间，均为测量工具与对象关系。",
     "topic": "行测·类比推理", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "《行政处罚法》规定，违法行为在几年内未被发现不再给予处罚？",
     "opts": json.dumps(["1 年", "2 年", "5 年", "10 年"]),
     "answer": json.dumps([1]), "explain": "一般违法行为 2 年内未被发现不再处罚；涉及公民生命健康安全等有特别规定。",
     "topic": "公共基础·法律", "difficulty": "medium"},

    # ── 大厂 追加（共 20 道） ──
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "Python 中 list 和 tuple 的主要区别是？",
     "opts": json.dumps(["list 可变，tuple 不可变", "tuple 可变，list 不可变", "二者都不可变", "二者都可变"]),
     "answer": json.dumps([0]), "explain": "list 可变（可增删改），tuple 不可变（创建后不能修改），这是核心区别。",
     "topic": "Python基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "一个栈的入栈序列为 1,2,3,4，合法的出栈序列是？",
     "opts": json.dumps(["4,3,2,1", "3,4,1,2", "1,3,2,4", "以上都合法"]),
     "answer": json.dumps([3]), "explain": "栈允许任意时机的入/出交错；4,3,2,1（全入后出）、3,4,1,2、1,3,2,4 均可能。",
     "topic": "数据结构", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "关于索引，下列说法正确的有？（多选）",
     "opts": json.dumps(["索引可加速查询", "索引会降低写入速度", "主键自动建立唯一索引", "索引越多越好"]),
     "answer": json.dumps([0, 1, 2]), "explain": "索引加速读但拖慢写，主键默认唯一索引；索引过多反而影响性能，并非越多越好。",
     "topic": "数据库", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "动态规划的核心思想通常包含？",
     "opts": json.dumps(["分治+记忆化", "暴力枚举", "随机搜索", "贪心即可"]),
     "answer": json.dumps([0]), "explain": "DP 通过最优子结构、重叠子问题与记忆化（缓存子问题结果）避免重复计算。",
     "topic": "算法", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "HTTP 状态码 404 表示？",
     "opts": json.dumps(["服务器错误", "请求成功", "资源未找到", "需要重定向"]),
     "answer": json.dumps([2]), "explain": "404 Not Found 表示服务器无法找到请求的资源。",
     "topic": "计算机网络", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "判断题", "stem": "React 中 useState 返回的 setter 函数是异步批量更新的。",
     "opts": json.dumps(["正确", "错误"]),
     "answer": json.dumps([0]), "explain": "正确。React 18 起默认自动批处理，同一事件中的多次 setState 会合并批量更新。",
     "topic": "前端基础", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "哈希表平均查找时间复杂度约为？",
     "opts": json.dumps(["O(1)", "O(log n)", "O(n)", "O(n²)"]),
     "answer": json.dumps([0]), "explain": "在理想哈希函数下，哈希表插入、删除、查找的平均时间复杂度均为 O(1)。",
     "topic": "数据结构", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "微服务架构中，服务间常用的注册与发现组件是？",
     "opts": json.dumps(["Nginx", "Redis", "Consul / Nacos", "Kafka"]),
     "answer": json.dumps([2]), "explain": "Consul、Nacos、Eureka 等是典型服务注册与发现组件；Nginx 是网关/负载均衡。",
     "topic": "系统设计", "difficulty": "medium"},
]


def seed_questions():
    """如果题库为空则插入种子数据"""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if count == 0:
        for q in SEED_QUESTIONS:
            conn.execute(
                "INSERT INTO questions (cat, src, type, stem, opts, answer, explain, topic, difficulty) VALUES (?,?,?,?,?,?,?,?,?)",
                (q["cat"], q["src"], q["type"], q["stem"], q["opts"], q["answer"], q["explain"], q["topic"], q["difficulty"])
            )
        conn.commit()
    conn.close()


# ================================================================
# 密码工具
# ================================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ================================================================
# 题库 API
# ================================================================
@app.get("/api/questions", response_model=list[QuestionOut])
def list_questions(cat: str | None = None):
    """获取题库列表，可按分类筛选：考研/考公/大厂"""
    conn = get_db()
    if cat and cat != "all":
        rows = conn.execute("SELECT * FROM questions WHERE cat=? ORDER BY id", (cat,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM questions ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/questions/{question_id}", response_model=QuestionOut)
def get_question(question_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "题目不存在")
    return dict(row)


# ================================================================
# 用户 API
# ================================================================
@app.post("/api/register", response_model=UserOut)
def register(data: UserRegister):
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username=?", (data.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "用户名已存在")
    if len(data.password) < 6:
        conn.close()
        raise HTTPException(400, "密码至少6位")
    h = hash_password(data.password)
    cur = conn.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (data.username, h))
    conn.commit()
    user_id = cur.lastrowid
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


@app.post("/api/login", response_model=UserOut)
def login(data: UserLogin):
    conn = get_db()
    h = hash_password(data.password)
    row = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (data.username, h)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(401, "用户名或密码错误")
    return dict(row)


# ================================================================
# 刷题记录 API
# ================================================================
@app.post("/api/quiz/record", response_model=QuizRecordOut)
def create_quiz_record(data: QuizRecordIn):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO quiz_records (user_id, cat, total, correct) VALUES (?,?,?,?)",
        (data.user_id, data.cat, data.total, data.correct)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM quiz_records WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/quiz/history/{user_id}", response_model=list[QuizRecordOut])
def get_quiz_history(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM quiz_records WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================
# 错题本 API
# ================================================================
@app.post("/api/wrong-book")
def add_wrong_question(data: WrongBookIn):
    """添加错题记录，重复错误则计数+1"""
    conn = get_db()
    existing = conn.execute(
        "SELECT id, error_count FROM wrong_book WHERE user_id=? AND question_id=?",
        (data.user_id, data.question_id)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE wrong_book SET error_count=?, last_error_at=CURRENT_TIMESTAMP WHERE id=?",
            (existing["error_count"] + 1, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO wrong_book (user_id, question_id) VALUES (?,?)",
            (data.user_id, data.question_id)
        )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/wrong-book/{user_id}", response_model=list[WrongBookOut])
def get_wrong_book(user_id: int):
    """获取用户错题本，按错误次数降序"""
    conn = get_db()
    rows = conn.execute("""
        SELECT wb.question_id, wb.error_count, wb.last_error_at,
               q.stem, q.topic, q.src, q.difficulty
        FROM wrong_book wb JOIN questions q ON wb.question_id = q.id
        WHERE wb.user_id=? ORDER BY wb.error_count DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================
# 打卡 API
# ================================================================
@app.get("/api/streak/{user_id}", response_model=StreakOut)
def get_streak(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT check_date FROM daily_streaks WHERE user_id=? ORDER BY check_date DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    dates = [r["check_date"] for r in rows]
    if not dates:
        return {"streak": 0, "last_date": None, "dates": []}

    # 计算连续天数
    today = date.today()
    streak = 0
    for d in dates:
        if d == str(today - timedelta(days=streak)):
            streak += 1
        else:
            break
    return {"streak": streak, "last_date": dates[0], "dates": dates}


@app.post("/api/checkin/{user_id}")
def checkin(user_id: int):
    today = str(date.today())
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO daily_streaks (user_id, check_date) VALUES (?,?)",
            (user_id, today)
        )
        conn.commit()
    except Exception:
        pass  # 今天已打卡
    finally:
        conn.close()
    return {"ok": True, "date": today}


# ================================================================
# 考场记录 API
# ================================================================
@app.post("/api/exam/record")
def create_exam_record(data: ExamRecordIn):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO exam_records (user_id, exam_type, total, correct, duration, time_used) VALUES (?,?,?,?,?,?)",
        (data.user_id, data.exam_type, data.total, data.correct, data.duration, data.time_used)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM exam_records WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/exam/records/{user_id}", response_model=list[ExamRecordOut])
def get_exam_records(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM exam_records WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================
# 知识点掌握度分析 API
# ================================================================
@app.get("/api/mastery/{user_id}", response_model=list[MasteryOut])
def get_mastery(user_id: int):
    """基于错题数据分析各知识点掌握度"""
    conn = get_db()
    # 从错题表按知识点统计
    rows = conn.execute("""
        SELECT q.topic,
               COUNT(DISTINCT wb.question_id) as wrong_count,
               (SELECT COUNT(*) FROM questions WHERE topic=q.topic) as total_count
        FROM wrong_book wb
        JOIN questions q ON wb.question_id = q.id
        WHERE wb.user_id=?
        GROUP BY q.topic
    """, (user_id,)).fetchall()

    # 也把没有错题的知识点（掌握度100%）加入
    all_topics = conn.execute("SELECT DISTINCT topic FROM questions").fetchall()

    result = []
    wrong_map = {r["topic"]: dict(r) for r in rows if r["topic"]}
    for t in all_topics:
        topic = t["topic"]
        # 从数据库查询该知识点总题数
        total_row = conn.execute("SELECT COUNT(*) as cnt FROM questions WHERE topic=?", (topic,)).fetchone()
        total = total_row["cnt"] if total_row else 0
        if topic in wrong_map:
            mastery = max(0, 100 - wrong_map[topic]["wrong_count"] * 15)
        else:
            mastery = 100
        result.append({"topic": topic, "total": total, "correct": total - (wrong_map[topic]["wrong_count"] if topic in wrong_map else 0), "mastery": mastery})
    conn.close()
    return result


# ================================================================
# AI 能力接口（讲题 / 变式题 / 押题报告）
#   无 API_KEY 时返回结构化降级内容，前端始终可用
# ================================================================
def _letter(i: int) -> str:
    return chr(65 + i)


def fallback_explain(q: dict) -> dict:
    opts = q.get("opts") or []
    ans = q.get("answer") or []
    return {
        "source": "fallback",
        "summary": f'本题考查「{q.get("topic", "")}」相关知识点。',
        "steps": [
            f'审题：识别题干关键信息，定位到 {q.get("topic", "")} 的考点。',
            f'分析选项：{ "；".join(f"{_letter(i)}.{o}" for i, o in enumerate(opts)) }',
            f'结合知识点判断，正确答案为 { "、".join(_letter(i) for i in ans) or "（见解析）" }。',
            f'巩固：{ q.get("explain", "") }',
        ],
        "tips": "建议把本题加入错题本，按遗忘曲线复习，并联想同类考点。",
    }


def fallback_gen(q: dict) -> dict:
    opts = q.get("opts") or []
    ans = q.get("answer") or []
    topic = q.get("topic", "")
    return {
        "source": "fallback",
        "baseTopic": topic,
        "variants": [
            {"stem": f"【变式1·同向变形】关于「{topic}」，下列说法正确的是？（基于原题考点）",
             "opts": list(opts), "answer": list(ans),
             "explain": "与原题同考点，调整了表述方式，检验你是否真正理解而非死记。"},
            {"stem": f"【变式2·反向提问】在「{topic}」中，下列哪一项是错误/不成立的描述？",
             "opts": ["（请基于原题知识点自行构造反向选项）", "B", "C", "D"],
             "answer": [0],
             "explain": "反向提问训练你对概念的边界理解，是考场高频陷阱。"},
            {"stem": f"【变式3·综合应用】将「{topic}」与相近知识点结合，最可能出现于哪类题型？",
             "opts": ["概念辨析题", "计算应用题", "材料分析题", "以上皆有可能"],
             "answer": [3],
             "explain": "综合应用是高分区的常见考法，建议结合真题进一步练习。"},
        ],
    }


def fallback_report(p: dict) -> dict:
    mastery = p.get("mastery", 0)
    weak = p.get("weakTopics") or []
    focus = "、".join(weak) if weak else "暂无显著薄弱点"
    return {
        "source": "fallback",
        "overall": f'当前整体掌握度约 {mastery}%，累计作答 {p.get("total", 0)} 题，正确 {p.get("correct", 0)} 题。',
        "prediction": (mastery >= 80 and "状态良好，保持稳定即可。"
                       or mastery >= 60 and "仍有提升空间，重点突破薄弱点。"
                       or "基础需巩固，建议回归课本系统复习。"),
        "focusTopics": focus,
        "plan": [
            "每天优先完成系统推送的薄弱点题目。",
            "对错误≥3次的题目进行深度复盘。",
            "每周做一次模拟考场，检验掌握度变化。",
        ],
        "encouragement": "坚持打卡与复盘，上岸只是时间问题。",
    }


@app.post("/api/explain")
async def api_explain(data: ExplainIn):
    q = data.question.model_dump()
    key = "explain:" + str(q.get("_idx") or q.get("stem", ""))
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        if not HAS_KEY:
            result = fallback_explain(q)
        else:
            system = ("你是资深备考讲师，擅长把题目讲透。请基于题目与官方解析，输出结构化结果："
                      "summary=简要结论, steps=步骤要点数组, tips=1句记忆/避坑建议。语言通俗、面向备考学生。")
            user = (f'题目：{q.get("stem","")}\n选项：{ " ".join(f"{_letter(i)}.{o}" for i,o in enumerate(q.get("opts",[]))) }\n'
                    f'正确答案：{ "、".join(_letter(i) for i in q.get("answer",[])) }\n'
                    f'知识点：{q.get("topic","")}\n官方解析：{q.get("explain","（无）")}')
            result = await _structured_llm(system, user, "explain_question", _EXPLAIN_SCHEMA, 600)
            if not result:
                result = fallback_explain(q)
            else:
                result["source"] = "llm"
        _cache_set(key, result)
        return result
    except Exception as e:
        print("[explain]", e)
        return fallback_explain(q)


@app.post("/api/gen")
async def api_gen(data: GenIn):
    q = data.question.model_dump()
    key = "gen:" + str(q.get("_idx") or q.get("stem", ""))
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        if not HAS_KEY:
            result = fallback_gen(q)
        else:
            system = ("你是题库命题专家。基于给定题目，生成3道「同考点」变式题，用于巩固训练。"
                      "baseTopic=原考点；variants=数组，每项含 stem/opts(4个字符串)/answer(正确项下标数组,0起)/explain。"
                      "变式应改变情境/表述/反向提问，但考查同一核心知识点。")
            user = (f'原题：{q.get("stem","")}\n选项：{ " ".join(f"{_letter(i)}.{o}" for i,o in enumerate(q.get("opts",[]))) }\n'
                    f'正确答案下标：{json.dumps(q.get("answer",[])) }\n知识点：{q.get("topic","")}\n解析：{q.get("explain","（无）")}')
            result = await _structured_llm(system, user, "gen_variants", _GEN_SCHEMA, 900)
            if not result:
                result = fallback_gen(q)
            else:
                result["source"] = "llm"
        _cache_set(key, result)
        return result
    except Exception as e:
        print("[gen]", e)
        return fallback_gen(q)


@app.post("/api/report")
async def api_report(data: ReportIn):
    p = data.model_dump()
    key = "report:" + json.dumps(p, sort_keys=True)
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        if not HAS_KEY:
            result = fallback_report(p)
        else:
            system = ("你是备考规划师。基于用户学习数据，生成考前押题/冲刺报告。"
                      "overall=总评；prediction=得分预测与判断；focusTopics=重点押题模块(字符串)；"
                      "plan=3条冲刺建议数组；encouragement=鼓励语。")
            user = (f'整体掌握度：{p.get("mastery",0)}%\n累计作答：{p.get("total",0)} 题\n'
                    f'正确：{p.get("correct",0)} 题\n薄弱知识点：{ "、".join(p.get("weakTopics",[]) or []) or "无明显薄弱点" }')
            result = await _structured_llm(system, user, "gen_report", _REPORT_SCHEMA, 700)
            if not result:
                result = fallback_report(p)
            else:
                result["source"] = "llm"
        _cache_set(key, result)
        return result
    except Exception as e:
        print("[report]", e)
        return fallback_report(p)


@app.post("/api/chat")
async def api_chat(data: ChatIn):
    """智能答疑：把用户自由提问转发给 Hermes Agent（后端代为鉴权，避免暴露 Agent 工具端口）。
    未配置 Hermes 时返回友好降级文案，前端始终可用。"""
    if not HAS_HERMES:
        return {"source": "fallback", "reply": "智能教练暂未接入，先去刷几道题热热身吧～"}
    messages = []
    if data.system:
        messages.append({"role": "system", "content": data.system})
    messages.extend(data.messages)
    url = f'{HERMES_CONFIG["BASE"]}/chat/completions'
    payload = {
        "model": HERMES_CONFIG["MODEL"],
        "messages": messages,
        "temperature": 0.7,
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                url,
                headers={"Content-Type": "application/json",
                          "Authorization": f'Bearer {HERMES_CONFIG["KEY"]}'},
                json=payload,
            )
            resp.raise_for_status()
            j = resp.json()
            reply = j.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"source": "hermes", "reply": reply}
    except Exception as e:
        print("[chat]", e)
        return {"source": "error", "reply": "教练开小差了，请稍后再问～"}


@app.get("/api/health")
def health():
    from agent.inference import QUANT_CONFIG
    from agent.channel import HUB
    ap = active_provider()
    return {"ok": True, "version": "3.7.0-channel-history-mcp",
            "ai": "enabled" if HAS_KEY else "fallback",
            "llm_provider": ap.get("name"),
            "llm_model": ap.get("model"),
            "llm_label": ap.get("label"),
            "channels": [c["name"] for c in HUB.list_channels()],
            "mcp_builtin_tools": ["exam_syllabus", "question_bank_search"],
            "mcp_remote": bool(os.getenv("MCP_SERVER_URL")),
            "hermes": "enabled" if HAS_HERMES else "off",
            "infer_opt": {"kv_cache": True, "compress": True, "speculative": True,
                          "distill": True, "continuous_batching": True,
                          "tool_substitution": True, "quant_awq": QUANT_CONFIG["enabled"]}}


# ================================================================
# 根路径重定向 + 静态文件服务
# ================================================================
@app.get("/")
def root():
    return RedirectResponse(url="/coach.html")

_STATIC_DIR = os.getenv("STATIC_DIR", os.path.dirname(DB_DIR))
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")


# ================================================================
# 启动入口
# ================================================================
if __name__ == "__main__":
    import uvicorn
    _port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=_port, reload=True)