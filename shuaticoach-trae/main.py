"""
专属刷题教练 - FastAPI Backend
TRAE AI 创造力大赛 · 学习工作赛道
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
import hashlib
import secrets
import time

app = FastAPI(title="专属刷题教练", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DATA_FILE = os.path.join(BASE_DIR, "data.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")

# ========== MODELS ==========
class StatsData(BaseModel):
    totalAnswered: int = 0
    correctCount: int = 0
    streak: int = 0
    lastDate: str = ""
    wrongBook: dict = {}
    answered: dict = {}

class SaveRequest(BaseModel):
    stats: StatsData
    answered: dict = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""

class AgentRequest(BaseModel):
    message: str
    model: str = "doubao"
    agent: str = "auto"
    temperature: float = 0.7

# ========== HELPERS ==========
def load_json(path: str, default: dict = None) -> dict:
    if default is None: default = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("token")
    if not token:
        return None
    users = load_json(USERS_FILE, {"users": {}, "tokens": {}})
    username = users.get("tokens", {}).get(token)
    if username and username in users.get("users", {}):
        return users["users"][username]
    return None

# ========== DEFAULT QUESTIONS ==========
DEFAULT_QUESTIONS = [
    {"id":1,"source":"LeetCode","type":"单选","question":"两数之和问题中，使用哈希表可以将时间复杂度优化到多少？","options":["O(n)","O(n²)","O(log n)","O(n log n)"],"answer":0,"explanation":"使用哈希表存储已遍历元素，一次遍历即可找到目标对，时间复杂度 O(n)。","knowledge":"哈希表","difficulty":"简单"},
    {"id":2,"source":"LeetCode","type":"单选","question":"在链表反转问题中，需要几个指针来完成原地反转？","options":["1个","2个","3个","4个"],"answer":2,"explanation":"需要三个指针：prev、curr、next，分别指向前驱、当前和下一个节点。","knowledge":"链表","difficulty":"简单"},
    {"id":3,"source":"牛客网","type":"单选","question":"以下哪种排序算法是稳定的？","options":["快速排序","堆排序","归并排序","选择排序"],"answer":2,"explanation":"归并排序在合并过程中保持相等元素的相对顺序，是稳定排序。","knowledge":"排序","difficulty":"中等"},
    {"id":4,"source":"牛客网","type":"判断","question":"二叉搜索树的中序遍历结果是有序的。","options":["正确","错误"],"answer":0,"explanation":"二叉搜索树的性质决定了左子树 < 根 < 右子树，中序遍历得到递增序列。","knowledge":"树","difficulty":"简单"},
    {"id":5,"source":"AcWing","type":"单选","question":"动态规划的两个核心要素是什么？","options":["递归和回溯","贪心和分治","最优子结构和重叠子问题","枚举和剪枝"],"answer":2,"explanation":"动态规划的核心是最优子结构和重叠子问题。","knowledge":"动态规划","difficulty":"中等"},
    {"id":6,"source":"AcWing","type":"多选","question":"以下哪些属于算法设计中的常用技巧？","options":["双指针","滑动窗口","前缀和","迪杰斯特拉"],"answer":0,"explanation":"双指针、滑动窗口、前缀和都是常用算法技巧。","knowledge":"算法技巧","difficulty":"简单"},
    {"id":7,"source":"洛谷","type":"单选","question":"vector 的 push_back 操作均摊时间复杂度是多少？","options":["O(1)","O(n)","O(log n)","O(n²)"],"answer":0,"explanation":"vector 的 push_back 均摊时间复杂度为 O(1)。","knowledge":"数据结构","difficulty":"简单"},
    {"id":8,"source":"洛谷","type":"判断","question":"DFS 总是能找到无权图中的最短路径。","options":["正确","错误"],"answer":1,"explanation":"DFS 不保证找到最短路径，最短路径问题应该使用 BFS。","knowledge":"图论","difficulty":"中等"},
    {"id":9,"source":"Codeforces","type":"单选","question":"KMP 字符串匹配算法的时间复杂度是多少？","options":["O(n)","O(n*m)","O(n²)","O(log n)"],"answer":0,"explanation":"KMP 算法通过预处理 next 数组，实现 O(n) 线性时间匹配。","knowledge":"字符串","difficulty":"中等"},
    {"id":10,"source":"Codeforces","type":"多选","question":"以下哪些数据结构可以用来实现优先队列？","options":["二叉堆","斐波那契堆","平衡树","普通队列"],"answer":0,"explanation":"二叉堆和斐波那契堆都可以实现优先队列。","knowledge":"数据结构","difficulty":"中等"},
    {"id":11,"source":"考研","type":"单选","question":"Cache 的映射方式不包括以下哪种？","options":["直接映射","全相联映射","组相联映射","链式映射"],"answer":3,"explanation":"Cache 的三种映射方式为：直接映射、全相联映射、组相联映射。","knowledge":"计算机组成","difficulty":"简单"},
    {"id":12,"source":"考研","type":"判断","question":"死锁的四个必要条件是：互斥、持有并等待、不可抢占、循环等待。","options":["正确","错误"],"answer":0,"explanation":"正确。死锁的四个必要条件：互斥、请求与保持、不可剥夺、循环等待。","knowledge":"操作系统","difficulty":"简单"},
    {"id":13,"source":"考研","type":"单选","question":"TCP 三次握手中，第二次握手包含的标志位是？","options":["SYN","ACK","SYN+ACK","FIN"],"answer":2,"explanation":"第二次握手服务器回复 SYN+ACK 标志位。","knowledge":"计算机网络","difficulty":"中等"},
    {"id":14,"source":"考公","type":"单选","question":"行测数量关系：某商品原价200元，先涨价20%再打八折，最终价格？","options":["192元","200元","208元","180元"],"answer":0,"explanation":"200 × 1.2 × 0.8 = 192 元。","knowledge":"数量关系","difficulty":"简单"},
    {"id":15,"source":"考公","type":"判断","question":"申论考试中，大作文的字数要求一般为800-1000字。","options":["正确","错误"],"answer":0,"explanation":"正确。国考申论大作文通常要求800-1000字。","knowledge":"申论","difficulty":"简单"},
    {"id":16,"source":"考公","type":"单选","question":"常识判断：我国现行宪法是哪一年通过的？","options":["1954年","1975年","1978年","1982年"],"answer":3,"explanation":"我国现行宪法是1982年12月4日通过的。","knowledge":"常识判断","difficulty":"简单"},
    {"id":17,"source":"大厂","type":"单选","question":"在 React 中，以下哪个 Hook 用于处理副作用？","options":["useState","useEffect","useContext","useReducer"],"answer":1,"explanation":"useEffect 用于处理副作用（数据获取、订阅、DOM操作等）。","knowledge":"React","difficulty":"简单"},
    {"id":18,"source":"大厂","type":"多选","question":"以下哪些是 HTTP 的常见状态码？","options":["200 OK","301 永久重定向","404 未找到","502 网关错误"],"answer":0,"explanation":"以上四个都是常见的 HTTP 状态码。","knowledge":"网络","difficulty":"简单"},
    {"id":19,"source":"大厂","type":"单选","question":"MySQL 中 InnoDB 存储引擎的默认隔离级别是？","options":["READ UNCOMMITTED","READ COMMITTED","REPEATABLE READ","SERIALIZABLE"],"answer":2,"explanation":"InnoDB 默认隔离级别是 REPEATABLE READ。","knowledge":"数据库","difficulty":"中等"},
    {"id":20,"source":"LeetCode","type":"单选","question":"二分查找算法的时间复杂度是？","options":["O(1)","O(n)","O(log n)","O(n log n)"],"answer":2,"explanation":"二分查找每次将搜索范围减半，时间复杂度为 O(log n)。","knowledge":"算法","difficulty":"简单"},
    {"id":21,"source":"牛客网","type":"填空","question":"在 Java 中，用于实现多线程的接口名称是 ____。","options":["Runnable"],"answer":0,"explanation":"Java 中实现多线程可以通过实现 Runnable 接口。","knowledge":"Java","difficulty":"简单"}
]

# Initialize questions file
if not os.path.exists(QUESTIONS_FILE):
    save_json(QUESTIONS_FILE, {"questions": DEFAULT_QUESTIONS})

# ========== ROUTES ==========
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Auth ---
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    users = load_json(USERS_FILE, {"users": {}, "tokens": {}})
    if req.username in users["users"]:
        raise HTTPException(400, "用户名已存在")
    users["users"][req.username] = {
        "username": req.username,
        "password": hash_password(req.password),
        "email": req.email,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stats": {"totalAnswered": 0, "correctCount": 0, "streak": 0, "lastDate": "", "wrongBook": {}, "answered": {}}
    }
    token = generate_token()
    users["tokens"][token] = req.username
    save_json(USERS_FILE, users)
    resp = JSONResponse({"status": "ok", "username": req.username})
    resp.set_cookie("token", token, max_age=3600*24*30, httponly=True)
    return resp

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    users = load_json(USERS_FILE, {"users": {}, "tokens": {}})
    user = users["users"].get(req.username)
    if not user or user["password"] != hash_password(req.password):
        raise HTTPException(401, "用户名或密码错误")
    token = generate_token()
    users["tokens"][token] = req.username
    save_json(USERS_FILE, users)
    resp = JSONResponse({"status": "ok", "username": req.username})
    resp.set_cookie("token", token, max_age=3600*24*30, httponly=True)
    return resp

@app.post("/api/auth/logout")
async def logout():
    resp = JSONResponse({"status": "ok"})
    resp.delete_cookie("token")
    return resp

@app.get("/api/auth/me")
async def me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "未登录")
    return {"username": user["username"], "email": user.get("email", ""), "stats": user.get("stats", {})}

# --- Data ---
@app.get("/api/data")
async def get_data(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"stats": {}, "answered": {}})
    return JSONResponse({"stats": user.get("stats", {}), "answered": user.get("stats", {}).get("answered", {})})

@app.post("/api/data")
async def post_data(req: SaveRequest, request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"status": "ok", "note": "not logged in"})
    users = load_json(USERS_FILE, {"users": {}, "tokens": {}})
    if user["username"] in users["users"]:
        users["users"][user["username"]]["stats"] = req.stats.model_dump()
        users["users"][user["username"]]["stats"]["answered"] = req.answered
        save_json(USERS_FILE, users)
    return JSONResponse({"status": "ok"})

# --- Questions ---
@app.get("/api/questions")
async def get_questions():
    data = load_json(QUESTIONS_FILE, {"questions": DEFAULT_QUESTIONS})
    questions = data["questions"]
    for q in questions:
        if "answer" in q:
            del q["answer"]
    return JSONResponse(questions)

@app.get("/api/questions/all")
async def get_all_questions():
    return JSONResponse(load_json(QUESTIONS_FILE, {"questions": DEFAULT_QUESTIONS}))

# --- Agent ---
@app.post("/api/agent/chat")
async def agent_chat(req: AgentRequest):
    responses = {
        "coach": [
            "让我来帮你分析这道题。首先，我们需要理解题目的核心考点...",
            "这道题的关键在于理解数据结构的特性。让我为你梳理一下思路...",
            "根据你的学习记录，这个知识点你掌握得还不够扎实。建议先回顾一下基础概念..."
        ],
        "explainer": [
            "这道题的解法可以分为以下几步：\n1. 理解题意，明确输入和输出\n2. 分析可能的解法，比较时间和空间复杂度\n3. 选择最优解法\n4. 注意边界条件",
            "从算法角度来看，这道题考察的是经典的数据结构应用。我们可以用图示来理解..."
        ],
        "planner": [
            "根据你当前的掌握度，我建议你按以下顺序学习：\n1. 先巩固基础数据结构\n2. 再攻克动态规划\n3. 最后练习综合题",
            "本周学习计划：\n- 周一至周三：复习错题本中的高频错误\n- 周四至周五：专项练习薄弱知识点\n- 周末：模拟考试检验成果"
        ],
        "auto": [
            "我理解你的问题。作为你的AI刷题教练，我建议从以下几个方面入手...",
            "这是一个很好的问题！让我结合你的学习数据来给出针对性建议...",
            "根据你的错题记录，这个知识点是你的薄弱环节。我建议你重点关注..."
        ]
    }
    agent = req.agent if req.agent in responses else "auto"
    pool = responses[agent]
    return JSONResponse({
        "reply": pool[hash(req.message) % len(pool)],
        "model": req.model,
        "agent": agent,
        "timestamp": time.strftime("%H:%M:%S")
    })

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)