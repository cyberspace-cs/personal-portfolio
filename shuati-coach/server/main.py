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

from database import (
    get_db, init_db, DB_DIR,
    record_bank_version, get_active_study_plan, save_study_plan,
    add_quiz_attempt_batch, get_topic_mastery, compute_profile,
)
from models import (
    ChatIn, ExamRecordIn, ExamRecordOut, ExplainIn, GenIn, MasteryOut, QuestionOut,
    QuizCheckIn, QuizRecordIn, QuizRecordOut, ReportIn, StreakOut, UserLogin,
    UserOut, UserRegister, WrongBookIn, WrongBookOut,
    PlanDay, StudyPlanRequest, StudyPlanResponse, StudyPlanSaveIn, StudyPlanOut, QuestionBankVersionOut,
    GraphNode, GraphEdge, WeakPoint, WeakPointsOut, AdaptivePlanRequest,
    WrongBookGroupOut, RelatedQuestionOut, BankUpdateOut, ProfileOut, LeaderboardItem,
    BadgeModel, ExamStartIn, ExamStartOut, ExamSubmitIn,
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
        "exam_point": {"type": "string", "description": "名师视角：本题核心考点（一句话）"},
        "pitfalls": {"type": "string", "description": "名师视角：易错点 / 考场陷阱"},
    },
    "required": ["summary", "steps", "tips", "exam_point", "pitfalls"],
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

_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "week_start": {"type": "string", "description": "周一开始日期 YYYY-MM-DD"},
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "theme": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer"},
                    "tip": {"type": "string"},
                },
                "required": ["day", "theme", "topics", "count", "tip"],
            },
        },
    },
    "required": ["week_start", "days"],
}


async def _structured_llm(system: str, user: str, tool_name: str, schema: dict, max_tokens: int = 700) -> dict:
    """用虚拟工具范式向激活厂商要结构化 JSON；返回空 dict 表示失败（调用方应降级）。

    健壮性：厂商接口偶发超时/网络抖动时自动重试一次，仍失败则降级为空 dict，
    由调用方回退到确定性 fallback，绝不让端点 500。
    """
    last: dict = {}
    for attempt in range(2):
        try:
            last = await call_llm_tool(system, user, tool_name, schema, max_tokens)
            if last:
                return last
        except Exception as e:  # 网络/超时/厂商错误 -> 重试一次后降级
            print(f"[llm:{tool_name}] 第{attempt + 1}次调用失败：{repr(e)}")
    return last

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


def _load_seed_questions():
    """优先从 data/questions.json 加载题库；缺失/异常时回退到代码内 SEED_QUESTIONS。"""
    path = os.path.join(DB_DIR, "data", "questions.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            qs = data.get("questions", [])
            if qs:
                return qs
        except Exception as e:
            print("[seed] 读取 questions.json 失败，回退硬编码题库:", e)
    return SEED_QUESTIONS


def _norm(v):
    """opts/answer 兼容 'JSON 字符串' 与 '列表' 两种格式，统一转成 JSON 字符串入库。"""
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def seed_questions():
    """如果题库为空则插入种子数据（来自 questions.json 或代码内 SEED_QUESTIONS）。"""
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if count == 0:
        qs = _load_seed_questions()
        for q in qs:
            conn.execute(
                "INSERT INTO questions (cat, src, type, stem, opts, answer, explain, topic, difficulty) VALUES (?,?,?,?,?,?,?,?,?)",
                (q["cat"], q["src"], q["type"], q["stem"],
                 _norm(q["opts"]), _norm(q["answer"]), q["explain"], q["topic"], q["difficulty"])
            )
        conn.commit()
        print(f"[seed] 已插入题库 {len(qs)} 题")
    else:
        print(f"[seed] 题库已有 {count} 题，跳过初始化")
    conn.close()


# ================================================================
# 密码工具
# ================================================================
def hash_password(password: str) -> str:
    """加盐 SHA-256：存储格式 `salt$hash`，避免相同密码产生相同哈希。"""
    import hmac
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    """校验密码：兼容升级前的无盐哈希（旧库）与新版加盐哈希。"""
    import hmac
    if not stored or "$" not in stored:
        # 兼容升级前的无盐哈希
        return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), stored or "")
    salt, h = stored.split("$", 1)
    return hmac.compare_digest(hashlib.sha256((salt + password).encode()).hexdigest(), h)


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


