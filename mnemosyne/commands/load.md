---
description: Load historical context. Quickly restore project background and progress in a new session.
argument-hint: [id] [--latest]
---

# /mnemosyne:load - Load Context

User input: $ARGUMENTS

---

## Step 1: Get Context List

**Read index file**: `.claude/mnemosyne/index.json`

**If user specified an ID**: Load the corresponding context directly
**If user specified --latest**: Load the most recently saved context
**Otherwise**: Display list for user to choose

---

## Step 2: Display Selection List

**Use AskUserQuestion to let user choose:**

```
Recently saved contexts:

1. [20241225-103000] Implement user authentication feature
   Tags: feature, auth, React
   Time: 2024-12-25 10:30

2. [20241224-150000] Fix login page bug
   Tags: bugfix, auth
   Time: 2024-12-24 15:00

3. [20241223-090000] Project initial configuration
   Tags: config, setup
   Time: 2024-12-23 09:00

Please select the context to load:
```

---

## Step 3: Load and Display

**Read context file**: `.claude/mnemosyne/<folder>/context.md`

**Display key information to user:**

```markdown
## 📥 Context Loaded

**Title**: Implement user authentication feature
**Project**: my-app
**Saved at**: 2024-12-25 10:30

---

### 🎯 Requirements Summary
Add JWT authentication feature to the application...

### ✅ Current Progress
- [x] JWT utility functions
- [x] Login page
- [ ] Registration page (50%)

### 🚀 Continuation Guide
Start from the form validation of the registration page...

---

Context has been loaded. You can continue your previous work now!
```

---

## Output Format

After successful loading, Claude should:
1. Understand the project background and current state
2. Know what decisions were made before
3. Be clear about what to do next
4. Be familiar with related files and code
