# 真实题库摄入规范（治本路线：引入官方 / 权威题库）

本文件说明如何把**真实、可溯源**的题目录入刷题教练题库。所有真实题都经
`server/ingest_real.py` 校验、去重、打权威标签后入库。**绝不抓取受版权保护内容**，
仅处理你已授权拥有的资料或 license 清晰的开放数据集。

## 权威类型（src_type）

| 值 | 含义 | 示例 |
|---|---|---|
| `official` | 官方真题（历年考试原题，最高权威性） | 考研历年真题、考公行测/申论真题卷 |
| `institution` | 权威机构 / 教材题 | 肖秀荣1000题、粉笔、LeetCode、牛客、中公、华图 |
| `ai_sim` | AI 生成的模拟练习题（非官方，仅供练习） | 现有 23102 道 DeepSeek 生成题 |

## 放置目录

把你整理好的文件放进 `server/data/incoming/`（该目录本地使用、不入库），然后运行：

```bash
# 在 server/ 目录下执行；COACH_DB 默认指向 server/coach.db
python ingest_real.py data/incoming/你的文件.json
python ingest_real.py data/incoming/你的文件.csv   --src-type institution
python ingest_real.py data/incoming/你的文件.md    --cat 考公 --src-type official --license "用户授权·自有资料"
python ingest_real.py 文件.json --dry-run          # 只校验，不写库
```

> 去重按「题干」做 md5 指纹，重复题自动跳过，可反复运行。

## 格式一：JSON

```json
[
  {
    "cat": "考研",
    "src": "肖秀荣1000题",
    "type": "单选题",
    "stem": "题干……",
    "opts": ["A. …", "B. …", "C. …", "D. …"],
    "answer": [0],
    "explain": "解析……",
    "topic": "政治·马原",
    "difficulty": "medium",
    "src_type": "institution",
    "year": 2024,
    "license": "用户授权·自有资料"
  }
]
```

## 格式二：CSV（首行表头，含逗号的字段用双引号包裹）

| 列 | 说明 |
|---|---|
| cat | 分类：考研 / 考公 / 大厂 |
| src | 来源名（如 肖秀荣1000题） |
| type | 题型：单选题 / 多选题 / 判断题 |
| stem | 题干 |
| opts | 选项，支持 JSON 数组或 `A;B;C;D` 或 `A,B,C,D` 分隔 |
| answer | 答案下标，支持 `[0,1]` / `0,1` / `AB`(字母) |
| explain | 解析 |
| topic | 知识点 |
| difficulty | easy / medium / hard |
| src_type | official / institution / ai_sim |
| year | 真题年份（可选） |
| license | 来源许可说明（可选） |

## 格式三：Markdown

每题以空行分隔，用「题干 / 选项 / 答案 / 解析 / 来源 / 分类 / 知识点 / 难度」标记行：

```
题干：商品的价值量由（ ）决定。
选项：A. 个别劳动时间 B. 社会必要劳动时间 C. 市场供求 D. 国家调控
答案：B
解析：商品价值量由社会必要劳动时间决定。
来源：考研政治真题
分类：考研
知识点：政治·马原
难度：easy
```

## 校验规则

- 题干非空；选项 ≥ 2 个；答案下标必须落在选项范围内。
- 题型 / 难度取值受白名单约束（非法值回退默认值）。
- 解析可为空；来源 / 知识点 / 年份 / 许可均为可选。
