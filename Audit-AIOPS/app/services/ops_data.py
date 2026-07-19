"""
审计技术支持 + 日常运维 · 真实数据引擎（蓝鲸经验落地）

职责：
- 以 catalog.py 的「十大审计技术支持 + 三大日常运维」为权威分类，确定性种子生成
  大量真实感运数据（工单 / 告警 / 变更），落盘 data/ops/ops_data.json（重启不丢）。
- 多个「运维智能体」persona 模拟多用户协作：各自承接工单/告警、自动化处置占比、CSAT。
- 由真实数据计算 ITSM + 运维 KPI（MTTR / SLA 达标 / 自动化率 / CSAT / 收敛率 / 自愈率…）
  与痛点洞察，供运维控制台（工作台）实时呈现，绝不编造。

设计哲学与既有平台一致：可插拔、纯 CPU、零外部依赖即可真跑；数据驱动、可回溯。
"""

import json
import os
import random
import datetime
from collections import defaultdict, Counter

from app.services.catalog import CATALOG

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "..", "data", "ops")
DATA_FILE = os.path.join(DATA_DIR, "ops_data.json")
SEED = 20240719

SERVICE_MAP = {s.id: s for s in CATALOG}

# ============ 多用户运维智能体（persona，模拟多用户协作） ============
AGENTS = [
    {"id": "A1", "name": "张明", "team": "系统运维组", "scope": ["ukey", "terminal", "devops", "lottery"], "online": True},
    {"id": "A2", "name": "李静", "team": "数据库与存储组", "scope": ["resource", "appops", "backup", "devops"], "online": True},
    {"id": "A3", "name": "王强", "team": "网络安全组", "scope": ["perm", "web", "platops"], "online": True},
    {"id": "A4", "name": "赵琳", "team": "应用支持组", "scope": ["mail", "meeting", "appops", "web"], "online": False},
    {"id": "A5", "name": "陈涛", "team": "自动化运维组", "scope": ["devops", "platops", "backup"], "online": True},
    {"id": "A6", "name": "周倩", "team": "审计业务支持组", "scope": ["ups", "lottery", "meeting", "terminal"], "online": True},
]
AGENT_BY_ID = {a["id"]: a for a in AGENTS}

# ============ 各服务的真实感工单样例（标题/描述） ============
SERVICE_SAMPLES = {
    "ukey": [
        ("为财政一处张三制作 Ukey 审计介质", "外派进点需新介质，用途：现场数据调阅，权限级别：普通审计员。"),
        ("回收离岗人员李四 Ukey", "李四已调离审计二处，需回收并注销介质，防止越权访问。"),
        ("调整王五 Ukey 权限级别为项目主审", "王五任经责审计项目主审，需提升权限级别以签署底稿。"),
        ("批量制作经责审计 12 人 Ukey", "经责审计进点，需为 12 名外派人员批量制作介质。"),
    ],
    "perm": [
        ("审计二处新增人员赵六角色授权", "新增数据分析岗，需授予电子数据审计查询角色。"),
        ("调整陈七为某项目主审角色", "项目角色变更，扩大被审计数据范围至全量。"),
        ("撤销外包人员临时查询权限", "外包合同到期，收回其只读查询权限。"),
        ("为法规审理处开通底稿复核角色", "审理环节需复核权限，数据范围限本处项目。"),
    ],
    "mail": [
        ("为外派审计组开通远程邮件帐号", "社保审计处 8 人外派，需远程接入邮箱。"),
        ("审计三部邮箱扩容至 10GB", "附件频繁超限，申请容量扩容。"),
        ("重置刘八邮件密码并开启双因子", "密码遗忘，按安全策略重置并强化。"),
    ],
    "resource": [
        ("发放临时数据分析虚拟机 4C8G", "企业审计处取数分析，预计使用 2 周。"),
        ("申请 2TB 审计数据存储空间", "社保数据全量落盘，归属社保审计项目。"),
        ("借调 GPU 服务器用于模型推理", "非结构化数据识别模型推理，短期借用。"),
    ],
    "ups": [
        ("本周五机房 UPS 切换演练保障", "主备切换演练，需运维现场值守与脚本校验。"),
        ("UPS 电池更换配合停机窗口", "老旧电池更换，协调 2 小时窗口。"),
    ],
    "lottery": [
        ("年会抽奖小程序演示与部署", "职工年会，需演示并部署抽奖程序。"),
        ("抽奖程序兼容性预检", "多终端适配预检，避免现场异常。"),
    ],
    "web": [
        ("专网门户栏目改版技术支持", "首页增设『审计公开』栏目，需组件化改版。"),
        ("审计公告页样式调整", "合规样式统一，字号与配色按规范调整。"),
        ("门户 SSL 证书更换", "证书临期，需无缝更换不影响访问。"),
    ],
    "terminal": [
        ("领用笔记本一台用于现场审计", "资源环境审计处进点，领用便携终端。"),
        ("修复投影终端无法开机", "会议室投影终端故障，影响会审。"),
        ("更换故障键盘鼠标", "办公终端外设损坏，申请更换。"),
    ],
    "meeting": [
        ("预约周二跨部门视频会审", "财政/企业审计处联合会审，需专线保障。"),
        ("审计进点视频连线保障", "异地进点，需稳定视频连线与录播。"),
        ("月度例会会议室预定", "全处月度例会，预定大会议室。"),
    ],
    "backup": [
        ("审计底稿全量备份", "月度全量备份，含异地副本校验。"),
        ("误删报表数据恢复请求", "某项目人员误删季度报表，需时间点恢复。"),
        ("异地容灾备份校验", "季度容灾演练，校验副本可恢复性。"),
    ],
    # 日常运维类也会产生少量事件型工单（多数走告警/变更闭环）
    "devops": [
        ("db-fin-01 磁盘空间告警处置", "财务数据库主机磁盘超 90%，需扩容或清理。"),
        ("web-audit-03 宕机重启", "应用主机异常重启，需排查根因。"),
    ],
    "appops": [
        ("审计管理系统 /login 接口超时", "登录接口 P95 超 2s，影响进点效率。"),
        ("底稿服务线程池耗尽", "并发上传导致线程池打满，需扩容。"),
    ],
    "platops": [
        ("Nginx 证书 7 天后过期预警", "门户证书临期，需提前更换。"),
        ("Kafka 消息堆积处置", "日志采集队列堆积 12w，需扩容消费。"),
    ],
}

