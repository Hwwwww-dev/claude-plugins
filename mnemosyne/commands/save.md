---
description: Save current session context. Intelligently extract requirements, decisions, code changes, progress, and other key information.
argument-hint: [title] [--tags tag1,tag2]
---

# /mnemosyne:save - Save Context

User input: $ARGUMENTS

> **Core Principle**: Record the session like writing a work log, enabling your future self (or Claude) to quickly understand and continue the work

---

## Step 1: User Confirmation

**Before performing any extraction work, confirm the save intent with the user:**

### 1.1 Quick Preview of Current Session

Briefly analyze the conversation content and generate a preliminary summary (no deep extraction):
- Scan the user's first message to extract core intent keywords
- Roughly count conversation turns and tool invocations
- Identify main files or modules involved

### 1.2 Ask User Using AskUserQuestion

```markdown
## 📝 Save Context Confirmation

**Session Summary**: [Quickly identified core content]
**Estimated Scale**: About [X] conversation turns, [Y] file changes

Please confirm save information:
```

**Options**:
- **Title**: [Auto-suggested] / User-defined
- **Tags**: [Auto-suggested tags] / User-defined
- **Action**: Confirm save / Modify info / Cancel

**If the user chooses to cancel, end immediately without executing subsequent steps.**

---

## Step 2: Create Memory Directory

**Execute only after user confirmation:**

### 2.1 Check and Create Directory Structure

```
.claude/mnemosyne/
├── index.json                    # Index file (create if not exists)
└── <YYYYMMDD-HHMMSS>-<title>/    # Context directory for this session
    ├── context.md               # Main context file
    ├── snippets/                # Code snippets directory (optional)
    └── attachments/             # Attachments directory (optional)
```

### 2.2 Update Index File

Add new record metadata to `index.json`.

---

## Step 3: Intelligent Information Extraction

**Traverse the entire conversation history and extract information according to the following rules:**

### 3.1 Starting Point: User Intent

**Extraction Rules**:
- Find the user's **first message**, which usually contains the core intent
- Identify key verbs: "implement", "fix", "add", "optimize", "refactor", "analyze", "configure"
- Extract target objects: feature names, module names, file names, error descriptions
- Record any constraints: "don't modify X", "must be compatible with Y", "performance requirement Z"

**Extraction Example**:
```
User message: "Help me add a remember password feature to the login page, use localStorage, don't use cookies"

Extraction result:
- Action: Add feature
- Target: Login page - Remember password
- Technical constraints: Use localStorage, no cookies
```

### 3.2 Process: Key Decisions

**Extraction Rules**:
- Search for **decision moments** in the conversation:
  - Claude provides multiple options for user to choose
  - User explicitly states "use A not B"
  - Technical solutions determined after discussion
- Record **three elements of decision**:
  - Decision point: What issue was decided on
  - Choice: What was finally chosen
  - Reason: Why this choice (stated by user or inferred)

**Recognition Patterns**:
```
Pattern 1: "I suggest using X because..." + User agrees
Pattern 2: "Do you want A or B?" + User chooses
Pattern 3: User directly says "use solution X"
Pattern 4: After discussion says "let's go with this"
```

### 3.3 Output: Code Changes

**Extraction Rules**:
- Scan all **Write/Edit tool invocations**, record:
  - File path (convert absolute path to relative path)
  - Operation type: Create / Modify / Delete
  - Change summary: What was changed (not complete code)
- Scan **Bash tool invocations**, identify:
  - Installed dependencies: `npm install`, `pip install`
  - Build executions: `npm run build`, `cargo build`
  - Test runs: `npm test`, `pytest`

**Output Format**:
```
New files:
  - src/hooks/useRememberMe.ts (Remember password Hook)
  - src/utils/storage.ts (localStorage wrapper)

Modified files:
  - src/pages/Login.tsx (Integrate remember password feature)
  - src/types/auth.ts (Add RememberMeOptions type)

Dependency changes:
  - No new dependencies

Executed commands:
  - npm run dev (Start dev server)
  - npm test (Run tests, all passed)
```

### 3.4 Status: Task Progress

**Extraction Rules**:
- Identify **completion markers**:
  - Claude says "completed", "done", "implemented"
  - Test passed output
  - User confirms "looks good", "no problem"
- Identify **incomplete markers**:
  - "still need to", "pending", "next step"
  - User says "leave it for now", "later"
  - Explicit TODO comments
- Identify **in-progress markers**:
  - "working on", "processing"
  - Tasks mentioned in the last message

