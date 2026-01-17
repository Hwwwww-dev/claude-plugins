---
description: 加载历史上下文。在新会话中快速恢复项目背景和进度。
argument-hint: [id] [--latest]
---

# /mnemosyne:load - 加载上下文

用户输入: $ARGUMENTS

---

## 流程

1. 读取索引：`.claude/mnemosyne/index.json`
2. 选择目标：
   - 指定 ID：`/mnemosyne:load <id>`
   - 最近一次：`/mnemosyne:load --latest`
   - 否则：AskUserQuestion 列表选择
3. 读取上下文：`.claude/mnemosyne/<folder>/context.md`
4. 输出摘要：标题/保存时间/一句话摘要/完成度/下一步（让用户能直接继续）

---

## 输出示例

```markdown
## 📥 已加载上下文

**标题**: <title>
**保存时间**: <YYYY-MM-DD HH:mm>

### 🎯 需求摘要
<summary>

### ✅ 当前进度
- [x] ...
- [ ] ...

### 🚀 续作指引
<next steps>
```
