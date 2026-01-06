---
description: 项目健康检查命令。一键诊断项目健康度，整合代码质量、安全漏洞、依赖状态、架构评估，输出综合健康评分和改进建议。
argument-hint: [--scope path] [--quick] [--export json|html] [--ci]
---

# /health - 项目健康检查

用户输入: $ARGUMENTS

---

## 第一步：确认检查选项

**如果用户未指定选项，使用 AskUserQuestion 询问：**

```
问题1: 检查模式
- full (默认): 完整检查（5个维度）
- quick: 快速检查（仅安全性和代码质量）
- security: 仅安全检查
- quality: 仅代码质量检查

问题2: 检查范围
- all: 整个项目
- scope: 指定目录/模块

问题3: 导出格式
- markdown (默认): Markdown 报告
- json: JSON 格式（适合 CI）
- html: HTML 可视化报告

问题4: CI 模式
- no (默认): 正常模式
- yes: CI 模式（包含阈值检查）
```

**如果用户已指定（如 `/health --quick --scope src/`），跳过询问。**

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
  ## 任务
  任务 ID: health-security-<timestamp>
  检查类型: security

  ## 范围
  - 路径: <scope>
  - 深度: deep

  ## 检查项
  1. 依赖漏洞检测:
     - 运行: npm audit / yarn audit
     - 检测: package.json 中的高危依赖
     - 评估: CVE 漏洞等级

  2. 硬编码密钥扫描:
     - 搜索模式: API_KEY, SECRET, PASSWORD, TOKEN
     - 检测: .env 文件泄露
     - 检查: 配置文件中的敏感信息

  ## 输出
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
  ## 任务
  任务 ID: health-quality-<timestamp>
  检查类型: code-quality

  ## 范围
  - 路径: <scope>
  - 文件类型: .js, .ts, .jsx, .tsx

  ## 检查项
  1. 代码复杂度:
     - 循环嵌套深度 > 3
     - 函数行数 > 100
     - 文件行数 > 500

  2. 代码覆盖率（如有 coverage/ 目录）:
     - 读取: coverage/coverage-summary.json
     - 提取: line/branch/function coverage

  3. 问题模式:
     - TODO/FIXME 数量
     - console.log 残留
     - 注释掉的代码块

  ## 输出
  写入: .claude/health/.scan/quality-<timestamp>.json
  格式同上，score 和 weight(0.25)
```

#### Subagent 3: 依赖健康扫描
```
Task(subagent_type="atlas:dependency-analyzer")
prompt: |
  ## 任务
  任务 ID: health-dependencies-<timestamp>
  检查类型: dependency-health

  ## 检查项
  1. 过期依赖:
     - 运行: npm outdated / yarn outdated
     - 统计: major/minor/patch outdated

  2. 依赖冲突:
     - 检测: package-lock.json 中的重复依赖
     - 评估: 版本不一致问题

  3. 依赖体积:
     - 统计: dependencies 数量
     - 分析: 大型依赖（>5MB）

  ## 输出
  写入: .claude/health/.scan/dependencies-<timestamp>.json
  格式同上，score 和 weight(0.20)
```

#### Subagent 4: 架构质量扫描
```
Task(subagent_type="atlas:code-reviewer")
prompt: |
  ## 任务
  任务 ID: health-architecture-<timestamp>
  检查类型: architecture

  ## 检查项
  1. 循环依赖:
     - 分析: import 关系图
     - 检测: 循环引用路径

  2. 模块耦合:
     - 统计: 跨模块引用数量
     - 评估: 高耦合模块（被引用 >20 次）

  3. 目录结构:
     - 检查: 是否遵循约定目录结构
     - 评估: 平坦化 vs 嵌套深度

  ## 输出
  写入: .claude/health/.scan/architecture-<timestamp>.json
  格式同上，score 和 weight(0.15)
```

#### 可维护性检查（主对话执行）
```
直接在主对话中快速检查:
1. 文档覆盖:
   - 统计: README.md, API docs 存在性
   - 检查: 核心模块是否有文档
2. 命名规范:
   - 搜索: 拼音命名、无意义变量名
3. 注释质量:
   - 统计: 注释行数 / 代码行数

输出: .claude/health/.scan/maintainability-<timestamp>.json
权重: 0.10
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