**Progress Evaluation**:
```
Completion calculation:
- Count all requirements raised by user
- Count requirements explicitly completed
- Completion = Completed / Total × 100%
```

### 3.5 Obstacles: Issues and Solutions

**Extraction Rules**:
- Search for **error signals**:
  - Error messages: `Error`, `Exception`, `Failed`
  - User feedback: "doesn't work", "got an error", "there's a problem"
  - Claude says: "found an issue", "needs fixing"
- Record **resolution process**:
  - Problem description
  - Attempted solutions (including failed ones)
  - Final solution
  - Current status: Resolved / Unresolved / Workaround

### 3.6 Environment: Technical Context

**Extraction Rules**:
- Infer language from **file extensions**: `.ts` → TypeScript, `.py` → Python
- Identify framework from **import statements**: `import React` → React, `from fastapi` → FastAPI
- Extract info from **config files**:
  - `package.json` → Node.js project, dependency list
  - `Cargo.toml` → Rust project
  - `pyproject.toml` → Python project
- Identify tools from **commands**: `npm` → npm, `pnpm` → pnpm, `cargo` → Cargo

### 3.7 Map: File Associations

**Extraction Rules**:
- List all **files read** (Read tool)
- List all **files modified** (Write/Edit tool)
- Analyze **dependencies**:
  - Extract from import statements
  - Mark core files vs auxiliary files

**Output Format**:
```
Core files (directly modified):
  - src/pages/Login.tsx
  - src/hooks/useRememberMe.ts

Related files (referenced):
  - src/types/auth.ts
  - src/utils/storage.ts

Dependency chain:
  Login.tsx → useRememberMe.ts → storage.ts
```

### 3.8 Signpost: Continuation Guide

**Extraction Rules**:
- Find **last working state**:
  - Last modified file
  - Last executed command
  - Last discussed topic
- Extract **explicit next steps**:
  - User says "do X next time"
  - Claude suggests "next you could Y"
  - Incomplete TODOs
- Generate **quick recovery instructions**:
  - Which files to read first
  - What commands to run first
  - Where to continue from

### 3.9 Session Statistics

**Extraction Rules**:
- Count **session scale**:
  - Total user messages
  - Total Claude replies
  - Conversation turns (back and forth count)
- Count **tool usage**:
  - Read tool invocations (how many files read)
  - Write tool invocations (how many files created)
  - Edit tool invocations (how many files modified)
  - Bash tool invocations (how many commands executed)
  - Grep/Glob tool invocations (search count)
  - Task tool invocations (how many subagents launched)
- Estimate **session duration**:
  - Time span from first to last message
  - Note main active periods

**Output Format**:
```
Conversation scale:
  - User messages: 15
  - Claude replies: 18
  - Conversation turns: 15

Tool usage:
  - File reads: 12
  - File modifications: 5 (2 created, 3 edited)
  - Command executions: 8
  - Code searches: 6
  - Subagents: 2

Session duration: About 45 minutes (14:30 - 15:15)
```

### 3.10 Code Quality Analysis

**Extraction Rules**:
- Count **code change scale**:
  - Total lines added (cumulative from all Write/Edit)
  - Total lines deleted (deletions in Edit operations)
  - Net line change (added - deleted)
- Detect **quality indicators**:
  - Linting check results (if eslint/pylint was run)
  - Type check results (if tsc/mypy was run)
  - Test coverage changes (if test reports exist)
- Identify **code style**:
  - Whether project's existing style is followed
  - Whether comments/documentation were added
  - Whether there are TODO/FIXME markers

**Output Format**:
```
Code scale:
  - Added: +356 lines
  - Deleted: -42 lines
  - Net: +314 lines

Quality checks:
  - ESLint: ✅ 0 errors, 2 warnings
  - TypeScript: ✅ Type check passed
  - Test coverage: From 78% → 82% (+4%)

Code style:
  - ✅ Follows Prettier format
  - ✅ Added JSDoc comments
  - ⚠️ Contains 2 TODO markers
```

### 3.11 Key Code Snippets

**Extraction Rules**:
- Identify **core code**:
  - Newly added core functions/classes (usually created by Write tool)
  - Important modification snippets (key logic modified by Edit tool)
  - Complex algorithms or business logic
- Save **condensed version**:
  - Keep only function signatures and key logic
  - Remove overly long implementation details
  - Keep at most 3-5 most important snippets
- Annotate **context**:
  - File location
  - Purpose description
  - Relationship with other code

