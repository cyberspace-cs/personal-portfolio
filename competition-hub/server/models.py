"""竞赛信息聚合平台 · Pydantic 数据模型（请求/响应 Schema）"""
from typing import Optional, List
from pydantic import BaseModel, Field


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
    name: str
    slug: str
    icon: str = ""
    description: str = ""
    sort_order: int = 0


# ---------------- 竞赛 ----------------
class CompetitionBase(BaseModel):
    title: str
    summary: str = ""
    description: str = ""
    category_id: Optional[int] = None
    organizer: str = ""
    location: str = ""
    mode: str = "offline"            # online / offline / hybrid
    prize: str = ""
    prize_amount: int = 0
    status: str = "upcoming"         # upcoming / ongoing / ended
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reg_deadline: Optional[str] = None
    tags: List[str] = []
    cover: str = ""
    source_url: str = ""
    featured: bool = False


class CompetitionIn(CompetitionBase):
    slug: str


class CompetitionOut(CompetitionBase):
    id: int
    slug: str
    views: int = 0
    category_name: str = ""
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
    email: str = ""
    password: str = Field(min_length=6, max_length=64)


class UserLogin(BaseModel):
    username: str
    password: str


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