**检查时间**: 2024-01-15 14:30:00
**检查模式**: full
**检查范围**: 整个项目

---

## 综合评分

### 总评
**分数**: 78 / 100
**等级**: B (良好)
**状态**: 🟢 可部署

### 维度评分

| 维度 | 分数 | 权重 | 贡献 | 状态 |
|------|------|------|------|------|
| 🔒 安全性 | 75 | 30% | 22.5 | 🟡 一般 |
| ⚙️ 代码质量 | 80 | 25% | 20.0 | 🟢 良好 |
| 📦 依赖健康 | 70 | 20% | 14.0 | 🟡 一般 |
| 🏗️ 架构质量 | 85 | 15% | 12.75 | 🟢 良好 |
| 🔧 可维护性 | 90 | 10% | 9.0 | 🟢 优秀 |

---

## 详细问题

### 🔒 安全性 (75/100)

#### ⚠️ Critical (1)
- **CVE-2023-12345**: lodash 依赖存在原型污染漏洞
  - 位置: package.json:23
  - 建议: 升级至 4.17.21 或更高版本

#### ⚠️ High (2)
- **硬编码密钥**: API_KEY 暴露在源码中
  - 位置: src/config/api.ts:15
  - 建议: 迁移至环境变量 (.env)

- **依赖漏洞**: axios 版本过低
  - 位置: package.json:45
  - 建议: 升级至 1.6.0+

#### ℹ️ Medium (5)
- TODO 注释中包含敏感信息
- .env.example 缺失
- ...

---

### ⚙️ 代码质量 (80/100)

#### ⚠️ High (3)
- **复杂度过高**: UserService.handleRequest 圈复杂度为 25
  - 位置: src/services/user.ts:120-185
  - 建议: 拆分为多个小函数

- **文件过大**: components/Dashboard.tsx 达 850 行
  - 位置: src/components/Dashboard.tsx
  - 建议: 拆分为多个子组件

#### ℹ️ Medium (8)
- 12 处 console.log 残留
- 45 处 TODO/FIXME 注释
- 测试覆盖率仅 65%（建议 ≥80%）
- ...

---

### 📦 依赖健康 (70/100)

#### ⚠️ High (4)
- **Major 版本过期**: react 16.x (最新 18.x)
- **Major 版本过期**: webpack 4.x (最新 5.x)
- **体积过大**: moment.js (289KB，建议替换为 date-fns)
- **重复依赖**: lodash 出现 3 个版本 (4.17.19, 4.17.20, 4.17.21)

#### ℹ️ Medium (12)
- 23 个 minor 版本过期
- 45 个 patch 版本过期
- ...

---

### 🏗️ 架构质量 (85/100)

#### ⚠️ Medium (2)
- **循环依赖**: utils/helpers.ts ↔ services/user.ts
  - 路径: helpers → user → api → helpers
  - 建议: 提取公共逻辑至独立模块

- **高耦合**: AuthService 被 18 个模块引用
  - 建议: 考虑依赖注入或接口抽象

#### ℹ️ Low (5)
- components/ 目录嵌套深度达 5 层
- 部分模块缺少 index.ts 导出
- ...

---

### 🔧 可维护性 (90/100)

#### ✅ 良好
- README.md 完善
- 核心模块有文档覆盖
- 命名规范基本一致

#### ℹ️ Low (3)
- API 文档不完整（7/12 端点缺少说明）
- 3 处拼音命名（如 yonghu, denglu）
- 部分注释已过时
- ...

---

## 改进建议

### 🎯 高优先级（2周内）
1. **安全修复**:
   - 升级 lodash 至 4.17.21+
   - 迁移硬编码密钥至环境变量
   - 升级 axios 至最新版本

2. **代码重构**:
   - 简化 UserService.handleRequest 复杂度
   - 拆分 Dashboard.tsx 为子组件

3. **依赖升级**:
   - 升级 React 至 18.x（评估兼容性）
   - 替换 moment.js 为 date-fns（减少 220KB）

### 📌 中优先级（1-2月）
4. **测试覆盖**:
   - 提升测试覆盖率至 80%+
   - 关键业务逻辑添加单元测试

5. **架构优化**:
   - 解决循环依赖问题
   - 重构高耦合模块（AuthService）

6. **依赖清理**:
   - 统一 lodash 版本
   - 清理未使用的依赖（运行 depcheck）

