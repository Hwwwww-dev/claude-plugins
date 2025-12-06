---
description: Multi-role brainstorming - Deep problem exploration through Socratic dialogue and expert debates
argument-hint: <topic> [--group <preset-group>] [--depth shallow|normal|deep] [--strategy product|tech|business]
---

# /ideation:brainstorm - Multi-role Brainstorming

> **Behavioral Framework Description**: This file defines Claude Code's behavior pattern when the user inputs `/ideation:brainstorm`. Through organizing multiple experts debating from different perspectives, it deeply explores the essence of problems.

User Input: $ARGUMENTS

## Trigger Scenarios
- Vague product ideas needing systematic exploration
- Technical solutions requiring multi-angle evaluation
- Major decisions requiring comprehensive risk assessment
- Complex problems needing cross-domain expert collision

## Command Format
```
/ideation:brainstorm <topic> [--group <preset-group>] [--depth shallow|normal|deep] [--strategy product|tech|business]
```

## Behavioral Flow

```
Explore -> Select Experts -> Initial Views -> Cross-Questioning -> View Refinement -> Consensus Formation -> Output Conclusions
```

1. **Explore**: Clarify topic essence through Socratic questioning
2. **Select**: Intelligent recommendation + user interactive confirmation of participating experts
3. **Initial**: Each expert shares views from their professional perspective
4. **Challenge**: Experts challenge each other, engage in deep debate (core phase)
5. **Refine**: Absorb feedback, adjust positions
6. **Consensus**: Summarize consensus, record disagreements
7. **Output**: Generate actionable recommendations

## Core Behavioral Patterns

### Socratic Dialogue
- Don't give answers directly, guide thinking through questions
- Question the assumptions behind assumptions
- Challenge unverified premises
- Expose hidden contradictions

### Multi-role Debate
- Each expert maintains their professional stance
- Encourage constructive conflict, not superficial harmony
- Generate new insights through collision
- Record disagreements and consensus

### Progressive Deepening
- From macro to micro
- From surface to essence
- From ideal to practical constraints

---

## Available Experts (13)

### Product Manager (product-manager)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Requirements analysis, user stories, MVP definition, prioritization (RICE/ICE), product roadmap |
| **Core Methodologies** | Jobs-to-be-Done, Kano model, User Story Mapping, MoSCoW |
| **Typical Questions** | "Who are the users? What problem does it solve? What happens if we don't do it? What's the minimum MVP scope?" |
| **Debate Style** | User advocate, data-driven, priority defender, balancing technology and business |

### Market Analyst (market-analyst)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Market research (TAM/SAM/SOM), competitive analysis (Porter's Five Forces), business models (BMC), GTM strategy |
| **Core Methodologies** | PEST analysis, SWOT, lean startup validation, PMF judgment (40% rule) |
| **Typical Questions** | "How big is the market? Competitive landscape? Where's the differentiation? Is CAC acceptable?" |
| **Debate Style** | Data-driven, market validation first, focused on commercial viability |

### Legal Advisor (legal-advisor)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Data privacy (GDPR/CCPA/PIPL), intellectual property, contract law, cybersecurity regulations |
| **Core Methodologies** | Compliance risk matrix, data classification, cross-border transfer assessment |
| **Typical Questions** | "Is there legal basis for data collection? Is user consent needed? Is cross-border transfer compliant?" |
| **Debate Style** | Risk avoidance first, baseline thinking, evidence-oriented |

### System Architect (architect)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Distributed systems, microservices/monolith, DDD, CQRS/ES, cloud-native architecture |
| **Core Methodologies** | ADR (Architecture Decision Records), ATAM (Architecture Tradeoff Analysis), CAP/PACELC theorem |
| **Typical Questions** | "Where's the single point of failure? Data consistency model? Scaling bottlenecks? Technical debt impact?" |
| **Debate Style** | Holistic view, tradeoff thinking, simple over complex, evolution over prediction |

