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


class QuizCheckIn(BaseModel):
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