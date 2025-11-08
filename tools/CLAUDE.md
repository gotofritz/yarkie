# CLI Script Rearchitecture Project

## Project Context

- **Type**: Local utility CLI application (no performance/security constraints)
- **Status**: Partially rearchitected, still functional but architecturally inconsistent
- **Priority**: Stabilize architecture while maintaining active development capability

## Current Phase

**Phase 0: Initial code analysis with Claude Code**

- Understand current structure, pain points, inconsistencies
- Map out what exists and how it flows
- Identify quick wins and structural problems
- Document findings to guide Phase 1

**Phase 1: Bring to consistent baseline state** (elegance can come later)

## Key Principles

1. **Pragmatic over perfect** - aim for consistent "mediocrity" first, elegant later
2. **Incremental improvement** - small changes tied to new features/fixes, not big rewrites
3. **Always functional** - maintain working state; no breaking changes without clear value
4. **Test as safety net** - tests verify behavior during refactoring, document expected functionality

## Working Agreement

When helping with this project, Claude should:

### Phase 0: Code Analysis (Claude Code)

Before suggesting any changes, analyze the codebase to:

- Map the overall structure and entry points
- Identify inconsistencies (naming, error handling, code style, patterns)
- Flag pain points (duplicated logic, unclear flow, hard-to-extend areas)
- Note quick wins (easy cleanups that improve readability without logic changes)
- Understand the feature set and data flow
- Create a structural summary with recommendations for Phase 1

**Deliverable**: A clear summary of findings that explains what exists, what's inconsistent, and where to focus initial cleanup efforts.

### When analyzing code

- Ask clarifying questions about current pain points before suggesting changes
- Point out inconsistencies in style, error handling, structure without requiring immediate fixes
- Identify which parts are causing friction in development (hard to add features, hard to debug)

### When suggesting refactors

- Propose small, discrete changes that can be validated independently
- Explain the "why" in terms of making future development easier
- Avoid suggesting rewrites unless the code is genuinely unmaintainable
- Suggest what tests would validate the change

### When adding features

- Use it as an opportunity to incrementally improve surrounding code
- Refactor only what's necessary to cleanly add the feature
- Leave everything else unchanged unless it directly impedes the new work

### When creating/updating code

- Maintain existing style and patterns unless explicitly changing them
- Add inline comments for non-obvious logic or recent refactors
- Include docstrings/help text for user-facing commands
- Suggest simple tests that verify the change works

## Project Structure Notes

[Add here after initial review: main entry point, key modules/functions, where new features typically go, known problem areas]

## Success Metrics for Phase 1

- Code style consistent throughout
- Error handling standardized
- Basic test coverage for main commands exists
- New features can be added without understanding the entire codebase
- No functionality lost or degraded

## Future Phases

- **Phase 2**: Modularize by concerns (command handling, utilities, config, output)
- **Phase 3**: Extract reusable patterns and establish plugin/extension points
- **Phase 4**: Optimize and refine based on actual pain points encountered
