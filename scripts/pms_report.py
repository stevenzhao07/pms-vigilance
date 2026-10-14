#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pms_report.py — 上市后监督（PMS）与警戒时限计算器
==================================================
把 NMPA / EU MDR / FDA 的不良事件报告、召回、PSUR 时限落成可运行的计算器。
所有时限均经一手核实（gov.cn 法规原文 / Regulation (EU) 2017/745 Art.87 /
21 CFR 803 & 806），并在输出中标注出处。

已核实事实（2026-10-12 以国务院公报官方全文逐条复核）：
  NMPA《医疗器械不良事件监测和再评价管理办法》（国家市场监督管理总局、国家卫生
  健康委员会令第1号，2019-01-01 施行）：
    导致死亡 → 7 日内报告；导致严重伤害/可能导致严重伤害或死亡 → 20 日内；
    境外持有人代理人（进口器械境外事件）→ 30 日内；
    死亡事件评价结果 → 30 日内；其他 → 45 日内；
    群体事件 → 12 小时内电话报告 + 24 小时内按个例报告；
    定期风险评价报告 → 每满一年后 60 日内。
  NMPA《医疗器械召回管理办法》（国家食品药品监督管理总局令第29号，2017-05-01 施行）：
    第十五条：一级 1 日 / 二级 3 日 / 三级 7 日内通知到有关经营企业、使用单位
    或告知使用者（**唯一的分级时限**）；
    第十六条：作出召回决定后**立即**提交召回事件报告表，**5 个工作日**内提交
    调查评估报告和召回计划备案；
    第二十条：实施过程中定期提交召回计划实施情况报告；
    第二十二条：召回完成后 **10 个工作日**内提交总结评估报告。
    （历史勘误：2026-10-12 前版本曾误载"1-3/3-7/7-15 日报告、10/30/60 日通知、
    30/60/90 日评估"——该组数字在令第29号全文中不存在，已按官方全文删除。）
  EU MDR Art.87：严重公共卫生威胁 2 天；死亡或意外严重恶化 10 天；
    其他严重事件 15 天；IIb/III PSUR 每年、IIa 至少每两年。
  FDA：MDR 30 日历日（21 CFR 803.50）；需补救行动的 5 工作日；
    user facility 10 工作日；召回/纠正移除报告 10 工作日（21 CFR 806）。
