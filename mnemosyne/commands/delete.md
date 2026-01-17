---
description: 删除指定的上下文记录。需要确认后执行。
argument-hint: <id> [--force]
---

# /mnemosyne:delete - 删除上下文

用户输入: $ARGUMENTS

---

## 流程

1. 验证 ID 是否存在（索引 + 目录）
2. 展示待删除记录概要
3. AskUserQuestion 确认（`--force` 可跳过）
4. 删除目录并更新 `index.json`

---

## 确认示例

```markdown
## 删除确认

**标题**: <title>
**ID**: <id>
**标签**: <tags>
**保存时间**: <time>

此操作不可恢复，确认删除吗？
```

---

## 输出示例

```
已删除: <title> (<id>)
```

```
已取消删除操作
```
