<!--
PR 模板（详见 CONTRIBUTING.md §5）
请尽量保持每个分节简短，能让 reviewer 5 分钟内看懂。
-->

## 背景

<!-- 这个 PR 解决什么问题？关联哪个 milestone / issue？为什么现在做？ -->

- Milestone: 
- 关联 issue / spec 章节: 

## 改动

<!-- 列 3-7 个 bullet，描述主要变化 -->

- 
- 
- 

## 风险与回滚

<!-- 这个改动可能在哪里出事？怎么撤回？ -->

- 风险点 1: 
- 回滚方式: 

## 测试

- [ ] 单元测试通过 (`uv run pytest -x`)
- [ ] 集成测试通过（如适用）
- [ ] 覆盖率不退化（如适用）
- [ ] 手动验证步骤:
  1. 
  2. 

## Checklist（合并前必须全部勾完）

- [ ] 类型 hint 完整
- [ ] 日志走 structlog（无 `print()` / `logging`）
- [ ] 配置走 YAML，密钥走 `.env`
- [ ] commit 走 `<type>(<scope>): <subject>` 规范
- [ ] 不引入实盘下单代码
- [ ] CHANGELOG.md 已更新（如里程碑 / 重要功能完成）
- [ ] 涉及敏感模块时已 request 2 人 review（详见 CONTRIBUTING.md §6）
- [ ] CI 全绿

## 截图 / 演示（可选）

<!-- 如改动涉及 UI / POC / 推送内容，附截图 -->
