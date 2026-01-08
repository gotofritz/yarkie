# /implement [step]

Read `docs/project-plan.md`, and pick either {step} or list the top level steps and ask the user which one to implement.

Ask if user wants new branch. If yes:

- pull main
- ask user if they have a github issue number and title
- if yes
  - create branch from {issue number}-{slugified title}
- if not
  - create branch from {slugified step}

Create todos, follow CLAUDE.md standards, atomic commits.

When work is completed, run ./tool-archive {step}
