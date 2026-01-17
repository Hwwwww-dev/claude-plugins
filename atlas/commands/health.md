---
description: 项目健康检查命令。一键诊断项目健康度，整合代码质量、安全漏洞、依赖状态、架构评估，输出综合健康评分和改进建议。
argument-hint: [--scope path] [--quick] [--export json|html] [--ci]
---

# /health - 项目健康检查

用户输入: $ARGUMENTS

---

## 第一步:分阶段确认检查选项

**如果用户已指定完整选项(如 `/health --quick --scope src/ --export json`),跳过所有询问。**

**第一个 AskUserQuestion: 执行模式选择**

```
问题: 执行模式
- 自动模式(推荐): 使用推荐配置,完整检查整个项目
- 交互模式: 自定义检查范围和详细配置
```

**第二个 AskUserQuestion: 检查配置(仅交互模式)**

如果用户选择了**交互模式**,询问详细配置:

```
问题1: 检查模式
- full (默认): 完整检查(5个维度)
- quick: 快速检查(仅安全性和代码质量)
- security: 仅安全检查
- quality: 仅代码质量检查

问题2: 检查范围
- all (默认): 整个项目
- scope: 指定目录/模块

问题3: 导出格式
- markdown (默认): Markdown 报告
- json: JSON 格式(适合 CI)
- html: HTML 可视化报告

问题4: 报告详细度
- full (默认): 包含所有问题详情
- summary: 仅摘要和关键问题
- minimal: 仅评分和统计

问题5: CI 模式
- no (默认): 正常模式
- yes: CI 模式(包含阈值检查)
```

**自动模式行为**(跳过第二个 AskUserQuestion):
- 默认值：`mode=full`、`scope=all`、`export=markdown`、`detail=full`、`ci=no`
---

## 第二步：环境检测（P0）

**检测必要工具是否可用：**

```bash
# 检查 git 仓库
git rev-parse --is-inside-work-tree 2>/dev/null

# 检查 package.json（Node.js 项目）
test -f package.json

# 检查常用安全工具
command -v npm audit 2>/dev/null
command -v yarn audit 2>/dev/null
```

**输出环境信息：**
```markdown
🔍 环境检测
- Git 仓库: ✓
- 项目类型: Node.js
- 包管理器: npm/yarn
- 可用工具: npm audit, eslint
```

---

## 第三步：并行扫描（P1）

**根据检查模式选择扫描维度：**

### Full 模式（5个维度）

**同时启动 4 个 subagent 并行扫描：**

#### Subagent 1: 安全扫描
```
Task(subagent_type="atlas:code-reviewer")
prompt: |
  任务 ID: health-security-<timestamp>
  检查类型: security
  范围: <scope>（deep）
  检查要点: 依赖漏洞（npm/yarn audit）+ 硬编码密钥/敏感配置
  写入: .claude/health/.scan/security-<timestamp>.json
  格式:
  {
    "dimension": "security",
    "score": 0-100,
    "weight": 0.30,
    "issues": [
      {
        "severity": "critical|high|medium|low",
        "type": "dependency|hardcoded-secret|config",
        "description": "问题描述",
        "location": "文件路径:行号",
        "recommendation": "修复建议"
      }
    ],
    "summary": "简要说明"
  }
```

#### Subagent 2: 代码质量扫描
```
Task(subagent_type="atlas:information-gatherer", model="haiku")
prompt: |
  任务 ID: health-quality-<timestamp>
  检查类型: code-quality
  范围: <scope>（.js/.ts/.jsx/.tsx）
  检查要点: 嵌套>3/函数>100行/文件>500行；coverage（如有）；TODO/console/注释代码
  写入: .claude/health/.scan/quality-<timestamp>.json
  格式同上，score 和 weight(0.25)
```

#### Subagent 3: 依赖健康扫描
```
Task(subagent_type="atlas:dependency-analyzer")
prompt: |
  任务 ID: health-dependencies-<timestamp>
  检查类型: dependency-health
  检查要点: outdated（major/minor/patch）；冲突/重复依赖；体积/大型依赖（>5MB）
  写入: .claude/health/.scan/dependencies-<timestamp>.json
  格式同上，score 和 weight(0.20)
```

#### Subagent 4: 架构质量扫描
```
Task(subagent_type="atlas:code-reviewer")
prompt: |
  任务 ID: health-architecture-<timestamp>
  检查类型: architecture
  检查要点: 循环依赖；高耦合模块（引用>20）；目录结构是否符合约定
  写入: .claude/health/.scan/architecture-<timestamp>.json
  格式同上，score 和 weight(0.15)
```

#### 可维护性检查（主对话执行）
```
主进程快速检查: 文档覆盖（README/API docs）/ 命名规范 / 注释比例
输出: .claude/health/.scan/maintainability-<timestamp>.json（weight 0.10）
```

