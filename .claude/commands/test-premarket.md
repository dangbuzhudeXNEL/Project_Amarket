手动测试 news-analyst agent 的盘前汇总流程。

## 用法

```
/test-premarket [date]
```

`date` 可选，默认今天。格式 `YYYY-MM-DD`。

## 执行步骤

1. **确认日期**：默认今天（`Asia/Shanghai` 时区）。用户可指定其他日期。

2. **检查原始新闻**：
   - 检查 `data/news/raw/<date>/` 目录是否存在
   - 如果不存在或为空，输出提示："原始新闻为 0，需要先跑 NewsCollector 抓数据"，但仍然继续测试 agent 写出空摘要

3. **统计输入**：
   - 用 `Glob` 数 `data/news/raw/<date>/*.json` 的数量
   - 报告给用户："找到 N 条原始新闻"

4. **调用 news-analyst agent**：
   - 用 Task 工具或直接 Read agent 定义，然后模拟调用
   - 实际 prompt 模板：
     ```
     读取 data/news/raw/<date>/*.json (共 N 条新闻)，
     生成今日盘前汇总，
     写入 data/news/summaries/<date>-premarket.json
     ```

5. **校验输出**：
   - 读 `data/news/summaries/<date>-premarket.json`
   - 检查必需字段：date, kind, summary_markdown, generated_at, input_news_count, model
   - 用 `json.loads()` 校验合法性
   - 报告校验结果

6. **预览结果**：
   - 把 `summary_markdown` 渲染出来给用户看
   - 把 `highlights` 列表也展示

## 输出格式

```
🧪 News-Analyst Agent 测试报告

📅 测试日期: 2026-06-14
📂 原始新闻: 47 条 (data/news/raw/2026-06-14/)
🤖 Agent 状态: completed | degraded | timeout | error
✅ 输出校验: PASS / FAIL (具体原因)
📄 输出文件: data/news/summaries/2026-06-14-premarket.json (4.2 KB)

📋 生成的盘前简报预览:

[渲染 summary_markdown]

🎯 Top Highlights:
[列表展示]

⏱️ 总耗时: XX 秒
```

## 异常处理

- 如果 agent 失败，给出具体错误（subprocess 退出码、stdout/stderr 摘要）
- 如果输出 JSON 不合法，定位到具体字段
- 如果 agent timeout，建议用户检查 `agents.yml` 里 `timeout_seconds` 是否够