@app.get("/api/questions/sample")
def sample_questions(
    cat: str | None = None,
    src: str | None = None,
    topic: str | None = None,
    difficulty: str | None = None,
    limit: int = 150,
):
    """随机抽取题（示例刷题 / 随机刷题），避免一次性把全库 2 万+ 题拉到前端。"""
    limit = max(1, min(int(limit or 150), 500))
    conn = get_db()
    sql = "SELECT * FROM questions WHERE 1=1"
    args: list = []
    if cat and cat != "all":
        sql += " AND cat=?"
        args.append(cat)
    if src:
        sql += " AND src=?"
        args.append(src)
    if topic:
        sql += " AND topic=?"
        args.append(topic)
    if difficulty and difficulty != "all":
        sql += " AND difficulty=?"
        args.append(difficulty)
    sql += " ORDER BY RANDOM() LIMIT ?"
    args.append(limit)
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/questions/page")
def page_questions(
    offset: int = 0,
    limit: int = 30,
    cat: str | None = None,
    src: str | None = None,
    topic: str | None = None,
    difficulty: str | None = None,
    q: str | None = None,
):
    """分页浏览全量题库（全量题库抽屉用），支持按分类/来源/知识点/难度/关键词过滤。"""
    offset = max(0, int(offset or 0))
    limit = max(1, min(int(limit or 30), 100))
    conn = get_db()
    where = ""
    args: list = []
    if cat and cat != "all":
        where += " AND cat=?"
        args.append(cat)
    if src:
        where += " AND src=?"
        args.append(src)
    if topic:
        where += " AND topic=?"
        args.append(topic)
    if difficulty and difficulty != "all":
        where += " AND difficulty=?"
        args.append(difficulty)
    if q:
        where += " AND stem LIKE ?"
        args.append("%" + q + "%")
    total = conn.execute("SELECT COUNT(*) FROM questions WHERE 1=1" + where, args).fetchone()[0]
    rows = conn.execute(
        "SELECT id, cat, src, type, topic, difficulty, stem FROM questions WHERE 1=1"
        + where
        + " ORDER BY id LIMIT ? OFFSET ?",
        args + [limit, offset],
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [dict(r) for r in rows],
    }


@app.get("/api/questions/meta")
def questions_meta():
    """公开展示题库概况（无需登录），用于首页/demo 展示与体验模式统计。
    额外返回题库版本信息（version/sources/checksum），由 questions.json 提供。"""
    from collections import Counter
    conn = get_db()
    rows = conn.execute("SELECT cat, type, src, difficulty, topic FROM questions").fetchall()
    conn.close()
    cats = Counter(r["cat"] for r in rows)
    types = Counter(r["type"] for r in rows)
    srcs = Counter(r["src"] for r in rows)
    diff = Counter(r["difficulty"] for r in rows)
    topics = Counter(r["topic"] for r in rows)

    # 版本元信息（来自 data/questions.json）
    meta_extra = {"version": None, "generated_at": None, "sources": dict(srcs), "checksum": ""}
    try:
        qj_path = os.path.join(DB_DIR, "data", "questions.json")
        if os.path.exists(qj_path):
            with open(qj_path, "r", encoding="utf-8") as f:
                qj = json.load(f)
            meta_extra["version"] = qj.get("version")
            meta_extra["generated_at"] = qj.get("generated_at")
            # 注意：sources 始终用实时库 GROUP BY 统计（见上方 srcs），
            # 保证「多源题库聚合状态」卡片与实际题量一致；
            # 不再用 questions.json 的静态快照覆盖，否则会与 total 对不上。
            meta_extra["checksum"] = qj.get("checksum", "")
    except Exception:
        pass

    # 最近一次题库版本更新时间（来自 question_bank_versions 审计表）
    updated_at = None
    try:
        conn2 = get_db()
        vr = conn2.execute(
            "SELECT created_at, version, checksum, status FROM question_bank_versions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn2.close()
        if vr:
            updated_at = vr["created_at"]
            # 若 JSON 无版本，用审计表版本兜底
            if meta_extra["version"] is None and vr["version"]:
                meta_extra["version"] = vr["version"]
    except Exception:
        pass

    return {
        "total": len(rows),
        "cats": dict(cats),
        "types": dict(types),
        "sources": meta_extra["sources"],
        "difficulty": dict(diff),
        "topics": dict(topics),
        "version": meta_extra["version"],
        "generated_at": meta_extra["generated_at"],
        "updated_at": updated_at,
        "checksum": meta_extra["checksum"],
    }


@app.post("/api/bank/update", response_model=BankUpdateOut)
def bank_update():
    """题库元信息定时更新：统计当前题库规模/来源，写入一条新版本记录（审计+回滚），返回最新元信息。

    演示环境无外部爬虫，故以"重新计量 + 落版本记录"模拟每日/每周的题库同步更新机制。
    """
    import hashlib as _hl
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, cat, src, topic FROM questions").fetchall()
        total = len(rows)
        src_counter = {}
        for r in rows:
            src_counter[r["src"]] = src_counter.get(r["src"], 0) + 1
        # 计算校验和（基于题目 id+src 的确定性指纹）
        digest_src = "|".join(f"{r['id']}:{r['src']}" for r in rows)
        checksum = _hl.md5(digest_src.encode("utf-8")).hexdigest()[:12]
        # 最近版本 +1
        prev = conn.execute("SELECT MAX(version) AS v FROM question_bank_versions").fetchone()
        new_version = (prev["v"] or 0) + 1
        # 落库
        cur = conn.execute(
            "INSERT INTO question_bank_versions (version, count, sources_json, summary, status, checksum) "
            "VALUES (?,?,?,?,?,?)",
            (new_version, total, json.dumps(src_counter, ensure_ascii=False),
             f"定时同步：题库共 {total} 题，来源 {len(src_counter)} 个平台", "published", checksum),
        )
        conn.commit()
        row_id = cur.lastrowid
        vrow = conn.execute(
            "SELECT version, count, sources_json, summary, status, checksum, created_at FROM question_bank_versions WHERE id=?",
            (row_id,),
        ).fetchone()
    finally:
        conn.close()
    return BankUpdateOut(
        version=vrow["version"], count=vrow["count"],
        sources=json.loads(vrow["sources_json"] or "{}"),
        checksum=vrow["checksum"], updated_at=vrow["created_at"], summary=vrow["summary"],
    )


@app.get("/api/daily")
def daily_question():
    """每日一题：按日期确定性选题（当天稳定、跨天轮换），无需登录。

    与竞品（LeetCode 每日一题 / 洛谷每日一题）一致的"每日更新"机制——
    用户每天打开都能看到一道由日期稳定推导的题目，跨天自动轮换，形成打卡习惯。
    """
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT id, cat, src, type, stem, opts, answer, explain, topic, difficulty "
        "FROM questions ORDER BY id"
    ).fetchall()
    conn.close()
    if not rows:
        return {"date": today, "question": None}
    n = len(rows)
    # 用日期字符串做稳定哈希，保证当天不变、跨天轮换、且覆盖全库
    h = int(hashlib.md5(today.encode("utf-8")).hexdigest(), 16)
    q = dict(rows[h % n])
    return {"date": today, "question": q}


