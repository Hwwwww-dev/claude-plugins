---
description: 测试生成命令。分析代码逻辑，自动生成单元测试和集成测试，支持多种测试框架。
argument-hint: [--scope path] [--framework jest|vitest|pytest|go] [--type unit|integration] [--coverage-target N]
---

# 测试生成命令

分析代码逻辑和边界条件，自动生成高质量的测试用例。

## 参数

| 参数 | 说明 | 默认值 |
|:-----|:-----|:-------|
| `--scope` | 生成范围 | . (全项目) |
| `--framework` | 测试框架 | 自动检测 |
| `--type` | 测试类型 | unit |
| `--coverage-target` | 目标覆盖率 | 80 |

---

## 支持的测试框架

| 框架 | 语言 | 检测方式 |
|:-----|:-----|:---------|
| Jest | JavaScript/TypeScript | package.json 依赖 |
| Vitest | JavaScript/TypeScript | vite.config / vitest.config |
| Mocha | JavaScript/TypeScript | package.json 依赖 |
| Pytest | Python | pytest.ini / pyproject.toml |
| Go Test | Go | go.mod 存在 |
| JUnit | Java | pom.xml / build.gradle |

---

## 执行流程

Phase 0 环境检测 → Phase 1 目标分析 → Phase 2 用例规划 → Phase 3 测试生成 → Phase 4 验证

### Subagent 分配

| Phase | 功能 | Subagent | 说明 |
|:------|:-----|:---------|:-----|
| 0 | 环境检测 | 主进程 | 检测测试框架和现有覆盖率 |
| 1 | 目标分析 | `atlas:information-gatherer` | 分析目标代码 |
| 2 | 用例规划 | `Plan` | 规划测试用例 |
| 3 | 测试生成 | `atlas:atlas-executor` | 并行生成测试文件 |
| 4 | 验证 | 主进程 | 运行测试，报告覆盖率 |

---

## Phase 0: 环境检测

**输入**: 命令参数

**输出**: 环境配置

**检测内容**:
1. 测试框架类型
2. 测试文件命名约定
3. 测试目录结构
4. Mock 库（jest-mock, sinon, unittest.mock 等）
5. 现有覆盖率（如果有报告）

**配置示例**:
```json
{
  "framework": "jest",
  "language": "typescript",
  "testDir": "__tests__",
  "testPattern": "*.test.ts",
  "mockLibrary": "jest-mock",
  "currentCoverage": {
    "lines": 65,
    "branches": 58,
    "functions": 70
  }
}
```

---

## 项目知识库

**优先从 `.claude/repowiki/` 获取项目信息**（如果存在）：

| 文件 | 用途 |
|:-----|:-----|
| `.claude/repowiki/.meta/project.pkg.json` | 项目配置、测试框架信息 |
| `.claude/repowiki/.meta/modules.pkg.json` | 模块结构（确定测试范围） |
| `.claude/repowiki/.meta/symbols.pkg.json` | 符号索引（函数签名、参数类型） |
| `.claude/repowiki/.meta/api.pkg.json` | API 端点（用于集成测试） |

**使用方式**：Phase 1 分析前先检查这些文件是否存在，可获取函数签名和依赖信息。

---

## Phase 1: 目标分析

**Subagent**: `atlas:information-gatherer`

**输入**: 范围 + 环境配置 + `.claude/repowiki/` 现有信息（如果存在）

**输出**: `.claude/test-gen/.meta/analysis.pkg.json`

**分析内容**:
1. 公开函数/方法的签名
2. 参数类型和边界值
3. 分支路径（if/switch/try-catch）
4. 依赖项（需要 mock 的服务）
5. 现有测试覆盖情况

**PKG 结构**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "targets": [
    {
      "file": "src/user/user.service.ts",
      "symbol": "UserService",
      "type": "class",
      "methods": [
        {
          "name": "create",
          "signature": "create(data: CreateUserDto): Promise<User>",
          "params": [
            {
              "name": "data",
              "type": "CreateUserDto",
              "required": true,
              "validations": ["@IsEmail() email", "@MinLength(8) password"]
            }
          ],
          "returns": "Promise<User>",
          "branches": [
            {"condition": "email already exists", "outcome": "throw ConflictException"},
            {"condition": "validation fails", "outcome": "throw BadRequestException"},
            {"condition": "success", "outcome": "return User"}
          ],
          "dependencies": ["PrismaService", "HashService"],
          "hasExistingTest": false,
          "complexity": 5
        }
      ],
      "existingTestFile": null
    }
  ],
  "summary": {
    "totalTargets": 15,
    "withTests": 8,
    "withoutTests": 7,
    "estimatedNewTests": 25
  }
}
```

---

## Phase 2: 用例规划

**Subagent**: `Plan`

**输入**: `.claude/test-gen/.meta/analysis.pkg.json`

**输出**: 测试用例规划 + TodoWrite todos

**规划原则**:
1. 每个公开方法至少 1 个正常路径测试
2. 每个参数的边界值测试
3. 每个异常路径的错误处理测试
4. 依赖项的 mock 设置

**用例规划示例**:
```markdown
## 测试用例规划

