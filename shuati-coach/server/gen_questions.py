"""生成题库 JSON：server/data/questions.json
把原 main.py 中的硬编码种子题外置为数据文件，并扩充题量/来源/题型。
支持「增量模式」：保留既有题顺序与 id 稳定性，仅追加新题；输出版本/来源/校验和。
运行：python gen_questions.py  （也可被 server/update_bank.py 导入调用）
"""
import json
import os
import hashlib
from datetime import date

# ───────────────────────── 原 60 道种子题（从 main.py 抽取，opt/answer 改为数组） ─────────────────────────
ORIGINAL = [
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设随机变量 X 服从参数为 λ 的泊松分布，则 E(X) 与 D(X) 的关系为？", "opts": ["E(X) > D(X)", "E(X) = D(X)", "E(X) < D(X)", "无法确定"], "answer": [1], "explain": "泊松分布的期望与方差均等于参数 λ，因此 E(X)=D(X)=λ。", "topic": "概率统计", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列关于矩阵可逆的说法中，正确的有？（多选）", "opts": ["行列式不为零", "秩等于阶数", "存在零特征值", "各行向量线性无关"], "answer": [0, 1, 3], "explain": "矩阵可逆 ⇔ 行列式非零 ⇔ 满秩 ⇔ 行向量线性无关。存在零特征值意味着行列式为零。", "topic": "线性代数", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "马克思主义哲学认为，世界的统一性在于它的？", "opts": ["运动性", "物质性", "矛盾性", "发展性"], "answer": [1], "explain": "辩证唯物主义认为世界统一于物质，物质是世界的本原。", "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "The word \"ubiquitous\" is closest in meaning to？", "opts": ["rare", "everywhere", "hidden", "dangerous"], "answer": [1], "explain": "ubiquitous 意为\"无处不在的\"，与 everywhere 意思最接近。", "topic": "英语词汇", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设 f(x) 在 [a,b] 上连续，在 (a,b) 内可导，且 f(a)=f(b)，则至少存在一点 ξ∈(a,b) 使得？", "opts": ["f(ξ)=0", "f'(ξ)=0", "f''(ξ)=0", "f(ξ)=f'(ξ)"], "answer": [1], "explain": "罗尔定理：若 f(a)=f(b)，则存在 ξ∈(a,b) 使 f'(ξ)=0。", "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "计算机组成原理中，冯·诺依曼体系结构的核心思想是？", "opts": ["程序存储与程序控制", "并行处理", "分布式计算", "面向对象"], "answer": [0], "explain": "冯·诺依曼结构核心是\"存储程序\"，将指令和数据预先存入存储器中自动执行。", "topic": "计算机组成", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列属于英国宪章运动时期工人阶级诉求的有？（多选）", "opts": ["普选权", "秘密投票", "八小时工作制", "废除议会"], "answer": [0, 1], "explain": "宪章运动六项要求包括普选权、秘密投票等，但八小时工作制和废除议会不在其中。", "topic": "政治·近代史", "difficulty": "hard"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "数据结构中，栈的典型特征是？", "opts": ["FIFO", "LIFO", "随机存取", "顺序存取"], "answer": [1], "explain": "栈是后进先出(LIFO)结构，队列是先进先出(FIFO)。", "topic": "数据结构", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "定积分 ∫₀^π sin x dx 的值为？", "opts": ["0", "1", "2", "π"], "answer": [2], "explain": "∫₀^π sin x dx = [-cos x]₀^π = -cosπ - (-cos0) = 1 + 1 = 2。", "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "英语中 \"It is high time that we ____ measures.\" 应填？", "opts": ["take", "took", "will take", "have taken"], "answer": [1], "explain": "It is high time (that)... 后用虚拟语气，谓语动词用一般过去时（took）。", "topic": "英语语法", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "判断题", "stem": "矛盾的基本属性是同一性和斗争性，二者缺一不可。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。矛盾的同一性与斗争性是相反相成、不可分割的两种基本属性。", "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "进程与线程的区别，下列说法正确的有？（多选）", "opts": ["进程是资源分配的基本单位", "线程是CPU调度的基本单位", "同一进程内的线程共享地址空间", "线程之间不能并发执行"], "answer": [0, 1, 2], "explain": "进程是资源分配单位，线程是调度单位，同进程线程共享内存；线程同样可以并发。", "topic": "操作系统", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "某工程队 8 天完成一项工程的 2/5，照此速度，完成剩余工程还需多少天？", "opts": ["10 天", "12 天", "14 天", "16 天"], "answer": [1], "explain": "8 天完成 2/5，即每天 1/20。剩余 3/5，需 (3/5)÷(1/20)=12 天。", "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "行政诉讼中，被告对作出的行政行为负有举证责任。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。《行政诉讼法》规定被告对其作出的行政行为承担举证责任。", "topic": "公共基础·法律", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "甲、乙、丙、丁四人参加比赛，赛前：甲说\"乙能得第一\"；乙说\"丙能得第一\"；丙说\"我不能得第一\"；丁说\"甲能得第一\"。已知只有一人说对了，请问谁得了第一？", "opts": ["甲", "乙", "丙", "丁"], "answer": [2], "explain": "逐一假设验证：若丙得第一，则乙说对、丙说错、甲说错、丁说错，只有一人说对，满足条件。", "topic": "行测·逻辑判断", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "2020年某市GDP为5000亿元，2023年为6655亿元，年均增长率约为？", "opts": ["8%", "10%", "12%", "15%"], "answer": [1], "explain": "5000×(1+r)³=6655, (1+r)³=1.331, r≈10%。", "topic": "行测·资料分析", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "下列成语与历史人物对应正确的是？", "opts": ["卧薪尝胆—勾践", "纸上谈兵—赵括", "破釜沉舟—项羽", "以上都对"], "answer": [3], "explain": "三个成语分别对应勾践、赵括、项羽，全部正确。", "topic": "行测·常识判断", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "申论写作中，\"总—分—总\"结构的核心是？", "opts": ["先提观点再论证最后总结", "先讲故事再分析", "直接罗列论据", "只写结论"], "answer": [0], "explain": "申论\"总—分—总\"结构要求开篇提出观点、中间分论点论证、结尾总结升华。", "topic": "申论", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "我国宪法规定，中华人民共和国的一切权力属于？", "opts": ["全国人民代表大会", "国务院", "人民", "中国共产党"], "answer": [2], "explain": "《宪法》第二条规定：中华人民共和国的一切权力属于人民。", "topic": "公共基础·宪法", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "图形推理：题干图形依次为○、△、□、○、△，下一个应是？", "opts": ["○", "△", "□", "☆"], "answer": [2], "explain": "周期为 3 的循环：○、△、□ 重复，第 6 个应为 □。", "topic": "行测·图形推理", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "多选题", "stem": "下列属于我国国家机构的有？（多选）", "opts": ["全国人民代表大会", "国务院", "中央军事委员会", "中国人民政治协商会议"], "answer": [0, 1, 2], "explain": "人大、国务院、中央军委均属国家机构；政协是爱国统一战线组织，非国家机构。", "topic": "公共基础·宪法", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "若 a:b = 3:4，b:c = 2:5，则 a:c 等于？", "opts": ["3:5", "3:10", "6:5", "4:5"], "answer": [1], "explain": "由 b:c=2:5 得 b:c=4:10，故 a:b:c=3:4:10，a:c=3:10。", "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "公务员录用考试笔试一般包括行政职业能力测验和申论两科。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。中央及地方公务员笔试通常含行测与申论。", "topic": "公共基础·常识", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "类比推理：医生∶病人 相当于？", "opts": ["教师∶学生", "司机∶汽车", "作家∶书店", "警察∶小偷"], "answer": [0], "explain": "医生服务病人，教师服务学生，均为职业与服务对象关系，最贴切。", "topic": "行测·类比推理", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "对一个已排序数组进行查找，采用二分查找的时间复杂度为？", "opts": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "answer": [1], "explain": "二分查找每次将搜索范围折半，时间复杂度为 O(log n)。", "topic": "算法", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "下列属于进程间通信(IPC)方式的有？（多选）", "opts": ["管道 Pipe", "共享内存", "消息队列", "局部变量"], "answer": [0, 1, 2], "explain": "管道、共享内存、消息队列、信号量、Socket 均为 IPC 方式。局部变量不能跨进程。", "topic": "操作系统", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "TCP 协议中，三次握手过程的第三个报文段包含的标志位是？", "opts": ["SYN", "SYN+ACK", "ACK", "FIN"], "answer": [2], "explain": "三次握手：客户端SYN→服务器SYN+ACK→客户端ACK（第三个报文只有ACK标志）。", "topic": "计算机网络", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "Java 中，HashMap 的底层数据结构在 JDK 1.8 之后是？", "opts": ["数组+链表", "数组+链表+红黑树", "纯数组", "纯链表"], "answer": [1], "explain": "JDK 1.8 后 HashMap 采用数组+链表+红黑树，当链表长度超过 8 时转为红黑树。", "topic": "Java基础", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "设计一个短链接系统，最核心的考量是？", "opts": ["前端美观度", "哈希冲突与唯一性", "数据库选型", "部署环境"], "answer": [1], "explain": "短链接系统最核心的是生成唯一短码，需解决哈希冲突、唯一性保证和分布式ID生成问题。", "topic": "系统设计", "difficulty": "hard"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "CSS 中，实现水平垂直居中的 flexbox 写法是？", "opts": ["display:flex; justify-content:center", "display:flex; align-items:center", "display:flex; justify-content:center; align-items:center", "display:flex; text-align:center"], "answer": [2], "explain": "justify-content:center 实现主轴居中，align-items:center 实现交叉轴居中，两者组合实现水平垂直居中。", "topic": "前端基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "快速排序平均时间复杂度是？", "opts": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "answer": [1], "explain": "快排平均时间复杂度为 O(n log n)，最坏 O(n²)。", "topic": "算法", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "关于 HTTP 与 HTTPS，下列说法正确的有？（多选）", "opts": ["HTTPS 默认端口 443", "HTTPS 基于 TLS/SSL 加密", "HTTP 是明文传输", "HTTPS 比 HTTP 慢所以不安全"], "answer": [0, 1, 2], "explain": "HTTPS 默认 443、基于 TLS 加密、HTTP 明文；HTTPS 虽稍慢但更安全。", "topic": "计算机网络", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "二叉树的前序遍历顺序是？", "opts": ["根-左-右", "左-根-右", "左-右-根", "根-右-左"], "answer": [0], "explain": "前序遍历：先访问根节点，再左子树，后右子树（根-左-右）。", "topic": "数据结构", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "数据库事务的 ACID 特性中，I 指的是？", "opts": ["原子性", "一致性", "隔离性", "持久性"], "answer": [2], "explain": "ACID：Atomicity 原子性、Consistency 一致性、Isolation 隔离性、Durability 持久性。", "topic": "数据库", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "判断题", "stem": "Python 中列表(list)是可变对象，而元组(tuple)是不可变对象。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。list 可变、tuple 不可变，这是二者核心区别。", "topic": "Python基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "在分布式系统中，CAP 理论指出不可能同时满足？", "opts": ["一致性与可用性", "一致性与分区容错性", "可用性与分区容错性", "三者可同时满足"], "answer": [1], "explain": "CAP 指出在网络分区(P)发生时，一致性(C)与可用性(A)不可兼得。", "topic": "系统设计", "difficulty": "hard"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "英语中 \"ambiguous\" 的含义最接近？", "opts": ["明确的", "模棱两可的", "遥远的", "熟悉的"], "answer": [1], "explain": "ambiguous 意为\"含糊不清的、模棱两可的\"。", "topic": "英语词汇", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "设函数 f(x)=x³-3x，则 f(x) 的极小值点为？", "opts": ["x=-1", "x=0", "x=1", "x=2"], "answer": [2], "explain": "f'(x)=3x²-3，令为0得x=±1；f''(1)=6>0为极小值点，极小值在x=1。", "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "多选题", "stem": "下列不等式中，对任意实数 x 恒成立的有？（多选）", "opts": ["x²≥0", "x²+1>0", "|x|≥x", "x+1>x"], "answer": [0, 1, 2, 3], "explain": "平方非负、平方加1恒正、绝对值不小于自身、x+1恒大于x，均恒成立。", "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "操作系统页式存储管理中，页表的作用是？", "opts": ["映射逻辑页到物理块", "管理文件", "调度进程", "分配内存给内核"], "answer": [0], "explain": "页表建立逻辑地址中页号到物理内存块号的映射关系，实现地址转换。", "topic": "操作系统", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "TCP 与 UDP 的区别，下列正确的是？", "opts": ["TCP 面向连接，UDP 无连接", "UDP 可靠，TCP 不可靠", "TCP 速度快于 UDP", "二者均为广播协议"], "answer": [0], "explain": "TCP 面向连接、可靠；UDP 无连接、尽力交付。UDP 通常更快但不保证可靠。", "topic": "计算机网络", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "判断题", "stem": "二叉树的中序遍历结果可以唯一确定一棵二叉树的结构。", "opts": ["正确", "错误"], "answer": [1], "explain": "错误。仅中序遍历无法确定结构，需配合前序或后序遍历才能唯一确定。", "topic": "数据结构", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "马克思主义哲学中，实践是认识的来源，这表明？", "opts": ["认识先于实践", "认识来源于实践", "实践等于认识", "认识可以脱离实践"], "answer": [1], "explain": "马克思主义认识论强调实践是第一性的，认识来源于实践并反作用于实践。", "topic": "政治·马哲", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "数据库事务的隔离级别中，可避免脏读的最低级别是？", "opts": ["读未提交", "读已提交", "可重复读", "串行化"], "answer": [1], "explain": "读已提交(Read Committed)可防止脏读，是避免脏读的最低隔离级别。", "topic": "数据库", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "某商品原价 100 元，先提价 20% 再打八折出售，现价为？", "opts": ["96 元", "100 元", "104 元", "120 元"], "answer": [0], "explain": "100×1.2=120，再×0.8=96 元。提价与打折比例不同，现价低于原价。", "topic": "行测·数量关系", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "我国现行宪法历经几次全面修改？自 1982 年宪法以来修正案共几件？", "opts": ["3 次修改，52 件修正案", "未全面修改，52 件修正案", "5 次修改，无修正案", "1 次修改，18 件修正案"], "answer": [1], "explain": "1982 年宪法沿用至今未全面修改，通过 52 件宪法修正案（1988/1993/1999/2004/2018 五次修宪共52条）。", "topic": "公共基础·宪法", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "多选题", "stem": "下列关于公文格式的说法，正确的有？（多选）", "opts": ["公文标题一般由发文机关+事由+文种组成", "主送机关顶格书写", "成文日期用阿拉伯数字", "密级和保密期限可不标注"], "answer": [0, 1, 2], "explain": "公文标题三要素、主送顶格、成文日期用阿拉伯数字均正确；密级依需标注，非必须。", "topic": "公共基础·公文", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "俗语\"一着不慎，满盘皆输\"体现的哲理是？", "opts": ["整体统帅部分", "关键部分对整体起决定作用", "部分无关紧要", "整体等于部分之和"], "answer": [1], "explain": "关键局部（一着）影响整体（满盘），体现关键部分对整体的决定作用。", "topic": "政治·马哲", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "资料分析：某省 2022 年粮食产量 6000 万吨，同比增长 2%，则增量约为？", "opts": ["约 118 万吨", "约 120 万吨", "约 130 万吨", "约 150 万吨"], "answer": [0], "explain": "增量=6000-6000/1.02≈6000×0.0196≈117.6 万吨，约 118 万吨。", "topic": "行测·资料分析", "difficulty": "medium"},
    {"cat": "考公", "src": "中公题库", "type": "判断题", "stem": "行政复议是行政诉讼的必经前置程序。", "opts": ["正确", "错误"], "answer": [1], "explain": "错误。多数情形可复议也可直接诉讼，仅法律特别规定事项才需复议前置。", "topic": "公共基础·法律", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "类比推理：天平∶重量 相当于？", "opts": ["温度计∶温度", "尺子∶长度", "钟表∶时间", "以上都正确"], "answer": [3], "explain": "天平测重量、温度计测温度、尺子测长度、钟表测时间，均为测量工具与对象关系。", "topic": "行测·类比推理", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "《行政处罚法》规定，违法行为在几年内未被发现不再给予处罚？", "opts": ["1 年", "2 年", "5 年", "10 年"], "answer": [1], "explain": "一般违法行为 2 年内未被发现不再处罚；涉及公民生命健康安全等有特别规定。", "topic": "公共基础·法律", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "Python 中 list 和 tuple 的主要区别是？", "opts": ["list 可变，tuple 不可变", "tuple 可变，list 不可变", "二者都不可变", "二者都可变"], "answer": [0], "explain": "list 可变（可增删改），tuple 不可变（创建后不能修改），这是核心区别。", "topic": "Python基础", "difficulty": "easy"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "一个栈的入栈序列为 1,2,3,4，合法的出栈序列是？", "opts": ["4,3,2,1", "3,4,1,2", "1,3,2,4", "以上都合法"], "answer": [3], "explain": "栈允许任意时机的入/出交错；4,3,2,1（全入后出）、3,4,1,2、1,3,2,4 均可能。", "topic": "数据结构", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "关于索引，下列说法正确的有？（多选）", "opts": ["索引可加速查询", "索引会降低写入速度", "主键自动建立唯一索引", "索引越多越好"], "answer": [0, 1, 2], "explain": "索引加速读但拖慢写，主键默认唯一索引；索引过多反而影响性能，并非越多越好。", "topic": "数据库", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "动态规划的核心思想通常包含？", "opts": ["分治+记忆化", "暴力枚举", "随机搜索", "贪心即可"], "answer": [0], "explain": "DP 通过最优子结构、重叠子问题与记忆化（缓存子问题结果）避免重复计算。", "topic": "算法", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "HTTP 状态码 404 表示？", "opts": ["服务器错误", "请求成功", "资源未找到", "需要重定向"], "answer": [2], "explain": "404 Not Found 表示服务器无法找到请求的资源。", "topic": "计算机网络", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "判断题", "stem": "React 中 useState 返回的 setter 函数是异步批量更新的。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。React 18 起默认自动批处理，同一事件中的多次 setState 会合并批量更新。", "topic": "前端基础", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "哈希表平均查找时间复杂度约为？", "opts": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "answer": [0], "explain": "在理想哈希函数下，哈希表插入、删除、查找的平均时间复杂度均为 O(1)。", "topic": "数据结构", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "微服务架构中，服务间常用的注册与发现组件是？", "opts": ["Nginx", "Redis", "Consul / Nacos", "Kafka"], "answer": [2], "explain": "Consul、Nacos、Eureka 等是典型服务注册与发现组件；Nginx 是网关/负载均衡。", "topic": "系统设计", "difficulty": "medium"},
]