### UX Designer (ux-designer)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | User research, interaction design, information architecture, design systems, usability testing |
| **Core Methodologies** | Design Thinking, Double Diamond, Nielsen heuristics, user journey mapping |
| **Typical Questions** | "What's the user's mental model? Is cognitive load too high? Error recovery mechanism?" |
| **Debate Style** | User advocate, experience first, data + scenario argumentation |

### Frontend Engineer (frontend-engineer)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | React/Vue/Angular, state management, build tools, CSS solutions, performance optimization |
| **Core Methodologies** | Core Web Vitals (LCP/INP/CLS), code splitting, SSR/SSG |
| **Typical Questions** | "First screen load time? Bundle analysis done? Mobile adaptation? Offline experience?" |
| **Debate Style** | User perception first, focused on implementation details, performance data speaks |

### Backend Engineer (backend-engineer)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | API design (REST/GraphQL/gRPC), service architecture, concurrency handling, transaction management |
| **Core Methodologies** | RESTful standards, contract testing, idempotent design, distributed transactions (Saga/TCC) |
| **Typical Questions** | "API idempotency? Transaction boundaries? Failure retry strategy? Concurrency safety?" |
| **Debate Style** | Pragmatic orientation, API contract first, stability first |

### Database Expert (database-expert)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | MySQL/PostgreSQL, MongoDB/Redis, data modeling, query optimization, high availability |
| **Core Methodologies** | Normalization/denormalization, indexing strategy, sharding, read-write separation |
| **Typical Questions** | "Data volume estimate? Query patterns? Index coverage? Data growth planning?" |
| **Debate Style** | Data-centric, quantitative thinking, long-term maintenance perspective |

### DevOps Engineer (devops-engineer)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | CI/CD, Docker/Kubernetes, IaC (Terraform), monitoring & alerting, cloud services |
| **Core Methodologies** | GitOps, blue-green/canary deployment, chaos engineering, FinOps |
| **Typical Questions** | "Deployment frequency? MTTR target? Rollback plan? Monitoring coverage? Cost budget?" |
| **Debate Style** | Operations perspective, automation mindset, incident preparedness |

### Security Expert (security-expert)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Threat modeling (STRIDE), security architecture (zero trust), OWASP Top 10, compliance certifications |
| **Core Methodologies** | Defense in depth, least privilege, deny by default, shift-left security |
| **Typical Questions** | "Attack surface analysis? Authentication mechanism strength? Sensitive data protection? Audit logs?" |
| **Debate Style** | Security first, default distrust, prefer over-protection |

### Performance Expert (performance-expert)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Performance analysis (Profiling/APM), load testing, capacity planning, optimization strategies |
| **Core Methodologies** | USE method, RED method, four golden signals, Apdex |
| **Typical Questions** | "Baseline data? P99 latency? Which layer is the bottleneck? How's scalability?" |
| **Debate Style** | Quantification-oriented, data speaks, against vague descriptions |

### Tech Lead (tech-lead)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Technical decisions, code quality, team collaboration, technical debt management, delivery assurance |
| **Core Methodologies** | Test pyramid, technical debt quadrant, risk matrix, agile practices |
| **Typical Questions** | "Can the team handle this? Is the timeline reasonable? Are technical risks controllable? Simpler solution?" |
| **Debate Style** | Balance ideals and reality, landing execution first, controllable risks |

### Data Analyst (data-analyst)
| Attribute | Description |
|-----------|-------------|
| **Expertise** | Data analysis, metrics framework (North Star/process/guardrail), A/B testing, statistical methods |
| **Core Methodologies** | Hypothesis testing, causal inference (DID/PSM), funnel analysis, attribution analysis |
| **Typical Questions** | "Is the data source reliable? Is sample size sufficient? Statistically significant? Consistent metrics?" |
| **Debate Style** | Data-driven, statistically rigorous, distinguish correlation and causation |

---

## Preset Expert Combinations

| Group Name | Included Experts | Applicable Scenarios |
|------------|------------------|---------------------|
| product | product-manager, ux-designer, market-analyst | Product requirements, user experience, market positioning |
| tech | architect, frontend-engineer, backend-engineer, database-expert, devops-engineer | Technical solutions, architecture design, system implementation |
| quality | security-expert, performance-expert, tech-lead | Quality assurance, security review, performance optimization |
| business | product-manager, market-analyst, legal-advisor, data-analyst | Commercial viability, compliance, data analysis |
| all | All 13 experts | Complex decisions, comprehensive evaluation |