"""
from __future__ import annotations
import argparse
import datetime as dt
import sys

# 辖区 × 事件类型 → (时限值, 单位: day/workday/hour, 法规出处)
# --- 辖区别名归一化（2026-10-14 跨模块统一词表）---
# 目标：同一句话在医疗线各模块间通用——既接受 ISO 国家码，也接受监管机构缩写。
# 注意：东盟(ASEAN) / 拉美(LATAM) 尚无实现，仍会被下方校验明确拒绝。
_JURIS_ALIAS = {
    "CN": "CN", "NMPA": "CN", "CHINA": "CN",
    "US": "US", "USA": "US", "FDA": "US",
    "EU": "EU", "MDR": "EU", "CE": "EU",
    "JP": "JP", "JAPAN": "JP", "PMDA": "JP",
}
_JURIS_LOCAL = {"CN": "CN", "US": "FDA", "EU": "EU"}


def _norm_juris(j):
    """把用户输入归一化到本模块内部键；未知值原样返回，交由原校验明确拒绝。"""
    s = (j or "").strip().upper()
    c = _JURIS_ALIAS.get(s)
    if c is None:
        return s
    return _JURIS_LOCAL.get(c, c)


REPORTING_RULES = {
    ("CN", "death"): (7, "day", "《医疗器械不良事件监测和再评价管理办法》第二十五条"),
    ("CN", "serious"): (20, "day", "同上"),
    ("CN", "foreign_holder"): (30, "day", "第二十七条（境外持有人代理人）"),
    ("CN", "cluster"): (12, "hour", "第三十一条（群体事件，电话报告）"),
    ("EU", "public_health_threat"): (2, "day", "MDR Art. 87(4)"),
    ("EU", "death"): (10, "day", "MDR Art. 87(5)"),
    ("EU", "serious"): (15, "day", "MDR Art. 87(3)"),
    ("FDA", "mdr_30"): (30, "day", "21 CFR 803.50"),
    ("FDA", "mdr_5work"): (5, "workday", "21 CFR 803.53（需补救行动）"),
    ("FDA", "user_facility"): (10, "workday", "21 CFR 803.30"),
}

# 召回时限（NMPA《医疗器械召回管理办法》国家食品药品监督管理总局令第29号，官方全文逐条核实 2026-10-12）
# 第十五条：一级 1 日 / 二级 3 日 / 三级 7 日内通知到有关经营企业、使用单位或告知使用者
# 第十六条：立即提交召回事件报告表 + 5 个工作日内提交调查评估报告和召回计划备案
# 第二十条：实施过程中定期提交召回计划实施情况报告
# 第二十二条：召回完成后 10 个工作日内提交总结评估报告
# 注意：除「通知已知对象」有 1/3/7 日分级外，其余时限不按级别分档。
RECALL_RULES = {
    1: {"notify_known": 1,
        "desc": "使用该器械可能或已经引起严重健康危害"},
    2: {"notify_known": 3,
        "desc": "可能或已经引起暂时的或可逆的健康危害"},
    3: {"notify_known": 7,
        "desc": "引起危害的可能性较小但仍需召回"},
}
RECALL_COMMON = {
    "报告监管部门": "立即提交召回事件报告表；5 个工作日内提交调查评估报告和召回计划备案（第十六条）",
    "实施过程报告": "定期提交召回计划实施情况报告（第二十条）",
    "总结评估": "召回完成后 10 个工作日内提交总结评估报告（第二十二条）",
    "出处": "《医疗器械召回管理办法》（国家食品药品监督管理总局令第29号）第十五/十六/二十/二十二条",
}

EVENTS = {
    "CN": ["death", "serious", "foreign_holder", "cluster"],
    "EU": ["public_health_threat", "death", "serious"],
    "FDA": ["mdr_30", "mdr_5work", "user_facility"],
}


def add_days(d: dt.date, n: int) -> dt.date:
    return d + dt.timedelta(days=n)


def add_workdays(d: dt.date, n: int) -> dt.date:
    cur, left = d, n
    while left > 0:
        cur += dt.timedelta(days=1)
        if cur.weekday() < 5:
            left -= 1
    return cur


def add_hours(d: dt.datetime, n: int) -> dt.datetime:
    return d + dt.timedelta(hours=n)


def deadline(aware: dt.date, juris: str, event: str) -> dict:
    if juris not in EVENTS:
        raise ValueError(f"未知辖区 {juris}（可选 {sorted(EVENTS)}）")
    if (juris, event) not in REPORTING_RULES:
        raise ValueError(f"辖区 {juris} 不支持事件 {event}（可选 {EVENTS[juris]}）")
    n, unit, src = REPORTING_RULES[(juris, event)]
    if unit == "day":
        due = add_days(aware, n)
    elif unit == "workday":
        due = add_workdays(aware, n)
    else:
        due = add_hours(dt.datetime.combine(aware, dt.time(0, 0)), n)
    return {
        "辖区": juris, "事件类型": event, "获知日期": str(aware),
        "时限": f"{n} {unit}", "截止": str(due),
        "法规出处": src,
        "口径": "日历日" if unit == "day" else ("工作日" if unit == "workday" else "小时"),
    }


def recall_table(level: int) -> dict:
    r = RECALL_RULES[level]
    return {"级别": level, "定义": r["desc"],
            "通知已知使用单位(日)": r["notify_known"],
            **RECALL_COMMON}


def psur_table() -> list[dict]:
    return [
        {"辖区": "EU MDR", "类别": "Class IIb / III", "周期": "每年（PSUR）", "出处": "MDR Art. 86"},
        {"辖区": "EU MDR", "类别": "Class IIa", "周期": "至少每两年", "出处": "MDR Art. 86"},
        {"辖区": "NMPA", "类别": "全部", "周期": "每满一年后 60 日内（定期风险评价报告）", "出处": "办法第三十九条（时限）/第三十八条（撰写义务）"},
    ]


def _fmt(title: str, d: dict) -> str:
    return f"### {title}\n" + "\n".join(f"  - {k}: {v}" for k, v in d.items())


def _demo() -> int:
    print("PMS/警戒时限计算器 · 演示\n")
    aware = dt.date(2026, 10, 1)
    for j, e in [("CN", "death"), ("CN", "serious"), ("EU", "death"),
                 ("EU", "serious"), ("EU", "public_health_threat"),
                 ("FDA", "mdr_30"), ("FDA", "mdr_5work")]:
        print(_fmt(f"{j}/{e}（获知 2026-10-01）", deadline(aware, j, e)))
    print("\n### 召回分级时限（NMPA）")
    for lv in (1, 2, 3):
        print(_fmt(f"{lv} 级召回", recall_table(lv)))
    print("\n### PSUR / 定期风险评价周期")
    for r in psur_table():
        print(_fmt(r["辖区"], r))
    print("\n[demo] 时限经一手核实；紧急事件以「立即报告」为第一原则，本工具只兜最迟期限。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="PMS/警戒时限计算器")
    ap.add_argument("--demo", action="store_true", help="跑内置演示")
    ap.add_argument("--selftest", action="store_true", help="跑内置自测（断言 + 负对照 + xfail）")
    ap.add_argument("--aware", help="获知日期 YYYY-MM-DD")
    ap.add_argument("--jurisdiction", help="CN|NMPA | US|FDA | EU|MDR | JP|PMDA | ALL（别名互通；ASEAN/LATAM 未实现）")
    ap.add_argument("--event", help="事件类型（见 --list-events）")
    ap.add_argument("--list-events", action="store_true", help="列出各辖区事件类型")
    ap.add_argument("--recall", action="store_true", help="打印召回分级时限表")
    ap.add_argument("--level", type=int, choices=[1, 2, 3], default=1, help="召回级别")
    ap.add_argument("--psur", action="store_true", help="打印 PSUR/定期风险评价周期")
    args = ap.parse_args()
    if getattr(args, "selftest", False):
        return _selftest()

    if args.demo:
        return _demo()
    if args.list_events:
        for j, evs in EVENTS.items():
            print(f"{j}: {', '.join(evs)}")
        return 0
    if args.recall:
        print(_fmt(f"{args.level} 级召回（NMPA）", recall_table(args.level)))
        return 0
    if args.psur:
        for r in psur_table():
            print(_fmt(r["辖区"], r))
        return 0
    if args.aware and args.jurisdiction and args.event:
        # 日期与辖区/事件组合均做友好校验（2026-10-12 压力测试修复：
        # 原实现 --aware 乱码 / --event 非法 / --jurisdiction 非法 均裸 traceback）
        try:
            d = dt.date.fromisoformat(args.aware)
        except ValueError:
            print(f"[error] --aware 须为 YYYY-MM-DD（收到 {args.aware!r}）", file=sys.stderr)
            return 2
        try:
            row = deadline(d, _norm_juris(args.jurisdiction), args.event)
        except ValueError as e:
            print(f"[error] {e}", file=sys.stderr)
            return 2
        print(_fmt(f"{args.jurisdiction}/{args.event}", row))
        return 0
    ap.print_help()
    return 2


# ==================== 内置自测（--selftest） ====================
# 由 conformance 补丁于 2026-10-14 生成（生成器 v2）。
# 特性：端到端 CLI 调用 + 内容断言 + 负对照 + xfail（已知缺陷显式标注，不掩盖）。
_SELFTEST_CASES = [(['--demo'], 0, ['召回', 'PSUR'], [], None), (['--aware', '2026-10-01', '--jurisdiction', 'CN', '--event', 'death'], 0, ['2026-10-08'], [], None), (['--aware', '2026-10-01', '--jurisdiction', 'EU', '--event', 'death'], 0, ['2026-10-11'], [], None), (['--aware', '2026-10-01', '--jurisdiction', 'FDA', '--event', 'mdr_5work'], 0, ['2026-10-08'], [], None), (['--aware', '2026-10-01', '--jurisdiction', 'XX', '--event', 'death'], 2, [], [], None), (['--aware', 'not-a-date', '--jurisdiction', 'CN', '--event', 'death'], 2, [], [], None)]


def _selftest() -> int:
    import os as _os
    import subprocess as _sp
    _here = _os.path.dirname(_os.path.abspath(__file__))
    # 仓库根：脚本位于 <repo>/scripts/ 时取上一级；否则取脚本所在目录
    _root = _os.path.dirname(_here) if _os.path.basename(_here) == "scripts" else _here
    _script = _os.path.abspath(__file__)
    _fail, _xfail, _n = [], [], 0
    for _case in _SELFTEST_CASES:
        _args, _rc, _must, _mustnot = _case[0], _case[1], _case[2], _case[3]
        _reason = _case[4] if len(_case) > 4 else None
        _n += 1
        _p = _sp.run([sys.executable, _script] + _args, capture_output=True, cwd=_root)
        _out = _p.stdout.decode("utf-8", "replace")
        _bad = []
        if _p.returncode != _rc:
            _bad.append(f"rc={_p.returncode} 期望 {_rc}")
        for _m in _must:
            if _m not in _out:
                _bad.append(f"输出缺少 {_m!r}")
        for _m in _mustnot:
            if _m in _out:
                _bad.append(f"输出含禁止内容 {_m!r}")
        if _rc == 0 and not _out.strip():
            _bad.append("rc=0 但输出为空（假绿）")
        if _bad:
            if _reason:
                _xfail.append(f"xfail args={_args}：{'；'.join(_bad)} ← 已知缺陷：{_reason}")
            else:
                _fail.append(f"args={_args}：{'；'.join(_bad)}")
    # 通用负对照：未知参数必须非零
    _n += 1
    _p = _sp.run([sys.executable, _script, "--__nonexistent_flag__"], capture_output=True, cwd=_root)
    if _p.returncode == 0:
        _fail.append("负对照失败：未知参数竟返回 0")
    for _x in _xfail:
        print("[selftest][xfail] " + _x)
    if _fail:
        print(f"[selftest] FAILED {len(_fail)}/{_n}")
        for _f in _fail:
            print("  - " + _f)
        return 1
    print(f"[selftest] PASS {_n - len(_xfail)}/{_n}（含负对照；xfail {len(_xfail)} 项为已知缺陷）")
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