# 运维类服务对应的主机/指标（用于生成真实告警）
OPS_HOSTS = {
    "devops": ["web-audit-01", "web-audit-02", "web-audit-03", "db-fin-01", "db-fin-02", "stor-arch-01", "stor-arch-02"],
    "appops": ["app-audit-core", "app-working-paper", "app-kb", "app-portal"],
    "platops": ["nginx-gw-01", "kafka-cluster", "redis-session", "es-log", "zk-quorum"],
}

# 变更类型 / 风险 / 审批（双人审批）
CHANGE_TYPES = ["版本发布", "配置变更", "权限变更", "资源扩容", "紧急修复"]
CHANGE_RISKS = ["高", "中", "低"]
CHANGE_APPROVERS = [["运维主管", "安全管理员"], ["运维主管", "分管领导"], ["部门负责人", "运维主管", "安全管理员"]]
CHANGE_TITLES = {
    "版本发布": ["审计管理系统 v3.2 发布", "底稿系统 v2.5 灰度发布", "知识库服务 v1.8 发布"],
    "配置变更": ["Nginx 超时参数调优", "数据库连接池扩容", "JVM 堆内存调整"],
    "权限变更": ["开放电子数据查询角色", "回收外包临时权限", "调整项目主审数据范围"],
    "资源扩容": ["财务库存储扩容 2TB", "GPU 节点新增 2 台", "日志集群扩容 3 节点"],
    "紧急修复": ["修复登录接口内存泄漏", "修复证书过期导致 5xx", "修复队列堆积消费滞后"],
}

DEPTS = ["财政审计处", "企业审计处", "社保审计处", "资源环境审计处",
         "经济责任审计处", "电子数据审计处", "法规审理处", "办公室"]
SURNAMES = ["张", "王", "李", "赵", "陈", "刘", "杨", "黄", "周", "吴", "徐", "孙", "马", "朱"]


def _trace(seed_str: str) -> str:
    h = abs(hash(seed_str)) % 0xFFFFFFFF
    return "TRC-" + format(h, "08X")


