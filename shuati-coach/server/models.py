"""Pydantic 数据模型"""
from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: int
    cat: str
    src: str
    type: str
    stem: str
    opts: str  # JSON 字符串
    answer: str  # JSON 字符串
    explain: str
    topic: str
    difficulty: str


class QuizRecordIn(BaseModel):
    user_id: int | None = None  # 匿名体验模式可为空，不落库
    cat: str
    total: int
    correct: int


class QuizRecordOut(BaseModel):
    id: int
    user_id: int
    cat: str
    total: int
    correct: int
    created_at: str


class WrongBookIn(BaseModel):
    user_id: int | None = None
    question_id: int


class WrongBookOut(BaseModel):
    question_id: int
    error_count: int
    last_error_at: str
    stem: str
    topic: str
    src: str
    difficulty: str


class ExamRecordIn(BaseModel):
    user_id: int | None = None
    exam_type: str
    total: int
    correct: int
    duration: int
    time_used: str


class ExamRecordOut(BaseModel):
    id: int
    user_id: int
    exam_type: str
    total: int
    correct: int
    duration: int
    time_used: str
    created_at: str


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    user_id: int
    username: str
    created_at: str


# ===== 匿名判分（体验模式，免登录） =====
class QuizCheckItem(BaseModel):
    question_id: int
    selected: list[int] = []   # 用户选择的下标
    correct: bool | None = None  # 该次作答是否正确（供逐题明细记录）


class QuizCheckIn(BaseModel):
    user_id: int | None = None  # 匿名体验模式可为空，不落库
    cat: str | None = None
    items: list[QuizCheckItem] = []


class StreakOut(BaseModel):
    streak: int
    last_date: str | None
    dates: list[str]


class MasteryOut(BaseModel):
    topic: str
    total: int
    correct: int
    mastery: int


# ===== AI 接口入参 =====
class QuestionPayload(BaseModel):
    _idx: int | None = None
    stem: str
    opts: list[str] = []
    answer: list[int] = []
    topic: str = ""
    explain: str = ""


class ExplainIn(BaseModel):
    question: QuestionPayload


class GenIn(BaseModel):
    question: QuestionPayload


class ReportIn(BaseModel):
    mastery: int = 0
    total: int = 0
    correct: int = 0
    weakTopics: list[str] = []


# ===== 智能答疑（转发 Hermes Agent） =====
class ChatIn(BaseModel):
    messages: list[dict] = []
    system: str = ""


# ===== AI 学习计划 =====
class PlanDay(BaseModel):
    day: int
    theme: str = ""
    topics: list[str] = []
    count: int = 0
    tip: str = ""


class StudyPlanRequest(BaseModel):
    user_id: int | None = None   # 匿名(None) → 返回示例计划，不读个人数据
    cat: str | None = None      # 目标分类：考研/考公/大厂
    days: int = 7


class StudyPlanResponse(BaseModel):
    fallback: bool = False
    plan: dict = {}             # { week_start, days:[PlanDay] }
    weak_topics: list[str] = []  # 自适应主线（最弱优先）


class StudyPlanSaveIn(BaseModel):
    user_id: int
    cat: str = ""
    plan_json: str              # 已序列化的计划 JSON
    week_start: str = ""


class StudyPlanOut(BaseModel):
    id: int
    user_id: int
    cat: str
    plan_json: str
    week_start: str
    is_active: int
    created_at: str


class QuestionBankVersionOut(BaseModel):
    version: int
    count: int
    sources_json: str
    summary: str
    status: str
    checksum: str
    created_at: str


# ===== 薄弱知识点知识图谱（Step ②） =====
class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "topic"          # topic | cat
    cat: str = ""
    mastery: int | None = None   # 0-100，无作答记录为 None


class GraphEdge(BaseModel):
    source: str
    target: str


class WeakPoint(BaseModel):
    topic: str
    cat: str
    total: int = 0
    correct: int = 0
    mastery: int = 0
    weak_score: int = 0          # 100 - mastery，越大越弱


class WeakPointsOut(BaseModel):
    weak: list[WeakPoint]
    graph: dict = {"nodes": [], "edges": []}


# ===== 自适应学习计划（Step ③） =====
class AdaptivePlanRequest(BaseModel):
    user_id: int | None = None
    cat: str | None = None
    days: int = 7


# ===== 错题本归类 + 举一反三（Step ④） =====
class WrongBookGroupOut(BaseModel):
    grouped: dict = {}
    flat: list = []


class RelatedQuestionOut(BaseModel):
    id: int
    cat: str
    src: str
    type: str
    stem: str
    opts: str
    answer: str
    explain: str
    topic: str
    difficulty: str


# ===== 双师讲题（Step ⑤） =====
class ExplainIn(BaseModel):
    question: QuestionPayload
    style: str = "default"        # default | concise | story


# ===== 题库元信息更新（Step ⑥） =====
class BankUpdateOut(BaseModel):
    version: int
    count: int
    sources: dict = {}
    checksum: str = ""
    updated_at: str = ""
    summary: str = ""


# ===== 成长画像 / 榜单（Step ⑦） =====
class BadgeModel(BaseModel):
    name: str
    icon: str = "🏅"


class ProfileOut(BaseModel):
    user_id: int
    exp: int = 0
    level: int = 1
    level_name: str = ""
    cur_exp: int = 0
    next_exp: int | None = None
    progress: int = 0
    streak: int = 0
    total: int = 0
    correct: int = 0
    wrong: int = 0
    exams: int = 0
    accuracy: int = 0
    badges: list[BadgeModel] = []


class LeaderboardItem(BaseModel):
    user_id: int
    username: str
    exp: int
    level: int
    level_name: str
    accuracy: int


# ===== 自适应考场（Step ⑧） =====
class ExamStartIn(BaseModel):
    user_id: int | None = None
    cat: str = "考研"
    count: int = 20
    duration: int = 30


class ExamStartOut(BaseModel):
    question_ids: list[int] = []
    adaptive: bool = False
    difficulty_note: str = ""


class ExamSubmitIn(BaseModel):
    user_id: int | None = None
    exam_type: str = ""
    total: int = 0
    correct: int = 0
    duration: int = 0
    time_used: str = ""
    weak_topics: list[str] = []
    attempts: list[dict] = []   # [{question_id, correct, topic, cat}] 用于逐题诊断