### 💡 低优先级（持续改进）
7. **代码清理**:
   - 移除 console.log 和调试代码
   - 清理过时注释
   - 修正拼音命名

8. **文档完善**:
   - 补充 API 文档
   - 更新过时文档

---

## CI 集成

**阈值设置**（建议）:
- 最低评分: 70 (C 级)
- Critical 问题: 0 个
- High 问题: ≤3 个

**CI 命令**:
```bash
/health --ci --export json

# 或通过脚本检查
node scripts/check-health.js
```

**失败处理**: 评分低于阈值时 CI 失败，阻止合并

---

## 下一步行动

1. **立即执行**: 修复 1 个 Critical 安全问题
2. **本周计划**: 处理 2 个 High 级代码质量问题
3. **本月目标**: 升级主要依赖，解决循环依赖
4. **持续改进**: 定期执行 `/health` 检查（建议每周一次）

---

**报告生成时间**: 2024-01-15 14:30:15
**下次检查建议**: 2024-01-22 (7天后)

**快速修复命令**:
```bash
# 升级依赖
npm update lodash axios

# 代码清理
/orchestrate 移除所有 console.log

# 测试覆盖
npm run test:coverage
```
```

### JSON 格式（CI 模式）

**写入文件：** `.claude/health/report-<timestamp>.json`

```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "mode": "full",
  "scope": ".",
  "summary": {
    "score": 78,
    "grade": "B",
    "status": "good",
    "passCI": true
  },
  "dimensions": [
    {
      "name": "security",
      "score": 75,
      "weight": 0.30,
      "contribution": 22.5,
      "status": "warning",
      "issues": {
        "critical": 1,
        "high": 2,
        "medium": 5,
        "low": 3
      }
    },
    {
      "name": "quality",
      "score": 80,
      "weight": 0.25,
      "contribution": 20.0,
      "status": "good",
      "issues": {
        "critical": 0,
        "high": 3,
        "medium": 8,
        "low": 12
      }
    }
    // ... 其他维度
  ],
  "issues": [
    {
      "dimension": "security",
      "severity": "critical",
      "type": "dependency",
      "description": "lodash 依赖存在 CVE-2023-12345 原型污染漏洞",
      "location": "package.json:23",
      "recommendation": "升级至 4.17.21 或更高版本"
    }
    // ... 所有问题
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "security",
      "action": "升级 lodash 至 4.17.21+",
      "impact": "修复 Critical 安全漏洞",
      "effort": "low"
    }
    // ... 所有建议
  ],
  "ci": {
    "threshold": 70,
    "pass": true,
    "blockers": []
  }
}
```

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
**分数**: 78 / 100
**等级**: B (良好)
**状态**: 🟢 可部署

## 维度分布
- 🔒 安全性: 75/100 (🟡 一般)
- ⚙️ 代码质量: 80/100 (🟢 良好)
- 📦 依赖健康: 70/100 (🟡 一般)
- 🏗️ 架构质量: 85/100 (🟢 良好)
- 🔧 可维护性: 90/100 (🟢 优秀)

## 关键问题
- ⚠️ Critical: 1 个
- ⚠️ High: 7 个
- ℹ️ Medium: 28 个

📊 **完整报告**: .claude/health/report-20240115-143000.md

## 下一步
1. 立即修复: 1 个 Critical 安全问题
2. 本周计划: 处理 2 个 High 级代码质量问题
3. 本月目标: 升级主要依赖

🔄 **建议检查频率**: 每周一次
```

---

## 历史趋势（可选）

**如果存在历史报告，显示趋势：**

```markdown
## 健康趋势

| 日期 | 评分 | 等级 | 变化 |
|------|------|------|------|
| 2024-01-15 | 78 | B | +5 ⬆️ |
| 2024-01-08 | 73 | C | -2 ⬇️ |
| 2024-01-01 | 75 | C | — |

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
  "thresholds": {
    "minScore": 70,
    "maxCritical": 0,
    "maxHigh": 3
  },
  "weights": {
    "security": 0.30,
    "quality": 0.25,
    "dependencies": 0.20,
    "architecture": 0.15,
    "maintainability": 0.10
  },
  "ignore": {
    "patterns": ["**/node_modules/**", "**/dist/**"],
    "rules": ["console-log", "todo-comments"]
  }
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