# ───────────────────────── 扩充新题（更多来源 / 题型 / 知识点） ─────────────────────────
EXTRA = [
    # 考研 · 政治/英语/数学 新增
    {"cat": "考研", "src": "肖秀荣1000题", "type": "单选题", "stem": "商品二因素是指？", "opts": ["使用价值与价值", "具体劳动与抽象劳动", "私人劳动与社会劳动", "简单劳动与复杂劳动"], "answer": [0], "explain": "商品二因素：使用价值（自然属性）与价值（社会属性）。", "topic": "政治·政经", "difficulty": "easy"},
    {"cat": "考研", "src": "考研真题", "type": "单选题", "stem": "极限 lim(x→0) (sin x)/x 的值为？", "opts": ["0", "1", "∞", "不存在"], "answer": [1], "explain": "重要极限：lim(x→0) sinx/x = 1。", "topic": "高等数学", "difficulty": "easy"},
    {"cat": "考研", "src": "考研英语", "type": "单选题", "stem": "“The project was completed ____ schedule.” 应填？", "opts": ["ahead of", "behind of", "after of", "before of"], "answer": [0], "explain": "ahead of schedule 意为\"提前\"，是固定搭配。", "topic": "英语语法", "difficulty": "easy"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "线性代数中，n 阶矩阵 A 可逆的充要条件是什么？", "opts": ["|A|≠0", "A 对称", "A 的对角元全为正", "A 的秩小于 n"], "answer": [0], "explain": "矩阵可逆 ⇔ 行列式不为零 ⇔ 满秩(rank=n)。", "topic": "线性代数", "difficulty": "medium"},
    {"cat": "考研", "src": "肖秀荣1000题", "type": "多选题", "stem": "关于实践是检验真理的唯一标准，下列说法正确的有？（多选）", "opts": ["实践具有直接现实性", "逻辑证明可替代实践", "实践标准是确定性与不确定性的统一", "实践是主观见之于客观的活动"], "answer": [0, 2, 3], "explain": "实践是唯一标准因其直接现实性；它是确定与不确定统一；逻辑证明不能替代实践。", "topic": "政治·马哲", "difficulty": "medium"},
    {"cat": "考研", "src": "考研真题", "type": "单选题", "stem": "设函数 z=f(x,y) 可微，则全微分 dz = ？", "opts": ["fx dx + fy dy", "fx + fy", "fx dy + fy dx", "∂f/∂x + ∂f/∂y"], "answer": [0], "explain": "全微分 dz = ∂f/∂x dx + ∂f/∂y dy = fx dx + fy dy。", "topic": "高等数学", "difficulty": "medium"},
    {"cat": "考研", "src": "考研帮", "type": "单选题", "stem": "操作系统死锁的四个必要条件不包括？", "opts": ["互斥", "占有并等待", "不可抢占", "高优先级"], "answer": [3], "explain": "死锁四条件：互斥、占有等待、不可抢占、循环等待。高优先级不是必要条件。", "topic": "操作系统", "difficulty": "medium"},
    {"cat": "考研", "src": "考研英语", "type": "单选题", "stem": "“His argument is ____; nobody was convinced.” 应填？", "opts": ["compelling", "feeble", "robust", "lucid"], "answer": [1], "explain": "feeble 意为\"无力的、站不住脚的\"，与\"没人被说服\"呼应。", "topic": "英语词汇", "difficulty": "medium"},
    # 考公 新增
    {"cat": "考公", "src": "华图教育", "type": "单选题", "stem": "下列属于行政处罚的是？", "opts": ["拘役", "罚款", "管制", "有期徒刑"], "answer": [1], "explain": "罚款是行政处罚；拘役、管制、有期徒刑均为刑罚。", "topic": "公共基础·法律", "difficulty": "medium"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "数字推理：2, 6, 12, 20, 30, ( )", "opts": ["40", "42", "44", "46"], "answer": [1], "explain": "相邻差为 4,6,8,10，下一项差 12，故 30+12=42。", "topic": "行测·数量关系", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "多选题", "stem": "下列属于民法基本原则的有？（多选）", "opts": ["平等原则", "自愿原则", "公平原则", "罪刑法定原则"], "answer": [0, 1, 2], "explain": "平等、自愿、公平、诚信、公序良俗为民法原则；罪刑法定属刑法。", "topic": "公共基础·法律", "difficulty": "medium"},
    {"cat": "考公", "src": "华图教育", "type": "单选题", "stem": "行政强制措施的种类不包括？", "opts": ["限制公民人身自由", "查封场所", "扣押财物", "加处罚款"], "answer": [3], "explain": "加处罚款属于行政强制执行，而非行政强制措施。", "topic": "公共基础·法律", "difficulty": "hard"},
    {"cat": "考公", "src": "粉笔行测", "type": "单选题", "stem": "言语理解：填入横线最恰当的是——\"这部纪录片以____的笔触，重现了那段峥嵘岁月。\"", "opts": ["细腻", "粗略", "生硬", "敷衍"], "answer": [0], "explain": "\"细腻的笔触\"搭配恰当，符合纪录片精良重现的语境。", "topic": "行测·言语理解", "difficulty": "easy"},
    {"cat": "考公", "src": "中公题库", "type": "单选题", "stem": "我国国家元首是国家主席，国家主席由谁选举产生？", "opts": ["全国人民代表大会", "全国人大常委会", "全国政协", "中共中央"], "answer": [0], "explain": "国家主席、副主席由全国人民代表大会选举产生。", "topic": "公共基础·宪法", "difficulty": "easy"},
    {"cat": "考公", "src": "粉笔行测", "type": "判断题", "stem": "货币政策的三大法宝是法定准备金率、再贴现率、公开市场业务。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。一般性货币政策工具即这三大法宝。", "topic": "公共基础·经济", "difficulty": "medium"},
    {"cat": "考公", "src": "华图教育", "type": "单选题", "stem": "类比推理：蜜蜂∶蜂蜜 相当于？", "opts": ["羊∶羊毛", "鸡∶鸡蛋", "牛∶牛奶", "蚕∶蚕丝"], "answer": [1], "explain": "蜜蜂生产蜂蜜（生产者与产物，且产物名称含生产者字）；鸡生产鸡蛋最对应。", "topic": "行测·类比推理", "difficulty": "easy"},
    # 大厂 新增
    {"cat": "大厂", "src": "剑指Offer", "type": "单选题", "stem": "反转单链表的最优时间复杂度是？", "opts": ["O(1)", "O(n)", "O(n log n)", "O(n²)"], "answer": [1], "explain": "迭代反转需遍历一次，时间复杂度 O(n)，空间 O(1)。", "topic": "算法", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "Redis 最适合用于下列哪种场景？", "opts": ["持久化存储核心业务数据", "缓存热点数据", "复杂多表联查", "全文检索"], "answer": [1], "explain": "Redis 是内存数据库，适合做缓存、计数器、排行榜等高性能场景。", "topic": "数据库", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "多选题", "stem": "关于 MySQL 事务隔离级别，下列说法正确的有？（多选）", "opts": ["读已提交可防止脏读", "可重复读可防止不可重复读", "串行化完全隔离", "读未提交最安全"], "answer": [0, 1, 2], "explain": "读已提交防脏读、可重复读防不可重复读、串行化全隔离；读未提交最不安全。", "topic": "数据库", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "二叉搜索树(BST)的中序遍历结果是？", "opts": ["降序", "升序", "无序", "与层序相同"], "answer": [1], "explain": "BST 中序遍历（左-根-右）得到升序序列。", "topic": "数据结构", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "HTTP 方法是幂等的有？", "opts": ["POST", "GET", "PATCH", "CONNECT"], "answer": [1], "explain": "GET、PUT、DELETE 是幂等的；POST、PATCH 非幂等。", "topic": "计算机网络", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "以下哪个数据结构可以实现 O(1) 的入队和出队？", "opts": ["普通数组", "循环队列", "单向链表（仅头指针）", "栈"], "answer": [1], "explain": "用循环数组（或双端队列）可实现均摊 O(1) 的入队出队。", "topic": "数据结构", "difficulty": "medium"},
    {"cat": "大厂", "src": "牛客网", "type": "单选题", "stem": "Python 中 GIL（全局解释器锁）主要影响？", "opts": ["单线程性能", "多线程并行执行 CPU 密集型任务", "内存占用", "文件读写"], "answer": [1], "explain": "GIL 使 CPython 同一时刻仅一个线程执行字节码，限制多线程 CPU 并行。", "topic": "Python基础", "difficulty": "medium"},
    {"cat": "大厂", "src": "剑指Offer", "type": "单选题", "stem": "用两个栈实现一个队列，入队操作的时间复杂度是？", "opts": ["O(1)", "O(n)", "O(log n)", "O(n²)"], "answer": [0], "explain": "入队直接压入栈1，O(1)；出队需在栈2为空时倒灌，均摊 O(1)。", "topic": "数据结构", "difficulty": "medium"},
    {"cat": "大厂", "src": "LeetCode", "type": "单选题", "stem": "负载均衡算法中，能将请求按服务器权重分发的是？", "opts": ["轮询", "加权轮询", "随机", "IP 哈希"], "answer": [1], "explain": "加权轮询按预设权重比例分配流量，适合异构服务器。", "topic": "系统设计", "difficulty": "easy"},
    {"cat": "大厂", "src": "牛客网", "type": "判断题", "stem": "NoSQL 数据库通常为了保证可用性与分区容错性，会在一致性上做妥协（最终一致）。", "opts": ["正确", "错误"], "answer": [0], "explain": "正确。许多 NoSQL 在 CAP 中倾向 AP，采用最终一致性。", "topic": "数据库", "difficulty": "medium"},
]