**Output Format**:
```typescript
// src/hooks/useRememberMe.ts
export function useRememberMe() {
  const saveCredentials = (username: string, remember: boolean) => {
    if (remember) {
      storage.set('username', username);
    }
  };
  // ... core logic ...
}

// src/utils/storage.ts
export const storage = {
  set: (key: string, value: string) => localStorage.setItem(key, value),
  get: (key: string) => localStorage.getItem(key),
  // ... localStorage wrapper ...
}
```

### 3.12 Timeline View

**Extraction Rules**:
- Record major events in **chronological order**:
  - User raises requirement (timestamp)
  - Important decision points (timestamp)
  - File creation/modification (timestamp)
  - Test execution (timestamp)
  - Problem occurrence and resolution (timestamp)
- Mark **milestones**:
  - 🎯 Requirement confirmed
  - 🏗️ Implementation started
  - 🐛 Bug found
  - ✅ Feature completed
  - 🧪 Tests passed

**Output Format**:
```
14:30 🎯 User raises requirement: Add remember password feature
14:35 💬 Discuss technical solution: localStorage vs cookie
14:40 🏗️ Start implementing useRememberMe Hook
14:50 📝 Create storage utility functions
15:00 🔧 Modify Login component to integrate feature
15:05 🐛 Found issue: Incorrect storage format
15:08 ✅ Fixed storage issue
15:12 🧪 Run tests: All passed
15:15 ✨ Feature completed
```

### 3.13 Learning Notes

**Extraction Rules**:
- Extract **new knowledge**:
  - First-time used API/library
  - Newly learned language features
  - Previously unknown concepts
- Record **pitfall experiences**:
  - Unexpected behaviors encountered
  - Common error patterns
  - Solutions and best practices
- Note **reference sources**:
  - Documentation links consulted
  - Stack Overflow answers referenced
  - GitHub code borrowed from

**Output Format**:
```
New knowledge:
  - localStorage storage limit (5-10MB)
  - React 18's useId Hook usage
  - TypeScript's satisfies operator

Pitfall records:
  - localStorage.setItem() only stores strings, objects need JSON.stringify
  - Clearing localStorage triggers storage event, needs filtering

Best practices:
  - Wrap storage utility for unified serialization handling
  - Use try-catch to handle quota exceeded
```

### 3.14 Related Resources

**Extraction Rules**:
- Extract **external links**:
  - Identify URLs from conversation (using regex)
  - Categorize as documentation, blog, Stack Overflow, GitHub, etc.
- Identify **key search terms**:
  - Technical terms mentioned by user
  - Content Claude searched for (if WebSearch was called)
- Record **related Issues/PRs**:
  - GitHub Issues mentioned
  - Pull Requests referenced
  - Related bug tickets

**Output Format**:
```
Documentation links:
  - [MDN: Window.localStorage](https://developer.mozilla.org/...)
  - [React Docs: Hooks](https://react.dev/reference/react)

References:
  - Stack Overflow: "How to securely store credentials in browser"
  - GitHub Issue: facebook/react#12345

Search keywords:
  - "React localStorage hook"
  - "TypeScript storage utility"
```

### 3.15 Impact Analysis

**Extraction Rules**:
- Analyze **impact scope**:
  - Directly modified modules
  - Indirectly affected modules (through dependencies)
  - Potentially affected features
- Assess **risk level**:
  - 🟢 Low risk: Pure new feature, non-breaking
  - 🟡 Medium risk: Modifies existing code, needs regression testing
  - 🔴 High risk: Core logic changes, affects multiple modules
- Propose **testing suggestions**:
  - Scenarios to test
  - Edge conditions to watch
  - Recommended regression test scope

**Output Format**:
```
Impact scope:
  - Direct impact: Login module
  - Indirect impact: Authentication flow
  - Potential impact: Session management

Risk assessment: 🟡 Medium risk
  - Modified existing login logic
  - Introduced new storage mechanism
  - Need to consider privacy security

Testing suggestions:
  - ✅ Unit test: useRememberMe Hook
  - ✅ Integration test: Complete login flow
  - ⚠️ Manual test: Cross-browser compatibility
  - ⚠️ Security test: XSS injection protection
```

---

## Step 4: Output Confirmation (Required)

**Before writing files, must self-check the following checklist:**

