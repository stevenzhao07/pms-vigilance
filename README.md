# pms-vigilance

> **Contributed by [@stevenzhao07](https://github.com/stevenzhao07) · Affiliation: MedXpert (medical-device RA & regulatory consultancy) · Pure technical input, no commercial promotion.**

上市后监督（PMS）与警戒（Vigilance）时限计算与合规工具：NMPA 不良事件报告（死亡 7 日/严重伤害 20 日/群体 12 小时）、EU MDR Art.87（2/10/15 天）、FDA MDR（30 日/5 工作日/806 召回 10 工作日）、召回分级时限表（NMPA 一级 1 日起/FDA Class I–III）、PSUR/定期风险评价周期。输入获知日期，输出各辖区截止日。

这是 MedXpert 把"医疗 AI 信任"方法论工程化落地的可插拔模块之一——把抽象的合规要求变成一条可重复运行的命令或参考实现。方法论四要素（白话版）：**治理守护者 XCGS** ＝ 为 AI 留下可核验的治理证据；**立法者 A³ Laws** ＝ 给自主系统划权限 / 监督 / 追责三条硬边界；**护照官 AI 护照** ＝ 为模型签发可追溯的身份凭证；**人机共存** ＝ 明确人类与 AI 的分工与兜底。

---

## 可插拔模块契约（lgd-skeleton/1.0）

本仓库是一个 **`lgd-skeleton/1.0` 可插拔模块**：

- **一切即插件**：仅依赖声明式 `module.json`，零配置；
- **按需装（lazy）**：仅 triggers 命中时加载；
- **可嵌套（nested）**：可被 `medical-ai-toolkit` 总入口路由发现；
- **扩展点**：`plugins/`(新增辖区/事件类型：在 REPORTING_RULES 加一项。)。

机器可发现入口：`AGENTS.md` · `CLAUDE.md` · `llms.txt`。

## 特性

- 报告时限计算：输入获知日期+辖区+事件类型 → 截止日期（自然日/工作日自动区分）
- 召回分级表：NMPA 一级/二级/三级（通知/报告/评估时限）与 FDA Class I/II/III
- PSUR 周期：EU MDR IIb/III 年度、IIa 两年；NMPA 定期风险评价每满一年 60 日内
- 已核实事实全部标注法规出处（Art.87 / 21 CFR 803/806 / 总局令第 1 号、第 29 号）

## 内容说明

时限依据已核实官方文本整理；日/工作日、时区按输入日期本地计算。紧急事件以「立即报告」为第一原则，计算器只做最迟期限兜底。

## 免责声明

本工具仅提供结构化模板与计算能力，**不构成法规建议、临床建议或产品合规结论**。具体产品的注册、临床评价、灭菌验证、风险分析、软件分级等决策，须由合资格人员依据目标辖区（NMPA / FDA / EU MDR / PMDA）最新法规文本作出；条款与限值以官方发布文本为准。使用本工具产生的一切后果由使用者自行承担。

## 使用

```bash
python scripts/pms_report.py --demo
python scripts/pms_report.py --aware 2026-10-01 --jurisdiction EU --event death
python scripts/pms_report.py --recall --level 1 --jurisdiction CN
```

## 快速开始（30 秒）

```bash
git clone https://github.com/stevenzhao07/pms-vigilance.git && cd pms-vigilance
python scripts/pms_report.py --demo
```

> 想参与或遇到问题？[提 Issue](https://github.com/stevenzhao07/pms-vigilance/issues) · 完整《AI 参与指南》见 [medical-ai-toolkit](https://github.com/stevenzhao07/medical-ai-toolkit)。

## 路由（总入口）

本模块由 **[medical-ai-toolkit](https://github.com/stevenzhao07/medical-ai-toolkit)** 作为 `lgd-skeleton/1.0` 总入口自动路由发现。

## 关联模块

- [iso14971-risk-file](https://github.com/stevenzhao07/iso14971-risk-file)
- [samd-ra-toolkit](https://github.com/stevenzhao07/samd-ra-toolkit)
- [clinical-evaluation](https://github.com/stevenzhao07/clinical-evaluation)

## 许可

Apache-2.0 — 见 [LICENSE](./LICENSE)。

## 关联（方法论来源）

- 理念溯源：个人专家关于医疗 AI 信任与治理的公开方法论（个人观点，不构成标准）
- 同账号系列：见 `medical-ai-toolkit` 导航