ALL = ORIGINAL + EXTRA


def load_existing(data_dir):
    """读取现有 questions.json；缺失/异常时返回空列表 + 基线版本。"""
    path = os.path.join(data_dir, "questions.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("questions", []), data.get("version", 2)
        except Exception as e:
            print("[gen] 读取现有 questions.json 失败，将以基线重建:", e)
    return [], 2


def build_questions():
    """合并基线(ORIGINAL+EXTRA)与现有题库，保留既有题顺序与 id 稳定性，仅追加新题。"""
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "data")
    existing, existing_version = load_existing(data_dir)
    existing_stems = {q.get("stem") for q in existing}
    merged = list(existing)
    added = 0
    for q in ALL:
        if q.get("stem") not in existing_stems:
            merged.append(q)
            existing_stems.add(q.get("stem"))
            added += 1
    return merged, existing_version, added, data_dir


def validate(questions):
    """质量校验：答案下标越界 / 重复题干 / 空知识点。失败抛异常阻断入库。"""
    for i, q in enumerate(questions):
        assert all(0 <= a < len(q["opts"]) for a in q["answer"]), f"第{i}题 answer 越界: {q['stem']}"
        assert q.get("topic"), f"第{i}题 知识点(topic)为空: {q['stem']}"
    stems = [q["stem"] for q in questions]
    dup = len(stems) - len(set(stems))
    assert dup == 0, f"存在 {dup} 道重复题干，需去重"
    return True