@app.post("/api/quiz/check")
def check_quiz(data: QuizCheckIn):
    """匿名判分（体验模式）：给定作答返回每题对错、正确答案与解析，不落库。
    前端可在未登录时调用，体验完整刷题+讲解流程。"""
    conn = get_db()
    results = []
    correct_count = 0
    for item in data.items:
        row = conn.execute("SELECT * FROM questions WHERE id=?", (item.question_id,)).fetchone()
        if not row:
            continue
        q = dict(row)
        correct_ans = json.loads(q["answer"]) if isinstance(q["answer"], str) else q["answer"]
        ok = sorted(item.selected) == sorted(correct_ans)
        if ok:
            correct_count += 1
        results.append({
            "id": q["id"],
            "correct": ok,
            "correct_answer": correct_ans,
            "explain": q["explain"],
            "topic": q["topic"],
            "stem": q["stem"],
            "type": q["type"],
        })
    conn.close()
    return {"total": len(results), "correct": correct_count, "results": results}


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
    return {"id": row["id"], "user_id": row["id"], "username": row["username"], "created_at": row["created_at"] or ""}


@app.post("/api/login", response_model=UserOut)
def login(data: UserLogin):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (data.username,)).fetchone()
    conn.close()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(401, "用户名或密码错误")
    return {"id": row["id"], "user_id": row["id"], "username": row["username"], "created_at": row["created_at"] or ""}


# ================================================================
# 刷题记录 API
# ================================================================
@app.post("/api/quiz/record", response_model=QuizRecordOut)
def create_quiz_record(data: QuizRecordIn):
    # 体验模式（匿名）：不落库，仅回显
    if data.user_id is None:
        return {"ok": True, "demo": True, "id": 0, "user_id": 0,
                "cat": data.cat, "total": data.total, "correct": data.correct, "created_at": ""}
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


