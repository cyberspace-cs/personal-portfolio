"""竞赛信息聚合平台 · Pydantic 数据模型（请求/响应 Schema）"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


# ---------------- 分类 ----------------
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    icon: str = ""
    description: str = ""
    sort_order: int = 0
    count: int = 0  # 该分类下的竞赛数量


class CategoryIn(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)
    icon: str = Field(default="", max_length=10)
    description: str = Field(default="", max_length=500)
    sort_order: int = 0


# ---------------- 竞赛 ----------------
class CompetitionBase(BaseModel):
    title: str = Field(max_length=200)
    summary: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=8000)
    category_id: Optional[int] = None
    organizer: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=100)
    mode: Literal["online", "offline", "hybrid"] = "offline"
    prize: str = Field(default="", max_length=200)
    prize_amount: int = 0
    status: Literal["upcoming", "ongoing", "ended"] = "upcoming"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reg_deadline: Optional[str] = None
    tags: List[str] = Field(default_factory=list, max_length=10)
    cover: str = Field(default="", max_length=500)
    source_url: str = Field(default="", max_length=500)
    featured: bool = False

    @field_validator("tags")
    @classmethod
    def _trim_tags(cls, v: List[str]) -> List[str]:
        # 清理前后空白、单标签上限 30 字符、总数上限 10
        cleaned = [t.strip()[:30] for t in v if t and t.strip()]
        return cleaned[:10]


class CompetitionIn(CompetitionBase):
    slug: str = Field(max_length=200)


class CompetitionOut(CompetitionBase):
    id: int
    slug: str
    views: int = 0
    category_name: str = ""
    source: str = ""          # 聚合来源（如「天天黑客松」「Kaggle」），用于「聚合自 xx」标记
    created_at: str = ""
    updated_at: str = ""
    is_favorited: bool = False


class CompetitionList(BaseModel):
    items: List[CompetitionOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------- 用户 / 认证 ----------------
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str = Field(default="", max_length=200)
    password: str = Field(min_length=6, max_length=64)


class UserLogin(BaseModel):
    username: str = Field(max_length=32)
    password: str = Field(max_length=64)


class UserOut(BaseModel):
    id: int
    username: str
    email: str = ""
    avatar: str = ""
    role: str = "user"
    created_at: str = ""


class AuthOut(BaseModel):
    token: str
    user: UserOut


# ---------------- 收藏 ----------------
class FavoriteAction(BaseModel):
    competition_id: int