```markdown
📋 Save Output Confirmation Checklist

- [ ] User intent accurately extracted
- [ ] Key decisions completely recorded
- [ ] Code changes fully listed (create/modify/delete)
- [ ] Task progress correctly assessed
- [ ] Issues and solutions recorded
- [ ] Technical context identified
- [ ] File associations established
- [ ] Continuation guide written
- [ ] Session statistics calculated
- [ ] Code quality analysis completed
- [ ] Key code snippets saved
- [ ] Timeline generated
- [ ] Learning notes extracted
- [ ] Related resources collected
- [ ] Impact analysis completed

**File Write Confirmation**:
- [ ] context.md correctly written
- [ ] index.json updated (new record added)
- [ ] Directory structure created

If anything is missing, supplement before writing files.
```

---

## Step 5: Generate Preview and Save

**After information extraction is complete, generate final preview and write files:**

### 5.1 Display Extraction Results Summary

```markdown
## 📋 Context Extraction Complete

**Title**: [User confirmed title]
**Tags**: [User confirmed tags]
**Summary**: [One sentence: What was done + Current status]

### Extraction Quality Check
| Section | Status | Content Preview |
|---------|--------|-----------------|
| 1. User Intent | ✅ | Add remember password feature... |
| 2. Key Decisions | ✅ | 3 decision points |
| 3. Code Changes | ✅ | 2 created, 2 modified |
| 4. Task Progress | ✅ | 80% complete |
| 5. Issue Records | ⚠️ | 1 unresolved |
| 6. Technical Context | ✅ | React + TypeScript |
| 7. File Associations | ✅ | 4 core files |
| 8. Continuation Guide | ✅ | Continue from test cases |
| 9. Session Statistics | ✅ | 15 turns, 45 minutes |
| 10. Code Quality | ✅ | +314 lines, 82% coverage |
| 11. Code Snippets | ✅ | 3 core functions |
| 12. Timeline | ✅ | 8 key nodes |
| 13. Learning Notes | ✅ | 3 knowledge points, 2 pitfalls |
| 14. Related Resources | ✅ | 2 documentation links |
| 15. Impact Analysis | ✅ | Medium risk, needs regression testing |

**Quality Score**: 15/15 sections complete ✨
```

### 5.2 Write Context File

Write extracted information to `context.md` file according to template format.

### 5.3 Update Index

Complete metadata for this record in `index.json`.

---

## Context Template

```markdown
---
id: "<YYYYMMDD-HHMMSS>"
title: "<title>"
project: "<project name>"
project_path: "<project path>"
created_at: "<ISO timestamp>"
updated_at: "<ISO timestamp>"
tags: ["<tag>"]
summary: "<one-line summary>"
completion: <completion percentage>
---

# <Title>

> <One-line summary>

## 1. Starting Point: User Intent

### Core Goal
<What the user wants to achieve>

### Specific Requirements
- <Requirement 1>
- <Requirement 2>

### Constraints
- <Constraint 1>
- <Constraint 2>

---

## 2. Process: Key Decisions

| # | Decision Point | Choice | Reason |
|---|----------------|--------|--------|
| 1 | <Issue> | <Solution> | <Reason> |
| 2 | <Issue> | <Solution> | <Reason> |

---

## 3. Output: Code Changes

### New Files
| File | Purpose |
|------|---------|
| `<path>` | <description> |

### Modified Files
| File | Changes |
|------|---------|
| `<path>` | <description> |

### Dependency Changes
<Added/removed dependencies>

### Executed Commands
```bash
<command1>
<command2>
```

---

## 4. Status: Task Progress

**Completion**: <X>%

### Completed ✅
- [x] <Task 1>
- [x] <Task 2>

### In Progress 🔄
- [ ] <Task 3> (progress note)

### Pending 📋
- [ ] <Task 4>

---

## 5. Obstacles: Issues and Solutions

| Issue | Status | Solution |
|-------|--------|----------|
| <Issue description> | ✅ Resolved | <Solution> |
| <Issue description> | ❌ Unresolved | <Attempted solutions> |

---

## 6. Environment: Technical Context

### Tech Stack
- **Language**: <language>
- **Framework**: <framework>
- **Tools**: <tools>

### Project Info
- **Package Manager**: <npm/pnpm/yarn/pip/cargo>
- **Build Tool**: <vite/webpack/esbuild>

---

## 7. Map: File Associations

### Core Files
<Directly modified files, sorted by importance>

### Related Files
<Referenced but not modified files>

### Dependency Graph
```
<entry file>
├── <dependency 1>
│   └── <sub-dependency>
└── <dependency 2>
```

---

## 8. Signpost: Continuation Guide

### Current State
<Description of last working state>

### Next Actions
1. <Specific action 1>
2. <Specific action 2>

### Quick Recovery
```bash
# Read these files first to understand context
<file list>

