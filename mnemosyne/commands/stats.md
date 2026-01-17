---
description: 显示上下文存储的统计信息。
argument-hint:
---

# /mnemosyne:stats - 统计信息

---

## 流程

1. 读取 `.claude/mnemosyne/index.json`
2. 统计：总数量、标签分布、时间分布、质量分布、存储占用

---

## 输出示例

```markdown
## Mnemosyne 统计

### 概览
| 指标 | 值 |
|------|------|
| 总上下文数 | <N> |
| 存储位置 | .claude/mnemosyne/ |
| 占用空间 | <X> MB |
| 最新记录 | <YYYY-MM-DD> |

### 标签分布
| 标签 | 数量 |
|------|------|
| <tag> | <n> |

### 质量评分
| 评分 | 数量 |
|------|------|
| <score> | <n> |
```

---

## 空数据

```
暂无保存的上下文
使用 `/mnemosyne:save` 开始保存会话上下文
```
