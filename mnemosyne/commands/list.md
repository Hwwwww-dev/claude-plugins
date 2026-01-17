---
description: 查看所有保存的会话上下文列表。
argument-hint: [--limit N] [--tag tag]
---

# /mnemosyne:list - 列表查看

用户输入: $ARGUMENTS

---

## 流程

- 读取 `.claude/mnemosyne/index.json`
- 支持：`--limit N`（默认 10），`--tag <tag>` 过滤
- 输出表格：ID/标题/标签/时间/质量

---

## 输出示例

```markdown
## 📚 已保存的上下文 (共 <N> 个)

| # | ID | 标题 | 标签 | 时间 | 质量 |
|---|-----|------|------|------|------|
| 1 | <id> | <title> | <tags> | <time> | <score> |

💡 `/mnemosyne:load <ID>` 加载；`/mnemosyne:search <关键词>` 搜索
```

---

## 空列表

```
📭 暂无保存的上下文
使用 `/mnemosyne:save` 保存当前会话上下文
```