# Then continue from here
<specific location or task>
```

### Notes
- <Important reminder 1>
- <Important reminder 2>

---

## 9. Session Statistics

### Conversation Scale
- **User messages**: <count>
- **Claude replies**: <count>
- **Conversation turns**: <count>

### Tool Usage Statistics
| Tool | Invocations | Description |
|------|-------------|-------------|
| Read | <count> | Read <count> files |
| Write | <count> | Created <count> files |
| Edit | <count> | Modified <count> files |
| Bash | <count> | Executed <count> commands |
| Grep/Glob | <count> | Performed <count> searches |
| Task (Subagents) | <count> | Launched <count> subagents |

### Session Duration
- **Time span**: About <X> minutes (<start time> - <end time>)
- **Main active period**: <time period>

---

## 10. Code Quality Analysis

### Code Change Scale
- **Lines added**: +<count>
- **Lines deleted**: -<count>
- **Net change**: +/-<count>

### Quality Check Results
| Check Item | Result | Details |
|------------|--------|---------|
| Linting | <status> | <details> |
| Type Check | <status> | <details> |
| Test Coverage | <status> | From <X>% → <Y>% |

### Code Style
- <Whether project style is followed>
- <Whether comments/docs were added>
- <TODO/FIXME marker status>

---

## 11. Key Code Snippets

### Core Functions/Classes
```<language>
// <file path>
<Code snippet 1 - function signature and key logic>

// <file path>
<Code snippet 2>
```

### Important Modifications
```<language>
// <file path> - <modification description>
<Before/after comparison or key changes>
```

---

## 12. Timeline View

```
<time1> 🎯 <Event 1 - Requirement confirmed>
<time2> 💬 <Event 2 - Technical discussion>
<time3> 🏗️ <Event 3 - Implementation started>
<time4> 📝 <Event 4 - File created>
<time5> 🔧 <Event 5 - Code modified>
<time6> 🐛 <Event 6 - Issue found>
<time7> ✅ <Event 7 - Issue resolved>
<time8> 🧪 <Event 8 - Test verification>
<time9> ✨ <Event 9 - Feature completed>
```

**Key Milestones**:
- 🎯 Requirement confirmed: <time>
- 🏗️ Implementation started: <time>
- ✅ Main feature completed: <time>
- 🧪 Tests passed: <time>

---

## 13. Learning Notes

### New Knowledge
- <Knowledge 1 - API/library/language feature>
- <Knowledge 2>
- <Knowledge 3>

### Pitfall Records
| Problem | Cause | Solution |
|---------|-------|----------|
| <Pitfall 1> | <Cause> | <Solution> |
| <Pitfall 2> | <Cause> | <Solution> |

### Best Practices
- <Practice 1 - Experience summarized from this session>
- <Practice 2>
- <Practice 3>

### Reference Sources
- <Documentation link or Stack Overflow link>
- <GitHub code reference>

---

## 14. Related Resources

### Documentation Links
- [<Document name>](<URL>)
- [<Document name>](<URL>)

### References
- <Stack Overflow question link or summary>
- <GitHub Issue/PR link>
- <Blog article link>

### Search Keywords
- "<keyword 1>"
- "<keyword 2>"
- "<keyword 3>"

**Tip**: These keywords can be used for subsequent searches

---

## 15. Impact Analysis

### Impact Scope
- **Direct impact**: <Directly modified modules>
- **Indirect impact**: <Modules affected through dependencies>
- **Potential impact**: <Potentially affected features>

### Risk Assessment
**Level**: <🟢 Low risk / 🟡 Medium risk / 🔴 High risk>

**Risk Points**:
- <Risk 1>
- <Risk 2>
- <Risk 3>

### Testing Suggestions
**Required Tests**:
- ✅ <Test type 1>: <Test content>
- ✅ <Test type 2>: <Test content>

**Recommended Tests**:
- ⚠️ <Test type 3>: <Test content>
- ⚠️ <Test type 4>: <Test content>

**Regression Test Scope**:
- <Modules or features requiring regression testing>
```

---

## Output

After successful save, output:
```
✅ Context saved

📁 Location: .claude/mnemosyne/<folder>/
🏷️ Tags: <tags>
📊 Completion: <X>%
📝 Quality: 15/15 sections complete
💾 Data size: <X> KB

💡 Use /mnemosyne:load <id> to restore this context
```