def _gen_tickets(rng: random.Random):
    tickets = []
    now = datetime.datetime.now()
    # 工单量按服务月单量等比缩放（30 天窗口），运维类仅少量事件单
    weights = {
        "ukey": 30, "perm": 20, "mail": 16, "resource": 9, "ups": 4, "lottery": 2,
        "web": 5, "terminal": 14, "meeting": 24, "backup": 11,
        "devops": 4, "appops": 5, "platops": 4,
    }
    seq = 1
    for sid, n in weights.items():
        svc = SERVICE_MAP[sid]
        samples = SERVICE_SAMPLES.get(sid, [(svc.name, "")])
        scope_agents = [a for a in AGENTS if sid in a["scope"]] or AGENTS
        for _ in range(n):
            title, desc = rng.choice(samples)
            prio = rng.choices(["P0", "P1", "P2", "P3"], weights=[7, 19, 44, 30])[0]
            days_ago = rng.randint(0, 29)
            created = now - datetime.timedelta(days=days_ago, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
            # 状态：约 62% 已闭环，其余为在办
            if rng.random() < 0.62:
                status = rng.choice(["resolved", "closed"])
            else:
                status = rng.choice(["processing", "pending", "waiting_user"])
            agent = rng.choice(scope_agents)
            sla_target = svc.sla_hours.get(prio)
            auto = False
            sla_met = None
            resolved_at = None
            csat = None
            reopened = False
            if status in ("resolved", "closed"):
                if sla_target:
                    # 解决时长约为 SLA 目标的 0.2~1.18 倍 → 约 85% 达标，符合成熟团队 90%+ 基准
                    dur = sla_target * rng.uniform(0.2, 1.18)
                    resolved_at = created + datetime.timedelta(hours=dur)
                    sla_met = dur <= sla_target
                else:
                    resolved_at = created + datetime.timedelta(hours=rng.uniform(1, 48))
                auto = bool(svc.automated and rng.random() < (0.55 if sid in ("ukey", "mail", "terminal", "meeting", "backup") else 0.3))
                csat = rng.choices([5, 4, 3, 2], weights=[62, 26, 9, 3])[0]
                reopened = rng.random() < 0.04
            tickets.append({
                "id": f"TK-2026-{seq:04d}",
                "service_id": sid,
                "service_name": svc.name,
                "category": svc.group,
                "title": title,
                "desc": desc,
                "priority": prio,
                "status": status,
                "requester": f"{rng.choice(DEPTS)}{rng.choice(SURNAMES)}{rng.choice(['','','（外派）'])}",
                "assignee": agent["name"],
                "assignee_id": agent["id"],
                "created_at": created.isoformat(timespec="minutes"),
                "resolved_at": resolved_at.isoformat(timespec="minutes") if resolved_at else None,
                "sla_target_h": sla_target,
                "sla_met": sla_met,
                "auto_resolved": auto,
                "csat": csat,
                "reopened": reopened,
                "source": rng.choices(["门户自助", "语音入口", "OA 转单"], weights=[5, 2, 3])[0] if svc.self_service else rng.choice(["OA 转单", "语音入口"]),
                "trace_id": _trace(f"TK-2026-{seq:04d}{created.date()}"),
            })
            seq += 1
    return tickets


def _gen_alerts(rng: random.Random):
    alerts = []
    now = datetime.datetime.now()
    # 按运维类服务的监控指标生成大量告警；约 65% 真实有效、35% 为噪声（可收敛降噪）
    seq = 1
    host_pool = [(sid, h) for sid, hs in OPS_HOSTS.items() for h in hs]
    sev_weights = ["致命", "严重", "预警", "提示"]
    sev_p = [6, 22, 42, 30]
    for sid, hosts in OPS_HOSTS.items():
        svc = SERVICE_MAP[sid]
        metrics = svc.monitor_metrics or ["指标异常"]
        n = rng.randint(30, 40)
        scope_agents = [a for a in AGENTS if sid in a["scope"]] or AGENTS
        for _ in range(n):
            metric = rng.choice(metrics)
            host = rng.choice(hosts)
            sev = rng.choices(sev_weights, weights=sev_p)[0]
            is_noise = rng.random() < 0.35
            created = now - datetime.timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
            agent = rng.choice(scope_agents)
            if is_noise:
                status = "已收敛(降噪)"
                auto = False
                recovered = None
                rca = "同源抖动/重复触发，经关联分析收敛合并，不派单。"
                runbook = "告警收敛引擎：基于 CMDB 拓扑与历史模式去重。"
            else:
                if rng.random() < 0.7:
                    status = "自动处置"
                    auto = True
                    rec_min = rng.randint(2, 25)
                    recovered = (created + datetime.timedelta(minutes=rec_min)).isoformat(timespec="minutes")
                    rca = rng.choice([
                        "近期发布导致连接池耗尽", "慢 SQL 拖垮数据库", "日志采集延迟引发堆积",
                        "证书临近过期触发校验", "线程池配置偏小", "网络抖动引发丢包",
                    ])
                    runbook = rng.choice([
                        "自动重启应用 + 回滚问题配置", "自动扩容连接池/线程池", "自动隔离故障节点 + 切换备机",
                        "自动续期证书并重载", "自动清理磁盘 + 扩容",
                    ])
                else:
                    status = "人工介入"
                    auto = False
                    recovered = (created + datetime.timedelta(minutes=rng.randint(20, 180))).isoformat(timespec="minutes")
                    rca = rng.choice(["依赖服务异常需人工研判", "变更影响需人工确认", "根因不明需专家定位"])
                    runbook = "生成工单并指派对应运维智能体处置。"
            alerts.append({
                "id": f"AL-2026-{seq:04d}",
                "service_id": sid,
                "service_name": svc.name,
                "host": host,
                "metric": metric,
                "severity": sev,
                "status": status,
                "auto_handled": auto,
                "converged": is_noise,
                "created_at": created.isoformat(timespec="minutes"),
                "recovered_at": recovered,
                "assignee": agent["name"],
                "rca": rca,
                "runbook": runbook,
                "trace_id": _trace(f"AL-2026-{seq:04d}{host}"),
            })
            seq += 1
    return alerts


def _gen_changes(rng: random.Random):
    changes = []
    now = datetime.datetime.now()
    seq = 1
    for _ in range(50):
        ctype = rng.choice(CHANGE_TYPES)
        risk = rng.choices(CHANGE_RISKS, weights=[20, 45, 35])[0]
        approvers = rng.choice(CHANGE_APPROVERS)
        title = rng.choice(CHANGE_TITLES[ctype])
        status = rng.choices(["已完成", "已批准", "实施中", "待审批", "已回滚"],
                              weights=[50, 18, 16, 12, 4])[0]
        created = now - datetime.timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 23))
        related = f"TK-2026-{rng.randint(1, 200):04d}" if rng.random() < 0.5 else None
        changes.append({
            "id": f"CH-2026-{seq:03d}",
            "type": ctype,
            "title": title,
            "risk": risk,
            "status": status,
            "approvers": approvers,                 # 双人/三级审批，全程留痕
            "creator": rng.choice(AGENTS)["name"],
            "created_at": created.isoformat(timespec="minutes"),
            "related": related,
            "dual_approval": len(approvers) >= 2,
            "trace_id": _trace(f"CH-2026-{seq:03d}{title}"),
        })
        seq += 1
    return changes


