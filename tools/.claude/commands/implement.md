# /implement

Ask if user wants new branch. If yes: pull main

**GitHub workflow:**

1. Run `gh issue list --assignee @me` to list assigned issues
2. If issues exist: ask user to pick an issue number OR create a new one
3. If no issues: ask if they want to create a new issue
4. If issue picked: use `gh issue develop XX --checkout` to create branch
5. If creating new or no issue: branch from slugified project-plan title
6. Push branch and create draft PR with `gh pr create --draft --title "{title}" --body "{summary from project-plan}"`

Then read `docs/project-plan.md`, implement next task(s) by priority/dependencies. Create todos, follow CLAUDE.md standards, atomic commits.
