---
description: 搜索历史会话上下文。支持标题、标签、内容、时间多维度搜索。
argument-hint: <关键词> [--tag tag] [--from date] [--to date]
---

# /mnemosyne:search - 搜索上下文

用户输入: $ARGUMENTS

---

## 维度

- 标题（title）
- 标签（`--tag`）
- 内容（全文）
- 时间范围（`--from/--to`）

---

## 流程

1. 解析参数（关键词 + 过滤条件）
2. 读取索引：`.claude/mnemosyne/index.json`
3. 过滤：tag → time → keyword（标题优先）
4. 排序：相关度 + 时间

---

## 输出示例

```markdown
## 搜索结果: "<关键词>" (共 <N> 条)

### 1. <标题>
- ID: <id>
- 标签: <tags>
- 时间: <time>
- 匹配: <title|content>

使用 `/mnemosyne:load <ID>` 加载指定上下文
```

---

## 无结果

```
未找到匹配的上下文
尝试：更换关键词 / 移除过滤 / 扩大时间范围
```