def write_questions():
    """生成并写盘 questions.json，附带 version/sources/checksum 元信息。"""
    from collections import Counter
    merged, existing_version, added, data_dir = build_questions()
    validate(merged)  # 校验失败则抛出，阻断后续入库
    new_version = existing_version + (1 if added > 0 else 0)

    srcs = Counter(q["src"] for q in merged)
    raw = json.dumps(merged, ensure_ascii=False, sort_keys=True).encode("utf-8")
    checksum = hashlib.sha256(raw).hexdigest()[:16]

    out = {
        "version": new_version,
        "generated_at": date.today().isoformat(),
        "count": len(merged),
        "sources": dict(srcs),
        "checksum": checksum,
        "questions": merged,
    }
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "questions.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    cats = Counter(q["cat"] for q in merged)
    types = Counter(q["type"] for q in merged)
    diff = Counter(q["difficulty"] for q in merged)
    print("题库已生成:", path)
    print(f"总题数: {len(merged)} ｜ 本次新增: {added} ｜ 版本: {existing_version} → {new_version}")
    print("分类:", dict(cats))
    print("题型:", dict(types))
    print("来源数:", len(srcs), dict(srcs))
    print("难度:", dict(diff))
    print("checksum:", checksum)
    return out


if __name__ == "__main__":
    write_questions()
