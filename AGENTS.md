# AGENTS.md · pms-vigilance

> 机器可发现入口（AI 编码代理 / Codex / Claude / Cursor）。单一事实源：本文件。

## 这是什么
上市后监督（PMS）与警戒（Vigilance）时限计算与合规工具：NMPA 不良事件报告（死亡 7 日/严重伤害 20 日/群体 12 小时）、EU MDR Art.87（2/10/15 天）、FDA MDR（30 日/5 工作日/806 召回 10 工作日）、召回分级时限表（NMPA 一级 1 日起/FDA Class I–III）、PSUR/定期风险评价周期。输入获知日期，输出各辖区截止日。

## 运行
```bash
python scripts/pms_report.py --demo
python scripts/pms_report.py --help
```

## 扩展契约（lgd-skeleton/1.0）
- **一切即插件**：仅依赖声明式 `module.json`，零配置。
- **按需装（lazy）**：仅 triggers 命中时加载。
- **可嵌套（nested）**：可被 `medical-ai-toolkit` 总入口路由。
- **扩展点**：`plugins/`(新增辖区/事件类型：在 REPORTING_RULES 加一项。)

## 红线
纯技术贡献，不含商业营销；MedXpert 仅作为贡献者署名（@stevenzhao07）。