### Quick 模式（2个维度）

**仅执行 Subagent 1 和 2（安全扫描和代码质量）**

### Security/Quality 模式（单维度）

**仅执行对应的 subagent**

---

## 第四步：评分计算（P2）

**等待所有扫描完成后，读取所有 JSON 文件：**

```bash
cat .claude/health/.scan/security-<timestamp>.json
cat .claude/health/.scan/quality-<timestamp>.json
cat .claude/health/.scan/dependencies-<timestamp>.json
cat .claude/health/.scan/architecture-<timestamp>.json
cat .claude/health/.scan/maintainability-<timestamp>.json
```

**计算综合评分：**

```
总分 = Σ (维度分数 × 维度权重)

示例:
security: 75 × 0.30 = 22.5
quality: 80 × 0.25 = 20.0
dependencies: 70 × 0.20 = 14.0
architecture: 85 × 0.15 = 12.75
maintainability: 90 × 0.10 = 9.0
-------------------------------
总分 = 78.25 ≈ 78 (B 级)
```

**评级映射：**

| 分数 | 等级 | 状态 | 说明 |
|------|------|------|------|
| 90-100 | A | 🟢 优秀 | 生产就绪，无重大问题 |
| 80-89 | B | 🟢 良好 | 可部署，有少量改进空间 |
| 70-79 | C | 🟡 一般 | 需要优化，存在中等问题 |
| 60-69 | D | 🟠 较差 | 不建议部署，问题较多 |
| <60 | F | 🔴 危险 | 禁止部署，严重问题 |

---

## 第五步：报告生成（P3）

**创建报告目录：**
```bash
mkdir -p .claude/health/
```

### Markdown 格式（默认）

**写入文件：** `.claude/health/report-<timestamp>.md`

**报告结构：**
```markdown
# 项目健康检查报告

**检查时间**: <ISO-8601>
**检查模式**: <full|quick|security|quality>
**检查范围**: <scope>

## 综合评分
**分数**: <0-100> | **等级**: <A|B|C|D|F> | **状态**: <good|warning|bad|fail>

## 维度评分
| 维度 | 分数 | 权重 | 贡献 | 状态 |
|------|------|------|------|------|
| ... | ... | ... | ... | ... |

## 关键问题
- Critical: X | High: Y | Medium: Z | Low: N

## 改进建议（按优先级）
- 高优先级: critical/high
- 中优先级: 质量/架构/依赖
- 低优先级: 覆盖率/文档/清理

*生成于 <ISO-8601>*
```

### JSON 格式（CI 模式）

**写入文件：** `.claude/health/report-<timestamp>.json`

```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "mode": "full",
  "scope": ".",
  "summary": {"score": 78, "grade": "B", "status": "good", "passCI": true},
  "dimensions": [{"name": "security", "score": 75, "weight": 0.3, "contribution": 22.5, "status": "warning", "issues": {"critical": 1, "high": 2, "medium": 5, "low": 3}}],
  "issues": [{"dimension": "security", "severity": "critical", "type": "dependency", "description": "lodash 依赖存在 CVE-2023-12345 原型污染漏洞", "location": "package.json:23", "recommendation": "升级至 4.17.21 或更高版本"}],
  "recommendations": [{"priority": "high", "category": "security", "action": "升级 lodash 至 4.17.21+", "impact": "修复 Critical 安全漏洞", "effort": "low"}],
  "ci": {"threshold": 70, "pass": true, "blockers": []}
}
```
> `dimensions/issues/recommendations` 为数组，元素结构同上例；必须覆盖所有维度/问题/建议。

### HTML 格式

**写入文件：** `.claude/health/report-<timestamp>.html`

**包含：**
- 可视化评分仪表盘
- 交互式问题过滤器
- 趋势图表（如有历史数据）
- 导出按钮（PDF/PNG）

---

## 第六步：CI 检查（仅 --ci 模式）

**如果指定了 `--ci` 选项：**

```bash
# 读取 JSON 报告
report=.claude/health/report-<timestamp>.json

# 检查阈值
score=$(jq '.summary.score' $report)
critical=$(jq '[.issues[] | select(.severity=="critical")] | length' $report)
high=$(jq '[.issues[] | select(.severity=="high")] | length' $report)

# CI 阈值（可配置）
MIN_SCORE=70
MAX_CRITICAL=0
MAX_HIGH=3

# 判断是否通过
if [ $score -lt $MIN_SCORE ]; then
  echo "❌ CI 失败: 评分 $score < $MIN_SCORE"
  exit 1
fi

if [ $critical -gt $MAX_CRITICAL ]; then
  echo "❌ CI 失败: 存在 $critical 个 Critical 问题"
  exit 1
fi

if [ $high -gt $MAX_HIGH ]; then
  echo "⚠️ CI 警告: 存在 $high 个 High 问题 (阈值: $MAX_HIGH)"
fi

echo "✅ CI 通过: 健康度检查合格"
```