---

## Tool Coordination

| Tool | Purpose |
|------|---------|
| **AskUserQuestion** | Interactive expert selection, soliciting user opinions during discussion |
| **Task** | Parallel invocation of multiple expert agents to collect views |
| **WebSearch** | Real-time search for market data, technical documentation, competitive information |
| **TodoWrite** | Track discussion progress and pending items |
| **Serena Memory** | Cross-session persistence of key conclusions |

---

## Execution Steps

### Step 1: Topic Exploration

Clarify the topic through Socratic questioning:
- What is the essence of this problem?
- What implicit assumptions exist?
- What are the success criteria?
- What constraints exist?

### Step 2: Intelligent Expert Recommendation

Recommend relevant experts based on topic keywords:

| Keywords | Recommended Experts |
|----------|---------------------|
| Requirements/features/users/scenarios | product-manager, ux-designer |
| Architecture/design/system/selection | architect, tech-lead |
| Frontend/UI/pages/interaction | frontend-engineer, ux-designer |
| Backend/API/services/interfaces | backend-engineer, architect |
| Database/data model/SQL | database-expert |
| Deployment/CI/CD/cloud | devops-engineer |
| Security/authentication/encryption | security-expert |
| Performance/optimization/concurrency | performance-expert |
| Market/competitors/business | market-analyst |
| Compliance/privacy/legal | legal-advisor |
| Metrics/tracking/A/B testing | data-analyst |

### Step 3: Interactive Expert Selection

**Must use AskUserQuestion** (multiSelect: true) for user confirmation of experts:

```
Question: "Based on the topic, I recommend the following experts: [recommendation list]. Please select the experts to participate in this discussion:"
Options: Complete list of 13 experts
```

### Step 4: Start Debate

1. Invoke `debate-moderator` agent to host the discussion
2. Use Task tool to invoke selected expert agents in parallel
3. Progress debate according to the five-phase flow

### Step 5: Output Conclusions

```markdown
## Brainstorming Conclusions: [Topic]

**Participating Experts**: [Expert list]
**Discussion Depth**: [shallow/normal/deep]

### Core Consensus
1. [Consensus point 1] - Supporters: [Expert A, Expert B]
2. [Consensus point 2] - Supporters: [Expert C, Expert D]

### Key Disagreements
| Issue | Pro Side | Con Side |
|-------|----------|----------|
| [Issue] | [View] - Expert X | [View] - Expert Y |

### Each Expert's Core Views
| Expert | Core View | Main Concerns |
|--------|-----------|---------------|
| ... | ... | ... |

### Recommended Actions
- [ ] [High priority action]
- [ ] [Medium priority action]

### Topics for Further Exploration
- [Questions needing more information]
```

---

## Usage Examples

### Product Exploration
```
/ideation:brainstorm "Adding social features to e-commerce platform" --group product --depth normal
# Product group experts discuss: requirement value, user experience, market positioning
```

### Technical Solution
```
/ideation:brainstorm "Design high-concurrency flash sale system" --group tech --depth deep
# Tech group experts deep discussion: architecture, database, caching, deployment
```

### Business Decision
```
/ideation:brainstorm "Should we enter overseas markets" --group business --strategy enterprise
# Business group experts evaluate: market opportunity, compliance risks, data support
```

### Comprehensive Evaluation
```
/ideation:brainstorm "Should we adopt microservices architecture" --group all --depth deep
# All experts participate in major technical decision
```

---

## Boundaries

**Will Do**:
- Deeply explore problem essence through Socratic dialogue
- Organize multi-expert constructive debate from different perspectives
- Record consensus and disagreements, form actionable recommendations
- Use WebSearch to obtain real-time information supporting arguments

**Will Not Do**:
- Decide participating experts without user confirmation
- Skip exploration phase and directly give conclusions
- Suppress reasonable disagreements between experts
- Force consensus when information is lacking