### UserService.create

#### 正常路径
- [ ] 应该成功创建用户并返回 User 对象
- [ ] 应该正确哈希密码

#### 边界值
- [ ] email 为空字符串时应该抛出 BadRequestException
- [ ] password 长度为 7（边界-1）时应该抛出 BadRequestException
- [ ] password 长度为 8（边界）时应该成功

#### 异常路径
- [ ] email 已存在时应该抛出 ConflictException
- [ ] 数据库错误时应该抛出 InternalServerException

#### Mock 设置
- PrismaService.user.create
- PrismaService.user.findUnique
- HashService.hash
```

---

## Phase 3: 测试生成

**Subagent**: `atlas:atlas-executor` (并行多个)

**输入**: 用例规划 + 环境配置

**输出**: 测试文件

**生成策略**:
1. 按文件分组，每个源文件对应一个测试文件
2. 并行生成各测试文件
3. 遵循项目现有的测试风格

**文件命名规则**:
| 框架 | 源文件 | 测试文件 |
|:-----|:-------|:---------|
| Jest/Vitest | src/user.service.ts | src/user.service.test.ts 或 __tests__/user.service.test.ts |
| Pytest | src/user_service.py | tests/test_user_service.py |
| Go | src/user/service.go | src/user/service_test.go |

**生成模板（Jest/TypeScript）**:
```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { UserService } from './user.service';
import { PrismaService } from '../prisma/prisma.service';
import { HashService } from '../hash/hash.service';
import { ConflictException, BadRequestException } from '@nestjs/common';

describe('UserService', () => {
  let service: UserService;
  let prismaService: jest.Mocked<PrismaService>;
  let hashService: jest.Mocked<HashService>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UserService,
        {
          provide: PrismaService,
          useValue: {
            user: {
              create: jest.fn(),
              findUnique: jest.fn(),
            },
          },
        },
        {
          provide: HashService,
          useValue: {
            hash: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<UserService>(UserService);
    prismaService = module.get(PrismaService);
    hashService = module.get(HashService);
  });

  describe('create', () => {
    const validData = {
      email: 'test@example.com',
      password: 'password123',
    };

    it('should create user successfully', async () => {
      // Arrange
      const hashedPassword = 'hashed_password';
      const expectedUser = { id: '1', email: validData.email };

      hashService.hash.mockResolvedValue(hashedPassword);
      prismaService.user.findUnique.mockResolvedValue(null);
      prismaService.user.create.mockResolvedValue(expectedUser);

      // Act
      const result = await service.create(validData);

      // Assert
      expect(result).toEqual(expectedUser);
      expect(hashService.hash).toHaveBeenCalledWith(validData.password);
      expect(prismaService.user.create).toHaveBeenCalledWith({
        data: { email: validData.email, password: hashedPassword },
      });
    });

    it('should throw ConflictException when email exists', async () => {
      // Arrange
      prismaService.user.findUnique.mockResolvedValue({ id: '1' });

      // Act & Assert
      await expect(service.create(validData)).rejects.toThrow(ConflictException);
    });

    it('should throw BadRequestException when password too short', async () => {
      // Arrange
      const invalidData = { ...validData, password: '1234567' };

      // Act & Assert
      await expect(service.create(invalidData)).rejects.toThrow(BadRequestException);
    });
  });
});
```

**生成模板（Pytest/Python）**:
```python
import pytest
from unittest.mock import Mock, patch
from src.user_service import UserService
from src.exceptions import ConflictError, ValidationError

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def mock_hash_service(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_db, mock_hash_service):
        return UserService(db=mock_db, hash_service=mock_hash_service)

    class TestCreate:
        def test_should_create_user_successfully(self, service, mock_db, mock_hash_service):
            # Arrange
            data = {"email": "test@example.com", "password": "password123"}
            mock_hash_service.hash.return_value = "hashed_password"
            mock_db.find_user_by_email.return_value = None
            expected_user = {"id": "1", "email": data["email"]}
            mock_db.create_user.return_value = expected_user

            # Act
            result = service.create(data)

            # Assert
            assert result == expected_user
            mock_hash_service.hash.assert_called_once_with(data["password"])

        def test_should_raise_conflict_when_email_exists(self, service, mock_db):
            # Arrange
            data = {"email": "existing@example.com", "password": "password123"}
            mock_db.find_user_by_email.return_value = {"id": "1"}

            # Act & Assert
            with pytest.raises(ConflictError):
                service.create(data)

        def test_should_raise_validation_error_when_password_too_short(self, service):
            # Arrange
            data = {"email": "test@example.com", "password": "1234567"}

            # Act & Assert
            with pytest.raises(ValidationError):
                service.create(data)
