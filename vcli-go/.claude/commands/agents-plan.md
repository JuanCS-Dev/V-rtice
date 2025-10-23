Execute ARQUITETO agent for architecture planning and design analysis.

**What it does:**
- Analyzes current codebase structure
- Generates implementation plans with ADRs (Architecture Decision Records)
- Estimates complexity and risks
- Identifies affected files and dependencies
- Creates step-by-step implementation roadmap
- Suggests design patterns and best practices

**Usage examples:**
- "Use agents-plan to design authentication system architecture"
- "Run ARQUITETO to plan microservices migration for ./services"
- "agents-plan: create implementation roadmap for rate limiting feature"

**Output includes:**
- **Architecture Overview** - High-level design
- **ADRs** - Architecture Decision Records with rationale
- **Risk Assessment** - Potential issues and mitigations
- **File Impact Analysis** - Which files need changes
- **Complexity Estimate** - 1-10 scale with justification
- **Implementation Steps** - Sequential roadmap
- **Testing Strategy** - Recommended test approach

**Plan structure:**
```json
{
  "task": "Add authentication middleware",
  "complexity": 7,
  "estimated_files": 5,
  "risks": ["Breaking existing routes", "Session storage"],
  "steps": [
    "Create auth middleware in ./internal/middleware",
    "Add JWT token validation",
    "Update route handlers",
    "Add tests"
  ]
}
```

**When to use:**
- Before implementing complex features
- When unsure about architecture approach
- For refactoring large code sections
- To document design decisions

The plan can be passed as context to DEV SENIOR for implementation.