@app.post("/api/quiz/attempt")
def log_quiz_attempt(data: QuizCheckIn):
    """批量记录逐题作答明细（弱项诊断 / 知识图谱 / 自适应的数据底座）。匿名用户不落库。"""
    if data.user_id is None:
        return {"ok": True, "demo": True, "count": 0}
    items = []
    conn = get_db()
    for it in data.items:
        q = conn.execute("SELECT topic, cat FROM questions WHERE id=?", (it.question_id,)).fetchone()
        if not q:
            continue
        # 该题是否已在该次提交中：前端按逐题正确性给出 correct 标记
        items.append({
            "question_id": it.question_id,
            "topic": q["topic"],
            "cat": q["cat"],
            "correct": 1 if getattr(it, "correct", None) else 0,
        })
    conn.close()
    try:
        add_quiz_attempt_batch(data.user_id, items)
    except Exception as e:
        print("[quiz/attempt] 记录失败（已忽略）:", e)
    return {"ok": True, "count": len(items)}


# ================================================================
# 错题本 API
# ================================================================
@app.post("/api/wrong-book")
def add_wrong_question(data: WrongBookIn):
    """添加错题记录，重复错误则计数+1（匿名体验模式不落库）"""
    if data.user_id is None:
        return {"ok": True, "demo": True}
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


@app.get("/api/wrong-book/group/{user_id}", response_model=WrongBookGroupOut)
def get_wrong_book_grouped(user_id: int):
    """错题本智能归类：按知识点 topic 分组，便于同类集中复盘。"""
    conn = get_db()
    rows = conn.execute("""
        SELECT wb.question_id, wb.error_count, wb.last_error_at,
               q.stem, q.topic, q.src, q.difficulty
        FROM wrong_book wb JOIN questions q ON wb.question_id = q.id
        WHERE wb.user_id=? ORDER BY wb.error_count DESC
    """, (user_id,)).fetchall()
    conn.close()
    flat = [dict(r) for r in rows]
    grouped = {}
    for r in flat:
        grouped.setdefault(r["topic"], []).append(dict(r))
    return WrongBookGroupOut(grouped=grouped, flat=flat)


