"""学习异常检测：把 AIOps 的「指标突变 / 缺失 / 反复抖动」迁移到「学习异常」。

对标 Step3 提取的 AIOps 范式——监控指标的异常检测，迁移到对「用户学习指标」的异常检测：
  - accuracy_drop  正确率骤降  ≈ 指标突降（某个知识点近期正确率相对基线明显下滑）
  - streak_break   连续断签    ≈ 指标中断/缺失（打卡记录出现连续多日空窗）
  - repeat_wrong   错题反复    ≈ 指标反复抖动（同一题目反复错，error_count 居高不下）

检测手段（轻量、零依赖、可解释，便于面试讲清原理）：
  - 时间序列分段：每个知识点的正确率序列切 baseline / recent 两段，比较均值差；
  - 阈值 + 幅度分级（severity: high / mid）；
  - 断签用「日期连续缺失天数」判定（含「截至今天的当前空窗」）；
  - 错题反复用 error_count 阈值判定。
生产可替换为「Z-score / EWMA / 孤立森林」等，接口保持 detect() 同构。
"""
import datetime

from database import get_db


class LearningAnomalyDetector:
    """学习异常检测器：输入 user_id，输出可解释异常列表（含建议）。"""

    def __init__(self, drop_threshold: float = 0.15,
                 gap_days_high: int = 3, gap_days_mid: int = 2,
                 repeat_high: int = 5, repeat_mid: int = 3):
        self.drop_threshold = drop_threshold      # 正确率下滑阈值（相对基线）
        self.gap_days_high = gap_days_high        # 断签 high 阈值（连续空窗天数）
        self.gap_days_mid = gap_days_mid          # 断签 mid 阈值
        self.repeat_high = repeat_high            # 反复错 high 阈值
        self.repeat_mid = repeat_mid              # 反复错 mid 阈值

    # ---------- 统一入口 ----------
    def detect(self, user_id: int) -> dict:
        anomalies = []
        anomalies += self._detect_accuracy_drop(user_id)
        anomalies += self._detect_streak_break(user_id)
        anomalies += self._detect_repeat_wrong(user_id)
        order = {"high": 0, "mid": 1, "low": 2}
        anomalies.sort(key=lambda a: order.get(a["severity"], 3))
        return {
            "user_id": user_id,
            "count": len(anomalies),
            "has_alert": len(anomalies) > 0,
            "anomalies": anomalies,
        }

    # ---------- ① 正确率骤降（指标突降） ----------
    def _detect_accuracy_drop(self, user_id: int) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT cat, total, correct, created_at FROM quiz_records "
            "WHERE user_id=? AND total>0 ORDER BY created_at",
            (user_id,),
        ).fetchall()
        conn.close()

        by_cat: dict = {}
        for r in rows:
            by_cat.setdefault(r["cat"], []).append(r)

        out = []
        for cat, recs in by_cat.items():
            n = len(recs)
            if n < 4:           # 样本过少不判定骤降，避免噪声
                continue
            k = max(1, n // 2)
            baseline, recent = recs[:k], recs[k:]

            def _acc(rs):
                t = sum(x["total"] for x in rs)
                c = sum(x["correct"] for x in rs)
                return c / t if t else 1.0

            acc_base, acc_recent = _acc(baseline), _acc(recent)
            drop = acc_base - acc_recent
            if drop >= self.drop_threshold:
                sev = "high" if drop >= 0.25 else "mid"
                out.append({
                    "type": "accuracy_drop",
                    "severity": sev,
                    "title": f"「{cat}」正确率骤降",
                    "detail": (f"近期正确率 {acc_recent*100:.0f}% 较前期 {acc_base*100:.0f}% "
                               f"下滑 {drop*100:.0f} 个百分点（样本 {n} 次）"),
                    "suggestion": (f"建议暂停新题，先回看「{cat}」的知识点与错题，"
                                   f"用低频高重复的方式补牢基础再提速。"),
                })
        return out

    # ---------- ② 连续断签（指标中断） ----------
    def _detect_streak_break(self, user_id: int) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT check_date FROM daily_streaks WHERE user_id=? ORDER BY check_date",
            (user_id,),
        ).fetchall()
        conn.close()

        dates = sorted({datetime.date.fromisoformat(r["check_date"]) for r in rows})
        if not dates:
            return []

        max_gap = 0
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i - 1]).days - 1   # 中间缺失天数
            if gap > max_gap:
                max_gap = gap
        # 当前空窗：今天距最近一次打卡
        cur_gap = (datetime.date.today() - dates[-1]).days - 1
        if cur_gap > max_gap:
            max_gap = cur_gap

        if max_gap < self.gap_days_mid:
            return []
        sev = "high" if max_gap >= self.gap_days_high else "mid"
        return [{
            "type": "streak_break",
            "severity": sev,
            "title": "学习中断预警",
            "detail": f"检测到最长连续 {max_gap} 天未打卡，备考节奏已中断。",
            "suggestion": "中断会加速遗忘曲线衰减。今天先完成 10 分钟轻量打卡找回手感，"
                          "再逐步恢复原计划。",
        }]

    # ---------- ③ 错题反复（指标反复抖动） ----------
    def _detect_repeat_wrong(self, user_id: int) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT q.topic, wb.question_id, wb.error_count FROM wrong_book wb "
            "JOIN questions q ON wb.question_id = q.id "
            "WHERE wb.user_id=? AND wb.error_count>=?",
            (user_id, self.repeat_mid),
        ).fetchall()
        conn.close()

        out = []
        for r in rows:
            sev = "high" if r["error_count"] >= self.repeat_high else "mid"
            out.append({
                "type": "repeat_wrong",
                "severity": sev,
                "title": f"「{r['topic']}」反复错",
                "detail": f"第 {r['question_id']} 题已累计错 {r['error_count']} 次，属顽固薄弱点。",
                "suggestion": f"这类题不要仅靠刷题，建议先看解析弄清坑点，"
                              f"再做 2~3 道同类变式题固化，必要时让我帮你讲透。",
            })
        return out

    # ---------- 主动推送文案 ----------
    @staticmethod
    def format_alert(result: dict) -> str:
        if not result.get("has_alert"):
            return "暂未发现明显的学习异常，继续保持节奏👍"
        lines = ["⚠️ 学习异常预警（已为你标记，建议优先处理）："]
        for i, a in enumerate(result["anomalies"], 1):
            tag = "🔴" if a["severity"] == "high" else "🟠"
            lines.append(f"{tag} {i}. {a['title']}：{a['detail']}")
            lines.append(f"   → 建议：{a['suggestion']}")
        return "\n".join(lines)