```

---

## Phase 4: 验证

**执行者**: 主进程

**操作**:
1. 运行生成的测试
2. 收集覆盖率报告
3. 对比目标覆盖率

**验证命令**:
| 框架 | 命令 |
|:-----|:-----|
| Jest | `npx jest --coverage --testPathPattern=<生成的测试>` |
| Vitest | `npx vitest run --coverage <生成的测试>` |
| Pytest | `pytest --cov=src <生成的测试>` |
| Go | `go test -cover ./...` |

**验证报告**:
```markdown
## 测试验证

### 执行结果
- ✅ 测试通过: 25/25
- ⏱️ 执行时间: 3.2s

### 覆盖率变化
| 指标 | 之前 | 之后 | 变化 |
|:-----|:-----|:-----|:-----|
| 行覆盖 | 65% | 82% | +17% |
| 分支覆盖 | 58% | 75% | +17% |
| 函数覆盖 | 70% | 88% | +18% |

### 目标达成
- 目标: 80%
- 当前: 82%
- ✅ 已达成

### 未覆盖代码
- src/order/order.service.ts:45-60 (边缘情况)
- src/auth/auth.guard.ts:30-35 (异常处理)
```

---

## 约束

**生成约束**:
- 只为公开方法/函数生成测试
- 不修改现有测试（除非明确要求）
- 遵循项目现有测试风格
- 使用项目已有的 mock 库

**质量约束**:
- 每个测试必须有 Arrange-Act-Assert 结构
- 测试命名必须描述预期行为
- Mock 设置必须合理（不过度 mock）
- 边界值测试必须覆盖关键边界

**执行约束**:
- Phase 1 必须使用 information-gatherer
- Phase 2 必须使用 Plan agent
- Phase 3 必须使用 atlas-executor

---

## 示例

### 基础用法
```bash
# 为全项目生成测试
/atlas:test-gen

# 指定范围
/atlas:test-gen --scope src/services

# 指定框架
/atlas:test-gen --framework vitest

# 生成集成测试
/atlas:test-gen --type integration

# 设置覆盖率目标
/atlas:test-gen --coverage-target 90
```

### 输出示例

**生成完成**:
```
✅ 测试生成完成

生成统计:
- 新增测试文件: 5
- 新增测试用例: 25
- 覆盖方法: 15

测试文件:
- __tests__/user.service.test.ts (8 用例)
- __tests__/order.service.test.ts (6 用例)
- __tests__/auth.service.test.ts (5 用例)
- __tests__/payment.service.test.ts (4 用例)
- __tests__/notification.service.test.ts (2 用例)

覆盖率变化:
- 行覆盖: 65% → 82% (+17%)
- 目标 80% ✅ 已达成

建议:
1. 检查生成的测试是否符合业务逻辑
2. 考虑添加更多边界情况测试
3. 运行 `npm test` 确保所有测试通过
```

**部分失败**:
```
⚠️ 测试生成部分完成

生成统计:
- 新增测试文件: 5
- 新增测试用例: 25
- 失败用例: 3

失败详情:
1. user.service.test.ts:45 - TypeError: Cannot read property 'create' of undefined
   建议: 检查 PrismaService mock 配置

2. order.service.test.ts:78 - Expected ConflictException but got InternalServerError
   建议: 检查异常处理逻辑

覆盖率: 75% (未达目标 80%)

建议:
1. 修复失败的测试用例
2. 添加缺失场景的测试
```