**CI 输出：**
```markdown
🏥 项目健康检查 CI

✅ 评分: 78 ≥ 70 (通过)
✅ Critical 问题: 0 个 (通过)
⚠️ High 问题: 5 个 (超出阈值 3，警告)

状态: PASS (允许合并，建议修复 High 问题)
```

**如果未通过：**
```markdown
🏥 项目健康检查 CI

❌ 评分: 58 < 70 (失败)
❌ Critical 问题: 2 个 (失败)
❌ High 问题: 12 个 (失败)

Blockers:
1. lodash CVE-2023-12345
2. 硬编码 API 密钥

状态: FAIL (阻止合并)
```

---

## 执行示例

### 示例 1: 完整检查

```
用户: /health

1. 询问选项（如未指定）
2. 环境检测
3. 并行启动 4 个 subagent 扫描（安全/质量/依赖/架构）+ 主对话检查可维护性
4. 等待所有扫描完成
5. 读取 5 个 JSON 结果
6. 计算综合评分: 78/100 (B 级)
7. 生成 Markdown 报告: .claude/health/report-20240115-143000.md
8. 输出摘要 + 报告路径
```

### 示例 2: Quick 模式

```
用户: /health --quick

1. 跳过询问
2. 环境检测
3. 并行启动 2 个 subagent（安全/质量）
4. 计算评分（仅这两个维度）
5. 生成简化报告
```

### 示例 3: CI 模式

```
用户: /health --ci --export json

1. 环境检测
2. 完整扫描（5个维度）
3. 生成 JSON 报告
4. 执行 CI 阈值检查
5. 输出 PASS/FAIL + 具体原因
```

---

## 输出格式

**固定输出结构：**

```markdown
🏥 项目健康检查完成

## 综合评分
**分数**: <0-100> | **等级**: <A-F> | **状态**: <good|warning|bad|fail>

## 维度分布
- security/quality/dependencies/architecture/maintainability: <score>/<100>

## 关键问题
- Critical/High/Medium/Low: <count>

📊 **完整报告**: `.claude/health/report-<timestamp>.(md|json|html)`

## 下一步
1. <建议1>
```

---

## 历史趋势（可选）

**如果存在历史报告，显示趋势：**

```markdown
## 健康趋势

| 日期 | 评分 | 等级 | 变化 |
|------|------|------|------|
| <YYYY-MM-DD> | <0-100> | <A-F> | <+/-N> |

**改进方向**: 安全性 +10, 代码质量 +5
**待改进**: 依赖健康 -3
```

---

## 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| --scope | 检查范围（目录路径） | . | --scope src/ |
| --quick | 快速模式（仅安全和质量） | false | --quick |
| --export | 导出格式 | markdown | --export json |
| --ci | CI 模式（包含阈值检查） | false | --ci |

---

## 配置文件（可选）

**支持自定义配置：** `.claude/health/config.json`

```json
{
  "thresholds": {"minScore": 70, "maxCritical": 0, "maxHigh": 3},
  "weights": {"security": 0.3, "quality": 0.25, "dependencies": 0.2, "architecture": 0.15, "maintainability": 0.1},
  "ignore": {"patterns": ["**/node_modules/**", "**/dist/**"], "rules": ["console-log", "todo-comments"]}
}
```

---

## 核心约束

**必须做**:
- 并行扫描多个维度（除非 quick/单维度模式）
- 使用固定的 JSON 输出格式（便于 CI 解析）
- 提供具体的文件路径和行号
- 给出可操作的修复建议
- 保存历史报告（支持趋势分析）

**禁止做**:
- 自己修复问题（仅诊断，不修改代码）
- 串行扫描（影响效率）
- 输出不完整的报告（必须包含所有维度）
- 忽略 CI 阈值检查（--ci 模式下必须执行）

---

## 与其他命令配合

```bash
# 工作流示例
/health                                # 1. 诊断项目健康度
/gather dependencies <package>         # 2. 分析问题依赖的影响范围
/orchestrate 升级所有 <package> 引用    # 3. 批量修复
/health --quick                        # 4. 验证修复效果
```

---

## 分段输出规范

**触发条件**（满足任一即分段）:
- 单次输出超过 800 字符
- 列表超过 15 项
- 代码块超过 30 行

### 输出前确认

确认输出的报告包含：
- [ ] 健康评分
- [ ] 各维度分析结果
- [ ] 问题列表
- [ ] 改进建议

---

## 注意事项

- 首次运行可能较慢（5-10分钟），后续检查会更快
- CI 模式建议在每次 PR 合并前执行
- 历史报告保留 30 天（可配置）
- 大型项目（>10万行）建议使用 --quick 模式