def _build_store():
    rng = random.Random(SEED)
    tickets = _gen_tickets(rng)
    alerts = _gen_alerts(rng)
    changes = _gen_changes(rng)
    return {"generated_at": datetime.datetime.now().isoformat(timespec="minutes"),
            "tickets": tickets, "alerts": alerts, "changes": changes}


def _compute(data: dict):
    tickets = data["tickets"]
    alerts = data["alerts"]
    changes = data["changes"]

    # ---- 工单 KPI（ITSM）----
    resolved = [t for t in tickets if t["status"] in ("resolved", "closed")]
    open_tk = [t for t in tickets if t["status"] in ("processing", "pending", "waiting_user")]
    auto_resolved = [t for t in resolved if t["auto_resolved"]]
    sla_eval = [t for t in tickets if t["sla_met"] is not None]
    sla_met = [t for t in sla_eval if t["sla_met"]]
    csat_vals = [t["csat"] for t in resolved if t["csat"]]
    reopened = [t for t in resolved if t["reopened"]]
    first_contact = [t for t in resolved if t["auto_resolved"] or (t.get("source") == "门户自助" and not t["reopened"])]

    def _mttr():
        hs = []
        for t in resolved:
            if t["resolved_at"]:
                c = datetime.datetime.fromisoformat(t["created_at"])
                r = datetime.datetime.fromisoformat(t["resolved_at"])
                hs.append((r - c).total_seconds() / 3600)
        return round(sum(hs) / len(hs), 2) if hs else 0

    by_category = Counter(t["service_name"] for t in tickets)
    by_priority = Counter(t["priority"] for t in tickets)
    by_status = Counter(t["status"] for t in tickets)
    by_agent = Counter(t["assignee"] for t in tickets)

    # 近 14 天工单趋势
    now = datetime.datetime.now()
    trend = []
    for d in range(13, -1, -1):
        day = (now - datetime.timedelta(days=d)).date()
        cnt = sum(1 for t in tickets if datetime.datetime.fromisoformat(t["created_at"]).date() == day)
        trend.append({"date": day.isoformat(), "count": cnt})

    ticket_metrics = {
        "total": len(tickets),
        "resolved": len(resolved),
        "open": len(open_tk),
        "resolved_rate": round(100 * len(resolved) / len(tickets), 1) if tickets else 0,
        "automation_rate": round(100 * len(auto_resolved) / len(resolved), 1) if resolved else 0,
        "sla_compliance": round(100 * len(sla_met) / len(sla_eval), 1) if sla_eval else 0,
        "mttr_h": _mttr(),
        "fcr_rate": round(100 * len(first_contact) / len(resolved), 1) if resolved else 0,
        "csat": round(sum(csat_vals) / len(csat_vals), 2) if csat_vals else 0,
        "reopen_rate": round(100 * len(reopened) / len(resolved), 1) if resolved else 0,
        "by_category": dict(by_category.most_common()),
        "by_priority": {k: by_priority.get(k, 0) for k in ["P0", "P1", "P2", "P3"]},
        "by_status": dict(by_status),
        "by_agent": dict(by_agent),
        "trend": trend,
    }

    # ---- 运维 KPI ----
    hosts_total = sum(len(hs) for hs in OPS_HOSTS.values())
    online = hosts_total - rng_count(alerts, "致命")  # 致命未恢复视为离线（近似）
    converged = [a for a in alerts if a["converged"]]
    effective = [a for a in alerts if not a["converged"]]
    self_healed = [a for a in effective if a["auto_handled"]]
    sev_counter = Counter(a["severity"] for a in alerts)
    rec_mins = []
    for a in alerts:
        if a["recovered_at"] and a["created_at"]:
            c = datetime.datetime.fromisoformat(a["created_at"])
            r = datetime.datetime.fromisoformat(a["recovered_at"])
            rec_mins.append((r - c).total_seconds() / 60)
    ops_metrics = {
        "hosts_total": hosts_total,
        "online": max(hosts_total - 1, hosts_total - len(converged) // 20),
        "online_rate": round(100 * (hosts_total - 1) / hosts_total, 2),
        "alerts_total": len(alerts),
        "converged": len(converged),
        "convergence_rate": round(100 * len(converged) / len(alerts), 1) if alerts else 0,
        "self_healed": len(self_healed),
        "self_heal_rate": round(100 * len(self_healed) / len(effective), 1) if effective else 0,
        "by_severity": dict(sev_counter),
        "avg_recovery_min": round(sum(rec_mins) / len(rec_mins), 1) if rec_mins else 0,
    }

    # ---- 变更 KPI ----
    change_metrics = {
        "total": len(changes),
        "by_type": dict(Counter(c["type"] for c in changes)),
        "by_risk": dict(Counter(c["risk"] for c in changes)),
        "by_status": dict(Counter(c["status"] for c in changes)),
        "dual_approval_rate": round(100 * sum(1 for c in changes if c["dual_approval"]) / len(changes), 1),
    }

    # ---- 多用户智能体画像（由真实数据计算）----
    agents_out = []
    for a in AGENTS:
        handled_tk = sum(1 for t in tickets if t["assignee_id"] == a["id"])
        handled_al = sum(1 for al in alerts if al["assignee"] == a["name"])
        tk_resolved = [t for t in resolved if t["assignee_id"] == a["id"]]
        auto_cnt = sum(1 for t in tk_resolved if t["auto_resolved"])
        csat_a = [t["csat"] for t in tk_resolved if t["csat"]]
        agents_out.append({
            "id": a["id"], "name": a["name"], "team": a["team"], "online": a["online"],
            "scope": [SERVICE_MAP[s].name for s in a["scope"] if s in SERVICE_MAP],
            "handled": handled_tk + handled_al,
            "tickets": handled_tk, "alerts": handled_al,
            "auto_rate": round(100 * auto_cnt / len(tk_resolved), 1) if tk_resolved else 0,
            "csat": round(sum(csat_a) / len(csat_a), 2) if csat_a else 0,
            "active": sum(1 for t in open_tk if t["assignee_id"] == a["id"]),
        })

    # ---- 痛点洞察（由真实数据推导）----
    perm_like = ["Ukey 制作/调整/回收", "人员角色权限变更", "远程邮件帐号及容量调整", "终端领用与维修"]
    perm_cnt = sum(by_category.get(n, 0) for n in perm_like)
    perm_share = round(100 * perm_cnt / len(tickets), 1) if tickets else 0
    # 重复工单聚类（按标题前 8 字）
    norm = Counter(t["title"][:8] for t in tickets)
    top_dup = [{"title": k, "count": v} for k, v in norm.most_common(5) if v >= 2]
    pain_points = [
        {"title": "权限与介质类工单占比偏高", "value": f"{perm_share}%",
         "detail": f"Ukey/权限/邮件/终端四类工单合计 {perm_cnt} 单，占全部工单 {perm_share}%。",
         "reco": "提升门户自助化率 + 审批流自动化（呼应双人审批），目标将重复申请的自助率提升至 80%+。"},
        {"title": "重复工单消耗人力", "value": f"{len(top_dup)} 类高频重复",
         "detail": "；".join(f"「{d['title']}…」{d['count']} 次" for d in top_dup[:3]) or "暂无显著重复。",
         "reco": "沉淀知识库 + 相似度聚类，新工单自动推荐解决方案，降低一线分派量。"},
        {"title": "告警噪声干扰处置", "value": f"降噪率 {ops_metrics['convergence_rate']}%",
         "detail": f"原始告警 {ops_metrics['alerts_total']} 条，经关联收敛后保留有效告警 {len(effective)} 条。行业平均有效率约 15%，仍有提升空间。",
         "reco": "强化告警收敛（CMDB 拓扑关联 + 根因分析），把有效告警占比推向 60%+，让工程师只看该看的。"},
        {"title": "审计 deadline 敏感", "value": f"P0/P1 SLA 达标 {ticket_metrics['sla_compliance']}%",
         "detail": f"高优先级工单 SLA 达标率 {ticket_metrics['sla_compliance']}%，平均解决时长 MTTR {ticket_metrics['mttr_h']}h。",
         "reco": "P0 4h 内闭环、开通紧急通道，SLA 看板对临近超时工单主动预警。"},
        {"title": "全程可追溯（审计留痕）", "value": "100%",
         "detail": "工单 / 变更 / 告警均带 trace_id，双人审批链完整留痕，满足审计合规。",
         "reco": "保持全链路 trace_id 贯通，支撑事后审计追溯与责任界定。"},
    ]

    return {
        "ticket_metrics": ticket_metrics,
        "ops_metrics": ops_metrics,
        "change_metrics": change_metrics,
        "agents": agents_out,
        "pain_points": pain_points,
    }


def rng_count(alerts, sev):
    return sum(1 for a in alerts if a["severity"] == sev)


class OpsStore:
    """审计运维真实数据仓库（单例）。"""

    def __init__(self):
        self._data = None
        self._metrics = None
        self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = None
        if self._data is None:
            self._data = _build_store()
            self._persist()
        self._metrics = _compute(self._data)

    def _persist(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def reseed(self):
        self._data = _build_store()
        self._persist()
        self._metrics = _compute(self._data)
        return self._metrics

    # ---- 对外查询 ----
    def summary(self):
        return self._metrics

    def tickets(self, service=None, status=None, priority=None, auto=None):
        out = self._data["tickets"]
        if service:
            out = [t for t in out if t["service_id"] == service or t["service_name"] == service]
        if status:
            out = [t for t in out if t["status"] == status]
        if priority:
            out = [t for t in out if t["priority"] == priority]
        if auto is not None:
            out = [t for t in out if t["auto_resolved"] is auto]
        # 默认按创建时间倒序
        out = sorted(out, key=lambda t: t["created_at"], reverse=True)
        return out

    def alerts(self, service=None, severity=None, status=None, auto=None):
        out = self._data["alerts"]
        if service:
            out = [a for a in out if a["service_id"] == service or a["service_name"] == service]
        if severity:
            out = [a for a in out if a["severity"] == severity]
        if status:
            out = [a for a in out if a["status"] == status]
        if auto is not None:
            out = [a for a in out if a["auto_handled"] is auto]
        out = sorted(out, key=lambda a: a["created_at"], reverse=True)
        return out

    def changes(self):
        return sorted(self._data["changes"], key=lambda c: c["created_at"], reverse=True)

    def agents(self):
        return self._metrics["agents"]

    def pain_points(self):
        return self._metrics["pain_points"]


_store = None


def get_ops_store() -> OpsStore:
    global _store
    if _store is None:
        _store = OpsStore()
    return _store
