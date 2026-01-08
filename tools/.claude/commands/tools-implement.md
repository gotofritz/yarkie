# /implement [step]

Read `docs/project-plan.md`, and pick either {step} or list the top level steps and ask the user which one to implement.

Ask if user wants new branch

- if the answer is anything except "no", change to the main branch and pull
- If the answer was {number} {string} assume "yes" and create branch from {number}-{slugified string}
- else if the answer was "yes", ask user if they have a github issue number and title
  - if yes
    - create branch from {issue number}-{slugified title}
  - if not
    - create branch from {slugified step name}

Create todos, follow CLAUDE.md standards, atomic commits.

When work is completed, run ./tool-archive {step}
