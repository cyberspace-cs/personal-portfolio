"""Pydantic 数据模型（API 出入参）。"""
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    icon: str
    description: str
    sort_order: int
    count: int = 0


class CategoryInput(BaseModel):
    name: str
    slug: Optional[str] = None
    icon: str = "sparkles"
    description: str = ""
    sort_order: int = 0


class ItemOut(BaseModel):
    id: int
    title: str
    slug: str
    summary: str
    content: str
    category_id: Optional[int] = None
    category_name: str = ""
    category_slug: str = ""
    source_type: str = "repo"
    source_url: str = ""
    github_stars: Optional[int] = None
    author_org: str = ""
    language: str = ""
    status: str = "active"
    featured: bool = False
    views: int = 0
    tags: List[str] = []
    created_at: str = ""
    updated_at: str = ""
    is_favorited: bool = False


class ItemListResp(BaseModel):
    items: List[ItemOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ItemInput(BaseModel):
    title: str
    slug: Optional[str] = None
    summary: str = ""
    content: str = ""
    category_id: Optional[int] = None
    source_type: str = "repo"
    source_url: str = ""
    github_stars: Optional[int] = None
    author_org: str = ""
    language: str = ""
    status: str = "active"
    featured: bool = False
    tags: List[str] = []


class Stats(BaseModel):
    total: int
    categories: int
    trending: int
    featured: int
    by_type: dict = {}
    by_category: List[dict] = []
    top_viewed: List[dict] = []


class SessionOut(BaseModel):
    session_id: str


class FavoriteToggleResp(BaseModel):
    ok: bool
    favorited: bool
