---
description: 清理过期或无用的上下文记录。
argument-hint: [--days N] [--dry-run]
---

# /mnemosyne:clean - 清理上下文

用户输入: $ARGUMENTS

---

## 规则

- `--days N`：删除 N 天前记录（默认 90）
- `--dry-run`：只预览不删除

---

## 流程

1. 扫描索引，计算待清理集合
2. 预览列表（数量 + 预计释放空间）
3. AskUserQuestion 确认（或调整天数）
4. 执行删除并更新 `index.json`

---

## 预览示例

```markdown
## 清理预览

将清理 <days> 天前的上下文记录（共 <N> 条）
| # | ID | 标题 | 时间 |
|---|-----|------|------|
| 1 | <id> | <title> | <date> |

确认清理吗？
```

---

## 输出示例

```
清理完成：已删除 <N> 个过期上下文，释放 <X> MB
```