@app.get("/api/related-questions", response_model=list[RelatedQuestionOut])
def get_related_questions(qid: int, limit: int = 5):
    """举一反三：返回与给定题目同知识点(topic)的其他题目（排除自身），用于同类巩固。"""
    conn = get_db()
    q = conn.execute("SELECT topic FROM questions WHERE id=?", (qid,)).fetchone()
    if not q:
        conn.close()
        return []
    topic = q["topic"]
    rows = conn.execute(
        "SELECT id, cat, src, type, stem, opts, answer, explain, topic, difficulty "
        "FROM questions WHERE topic=? AND id<>? ORDER BY RANDOM() LIMIT ?",
        (topic, qid, limit),
    ).fetchall()
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
    if data.user_id is None:
        return {"ok": True, "demo": True, "id": 0, "user_id": 0,
                "exam_type": data.exam_type, "total": data.total, "correct": data.correct,
                "duration": data.duration, "time_used": data.time_used, "created_at": ""}
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
# 自适应模拟考场（Step ⑧）
# ================================================================
@app.post("/api/exam/start", response_model=ExamStartOut)
def exam_start(data: ExamStartIn):
    """自适应组卷：登录用户优先抽取薄弱知识点题目（约 60%），并混合难度；匿名用户从分类随机抽题。"""
    conn = get_db()
    try:
        pool = conn.execute(
            "SELECT id, topic, difficulty FROM questions WHERE cat=? ORDER BY id", (data.cat,)
        ).fetchall()
    finally:
        conn.close()
    if not pool:
        return ExamStartOut(question_ids=[], adaptive=False, difficulty_note="该分类暂无题目")
    pool_ids = [r["id"] for r in pool]

    if data.user_id:
        master = get_topic_mastery(data.user_id)
        # 知识点按掌握度升序 → 最弱优先
        topic_mastery = {}
        for r in pool:
            t = r["topic"]
            topic_mastery.setdefault(t, master.get(t, {"mastery": 50})["mastery"])
        weak_topics = sorted(set(topic_mastery), key=lambda t: topic_mastery[t])
        weak_pool = [r["id"] for r in pool if r["topic"] in weak_topics[: max(1, len(weak_topics) // 2)]]
        strong_pool = [r["id"] for r in pool if r["id"] not in weak_pool]
        import random as _rnd
        _rnd.seed()
        weak_n = min(len(weak_pool), max(1, int(data.count * 0.6)))
        strong_n = min(len(strong_pool), data.count - weak_n)
        chosen = _rnd.sample(weak_pool, weak_n) + _rnd.sample(strong_pool, strong_n) if weak_pool and strong_pool else (_rnd.sample(pool_ids, min(data.count, len(pool_ids))))
        # 若不足，补随机
        while len(chosen) < min(data.count, len(pool_ids)):
            add = _rnd.choice(pool_ids)
            if add not in chosen:
                chosen.append(add)
        note = f"已为你自适应组卷：优先抽取 {weak_n} 道薄弱知识点题 + {strong_n} 道巩固题"
        return ExamStartOut(question_ids=chosen[:data.count], adaptive=True, difficulty_note=note)
    else:
        import random as _rnd
        _rnd.seed()
        chosen = _rnd.sample(pool_ids, min(data.count, len(pool_ids)))
        return ExamStartOut(question_ids=chosen, adaptive=False, difficulty_note="体验模式：分类随机组卷（登录后启用自适应）")


@app.post("/api/exam/submit", response_model=dict)
def exam_submit(data: ExamSubmitIn):
    """自适应交卷：记录考场成绩 + 逐题诊断 + 打卡；返回本次最需巩固的薄弱点。"""
    # 记录逐题诊断
    if data.user_id and data.attempts:
        try:
            add_quiz_attempt_batch(data.user_id, data.attempts)
        except Exception as e:
            print("[exam/submit] 逐题诊断记录失败（已忽略）:", e)
    # 记录考场成绩
    if data.user_id is not None:
        conn = get_db()
        conn.execute(
            "INSERT INTO exam_records (user_id, exam_type, total, correct, duration, time_used) VALUES (?,?,?,?,?,?)",
            (data.user_id, data.exam_type, data.total, data.correct, data.duration, data.time_used),
        )
        conn.execute(
            "INSERT OR IGNORE INTO daily_streaks (user_id, check_date) VALUES (?,?)",
            (data.user_id, str(date.today())),
        )
        conn.commit()
        conn.close()
    # 计算自适应反馈（最弱知识点）
    weak_topics = data.weak_topics or []
    if data.user_id:
        master = get_topic_mastery(data.user_id)
        weak_topics = sorted(master, key=lambda t: master[t]["mastery"])[:3]
    accuracy = round(data.correct / data.total * 100) if data.total else 0
    feedback = (
        "本次自适应诊断完成！" + (f"建议重点巩固：{ '、'.join(weak_topics) }。" if weak_topics else "继续保持，薄弱点不明显。")
    )
    return {
        "ok": True,
        "score": accuracy,
        "accuracy": accuracy,
        "weak_topics": weak_topics,
        "adaptive_feedback": feedback,
        "recorded": data.user_id is not None,
    }


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
# 薄弱知识点知识图谱诊断（Step ②）
# ================================================================
@app.get("/api/weak-points/{user_id}", response_model=WeakPointsOut)
def get_weak_points(user_id: int):
    """基于逐题作答明细，诊断薄弱知识点并构建知识点→分类的知识图谱。

    图谱节点：全部题库知识点(topic) + 分类(cat)；边：topic→所属 cat。
    每个 topic 节点带掌握度（来自 quiz_attempts，无作答记录为 null）。
    """
    conn = get_db()
    try:
        # 知识点掌握度（来自逐题作答明细）
        master = get_topic_mastery(user_id)
        # 全部题库知识点与分类，构建完整知识图谱
        topics = conn.execute("SELECT DISTINCT topic, cat FROM questions WHERE topic<>'' ORDER BY cat, topic").fetchall()
        cats = conn.execute("SELECT DISTINCT cat FROM questions WHERE cat<>'' ORDER BY cat").fetchall()
        # 也保留基于错题的弱项（无作答记录时仍有价值）
        wrong_rows = conn.execute("""
            SELECT q.topic, COUNT(DISTINCT wb.question_id) as wrong_count
            FROM wrong_book wb JOIN questions q ON wb.question_id=q.id
            WHERE wb.user_id=? GROUP BY q.topic
        """, (user_id,)).fetchall()
        wrong_map = {r["topic"]: r["wrong_count"] for r in wrong_rows}
    finally:
        conn.close()

    cat_nodes = []
    for c in cats:
        cat = c["cat"]
        cat_nodes.append(GraphNode(id="cat:" + cat, label=cat, type="cat", cat=cat))
    topic_nodes = []
    edges = []
    weak = []
    for t in topics:
        topic = t["topic"]; cat = t["cat"]
        m = master.get(topic)
        if m:
            mastery = m["mastery"]
            total = m["total"]; correct = m["correct"]
        else:
            # 没有逐题记录但有错题：用错题数估算一个偏低掌握度，体现"薄弱"
            wc = wrong_map.get(topic, 0)
            mastery = max(0, 100 - wc * 20) if wc else None
            total = wc; correct = max(0, wc - wc)
        node = GraphNode(id="topic:" + topic, label=topic, type="topic", cat=cat, mastery=mastery)
        topic_nodes.append(node)
        edges.append(GraphEdge(source="topic:" + topic, target="cat:" + cat))
        if mastery is not None:
            weak_score = 100 - mastery
            weak.append(WeakPoint(topic=topic, cat=cat, total=total, correct=correct, mastery=mastery, weak_score=weak_score))
    weak.sort(key=lambda x: x.weak_score, reverse=True)

    nodes = cat_nodes + topic_nodes
    return WeakPointsOut(weak=weak, graph={"nodes": [n.model_dump() for n in nodes], "edges": [e.model_dump() for e in edges]})


# ================================================================
# AI 学习计划（诊断 → 可执行日程）
# ================================================================
def _build_study_context(user_id, cat, days):
    """聚合用户数据，构造学习计划上下文。匿名(user_id=None)仅用题库总体分布。"""
    conn = get_db()
    try:
        if user_id:
            mastery_rows = conn.execute("""
                SELECT q.topic, COUNT(DISTINCT wb.question_id) as wrong_count
                FROM wrong_book wb JOIN questions q ON wb.question_id=q.id
                WHERE wb.user_id=? GROUP BY q.topic
            """, (user_id,)).fetchall()
            weak = []
            for r in mastery_rows:
                topic = r["topic"]
                total = conn.execute("SELECT COUNT(*) cnt FROM questions WHERE topic=?", (topic,)).fetchone()["cnt"]
                m = 100 - (r["wrong_count"] * 15)
                weak.append((topic, max(0, m)))
            weak.sort(key=lambda x: x[1])  # 掌握度最低排前
            weak_topics = [t for t, _ in weak[:8]]
            rec = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM quiz_records WHERE user_id=?", (user_id,)).fetchone()
            quiz_count = rec["c"]
            quiz_total = rec["t"]
            streak = 0  # 连续天数由 /api/streak 计算，此处仅作上下文占位
        else:
            weak_topics = []
            quiz_count = 0
            quiz_total = 0
            streak = 0
        all_topics = [r["topic"] for r in conn.execute("SELECT DISTINCT topic FROM questions").fetchall()]
        cats = [r["cat"] for r in conn.execute("SELECT DISTINCT cat FROM questions").fetchall()]
    finally:
        conn.close()
    return {
        "user_id": user_id, "cat": cat, "days": days,
        "weak_topics": weak_topics, "all_topics": all_topics, "cats": cats,
        "quiz_count": quiz_count, "quiz_total": quiz_total, "streak": streak,
    }


@app.post("/api/study-plan", response_model=StudyPlanResponse)
async def api_study_plan(data: StudyPlanRequest):
    """生成 AI 学习计划：登录用户基于个人数据，匿名返回示例预览。LLM 失败降级。"""
    ctx = _build_study_context(data.user_id, data.cat, data.days)
    cat_line = f"目标分类：{data.cat}" if data.cat else "目标分类：全部（考研/考公/大厂）"
    weak_line = "、".join(ctx["weak_topics"]) if ctx["weak_topics"] else "（暂无错题数据，按题库知识点示例规划）"
    user_line = "已登录用户（基于个人错题/练习数据）" if data.user_id else "匿名访客（仅示例预览，不读取个人数据）"
    system = (
        "你是备考规划教练。根据用户薄弱知识点与目标，生成一份结构化的每日学习计划。"
        "计划需可执行：每天一个主题、若干知识点、建议题量、一句复习贴士。只输出结构化 JSON，不要解释。"
    )
    user = (
        f"{user_line}。{cat_line}。计划天数：{data.days} 天。\n"
        f"薄弱知识点（掌握度从低到高）：{weak_line}\n"
        f"全知识点库：{'、'.join(ctx['all_topics'])}\n"
        f"历史练习次数：{ctx['quiz_count']}，累计题量：{ctx['quiz_total']}，连续打卡：{ctx['streak']} 天。\n"
        f"请输出 week_start（本周一 YYYY-MM-DD）与 days 数组（每天含 day/theme/topics/count/tip）。"
    )
    plan = await _structured_llm(system, user, "study_plan", _PLAN_SCHEMA, max_tokens=900)
    if not plan or not plan.get("days"):
        plan = fallback_study_plan(ctx["weak_topics"], ctx["all_topics"], data.cat or "", data.days)
        return StudyPlanResponse(fallback=True, plan=plan)
    norm_days = []
    for d in plan.get("days", [])[: data.days]:
        norm_days.append({
            "day": int(d.get("day", len(norm_days) + 1)),
            "theme": str(d.get("theme", "")),
            "topics": [str(x) for x in (d.get("topics") or [])],
            "count": int(d.get("count", 15) or 15),
            "tip": str(d.get("tip", "")),
        })
    plan["days"] = norm_days
    return StudyPlanResponse(fallback=False, plan=plan)


@app.get("/api/study-plan/{user_id}", response_model=StudyPlanOut)
def get_study_plan(user_id: int):
    """读取用户当前活跃学习计划。"""
    row = get_active_study_plan(user_id)
    if not row:
        raise HTTPException(404, "暂无保存的学习计划")
    return row


@app.post("/api/study-plan/save", response_model=StudyPlanOut)
def save_study_plan_api(data: StudyPlanSaveIn):
    """保存（UPSERT）当前活跃学习计划：旧计划置为非活跃，插入新计划。"""
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE id=?", (data.user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(400, "用户不存在，无法保存计划")
    conn.close()
    try:
        rid = save_study_plan(data.user_id, data.cat, data.plan_json, data.week_start)
    except Exception as e:
        raise HTTPException(400, "保存失败：" + str(e))
    conn = get_db()
    row = conn.execute("SELECT * FROM study_plans WHERE id=?", (rid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "保存失败")
    return dict(row)


# ================================================================
# 学习激励 / 段位 / 榜单（Step ⑦）
# ================================================================
@app.get("/api/profile/{user_id}", response_model=ProfileOut)
def get_profile(user_id: int):
    """成长画像：经验值 / 等级 / 段位 / 徽章 / 准确率。"""
    try:
        p = compute_profile(user_id)
    except Exception as e:
        print("[profile]", e)
        raise HTTPException(500, "计算画像失败")
    p["badges"] = [b.model_dump() for b in [BadgeModel(**b) for b in p["badges"]]]
    return ProfileOut(**p)


@app.get("/api/leaderboard", response_model=list[LeaderboardItem])
def get_leaderboard(limit: int = 20):
    """段位榜单：按经验值对所有用户排名（仅展示有学习记录的用户）。"""
    conn = get_db()
    try:
        users = conn.execute("SELECT id, username FROM users ORDER BY id").fetchall()
    finally:
        conn.close()
    items = []
    for u in users:
        try:
            p = compute_profile(u["id"])
        except Exception:
            continue
        if p["exp"] <= 0:
            continue
        items.append(LeaderboardItem(
            user_id=u["id"], username=u["username"], exp=p["exp"],
            level=p["level"], level_name=p["level_name"], accuracy=p["accuracy"],
        ))
    items.sort(key=lambda x: x.exp, reverse=True)
    return items[:limit]


# ================================================================
# 自适应学习计划（Step ③）：基于逐题掌握度，优先攻克最弱知识点
# ================================================================
def _weak_topics_from_mastery(user_id, cat=None, limit=8):
    """从逐题作答明细 / 错题本推导薄弱知识点（掌握度升序）。"""
    conn = get_db()
    try:
        master = get_topic_mastery(user_id)
        rows = conn.execute("""
            SELECT q.topic, COUNT(DISTINCT wb.question_id) as wrong_count
            FROM wrong_book wb JOIN questions q ON wb.question_id=q.id
            WHERE wb.user_id=? GROUP BY q.topic
        """, (user_id,)).fetchall()
    finally:
        conn.close()
    wrong_map = {r["topic"]: r["wrong_count"] for r in rows}
    scored = []
    # 优先用逐题掌握度
    for topic, m in master.items():
        if cat:
            # 仅在指定分类下
            pass
        scored.append((topic, m["mastery"]))
    # 补充仅有错题、无逐题记录的知识点
    for topic, wc in wrong_map.items():
        if topic not in master:
            scored.append((topic, max(0, 100 - wc * 20)))
    scored.sort(key=lambda x: x[1])  # 掌握度从低到高
    return [t for t, _ in scored[:limit]]


@app.post("/api/study-plan/adaptive", response_model=StudyPlanResponse)
async def api_study_plan_adaptive(data: AdaptivePlanRequest):
    """自适应计划：以逐题掌握度诊断出的薄弱知识点为主线，按"最弱优先"排布每日训练。"""
    weak_topics = _weak_topics_from_mastery(data.user_id) if data.user_id else []
    if data.cat and weak_topics:
        # 过滤到目标分类（若题库 topic 已含分类语义则不过滤，这里仅作上下文）
        pass
    all_topics = []
    conn = get_db()
    try:
        all_topics = [r["topic"] for r in conn.execute("SELECT DISTINCT topic FROM questions WHERE topic<>''").fetchall()]
    finally:
        conn.close()
    cat_line = f"目标分类：{data.cat}" if data.cat else "目标分类：全部（考研/考公/大厂）"
    weak_line = "、".join(weak_topics) if weak_topics else "（暂无逐题诊断数据，按题库知识点示例规划）"
    system = (
        "你是备考规划教练。基于用户薄弱知识点掌握度，生成一份『自适应』每日计划："
        "优先安排最弱知识点，每天一个主题、若干知识点、建议题量、一句复习贴士。只输出结构化 JSON。"
    )
    user = (
        f"匿名访客（仅示例）" if not data.user_id else "已登录用户（基于逐题诊断数据）"
        f"。{cat_line}。计划天数：{data.days} 天。\n"
        f"自适应薄弱主线（掌握度从低到高）：{weak_line}\n"
        f"全知识点库：{'、'.join(all_topics)}\n"
        f"请按『最弱优先』原则排布 days 数组（每天含 day/theme/topics/count/tip）。"
    )
    plan = await _structured_llm(system, user, "study_plan_adaptive", _PLAN_SCHEMA, max_tokens=900)
    if not plan or not plan.get("days"):
        plan = fallback_study_plan(weak_topics, all_topics, data.cat or "", data.days)
        return StudyPlanResponse(fallback=True, plan=plan, weak_topics=weak_topics)
    norm_days = []
    for d in plan.get("days", [])[: data.days]:
        norm_days.append({
            "day": int(d.get("day", len(norm_days) + 1)),
            "theme": str(d.get("theme", "")),
            "topics": [str(x) for x in (d.get("topics") or [])],
            "count": int(d.get("count", 15) or 15),
            "tip": str(d.get("tip", "")),
        })
    plan["days"] = norm_days
    return StudyPlanResponse(fallback=False, plan=plan, weak_topics=weak_topics)


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
        "exam_point": f'核心考点：{q.get("topic", "")}（{q.get("difficulty", "medium")}难度）',
        "pitfalls": "注意排除干扰项，先判考点再下结论，避免凭直觉选答。",
        "teacher": {"exam_point": f'核心考点：{q.get("topic", "")}', "pitfalls": "考场常见陷阱：混淆相近概念、忽略题干限定词。"},
    }


def _explain_style_prompt(style: str) -> str:
    if style == "concise":
        return "请用极简风格讲题：summary 一句话结论，steps 不超过 3 条，直击要点。"
    if style == "story":
        return "请用生动类比 / 生活化故事讲题，让抽象考点更易记忆，steps 可带场景化描述。"
    return "讲解需条理清晰、面向备考学生。"


def fallback_study_plan(weak_topics: list, all_topics: list, cat: str, days: int = 7) -> dict:
    """确定性降级：按薄弱知识点升序铺满 days 天，无 LLM 也可用。"""
    from datetime import timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_start = monday.isoformat()
    pool = list(weak_topics) if weak_topics else list(all_topics)
    if not pool:
        pool = ["综合巩固"]
    plan_days = []
    for i in range(days):
        t = pool[i % len(pool)]
        plan_days.append({
            "day": i + 1,
            "theme": f"第{i + 1}天 · {t}",
            "topics": [t],
            "count": 15,
            "tip": "先复习概念再做题，错题当晚复盘。",
        })
    return {"week_start": week_start, "days": plan_days}


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
    style = data.style or "default"
    key = "explain:" + style + ":" + str(q.get("_idx") or q.get("stem", ""))
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        if not HAS_KEY:
            result = fallback_explain(q)
        else:
            system = ("你是资深备考讲师，擅长把题目讲透（双师模式）。请基于题目与官方解析输出结构化结果："
                      "summary=简要结论；steps=步骤要点数组；tips=1句记忆/避坑建议；"
                      "exam_point=名师视角一句话核心考点；pitfalls=名师视角易错点/考场陷阱。"
                      + _explain_style_prompt(style))
            user = (f'题目：{q.get("stem","")}\n选项：{ " ".join(f"{_letter(i)}.{o}" for i,o in enumerate(q.get("opts",[]))) }\n'
                    f'正确答案：{ "、".join(_letter(i) for i in q.get("answer",[])) }\n'
                    f'知识点：{q.get("topic","")}\n官方解析：{q.get("explain","（无）")}')
            result = await _structured_llm(system, user, "explain_question", _EXPLAIN_SCHEMA, 700)
            if not result:
                result = fallback_explain(q)
            else:
                result["source"] = "llm"
                result["teacher"] = {
                    "exam_point": result.get("exam_point", ""),
                    "pitfalls": result.get("pitfalls", ""),
                }
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